---
doc_type: plan
title: tradfi satellite AO dispatch batch 16 — 2026-08-17
summary: >-
  Extraction batch from the tradfi tranche's 2026-08-17 /na-eligibility-audit sweep (dispatch agt-071b5c) — 8
  conflict-cleared, bounded/deterministic items pulled from tradfi_reconciliation_2026_08_17_findings_2026_08_17.md
  (the post-full-backfill reconciliation checkpoint's residual findings). One item from that source doc (the
  multi-token equity symbol join-convention design call) was deliberately NOT extracted — stays NA, a genuine
  judgment call with no existing corpus precedent to apply mechanically, despite the source doc's own
  "Recommended decision" section framing it as bounded. Conflict-checked against every existing active
  batch/finalize plan for this tranche (batch9 x2, batch12, batch13, batch15) and the tradfi consolidated closeout —
  2 near-hits found and confirmed different ground (tradfi_phase_d_terminal_gate_2026_07_24.md is this source doc's
  own parent, already pointing back here; batch13's KRW-USD pipeline_mode restamp is a different axis, already-done,
  explicitly scoped to one FX pair) — no item here duplicates ground an existing dispatched todo already claims.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service, unified-api-contracts]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, na-eligibility-audit]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md,
    /plans/audit/results/data_pipeline_reconciliation_tradfi_2026_08_17.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
sequential: true
context_scope:
  [
    /plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/non-canonical-path-inventory.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
source: >-
  Drafted by the 2026-08-17 /na-eligibility-audit tradfi-tranche scheduled dispatch (dispatch agt-071b5c). Authored
  status: active directly per the skill's Phase 3 "the parent skill's own verdict IS the operator decision that
  flips the draft gate" rule (na-eligibility-audit, unlike ag-closeout-audit, is authorized to apply).
---

# tradfi satellite AO dispatch batch 16 — 2026-08-17

> Every todo below was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call)
> by the 2026-08-17 `/na-eligibility-audit tradfi` sweep (dispatch agt-071b5c) and conflict-checked against every
> existing active batch/finalize plan for this tranche before being drafted here. One item from the source doc (a
> multi-token equity symbol naming-convention decision) was deliberately excluded — no existing corpus precedent,
> a genuine design call, stays `assigned_vm: NA` in the source doc.
>
> **`sequential: true`** — Todo 4 and Todo 8 both edit `/codex/02-data/non-canonical-path-inventory.md` (a
> disposition line each); serialized to avoid a concurrent-edit collision on that one shared file, per this
> workspace's "concurrent todos MUST touch different files" rule.

## Todos

- [x] ✅ [DATA] P1. **Root-cause + fix the FX `ohlcv_24h` `source=databento` mis-stamping** — market-tick-data-service@81f5fb8f
      (regression test proving the write-path is already correct at both call sites; no further code change
      needed) + data repair executed live: 1,008 rows across 667 days — physical GCS objects moved
      `pipeline_mode=batch_databento` → `batch_yahoo` (copy+verify+delete, delete-safety-gated) and manifest
      `pipeline_mode`+`source` both restamped via a snapshot-first CAS write, self-verified 0 remaining. Root
      cause + full evidence + the flagged KRW-USD regression concern (operator-resolved 2026-08-17 option A,
      same repair pattern applied to 1,947 KRW-USD rows, self-verified):
      `/plans/archive/2026_08/issues/tradfi_fx_ohlcv24h_databento_writepath_misplacement_2026_08_17.md`. Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 1.

- [ ] [DATA] P2. **Finish the FX manifest `instrument_id` "ticks"-literal backfill residual** (670 rows, down from
      983 on 07-24 — the 2026-08-04 restamp `market-tick-data-service@c86016f6` raised well-formed FX manifest ids
      from 0% to 72.4% but did not cover this sub-population). Extend the existing restamp mechanism or run a
      targeted follow-up CAS-apply. Done when: 0 rows carry the literal `"ticks"` bundle-filename leak in the FX
      manifest `instrument_id` field, or a documented remainder with root cause if some genuinely can't resolve.
      (repo: market-tick-data-service) Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 2.

- [ ] [DATA] P1. **Re-measure `_quarantine/` with an uncapped, time-boxed VM walk and identify the feeding
      process.** Three consecutive reconciliation runs (07-21, 07-24, 08-17) have re-flagged growth (146,288 ->
      >=400,000 -> >=500,000, this run's 500K enumeration cap hit in 41s without exhausting its 60s budget, meaning
      the true population is materially above 500K) without an uncapped measurement or feeder-process investigation
      ever happening. **Heavy-I/O rule applies — launch a VM** (`/codex/05-infrastructure/vm-launcher-runbook.md`,
      SPOT default; no fire-and-forget — verify STARTED + progress + a terminal state; a >30min run needs
      `/vm-resource-rightsizing-check`); do not run this uncapped walk on the shared interactive host. Done when: an
      uncapped count is obtained, the feeding process is identified, and a disposition is recorded — either drain it
      faster (spin a tracked follow-up if that's more than this todo's own scope) or confirm the growth is a
      bounded/expected side-effect with evidence. (repo: market-tick-data-service or deployment-service) Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 3.

- [ ] [DOCS] P3. **Confirm the provenance of `_migration_backup_2026_07_25/`** (20,000+ objects / 2.35+ GB capped,
      true size likely higher; not investigated this run) and add a disposition line to
      `/codex/02-data/non-canonical-path-inventory.md` — the register-patch stanza is already drafted in
      `/plans/audit/results/data_pipeline_reconciliation_tradfi_2026_08_17.md` Phase 2; reuse it, do not re-derive.
      **Touches the same file as Todo 8 below — this batch is `sequential: true` specifically because of this
      pair.** Done when: provenance is confirmed (or documented as genuinely undetermined after a real attempt), and
      the disposition line is landed. (repo: unified-trading-pm) Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 4.

- [ ] [DATA] P3. **Root-cause the 4,142 `venue=CME, instrument_type=UNKNOWN, data_type=ohlcv_1m,
      capture_status=attempted_failed` rows** — a new census entry, not present in the 07-24 non-standard-value
      census; no captured data affected. Done when: either a classifier/capture-path bug is identified and fixed, or
      the population is confirmed a genuine non-actionable quirk (e.g. a real CME product class the classifier
      correctly can't type) with evidence recorded citing why. (repo: market-tick-data-service) Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 6.

- [ ] [DATA] P3. **Run a fresh tradfi phantom audit.** `phantom_audit_latest.json`'s published count grew 10x
      (1,635 @2026-07-14 -> 16,997 @2026-07-30) and is now 18 days stale as of 2026-08-17 — not itself evidence of a
      live defect (a published, not-re-derived number), but growth + staleness together warrant a fresh run. Done
      when: a fresh phantom-audit run completes and publishes an updated, current count. (repo:
      market-tick-data-service) Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 7.

- [ ] [DOCS] P3. **Clean up the `venue=BARCHART` manifest vocabulary residual** — 9,119 `empty_confirmed` rows,
      unchanged across 4 consecutive reconciliation runs since BARCHART's removal from
      `VENUES_BY_ASSET_GROUP["tradfi"]` 2026-06-24 (`max(attempted_at)=2026-07-07`, not re-touched since). Done
      when: the BARCHART rows are reconciled out of the live manifest vocabulary (or the corpus's standard
      disposition for a retired-venue residual is applied, per the manifest-consolidator SSOT's retired-venue
      guidance) with evidence. (repo: market-tick-data-service or unified-api-contracts) Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 8.

- [ ] [DOCS] P3. **Apply the `manifest_dedup_2026_07_10/` register-patch line** to
      `/codex/02-data/non-canonical-path-inventory.md` — proposed 2026-07-21, re-flagged 2026-07-24, re-flagged again
      2026-08-17, never applied (see the raw-tick reconciliation report's Phase 2 register-patch stanza for the
      exact line). **Touches the same file as Todo 4 above — this batch is `sequential: true`.** Done when: the
      register-patch line is landed in `non-canonical-path-inventory.md`. (repo: unified-trading-pm) Source:
      `/plans/active/issues/tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` item 9.

## Progress Log

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-071b5c): drafted alongside the source doc's
  checkbox flips, gated finalize plan authored in the same commit per the AO-dispatched finalize-plan-coverage rule.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
