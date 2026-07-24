---
title:
  "DeFi handler phantom risk — structural write-before-manifest gap in 4 handlers (evm_defi, gas_fee, solana_defi,
  lst_rates)"
created: 2026-05-15
author: harsh-slot-9 (Day-4 MTDS handler readiness audit)
resolved: 2026-05-16
resolution: >
  SHIPPED — all 4 handlers structurally hardened by `MTDS@f657431` (lst_rates) + `MTDS@c1e6963` (evm_defi / gas_fee /
  solana_defi recorder.close() in finally). Re-verified by slot-3 2026-05-16: every (protocol, chain) shard now wraps
  upload + record_captured in the same try block; upload exception → record_failed; `recorder.close()` in finally;
  eigenlayer_rewards pattern matched. Safe to launch DeFi backfill VMs (features-onchain-defi-backfill-20260516-220052
  launched on this basis).
source:
  - "slot-9 Day-4 item 4: MTDS handler readiness audit for DeFi backtests"
  - "companion to /plans/active/issues/b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md"
severity: "P1 (systemic: affects all DeFi backfill VMs; P0 instance already confirmed in lst_rates)"
locked_by: live-defi-rollout
locked_since: 2026-05-15
---

> **✅ RESOLVED 2026-05-16 (slot-3 verification)** — All 4 handlers structurally hardened before this issue was filed.
> Author's audit window was pre-`c1e6963` (2026-05-15 08:33 UTC); the lst_rates fix at `f657431` and the evm_defi /
> gas_fee / solana_defi `recorder.close()` finally fix at `c1e6963` together close the systemic risk. Slot-3 re-verified
> 2026-05-16 by reading each handler's `record_captured` callsite + outer try/except + finally block. Safe to launch
> DeFi backfill VMs.

## What I found

Code audit of 5 MTDS DeFi handlers (lst_rates, evm_defi, gas_fee, solana_defi, eigenlayer_rewards) for the same phantom
manifest risk that caused B-015 silent-skip (see companion issue doc).

**All 5 handlers call `record_captured()` AFTER the GCS write** (`upload_bytes` / `upload_parquet`). This creates a
write-then-manifest sequencing gap: if the GCS upload succeeds but the manifest call fails or is skipped (exception,
process kill, stale lock), a phantom row can be created in either direction (data without manifest, or manifest without
data).

### Per-handler risk summary

| Handler                         | Phantom Risk | Protection                                            | Key concern                                                                                                                         |
| ------------------------------- | ------------ | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `lst_rates_handler.py`          | HIGH         | None outside `record_empty` routing                   | Partial-group writes (per protocol/chain) with no transactional guarantee across the group; stale lock confirmed live (B-015)       |
| `evm_defi_handler.py`           | MEDIUM       | Outer try/except calls `record_failed()` on exception | Multi-protocol loop: if one pair uploads but record_captured fails, that pair has phantom with recovery via outer except only       |
| `gas_fee_handler.py`            | MEDIUM       | Loop-level except calls `record_failed()` on throw    | Multiple write paths (EVM/Solana/BTC); each path uploads then records; no atomicity across chain loop                               |
| `solana_defi_handler.py`        | MEDIUM       | Outer except at 242-253 calls `record_failed()`       | Upload (line 342) before record_captured (lines 225-232); brief unclean window if record_captured throws mid-write                  |
| `eigenlayer_rewards_handler.py` | LOW          | Try/except/finally wraps BOTH write AND manifest      | Most defensive: if upload succeeds but record_captured fails, outer except emits record_failed immediately; finally ensures close() |

### Root cause (structural)

The safe pattern (eigenlayer_rewards) is:

```python
try:
    storage.upload_bytes(...)     # GCS write
    recorder.record_captured(...)  # manifest — inside same try block
except Exception as exc:
    recorder.record_failed(...)    # recovery — if either write OR manifest fails
finally:
    recorder.close()              # ensures flush even on exit
```

The risky pattern (lst_rates / evm_defi / gas_fee / solana_defi) is:

```python
storage.upload_bytes(...)         # GCS write — no try block or separate try
recorder.record_captured(...)     # manifest — outside the upload try scope
```

If the GCS write throws and is caught at an outer loop level that doesn't call `record_failed()`, the manifest row is
silently absent. If the GCS write succeeds but the process is killed before `record_captured()`, the manifest row is
absent but data exists.

## Why it matters

1. **B-015 blocker root cause**: The lst_rates phantom rows confirmed live (2026-05-14) are the same structural pattern
   as the other 4 handlers. Ikenna's phantom audit + apply-flips fixes the DATA state but doesn't fix the CODE — the
   same phantom can re-accumulate on the next backfill unless the handler code is hardened.
2. **DeFi cutover readiness (May-23)**: Before any DeFi backfill VM runs successfully, the code must not regenerate
   phantom rows. A hardened handler + re-run is the only durable fix.
3. **Scope of risk**: Any DeFi backfill VM that runs lst_rates, evm_defi, gas_fee, or solana_defi can produce phantom
   rows in the same way. gas_fee_handler has multiple write paths (EVM, Solana, BTC) — higher risk surface.

## Recommended decision

**Two-phase fix**:

1. **Immediate (before B-015 re-smoke)**: Harden `lst_rates_handler.py` to use the eigenlayer pattern (wrap upload +
   record_captured in same try block; outer except calls record_failed; finally calls recorder.close()). ~30 min, low
   blast radius.
2. **Follow-up sweep (within next cycle)**: Apply same pattern to evm_defi, gas_fee, solana_defi. File as a single
   hardening PR. Eigenlayer_rewards is already safe — use it as the reference.

**Assignment**: Harsh slot 9 or slot 2 (reserve) can take Phase 1 (lst_rates hardening) if B-015 is still blocked. Phase
2 sweep goes to whoever ships lst_rates first.

**Do NOT attempt B-015 Phase 2 re-smoke with lst_rates handler in current state** — the phantom rows will re-accumulate
even after Ikenna's apply-flips clears the backlog.

## Cross-references

- Companion P0 issue: `plans/active/issues/b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md`
- Phantom audit: `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`
- Safe pattern reference: `market_tick_data_service/cli/handlers/eigenlayer_rewards_handler.py`
- Shard-level failure isolation SSOT: `/codex/04-architecture/shard-level-failure-isolation.md`

execution: owner: harsh-slot-9 (Phase 1 lst_rates hardening) + TBD sweep (Phase 2) cadence: one-shot (Phase 1 before
B-015 re-smoke; Phase 2 within next cycle) verifier: QG green + re-smoke with zero phantom rows in manifest (4-pillar
check) last_executed: NEVER

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED **Triaged by**: slot-8 triage sweep **Reason**: Resolved 2026-05-16; MTDS@f657431 + c1e6963
hardened
