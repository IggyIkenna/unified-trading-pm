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

> **🚨 OPERATOR DIRECTIVE 2026-05-20 — supersedes any "deadline-driven cutbacks"
> in this tracker**: "The data pipeline is critical to everything we do. I don't
> care about the 23rd deadline... I want every single issue that we found fully
> fixed, bad manifest data migrated, without exception... I won't accept
> anything less than perfect on this."
>
> Codified as workspace HARD RULE in CLAUDE.md § "Data Pipeline Correctness Is
> The Heartbeat" + SSOT `codex/02-data/data-pipeline-correctness-hard-rule.md`.
>
> **Operational consequence for THIS tracker**: all Phase A items (A1-A6) MUST
> land GREEN before any layer-N+1 work proceeds for the affected asset_groups.
> No `DEFERRED`. No "we'll do it after the 23rd". Closed-set deferral only via
> `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` / `BLOCKED-UPSTREAM-OUTAGE`
> with operator ack. Sub-audits A5 + A6 are part of the same gate, not optional.
>
> **Audit transparency section is mandatory** for every Phase-A deliverable —
> see [`plans/audit/results/mega_audit_phase_a_issues_human_readable_2026_05_20.md`](../../audit/results/mega_audit_phase_a_issues_human_readable_2026_05_20.md)
> § "Coverage matrix" as the canonical template.

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

- [x] ✅ **A1. Inventory script (codified-shape compliance matrix)** — 2026-05-20 slot-1 opus.
      Output: `plans/audit/results/codified_shape_compliance_2026_05_20.csv` +
      `..._summary.md`. **8,142 files scanned across 25 repos; 1,274 violating; 2,593 total violations.**
      Top checks by raw violation count: `uac_import_surface` (995), `resolve_bucket_name` (759),
      `classify_venue_error` (302), `record_emission` (215), `no_hardcoded_venue_urls` (189),
      `typed_empty_reason` (81), `has_log_upload_trap` (28), `no_hardcoded_venue_universe` (18),
      `manifest_v8` (6), `lifecycle_class` (0).
      Gap analysis (lacking QG enforcement): `typed_empty_reason`, `uac_import_surface`,
      `lifecycle_class` CI check, `manifest_v8` workspace-wide constant ratchet. These slot
      into the existing Cross-cutting QG ratchet plan (no new SSOT).

- [x] ✅ **A2. `expected_coverage()` function build + dump** — 2026-05-20 slot-1 opus.
      Function landed in `unified-api-contracts/unified_api_contracts/registry/expected_coverage.py`
      (per operator directive merge into existing scope-policy SSOT, single module).
      Composes existing UAC SSOTs: `EXPECTED_COVERAGE_BY_ASSET_GROUP` (scope) +
      `CEFI/DEFI/PREDICTION_VENUE_LAUNCH_DATES` + `CHAIN_GENESIS_DATES` +
      `US_MARKET_HOLIDAYS` + `HALF_DAY_SESSIONS`. 14 unit tests pass; basedpyright clean.
      Dump: `plans/audit/results/expected_coverage_dump_2026_05_20.parquet`
      (429,088 rows, 0.56 MiB; 70% SHOULD_HAVE_DATA, 28% NOT_YET_LIVE, 2% EXPECTED_EMPTY).
      Sidecar calendar decisions: `expected_coverage_calendar_decisions_2026_05_20.md`
      (lists 5 known gaps — sports off-seasons, DeFi protocol pauses, per-symbol axis,
      `SourceCapability.coverage_start` integration, pre-Tardis-archive windows).

- [x] ✅ **A3. Manifest divergence report** — 2026-05-20 slot-1 opus.
      Read 5 MTDS manifest indexes from prod GCS (CEFI / DEFI / TRADFI / SPORTS / PREDICTION
      buckets, `_index/availability_index.parquet`, single-walk discipline — one parquet
      per bucket). **3,968,880 manifest rows ingested.** Output:
      `plans/audit/results/manifest_divergence_2026_05_20.parquet` (1.2M joined cells)
      + `..._summary.md`. **Headline findings:**
      - **765 `DIVERGENT_EMPTY` cells** (the Drift-bug class — review-blocking) — all in DeFi.
      - **236,892 `MISSING_EXPECTED` cells** (silent gaps — review-blocking) — DeFi 184k,
        sports 25k, cefi 16k, tradfi 7k, prediction 3k. Top venues:
        - DeFi: FLUID-ETHEREUM (lending) + MORPHO-ETHEREUM/POLYGON (lending) + CURVE-ETHEREUM
          + BALANCER + UNISWAPV2 (all dex_pools/dex_swaps missing).
        - Sports: every bookmaker (BET365/BETFAIR/DRAFTKINGS/FANDUEL/ODDS_API/PINNACLE)
          missing all 2,332-day odds_snapshot/movement window.
        - Prediction: KALSHI (1,756 cells) + POLYMARKET (1,686 cells) missing trades.
        - CeFi: OKX + COINBASE + UPBIT missing trades/book_snapshot_5 backfill chunks.
        - TradFi: ICE + CME tbbo gaps, YAHOO_FINANCE ohlcv windows, NYSE/NASDAQ ohlcv_1m gaps.
      - **18,753 `ATTEMPTED_FAILED` cells** (per-row noise; check `error_reason` column for
        taxonomy). Concentrated in DERIBIT/BINANCE-FUTURES/BYBIT futures_chain/options_chain,
        ASTER (all 4 data types), HYPERLIQUID liquidations, BINANCE-FUTURES/BYBIT
        book_snapshot_5, YAHOO_FINANCE ohlcv_24h/15m.
      - **Only 44,955 `OK_CAPTURED` cells (3.66%)** — i.e. the workspace has confirmed-captured
        data on only ~4% of in-scope cells. Bulk of the gap is `MISSING_EXPECTED` (silent gaps
        the master plan hasn't yet enumerated/scheduled).

### Phase A — Diagnostics: expanded-scope additions (operator directive 2026-05-20)

The original A1/A2/A3 scope was insufficient — operator flagged 3 additional cross-cutting
audit dimensions that must land for full data-pipeline coverage. These are A-phase
(not B/C) because they're prerequisites for the Phase D plan beef-ups (the layer-N+1
work shouldn't ship if these audits are RED).

- [ ] **A4. Manifest v8 deep audit (data + code paths)**
      Two dimensions, both per-asset-group:
      - **Data side**: read each MTDS + IS manifest's `_index/availability_index.parquet`,
        group by `schema_version` column → confirm 100% are v8. Any row at v<8 is
        unmigrated data — emit a remediation cell. A1 only catches the *code* side
        (constants in source) — this catches the *data* side (rows already written
        at older schema versions that never got rewritten).
      - **Code-path side**: scan every consumer of manifest rows (MTDS handlers, IS
        orchestrator, deployment-api, features-service readers, strategy/execution
        readers) for branches that handle pre-v8 rows or are missing v8 enhanced-field
        consumers. Output: per-file v8-readiness flag (consumes_v8_enhanced_fields,
        falls_back_to_v_lt_8). Surface mixed states as **review-blocking**.
      Output: `plans/audit/results/manifest_v8_compliance_2026_05_20.csv` +
      `..._summary.md`. Owner: background agent. Estimate: 1.0 calibrated AI-day.
      Composes with: A1 (file-level v8 constant scan) + existing QG STEP for manifest
      schema-version checks. SSOT: extend existing Cross-cutting QG ratchet plan
      with the data-side ratchet step (no new SSOT).

- [ ] **A5. Dependency-data-checking + fail-propagation audit (per service × mode)**
      Every service must declare what upstream data it depends on, AND fail loudly
      when that data is missing. Two sub-dimensions:
      - **Batch mode**: pre-flight gate before each shard write. If upstream
        manifest row is missing OR `attempted_failed`, raise `DependencyError(fail_fast=True)`
        — NOT silently `record_empty()`. Audit every service's batch handler for the
        pattern. Must match `EXPECTED_UPSTREAM_EMPTY` reason taxonomy only where upstream
        is *legitimately* empty (oracle says `EXPECTED_EMPTY`) — otherwise raise.
      - **Live mode**: stream-time freshness gate. If upstream stream is stale
        (no new row in window-N), raise `StaleUpstreamError` — NOT fall through to
        zero. Audit every service's live handler.
      Per service × mode = matrix of (upstream_checked, fail_propagates_loudly,
      uses_typed_reason). Concentration on: features-service (consumes MTDS),
      strategy-service (consumes features), execution-service (consumes strategy),
      ML services (consume features). Output: `plans/audit/results/dependency_propagation_2026_05_20.csv`
      + `..._summary.md`. **MUST surface every service × mode cell that swallows a
      missing-upstream condition** (the silent-empty class on the consumer side, sister
      to A3's DIVERGENT_EMPTY on the producer side).
      Owner: background agent. Estimate: 1.5 calibrated AI-days.
      Codify the patterns as QG steps: `check_dependency_fail_propagation.py` (per
      service × mode) wired into each service's `quality-gates.sh` — operator directive
      "any issues caught should be hardened in tests that quality gates uses".

- [ ] **A6. Batch-live adapter parity audit (per venue × data_type)**
      Per CLAUDE.md "Batch = Live (CRITICAL)" — live + batch are operational modes of
      the same pipeline. For every venue × data_type with a batch adapter, there
      MUST be a live adapter (potentially from a different upstream source, but
      same schema + same manifest emission contract). Audit:
      - Enumerate batch adapters (MTDS handlers + IS handlers).
      - Enumerate live adapters (MTDS live handlers + IS live handlers).
      - Diff: every batch-only cell is a P0 gap on the live track; every live-only
        cell may be intentional (live-only data_type) or a P1 gap on the batch track.
      Output: `plans/audit/results/batch_live_adapter_parity_2026_05_20.csv` +
      `..._summary.md` with the per-(venue, data_type) matrix. **MUST list every
      batch-only adapter** so the live-rollout plan can size the gap explicitly.
      Owner: background agent. Estimate: 1.5 calibrated AI-days.
      Note: different upstream sources between batch + live is fine (e.g. Tardis for
      batch CeFi vs venue WebSocket for live CeFi) — the audit checks contract parity,
      not source identity.

**Why these aren't in the original A1/A2/A3**: A1 is *code-shape* compliance (regex
scan of source); A2/A3 are *data-availability* expected vs actual. A4-A6 are *contract-
correctness* audits — they verify that the workspace's internal contracts (manifest
schema, dependency-fail propagation, batch-live parity) hold across services + modes.

**Sequencing**: A4-A6 can run in parallel with B (template extraction) but must
finish before C (per-pair contract audits) since C consumes these. Phase D plan
beef-ups consume all of A1-A6.

### Phase B — Template extraction (small, unblocks all sibling audits)

- [x] ✅ **B1. Write `codex/04-architecture/service-contract-audit-template.md`**
      Lift the 7 reusable patterns out of `is_mtds_contract_audit_2026_05_20.md`:
      (1) SSOT-owned reference flowing down, (2) manifest emission discipline,
      (3) schema-version compliance, (4) honest-absence reason taxonomy,
      (5) expected_coverage preflight + DIVERGENT_EMPTY post-hoc check,
      (6) error classification at the boundary, (7) bucket-SSOT.
      Include: 4-dim audit matrix structure, pre-audit grep recipes, QG-ratchet
      phase shape, continuous-verification column. Owner: ikenna. Estimate:
      0.8 calibrated AI-days.
      Evidence: PM@568f757fb — 467-line template with all 7 patterns + grep
      recipes + QG-ratchet table + continuous-verification column. Unblocks
      C1–C11 audits. Shipped 2026-05-20 slot-8.

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
| C6 | features → strategy | `features_strategy_contract_audit_2026_05_20.md` | 5, 6 |  [scope addendum 2026-05-20: see below](#c6-scope-addendum-2026-05-20-per-pair-viability--pricing-ownership) |
| C7 | strategy → execution | `strategy_execution_contract_audit_2026_05_20.md` | 6 |
| C8 | execution → venue adapter | `execution_venue_contract_audit_2026_05_20.md` | 6, 7 |
| C9 | All → UAC | `uac_consumer_contract_audit_2026_05_20.md` | cross-cutting |
| C10 | All → UTL (events, manifest, cloud) | `utl_consumer_contract_audit_2026_05_20.md` | cross-cutting |
| C11 | agent-orchestrator → all | `orchestrator_service_contract_audit_2026_05_20.md` | 0 (orchestrator migration) |

- [x] ✅ **C0. Relocate** existing `is_mtds_contract_audit_2026_05_20.md` from
      `plans/active/` to `plans/audit/`. Re-source remediation P0 todos into
      the beefed `mtds_adapters_preflight_*.md` actionable plan in Phase D.
      **DONE 2026-05-20 slot-2**: `git mv` to `plans/audit/` — PM@8e3755a9d.
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
- [ ] **Cross-cutting QG ratchet plan** — beef from A1 + B1 (the 7 patterns become 7 QG steps).
      **Progress: 6/7 patterns SHIPPED as QG steps**: (a) `no_silent_absence_handlers.sh` STEP 5.70 (manifest emission),
      (b) `no_hardcoded_venue_urls.sh` STEP 5.70 (IS→MTDS URL ownership), (c) `no_hardcoded_venue_universe.sh` STEP 5.70
      (IS→MTDS universe ownership), (d) `no_adapter_contract_regression.sh` STEP 5.83 (per-file ratchet on
      `classify_venue_error|ADAPTER_FETCH_FAILED|record_captured|record_empty|record_failed`; shipped 2026-05-20 per
      `lint_sweep_774602ea8_regression_audit_2026_05_20.md`), (e) `no_legacy_schema_version.sh` STEP 5.84
      (schema-version compliance; IS@f766e5d + MTDS@c4a82a5; 2026-05-20), (f) `no_blank_empty_reason.sh` STEP 5.85
      (honest-absence reason taxonomy enforcement; IS@f766e5d + MTDS@c4a82a5; 2026-05-20). **Remaining 1 pattern**
      awaiting codification: (g) expected_coverage preflight + DIVERGENT_EMPTY post-hoc check (runtime-only; requires
      dedicated QG integration test harness — deferred to D2 plan).

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

## C6 scope addendum 2026-05-20: per-pair viability + pricing ownership

Per operator directive 2026-05-20 (when archiving `cross_asset_instruments_service_scope_2026_05_14.md`): the C6 audit must verify features-service is the implicit owner of synthetic / cross-pair viability + pricing. There is **no** separate "synthetic universe" registry; the universe is encoded in features-service's per-pair feature output.

### Scope items the C6 audit MUST cover

For each active archetype (`carry_staked_basis`, `arbitrage_price_dispersion`, sports arb when active):

1. **Universe enumeration**: features-service produces a feature stream per viable pair. Pairs absent from the stream = not in the universe at that time. Verify:
   - Per-leg data-freshness filter is wired (no stale-leg pair makes it to strategy).
   - Per-leg liquidity floor is enforced (illiquid leg → pair drops).
   - Per-leg event filter is wired (LST unwind / depeg / funding cap → pair drops).

2. **Per-pair pricing signal**: features-service emits the spread / carry / dispersion feature that strategy-service consumes for selection. Verify:
   - Feature schema includes both legs' identifiers + spread/carry value.
   - Feature is produced for ALL viable pairs, not a curated subset.
   - Feature timestamp + staleness tag is per-pair, not per-leg.

3. **Strategy-service consumes correctly**: verify strategy archetypes read the per-pair feature stream (not raw per-leg data) for selection. Banned: strategy code that re-enumerates legs from MTDS / instruments-service directly.

4. **No instruments-service `cross_asset` shard reads** in strategy-service or features-service code. The `instruments-service` venue catalogue is per-asset_group only; any synthetic-pair concept lives in features-service derivation.

### Why this matters

If features-service does NOT fully own per-pair viability, strategy-service ends up re-deriving leg-combinations from raw data — duplicating logic, missing freshness filters, producing inconsistent universe between backtest and live. The C6 audit catches this drift before live trading exposes the gap.

### Out of scope (still)

`cross_asset` as an instruments-service shard remains REJECTED. Stable synthetic-instrument identity is a separate concern (deferred indefinitely; revisit only for client-facing structured products or rebalanced-basket backtests — neither active).
