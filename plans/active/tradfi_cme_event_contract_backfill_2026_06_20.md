---
title: "TradFi CME event-contract Phase 0 catalog backfill + manifest legacy-blank apply-flips"
parent_epic: tradfi_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/tradfi_master.md
  - ./tradfi_manifest_canonicalisation_2026_06_01.md
  - ../archive/2026_05/cme_polymarket_arb_2026_05_08.md
---

> **Provenance**: extracted 2026-06-20 from the inline `tradfi_master` epic body during the asset-group-umbrella
> restructure (the L0 umbrellas had accumulated ~stale May-07/08 inline todos that the backlog regen
> `regen_backlog_from_plan.py` never scans — it only reads `plans/active/*.md`, never `plans/epics/`). This plan is the
> **genuinely net-new, unowned** CME event-contract Phase-0 catalog backfill (epic L536–545), which unblocks the
> archived CME↔Polymarket arb sub-plan's Phases 1-5. It also absorbs the small genuine residual TradFi manifest
> legacy-blank `--apply-flips` VM run (epic L386, scan already complete with 0 uncertain cases). Broader TradFi manifest
> / source / canonicalisation work is owned separately by
> [`tradfi_manifest_canonicalisation_2026_06_01.md`](./tradfi_manifest_canonicalisation_2026_06_01.md) — do NOT
> duplicate that here.

## Context

The `cme_event_contracts_cross_venue_arb_shard_design_2026_05_08` design RFC (26KB, archived) was operator-split
2026-05-08 into Option (a): **Phase 0 (catalog backfill — the unblocking move) lands in tradfi_master scope**, and
Phases 1-5 (structural fixes spanning UAC + MTDS + strategy-service + execution) land in the archived
[`cme_polymarket_arb_2026_05_08`](../archive/2026_05/cme_polymarket_arb_2026_05_08.md) sub-plan. Phase 0 was carried as
an OPEN inline `- [ ]` in the epic body but, because the backlog regen never scans `plans/epics/`, it was never
dispatched. This plan makes Phase 0 a dispatchable active plan.

It also carries the single genuine residual from the TradFi manifest legacy-blank scan (epic L386): the scan-only run
(Gate 3, 2026-05-17) confirmed the upgrade logic correct with **0 uncertain cases** — only the `--apply-flips` VM run
remains (5,099 `empty_confirmed/SOURCE_RETURNED_ZERO → attempted_failed/LegacyBlankErrorReasonError` + 113
`SOURCE_RETURNED_ZERO → EXPECTED_PARTIAL_HALF_DAY`). This is a small bounded operational run, included here to keep it
least-duplicative rather than spinning a separate one-item plan.

## P0 — CME event-contract Phase 0 catalog backfill

- [x] ✅ [AGENT] [SCRIPT] P0. **Phase 0 — TradFi instruments-service backfill VM** for the 9 CME event-contract roots (ECES / ECBTC
      / ECRTY / ECYM / ECGC / ECCL / ECNG / EC6E / ECNQ — full list in the archived RFC). VM launcher under
      `deployment-service/scripts/vm/launch-tradfi-event-contract-backfill.sh` (per CLAUDE.md launcher SSOT rule). Range
      `[2025-09-28, today]` (the listing window for the early roots; later roots have later listing dates per the
      archived RFC's Phase 0 detail). Source: Databento metadata endpoint + per-day OHLCV. Writes to the existing tradfi
      instruments path (no new path). Verify STARTED + ≥1 progress/hour + STOPPED/FAILED at exit per the no-fire-and-
      forget rule; verify at T+10min (registry heartbeat + `gcloud instances describe` = RUNNING).
      — 2026-06-16: launcher created at deployment-service/scripts/vm/launch-tradfi-event-contract-backfill.sh,
      dry-run verified. VM launched: see task -001 evidence.
- [x] ✅ [AGENT] [SCRIPT] P0. **Register the VM prefix** `tradfi-event-contract-backfill-` in `vm_zombie_watchdog.py`
      `VM_PREFIX_TO_BUCKET` (per CLAUDE.md VM-naming-convention rule), with a `lifecycle_class` — register BEFORE the
      first launch (a launcher whose prefix is not in the map is invisible to the zombie watchdog).
      — 2026-06-16: registered in vm_zombie_watchdog.py with `_INSTR_TRADFI` bucket + `EPHEMERAL_BATCH` lifecycle; committed in deployment-service@6de9aa3.
- [ ] [VERIFY] P0. Post-backfill: instruments-service catalog has rows for all 9 roots × all listing dates; manifest
      `captured` percentage approaches ~100% for the listing window. Confirm via direct manifest query (not assumed).
      Once verified, the archived CME↔Polymarket arb sub-plan's Phases 1-5 are unblocked.

## P0 — TradFi manifest legacy-blank apply-flips (residual)

- [ ] [SCRIPT] P0. **TradFi 5,212 legacy-blank apply-flips run** —
      `reconcile_legacy_blank_to_typed_reason --asset-group tradfi --apply-flips` on a same-region VM. The scan-only run
      (Gate 3, 2026-05-17) confirmed upgrade logic correct (0 uncertain cases): 5,099 rows
      `empty_confirmed/SOURCE_RETURNED_ZERO → attempted_failed/LegacyBlankErrorReasonError` + 113 rows
      `SOURCE_RETURNED_ZERO → EXPECTED_PARTIAL_HALF_DAY`. Safe to apply. Use `launch-manifest-recon-all-vm.sh` with the
      `--apply-flips` variant or a dedicated VM; verify the post-run manifest distribution matches the scan-predicted
      counts. **MIGRATED FROM: `plans/active/gate_3_phantom_audit_runbook_2026_05_13.md`** (§ "TradFi Side-Finding"),
      via the inline `tradfi_master` epic body (L386).

## Success criteria

- All 9 CME event-contract roots backfilled to instruments-service catalog across their listing windows; manifest
  `captured` % ≈100% for the window; Phases 1-5 of the archived CME↔Polymarket arb sub-plan unblocked.
- VM prefix registered in `VM_PREFIX_TO_BUCKET` before launch; the VM emitted STARTED + progress + STOPPED.
- The 5,212 TradFi legacy-blank rows are flipped to their typed reasons on real GCS manifest data; post-run distribution
  matches the scan prediction (5,099 + 113); zero rows left with a blank/legacy reason.
- `bash scripts/quality-gates.sh` green on any `deployment-service` / `instruments-service` change (launcher,
  watchdog-map) before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the backfill VM runs to completion on
real infra with manifest-verified rows; the apply-flips run executes on a same-region VM and the post-run manifest
distribution is verified, not assumed.
