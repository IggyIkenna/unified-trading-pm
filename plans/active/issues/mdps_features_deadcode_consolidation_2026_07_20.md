---
doc_type: issue
title:
  MDPS + features dead-code / orphan-launcher consolidation — broken/registered-but-unrunnable launchers, a monitoring
  blind spot, and stale post-consolidation config (surfaced building /data-pipeline-check-mdps + -features)
summary: >-
  Grep-then-read-verified dead-code + orphaned-launcher findings in deployment-service / features-service /
  market-data-processing-service, surfaced by the pass-2 audit while building the two data-pipeline-check skills. THREE
  are big findings needing an operator keep/delete decision because of self-heal / registered-live-launcher blast
  radius: (S1-a) launch-prediction-features-vm.sh is BROKEN — it packages the removed features-cross-instrument-service
  repo and its import-verify ModuleNotFounds under set -e, yet launcher_registry.py binds the prediction-features-
  relaunch to it, so an OOM/preempted prediction-features VM self-heals via a launcher that cannot succeed (also: no
  SPOT, 50GB disk that escapes the disk QG, no live-collision guard); (S1-b) launch-mdps-features-live.sh is registered
  production-ready in vm_prefix_registry.py (5 rows) but has no dispatcher branch and emits
  VM_SERVICE=market_data_processing_service+features_service (a + in a module name) → ModuleNotFoundError; its enabling
  plan is archived; (S1-c) launch-mdps-sharded-backfill.sh emits mdps-sports-<year>-<ts> VM names that are registered in
  NEITHER vm_prefix_registry.py NOR launcher_registry.py, so a preempted sports MDPS shard is invisible to the zombie
  watchdog and has no relaunch binding — and the parity test misses it because both registries agree with each other.
  Plus lower-severity dead code (S2/S3) that is safe to trim.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [deployment-service, features-service, market-data-processing-service]
scope: [engineer, admin]
tags: [dead-code, orphan, vm-launcher, registry, self-heal, monitoring, consolidation, mdps, features]
related: [/plans/active/data_pipeline_check_mdps_features_2026_07_20.md, /codex/05-infrastructure/vm-launcher-runbook.md]
created: 2026-07-20
author: unknown
last_updated: 2026-07-20
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    deployment-service/deployment_service/data_pipeline_monitors/launcher_registry.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
  ]
supersedes:
superseded_by:
resolved_by:
source: >-
  pass-2 audit (6 sub-agents, 2026-07-20) while building /data-pipeline-check-mdps + /data-pipeline-check-features; all
  findings verified by direct Read at the cited file:line, no conclusion rests on a grep-0.
---

# MDPS + features dead-code / orphan-launcher consolidation

> Filed autonomously 2026-07-20 while the operator is away. The three S1 findings are BIG (blast radius on a shared
> fleet the operator returns to: self-heal rebinding, deleting a registered live-pipeline launcher, registry parity) —
> per findings-triage they are documented here + surfaced in the final report, NOT auto-deleted. S2/S3 are safe trims.

## Big findings — keep/delete decision (options)

**Recommended (A):** delete the two orphan launchers (S1-a, S1-b) + their registry rows, and close the `mdps-sports-`
registry gap (S1-c) by registering it. **(B):** finish `launch-mdps-features-live.sh`'s dispatcher branch and keep it;
repoint S1-a's self-heal to `launch-features-vm.sh`. **(C):** do only the `mdps-sports-` registry gap now, defer the
launcher deletions. Other: free-text.

> **UPDATE 2026-08-15 (batch19 citation-reconciliation): option (B), not (A), is what actually shipped for S1-b.**
> `deployment-service@e7d17f2` finished `launch-mdps-features-live.sh`'s dispatcher branch instead of deleting the
> launcher; the CEFI 117-shard + DeFi 3,535-shard production launches were verified RUNNING with zero OOM as of
> 2026-08-07 (see todo 2 below for the full citation chain). S1-a (deleted, per A) and S1-c (registry gap closed) still
> match the original recommendation; only the S1-b half of "Recommended (A)" is superseded by what B actually delivered.

> **NOT genuinely `[OPERATOR]`-gated (round5-cefi-question-resolution 2026-08-08).** Applying
> `plans/active/task_template.md` finding U's explicit positive test: `[OPERATOR]` is for (i) a business/spend/value
> judgment with no data-derivable answer, (ii) a credential/access-only gate, or (iii) a whole-bucket destroy / failed
> reversibility check. This is none of those — S1-a/S1-b are launchers ALREADY confirmed non-functional
> (`ModuleNotFoundError` on every invocation, not merely deprecated-but-working), so deleting them + repointing the
> self-heal binding to the already-working
> `launch-features-vm.sh --feature-family cross_instrument --asset-group PREDICTION` STRICTLY REDUCES blast radius (a
> broken launcher can't succeed today regardless; repointing to a working one only helps). S1-c is a pure registry-gap
> fix (add missing rows), zero deletion involved. This doc's own stated "Recommended (A)" is the correct, low-risk
> engineering default — ordinary dead-code cleanup + registry hygiene, not a product/strategic call. S3-b (sports dual
> entrypoint) is DIFFERENT and correctly stays a real design adjudication — do NOT silently delete, it backs live sports
> backfills. Reclassifying todos 1-3 as ordinary AO-dispatchable `[SCRIPT]` work per option A; the actual multi-file
> deletion + registry edit was not executed in this pass (documentation-question audit, not an implementation dispatch).

## Todos

- [x] ✅ 1. [SCRIPT] P2. S1-a — `launch-prediction-features-vm.sh` BROKEN, superseded by
      `launch-features-vm.sh --feature-family cross_instrument --asset-group PREDICTION`; DELETE + repoint registry.
      **DONE (cefi_satellite_ao_dispatch_batch12_2026_08_09.md todo 1, 2026-08-09)** — `deployment-service@4150c6c2`:
      `launch-prediction-features-vm.sh` deleted; `launcher_registry.py`'s `"prediction-features-"` key now maps to
      `launch-features-vm.sh` (documented comment for the `--feature-family cross_instrument --asset-group PREDICTION`
      invocation, per the registry's bare-filename value convention). `test_launcher_registry.py` (9/9) +
      `quality-gates.sh` green on the shipped SHA.
- [x] ✅ 2. [SCRIPT] P2. S1-b — `launch-mdps-features-live.sh` non-runnable (no dispatcher branch;
      `VM_SERVICE=market_data_processing_service+features_service` → ModuleNotFoundError; plan archived) but registered
      in `vm_prefix_registry.py:841-851` (5 rows). DELETE launcher + 5 rows OR finish the dispatcher branch (pending
      operator). **RE-CHECKED 2026-08-09T21:47Z (slot-17, review,
      `cefi_satellite_ao_dispatch_batch12_2026_08_09_finalize.md` todo 2) — the "finish the dispatcher branch" option
      (B) has since been chosen and COMPLETED, this todo's own premise is now stale.** Two related issue docs —
      independent of this one, surfaced via unrelated
      `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` work — show the exec-dispatch branch was built
      out end-to-end and PRODUCTION-VERIFIED:
      `plans/archive/2026_08/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md` (exec-dispatch branch
      shipped `deployment-service@e7d17f2`, archived 2026-08-07, all todos done) and
      `plans/archive/issues/mdps_features_live_streaming_aggregation_never_actually_invocable_2026_08_04.md` (the CLI
      bridging + OOM + live-mode defects the first fix didn't catch, all 11 todos done, CEFI 117-shard + DeFi
      3,535-shard production launches both verified RUNNING with ZERO OOM as of 2026-08-07, archived same day). Live
      registry confirms the 5 `mdps-features-live-{ag}-` rows in `vm_prefix_registry.py` are unchanged (still
      registered) and the launcher script itself is present with no deletion. **CLOSED 2026-08-15 (batch19
      citation-reconciliation, slot-11)** — `deployment-service@e7d17f2` re-verified as a reachable ancestor of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor`) before flipping; the "Big findings" recommendation
      section above updated to record that option (B) — finish-the-dispatcher-branch — is what actually shipped for
      S1-b, not the doc's original "Recommended (A): delete" text. No new code shipped by this todo (mechanical citation
      reconciliation only, per its own prior note).
- [x] ✅ 3. [SCRIPT] P1. S1-c — `mdps-sports-<year>-<ts>` emitted by `launch-mdps-sharded-backfill.sh:206` but
      registered in NEITHER `vm_prefix_registry.py` NOR `launcher_registry.py` → sports MDPS shard invisible to zombie
      watchdog + no relaunch binding; parity test misses it (both registries agree). Add `mdps-sports-` (bucket
      `_TICK_SPORTS`, EPHEMERAL_BATCH) to both, OR drop `sports` from the sharded launcher default set. Add a
      launcher→emitted-name test. **DOC-HYGIENE CORRECTION 2026-08-09 (cefi batch12 finalize) — already fixed, checkbox
      was stale**: `deployment-service@c79f984c` ("fix(vm): wire SPOT preemption auto-recovery fleet-wide + register
      mdps-sports- prefix", 2026-07-20) registered `mdps-sports-` (bucket `_TICK_SPORTS`, `EPHEMERAL_BATCH`) in BOTH
      `launcher_registry.py` and `vm_prefix_registry.py`, plus a guard test that no SPOT launcher may be
      preemption-blind. Verified via direct commit-content read (not re-implemented).
- [x] ✅ 4. [SCRIPT] P3. S2-a — trim `launch-features-backfill-vm.sh` to the redirect stub (lines 170-309 unreachable
      dead body; duplicate `lc_verify_tarball_freshness` 274-278/280-284; pre-consolidation module names in
      `_python_module_for`). **DONE (na-eligibility-audit 2026-08-03)** — closed via
      `plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md:93`: `deployment-service@77c0206`, deleted the
      entire unreachable post-redirect body + fixed `_python_module_for`/`lc_verify_tarball_freshness`,
      `quality-gates.sh` green.
- [x] ✅ 5. [SCRIPT] P3. S2-b — delete the 8 stale `features_*_service` keys in `setup-data-pipeline-vm.sh`
      SERVICE_TARBALLS (post-2026-05-08 consolidation; only `features_service` is built). Adjacently fix the stale
      `ml_*_service` keys. **DONE (ao-dispatch batch2 2026-08-03)** — closed via
      `plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md`:100: `deployment-service@d3b5a3f`, deleted all 10
      stale keys from SERVICE_TARBALLS + orphaned TARBALL_DIRS entries + MTDS_DEPENDENT_SERVICES + AWS twin,
      `quality-gates.sh` green.
- [x] ✅ 6. [SCRIPT] P3. S3-a — delete MDPS one-offs past `Delete-when` after verifying each condition:
      `reconcile_mdps_available_at_2026_05_13.py`, `reconcile_mdps_available_at_off_by_one_2026_05_10_2026_05_11.py`,
      `reconcile_1440_nan_placeholders.py`. KEEP `benchmark_fullmonth_binance.py` (reused for the MDPS steady-state
      benchmark in the parent plan; its `Delete-when` plan is archived but the tool is in active use). **DONE
      (ao-dispatch batch2 2026-08-03)** — closed via
      `plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md`:106: `market-data-processing-service@d1e47e4`,
      Delete-when verified 2026-08-04 for all 3 scripts, companion test files deleted, benchmark_fullmonth_binance.py
      confirmed still present, `quality-gates.sh` green.
- [x] ✅ 7. [SCRIPT] P3. S3-c — repoint `features-service/scripts/sports/smoke_matrix.py` SSOT citations (archived
      plan + dead `launch-features-backfill-vm.sh` header) to `launch-features-vm.sh` + the codex smoke-matrix doc.
      **DONE (ao-dispatch batch2 2026-08-03)** — closed via
      `plans/active/infra_satellite_ao_dispatch_batch2_2026_07_27.md`:113: `e2e-testing@e117593` (file already relocated
      from features-service@7717fbee; fixed at new location), 4 citations replaced, `quality-gates.sh` green.
- [ ] [SCRIPT] P3. 8. S3-b — sports dual entrypoint (`python -m features_service.sports` with `--tables`/sfi-progressive
      vs `--feature-family sports`) — operator/design adjudication (fold submodule behind the family flag OR bless the
      submodule). Do NOT silently delete (breaks live sports backfills). Also the misleading "DEPRECATION NOTE" on the
      live `launch-features-sports-*` launchers.

## Data-orphan findings (from the same audit — tracked in the parent plan, not here)

Feature families `performance_features` + `strategy_pnl_archetype` = honest-by-design orphans (unwired
StrategyPnlStreamEvent → always `empty_confirmed(EXPECTED_NO_PNL_STREAM)`; consumers NO-OP/post-cutover). Candle cells
produced-but-unconsumed to VERIFY: TRADFI `ohlcv_1s`, DEFI `book_snapshot_5/market_state/liquidity/fx_rates`, SPORTS
`arbitrage_opportunity`; upstream trap TRADFI `mbp_10` (`needs_candle_processing` defaults True, no adapter, not
captured → should be pinned False). These are handled by the `/data-pipeline-check-mdps` + `-features` skills' canonical

- orphan checks (parent plan `data_pipeline_check_mdps_features_2026_07_20.md` todos 11/13).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the doc's own header puts 3 S1
  findings behind an operator keep/delete A/B/C decision (self-heal rebinding + deleting a registered live launcher),
  and todo 8 is an explicit design adjudication.
- **na-eligibility-audit 2026-07-30** (tranche=defi, autonomous): KEEP-NA, valid - S1-a/S1-b/S3-b are explicit operator
  keep/delete (A/B/C) decisions with self-heal + registered-live-launcher blast radius. Reached independently of the
  cefi tranche above; both agree.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — carries an explicit unanswered 'Big findings —
  operator keep/delete decision (options) A/B/C' block; todos 1, 2 and 8 each say 'pending operator' / 'operator-design
  adjudication' in their own text. Todos 3-7 are bounded but cannot be dispatched without the doc, and the
  launcher-deletion blast radius is exactly what the A/B/C ask covers
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — all 4 remaining open todos are gated
  on an unanswered operator keep/delete decision (options A/B/C for S1-a/b/c) plus an explicit S3-b operator/design
  adjudication ("Do NOT silently delete"). Reaffirms 3 prior 2026-07-30 passes (cefi/defi/sports).
- **round5-cefi-question-resolution 2026-08-08**: todos 1-3 (S1-a/b/c) declassified from `[OPERATOR]` per finding U's
  explicit test — see the annotation above the todos. Todo 8 (S3-b) correctly remains a genuine design adjudication,
  unchanged. The actual multi-file deletion + registry edit (implementing recommendation A) was not executed in this
  pass — this was a documentation-question audit, not an implementation dispatch. The sibling doc
  `plans/archive/2026_08/issues/ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` (2
  more launchers with the same defect class) followed the same reasoning once picked up (resolved + archived
  2026-08-15).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid - per the HARD RULE, `assigned_vm` flips
  WHOLE-DOC only, and todo 8 (S3-b, sports dual entrypoint) remains an explicit, un-superseded design adjudication ("Do
  NOT silently delete... operator/design adjudication") — one genuine judgment call among the 4 open items blocks the
  whole-doc flip even though todos 1-3 are now correctly declassified/bounded (per the same-day round5 pass above). Doc
  stays NA in full; todos 1-3 are ready for dispatch the moment todo 8 is resolved or split out, but that split is not
  performed here since it changes doc structure beyond a citation/marker touch.

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms round7 (2026-08-08)
  whole-doc-only-flip ruling: todo 8 (sports dual-entrypoint) remains an un-superseded design adjudication that traps
  otherwise-bounded todos 1-3.
- **cefi_satellite_ao_dispatch_batch12_2026_08_09_finalize.md todo 1, 2026-08-09** (review): reconciled checkbox
  pointers with verified shipping evidence — todo 1 (S1-a) flipped `[x]`, `deployment-service@4150c6c2`; todo 3 (S1-c)
  flipped `[x]` as a doc-hygiene correction, `deployment-service@c79f984c` (already fixed pre-existing, checkbox was
  stale). Both commits confirmed reachable on `origin/live-defi-rollout` before citing. **Remaining open in this doc:
  2** — todo 2 (S1-b, still design-gated by real successor work) and todo 8 (S3-b, still a genuine sports-dual-
  entrypoint design adjudication). Neither re-checked for newly-cleared status here — that is finalize todo 2's scope,
  not this todo's.
- **cefi_satellite_ao_dispatch_batch12_2026_08_09_finalize.md todo 2, 2026-08-09T21:47Z** (slot-17, review): re-checked
  both remaining open items for newly-cleared status. **S1-b (todo 2) — CLEARED, batch13 candidate**: see the dated note
  on the todo itself above — the dispatcher branch was finished + production-verified (CEFI 117-shard + DeFi 3,535-shard
  live launches, zero OOM, 2026-08-07) via unrelated successor work, so this todo's "non-runnable" premise is stale; the
  actual checkbox reconciliation (+ updating the "Big findings" recommendation from A to what B actually delivered) is
  left as a batch13 todo, not done here. **S3-b (todo 8) — unchanged, still genuinely blocked**: grepped the corpus for
  any newer operator/design ruling on the sports dual-entrypoint question (fold `--tables`/sfi-progressive behind
  `--feature-family sports` vs bless the submodule) — none found; `launch-features-sports-backfill-vm.sh`'s DEPRECATION
  NOTE is unchanged since 2026-05-08. Doc's remaining-open count stays 2, but todo 2 is now evidence-annotated and ready
  for a mechanical citation-only close in batch13.
- **na-eligibility-audit 2026-08-16** [body-hash:bbdf20638a45ebde]: KEEP-NA, valid — 7 of 8 todos are already [x] with hard commit-SHA evidence (todos 1-3 = the original three "big finding" S1 items, closed via deployment-service@4150c6c2 / @c79f984c / @e7d17f2 across three separate reconciliation passes 2026-08-0…
- **na-eligibility-audit 2026-08-17** [body-hash:554d56e76da47c1b]: KEEP-NA, valid — Reaffirmed. Sole open item (S3-b, sports dual entrypoint fold-vs-bless, line 155) remains an unresolved operator/design adjudication with two named options and no decided answer, reaffirmed unresolved across 7 prior audit passes through 2026-08-16 plus a dedicated finalize-pass re-check. Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: populated context_scope (4 entries).
- **context-scout 2026-08-20**: refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirms prior verdicts; sole open item (S3-b, sports
  dual-entrypoint fold-vs-bless) remains an unresolved operator/design adjudication, no new ruling found.
