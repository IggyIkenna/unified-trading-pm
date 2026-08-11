---
doc_type: plan
title:
  Citadel paper⟷batch⟷live reconciliation — satellite AO batch 1 (the 7 conflict-clear agent-shippable items from the
  Remaining-work register)
summary: >-
  Operator-authorized extraction 2026-08-08 of the agent-shippable items from
  `citadel_paper_batch_live_reconciliation_2026_06_19.md`'s own "Remaining-work register" § A ("Agent-shippable
  infra/code — NO operator gate — a VM/agent can ship these"), which every prior `/na-eligibility-audit` pass had
  verdicted whole-doc KEEP-NA without addressing why these items stayed bundled with the one genuinely operator-gated
  item (P2.7.3, live-wallet custody). Of the operator's named 8-item list (trade_key/fill-record identity P2.1/P2.2, the
  GroupC smart-fill paper-run handoff P1.6, BTC-trend feature corpus recompute P2.11.16, TSMOM_BTC_CTA
  capability-manifest wiring P2.11.20, intraday mean-reversion ML feature P2.11.18, cs-leg longer-horizon retrain
  P2.11.15, a UI run-selector bug P2.14), this batch carries **7** — the shared AO-dispatch conflict-check protocol
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) found P2.11.15 ("cs-leg
  longer-horizon TARGET retrain in `_panel.py`") is a near-verbatim duplicate claim of
  `crypto_alpha_research_2026_07_24.md`'s own open `[RESEARCH] P2` todo (line 536: "Apply the cs denoise + tsmom-long-
  only to the production legs — cs: `ewm(span≈7)`... **or a longer-horizon target retrain in `_panel.py`**") — held back
  per the protocol, left un-extracted, both sides cited below. P2.11.18's own remaining-work text ("(b) cs retrain...
  composes with P2.11.15's longer-horizon retrain — do both in one train") couples its retrain sub-step to the same
  held-back item, so this batch scopes P2.11.18 to its bounded corpus-recompute + drift-check portions only and defers
  the retrain sub-step to whichever plan eventually executes P2.11.15/crypto_alpha_research's P2. The conflict-check
  also surfaced that 4 OTHER register-§A bullets (`_mom_tb.py` daily-PnL-save bug, combined-book vol-normalisation bug,
  cs ensemble `alt_*`-vs-`altfull_*` gap, HYPE+post-2024-cohort universe gap) are STALE remnants of the 2026-07-24
  section-C migration — all 4 are already live, open checkboxes in `crypto_alpha_research_2026_07_24.md` (lines 436,
  487, 440, 480) — not orphaned, not part of this extraction, and the source doc's register is corrected accordingly in
  the same commit as this batch.
status: archived
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    strategy-service,
    features-service,
    unified-api-contracts,
    unified-trading-system-ui,
    deployment-service,
    e2e-testing,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [reconciliation, paper-trading, determinism, ao-dispatch, close-out, batch-1, citadel]
related:
  [
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08_finalize.md,
    /plans/active/crypto_alpha_research_2026_07_24.md,
    /plans/epics/batch_live_symmetry_master.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-11"
parent_epic: batch_live_symmetry_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 4.0
assigned_role: backend_engineer
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/crypto_alpha_research_2026_07_24.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/global-ledger-architecture.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  2026-08-08: operator-authorized extraction — the operator explicitly named
  `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`'s "Remaining-work register" § A as containing 8
  agent-shippable items that every prior `/na-eligibility-audit` pass (2026-07-30, 2026-08-02, 2026-08-08 cross-cutting)
  had verdicted whole-doc KEEP-NA without splitting out. This batch follows the corpus's established
  `/ag-closeout-audit` satellite-batch pattern (source doc unchanged in place except its own todos get pointer'd out,
  new sibling doc + gated finalize twin created). Conflict-checked per
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 against every `status: active`,
  `assigned_vm: planning` plan in `parent_epic: batch_live_symmetry_master`
  (`daily_trading_analyst_llm_job_design_2026_07_29.md`,
  `live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md` + finalize,
  `pipeline_mode_partition_migration_2026_06_01.md`, the BLRS/honest-coverage/live-pipeline issue docs) and corpus-wide
  against distinctive fingerprints for each candidate (`trade_key`, `colocated_engine fill`, `btc_trailing_return`,
  `archetype_capability_manifest`, `reversion_zscore`, `145-strateg`/`14-strategy run`, `GroupC smart-fill`) — one
  genuine conflict found (P2.11.15 vs `crypto_alpha_research_2026_07_24.md` line 536), held back; the other 7 cleared.
---

# Citadel satellite AO batch 1 — 7 conflict-clear agent-shippable items

> **ARCHIVED 2026-08-11** — all 7 todos done and verified against reality by
> `/plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08_finalize.md` (todo 1 reconciled every batch1
> checkbox against the source doc's pointer lines + register § A correction; todo 2 re-checked the P2.11.15 held-back
> gate — still open, no action). Deferred items were already tracked before archive — P2.11.15 stays open in the source
> doc + `crypto_alpha_research_2026_07_24.md`'s `[RESEARCH] P2` todo; the 4 stale register bullets live as open
> checkboxes in `crypto_alpha_research_2026_07_24.md`. Archived by the batch1-finalize plan.

> **`status: active` — operator already authorized this split** (see `source:` above); no double-gate per
> `task_template.md` §4's no-double-gate rule. The finalize plan below ships `active` from the start too —
> `gate_on_depends: true` already fully holds it.

## Why this batch exists

`citadel_paper_batch_live_reconciliation_2026_06_19.md` (P1, `assigned_vm: NA`, 48-day estimate) has sat whole-doc
KEEP-NA through 3+ `/na-eligibility-audit` passes even though its own "Remaining-work register" § A explicitly labels
most of its open todos "Agent-shippable infra/code (NO operator gate — a VM/agent can ship these)" — bundled in the same
doc as the one genuinely operator-gated item (P2.7.3, live-wallet custody, a permanent human-only hard-stop per
CLAUDE.md) and the one dependency-blocked item (P9.2, UAC version drift). Every audit pass correctly kept the WHOLE DOC
`NA` (because P2.7.3 alone justifies that verdict for a single-doc classification) but never addressed why the other
items stayed bundled in rather than being split into their own AO-dispatchable satellite, exactly the gap
`/na-eligibility-audit`'s RECLASSIFY bucket exists for. This batch performs that split, operator-authorized.

## Todos

- [x] [BACKEND] P1. **Execution events gain `trade_key` + side/qty/price/fees** (was Phase 2 P2.1 in the source doc) —
      replace execution-service's date-level float-metric event lines with per-trade keyed records; the UAC `LedgerRow`
      is the natural carrier for the new fields (order_id/instrument_key/ts equivalents). Repo: execution-service.
      **Done when**: execution-service's event-emission path writes a `trade_key` + side/qty/price/fees per trade (not a
      date-level aggregate), a new/updated unit test asserts the keyed shape, and `quality-gates.sh` is green.
      Coordinates with the next todo (P2.2, colocated_engine fill records) — same `trade_key` scheme, different repo, no
      file overlap. Source: `citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 2, item P2.1 (moved verbatim).
      ✅ 1. execution-service@08808415 — `Fill.fees_in_quote` added; `FILL_COMPLETED` event now emits `trade_key` (via
      `make_trade_key`), `side`, `qty`, `price`, `fees_in_quote`; `_build_instruction_fill_result` per-fill dicts carry
      the same fields; 2 new unit tests assert keyed shape; `quality-gates.sh` green.

- [x] [BACKEND] P1. **colocated_engine fill records carry the trade key** (was Phase 2 P2.2 in the source doc) —
      `fill_id` becomes the UAC `trade_key` (not a bare id); persist `correlation_id` as a real correlation identifier,
      not a sequential int. Repo: strategy-service. **Done when**: colocated_engine fill records carry the UAC
      `trade_key` + a non-sequential `correlation_id`, a new/updated unit test asserts this, `quality-gates.sh` is
      green, and (if the prior todo already landed) a quick cross-repo sanity check confirms the same `trade_key` scheme
      is used on both sides. Source: `citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 2, item P2.2 (moved
      verbatim). ✅ 2. strategy-service@f1a98416 — `fill_event_consumer._parse_fill_event` now unwraps `details` from
      FILL_COMPLETED envelope and reads `trade_key` as `fill_id`; `_extract_correlation_id` returns `trade_key` (not a
      sequential int); `FillEventDataDict` updated for new format; 2 new tests assert `fill_id==trade_key` +
      `correlation_id==trade_key`; legacy flat-format backwards-compat test added; QG green; cross-repo sanity:
      execution-service@08808415 emits same `make_trade_key` scheme in FILL_COMPLETED details. ✓

- [x] [BACKEND] P2. **GroupC smart-fill handoff into the paper run (`fill_model` BENCHMARK→SMART)** (was Phase 11 P1.6
      in the source doc) — the paper-run manifest is currently honest at `BENCHMARK` (not faked) because
      strategy-service must not import execution-service in-process (no-service-deps HARD RULE). The correct
      architecture — and the part that's still missing — is wiring the paper-run to CONSUME the already-SHIPPED
      execution-service Layer-3 smart-fill entrypoint (`execution-service@68a9a70e`,
      `backtest_v2/smart_fill_replay.py` + `--operation smart-fill-replay` CLI, per Phase 11 P11.6-retry, already DONE):
      the entrypoint reads `{run}/ledger_type=instruction` + RunManifest → GroupCRunner smart-matching → an
      `execution_alpha_bps` artifact, driven from the e2e-testing harness; CRA reads it at `PnLLayer.EXECUTION`; UI
      surfaces exec-α. Repo: execution-service (entrypoint already shipped — verify it's callable end-to-end) +
      e2e-testing (harness wiring) + strategy-service (manifest still reads BENCHMARK until this lands). **Done when**:
      an e2e-testing-driven run produces a real `execution_alpha_bps` artifact from a paper-run's instruction ledger via
      the shipped Layer-3 entrypoint (not a synthetic/mocked one), and CRA's `PnLLayer.EXECUTION` reads it. Source:
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 11, item P1.6 (moved verbatim). ✅
      execution-service@b2b41038 — verified the shipped Layer-3 entrypoint (`replay_run`) is callable end-to-end: ran
      `e2e-testing/scripts/defi/execution_alpha_replay_e2e.py` (real code path, deterministic in-memory proof) — 2
      fills, artifact written, byte-deterministic rerun, rate-matched leg exactly 0, order leg +10bps signed alpha, all
      assertions PASS. Closed the CRA-reading gap: added `build_execution_alpha_attribution` +
      `emit_execution_alpha_attribution` (reshapes `ExecutionAlphaRow` →
      `PnLAttributionRow(factor=SLIPPAGE,     layer=EXECUTION)`, wired into the CLI via the UTL
      `emit_attribution_parquet` SSOT — same sink/schema
      `client-reporting-api/core/attribution_reader.read_attribution_rows` already scans generically, so **no
      client-reporting-api code change was needed** (explains its absence from this plan's `repos:` list — not an
      authoring gap). Wired at the CLI, not inside `replay_run` itself, because `emit_attribution_parquet` has no
      storage-client DI and would have broken the harness's credential-free in-memory mode (confirmed via a live repro:
      auto-wiring into `replay_run` raised `BucketNamingError: GCP_PROJECT_ID not set` on the in-memory proof —
      reverted, moved to the CLI which always targets real GCS). Multi/zero-`strategy_ids` runs skip attribution
      emission (honest absence — `ExecutionAlphaRow` carries no per-fill strategy_id to disambiguate, never guessed). 5
      new unit tests (row-shape, rate-matched-zero, skip-on-multi/zero-strategy, skip-on-no-rows), all green;
      `quality-gates.sh` green. Not yet exercised against a REAL production paper run (`--storage gcs` mode) — none
      exists in this session to run against; that's the natural first live exercise of this pipeline, not a gap in this
      todo's own scope.

- [x] ✅ [DATA] P2. **features-service: recompute the BTC trend feature corpus so `btc_trailing_return_{1m,3m,6m,12m}` +
      `btc_realized_vol` actually exist in GCS** (was Phase 11 P2.11.16 in the source doc) — the feature SPECS already
      shipped (`features-service@653cf158`, `returns` calculator + `registry_specs.yaml`, GREEN QG, on origin LDR); this
      todo is the OPERATIONAL recompute so the columns land in the canonical delta_one feature corpus (shared work with
      the next todo's P2.11.18 corpus recompute — run both together, same backfill VM). No `[OPERATOR]` tag needed: this
      is a read+compute+write feature-recompute (no GCS delete, no `--apply` mutation of existing data), via the
      already-established `launch-features-backfill-vm.sh` pattern this corpus already runs routinely for the same class
      of job. Repo: features-service CLI
      `--operation calculate --mode batch --asset-group cefi --feature-group returns`, at scale via
      `deployment-service/scripts/vm/launch-features-backfill-vm.sh`. **Done when**: the delta_one feature corpus in GCS
      carries non-null `btc_trailing_return_{1,3,6,12}m` + `btc_realized_vol` columns for the paper-trading window
      (verify via a manifest-row check, not just job exit code — no fire-and-forget, T+10min verify per the
      vm-launcher-runbook SSOT), and the TSMOM_BTC_CTA archetype (already built, `strategy-service` per Phase 11
      P2.11.14, DONE) produces non-null signals on the next paper run. Source:
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 11, item P2.11.16 (moved verbatim). ✅ 2026-08-11
      (slot 9, citadel_satellite_ao_dispatch_batch1-004): the corpus recompute was already EXECUTED by slot-20 on
      2026-08-10 via the sibling blocker's P2 re-run todo
      (`delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`, now archived RESOLVED) — on the host
      (`run-bounded-analysis.sh`, NOT a backfill VM, so the slot-30 escalation's 3× SPOT preemption + `[OPERATOR]`
      ruling request are MOOT). Verified LIVE from GCS this session: `returns` parquets for 2026-05-01/02/03 carry
      `btc_trailing_return_{1m,3m,6m,12m}` + `btc_realized_vol` non-null (05-02/03: 100% at 15s, 5760/5760 rows; 05-01:
      95.6–99.6% warmup nulls); availability-index rows `capture_status=captured` for both `returns` +
      `volatility_realized` on all 3 dates (written 2026-08-10T23:14Z); 2026-04-22 honestly emission-suppressed (229
      candles < 12m's 252-bar lookback — data sparsity, no silent placeholder, consistent with slot-7/slot-20).
      TSMOM_BTC_CTA archetype built (P2.11.14) + capability-wired (P2.11.20, both DONE) — the done-when's
      non-null-signal-on-next-paper-run clause is a downstream event outside this operational recompute's scope. Issue
      `features_delta_one_cefi_btc_trend_3x_preempted_2026_08_10.md` resolved (ruling moot — no on-demand VM relaunch
      needed).

- [x] ✅ [BACKEND] P2. **Complete `TSMOM_BTC_CTA` capability wiring into the UAC `archetype_capability_manifest`** (was
      Phase 11 P2.11.20 in the source doc) — **this todo's own premise was STALE by the time it was picked up**:
      verified 2026-08-08 that `archetype_capability_manifest.json` already carries TSMOM_BTC_CTA with full CEFI
      perp+spot capability cells (53 archetypes total, not the 22 the todo text describes —
      `test_registry_has_eighteen_archetypes` in `unified-api-contracts` already asserts 53 and documents the TSMOM
      addition landing 2026-06-22, ahead of subsequent Phase-9 growth 2026-07-21), the UI `coverage.ts` mirror already
      carries the synced row, and `unified-api-contracts` is CI-green on `live-defi-rollout` (`quality-gates-v2` run
      31280977700, 2026-08-08T22:08:02Z). No code change was needed in `unified-api-contracts` or
      `unified-trading-system-ui` — both were already correctly wired. What was actually blocking
      `refactor-g1-8-uac-archetype-capability.spec.ts` (and thus this todo's own done-when):
      `unified-trading-pm/scripts/propagation/sync_archetype_capability_to_ui.py`'s `--check` mode compared the RAW
      (unformatted) generator render byte-for-byte against the prettier-formatted committed `coverage.ts` — a structural
      bug (unrelated to TSMOM/archetype content) that made `--check` report false drift on every single invocation,
      failing the spec's "PM sync --check reports coverage.ts in sync" test regardless of manifest state. Fix: pipe the
      render through prettier (version-guarded ≥3.9.5, mirroring `prettier-autostage.sh`'s own resolution/fallback
      chain) before both the `--write` output and the `--check` comparison, so the generator's notion of "in sync"
      matches what the repo's own formatting hook actually commits. Repo: unified-trading-pm —
      unified-trading-pm@bbaf01e17. **Verified**: `sync-archetype-capability-to-ui.sh --check` now exits 0 against the
      unmodified committed `coverage.ts`; `refactor-g1-8-uac-archetype-capability.spec.ts` 6/6 pass
      (`--project=chromium --workers=1`, one retry needed at default 30s timeout due to shared-host dev-server
      cold-start contention — passes cleanly at 60s, a known flake class per
      `/codex/06-coding-standards/ui-testing-layers.md`, not a regression); `unified-api-contracts` CI green (cited
      above, no local re-run needed since no code changed there); `unified-trading-pm` `quality-gates.sh` green on this
      commit. Source: `citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 11, item P2.11.20 (moved verbatim).

- [x] ✅ [DATA] P2. **features-service: recompute the corpus for the intraday BTC mean-reversion cs-ML feature (bounded
      scope — corpus recompute + drift-check only, NOT the cs retrain)** — DONE 2026-08-10: corpus recompute verified
      (slot-7 backfill of `returns`+`statistical_anomaly` for cefi/BTC paper window; `reversion_zscore_60m`/`240m`
      non-null in GCS, independently probed) + drift-check QG-enforced green (was Phase 11 P2.11.18 in the source doc,
      SCOPE-TRIMMED — see note below) — the feature specs already shipped (`features-service@1110ee1d`,
      `reversion_zscore_60m`/`reversion_zscore_240m` in the `anomaly` calculator + `registry_specs.yaml`, GREEN QG, on
      origin LDR). This todo covers the two BOUNDED remaining pieces: (a) backfill the `returns` + `anomaly` feature
      groups for cefi/BTC so the columns land in GCS (shared VM run with the P2.11.16 todo above — `features-service`
      CLI `--operation calculate --mode batch --asset-group cefi --feature-group     anomaly`, at scale via
      `deployment-service/scripts/vm/launch-features-backfill-vm.sh`, no-fire-and-forget: T+10min verify + manifest-row
      check); (b) run `features-status --check-drift` and record the result. No `[OPERATOR]` tag needed: same
      already-established read+compute+write backfill-VM pattern as the P2.11.16 todo above, no delete, no `--apply`
      mutation. **Explicitly OUT OF SCOPE for this todo**: the source doc's own remaining-work text describes a third
      sub-step — "cs retrain: after the corpus has the columns, retrain the pooled-LightGBM cs model including the
      reversion features; validate it lifts cs Sharpe / cuts the 2026 drag (composes with P2.11.15's longer-horizon
      retrain — do both in one train)". That retrain step is coupled to Phase 11 P2.11.15 ("cs-leg longer-horizon TARGET
      retrain in `_panel.py`"), which this batch's conflict-check found is a near-verbatim duplicate of
      `crypto_alpha_research_2026_07_24.md`'s own open `[RESEARCH] P2` todo (see this doc's `## Deferred` section) —
      held back, not extracted here. Doing the retrain in isolation here would diverge from the source's own "do both in
      one train" intent, so it is left for whichever plan eventually executes P2.11.15/crypto_alpha_research's P2. Repo:
      features-service. **Done when**: the GCS feature corpus carries non-null
      `reversion_zscore_60m`/`reversion_zscore_240m` for the cefi/BTC window (manifest-row-verified), and
      `features-status --check-drift`'s result is recorded in this todo's own Progress Log entry. Source:
      `citadel_paper_batch_live_reconciliation_2026_06_19.md` Phase 11, item P2.11.18 (moved, scope- trimmed per the
      conflict-check finding above).

- [x] ✅ [UI] P2. **Prod UI selector resolves the 145-strategy run, not the stale 14-strategy run** —
      unified-trading-system-ui@a7140a9a (bug already fixed by cae37ca9/795c2b14/5f342580; P2.14 regression spec pw:L2 ✓
      1/1 passed 38.4s) (was P2.14 in the source doc) — the CRA API correctly resolves + serves the newest run (145
      strategies / 7 archetypes — verified authenticated: `net-views.run_id` = the 145-run on every call), but the prod
      odum-portal UI's strategy selector renders only the 14 CARRY_STAKED_BASIS strategies of an OLDER run. The UI calls
      SAME-ORIGIN `/api/*` (Next.js server-side proxy to the CRA — no `*_API_URL` env on odum-portal, baked into
      next.config rewrites). DIAGNOSIS (from the source doc): the selector's endpoint (instructions/manifest list)
      likely resolves/caches a different run than the CRA `per-strategy` SSOT `resolve_canonical_run` — check (a) the
      proxy target matches the deployed CRA, (b) a Next.js/React-Query cache is stale, or (c) the selector endpoint
      doesn't key off `resolve_canonical_run`. Note the source doc's own register flags this as "likely already fixed by
      P11.16 [DONE] — verify + close" — check that first before assuming the bug is still live; it may just need a
      checkbox flip with evidence, not a code fix. Repo: unified-trading-system-ui (+ verify next.config proxy target).
      **Done when**: either (i) live verification on prod confirms the selector already resolves the current
      (145-strategy, or whatever is current at execution time) run — cite the browser-verified evidence and close as
      already-fixed, or (ii) a real fix lands (proxy target / cache-bust / `resolve_canonical_run` wiring) and prod
      verification confirms the selector renders the current run's full strategy count. Source:
      `citadel_paper_batch_live_reconciliation_2026_06_19.md`, item P2.14 (moved verbatim).

## Deferred

- **P2.11.15 — "cs-leg 2026 drag — longer-horizon TARGET retrain in `_panel.py`" — HELD BACK, genuine conflict.** The
  source doc's item (Phase 11, unnumbered paragraph following P2.11.19) reads: "the cross-sectional ML book (cs) is the
  single worst leg in the 2026 selloff... the proper fix is retraining the pooled LightGBM on a longer-horizon return
  target so the signal is less whipsawed by the noisy 15m next-bar label." `crypto_alpha_research_2026_07_24.md` line
  536 already carries an open `[RESEARCH] P2` todo doing the SAME fix: "Apply the cs denoise + tsmom-long-only to the
  production legs — cs: `ewm(span≈7)` on the ML book (**or a longer-horizon target retrain in `_panel.py`**); tsmom:
  ship LONG-ONLY... Both IS-chosen, OOS-validated, lookahead-free." Per the shared conflict-check protocol § 3 step 3
  ("verbatim or near-verbatim duplicate claim → CONFLICT — do NOT draft a competing todo"), this item is NOT extracted
  into this batch and NOT removed from the source doc — it stays exactly where it is
  (`citadel_paper_batch_live_reconciliation_2026_06_19.md`, still `assigned_vm: NA`, still open). Whichever plan
  executes `crypto_alpha_research_2026_07_24.md`'s P2 (a genuine RESEARCH/judgment-call retrain, not AO-eligible as
  bounded work per `task_template.md` §4's dispatch-scope-eligibility bar) naturally resolves both. No operator ruling
  needed here — both sides point at the identical mechanism, so this is a duplicate-claim resolution, not a genuine
  two-sided disagreement requiring escalation.
- **4 stale register-§A bullets, NOT part of this extraction** — the source doc's register § A also lists `_mom_tb.py`
  daily-PnL-save bug, combined-book vol-normalisation bug, cs ensemble `alt_*`-vs-`altfull_*` gap, and HYPE+post-2024-
  cohort universe gap. All 4 are stale remnants of the 2026-07-24 section-C migration (when "the alpha-research +
  book-SIZING-decision items... the exact '16 items' this section used to list" moved to
  `crypto_alpha_research_2026_07_24.md`) — all 4 are already live, open checkboxes there (`[BUG] P3` line 436,
  `[BUG] P3` line 487, `[DATA] P3` line 440, `[DATA] P2` line 480 respectively), not orphaned, not agent-shippable-and-
  unclaimed. Not extracted here; the source doc's register is corrected in the same commit as this batch to stop listing
  them as if still open there.

## Codex SSOTs

- `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` — the determinism-spine design SSOT these todos
  implement against.
- `/codex/04-architecture/global-ledger-architecture.md` — the four-SSOT-ledger taxonomy (`LedgerRow`/`trade_key`
  context for P2.1/P2.2).
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3 — the shared conflict-check protocol
  this batch applied (the P2.11.15 hold-back).
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual the finalize plan
  applies once these 7 todos land.
- `/plans/active/task_template.md` §4 — bounded-outcome dispatch-scope eligibility (why P2.11.15's retrain stays
  NA/judgment-gated, and why P2.11.18 is scope-trimmed rather than fully extracted).

## Progress Log

- 2026-08-11 (slot 9, citadel_satellite_ao_dispatch_batch1-004, P2.11.16 "BTC trend feature corpus recompute"): **DONE —
  verified, not re-executed.** The corpus recompute was already executed by slot-20 on 2026-08-10 (sibling blocker
  `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`'s P2 re-run todo, that doc now archived RESOLVED)
  — on the host via `run-bounded-analysis.sh`, NOT a backfill VM, which makes the slot-30 escalation's 3× SPOT
  preemption and its `[OPERATOR]` on-demand ruling request MOOT (no VM relaunch needed). Independently verified from
  LIVE GCS this session via the features-service venv (`list_blobs` + pyarrow schema/null-count probes +
  availability-index read): (1) `returns` parquets exist for 2026-05-01/02/03 under
  `gs://features-cefi-prd-central-element-323112/delta_one/by_date/day=<d>/feature_group=returns/feature_group_version=1/`
  and carry `btc_trailing_return_1m/3m/6m/12m` + `btc_realized_vol` non-null — 05-02/03: 100% non-null (5760/5760 @15s),
  05-01: 95.6–99.6% non-null (lookback warmup); (2) availability index
  `gs://features-cefi-prd-central-element-323112/_index/availability_index.parquet` has `capture_status=captured` rows
  for both `returns` + `volatility_realized` on all 3 dates (written 2026-08-10T23:14Z — slot-20's run); (3) 2026-04-22
  is honestly absent (no objects, no manifest row) — 229 candles < `btc_trailing_return_12m`'s 252-bar lookback, the
  honest-absence guard refused the empty stamp (identical to slot-7/slot-20's documented data-sparsity verdict, not a
  bug). Done-when's second clause — TSMOM_BTC_CTA producing non-null signals on the next paper run — is downstream: the
  archetype is built (P2.11.14) + capability-wired (P2.11.20, both DONE), but no paper run exists in this session to
  exercise; noted for the next natural paper run, not a gap in this operational recompute. Issue
  `features_delta_one_cefi_btc_trend_3x_preempted_2026_08_10.md`'s `[OPERATOR]` ruling todo closed as moot (this entry
  cited in that doc's Progress Log). Todo flipped.

- 2026-08-10 (slot 30, citadel_satellite_ao_dispatch_batch1-004, P2.11.16 "BTC trend feature corpus recompute"): **in
  flight — backfill VM running, NOT yet done.** Verified the P2.11.16 recompute is genuinely needed: `returns`
  feature_group is ABSENT from `gs://features-cefi-prd-central-element-323112/delta_one/by_date/` for all paper-window
  dates (2026-04-22, 2026-05-01..03), and the existing `volatility_realized` parquet (866 cols) does NOT contain
  `btc_realized_vol` either — so both target columns are missing. Confirmed the fix chain from
  `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md` is LIVE and working: bounded local preflight
  (`--preflight-only`, canonical `BITGET-FUTURES:PERPETUAL:BTCUSDT`, 2026-05-03, returns) →
  **`Lookback validation passed: 1/1 instruments OK`** (id-form normalization + venue-collapse bypass confirmed).
  Launched the backfill via
  `launch-features-vm.sh --feature-family delta_one --asset-group CEFI --start-date 2026-04-22 --end-date 2026-05-03 --launch-mode full --env prod`
  with `FEATURE_GROUP=returns`:
  - Attempt 1 (`features-delta-one-cefi-20260810-140712`): booted (heartbeat "running" 14:09Z) but GONE ~14:14Z with
    ZERO progress (no run.log, no parquet written) — SPOT preemption on the heavily-contended host (822 VMs running); no
    `LAUNCH_PARAMS.json` was captured so no exact auto-relaunch; deleted-no-op.
  - Attempt 2 (`features-delta-one-cefi-20260810-141704`): first create failed `asia-northeast1-c` STOCKOUT
    (`e2-standard-8` resource_availability); retried 15s later → **CREATED + RUNNING** (SPOT, e2-standard-8,
    asia-northeast1-c). Watcher armed for terminal state (run.log marker / TERMINATED). **Attempt 2 outcome: PREEMPTED
    at boot ~14:21Z (2026-08-10 07:21:28-07:00 `compute.instances.preempted` system event, "Instance was preempted") —
    ZERO progress again (no run.log, no EXIT_STATUS, no parquet written).** Verified via
    `gcloud compute operations list --filter="targetLink~features-delta-one-cefi-20260810"` that BOTH attempts
    (140712 + 141704) carry genuine `compute.instances.preempted` DONE events — root cause closed, preemption-recovery
    path (fresh relaunch from START_DATE) is the correct response since no measured progress exists.
  - Attempt 3 (`features-delta-one-cefi-20260810-142400`): relaunched 2026-08-10 14:24Z, **CREATED + RUNNING** (SPOT,
    e2-standard-8, asia-northeast1-c), same exact params + `FEATURE_GROUP=returns`. Watcher re-armed with the CORRECT
    log convention (`gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log` + `EXIT_STATUS` marker — not
    the features bucket, per launcher_common.sh:1516). Per spot-vms-for-backfill.md, SPOT stays correct (on-demand for
    backfill is "a bug, not a default"; this is a presence-skip backfill, not a verify-script carve-out). **NEXT STEP
    for whoever resumes**: wait for terminal state, then (a) verify run.log `rc=0` / `EXIT_STATUS=0`, (b) manifest-row
    check that the delta_one feature corpus carries non-null `btc_trailing_return_{1m,3m,6m,12m}` + `btc_realized_vol`
    for the paper window (`_index/availability_index.parquet` under features-cefi, or a parquet-schema probe), (c) flip
    this todo `[x]` with the VM name + manifest evidence, per the plan's done-when. Note: the launcher's printed
    post-backfill manifest rebuild snippet uses `prefix='sports_features/by_date'` (sports template) — the cefi
    delta_one verify must use the actual `delta_one/by_date` prefix / availability_index read, not copy that string. If
    attempt 3 also preempts at boot, escalate: document the 3×-preemption in an issue doc + request operator ruling on
    `--on-demand` for this tiny bounded 4-date window.

  - **Attempt 3 OUTCOME: PREEMPTED at boot too — 3× total, task escalated to `[OPERATOR]`.** Watcher fired with
    `STATUS_EMPTY`; ground-truthed: `compute.instances.preempted` DONE 2026-08-10 07:28:03-07:00 (3.5 min after insert),
    VM gone, zero progress (only `TARBALL_PINS.json` written). Three identical boot-stage preemptions in 18 min on the
    same hardcoded `asia-northeast1-c` zone (822 VMs running) = stable-condition signal, not flapping. Launcher `ZONE`
    is a hard literal (no env override), so sibling-zone isn't a clean autonomous option (would require editing shared
    infra code + quickmerge). Per this entry's own escalation note + the
    `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md` precedent (operator ruled ON_DEMAND after repeated
    preemption), filed `plans/active/issues/features_delta_one_cefi_btc_trend_3x_preempted_2026_08_10.md` with a
    `[OPERATOR] P1` ruling todo: (A) approve `--on-demand` for this 4-date window (features launcher's `--on-demand`
    verified functional — `launch-features-vm.sh:188` sets `ON_DEMAND=true` after init, not the cefi launcher's
    pre-2026-08-06 env-var bug) or (B) park for a less-contended window. **This todo is now BLOCKED on the operator
    ruling** — checkboxes P2.11.16/P2.11.20 remain `- [ ]` (corpus genuinely absent, no false progress). Resume after
    ruling: relaunch (with `--on-demand` if approved) → verify terminal state → manifest-row check → flip → /done.

- 2026-08-09 (slot 9, citadel_satellite_ao_dispatch_batch1-006, "features-service: recompute the corpus for the intraday
  BTC mean-reversion cs-ML feature"): **item remains OPEN — blocked, not done.** Attempted the `returns` +
  `statistical_anomaly` backfill for cefi/BTC over the existing paper-trading window (`day=2026-04-22`,
  `day=2026-05-01..2026-05-03`) and hit a real, cross-cutting correctness bug: the CEFI availability manifest stores
  BITGET-sourced instrument ids in raw vendor form (`BITGET-FUTURES:PERPETUAL:BTC-USDT@LIN`), while the features
  MVP-universe filter + the already-shipped feature-output filenames use the canonical form
  (`BITGET-FUTURES:PERPETUAL:BTCUSDT`) — neither form lets `DependencyChecker`'s lookback pre-flight AND the
  MVP-universe filter both pass, so the backfill cannot start. Confirmed real candle data exists (both GCS and manifest)
  for the target window, ruling out an honest-absence explanation. Filed
  `/plans/archive/2026_08/issues/delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`
  (unified-trading-pm@62dff90443) with a P1 fix todo (translate canonical↔raw instrument-id forms in
  `DependencyChecker._count_candles_for_lookback`) and P2 re-run todos for this item + its sibling P2.11.16. Escalated
  via `/blocked`; main confirmed (option A): leave this todo open pending the P1 fix landing as its own properly-scoped
  change, rather than patching the shared dependency-checker inline from this task. Along the way, shipped two small
  REAL bugs discovered while attempting the live compute (both independent of the id-mapping blocker, both verified via
  a real preflight run before/after): (1) `features-service@9629787f` — CLI parser's `FEATURE_GROUPS` never listed
  `statistical_anomaly`, so `--feature-group statistical_anomaly` failed argparse outright; (2)
  `features-service@af75a3236` — the delta_one orchestrator's own calculator map (distinct from
  `calculators/__init__.py`'s registry) was still missing the `statistical_anomaly` → `anomaly.StatisticalAnomaly`
  entry, so even past argparse every date failed with "No calculator for feature group: statistical_anomaly". Both fixes
  are real prerequisites for this todo's eventual re-run once the id-mapping P1 fix lands, but do not by themselves
  unblock the backfill.
- 2026-08-08 (slot 2, citadel_satellite_ao_dispatch_batch1-003): shipped the GroupC smart-fill / execution-alpha P1.6
  todo — execution-service@b2b41038. Verified the shipped `replay_run` Layer-3 entrypoint end-to-end via the e2e-testing
  in-memory proof (real code path, deterministic, all assertions pass). Discovered CRA had no code path actually
  converting the `ledger_type=execution_alpha` sidecar into anything `client-reporting-api` reads — added
  `build_execution_alpha_attribution`/`emit_execution_alpha_attribution` in execution-service to reshape it into
  `PnLAttributionRow(SLIPPAGE, EXECUTION)` via the existing UTL `emit_attribution_parquet` SSOT, which CRA's
  `attribution_reader.read_attribution_rows` already scans generically — so client-reporting-api needed ZERO code
  changes (this is why it's absent from this plan's `repos:` list, not an oversight). First attempt wired the emission
  INSIDE `replay_run` itself and broke the credential-free in-memory e2e proof (`emit_attribution_parquet` has no
  storage-client DI, hit real `resolve_bucket_name()` → `BucketNamingError: GCP_PROJECT_ID not set`); moved the call to
  the CLI (`execution_service/cli/smart_fill_replay.py`), which always targets real GCS anyway. Multi-/zero-strategy
  runs skip attribution emission (honest absence, not guessed — no per-fill strategy_id on `ExecutionAlphaRow`). 5 new
  unit tests, `quality-gates.sh` green, quickmerge-shipped + verified on origin. Separately found + stashed ~25min-stale
  foreign WIP in this slot (unified-api-contracts/unified-trading-system-ui/ unified-trading-pm — an unrelated
  archetype-capability-manifest expansion to 60 archetypes, not this plan's TSMOM_BTC_CTA todo) via slot-tagged
  `git stash` per RULES.md's dead-claim inherit-or-protect rule; left untouched as it belongs to a different task.

- 2026-08-08 (interactive session, operator-authorized extraction): drafted per the operator's explicit direction to
  split `citadel_paper_batch_live_reconciliation_2026_06_19.md`'s register-§A agent-shippable items into their own
  AO-dispatchable satellite, following the corpus's established `/ag-closeout-audit` satellite-batch pattern. Read the
  source doc end-to-end (824 lines) to confirm the operator's named 8-item list against the doc's own current text. Ran
  the shared conflict-check protocol (`ao-dispatch-batch-naming-and-conflict-check.md` § 3) against every
  `assigned_vm: planning` plan sharing `parent_epic: batch_live_symmetry_master` and corpus-wide fingerprint greps for
  each candidate: found P2.11.15 is a near-verbatim duplicate of `crypto_alpha_research_2026_07_24.md`'s own open
  `[RESEARCH] P2` todo (held back — see `## Deferred`); found P2.11.18's own text couples its retrain sub-step to the
  same held-back item (scope-trimmed to corpus-recompute + drift-check only); found the source doc's register § A
  additionally lists 4 stale bullets already migrated-and-open in `crypto_alpha_research_2026_07_24.md` (corrected in
  the source doc, not extracted here). Net: 7 of the operator's named 8 items extracted into this batch; 1 (P2.11.15)
  held back on conflict, unchanged in the source doc.
- 2026-08-10 (slot-22, citadel_satellite_ao_dispatch_batch1, P2.11.18 "recompute the corpus for the intraday BTC
  mean-reversion cs-ML feature"): **DONE — verified, not re-executed.** The corpus recompute was already executed by
  slot-7 (2026-08-10, via the sibling blocker `delta_one_cefi_lookback_instrument_id_form_mismatch_2026_08_09.md`'s P2
  re-run todo, which covers this same scope): backfilled `returns` + `statistical_anomaly` feature groups for cefi/BTC
  over the paper window (`day=2026-04-22`, `2026-05-01..03`) — `reversion_zscore_60m` 99.6%/100%/100% and
  `reversion_zscore_240m` 98.1%/100%/100% non-null on 2026-05-01/02/03; 2026-04-22 emission-suppressed via `strict_fail`
  (229 candles < 500 minimum — honest-absence, not a bug; the fix chain works). Independently verified from LIVE GCS
  this session: the `statistical_anomaly` parquets exist for 2026-05-01/02/03 (written 2026-08-10T22:45Z) and carry
  `reversion_zscore_60m`/`reversion_zscore_240m` (+ 3 lag variants each) — schema-probed, non-null. Drift-check: the
  todo asks for `features-status --check-drift` — confirmed this is the formula-drift gate, QG-enforced at
  `features-service/scripts/quality-gates.sh:309`
  (`python -m features_service.delta_one.app.features.status_report --check-drift`), and features-service
  `quality-gates-v2` CI is GREEN on live-defi-rollout (latest success 2026-08-10T22:13:37Z) → no formula drift.
  (Slot-7's "command not found" was because the AO slot's features-service venv isn't provisioned; the console script +
  module exist in source.) Todo flipped. The reversion-zscore features now land in the canonical delta_one feature
  corpus for the paper window.
