---
doc_type: plan
title:
  Data-pipeline alert-storm root-cause batch — 19 findings traced from one 108-message /50-minute
  #data-pipeline-alerts burst (2026-08-10)
summary: >-
  One live #data-pipeline-alerts burst (108 messages in ~50 minutes, but only 7 distinct VMs + 6 data_type rows
  underneath) was traced end-to-end rather than triaged alert-by-alert. The storm itself was the primary bug: the
  emitting `uts-prod-dp-exit-code-monitor` is a Cloud Run JOB on a */5 schedule (PROVEN via `gcloud logging read` —
  every DP_VM_PREEMPTED_NO_RELAUNCH carried `resource.type=cloud_run_job, job_name=uts-prod-dp-exit-code-monitor`, no
  other emitter), so its relaunch actuator's `tempfile.gettempdir()` budget was discarded with the container every 5
  minutes: the documented `_MAX_RELAUNCHES_PER_DAY=2` cap never engaged, every sweep re-attempted the same relaunch, and
  every sweep re-paged. Executions also OVERLAP (a 15:30 execution finished 15:45 while 15:35/15:40/15:45 had started),
  so a shared-document fix would have lost updates — the state is therefore one-object-per-fact with an atomic
  create-if-absent claim, no lock, mirroring the manifest writer's own per-VM shard isolation after it hit the identical
  lost-update bug.

  Chasing the remaining alerts surfaced 18 further findings across 6 repos, including two the alerts actively
  mis-described. Most consequential: a proposed remedy to DELETE all Deribit 2019 data as a "2019 vintage schema
  problem" was REFUTED by a single control probe — a 2025-06-16 shard has the IDENTICAL 25-column schema and fails
  identically. The real defect is adapter routing (options_chain content stored at `data_type=trades`, so
  `CefiTradesAdapter` runs instead of the already-existing `CefiOptionsChainAdapter`), affecting every vintage. Deleting
  would have destroyed 6+ years of good data and left the bug live.
status: active
nature: process
asset_group: [cefi, sports, cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    unified-trading-library,
    market-data-processing-service,
    features-service,
    agent-orchestrator,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [data-pipeline-alerts, alert-storm, root-cause, dp-vm-008, adapter-routing, race-condition, P1]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_vm_002_detector_generic_alert_text_and_bucket_kind_blindness_2026_08_09.md,
    /plans/active/issues/mtds_backfill_odds_smallchunk10_relaunch_budget_bug_and_oom_2026_08_09.md,
    /plans/active/issues/cefi_fwd_vm_preempted_false_positive_standard_provisioning_2026_08_06.md,
    /plans/active/deployment_registry_firestore_p5_verify_2026_07_14.md,
    /plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md,
  ]
created: "2026-08-10"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
effort: high
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-10, operator-pasted #data-pipeline-alerts dump, traced to root cause across 6 repos.
  Operator decisions recorded inline: chain fix = "both, sequenced"; packaging = one batch plan + existing-doc
  enhancements; dispatch = all human/local.
last_updated: 2026-06-27
---

# Data-pipeline alert-storm root-cause batch (2026-08-10)

## Codex SSOTs this plan references (never duplicates)

- `/codex/05-infrastructure/data-pipeline-alerts.md` + `.registry.yaml` — the DP-`<CATEGORY>`-`<NNN>` registry
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest verbs, shard atom
- `/codex/02-data/honest-absence-downstream-handling.md` — empty vs failed
- `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — governs todo 8
- `/codex/05-infrastructure/spot-vms-for-backfill.md` — preemption recovery contract

## The measured storm

| Event                         | Msgs | Distinct subjects |
| ----------------------------- | ---- | ----------------- |
| `DP_VM_PREEMPTED` (INFO)      | 31   | 2 VMs             |
| `DP_VM_EXIT_NONZERO` (CRIT)   | 21   | 3 VMs             |
| `DP_VM_PREEMPTED_NO_RELAUNCH` | 20   | 2 VMs             |
| `DP_VM_GONE_NO_CAPTURE`       | 18   | 4 VMs             |
| `DP_RUN_MOSTLY_EMPTY`         | 18   | 6 data_types      |

108 messages / ~13 real subjects. A messages:subjects ratio far above ~2:1 means the storm IS the bug.

## Todos

### Code complete + gate-verified, NOT YET SHIPPED

> Deliberately UNCHECKED. The first `quickmerge` attempt FAILED (re-gate hit the repo's 960-line file cap, broken by
> three concurrent agents' additions incl. this one: 853→998). Fixed by extraction into
> `scripts/recovery/ _durable_state.py` (998→895); awaiting a re-gate + a real sha. A checkbox goes `[x]` only when the
> sha RESOLVES — see this session's own correction of a false `305d897a` claim in
> `/plans/active/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md`.
>
> **⚠️ CORRECTION (2026-08-10, data-pipeline-alerts reconciler slot-20): the "code complete" claim above is now FALSE —
> the code is LOST, not awaiting a re-gate.** Verified 2026-08-10T23:44Z: `scripts/recovery/_durable_state.py` (and the
> sibling extractions `_captured_reader.py`/`_classify.py`) exist on NO branch, NO stash, NO reflog entry in
> `deployment-service`; `git log --all -- scripts/recovery/_durable_state.py` is empty and the working tree is clean.
> The authored fix lived only in an uncommitted worktree that was lost (never committed before the session ended). The
> live `tempfile.gettempdir()` budget bug is STILL PRESENT at `scripts/recovery/relaunch_backfill_vm.py:399-400` —
> `_MAX_RELAUNCHES_PER_DAY=2` is still a no-op in production, and the `DP_VM_PREEMPTED_NO_RELAUNCH` storm this todo was
> built to stop is STILL FIRING (724 messages in the 24h to 2026-08-10T23:34Z). This todo must be RE-AUTHORED from
> scratch, not "picked up where the code left off".
>
> **⚠️⚠️ COUNTER-CORRECTION (2026-08-11T06:2xZ, slot 1 — the authoring slot). DO NOT RE-AUTHOR. The code is NOT lost.**
> All four modules exist RIGHT NOW, uncommitted, in slot 1's working tree: `scripts/recovery/_durable_state.py` (138 L),
> `_captured_reader.py` (205 L), `_classify.py` (565 L), `_attempted_failed_index.py` (176 L), alongside 8 modified
> files. The slot-20 check was CORRECT FROM WHERE IT LOOKED and the inference was reasonable — but each slot is a
> SEPARATE clone with its own working tree, so uncommitted work in slot 1 is invisible from slot 20, from `--all`, from
> the reflog, and from origin. "Not on any branch/stash/reflog" proves it is unshipped, NOT that it does not exist.
> **This is the single most expensive failure mode in this batch** and it has now bitten three distinct ways in one
> session: (1) `safe-doc-push` exited 0 having pushed nothing, (2) a peer operation silently reverted an uncommitted
> append (323 L → 286 L, with no artifact left to recover from), and (3) this — a peer correctly observing absence and
> reasonably concluding loss, nearly triggering a full re-author of a day's work. **Also corrected: the "bug STILL
> PRESENT at :399-400" claim.** `tempfile.gettempdir()` at lines 80 and 401 is the deliberate LOCAL-ONLY fallback
> (`_default_budget_dir()` / `_default_preemption_budget_dir()`), used only when a caller passes an explicit
> `budget_dir` — i.e. unit tests. Production passes nothing and goes through `_ShardedState(..., local_only=False)`
> against GCS. Presence of the symbol is not presence of the bug; that read was grep-then-conclude rather than
> grep-then-READ. **RESOLVED 2026-08-11 — shipped at `deployment-service@0c38c00d`.** All four modules are now ON ORIGIN
> (verified by name: `_durable_state.py`, `_captured_reader.py`, `_classify.py`, `_attempted_failed_index.py`), with the
> race-free `_ShardedState` wiring and the windowed-ratio fix present. Final gate: 3,317 passed / 0 failed, sentinel ==
> HEAD. Nothing to re-author. Original status line follows for provenance: Status at the time of writing: the tree is
> fast-forwarded clean onto the current HEAD and the full gate is RUNNING. **If slot 1 dies before that gate +
> `quickmerge` complete, THEN the work is genuinely lost and re-authoring is correct** — the record below will carry a
> resolving sha the moment it lands.

- [x] ✅ [SCRIPT] P1. **SHIPPED — deployment-service@0c38c00d.** Durable, race-free relaunch state — replaced the
      `tempfile.gettempdir()` budget with one-object-per-fact GCS state in `deployment-scripts-<project>`;
      `DP_VM_PREEMPTED_NO_RELAUNCH` now pages at most once per VM via an ATOMIC create-if-absent claim
      (`if_generation_match=0`), and the repeat sweep returns `SUPPRESSED` BEFORE re-running the launcher (stopping the
      wasted relaunches, not just the page). Budget counts OBJECTS under a day-partitioned prefix instead of
      incrementing an integer, so overlapping executions cannot lose an increment. No lock: the manifest writer's own
      record shows CAS-on-a-shared-doc "melts under fleet load", and its durable answer was per-writer sharding. Also
      fixed a `_PAGED_GROUP` NameError (AST-clean, would have been a runtime failure in prod) and a test-hermeticity
      defect this change introduced (the pytest fake-GCS backend under `$TMPDIR/local-storage/` persists BETWEEN runs,
      so a claim from one run silently suppressed the alert the next run asserted on — two `sweep()` tests passed then
      failed with no code change; closed with a per-test namespacing autouse fixture in `tests/conftest.py`). Gate
      evidence (pre-extraction): quality-gates.sh QG_EXIT=0, 3265 passed, sentinel == HEAD; 5 new regression tests incl.
      two that assert CONCURRENT behaviour (atomic claim admits exactly one winner; concurrent stamps tally 2 not 1),
      proven hermetic by passing twice consecutively without clearing stale state.
- [x] ✅ [OPERATOR] P2. Firestore dual-write 403 — `uts-prd-sa` had NO Firestore role at all. Granted
      `roles/datastore.user`, verified live via `gcloud projects get-iam-policy`. This ALSO closes the 11× "transaction
      has no transaction ID, so it cannot be rolled back" errors: `heartbeat()` is transactional (`@fs.transactional`),
      so a PERMISSION_DENIED on BeginTransaction surfaces as a rollback of a transaction that never got an ID — one root
      cause, two symptoms, split by which method ran.
- [x] ✅ [SCRIPT] P2. `/data-pipeline-alerts-reconcile` §1.5 — added the five checks a live pass proved §0-1 did not
      cover, incl. the one place the skill would have actively MIS-fixed this storm (§1(b) sends you to a cooldown,
      which silences the page while the actuator keeps burning relaunches) and a mandatory control-sample rule before
      any destructive action. Evidence: `unified-trading-pm@009026a7a7`.

### Root-cause fixes — in flight (sub-agent authored, parent ships)

- [x] ✅ [SCRIPT] P1. Preemption-safe per-VM manifest shard flush — SIGTERM/SIGINT handler forcing a `process_final`
      drain, install-once with rollback, chains to any pre-existing handler (incl. `SIG_DFL` re-delivery via `os.kill`),
      degrades to a logged no-op off the main thread, never raises. Extracted to a new
      `manifest_writer/_preemption_signal.py` so `_state.py` stays byte-identical to HEAD (it was already exactly at its
      900-line cap). Evidence: **unified-trading-library@3b006d9f**, `UTL_QG_EXIT=0`, 7 new + 546 manifest_writer tests
      green, basedpyright clean.
- [x] ✅ [SCRIPT] P0. Chain adapter route-on-content — part 1 of 2. Routes on the authoritative `instrument_type=` path
      segment (deterministic, not column-sniffing), so a genuine trades bundle can never misroute. Evidence:
      **market-data-processing-service@93d783df**, `MDPS_QG_EXIT=0`, 2399 passed; 8 new tests including a NEGATIVE
      CONTROL that reproduces `MalformedTickFieldError` against `CefiTradesAdapter` with the real 25-column frame —
      which is what makes the fix provable rather than merely passing.
- [x] ✅ [SCRIPT] P1. features-service records honest absence instead of exiting 1 when an upstream IS shard for the
      current day is missing (batch). Root cause: `DependencyError` was absent from `_run_feature_group`'s per-shard
      `except` tuple, so it escaped shard isolation and killed the process. Uses `record_failed` (retryable
      `attempted_failed`), NOT `record_empty` — a lagging upstream is not a confirmed absence, and a false
      `empty_confirmed` would block the later recompute (codex `/codex/02-data/honest-absence-downstream-handling.md`
      §6A Class 1). LIVE-mode halt verified unchanged. Evidence: **features-service@692ce76b**, `FS_QG_EXIT=0`, 18,387
      passed; full `tests/sports/unit` 3107 passed / 0 failed. NOTE: this ALSO closes the FALSE claim in
      `/plans/active/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md` that the
      fix had landed at `features-service@305d897a` — that sha never existed (`git cat-file -t` → not a valid object);
      692ce76b is the real one.
- [ ] [SCRIPT] P1. Alert-accuracy quartet (deployment-service): interpolate or drop the fixed-template `"(0 → 0)"`;
      extend the captured-reader probe fallback to the bucket-resolves-but-blob-absent case (+ `instruments-store` /
      `features` kind buckets); make the "relaunching through the Tardis/launcher concurrency guard" text conditional on
      the VM's ACTUAL launcher binding (`mdps-*` binds `launch-mdps-sharded-backfill.sh`, which has ZERO Tardis
      references); exempt cron/launcher HOST VMs from the capture-based `GONE_NO_CAPTURE` population.
- [x] ✅ [SCRIPT] P2. Make `/data-pipeline-alerts-reconcile` AO-schedulable — **already shipped upstream by a peer while
      this session worked** (agent-orchestrator slot-18): the `data_pipeline_alerts_reconciler` AgentKind, the
      `plan_health` mode + prompt-template mapping, and `install-data-pipeline-alerts-reconciler-timer.sh` were all on
      origin by the time this slot went to push, so this session's independently-written versions were DISCARDED as
      duplicates rather than merged (verified line-by-line first: zero unique content). What was genuinely unique — the
      tests — was rebased onto the peer's implementation and shipped, and one of them was rewritten after it failed: it
      asserted server-side smart-tier forcing, which upstream DELIBERATELY omits for this mode (tier comes from the role
      file's frontmatter, same as its `ci_reconcile` sibling). The test now pins that real contract instead of "fixing"
      upstream to match an assumption. **Bug found and fixed in the peer's shipped code while adding those tests**: the
      `--window 6hour` guard built an ISO-8601 string PREFIX (`f"{date}T{(hour//6)*6:02d}"`) and matched with
      `startswith`, but a 6-hour bucket spans SIX clock hours and a prefix can only match one. Measured against the real
      predicate with the guard firing at 09:30: a prior run at 06:15 blocked, but 07:15 / 08:15 / 09:15 / 10:15 / 11:15
      all came back UNBLOCKED — so the 60-minute timer would have dispatched up to FIVE duplicate reconcilers per
      bucket, each burning a Max-plan slot, the exact opposite of the "at most one success per 6h bucket" the installer
      advertises. Replaced with a real timestamp comparison (`day`/`hour` keep prefix semantics byte-for-byte).
      Evidence: **agent-orchestrator@0eb0da5**, `AO_QG_EXIT=0`, **3,364 passed / 0 failed**; the parametrized negative
      control fails on hours 7-11 against the pre-fix code and passes on all six after (verified by running the new
      tests against a clean copy of the old implementation). NOTE: the earlier AO gate reporting 9 failures was HOST
      CONTENTION, not this change — the same tests passed on a stashed-clean tree, and the full suite ran 3,363 passed /
      0 failed in 264s once the host was quiet vs 776s under load 283. The timer INSTALLER remains deliberately un-run —
      see the cross-cloud WIF todo below; ship the code, hold the installer. Superseded original text: it has no timer
      and no server module today, which is why this storm sat unattended. Includes confirming AO's SA has
      `secretmanager.versions.access` on `SLACK_ALERTS_READER_BOT_TOKEN`.
- [ ] [DATA] P1. Determine which layer wrote the cefi `attempted_failed` rows (MTDS fetch vs MDPS derivation) and
      whether the 2026-08-02 ruling is inflating them. Read-only analysis; the operator's hypothesis (a 200-with-zero-
      rows is legitimately `empty_confirmed`) is the thing under test.

### New findings surfaced by the 2026-08-10 fan-out (none existed before this session)

- [ ] [DATA] P0. **⚠️ DIAGNOSIS REVERSED 2026-08-10 — READ THIS BEFORE ACTING.** The "brand-new regression / missing
      SchemaContract" framing below is WRONG and must not be acted on. A direct manifest query (`duckdb` over the cefi
      `_index/availability_index.parquet`, grouping the `SCHEMA_VALIDATION_FAILED` rows by `instrument_type`/`venue`)
      returned: `PERPETUAL/BINANCE-FUTURES 73,767 (2020-01-01→2026-01-21)`, `PERPETUAL/OKX-SWAP 38,832`,
      `PERPETUAL/BYBIT 24,678`, `PERPETUAL/KRAKEN-FUTURES 9,784`, `PERPETUAL/BITFINEX-FUTURES 2,892`,
      `FUTURE/BYBIT 128`, `PERPETUAL/DERIBIT 93`, `FUTURE/KRAKEN-FUTURES 8`. Two facts kill the original hypothesis: (a)
      the dates span **SIX YEARS of historical data**, not new capture; and (b) it is overwhelmingly **`PERPETUAL`,
      which IS registered** (perpetual was the ORIGINAL `liq_agg` type — `future` was the one added later by
      `mdps_liq_agg_contract_missing_future_instrument_type_2026_07_27`). So this is NOT a missing registration, and
      shipping one would have been a no-op. **What it actually is: a recent BACKFILL WAVE over 2020-2026 historical
      liquidations failed schema validation across every major perp venue.** The "150k in the last 24h" figure measured
      manifest WRITE time (the backfill's run time), not data date — that was misread as onset. **✅ ROOT CAUSE FOUND +
      PROVEN 2026-08-10 (second pass).** Not a regression at all: `liq_agg` has NEVER been able to write. The
      `liq_agg_{tf}` contract (`liq_shape=True`) demands `liquidation_count int64 NOT NULL` +
      `liquidation_notional_usd float64 NOT NULL`; `CefiLiquidationsAdapter` satisfies NEITHER — it builds
      `liq_count_arr` as `np.int32` (the write seam coerces `trade_count` int32→int64 but not `liquidation_count`), and
      `CandleOutput`'s field was spelled `liquidation_notional` (no `_usd`) and was never populated by any adapter,
      while the strict writer matches contract columns BY NAME. Proven by running the REAL validator
      (`unified_api_contracts.internal.schemas._validation.validate_dataframe`, the one
      `canonical_writer.py:499 _utl_write_chunk` calls under `strict=True` — NOT the `candle_write_mixin.py:~650`
      `ParquetSchemaEnforcer` pre-flight, which is a different schema source and was a wrong pointer in the earlier
      framing) over four candidate frame shapes: current shape → exactly 2 violations
      (`missing_column liquidation_notional_usd`, `wrong_dtype liquidation_count int32≠int64`); +notional +int64 → 0
      violations; extra OHLCV columns are tolerated. Corroborating measurements: (a) all 4,491 MDPS `captured`
      liquidation rows have a BLANK `instrument_id` (day/venue aggregate rows, `instrument_count` up to 190,080) — so NO
      per-instrument `liq_agg` shard has ever been captured; (b) 150,181 of the 150,182 failures have `written_at` in
      2026-08, confirming one backfill wave over six years of data dates; (c) the manifest's own `margin_type` column is
      EMPTY on every failing row, so the `@LIN`/`@INV` instrument_id suffix is the only usable margin discriminator
      (143,082 LIN · 5,522 INV · 1,578 neither). Notional arithmetic is fixed by `MarginType`'s own docstring + real
      tick files: linear `amount` is BASE units → `Σ(price×amount)`; inverse `amount` is USD-denominated contracts →
      `Σ(amount)`. Operator approved FULL remediation (fix + re-drive the ~150k cells); the ~1% unresolved-margin ids
      fail honestly rather than get a fabricated notional. Superseded framing follows for provenance only — **LIVE
      REGRESSION — cefi `liquidations` `SCHEMA_VALIDATION_FAILED` went from 1 row (2026-08-02) to 150,182 rows,
      essentially all inside 24h** — 88% of that cell and the single biggest `attempted_failed` driver fleet-wide. No
      commits touched the schema/writer files in that window, which points at an UPSTREAM venue payload-shape change our
      schema contract now rejects, not a regression we shipped. Every VM still exits 0, so this corrupts coverage
      silently. Evidence: DuckDB query over
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, discriminated by
      `service_name` + `error_reason`. Prior doc
      `/plans/archive/issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md` records this reason
      at exactly 1 row as of 2026-08-02, which is what dates the onset.
- [ ] [DATA] P2. Resolve `margin_type` for the ~1,578 cefi liquidation instrument_ids that carry NEITHER an `@LIN` nor
      an `@INV` suffix (`BINANCE-FUTURES:PERPETUAL:IP-USDC`, `BYBIT:PERPETUAL:XRPUSD`, `BYBIT:FUTURE:BTC-20250926`, …)
      from instruments-service reference data — the proper SSOT — instead of string heuristics. Surfaced by the liq_agg
      fix: the notional formula BRANCHES on margin type, so an unresolvable id must fail honestly rather than take a
      guessed branch (a wrong notional is worse than a failed shard). Until this lands, ~1% of liquidation shards stay
      `attempted_failed` with a precise unresolved-margin reason. Cross-links the same reference-data gap as
      `/plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md`.
- [ ] [SCRIPT] P3. The write seam (`canonical_writer_shaping._inject_schema_contract_columns`) coerces ONLY
      `trade_count` int32→int64 against contract dtypes. `liquidation_count` had the identical int32 defect and was
      invisible for the life of the pipeline. Either widen the coercion to every contract-declared int64 column or
      assert at the seam that adapter dtypes match the contract, so the next adapter cannot reintroduce this class.
- [ ] [SCRIPT] P1. Audit `UNCLASSIFIED_ADAPTER_ERROR` rows — 51% of the `trades` cell and 14% of `derivative_ticker`.
      The UAC enum's OWN docstring says any production occurrence is "a bug in the calling adapter", so half the trades
      cell is a self-declared bug nobody has been reading.
- [ ] [SCRIPT] P2. `meta_watchers.check_high_attempted_failed` computes a MEANINGLESS ratio: `attempted_failed` is
      counted over a TRAILING 14-DAY WINDOW (`ATTEMPTED_FAILED_TRAILING_WINDOW_DAYS=14`, `deployment-service@96271280`)
      while `captured` is ALL-TIME. Every "ratio" in every DP_RUN_MOSTLY_EMPTY alert is a 14-day numerator over an
      all-time denominator. Either window both or drop the ratio.
- [ ] [OPERATOR] P1. **Cross-cloud identity for the AO VM — prerequisite for the #17 timer.** The orchestrator VM has NO
      GCP identity at all: it is AWS EC2, `gcloud auth list` returns no credentialed accounts, there is no SA key or
      `GOOGLE_APPLICATION_CREDENTIALS`, and no AWS→GCP Workload Identity Federation pool is wired to it
      (`gcloud iam     workload-identity-pools list` shows only github-actions-pool / gitlab-wlif / aws-glue-runners /
      github-pool). So `secretmanager.versions.access` on `SLACK_ALERTS_READER_BOT_TOKEN` is NOT a one-line grant. Until
      WIF is stood up, DO NOT install the timer — a dispatched worker would spawn, fail the skill's §0 Slack read, and
      burn a slot every cycle. Ship the code, hold the installer.
- [ ] [SCRIPT] P1. Sports reference-table exporter FABRICATES `http_status=200` `FetchEvidence` for a GCS-missing
      upstream that it classifies `SOURCE_RETURNED_ZERO`. `FetchEvidence` is the gate that makes `empty_confirmed`
      trustworthy at all — fabricating it defeats the honest-absence model at its root.
- [ ] [DATA] P2. 2026-08-10 sports reference tables were falsely recorded `empty_confirmed(SOURCE_RETURNED_ZERO)` by an
      aborted mitigation run; they need a `--force` recompute once instruments-service backfills that day.
- [x] ✅ [SCRIPT] P2. Corrected a FALSE-PROGRESS claim in
      `/plans/active/issues/features_sports_compute_features_hard_fail_missing_upstream_today_2026_08_10.md`: it stated
      "Fix committed (features-service @ `305d897a`, quickmerge pending QG)" but `git cat-file -t 305d897a` returns
      `fatal: Not a valid object name` and `git log --all --grep` finds nothing on any ref — the commit never existed.
      Added a correction banner rather than deleting the text, because the pattern is the lesson: a "committed at <sha>"
      claim is only true once the sha RESOLVES. NOTE: this session's own pre-task conflict check MISSED this doc and
      wrongly concluded a new one was needed — the check searched the wrong terms.

### Remaining — not started

- [ ] [SCRIPT] P1. Chain relabel migration — part 2 of 2, operator-approved "both, sequenced". `options_chain` /
      `futures_chain` are `DataType` members in UAC but are written into the `instrument_type=` path position while
      `data_type=trades` carries the actual content. Governed by the entity-rename rule: writer, manifest, status, gate
      and UI must migrate in the SAME change. **Move, don't copy-then-delete-separately** (operator, 2026-08-10) —
      noting GCS has no atomic move, so the delete half still falls under the delete-safety protocol; check
      `scripts/backfill_defi_dex_pool_swaps_source_correction.py`'s deliberate "copy-not-move" rationale before
      overriding it.
- [ ] [SCRIPT] P2. Shard the slow date in the MDPS per-date backfill so one date cannot fail a 944/944-complete run
      (`subprocess-per-date: date=2026-08-01 TIMED OUT after 1800s`). Operator-approved. Fix the per-date timeout /
      shard the date — NOT a bigger machine, which is what the alert's canned advice wrongly suggests.
- [ ] [SCRIPT] P3. Rightsize the MDPS backfill VM class — `RESOURCE_SAMPLE` at failure showed `cpu=149.6%` (of 1600
      available) and `mem=22.1%`. Per the 2026-08-10 rightsizing HARD RULE, run `/vm-resource-rightsizing-check`.
- [ ] [SCRIPT] P3. Empty `instrument_id` in the chain-bundle path — `live_workers_streaming.py` returns early without
      writing any manifest row ("writing a row keyed on an empty instrument_id would corrupt the manifest"), so the
      shard is invisible. Cross-links
      `/plans/active/issues/cefi_batch_manifest_blank_instrument_type_on_failure_2026_07_12.md` (same axis, different
      path: MTDS failure path writes `instrument_type=""`).
- [ ] [SCRIPT] P3. Promote `_ShardedState` out of `relaunch_backfill_vm.py` into a shared helper so the next actuator
      needing cross-execution state does not re-derive the race-free pattern. Deliberately left private during the
      original fix rather than widening scope mid-change.
- [ ] [SCRIPT] P3. Flaky shellcheck under host load — `launch-expected-universe-v2-vm.sh` shellcheck killed by SIGPIPE
      (`returncode == -13`) during a contended QG run; all 180 pass in isolation. Will keep producing false reds.
- [ ] [SCRIPT] P3. Generalise the test-hermeticity guard — the pytest fake-GCS backend at `$TMPDIR/local-storage/`
      persists across runs, so ANY feature that starts writing durable state inherits the pass-then-fail trap closed ad
      hoc in `tests/conftest.py` this session.
- [ ] [SCRIPT] P3. Pre-existing QG violation not owned by this session: "Hardcoded prod project ID in tests" in
      `tests/unit/test_vm_launcher_scripts.py` (honest-coverage VM + bucket). Non-blocking today (gate still exits 0).

## Deferred work after 2026-08-10

| item                                                                                                              | state / why deferred                                                                                                                                                                                                                                                                                                                               | blocked-on                       |
| ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **deployment-service ship** (#1 relaunch state + #2/#3/#5/#6 alert accuracy)                                      | **Not done.** Code complete, lint clean, 392 tests pass, all files under the 960 cap. Gate FAILS on the basedpyright ratchet: `1268 errors > BASEDPYRIGHT_MAX_ERRORS=1259` — the two extractions (`_captured_reader.py`, `_classify.py`) added ~9 type errors above baseline. Ratchets only go DOWN, so these must be fixed, not baselined.        | nobody — pick up directly        |
| **agent-orchestrator ship** (#17)                                                                                 | **CORRECTED 2026-08-12 (/plan-reconcile): DONE.** This row was a stale pre-compaction snapshot — the doc's own checked `[x]` todo (line 187, "Make /data-pipeline-alerts-reconcile AO-schedulable") cites resolving evidence `agent-orchestrator@0eb0da5`, `AO_QG_EXIT=0`, 3,364/0 tests, matching this row's own gate figures, proving it landed. | shipped — landed                 |
| **features-service ship** (#14)                                                                                   | **CORRECTED 2026-08-12 (/plan-reconcile): DONE.** Stale pre-compaction snapshot — the doc's own checked `[x]` todo (line 172, honest-absence fix) cites the identical `FS_QG_EXIT=0, 18,387 passed` figure with a landed sha `features-service@692ce76b`, proving it shipped.                                                                      | shipped — landed                 |
| **liquidations P0 root cause**                                                                                    | **Not done.** Operator approved FULL remediation (fix + re-drive ~150k cells). Diagnosis is NOT yet complete — see the reversal in the Progress Log below.                                                                                                                                                                                         | nobody — highest-value next item |
| **#9 chain relabel migration**                                                                                    | **Not done.** Part 2 of the operator's "both, sequenced". Entity-rename scope.                                                                                                                                                                                                                                                                     | needs #8 live first (shipped)    |
| **#13 date sharding, #15 rightsizing, #11 empty instrument_id, #18 shellcheck flake, #19 test-hermeticity guard** | **Not done.** All scoped, none started.                                                                                                                                                                                                                                                                                                            | nobody                           |
| **AO ledger live verification**                                                                                   | **Cannot be done yet** in-session — SSM `send-command` failed on parameter quoting (access is fine: valid IAM identity, `i-0c9b283b31d6b5ca7` = `agent-orchestrator-vm-1`, running). Retry with a JSON parameter file.                                                                                                                             | mechanical retry                 |
| **Cross-cloud WIF for the AO VM**                                                                                 | **Operator-owned.** The AO VM has NO GCP identity at all (AWS EC2, no ADC, no SA key, no WIF pool). Blocks the #17 timer from ever being installed.                                                                                                                                                                                                | operator                         |
| **liquidations remediation execution**                                                                            | **Operator-owned** at the backfill step (re-driving ~150k cells is a VM launch + cost decision under delete-safety/launch gating).                                                                                                                                                                                                                 | operator, after root cause       |

**Recommended NEXT item: the liquidations root cause** — it is the only finding still actively degrading (~150k
attempted_failed cells accruing), and its diagnosis just reversed, so nobody should act on the old hypothesis.

## Lessons — carry these, they each cost real time

1. **A control sample is not optional before anything destructive.** The "2019 Deribit vintage" theory was refuted by
   ONE probe of a 2025 shard (identical 25-column schema, identical failure). Acting on it would have deleted 6+ years
   of good data and left the real bug (adapter routing) live. Now encoded as `/data-pipeline-alerts-reconcile` §1.5(iv).
2. **`| tail` destroys the exit code.** Three times this session a "green" gate/ship was actually a FAILURE — the
   reported code was `tail`'s. Always `rc=$?; echo "X_EXIT=$rc"; exit $rc`, never pipe the thing whose status matters.
3. **A "fixed template" claim must be read in the code, not inherited from a doc.** The `(0 → 0)` figure was ALWAYS
   interpolated; the repeated zeros were a symptom of the bucket-blind reader. The issue doc was wrong and it was
   repeated several times before an agent read the git history to inception.
4. **`ruff --fix` is WRONG for F401 on intentional re-exports** — it deletes the import and silently breaks the
   attribute paths an extraction was designed to preserve. Use `# noqa: F401` with a reason.
5. **A gate can pass and still be non-hermetic.** The pytest fake-GCS backend at `$TMPDIR/local-storage/` PERSISTS
   between runs, so a claim written by one run suppressed the alert the next run asserted on — two tests passed, then
   failed, with no code change. Run a suite TWICE before trusting it.
6. **Extraction's second-order cost**: a moved function takes its imports with it, so every `patch('<old_module>.X')`
   must be repointed. Caught in `_captured_reader` (resolve_bucket_name) — worth checking on every future extraction.
7. **Verify the emitter, don't infer it from cadence.** `gcloud logging read` on `resource.labels.job_name` proved the
   Cloud Run Job was the sole source of the storm; a cadence match alone would have been circumstantial.

## Progress Log

- **2026-08-10 (interactive, slot 1)**: Traced one pasted alert dump to root cause rather than triaging alert-by-alert.
  Key corrections made DURING the session, recorded because each was a wrong turn caught by verification rather than by
  review: (1) the "2019 Deribit vintage" hypothesis was REFUTED by a control probe of a 2025 shard — identical 25-column
  schema, identical failure — cancelling a proposed deletion of all Deribit 2019 data; (2) an initial read-modify-write
  design for the durable state was a lost-update race against the monitor's own overlapping executions, replaced with
  atomic one-object-per-fact claims; (3) two "QG green" claims were false because the background command ended in
  `tail`, so the reported exit code was tail's, not the gate's — corrected by propagating `exit $rc`. Three successive
  QG runs failed for three different causes (a SIGPIPE flake; non-hermetic state I introduced; an isort violation I
  introduced) before a genuine `QG_EXIT=0`.

- **2026-08-10 (checkpoint before compaction)**: SHIPPED this session — `unified-trading-library@3b006d9f`
  (preemption-safe manifest drain), `market-data-processing-service@93d783df` (chain adapter routing),
  `unified-trading-pm@8ad5879647` (parallel-agent rule + codex §5), `unified-trading-pm@b2c20ccdae` (parallel-agent cap
  10→5), `unified-trading-pm@280b3c0aac` (macOS physical-core detection in qg-host-governor),
  `unified-trading-pm@67c4c42f92` (QG governor default flipped token→reservation, fleet-wide). Firestore IAM
  (`roles/datastore.user` on `uts-prd-sa`) applied by the operator and verified live.

  **The throughput story, corrected twice.** I spent a long stretch attributing slow shipping to "the governor caps
  gates at 2 host-wide, so parallel gating is futile", and wrote that into codex §5. Both halves were wrong. First, the
  macOS branch of `_qg_governor_default_k` never existed, so `lscpu`+`nproc` both missing made `cores` fall back to a
  hardcoded 4 → K=2 on EVERY Mac regardless of size (a 24-core Mac Studio got 2, not 6) — fixed with
  `sysctl -n hw.physicalcpu`; it happens to yield the SAME K=2 on this 10-core box, which is why it hid. Second, and
  much bigger: the reservation ledger that replaces fixed-K admission was already fully built, tested, and LIVE on the
  AO VM since 2026-07-22 — this laptop was simply never bootstrapped, so `QG_GOVERNOR_MODE` was unset and defaulted to
  `token`. A dispatched agent, briefed to BUILD the wiring, correctly refused and verified the existing implementation
  instead. Flipping the default (operator decision, previously deferred six times) takes this host from K=2 to **8 CPU
  slots / 17.2 GB RAM budget**, verified by `--status` and by slots 1+2 resolving to the identical shared ledger. codex
  §5 has been corrected to say `K` is a token-mode backstop only.

- **2026-08-10 (post-compaction, slot 1) — liquidations P0 root cause CLOSED (diagnosis → proven cause).** The reversed
  diagnosis resolved on the second pass, and the answer was neither of the two earlier hypotheses (not a missing
  SchemaContract registration, not an upstream venue payload change). `liq_agg` has never been writable: the contract
  asks for two columns the adapter cannot supply. Method that settled it, recorded because the earlier passes each
  failed on a _pointer_ rather than on reasoning: I stopped reading call sites and ran the REAL validator over four
  candidate frame shapes, which returned the exact violation list instead of a plausible story. That also corrected an
  inherited wrong pointer — the manifest's `SCHEMA_VALIDATION_FAILED` rows come from the strict UTL writer
  (`canonical_writer.py:499`), NOT from the `candle_write_mixin.py:~650` `ParquetSchemaEnforcer` pre-flight the previous
  framing named; the two use DIFFERENT schema sources, so a fix aimed at the pre-flight would have changed nothing.
  Three measurements then bounded the blast radius and the fix's shape: the 4,491 "captured" rows are
  blank-instrument_id aggregates (so nothing has ever succeeded), `written_at` puts 150,181 of 150,182 failures in
  2026-08 (one wave, six years of data), and the manifest `margin_type` is empty on every failing row (so the
  `@LIN`/`@INV` suffix, not the manifest, must carry the linear-vs-inverse branch). **Also corrected**: PM's local
  checkout was 111 commits behind with my previous session's edits sitting dirty on top; every one of those files was
  already on origin in prettier-normalised form (verified file-by-file before discarding), so the apparent "unshipped
  work" was a stale-checkout artifact, not lost work.

- **2026-08-10 (slot 2, escalation agt-b947d5) — `mdps-cefi-2021-20260810-052119` DP-VM-002 VERIFIED as the
  already-fixed POLARS-AGGREGATED false-positive class; root causes all shipped.** The VM (SPOT, e2-standard-8, cefi
  2021 full-year MDPS backfill) did real work — run.log shows `POLARS AGGREGATED` candle writes, `PROGRESS.json` has
  `last_completed_date=2021-01-01` — then died mid-run at 07:14:52 (mem 83.2% vs 85% watchdog, backpressure at 77.1%;
  SPOT with `instanceTerminationAction=DELETE`), stranding its per-VM manifest shard (`_index/per_vm/` has NO
  `...-052119.parquet`). Pre-fix `_PROGRESS_RE` didn't match `POLARS AGGREGATED` → SILENT → false GONE_NO_CAPTURE
  CRITICAL page. Root causes + fix SHAs, all on `origin/live-defi-rollout`: (1) detector false-page →
  `deployment-service@2f077c97` (POLARS AGGREGATED → PROGRESS → EXPECTED_NO_CAPTURE; re-ran the shipped classifier on
  the real run.log → now EXPECTED_NO_CAPTURE, no page); (2) OOM on undersized machine → `deployment-service@5597e398`
  (cefi/defi → e2-highmem-8); (3) stranded shard on preemption → `unified-trading-library@3b006d9f` (preemption-safe
  per-VM drain). **Data safety verified**: availability index for cefi shows 118,549 `captured` MDPS rows for 2021
  (13,225 `attempted_failed`) + `processed_candles/by_date/day=2021-01-01/` present in GCS — the VM's death lost
  nothing; sibling VMs cover the range. **Remaining systemic issue (not this finding)**: the live fleet storm (~1000+
  SPOT mdps VMs, still spawning every ~15s, launcher `launch-mdps-sharded-backfill.sh` has no singleton guard) is the
  exit-code monitor's relaunch-budget bug — this plan's todo #1 (durable race-free relaunch state) is code-complete but
  unshipped; sibling escalation `agt-c06379` (deployment-service) is dispatched on it. This finding needs no MTDS code
  change — the MTDS side was already correct.

## Liquidations re-drive — operator decision recorded 2026-08-11

**There is nothing to migrate, delete, or overwrite.** Schema validation raises at `canonical_writer.py:537`, while
`finalize_local()` (539) and `_upload_local_to_gcs` (553) come AFTER it — so every one of the 150,182 failed cells wrote
NO parquet. There is no corrupt data on GCS; the manifest rows are honest `attempted_failed` markers doing exactly their
job. (Established from the writer's control flow, NOT from a corpus walk — single-walk discipline; a scoped prefix probe
on a few known-failed shard-days would confirm it empirically if ever needed.)

**It is therefore a re-DERIVE, not a re-FETCH.** The raw liquidation ticks are intact (704,780 `captured` rows written
by market-tick-data-service), so the work is pure recompute off existing GCS objects: no Tardis API cost, no vendor rate
limits, and the hard 1-concurrent-Tardis-VM cap does NOT apply. Launcher already exists:
`deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh` (the `mdps-*` family — which, per this plan's own
alert-accuracy finding, has ZERO Tardis references, consistent with MDPS reading from MTDS rather than the vendor).

**Operator ruling (2026-08-11): CANARY FIRST, then full.** The canary must cover at least one `@LIN` and one `@INV`
instrument so BOTH notional branches execute against real data — every number this produces is new data that did not
exist before, and a swapped linear/inverse branch would be silently plausible rather than loudly broken. Verify the
manifest rows flip to `captured` AND spot-check written `liquidation_notional_usd` values before the full run.

**Hard prerequisite: the fix must be DEPLOYED first.** `market-data-processing-service@6c2c4b6e` is on
`live-defi-rollout` only. MDPS VMs deploy from a tarball built off promoted code, so a re-drive launched before
promotion+deploy would re-derive all 150k cells and fail them identically — burning the VM and rewriting the same 150k
rows. Promotion is HEALTHY, not stalled (operator ruling: check, nudge only if genuinely stalled): this repo uses
Option-B DIRECT promotion, so the absence of `chore(promote)` PRs is expected rather than a stall, and main advanced
three times in the two hours around the ship (20:19 / 21:33 / 22:01 UTC). The commit's 21:26 UTC commit-object time
predates the 22:01 sweep, but its PUSH landed after it (the object was created before the re-gate + retry loop), so the
NEXT cycle takes it. No manual dispatch — `ldr-to-main-promote-fleet.yml` is a shared single-concurrency slot and ad-hoc
dispatches measurably starved it for 2+ hours on 2026-08-07.

- [x] ✅ [OPERATOR] P1. Canary re-drive — **MOOT, the re-drive was already in flight and the canary's question got
      answered by production**. `6c2c4b6e` promoted inside the 22:01 UTC sweep (verified by CONTENT: the adapter and its
      test file are byte-identical between `origin/main` and `origin/live-defi-rollout` — `git merge-base --is-ancestor`
      says "not on main" because Option-B promotion squashes, so ancestry is the WRONG oracle here) and the fleet began
      writing 11 minutes later. Measured 2026-08-11T14:19Z: **113,210 per-instrument liq_agg shards `captured`**, first
      at 22:37:47Z, against ZERO before the fix (the prior 4,491 all had a blank `instrument_id`). Both branches
      executed — LIN 108,575 shards / 1,310 ids, INV 3,347 / 61 ids — so the `@LIN`+`@INV` coverage the ruling required
      was satisfied on real data. `margin_type` is now populated on the manifest rows, and `MalformedTickFieldError`
      appears 3,409 times across 42 ids (the honest-failure path working). Note the launcher could NOT have expressed
      the requested canary anyway: `launch-mdps-sharded-backfill.sh` is asset_group×YEAR only — no
      `--instrument-ids`/`--data-types` pass-through — even though the MDPS CLI itself supports both.
- [x] ✅ [DATA] P0. **The canary's value-check found the fix WRONG for inverse — fixed fail-closed,
      market-data-processing-service@bcf02eb96d.** Manifest `captured` proves only that the frame satisfies the
      SchemaContract; it says nothing about whether the linear/inverse branch is the right way round. Reading the actual
      written parquet: `OKX-SWAP:PERPETUAL:BTC-USD@INV` day=2026-01-27 1d wrote **$1,769 for 19 liquidations = $93 per
      event**, against **$7,908/event** for `BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN` on the same day. A $93 BTC
      liquidation is below any venue minimum; ×100 gives
      $9,311, in line with the linear reference. Root cause: UAC
      `MarginType` says inverse USD notional is `qty × contract_size`, and `contract_size` is the venue FACE VALUE —
      $100
      for OKX `BTC-USD-SWAP`, $10 for its `ETH-USD-SWAP`, $1 for Kraken `PI_XBTUSD`/Bybit inverse — but the adapter
      shipped a bare `sum(amount)`, i.e. it assumed 1 everywhere. Linear (97% of rows) is correct and was verified
      against the same real shard ($6,318,474 = 71.4 BTC × ~$88.5k). Inverse now raises
      `MalformedTickFieldError(field="contract_size")` — operator ruling 2026-08-11 recorded in this plan's
      "Liquidations re-drive" section (`/plans/active/data_pipeline_alert_storm_root_cause_batch_2026_08_10.md`),
      applying the honest-absence contract in `/codex/02-data/honest-absence-downstream-handling.md`: a wrong notional
      is silently plausible while a failed shard is absence the coverage model already handles.
- [x] ✅ [DATA] P1. Answered the operator's question "isn't contract_size part of instrument definitions?" — **it is
      DEFINED but NOT RECORDED for CeFi.** `instruments-store-cefi-prd-*/prod/catalog.parquet` has 431,768 rows and 40
      columns and `contract_size` is not among them, even though instruments-service's own `engine/orchestrator/sink.py`
      and the UAC instruments parquet schema both declare the field. So this is a population gap, not a design gap.
      **`margin_type` IS present and correct** there (`inverse` for all four flagged ids, `linear` for the BTC-USDT
      reference) — which is a second finding: the adapter's `infer_cefi_quote_margin` string heuristic duplicates
      reference data it could read, and MDPS cannot read it anyway (T4 has no service↔service deps).
- [x] ✅ [DATA] P0. **Populated `contract_size` for CeFi instruments and gave MDPS a T4-legal read channel — inverse
      liquidation notional is now computed for real, not fail-closed.** Traced the actual gap first (Explore agent): the
      Tardis adapter already wrote `contract_size` correctly into the per-date `instruments.parquet` sink
      (`instruments-service/instruments_service/reference_data/adapters/cefi/tardis/adapter.py:872-876`) — the field was
      silently dropped one step later, in `scripts/build_instrument_catalogue.py`'s `CATALOG_COLUMNS` hardcoded
      40-column allowlist for the rolled-up `catalog.parquet` (the object the 40-columns finding above actually
      measured). Three-repo fix, shipped in dependency order: instruments-service@2e59354a10 (added `contract_size` to
      `CATALOG_COLUMNS` + the `_extract_meta`/row-dict propagation, mirroring the existing `margin_type` pattern
      exactly; +1 rollup-propagation test), unified-trading-library@d89467c24f (new
      `read_instruments_catalog_contract_size()` in `instruments_catalog_reader.py` — reads the same `catalog.parquet`
      GCS object `read_instruments_catalog_bounds` already reads, T4-legal since MDPS may not call instruments-service
      directly; refactored the shared row-lookup cache so both readers share one scan/memoization, not two),
      market-data-processing-service@3ff54776e0 (`liquidations_adapter.py`'s inverse branch now calls the new reader and
      computes `qty * contract_size`; still fails closed with `MalformedTickFieldError(field="contract_size")` on a
      genuine catalog miss — narrowed from "always" to "only when reference data doesn't have this instrument yet").
      `TestInverseFailsClosedWithoutContractSize` renamed to `TestInverseNotionalFromCatalogContractSize` per this
      todo's own instruction — real arithmetic assertions added (parametrized across OKX-SWAP $100/$10, Kraken/ Bybit
      $1), the fail-closed case kept as one test for the catalog-miss path. All three gates green (instruments-service
      5,351 passed / unified-trading-library 7,032 passed / market-data-processing-service 2,419 passed). **NOT yet
      done**: the ~4,113 already-wrong shards below still need the re-derive run — this todo only unblocks it.
- [ ] [DATA] P0. **~4,113 already-written shards carry a knowably-wrong inverse notional and are still readable.**
      Fail-closing stops NEW wrong values; it does not remove the ones on GCS, which keep their `captured` manifest rows
      so downstream features/strategy cannot tell them from correct ones. Scope at the 14:19Z snapshot (higher now — the
      fleet was still writing): `@INV` 3,347 shards — OKX-SWAP 2,172 / KRAKEN-FUTURES 667 / BYBIT 412 / DERIBIT 96 —
      plus 766 unsuffixed BYBIT shards the heuristic resolved to `inverse`. Timeframes 1d 3,030 · 4h 315 · 1h 2. The
      108,575 linear shards are correct and must NOT be touched. **Operator chose delete + manifest-flip 2026-08-11;
      that route then proved to require prod manifest SURGERY, so it is held pending a re-decision.** The blocker:
      `_merge_shard_frames`' **captured-outranks tie-break** (`_read_index.py`, added 2026-07-13 by
      `sports_index_recency_masked_captured_atoms_2026_07_13`) makes `capture_status='captured'` beat any non-captured
      row for the same key **regardless of recency** — so writing a `record_failed` row does NOT flip these shards, the
      stale `captured` row keeps winning at read time. Removing the row needs a maintenance rewrite, and UTL exposes no
      instrument-scoped removal (only `purge_venue_before_date`, venue+date-scoped, and the whole-corpus
      `rebuild_manifest_from_canonical_paths`) — i.e. exactly the operation class that destroyed 7,185 rows describing
      ~344k objects in the 2026-07-17 consolidator incident cited by the delete-safety SSOT. Deleting the objects
      WITHOUT the flip is strictly worse than today: it converts wrong-but-present data into phantom rows. **Safer route
      now available**: `--skip-existing` is opt-in (`store_true`, default False) and `--force` exists, so once
      `contract_size` lands a scoped re-derive OVERWRITES each wrong parquet in place and writes a fresh `captured` row
      — correct values, no delete, no manifest surgery. **RE-DECIDED 2026-08-11: take the re-derive route.** The earlier
      delete+flip choice is withdrawn (it predated the captured-outranks discovery); no GCS delete and no manifest
      surgery will be performed. Retagged `[OPERATOR]` → `[DATA]` because nothing here is operator-gated any more — the
      work is now entirely "land `contract_size`, then re-derive". `contract_size` landed 2026-08-11 (todo above,
      instruments-service@2e59354a10 + unified-trading-library@d89467c24f + market-data-processing-service@3ff54776e0) —
      this re-derive is now the highest-value next item; nothing else blocks it. **RE-MEASURED 2026-08-11 (continuation
      session)**: population is now 4,429 `capture_status='captured'     margin_type='inverse'` liquidations shards (up
      from ~4,113 — expected, the population moves every wave), 64 distinct instrument_ids, dates 2020-01-03 to
      2026-01-28 (query: DuckDB over
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` filtered
      `service_name='market-data-processing-service'`; `margin_type` column is authoritative and matches the
      `@INV`/unsuffixed-BYBIT heuristic exactly, 4,429 either way). **New finding: a large ambient VM fleet (439
      `mdps-cefi-{year}-*` instances, label `purpose=mdps-sharded-backfill`, `VM_OPERATION=backfill-cefi`, command
      `--operation process --mode batch --start-date {year}-01-01 --end-date {year}-12-31`, years 2019-2026, oldest
      instance created 2026-08-06 — a 5+ day standing operation, not something launched today) is independently
      reprocessing the full CEFI corpus right now and, per a direct spot-check, IS already overwriting some
      already-`captured` inverse shards with correct values: `OKX-SWAP:PERPETUAL:BTC-USD@INV` day=2022-01-29 1d,
      written_at 2026-08-11T20:43:36Z, reads `liquidation_notional_usd=6872.0` for `liquidation_count=37` (about
      $185.7/event, about 1.86 contracts x $100 face value — consistent with the fixed `contract_size` formula, NOT the
      old bare-`sum(amount)` bug). This fleet is NOT scoped to the inverse population specifically (it's a general
      per-year full reprocess) and VMs appear to pick up whichever code was current at THEIR OWN launch time (SPOT,
      preemption-recovery churns run-ts continuously — 20-43 instances per year), so convergence on the 4,429 is neither
      instant nor guaranteed complete (a VM that finished its year range before `3ff54776e0` deployed and never
      relaunches leaves that year's wrong shards untouched indefinitely). **Operator ruling 2026-08-11: prune the
      ambient duplicate fleet first (billing waste), then execute the scoped re-derive regardless of redundant
      compute.** Executed 2026-08-12 (continuation session): 1. **Fleet pruned first** (see the second remediation
      section in `/plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`) —
      411 duplicate `mdps-{cefi,tradfi,defi,sports}-{year}` VMs reaped, 485/467 running → 69/51 running. 2.
      **Re-measured before launch**: population moved 4,113 → 4,429 (2026-08-11 late) → **4,463** (2026-08-12, 64
      instrument_ids unchanged, dates 2020-01-03 to 2026-01-28) — re-measure again before quoting, it moves every
      wave. 3. **First launch attempt failed harmlessly** —
      `bash deployment-service/scripts/vm/launch-mdps-backfill-vm.sh        --force --data-types liquidations --timeframes "1d 4h 1h 15m" --instrument-ids <64 ids> --date-concurrency 4        cefi 2020-01-01 2026-01-31 full`
      created VM `mdps-backfill-cefi-20260812-014240`, which self-deleted via `VM_SHUTDOWN_ON_COMPLETION=true` within 3
      minutes, `EXIT_STATUS=2`. Root cause (found via the tee'd `gs://deployment-scripts-.../vm-logs/<vm>/run.log`,
      downloaded with UTL `download_from_storage` — never a subprocess `gcloud storage`/`gsutil`): the launcher's
      `--date-concurrency N` flag appended `--date-concurrency        N` onto the `--operation process --mode batch`
      entrypoint's own argv, but that entrypoint's argparser has no such flag (only the legacy sub-parser reached via
      `cli/main.py`'s internal bridge does) — a hard parse error, not a no-op, so the lever was silently broken every
      time anyone used it. Zero data written or touched before the crash — safe no-op, not a near-miss on correctness.
      **Fixed at the root, not worked around**: `deployment-service@decdf98fb2` changes the launcher to prepend
      `MDPS_DATE_CONCURRENCY=$DATE_CONCURRENCY` as an env var (config.py already reads it directly via `get_config()`)
      instead of appending the broken CLI flag — gate green (353s), shipped via quickmerge. 4. **Relaunched
      successfully** — VM `mdps-backfill-cefi-20260812-015953`, tarball-freshness check passed for all 5 repos
      (confirmed `market-data-processing-service-code @ a959bd0192de`, the commit carrying `3ff54776e0`'s contract_size
      fix, and `deployment-service-code @ decdf98fb2a5`, the launcher fix just shipped — same-session tarball turnaround
      confirmed fast enough to pick up a fix shipped minutes earlier). Verified via `run.log`: `MDPS_DATE_CONCURRENCY=4`
      correctly threaded (3-4 dates processing concurrently), correctly scoped to the 64 instrument_ids +
      `liquidations` + the 4 timeframes, catalogue loaded (431,890 rows, contract_size present). 5. **RAN TO COMPLETION
      (2026-08-12T05:42Z, all 2223 dates) BUT FIXED ZERO SHARDS — correcting an earlier WRONG in-session claim of
      partial success.** The mid-run spot-check above (read while the job was still running) sampled a handful of error
      lines, correctly diagnosed two REAL failure classes, and was then wrongly generalized to "the fix works, only a
      narrow sub-daily bug blocks some shards, 1d is fine (the majority)." **That was never verified against the actual
      outcome and was wrong.** Post-completion verification (this same continuation, after being asked "is liquidations
      done"): parsed the full `run.log` (`grep liquidations complete.*succeeded` across all 2,197 per-date summary
      lines) — **0 of 33,686 attempted (instrument x timeframe) writes succeeded, fleet-wide, every venue, every
      timeframe.** Confirmed three ways, not just the counter: (a) manifest re-query shows the 1d timeframe's newest
      `written_at` for the inverse population is `2026-08-11T21:57Z` — BEFORE this VM even launched; (b) direct
      `gcs_describe_object` on `OKX-SWAP:PERPETUAL:BTC-USD@INV` day=2022-01-29 1d (a shard this job explicitly
      requested) shows `last_modified=2026-08-11T20:43:36Z` — the AMBIENT fleet's write from the day before, untouched
      by this job; (c) the sub-daily failure classes are real but their combined volume (15m/1h/4h only —
      `SCHEMA_VALIDATION_FAILED` 59,290 + `MalformedTickFieldError` 39,132 + generic `candle write failed` 10,074)
      already exceeds 100% coverage of those three timeframes many times over, i.e. NOTHING got through even there.
      **The 1d timeframe (the majority of the target population) is the more serious open question**: it almost never
      appears in a success line, error line, or `ERRORS` block anywhere in the 96 MB log — correction to an even earlier
      "NEVER appears" overclaim in this same entry: a targeted re-query found exactly **20** genuine `attempted_failed`
      1d rows for the 64 target instruments, all `MalformedTickFieldError` (honest catalog-miss, mostly pre-2022 dates),
      written at scattered points throughout the run (02:10-05:29Z) — so 1d IS reachable and DOES sometimes get
      attempted. But 20 out of a target population whose 1d slice alone is ~3,030 shards means **~99% of target 1d
      shard-days have literally zero trace of ever being attempted** — not captured, not attempted_failed, not
      empty_confirmed. That's the real mystery, and two follow-up checks this session ruled OUT as the explanation: (1)
      **not a raw-data-availability/density gap** — `OKX-SWAP:PERPETUAL:BTC-USD@INV` (the running example) has 1,513
      MTDS-captured liquidation-tick days, row_count range 1-45,993 (median 49, mean 348), and the specific untouched
      reference day (2022-01-29) has 74 raw tick rows — solidly non-sparse, and this exact instrument+day was
      successfully computed by the ambient fleet BEFORE this job ran (real notional value already confirmed), so raw
      data plainly exists and is adequate; the job still never touched it. (2) **not scoped to my job alone** —
      re-querying with NO instrument filter (all venues, all instruments, entire manifest) found ZERO 1d liquidations
      captures fleet-wide with `written_at` inside the run window (2026-08-12T01:00-06:00Z), i.e. even the ~47-VM
      ambient fleet running concurrently produced no 1d liquidation writes in that window either. That's either a
      genuinely fleet-wide 1d-liquidations outage during this window, or the same underlying bug affecting every VM that
      picked up the current tarball. Root cause NOT YET FOUND: `candle_write_mixin.py`'s `not force and blob_exists()`
      skip guard (the obvious suspect) is shared code across all timeframes and correctly gates on `force`, so it
      doesn't explain a near-total 1d silence while 15m/1h/4h at least attempt (and fail) everything — needs someone to
      actually trace the 1d-specific aggregation/scheduling branch (likely NOT `aggregate_from_15s_efficient`, which is
      what throws the sub-daily density error, and likely upstream of the per-timeframe write call entirely, e.g. in
      whatever decides which timeframes to even enqueue for a given instrument+date) rather than assume it is the same
      code path as the sub-daily bug. **This P0 remains OPEN — 0% of the ~4,463-5,232-shard (population moves) target
      population is fixed.** Nothing was corrupted (failed/skipped writes leave prior rows untouched, confirmed above),
      but nothing was corrected either. **Next steps, not yet done**: (i) find why 1d attempts almost never happen under
      `--force` — likely the actual P0 blocker, more central than the sub-daily density bug, and worth checking whether
      it's also silently degrading the AMBIENT fleet's normal (non-`--force`) 1d coverage, not just this scoped
      re-derive; (ii) fix the sub-daily `aggregate_from_15s_efficient` NaN-density issue (P2 below) since it blocks 100%
      of 15m/1h/4h too, not the minority case originally described; (iii) only then re-launch and re-verify with the
      SAME rigor as this correction (parse `run.log`'s aggregate succeeded/attempted counts and spot-check GCS object
      `last_modified` directly — a "VM completed" or "some dates showed success in a sample" signal is NOT sufficient,
      both were tried and both were misleading here). **(i) SOLVED 2026-08-12 (this continuation): root cause found and
      fixed.** Traced via an Explore sub-agent, then independently verified line-by-line against the live code before
      shipping. The service's internal/legacy timeframe vocabulary is `"24h"` for daily bars — UAC's own
      `TIMEFRAME_SECONDS`/`TIMEFRAMES` registry
      (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:92-101`) has **no `"1d"` key at
      all**, only `"24h"`. `MDPS_TIMEFRAMES=1d,15m,1h,4h` (this job's exact invocation) bridges the literal token `"1d"`
      straight into `--timeframes` with zero validation (`cli/main.py:315-317`; `--timeframes` has no `choices=`
      constraint, unlike `--data-types`). That `"1d"` then reaches the actual scheduling filter,
      `BaseAdapter.get_valid_output_timeframes()` (`app/adapters/base_adapter.py:164-168`,
      `TIMEFRAME_SECONDS.get(tf, 0) >= base_secs`) — a dict-miss on the unrecognized `"1d"` key silently defaults to
      `0`, which reads as _finer than any base granularity_ (backwards — `"1d"` is the coarsest timeframe there is), so
      `"1d"` is dropped from the work list before any candle math runs, for every instrument-file, every date. Confirmed
      this is the actual call path: `process_category()` in `orchestration_service.py:169` **always** routes the
      caller's explicit `--timeframes` list through `config.resolve_timeframes()` (not conditionally, per a 2026-07-26
      fix for a related sports-scoping bug) — verified `resolve_timeframes()` had no asset-group ceiling for CEFI, so
      the literal `"1d"` token passed through unchanged into the adapter filter. **Not a downstream consequence of the
      15m/1h/4h `aggregate_from_15s_efficient` NaN-density bug (P1 below)** — the two bugs are independent; `"1d"` is
      filtered out of the timeframe list before any aggregation code is ever reached. The ~20 genuine `attempted_failed`
      1d rows found in the run.log are explained too: `orchestration_service.py`'s dependency-skip/live-gap-gate paths
      (`_record_expected_unattempted_on_skip`, `_gate_live_gap_data_types`) write manifest rows using
      `config.resolve_timeframes()`'s result directly, bypassing the adapter-level filter — those only fire on the small
      minority of dates with a genuine upstream-MTDS skip or live-connectivity gate, matching "~20 out of ~3,030."
      **Fixed at the two points that need it, not worked around**: (1) `market-data-processing-service@c9d14458fa` —
      `config.resolve_timeframes()` now normalizes `"1d"→"24h"` in the candidate list before the
      (asset-group-conditional) ceiling check, so the single choke point every explicit `--timeframes`/`MDPS_TIMEFRAMES`
      call passes through fixes every asset_group uniformly; (2) defense-in-depth, same commit —
      `BaseAdapter.get_valid_output_timeframes()` also normalizes `"1d"→"24h"` before its `TIMEFRAME_SECONDS` lookup, so
      the same dict-miss-defaults-to-0 failure mode can't silently recur for any future caller that reaches the adapter
      filter directly. Gate green (55s), shipped via quickmerge, `ahead=0` verified. **Not yet done**: re-launch the P0
      re-derive — blocked on (ii) below (the sub-daily density bug still fails 15m/1h/4h 100%), and this fix alone does
      not retroactively correct anything already on GCS; a fresh `--force` run is still required once both bugs are
      closed.
- [ ] [OPERATOR] P1. Full re-drive of the remaining cells once `contract_size` lands. The failure population has GROWN
      since the plan's original 150,182: measured 355,818 MDPS liquidation failures at 14:19Z (352,409
      `SCHEMA_VALIDATION_FAILED` + 3,409 `MalformedTickFieldError`), split LIN 335,931 / INV 12,822 / neither 7,065 —
      re-measure before quoting, this number moves with every backfill wave. **2026-08-11 continuation — likely ALREADY
      IN FLIGHT, unattributed.** Found 439 `mdps-cefi-{year}-*` VMs (`VM_OPERATION=backfill-cefi`,
      `--operation process --mode batch` per-year, 2019-2026) currently RUNNING — oldest instance created 2026-08-06, so
      this predates today and is plausibly the standing mechanism behind this exact todo (or its precursor), not a fresh
      dispatch. Nobody in this plan's history has claimed launching it. Evidence + implications recorded on the P0
      re-derive todo above (same fleet). Before marking this `[x]`, confirm who/what owns it and whether it is scoped to
      cover the full 355,818 (it is NOT `--force` per the visible `VM_BACKFILL_CMD`, so it will only fill
      `attempted_failed`/`expected_unattempted` gaps, not touch cells already wrongly `captured` — separate question
      from the P0 inverse-notional overwrite).
- [x] ✅ [SCRIPT] P2. The GCS guardrail hook's own block message told agents to
      `from unified_trading_library.cloud_interface import list_blobs` — an import that raises `ImportError`, because
      listing is a METHOD (`get_storage_client().list_blobs(bucket, prefix=...)`), not a module-level export. Hit live
      2026-08-11 while following the hook's advice after it correctly blocked a `gcloud storage` call. A guardrail that
      blocks the wrong path and then hands out a broken replacement costs every agent the same round-trip —
      agent-orchestrator@03848b608c.
- [ ] [SCRIPT] P2. `output_schemas.py`'s `expiration.applies_to={"options_chain", "futures_chain"}` is hardcoded and did
      NOT follow UAC adding `combo_chain` to `CEFI_CHAIN_INSTRUMENT_TYPES`. Bundle ROUTING follows automatically
      (`is_chain_bundle_data_type` reads the UAC frozenset), so the drift pin in `test_output_path_helpers.py` was
      re-pinned rather than widened blind — but whether a combo chain should carry `expiration` is a real domain
      question nobody has answered. Surfaced 2026-08-11 by the pin failing the whole MDPS suite, which is exactly its
      job.
- [x] ✅ [SCRIPT] P1. **Liquidations sub-daily (15m/1h/4h) candles fail schema validation on sparse-event days —
      pre-existing, unrelated to the inverse-notional fix, and TOTAL not partial.** UPGRADED P2->P1 and corrected
      2026-08-12: originally described (from a mid-run sample) as affecting "some KRAKEN-FUTURES shards" while 1d was
      unaffected. Full-log analysis after the P0 re-derive VM completed shows this is not a minority edge case: EVERY
      15m/1h/4h attempt in the entire run failed (`SCHEMA_VALIDATION_FAILED` 59,290 + `MalformedTickFieldError` 39,132 +
      generic `candle write failed` 10,074 across all venues), and separately, 1d itself never wrote anything either
      (see the P0 todo's corrected finding — a different, not-yet-diagnosed silent no-op, not this bug). Root cause of
      the sub-daily failures per the log:
      `aggregate_from_15s_efficient: N NaN values in 'open' input column — adapter density bug, expected LOCF-dense base candles`.
      **ROOT CAUSE CORRECTED 2026-08-12 (this continuation) — the `aggregate_from_15s_efficient` WARNING is a real
      symptom but a red herring for causality, not the actual failure mechanism.** Traced via an Explore sub-agent, then
      every load-bearing claim independently re-verified against the live code before shipping (contract build, schema
      fallback chain, adapter behavior — 5 separate greps/reads). The actual chain: (1) `CefiLiquidationsAdapter`
      (`app/adapters/cefi/liquidations_adapter.py`) never calls `_finalize_session_grid` — by design, confirmed correct:
      liquidations have no "prior close" concept, so LOCF-forward-filling a stale liquidation price would fabricate
      data, exactly what the UAC `liq_agg` contract avoids by declaring NO `open`/`high`/`low`/`close` columns at all
      (`liq_shape=True` branch, `unified-api-contracts/.../_candle_contracts.py`), only
      `liquidation_count`/`liquidation_notional_usd`. (2) The bug is in the SEPARATE legacy pre-flight validator:
      `mdps_ohlc_is_nullable()` (`canonical_writer_shaping.py`) loops the contract's columns looking for `open`; when
      the contract has no such column (liq_agg's case) the loop falls through to the SAME `None` sentinel used for
      "contract lookup failed entirely" — conflating two different things. (3) `get_schema_for_data_type()`
      (`schemas/output_schemas.py`) treats `ohlc_nullable is None` as "fall back to the non-nullable
      `PROCESSED_CANDLE_SCHEMA` default." (4) That schema declares `open`/`high`/`low`/`close` `nullable=False`
      unconditionally — so a liquidation-free window's structurally-NaN OHLC (the adapter always emits the
      `open`/`high`/`low`/`close` fields, NaN-filled when there's no event, since `CandleOutput` is a shared dataclass)
      fails validation and the WHOLE SHARD's write is aborted, not just the offending bar — explaining "100% of
      15m/1h/4h" (small windows → near-certain to contain an all-empty sub-window) vs "1d/24h less likely but not
      immune" (whole-day all-empty is rarer but not impossible for a thin instrument). **This is NOT scoped to 15m/1h/4h
      — 1m/5m are structurally identical (same `aggregate_from_15s_efficient` input frame, same validator chain, and
      smaller windows make an all-empty window MORE likely, not less) and 24h/1d hits the identical mechanism once
      actually scheduled (see the P0 todo's separate 1d-scheduling fix above — that fix makes 24h reachable again, and
      this fix is what keeps it from then failing the same way).** **Fixed, not worked around**:
      `market-data-processing-service@c3ec4d52a5` — `mdps_ohlc_is_nullable()` now returns `True` (nullable) when the
      contract resolves but declares no `open` column at all, distinct from the lookup-failure branch which correctly
      keeps returning `None`. This is a general fix (any future no-OHLC contract shape gets the same correct treatment),
      not a liquidations-specific special case. Added 5 regression tests (`test_schema_robustness.py`) —
      `mdps_ohlc_is_nullable` for liquidations across 15m/1h/4h/1d, plus an end-to-end NaN-OHLC-candle validation test
      mirroring the existing derivative_ticker/book_snapshot_5 regression pattern (book_snapshot_5's non-nullable
      behavior is unaffected — it still has an explicit `open` column with `nullable=False`, untouched by this branch).
      34/34 tests pass, gate green (60s), shipped. Does NOT corrupt anything (a failed write leaves the prior row
      untouched, per the captured-outranks tie-break documented above) — it blocked 100% of sub-daily liquidations
      writes fleet-wide (not just the wrong-inverse re-derive) until this fix. Evidence:
      `gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-cefi-20260812-015953/run.log`.

## Deferred work after 2026-08-11

| item                                                                                                                                                                                | state / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | blocked-on                                            |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| ~~**deployment-service ship**~~                                                                                                                                                     | ✅ **SHIPPED `0c38c00d`** (3,317 passed). Superseded row: 12 files, tree fast-forwarded clean (16 commits, no conflicts), gate re-running at pre-compact. Previously gated GREEN at `d85832ba` (3,287 passed, tests genuinely ran) BEFORE the 16-commit pull, so the code is sound; it needs one clean gate on the current HEAD then `quickmerge`. Four prior gate attempts died to environment, not code: import-pattern deep-import (fixed), ruff I001 (fixed), file-size cap 972>960 (fixed by extraction), and TWO kills — one governor RAM-watchdog while I foolishly ran it beside AO's re-gate, one session teardown.                    | nobody — pick it up, gate ALONE                       |
| ~~**PM batching checker**~~ (`scripts/finops/check_tool_call_batching.py`)                                                                                                          | ✅ **SHIPPED `8c1df0e69e`** (240 lines, verified on origin by content). Row was stale — found during `/pre-compact` still reading "Not done… Untracked" against a tree where it had already shipped.                                                                                                                                                                                                                                                                                                                                                                                                                                            | done                                                  |
| ~~**Liquidations re-drive** / **canary execution**~~                                                                                                                                | ✅ **Both resolved 2026-08-11.** `6c2c4b6e` was already on main (verify by CONTENT — squash promotion breaks ancestry) and 113,210 per-instrument shards were captured across BOTH margin branches, so the canary's coverage requirement was met by production. Its value-check then found the inverse branch wrong; fail-closed shipped as `bcf02eb96d`.                                                                                                                                                                                                                                                                                       | done                                                  |
| **Wrong inverse notional already on GCS** (~4,113 shards)                                                                                                                           | **Not done, no longer blocked.** `contract_size` landed (row below) so the re-derive-in-place route (`--force`, no delete, no manifest surgery — see the P0 todo) can run now. Fail-closing stopped new wrong values; these keep `captured` rows and stay readable downstream until the re-derive runs. Retagged `[OPERATOR]`→`[DATA]` on 2026-08-11 — nothing here needs a human decision any more.                                                                                                                                                                                                                                            | nobody — highest-value next item                      |
| ~~**`contract_size` population for CeFi**~~                                                                                                                                         | ✅ **SHIPPED 2026-08-11** — instruments-service@2e59354a10 + unified-trading-library@d89467c24f + market-data-processing-service@3ff54776e0. Real root cause was the rollup projection (`build_instrument_catalogue.py`'s `CATALOG_COLUMNS` allowlist), not the sink — see the P0 todo above for the full chain.                                                                                                                                                                                                                                                                                                                                | done                                                  |
| **VM fleet wedge + blind monitor**                                                                                                                                                  | **Mostly done.** 393 wedged VMs deleted (651→~358). The delete itself then triggered a relaunch burst (monitor read the reaped VMs as `PARTIAL_UNCONFIRMED`, fleet 250→364 in 6 min) — contained by pausing the scheduler + cancelling in-flight executions, then closed at the root: `deployment-service@ecd6d2bd90` ships a `REAPED` tombstone the classifier checks ahead of `preempted`. Monitor stays PAUSED pending deploy + tombstone-backfill of the 393 (list committed), in that order — unpausing first replays the burst. The still-untouched CAUSE (why ~398 VMs hung mid-shutdown in one hour) is a separate P1 in the issue doc. | nobody — see the issue doc for the unpause sequencing |
| **Cross-cloud WIF for the AO VM**                                                                                                                                                   | **Operator-owned.** AO VM has NO GCP identity (AWS EC2, no ADC/SA key/WIF pool). Blocks installing the data-pipeline-alerts-reconciler timer — code shipped, installer deliberately held.                                                                                                                                                                                                                                                                                                                                                                                                                                                       | operator                                              |
| **#9 chain relabel migration · #13 date sharding · #15 rightsizing · #11 empty instrument_id · #18 shellcheck flake**                                                               | **Not done.** All scoped, none started.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | nobody                                                |
| **New findings from this session** (Tardis-403 classification · adapter-error fix · pytest-timeout-vs-admission · content-sentinel skip · stale governor token · safe-doc-push P0s) | **Not done.** All filed as `- [ ]` todos in this plan / the safe-doc-push issue.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | nobody                                                |

**Recommended NEXT item (updated 2026-08-11): re-derive the ~4,113 wrong-inverse shards in place.** deployment-service
already shipped (`0c38c00d`, row above) and `contract_size` landed — nothing else blocks this. It is a scoped overwrite
(`--force`/`--skip-existing`, no GCS delete, no manifest surgery) per the P0 todo's per-venue breakdown.

## Deferred work after 2026-08-12

| item                                                                                     | state / why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | blocked-on                                               |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| **Wrong inverse notional already on GCS** (~5,232 shards, population moves — re-measure) | **First attempt FAILED — 0% fixed** (2223-date VM, 0/33,686 writes succeeded). Both root causes now ✅ **FIXED 2026-08-12**: (1) `"1d"` vs `"24h"` spelling mismatch silently dropped the 1d timeframe from scheduling entirely (`market-data-processing-service@c9d14458fa`); (2) a legacy schema-validator fallback wrongly enforced non-null OHLC on liq_agg (which has no OHLC concept at all), failing 100% of 1m/5m/15m/1h/4h/24h writes on any liquidation-free sub-window (`market-data-processing-service@c3ec4d52a5`). Both gate-green, both verified against live code before shipping, 34/34 unit tests pass. Nothing blocks a re-launch now — see the P0 todo for full evidence. | nobody — re-launch the re-derive with 3-way verification |
| ~~**VM fleet billing waste (411 duplicate year-shard VMs)**~~                            | ✅ **RESOLVED 2026-08-12.** Reaped via the sanctioned tombstone-then-delete tool after confirming the exit-code monitor was still paused (no relaunch-storm risk). 485/467 running → 69/51 running. Full write-up in `mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`'s second remediation section.                                                                                                                                                                                                                                                                                                                                                               | done                                                     |
| ~~**`launch-mdps-backfill-vm.sh --date-concurrency` broken**~~                           | ✅ **FIXED 2026-08-12** — `deployment-service@decdf98fb2`. The flag appended a nonexistent CLI flag onto the wrong entrypoint; fixed to prepend `MDPS_DATE_CONCURRENCY` as an env var instead, matching every other narrow-scope filter in the same launcher. Every prior use of this lever was silently a no-op.                                                                                                                                                                                                                                                                                                                                                                             | done                                                     |
| ~~**Stale/superseded uncommitted docs from a predecessor session**~~                     | ✅ **RESOLVED 2026-08-12.** 6 dirty files surveyed; 4 were already-archived duplicates on origin (dropped, not shipped — shipping would have recreated dead copies contradicting the real archived versions), 2 were genuine (1 recovered a retag lost to a concurrent stale-base commit, 1 a new stash-audit report) and shipped `9c3cfc9b21`. A large raw JSON data dump in the repo root was deleted (never belonged in git).                                                                                                                                                                                                                                                              | done                                                     |
| **VM fleet wedge root cause (why ~398 VMs hung mid-shutdown in one hour)**               | **Not done.** Carried forward unchanged from 2026-08-11 — the reap above treats a symptom (duplicates), not this cause.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | nobody                                                   |
| **Cross-cloud WIF for the AO VM · #9/#13/#15/#11/#18 · other 2026-08-10/11 findings**    | **Not done.** Carried forward unchanged from the 2026-08-11 table above — not touched this continuation.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | operator (WIF) / nobody (rest)                           |

**Recommended NEXT item (updated 2026-08-12, both fixes shipped): re-launch the P0 re-derive.** Both blockers are
SOLVED: (1) the 1d silent-skip (`"1d"`/`"24h"` spelling mismatch, `market-data-processing-service@c9d14458fa`) and (2)
the sub-daily/24h schema-validation false-reject (a legacy fallback wrongly enforcing non-null OHLC on liq_agg's no-OHLC
shape, `market-data-processing-service@c3ec4d52a5` — confirmed to affect 1m/5m too, not just 15m/1h/4h, though neither
was requested by the failed run). Re-launch with `--force --data-types liquidations --timeframes "1d 4h 1h 15m"` (the
same scope as before — 1m/5m were never part of the wrong-inverse population) and verify with the SAME three-way rigor
as the correction above (run.log counters + manifest `written_at` + direct GCS `last_modified` — a "VM completed" signal
alone was proven misleading here) before declaring the re-derive done.

## Lessons from the 2026-08-10/11 continuation — each cost real time

8. **Uncommitted work in a shared checkout is invisible, revertible, and looks LOST to everyone else.** This is the
   single most expensive class in the batch and it bit THREE distinct ways in one session: (a) `safe-doc-push` exited 0
   having pushed nothing, twice identically, because it quarantines the dirty tree BEFORE staging and then reads the
   resulting clean tree as "a concurrent session already landed it"; (b) a peer operation silently reverted an
   uncommitted append (323 L → 286 L) with no artifact left in the worktree, HEAD, or the autostash — it survived only
   because the author still had the text in-session; (c) a peer agent checked from its OWN slot, correctly found the
   modules on no branch/stash/reflog, reasonably concluded the work was lost, and wrote "must be RE-AUTHORED from
   scratch" into this plan. **"Not on any ref" proves UNSHIPPED, never NON-EXISTENT** — each slot is a separate clone.
   The mitigation is not vigilance, it is shipping sooner: commit at every shippable unit, and never let a ship script's
   exit code stand in for a verified `origin` read.
9. **Absence of test output means different things in a SERVICE repo and a LIBRARY repo.** `base-service.sh` streams
   pytest; `base-library.sh` CAPTURES it into `$_pytest_out` and echoes only on failure, so a passing library gate
   legitimately renders as `── TESTS ──` → `✅ Tests PASSED` with no collection line and no dots. I read that as a
   skipped-test run, escalated a P2 finding to P1 on a second occurrence that never happened, and burned a 15-minute
   forced re-gate. Verify a skip by the explicit skip LINE, a moved test COUNT, or fresh `coverage.xml`/`.coverage`
   mtimes — never by the absence of dots.
10. **The gate and the pre-commit hook enforce DIFFERENT rule sets.** A `quality-gates.sh`-green tree was still rejected
    at commit by ruff's hook config (SIM108, ternary-over-if/else). Gate-green is necessary, not sufficient — expect a
    second, narrower lint pass at commit time.
11. **A green gate can mean "tests skipped" (service repos).**
    `SHA sentinel NOT refreshed (content-sentinel HIT → tests skipped)` is logged mid-run while the SUMMARY still prints
    `ALL QUALITY GATES PASSED`, and `.qg_last_passed_sha == HEAD` still reads TRUE from an earlier full run. Caught on
    MDPS; forcing `QG_SENTINEL_DISABLE=true` moved the count 2,399 → 2,415, proving the new tests had never run.
12. **Deleting a peer's superseded helper can break tests that arrive LATER.** Removing `_probe_gcs_budget_client` was
    right (its read-modify-write budget loses updates under overlapping executions), but a subsequent 16-commit pull
    brought an autouse fixture still patching it — 64 setup errors, one cause. The fix is not a shim: the determinism
    that fixture bought is now STRUCTURAL (`budget_dir` ⇒ `local_only=True`), and the comment left in its place says so
    to stop anyone re-adding the patch.
13. **Re-gate after every pull; a gate result describes the tree it ran on.** MDPS went green, then a main→LDR backmerge
    landed 2 TradFi canon tests that a UTL ruling (`74fe04fd`, `continuous_future` no longer → `FUTURE`, after a census
    found 473,374 bundle-grain rows misclassified) had made stale. Proven not-mine by stashing and re-running on a clean
    tree before touching it.
14. **Host contention manufactures FALSE RED gates, and the governor cannot see the cause.** ~7 of 10 cores were burned
    by spinning BATS tmux fixtures the governor never admitted; it reported `reserved: 0MB, running heavy phases: 0` at
    load 283. AO failed 9 tests under load and passed 3,364/0 on a quiet host (264s vs 776s). Always re-run a suspicious
    red on a quiet host, and prove not-mine by stashing.
15. **A `git merge-base --is-ancestor` "NOT ON MAIN" verdict can be wrong when promotion squashes.** Option-B direct
    promotion doesn't fast-forward — it re-commits, so a shipped commit's object is never literally an ancestor of
    `origin/main` even though its content landed. Trusted CONTENT (byte-identical file diff) instead and it matched; the
    ancestry check alone would have wrongly re-triggered a "promotion stalled" investigation.
16. **A guardrail hook's own remediation message can be wrong, and following it costs the same round-trip as the
    violation it caught.** The GCS-object-ops block told agents to
    `from unified_trading_library.cloud_interface import list_blobs` — that import raises `ImportError`; listing is a
    method (`get_storage_client().list_blobs(...)`), not a module export. Hit live while doing exactly what the hook
    said to do after it correctly blocked a `gcloud storage` call. Fixed at the source (agent-orchestrator@03848b608c)
    rather than worked around once.
17. **Deleting a VM the monitor doesn't understand is not idempotent cleanup — it's a trigger.** Reaping 393 wedged VMs
    made `exit_code_fleet_monitor` classify them `PARTIAL_UNCONFIRMED` (indistinguishable from a preemption by
    observation) and relaunch ~108 of them in six minutes. A cleanup script that deletes infrastructure a monitor also
    watches needs to speak the monitor's language BEFORE it deletes anything, not after the recreation is already
    running. Pausing the scheduler was not sufficient containment — an execution keeps relaunching for its full timeout;
    the in-flight executions had to be cancelled too.
18. **Schema validation passing is not proof the VALUES are right.** `liq_agg`'s manifest flipping `captured` proved the
    frame satisfied the SchemaContract; it said nothing about whether the linear/inverse notional formula was correct.
    Reading the actual written parquet (not just re-running the validator) caught a 100x understatement on inverse — a
    value-check on real data is a different and necessary check from a schema-conformance check, and this session
    shipped the SECOND without ever having done the first.
19. **A truncated `tail -N` on a captured log can hide the actual failing STEP twice in a row.** Two separate `tail -8`
    reads over a multi-thousand-line gate log both showed only the terminal "FAILED" summary line, not the `❌ STEP`
    line above it — reproducing the same non-answer before switching to a full-log grep for `❌`. When a summary line
    says "see the ❌ STEP lines above" and a truncated tail doesn't show one, the tail was too short, not the log
    silent.
20. **Two identical stash-pop conflicts on the same file is the signal to stop retrying and extract selectively.**
    `git stash pop` conflicted twice on the same already-landed plan file (my own prior push, stale in the autostash).
    Resolving from `origin` and then `git checkout stash@{0} -- <one-file>` for the genuinely-needed peer file avoided a
    third blind retry and confirmed the peer's content was already on origin (0-line diff) before leaving the stash in
    place, untouched, for its owner.
21. **"VM ran to completion" and "a mid-run log sample looked fine" are BOTH insufficient proof of success — this cost a
    wrong claim that had to be corrected in-session.** Mid-run, a handful of error lines were read, correctly diagnosed
    as two real-but-survivable failure classes, and wrongly generalized to "the fix mostly works." After the VM's own
    `VM_SHUTDOWN_ON_COMPLETION` self-delete (a clean exit signal), the ACTUAL verification was: sum every
    `X/Y succeeded` counter across the full log (0/33,686), cross-check a specific GCS object's `last_modified` directly
    (untouched since before the job), and re-query the manifest for `written_at` inside the run window. Only that
    combination caught that the real result was 0% fixed, not "mostly working." A completion signal or a favorable
    sample proves the job didn't crash — it proves nothing about whether it did its job.
22. **A launcher's `DRY_RUN=true` env var can mean something completely different from what the name implies.** On
    `launch-mdps-backfill-vm.sh`, `DRY_RUN=true` skips ONLY the tarball-freshness safety check — it still creates a
    real, live, `--force`-executing VM if the positional `MODE` arg is `full`. Used once expecting a safe
    command-construction test; got a real (harmlessly failed, but real) launch instead. There is no actual "print the
    command, touch nothing" mode in this script — read the flag's own code, don't infer behavior from its name.
23. **When a "why isn't X being processed" mystery shows up, check density/data-availability directly before assuming a
    code bug (and vice versa) — both directions were verified empirically here, not guessed.** The instinct "maybe we
    just don't have the underlying data for those shards" was checked directly (MTDS capture count, row_count
    distribution, and the specific untouched shard's own tick count) and cleanly ruled out — which then correctly
    redirected the investigation to an unresolved code-path question instead of a data-completeness one.
24. **A `dict.get(key, 0)` silent default is a landmine when the dict is a controlled vocabulary and the key comes from
    an uncontrolled caller.** The 1d-timeframe bug wasn't a missing feature or an aggregation edge case — it was
    `TIMEFRAME_SECONDS.get("1d", 0)` returning `0` for an unrecognized spelling and that `0` reading as "finer than base
    granularity" (backwards for what should be the COARSEST timeframe), so a filter meant to drop overly-fine requests
    silently dropped the one request that should never have qualified for dropping at all. The service had TWO spellings
    for the same concept ("1d" UAC-canonical vs "24h" legacy-internal) with a one-way normalizer (`24h→1d`) that only
    ran at schema-lookup/manifest time — nothing normalized the OTHER direction at the scheduling layer, and
    `--timeframes` had no `choices=` validation to catch the mismatch loud. A sub-agent (Explore) traced this end-to-end
    from the CLI env-var bridge down to the exact `.get(tf, 0) >= base_secs` comparison in one pass; every claimed
    file:line was independently re-verified against the live code before the fix shipped — cheap insurance (4 grep/read
    calls) against shipping a fix for a bug that wasn't actually there.
25. **A logged WARNING at the point of suspicion is not proof of causality — trace to the actual hard failure, don't
    stop at the loudest symptom.** The sub-daily bug's own log line
    (`aggregate_from_15s_efficient: N NaN values in 'open' input column`) looked like an obvious smoking gun and the
    plan's original theory built directly on it ("LOCF-density assumption doesn't hold for sparse liquidations"). The
    real defect was two validator layers downstream — a schema lookup silently conflating "no OHLC column in this
    contract" with "contract lookup failed" — and the aggregator's own null-skipping roll-up rules were already correct.
    The WARNING and the failure were correlated (same root sparsity) but not causally linked; asking "does the code that
    logs the warning actually RAISE, or does something else downstream?" (it only `logger.warning`s, never raises —
    visible right in the same function) was the thread that unraveled the wrong theory. Same discipline as lesson 24:
    every claim from the tracing sub-agent was re-verified against the live contract-builder, schema-fallback, and
    schema-definition code before the fix shipped — a plausible, detailed, wrong theory reads identically to a correct
    one until checked.
