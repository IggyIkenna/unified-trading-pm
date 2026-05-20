---
title: Mega audit + plan beef-up progression tracker — 2026-05-20
created: 2026-05-20
author: ikenna (slot-1 main)
source:
  - operator directive 2026-05-20 "we got loose ends in 3+ places... done so many ai DAYS ITS UNACCEPTABLE"
  - drift S3 silent-absence bug 2026-05-19
  - 14-launcher EXIT-trap fix 2026-05-19 (deployment-service@6b4610c)
locked_by: live-defi-rollout
related_plans:
  - is_mtds_contract_audit_2026_05_20.md
  - master_to_live_defi_2026_05_23.md
---

## What this tracks

End-to-end progression of the **mega audit + plan beef-up** effort kicked off
2026-05-20. The goal is to discover the true loose-ends count (not the
plan-derived one) and turn it into a beefed-up actionable plan set that closes
the gap between "code shipped" and "live DeFi by 2026-05-23 / 2026-06-04".

## Why this is an issue-doc not a plan

This file is a **troubleshooting / coordination guide**. The actionable work
lives elsewhere:

| Output | Lands in |
|---|---|
| Diagnostic scripts + reports | `plans/audit/results/` + script output to `/tmp/` |
| Service-contract audit results (the matrix output) | `plans/audit/<pair>_contract_audit_2026_05_20.md` |
| Beefed-up actionable plans | `plans/active/<slug>.md` (new + updates to existing) |
| Codified patterns (the template doc) | `codex/04-architecture/service-contract-audit-template.md` |

This file closes when (a) all audits in `plans/audit/` are complete, AND (b)
all 8 ordering-step plans in `plans/active/` are beefed up against the audit
output. Mark `resolved: <date>` + `resolution:` block when closing.

## Terminology lock

- **`expected_coverage()`** is the locked name for the deterministic
  availability function (NOT "oracle" — collides with Chainlink/Pyth). Inputs:
  `instruments-service` catalogue + `UAC data_source_continuity` +
  known-gap calendars. Outputs: `SHOULD_HAVE_DATA | EXPECTED_EMPTY:<reason> | NOT_YET_LIVE`.
- **`DIVERGENT_EMPTY`** is the new manifest signature for "actual=0 rows but
  expected_coverage said SHOULD_HAVE_DATA" — the Drift-bug class. Review-blocking.

## Progression — ordered phases

### Phase A — Diagnostics (parallel, gates everything else)

- [ ] **A1. Inventory script (codified-shape compliance matrix)**
      Scan all repos for adherence to: log-upload trap, manifest v8 schema,
      `record_*` emission, typed `EmptyConfirmedReason`, `classify_venue_error`,
      `resolve_bucket_name`, `lifecycle_class` on VM prefixes, no hardcoded
      venue URLs, no hardcoded venue universes, UAC import-surface rule.
      Output: `plans/audit/results/codified_shape_compliance_2026_05_20.csv`.
      Owner: background agent. Estimate: 1.5 calibrated AI-days.

- [ ] **A2. `expected_coverage()` function build + workspace-wide CSV dump**
      Build the function in UAC (`canonical/crosscutting/expected_coverage.py`)
      reading instruments-service + UAC continuity + gap calendars. Dump
      `expected_coverage(asset_group, source, symbol, date)` for every cell
      since 2020-01-01. Output: `plans/audit/results/expected_coverage_dump_2026_05_20.parquet`.
      Owner: background agent (function) + ikenna (gap calendars require
      trading judgment — tradfi holidays per venue, no-fixture days per league,
      chain-reorg windows, halving epochs). Estimate: 3 calibrated AI-days.

- [ ] **A3. Manifest divergence report**
      Cross-reference current GCS manifest state against the A2 dump. Output
      two lists: `DIVERGENT_EMPTY` cells (likely adapter bugs, à la Drift) and
      `MISSING_EXPECTED` cells (silent gaps). Output:
      `plans/audit/results/manifest_divergence_2026_05_20.parquet` +
      `plans/audit/results/manifest_divergence_2026_05_20_summary.md`.
      Owner: background agent. Blocked-on: A2. Estimate: 1.5 calibrated AI-days.

### Phase B — Template extraction (small, unblocks all sibling audits)

- [ ] **B1. Write `codex/04-architecture/service-contract-audit-template.md`**
      Lift the 7 reusable patterns out of `is_mtds_contract_audit_2026_05_20.md`:
      (1) SSOT-owned reference flowing down, (2) manifest emission discipline,
      (3) schema-version compliance, (4) honest-absence reason taxonomy,
      (5) expected_coverage preflight + DIVERGENT_EMPTY post-hoc check,
      (6) error classification at the boundary, (7) bucket-SSOT.
      Include: 4-dim audit matrix structure, pre-audit grep recipes, QG-ratchet
      phase shape, continuous-verification column. Owner: ikenna. Estimate:
      0.8 calibrated AI-days.

### Phase C — Spawn sibling contract audits (post-B1, parallel)

Each audit instantiates the B1 template against its specific upstream→downstream
pair. Lands in `plans/audit/<slug>_2026_05_20.md` (NOT `plans/active/` — audits
are diagnostic outputs, not actionable until phase D digests them).

| # | Pair | Audit file | Feeds ordering step |
|---|---|---|---|
| C0 | IS → MTDS | (existing) `plans/active/is_mtds_contract_audit_2026_05_20.md` — RELOCATE to `plans/audit/` after B1 lands | 1, 4 |
| C1 | IS → features-service | `is_features_contract_audit_2026_05_20.md` | 1 |
| C2 | IS → strategy-service | `is_strategy_contract_audit_2026_05_20.md` | 1 |
| C3 | IS → execution-service | `is_execution_contract_audit_2026_05_20.md` | 1 |
| C4 | MTDS → features-service | `mtds_features_contract_audit_2026_05_20.md` | 4, 5 |
| C5 | MTDS → strategy-service | `mtds_strategy_contract_audit_2026_05_20.md` | 4, 6 |
| C6 | features → strategy | `features_strategy_contract_audit_2026_05_20.md` | 5, 6 |
| C7 | strategy → execution | `strategy_execution_contract_audit_2026_05_20.md` | 6 |
| C8 | execution → venue adapter | `execution_venue_contract_audit_2026_05_20.md` | 6, 7 |
| C9 | All → UAC | `uac_consumer_contract_audit_2026_05_20.md` | cross-cutting |
| C10 | All → UTL (events, manifest, cloud) | `utl_consumer_contract_audit_2026_05_20.md` | cross-cutting |
| C11 | agent-orchestrator → all | `orchestrator_service_contract_audit_2026_05_20.md` | 0 (orchestrator migration) |

- [ ] **C0. Relocate** existing `is_mtds_contract_audit_2026_05_20.md` from
      `plans/active/` to `plans/audit/`. Re-source remediation P0 todos into
      the beefed `mtds_adapters_preflight_*.md` actionable plan in Phase D.
- [ ] **C1–C11.** Spawn one background agent per audit. Each agent reads B1
      template + A1/A3 outputs for its rows, fills the 4-dim matrix, lands
      audit doc in `plans/audit/`. Estimate per audit: ~2 calibrated AI-days
      (template-driven, not from-scratch). Total: ~22 calibrated AI-days,
      heavily parallelisable across slots.

### Phase D — Plan beef-up (post-C, the actionable output)

For each of the 8 ordering steps, write/update the actionable plan in
`plans/active/` to absorb the audit findings. Each plan cites the audits that
feed it + lists the full remediation backlog drawn from those audits.

- [ ] **D0. Orchestrator migration plan** — beef from C11
- [ ] **D1. IS hardening plan** — beef from C0, C1, C2, C3
- [ ] **D2. UAC continuity + known-gap calendars plan** — covered by A2 (built during diagnostics)
- [ ] **D3. Manifest v8 finish + reason-enum wiring + divergence-detector plan** — beef from all C audits + A3
- [ ] **D4. MTDS adapters preflight plan** — beef from C0, C4, C5
- [ ] **D5. Features missing-data downgrade plan** — beef from C4, C6
- [ ] **D6. Strategy + execution plan** — beef from C5, C6, C7, C8
- [ ] **D7. Live adapters plan** — beef from C4, C8 (live mode rows)
- [ ] **D8. Perf upgrade plan** — beef from A1 (hot-path identification)
- [ ] **Cross-cutting QG ratchet plan** — beef from A1 + B1 (the 7 patterns become 7 QG steps)

Estimate per plan-beef-up: ~1 calibrated AI-day (audit-driven fill-in). Total:
~10 calibrated AI-days, parallelisable.

### Phase E — Execute (the ordering chain locked 2026-05-20)

This phase IS the existing dependency-ordered execution. Plans D0-D8 are now
beefed up; this is just running them.

| Order | Plan | Exit criterion |
|---|---|---|
| 0 | D0 orchestrator migration | C11 audit GREEN |
| 1 | D1 IS hardening | C0/C1/C2/C3 audits GREEN |
| 2 | D2 expected_coverage + gap calendars | A2 dump verified by ikenna |
| 3 | D3 manifest v8 + divergence-detector | all buckets v8 + detector live |
| 4 | D4 MTDS preflight | C0/C4/C5 audits GREEN |
| 5 | D5 features downgrade | C4/C6 audits GREEN |
| 6 | D6 strategy+execution | C5/C6/C7/C8 audits GREEN |
| 7 | D7 live adapters | parallel to 4; live rows GREEN |
| 8 | D8 perf | gated on 6 GREEN |

Cross-cutting: D-QG ratchet runs from end of Phase B onward, locking each
pattern as it ships.

### Phase F — Env-bucket migration + code-freeze cutover (post-E gated)

**Trigger gate**: full IS + MTDS backfill at 100% coverage on current (single)
prod buckets — verified by Phase A3 manifest-divergence dump returning zero
`MISSING_EXPECTED` cells for IS + MTDS asset-groups. Doing this split before
100% coverage forces re-backfill into new buckets — avoid.

**Per-service split policy** (ikenna directive 2026-05-20):

| Service | dev bucket | staging bucket | prod bucket | Notes |
|---|---|---|---|---|
| instruments-service | **single shared `instruments-store-*` (no env split)** | — | — | IS is the registry of truth; one bucket across all envs. Dev/staging IS reads + writes hit the same canonical store. Per ikenna: "IS needs no split — it's effectively a registry of truth." |
| MTDS | empty (ad-hoc per-developer; case-by-case populated) | **sample-mirror of prod** (date-windowed rsync) | canonical | Staging is a sample (not full mirror) for parity testing + comparison runs without re-backfill cost. Dev defaults empty; developer populates what they need. |
| features / strategy / execution / ML | TBD during Phase F | TBD | canonical | Provisionally follow MTDS pattern unless service-specific reason emerges. |

**Required changes**:
- Deployment scripts: env-aware bucket-name resolution. Partial today via
  `resolve_bucket_name()` in UTL — Phase F verifies the env dimension is wired
  through every callsite and adds the per-service split policy table to
  `deployment-service/configs/cloud-providers.yaml`.
- Code changes: per-service config consumes `CLOUD_ENV` and routes to the
  correct bucket. The IS exception (always prod-canonical bucket regardless of
  env) needs an explicit override path with a code comment + QG step asserting
  IS handlers don't accept an env-overrideable bucket arg.
- New script: `deployment-service/scripts/sync-staging-sample-from-prod.sh` —
  rsync a configurable date-window of prod MTDS → staging MTDS bucket.
  Scheduled cron or operator-triggered.
- QG enforcement: extend QG STEP 5.69 (bucket-name SSOT) with env-correctness
  assertion — each callsite must consult `CLOUD_ENV` for non-IS services.

**Why post-E (the dual-state risk)**: during partial backfill coverage,
splitting buckets means existing parquets sit in old (single) bucket while new
writes go to env-specific buckets. Reconciliation requires double-walk of GCS
which violates the workspace single-walk discipline. Wait until backfill is
100% on the single bucket, do a clean cutover with a one-shot migration.

- [ ] **F1. Gate check**: A3 divergence report returns zero `MISSING_EXPECTED`
      for IS + MTDS asset-groups across the full backfill window
      (2020-01-01..today). Until this passes, Phase F is blocked.
- [ ] **F2. Env-aware bucket-name audit** — extend A1 inventory script with an
      "env dimension wired" compliance row per `resolve_bucket_name()`
      callsite. Output: per-service env-readiness matrix.
- [ ] **F3. Cloud-providers.yaml policy table** — add the per-service split
      table above as canonical config; QG enforces consistency with code.
- [ ] **F4. IS exception path** — explicit code comment + QG step that IS
      handlers do NOT route via `CLOUD_ENV` (always prod-canonical bucket).
- [ ] **F5. MTDS staging sample-mirror script** + scheduled run + manifest
      consolidation post-mirror.
- [ ] **F6. Cutover sequence** — code-freeze window per
      `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.0 (drain
      all VMs + snapshot manifest + flip env-config + restart VMs reading new
      buckets).
- [ ] **F7. Post-cutover verification** — every service reads + writes the
      correct env bucket per the policy table; IS still hits the canonical
      shared bucket.

**Risks**:
- IS-shared-across-envs means dev/staging test runs against IS hit the prod
  registry. Acceptable per ikenna directive (it IS a registry of truth) but
  needs test-isolation review for any test that mutates IS.
- MTDS staging sample requires a freshness policy — point-in-time snapshot
  acceptable for parity testing, but the date-window needs documenting +
  re-running on schedule (or accept that staging lags prod by N days).
- Cross-asset migrations (DeFi vs CeFi vs TradFi) may need per-asset-group
  cutover windows rather than one big-bang cutover. Decision deferred to F6.

**Estimate**: ~6 calibrated AI-days. Bulk of the work is auditing every
existing `resolve_bucket_name()` callsite for env-correctness + writing the
sample-mirror script.

## Allocation guidance (background / Harsh / Ikenna)

- **Background agents**: A1, A3, B1 template instantiation, C1–C11 audit
  filling, D plan beef-up drafts, all of E mechanical work.
- **Harsh local oversight**: running diagnostic scripts, sweeping QG
  violations, paper smoke runs, manifest backfills.
- **Ikenna interactive**: A2 gap calendars (trading judgment), credential /
  wallet / paper-key fulfilment, divergence-report triage (which DIVERGENT_EMPTY
  cells are bugs vs surprises), final approval of D-plan beef-ups before
  Phase E execution.

## Close criterion

Mark `resolved` + `resolution:` block when:

1. All A1/A2/A3 diagnostic outputs exist + ikenna-reviewed.
2. B1 template doc landed.
3. All C0–C11 audit docs landed in `plans/audit/` with GREEN/RED status.
4. All D0–D8 actionable plans in `plans/active/` cite the audits feeding them
   and have absorbed the remediation backlog.
5. Phase E execution has STARTED (step 0 plan in-flight).

After close, this issue is replaced by progress on the D plans themselves;
no further bookkeeping in this file.

## Risks + traps

- **Audit sprawl**: 11 audits × full design = 55 AI-days. Template (B1) is
  the ONLY thing that keeps this tractable. Do not spawn C audits before B1
  lands.
- **Diagnostic drift**: A2 gap calendars + A3 divergence report must be
  refreshed before any Phase D plan ships, since `expected_coverage()` evolves
  as ikenna fills in calendars. Stale A3 = stale D plans.
- **Confusion between audit + plan**: keep `plans/audit/` and `plans/active/`
  strict. An audit DESCRIBES state; a plan PRESCRIBES action. Audit
  remediation P0 todos get COPIED into the corresponding D plan, not run from
  the audit doc directly.
- **CLAUDE.md inflation**: do not add `expected_coverage` or
  `DIVERGENT_EMPTY` rules to CLAUDE.md until they're shipped in code +
  enforced by QG. Premature codification = drift between doc and code.
