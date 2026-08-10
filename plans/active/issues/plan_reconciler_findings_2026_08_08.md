---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — whole-corpus (all) pass, 2026-08-08"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-2add8d (slot 11, 2026-08-08), no tranche supplied so this is the
  whole-corpus `all` default. Corpus: 220 active plans + 375 issues + 28 epics (~623 docs, ~21MB); 262 docs (44%) are in
  the 12h grace window and read-only this run, leaving 333 non-grace active/issue docs (~11MB) + 28 epics as the
  actionable set. Given the operator's 2026-08-06 finding that unsharded full runs die mid-flight 7/8 attempts and take
  13.5h to complete, this run prioritizes genuine adversarially-verified coverage over false completeness and reports
  exact coverage achieved.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled]
related: []
created: "2026-08-08"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-08"
supersedes:
superseded_by:
resolved_by:
source: "slot 11, plan_reconciler agt-2add8d, 2026-08-08"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/scripts/plan-hygiene/check_archive_candidates.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-08 (agt-2add8d, whole-corpus `all`)

## Scope + method

- No `TRANCHE` supplied → whole-corpus `all` default (the weekly cross-tranche / unsharded-caller fallback).
- Grace set (newest commit <12h old at run start): 262 of 595 active+issue docs (44%). Read-only context this run.
- Non-grace actionable set: 333 active+issue docs (~11MB) + 28 epics (all non-grace).
- Given the corpus scale and the operator's 2026-08-06 finding (unsharded runs die mid-flight 7/8 attempts, 13.5h when
  complete), this run prioritizes real adversarially-verified findings over attempting literal 100% coverage in one
  pass, and reports exact coverage in the `## Coverage` section below rather than overclaiming.

## Flips verified

1. **`data_completion_cefi_2026_07_15.md` E8** (legacy CeFi bucket delete) — independently confirmed via sibling doc's
   cited Cloud Audit Log entry (`storage.buckets.delete` 2026-07-14T11:02:29Z). Flipped `[x]` — prevents a worker
   re-attempting an already-completed irreversible delete. unified-trading-pm@243d9b6e6.
2. **`orphaned_wip_slot12_slot8_recovery_2026_08_04.md` todo 2** (slot-8 stranded sha, "MOOT" claim) — independently
   re-verified myself via `git merge-base --is-ancestor`: `b0909a5e` IS on `origin/live-defi-rollout`, `bd0e231f` is
   NOT. Flipped `[x]`. unified-trading-pm@243d9b6e6.

## Archived (verified-done, unlocked, non-grace)

1. **`mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`** — all 5 todos `[x]` with hard evidence (2 QG
   checkers shipped+wired, `PLAN_FORMAT.md` §8c documents one of them, source doc corrected). Found + fixed a latent
   gate bug along the way: `locked_by: ""` (literal empty-string quotes) false-trips `check-locked-plan-deletion.sh`'s
   naive grep parser as "locked" even though it's semantically unlocked — normalized to true-blank in a prior commit
   before the archival mv (5 other active docs carry the same `locked_by: ""` pattern and would hit the same false
   gate-trip on their own eventual archival — filed below). Fixed 5 corpus referrers' now-stale
   `/plans/active/issues/...` citations to the new `/plans/archive/2026_08/...` path; one referrer
   (`tradfi_finding_e1_unsourced_operator_ruling_citation_2026_08_03.md`) is grace-protected and its 2 citations stay
   dangling until a future run can fix them — `check_reference_paths.py`'s ratchet still passes (84 ≤ baseline 86).
   unified-trading-pm@556dc00f3, @378d3b5dc.
2. **`dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`** — both todos done, 0 remaining
   `attempted_failed` rows verified. unified-trading-pm@f44dfadd4.
3. **`sports_index_recency_masked_captured_atoms_2026_07_13.md`** — all 7 todos done, doc's own 2026-08-05 Progress Log
   already said "this closes the last open todo" but `status:` was never flipped. Both #2 and #3 were masked archive
   candidates until the `locked_by: ""` normalization (same latent gate bug — 6 active docs total carried this pattern;
   all 6 now normalized, see Hygiene fixes). unified-trading-pm@ad137ae4e, @f44dfadd4.

**Latent bug found + fixed**: `locked_by: ""` (literal empty-string quotes, not truly blank) false-trips
`scripts/hooks/check-locked-plan-deletion.sh`'s naive `grep -oP '^\s*locked_by:\s*\K.*'` parser as "locked" — the
extracted string is 2 quote characters, non-empty to bash, even though the doc was never actually locked. This only
surfaces when a doc carrying this pattern is archived (checked HEAD content, not just current state) or run through
`check_archive_candidates.sh` (which correctly reads it as empty and returns the doc as a candidate — the two checks
disagree). All 6 corpus instances found + normalized to true-blank this run.

## Contradictions

1. **[FIXED] Stale "🟡 IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation" banner, 5 epics.** `infrastructure_master.md`,
   `strategy_master.md`, `execution_master.md`, `orchestrator_master.md`, `features_and_ml_master.md` all carried an
   identical banner blocking concurrent slots from touching strategy risk-eval/ml-registry/features-builder-registry
   surfaces "until those phase plans land." All 4 referenced phase plans (`utl_reuse_phase0/1/3/4_*_2026_07_13`) were
   independently verified archived (`find` confirms). `infrastructure_master.md`'s own body already carried an open
   `[VERIFY] P1` todo (folded in 2026-07-15, still open as of 2026-07-27) explicitly naming all 5 files and instructing
   this exact removal. Evidence: 5 epic-cluster hunters (infra_1/2/3/5/6) + 1 epic-vs-epic hunter (epics_2)
   independently surfaced this. Fixed: banner removed from all 5 files, todo flipped `[x]` with evidence —
   unified-trading-pm@ad1a887ae.
2. **[FIXED] Operator ruling not mirrored across 2 days** — `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todo
   5 still posed "place a real order on the live Kalshi exchange" as an open option 2 days after
   `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` recorded an explicit operator "NO — do not touch the
   live exchange" ruling; the source doc's own na-eligibility- audit had already flagged the sync gap. Ruled-out in
   place, citing the source ruling. unified-trading-pm@8cda7d1d6.
3. **[FIXED] Stale BLOCKED-OPERATOR clause co-located with its own resolving ruling** —
   `deribit_combo_perpetual_partition_move_2026_07_21.md`'s P2 todo asserted, in the same bullet, both "RULED
   2026-08-06: proceed now" and "BLOCKED-OPERATOR — genuine sign-off decision" — the sign-off IS the ruling. Removed the
   stale clause; left the checkbox open since no Progress Log entry evidences the `--apply` actually ran.
   unified-trading-pm@8cda7d1d6.
4. **[FLAGGED, not fixed]** `crypto_alpha_research_2026_07_24.md`'s 16 permanently-operator-gated items carry no
   `BLOCKED-OPERATOR-DECISION` marker on their own checkbox lines (only in the surrounding prose) — a parser-blind- spot
   risk (the dispatch parser reads only each todo's own line). Currently inert (`assigned_vm: NA`); the identical gap
   was found live-dispatchable in a sibling doc this run (`l2_book_microstructure_capture_2026_07_13.md`, already fixed
   there). Did not attempt the precise 16-of-21 checkbox mapping myself under time pressure — added a prominent warning
   instead, gating any future reclassification to `planning` on doing that mapping first. unified-trading-pm@8cda7d1d6.

## Doc-drift

(populated as STEP 4 confirms items)

## Hygiene fixes

1. **6 stale "archive-candidate audit" banners** claiming a follow-up "was never converted to a tracked todo" while a
   real `- [ ]` Follow-ups todo answering that exact complaint sat directly above it (added same day, slightly out of
   sync) — corrected in: `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`,
   `features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`,
   `features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`,
   `tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01.md`,
   `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`,
   `tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`. unified-trading-pm@b00ac5732.

## Filed

**Both `/blocked` questions below were answered by main during this run** (BLK-5583f6d2, BLK-c60f4898 — both "A,
confirmed correct"). Neither required reversing anything already done. For BLK-5583f6d2, main additionally ran live
`gcloud scheduler jobs` verification on the DeFi capture-status item (this role has no cloud read access) and found
neither doc's binary framing holds — capture is PARTIALLY live (daily `dex_swaps` cron enabled, `dex_pools` cron + both
5-min forward-fill jobs paused); main dispatched that evidence as a small addendum task to slot 4 (not duplicated here
to avoid a same-file double-edit). The TradFi Massive-purge item (below) remains open, explicitly needing "a proper
bounded reconciliation check, not an ad-hoc bucket walk, per single-walk discipline" per main's answer — still routed to
the operator, not resolved by this run.

### Big findings — data-pipeline-correctness-adjacent, routed to operator via `/blocked`

- [x] ✅ [OPERATOR] P1. **Has the TradFi Massive estate (~1.7M GCS objects) actually been purged, or not?** **RESOLVED
      2026-08-09 (interactive session, sub-agent dispatch) — YES, purged, and it stays purged.** See "Massive-purge
      reconciliation, 2026-08-09" in the Progress Log below for the full evidence chain (doc archaeology + a live
      bounded prefix-scoped GCS check).
- [ ] [OPERATOR] P1. **Is DeFi `collect-dex-pools`/`collect-dex-swaps` live capture currently STOPPED or RUNNING?**
      `plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md:68,195,338` (last touched 2026-08-06) says
      ALL DeFi capture is STOPPED, with `collect-dex-pools` gated-paused behind Track-8 and its own "RESUME the stopped
      DeFi capture VMs/crons" todo still unchecked — vs.
      `plans/active/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md:493` (dated 2026-08-05, one day
      EARLIER) confirming `launch-defi-forward-poll.sh --operation collect-dex-pools` runs live via Cloud Scheduler on a
      `*/5` cadence, with zero mention of any stop-order. Neither doc cross-references the other. Affects which
      collectors are actually live — a genuine data-correctness question, not resolvable from docs alone. - **Live
      verification (main, 2026-08-08, BLK-5583f6d2 answer)**: checked gcloud scheduler jobs directly
      (location=asia-northeast1). Neither doc is fully accurate. The 5-min-cadence forward-fill jobs are BOTH PAUSED:
      defi-fwd-dex-swaps-prd (schedule=*/5 * * * *) and defi-fwd-dex-pools-prd (schedule=1-59/5 * * * *) — so the
      runs-on-a-5-min-cadence claim is stale/wrong. But uts-prod-mtds-collect-dex-swaps-cron (daily, schedule=30 0 * *
      *) is ENABLED with lastAttemptTime=2026-08-08T00:30:03Z (ran this morning) — so the ALL-capture-STOPPED claim is
      also wrong for dex_swaps specifically. uts-prod-mtds-collect-dex-pools-cron (daily, schedule=15 0 * * *) IS PAUSED
      though, matching the stopped claim for dex_pools. Net: capture is PARTIALLY live (daily dex_swaps cron only;
      dex_pools and both 5-min forward-fill jobs are paused). **Resolved 2026-08-09 (operator-directed research,
      interactive session)**: dex_pools/dex_swaps is BATCH-BY-DESIGN (poll-based), not genuine live/websocket capture —
      confirmed at the code level. `dex_swaps_handler.py`/ `dex_pools_handler.py` issue one-shot GraphQL POSTs to a
      subgraph gateway per invocation, no persistent socket anywhere. A `WSFeedConnector`-named abstraction exists
      (`live/connectors/dex_swap_uniswap_v3_ws.py`) but its own header explicitly documents choosing subgraph-polling
      (15-30s interval) over a raw `eth_subscribe` websocket, specifically to keep the "Live = batch" invariant (same
      code path, only `pipeline_mode` differs) — only 1 of 22 registered (protocol×chain) venues has even been upgraded
      to this poller; the rest are `NotImplementedError` placeholders. Codex confirms by design: `live_websocket` as a
      mode is RETIRED workspace-wide; `dex_pool_state`/`dex_pool_swaps` resolve to source `onchain_subgraph` (a pull
      source). **"5-min forward-fill" mechanically means**: boot an ephemeral VM that re-runs the SAME batch handler in
      `--mode live` every 5 min (`defi_forward_poll_scheduler.tf`'s own comment: "near-real-time without per-block
      streaming infra") — gap-filling/refresh polling, never a subscription. **The specific paused/enabled asymmetry is
      NOT a regression** — it's a documented, deliberate operator pause:
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md:66-75` records the operator (2026-07-18) explicitly
      stopping ALL DeFi forward-poll VMs + pausing every `defi-fwd-*-prd`/daily-collect cron for the Track 0-1
      per-instrument re-architecture, and `defi_consolidated_closeout_history_2026_07_18.md:1937` names `dex_pools`
      specifically (not `dex_swaps`) as still mid-migrating — exactly matching why dex_pools' daily cron stayed paused
      while dex_swaps' was safe to re-enable. Net: the architecture question is answered (batch-by-design, correct); the
      remaining call is narrower — is daily-only cadence (vs. resuming the 5-min forward-fill polling) the intended
      state to leave things in until Track 1/2/3 land, which is an operator preference, not a data-correctness question
      anymore.

### Codex-drift — 9 findings, routed per "codex updates are in-scope but never autonomous"

The codex-alignment spot-check hunter checked the 12 highest-traffic codex docs against their most substantive citing
plans; 9 of 12 showed drift (codex-side stale in most cases). Per plan_reconciler's own rule, a codex/SSOT edit is only
ever applied after an explicit operator ruling — filed here, not edited:

- [ ] [OPERATOR] P2. `/codex/05-infrastructure/vm-launcher-runbook.md:564` claims a preempted backfill VM is
      "auto-relaunched by `RelaunchPreemptedVm`" — but `cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`'s
      Progress Log shows the cefi sharded-backfill launcher died 5× in 8 days with ZERO automatic relaunch each time
      (already escalated to the operator separately). Codex overstates a capability that doesn't exist for this
      launcher.
- [ ] [OPERATOR] P3. `/codex/06-coding-standards/quality-gates.md:3248` calls the RAM-pressure abort-monitor "(planned)"
      — it shipped 2026-07-27 (`761edd205`), 11+ days ago (`qg_host_adaptive_resource_governor_2026_07_14.md`).
- [x] ✅ [DOCS] P3. `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md:95-99` documented
      exactly 3 conflict-check surfaces; a measured 4th real surface slipped through. **Fixed**:
      unified-trading-pm@c2083029dc ("docs(codex): add 4th conflict-check surface for draft satellite batches") — the
      codex doc's § 3 now lists surface (d): `status: draft` satellite batches from either skill's prior run. The
      originating todo (`na_and_ag_closeout_audit_population_overlap_2026_07_31.md:141`) still tracks the SKILL.md
      cross-reference half of the same fix separately — not duplicated here.
- [x] ✅ [DOCS] P3. `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md:159`'s Class-B table said
      `plan_reconciler` (this very role) runs "daily 01:00 UTC, opus" — current reality is sharded-by-tranche,
      2h-retry-until-capacity Sun-Fri / unsharded `all` Saturday, sonnet (per
      `daily_trading_analyst_llm_job_design_2026_07_29.md`'s 07-28/29 rulings and this dispatch's own
      MODEL=claude-sonnet-5). **Fixed 2026-08-09 (interactive session)**: the opus/schedule half was already corrected
      in `unified-trading-pm@879b8e9907`, but that fix carried this finding's OWN stale "hourly-retry" phrasing forward
      verbatim — the installer was widened hourly→every-2h on 2026-07-30, before this finding was filed. Corrected in
      `unified-trading-pm@717a17bdfa`. Separately, `plan_reconciler` itself graduated to STEADY STATE (direct push, no
      review PR) 2026-08-09 — see `agents/plan_reconciler.md`.
- [ ] [OPERATOR] P3. `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` self-declares
      `authoritative_for` the archival ritual, but the real "never combine flip+`git mv`" rule lives only in
      `agents/RULES.md`; 10+ plans miscite the source.
- [ ] [OPERATOR] P3. `/codex/02-data/pipeline-mode-partition.md:252-254` still tags the M4 live read-path resolver
      `[GATED — rides M1-BREAKING]` though M1 landed and M4 itself was verified shipped 2026-07-12 — the adjacent M1 tag
      was fixed 2026-08-04 but M4's was missed in the same edit.
- [ ] [OPERATOR] P3. `/codex/02-data/honest-coverage-model.md` CK3 table shows cefi Layer-1 at a superseded 79.55%
      figure (07-03, superseded 07-07 and again 07-12) — other asset_group rows got updated 2026-07-28, cefi's didn't.
- [ ] [OPERATOR] P3. `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3/§3a — PLAN-side staleness, codex is
      fine here: `bucket_estate_consolidation_closeout_2026_07_24.md` repeatedly quotes only half the delete rule and
      declares an `ml-models-store` delete "categorically human-only" without ever running the §3a
      fresh-retention-seconds check. No incorrect action has occurred (independently blocked by an unrelated IAM gap
      too) — flagging the plan's mischaracterization, not a codex fix.
- [x] ✅ [DOC] P3. **RULED 2026-08-09 (operator): "Override grace — fix it now."** Operator explicitly overrode the
      grace-protection window for this mechanical fix rather than waiting for it to clear naturally. Corrected
      `/codex/08-workflows/ci-cd-flow.md`'s "Version Bump Flow (Semver Agent)" section (the "Compute" table row + the
      commit-prefix result table, ~lines 936/941-946) — both described semver PATCH bumps as purely commit-label-driven
      (`fix:` prefix), which has been structurally unreachable since the LDR→main model went squash-only (every commit
      reaching `main` is `chore(promote): LDR → main ...`, carrying no original conventional-commit message). Corrected
      wording to describe the actual current mechanism per
      `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` (fix landed 2026-08-07 18:33-20:59Z): the AST
      content differ (`detect_breaking_change.py`) still correctly computes `is_breaking` via content (works under
      squash) for the MINOR tier, and a NEW content-based fallback (any `SOURCE_DIR/` file changed in the diff window,
      no breaking delta → default PATCH) now implements the PATCH tier that was previously dead. Kept the old
      commit-prefix table for human intuition but retitled/annotated it to point at the real, content-based live signal
      per tier rather than removing the historical framing outright.

### Other filed follow-ups

- [x] ✅ [SCRIPT] P3. Extend `check-locked-plan-deletion.sh`'s `locked_by` parser to treat a literal `""`/`''` value as
      empty (currently a naive `grep -oP` extracts the quote characters themselves as a non-empty string) — found via 6
      real corpus instances this run, all now individually normalized, but the parser bug itself is unfixed and will
      recur on any future doc authored with `locked_by: ""` instead of a true-blank value. —
      unified-trading-pm@81dbe27cd7
- [x] ✅ [REVIEW] P3. Live-check whether `market-tick-data-service`'s VM `fts-backfill-20260806-012831`
      (`sports_closeout_track_s2_foldin_2026_07_25.md` todo, "RELAUNCHED 2026-08-06") has since completed —
      last-observed state (2026-08-06) was "still RUNNING, no exit signal"; ~2 days have passed as of this run
      (2026-08-08) so it has almost certainly resolved one way or the other by now, but I have no VM/cloud read access
      from this role to confirm. **DONE 2026-08-08 (slot-27, review)**: it has NOT resolved — live `gcloud`/`gsutil`
      check confirms genuinely still RUNNING (not stalled: log written 2s before check, watchdog trace monotonically
      growing), at 39.6% of its date range (892/2,253 days) after 67.4h, ETA ~4.3 more days. Also found + fixed an
      adjacent premature-checkbox-flip bug on the same VM's plan todo (flipped `[x]` at launch instead of at its own
      done-when, same class as the 08-05 predecessor VM). Full evidence + fix:
      `sports_closeout_track_s2_foldin_2026_07_25.md` Progress Log, 2026-08-08 entry. unified-trading-pm (this commit).

## Archive candidates (operator review)

- `plans/active/issues/main_ci_red_promotion_blocked_by_plan_hygiene_backlog_2026_08_06.md` — both todos ✅ with hard
  evidence (PR #2514 `quality-gates-v2: SUCCESS`, MERGED 2026-08-07T23:19:35Z, unified-trading-pm@2c8bd8125; operator
  ruling for BLK-46fa5703 dated in Progress Log). This is the ONE doc `check_archive_candidates.sh` flags (baseline 0,
  live 1) — **but it is in the 12h GRACE WINDOW (last touched ~54 min before this run started)**, so it is NOT archived
  this run per the HARD LIMIT (never modify a plan <12h old). Expected to self-resolve: either a future reconciler run
  archives it once grace expires, or it's archived sooner as ordinary hygiene follow-up. Not a judgment call — a timing
  gate — so not raised as a blocked-question.

## Refuted (dropped by verify)

1. **cefi_master hunter's hedged P1** (`cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`'s VENUES list
   silently dropping UPBIT/BINANCE-SPOT/COINBASE-SPOT via `_filter_spot_only_venues`) — **REFUTED** by direct code read:
   `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh` does not reference
   `shard_distribution.py`/`_get_tardis_access_mode`/`ShardDistribution` anywhere — it's a bash launcher that builds its
   VENUES string directly with no dependency on that Python filter, which is scoped to a completely different code path
   (`service == "market-tick-data-handler"`). The hunter correctly hedged this as unconfirmed; it does not hold up.

## Coverage (hunters / batches / docs)

- **30 hunters fanned out** across 3 waves: 24 epic-cluster batches (infra ×6, sports ×2, agent_operating_framework ×2,
  defi ×2, orchestrator ×2, cefi/predictions/manifest/tradfi/instruments/mtds_mdps/deployment_and_user_management ×1
  each, 2 combined-small-epic batches), 2 epic-vs-epic sweeps (covering all 28 `plans/epics/*.md`), 1 corpus-wide
  missed-flip grep sweep, 3 cross-cutting topic sweeps (CI/CD+AO-lifecycle, data-correctness cross-AG, codex-alignment).
- **Docs read in full**: all 333 non-grace `plans/active/*.md` + `plans/active/issues/*.md` (the full actionable set)
  - all 28 `plans/epics/*.md` = 361 docs, each read by exactly one epic-cluster/epic-vs-epic hunter, plus targeted
    grep-scoped reads by the missed-flip/topic hunters layered on top. Grace-protected docs (262, 44% of the corpus)
    were correctly excluded from the actionable set per the 12h HARD LIMIT — read-only where a hunter happened to
    cross-reference one for context, never written.
- **Candidates generated**: ~75 distinct findings across P1-P3. **Verified + applied this run**: ~20 (5-epic stale
  banner removal, 6 stale archive-audit banners, 2 missed-flips, 3 archived docs + 5 referrer path fixes, 6 `locked_by`
  normalizations, 3 operator-ruling-mirror/tag fixes). **Refuted**: 1 (cefi venues-filter hypothesis, via direct code
  read). **Filed as tracked todos + alerted via `/blocked`**: 13 (2 data-correctness big-findings, 9 codex-drift, 2
  other).
- **Not individually re-verified/applied this run** (found by a hunter, evidence looked solid on read, but time budget
  didn't extend to personally verifying + fixing each): a meaningful tail of P2/P3 items — mostly epic-hub staleness
  (stale rosters/priority tables in `cefi_master.md`, `manifest_master.md`, `predictions_master.md`,
  `strategy_master.md`, `deployment_and_user_management_master.md`; stale `last_updated` fields on ~10 of the 28 epics),
  a handful of same-doc checkbox/prose contradictions in individual issue docs
  (`ao_satellite_ao_dispatch_ batch6_2026_08_04.md`'s and `batch7_2026_08_06.md`'s internal ledger-arithmetic
  mismatches, `honest_coverage_shard_ dimension_model_definitional_data_2026_07_07.md`'s tracker-vs-source drift,
  several more), and ~5 more stale same-day-ruling-vs-audit-verdict pairs of the shape already fixed above (e.g.
  `strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`,
  `pytest_timeout_60s_flaky_under_contention_continued3_ 2026_08_03.md`). None are safety-critical or
  data-correctness-adjacent (those were prioritized and either fixed or routed above) — all are cosmetic/bookkeeping
  drift. Preserved for a follow-up pass: the full per-hunter raw candidate list this section summarizes is in this run's
  session transcript; a future `/plan-reconciler` or `/plan-reconcile` pass re-hunting the same non-grace set will
  resurface any still-live ones (none are time-sensitive enough to need filing as individual todos right now, unlike the
  13 above).

## Plans not reached

None in the non-grace actionable set (333 active/issue docs + 28 epics) — every one was assigned to and read by at least
one hunter this run. The 262 grace-protected docs were correctly excluded per the HARD LIMIT, not "not reached."

## Progress Log

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **stale-`[OPERATOR]`-flip sweep 2026-08-09**: the 4th-conflict-check-surface codex-drift finding was stale — the codex
  fix already landed (`unified-trading-pm@c2083029dc`, verified via `git log` against the target file). Flipped `[x]`,
  retagged `[OPERATOR]` → `[DOCS]`.
- **RULED 2026-08-09 (operator)**: "Override grace — fix it now." Overrode the grace-protection window for the
  semver-PATCH-bump-wording finding rather than waiting for `plan_reconciler`'s next natural clearing pass. Fixed
  `/codex/08-workflows/ci-cd-flow.md` directly (Compute row + commit-prefix result table in the "Version Bump Flow"
  section) to describe the actual content-based mechanism per
  `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` instead of the stale pure-commit-label framing.
- **Massive-purge reconciliation, 2026-08-09 (sub-agent dispatch, answering the P1 `[OPERATOR]` question above)**:
  **VERDICT — the Massive estate IS purged, and stays purged as of today.** Resolved without an ad-hoc bucket walk, per
  the single-walk-discipline instruction, using two layers of evidence:
  1. **Doc archaeology.** The doc-side "contradiction" was never a genuine open question — it was one epic sentence
     (`tradfi_master.md:181-182`, both halves written in the SAME commit `1dd1a22fd97`, 2026-07-21) that hedged on
     whether recognition should be dropped, sitting next to **nine independent, cross-dated, mutually-corroborating
     records** of the same executed purge: the archived issue doc
     (`plans/archive/issues/massive_purge_blocked_databento_l1_entitlement_2026_07_20.md`) with full VM-fanout terminal
     evidence (RUN_TS=20260720-193849, 1,701,414 PURGED + 8 QUARANTINE stragglers deleted directly = 1,701,422, 0
     `PURGE_REFUSED_GATED`, 0 ORPHAN, a Phase-2 per-day before/after table showing massive→0 with databento counts
     UNCHANGED); the manifest surgical CAS drop (`manifest-consolidator-ssot.md:603`, 686,005 `batch_massive` rows
     removed 2026-07-20, 5,209,585→4,519,965); and independent CLOSED/COMPLETED/RETIRED confirmations dated 07-21
     through 07-25 in `canonical-cutover-register.md` (§4, "COMPLETED 2026-07-21"),
     `gcs-and-manifest-delete-safety-protocol.md` (hard-stop #3, "EXECUTED 2026-07-20/21 ... not because this specific
     purge is still pending — it is not"), `reconciliation-finding-taxonomy.md` (AE-4, "CLOSED 2026-07-20/21"),
     `four-surface-reconciliation-procedure.md` (§6, "COMPLETED 2026-07-20"), `non-canonical-path-inventory.md` (row 10,
     "RETIRED — the Massive purge EXECUTED"), `tradfi-databento-sourcing-ssot.md`, and two independently-dated active
     plans (`tradfi_manifest_content_recovery_completion_2026_07_24.md:350` "batch_massive=ZERO (already purged
     2026-07-21)"; `tradfi_backfill_throughput_followups_2026_07_24.md:195`). All nine cite the identical non-round
     figure (1,701,422) — not a number that would independently coincide across nine documents by accident.
  2. **Live, bounded, prefix-scoped verification (not a bucket walk)** — reused the ORIGINAL campaign's own 6 Phase-2
     verification days from the archived issue doc, plus 2 recent dates well after the purge to rule out resurrection,
     against the real bucket (`gs://market-data-tick-tradfi-prd-central-element-323112`):
     `gcloud storage ls ".../day=<D>/pipeline_mode=batch_massive/**"` for
     `D ∈ {2020-06-15, 2021-06-15, 2022-06-15, 2023-05-23, 2024-06-17, 2025-04-08, 2026-07-25, 2026-08-05}` → **0
     objects on every single day**, including the two recent dates. A sanity check on the same days against
     `pipeline_mode=batch_databento` returned 1,350/1,387 objects respectively, confirming the bucket/prefix pattern
     itself is correct (not a false-empty from a wrong prefix). A cheap delimiter-listing of the bucket root found two
     `_migration_backup*/` prefixes; spot-checked — these hold manifest/index snapshot parquet only (~118MB), not raw
     tick data, and are unrelated to the Massive estate. This is the sanctioned §5 route-1 pattern from
     `/codex/02-data/four-surface-reconciliation-procedure.md` (prefix-scoped listing per known date, not a corpus walk)
     — no whole-bucket or whole-corpus listing was performed.
  - **Which docs were wrong — flagged, and one fixed:**
    - **`plans/epics/tradfi_master.md:181-183` — FIXED this session** (purely mechanical, hard-evidence-backed): removed
      the self-contradicting "retain recognition only until the separate gated GCS purge" clause and replaced it with
      the corrected state (purge executed, live-reverified 2026-08-09, citing this entry).
    - **`plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md` — FLAGGED, NOT fixed.** This doc
      predates the purge (created 2026-07-19; purge ran 2026-07-20/21) and its "Sequencing"/"Hard-stops" sections still
      frame BOTH step 5 (general canonical `--apply` migration) and step 6 (Massive purge) as future `[GATE]`
      operator-go items. Beyond the Massive question this doc's own scope was asked about, there is strong independent
      evidence the ENTIRE migration it describes — not just the Massive purge — has ALSO since executed:
      `canonical-cutover-register.md:258-259` states "UPDATED 2026-07-27 — migration COMPLETE, not
      operator-gated/pending ... run `20260720-120911` (mtds-code@5581dcf9), 20/20 SPOT shards reporting ORPHAN=0 over
      2,649,469 objects," catalogue SHIPPED+APPLIED LIVE 2026-07-25, chain-bundle content gate CLOSED 2026-07-27. The
      doc's own `## Todos` section already carries zero open items (its one todo is `[x]` done). This looks like a doc
      whose core content is fully stale/executed and may be an archive candidate — **not resolved here**, since
      confirming that requires auditing the doc's OTHER still-open surfaces (manifest resurrection cleanup, casing
      normalization residuals, quarantine disposition) that are outside this todo's scope, and archival needs the full
      6-step ritual + its `locked_by: live-defi-rollout` clearance. Recommend a dedicated closeout pass on this doc.
    - **`plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md:195-196` — FLAGGED, NOT fixed.** Its "stays
      deferred as one unit, unchanged from batch1-6" framing is a downstream inheritance of the design doc's stale
      gating above — once that doc's status is corrected, this batch's "Deferred" list entry needs updating too (it may
      no longer be deferred work at all). Left as-is pending the design-doc closeout above; batch8 (or whichever picks
      this up next) should re-check against the corrected design doc, not this framing.
  - **Confidence**: high on the narrow question asked (has the Massive estate been purged — yes, confirmed live
    2026-08-09, not just by trusting doc prose). Lower/flagged on the broader "is the whole migration done" question the
    investigation surfaced as a side-finding — that one is evidenced but not independently live-verified this session,
    so it is flagged rather than asserted as fact. Flipped this todo done, retagged `[OPERATOR]` → `[DOC]`.
