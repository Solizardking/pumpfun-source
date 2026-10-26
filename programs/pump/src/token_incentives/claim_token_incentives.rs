//! Bounded claim of Token-2022 incentives from a local daily-volume fixture.
use anchor_lang::prelude::*;
use anchor_lang::Event;
use anchor_lang::solana_program::{instruction::{AccountMeta, Instruction},
    program::invoke_signed};
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token_interface::{self, Mint, TokenAccount, TokenInterface,
    TransferChecked};

use crate::{GlobalVolumeAccumulator, UserVolumeAccumulator};

const EVENT_CPI_DISCRIMINATOR: [u8; 8] = [228, 69, 165, 46, 81, 203, 154, 29];

#[derive(Accounts)]
pub struct ClaimTokenIncentives<'info> {
    /// CHECK: The user key names its ATA and volume PDA; it is not a signer.
    pub user: UncheckedAccount<'info>,
    #[account(mut, associated_token::mint = mint,
        associated_token::authority = user,
        associated_token::token_program = token_program)]
    pub user_ata: InterfaceAccount<'info, TokenAccount>,
    #[account(seeds = [b"global_volume_accumulator"], bump,
        has_one = mint)]
    pub global_volume_accumulator: Account<'info, GlobalVolumeAccumulator>,
    #[account(mut, associated_token::mint = mint,
        associated_token::authority = global_volume_accumulator,
        associated_token::token_program = token_program)]
    pub global_incentive_token_account: InterfaceAccount<'info, TokenAccount>,
    #[account(mut, seeds = [b"user_volume_accumulator", user.key().as_ref()], bump)]
    pub user_volume_accumulator: Account<'info, UserVolumeAccumulator>,
    pub mint: InterfaceAccount<'info, Mint>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    /// CHECK: This is the program's event CPI signer PDA.
    #[account(seeds = [b"__event_authority"], bump)]
    pub event_authority: UncheckedAccount<'info>,
    /// CHECK: The pinned program account is the event CPI target.
    #[account(address = crate::ID @ anchor_lang::error::ErrorCode::InvalidProgramId)]
    pub program: UncheckedAccount<'info>,
    #[account(mut)]
    pub payer: Signer<'info>,
}

#[event]
#[derive(Clone)]
pub struct ClaimTokenIncentivesEvent {
    pub user: Pubkey,
    pub mint: Pubkey,
    pub amount: u64,
    pub timestamp: i64,
    pub total_claimed_tokens: u64,
    pub current_sol_volume: u64,
}

pub fn claim(ctx: Context<ClaimTokenIncentives>) -> Result<()> {
    let now = Clock::get()?.unix_timestamp;
    let global = &ctx.accounts.global_volume_accumulator;
    let start = global.start_time;
    let seconds = global.seconds_in_a_day;
    require!(seconds > 0, crate::ReconstructionError::ReconstructionBranchUnsupported);
    if now < start {
        return Ok(());
    }
    // The observed time bound compares integer day indices. If a synthetic
    // end_time permits index 30, the pinned program then panics indexing its
    // fixed 30-day array; a rounded end-day below that returns successfully.
    let current_day_number = (now - start) / seconds;
    let final_day_number = (global.end_time - start) / seconds;
    if current_day_number > final_day_number {
        return Ok(());
    }
    let current_day = usize::try_from(current_day_number)
        .map_err(|_| crate::ReconstructionError::ReconstructionBranchUnsupported)?;
    let _ = global.total_token_supply[current_day];
    let user = &mut ctx.accounts.user_volume_accumulator;
    let previous = user.last_update_timestamp;
    user.last_update_timestamp = now;
    if previous < start || previous >= now {
        return Ok(());
    }
    let day = usize::try_from((previous - start) / seconds)
        .map_err(|_| crate::ReconstructionError::ReconstructionBranchUnsupported)?;
    if day >= 30 {
        return Ok(());
    }
    let mut accrued = 0u64;
    let daily_sol_volume = global.sol_volumes[day];
    if daily_sol_volume > 0 {
        accrued = u64::try_from(
            u128::from(user.current_sol_volume)
                .checked_mul(u128::from(global.total_token_supply[day]))
                .ok_or(crate::ReconstructionError::ReconstructionBranchUnsupported)?
                / u128::from(daily_sol_volume))
            .map_err(|_| crate::ReconstructionError::ReconstructionBranchUnsupported)?;
        user.current_sol_volume = 0;
        user.needs_claim = false;
    }
    let amount = user.total_unclaimed_tokens.checked_add(accrued)
        .ok_or(crate::ReconstructionError::ReconstructionBranchUnsupported)?;
    if amount == 0 {
        return Ok(());
    }
    let bump = [ctx.bumps.global_volume_accumulator];
    let signer: &[&[u8]] = &[b"global_volume_accumulator", &bump];
    let transfer = TransferChecked {
        from: ctx.accounts.global_incentive_token_account.to_account_info(),
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.user_ata.to_account_info(),
        authority: global.to_account_info(),
    };
    token_interface::transfer_checked(
        CpiContext::new_with_signer(ctx.accounts.token_program.to_account_info(),
                                    transfer, &[signer]),
        amount, ctx.accounts.mint.decimals)?;
    user.total_unclaimed_tokens = 0;
    user.total_claimed_tokens = user.total_claimed_tokens.checked_add(amount)
        .ok_or(crate::ReconstructionError::ReconstructionBranchUnsupported)?;
    user.has_total_claimed_tokens = true;
    let event = ClaimTokenIncentivesEvent {
        user: ctx.accounts.user.key(), mint: ctx.accounts.mint.key(),
        amount, timestamp: now,
        total_claimed_tokens: user.total_claimed_tokens,
        current_sol_volume: user.current_sol_volume,
    };
    emit!(event.clone());
    let mut data = EVENT_CPI_DISCRIMINATOR.to_vec();
    data.extend_from_slice(&event.data());
    let ix = Instruction {
        program_id: crate::ID,
        accounts: vec![AccountMeta::new_readonly(
            ctx.accounts.event_authority.key(), true)],
        data,
    };
    let event_bump = [ctx.bumps.event_authority];
    let event_signer: &[&[u8]] = &[b"__event_authority", &event_bump];
    invoke_signed(&ix, &[
        ctx.accounts.event_authority.to_account_info(),
        ctx.accounts.program.to_account_info(),
    ], &[event_signer])?;
    Ok(())
}
