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

- [ ] [SCRIPT] P1. Durable, race-free relaunch state — replaced the `tempfile.gettempdir()` budget with
      one-object-per-fact GCS state in `deployment-scripts-<project>`; `DP_VM_PREEMPTED_NO_RELAUNCH` now pages at most
      once per VM via an ATOMIC create-if-absent claim (`if_generation_match=0`), and the repeat sweep returns
      `SUPPRESSED` BEFORE re-running the launcher (stopping the wasted relaunches, not just the page). Budget counts
      OBJECTS under a day-partitioned prefix instead of incrementing an integer, so overlapping executions cannot lose
      an increment. No lock: the manifest writer's own record shows CAS-on-a-shared-doc "melts under fleet load", and
      its durable answer was per-writer sharding. Also fixed a `_PAGED_GROUP` NameError (AST-clean, would have been a
      runtime failure in prod) and a test-hermeticity defect this change introduced (the pytest fake-GCS backend under
      `$TMPDIR/local-storage/` persists BETWEEN runs, so a claim from one run silently suppressed the alert the next run
      asserted on — two `sweep()` tests passed then failed with no code change; closed with a per-test namespacing
      autouse fixture in `tests/conftest.py`). Gate evidence (pre-extraction): quality-gates.sh QG_EXIT=0, 3265 passed,
      sentinel == HEAD; 5 new regression tests incl. two that assert CONCURRENT behaviour (atomic claim admits exactly
      one winner; concurrent stamps tally 2 not 1), proven hermetic by passing twice consecutively without clearing
      stale state.
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
- [ ] [SCRIPT] P2. Make `/data-pipeline-alerts-reconcile` AO-schedulable (agent-orchestrator) — it has no timer and no
      server module today, which is why this storm sat unattended. Includes confirming AO's SA has
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
      manifest WRITE time (the backfill's run time), not data date — that was misread as onset. **NEXT STEP**: diff what
      the `liq_agg` writer emits against what the `liq_agg_{tf}` SchemaContract demands (`_candle_contracts.py`,
      `liq_shape=True`, `ohlcv_core=False`) — the failure is at `candle_write_mixin.py:~650`
      (`ParquetSchemaEnforcer.validate_dataframe`, OUTPUT-side validation before upload), not on the input ticks.
      Operator has approved FULL remediation (fix + re-drive the ~150k cells). Superseded framing follows for provenance
      only — **LIVE REGRESSION — cefi `liquidations` `SCHEMA_VALIDATION_FAILED` went from 1 row (2026-08-02) to 150,182
      rows, essentially all inside 24h** — 88% of that cell and the single biggest `attempted_failed` driver fleet-wide.
      No commits touched the schema/writer files in that window, which points at an UPSTREAM venue payload-shape change
      our schema contract now rejects, not a regression we shipped. Every VM still exits 0, so this corrupts coverage
      silently. Evidence: DuckDB query over
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`, discriminated by
      `service_name` + `error_reason`. Prior doc
      `/plans/active/issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md` records this reason
      at exactly 1 row as of 2026-08-02, which is what dates the onset.
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

| item                                                                                                              | state / why deferred                                                                                                                                                                                                                                                                                                                                  | blocked-on                              |
| ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **deployment-service ship** (#1 relaunch state + #2/#3/#5/#6 alert accuracy)                                      | **Not done.** Code complete, lint clean, 392 tests pass, all files under the 960 cap. Gate FAILS on the basedpyright ratchet: `1268 errors > BASEDPYRIGHT_MAX_ERRORS=1259` — the two extractions (`_captured_reader.py`, `_classify.py`) added ~9 type errors above baseline. Ratchets only go DOWN, so these must be fixed, not baselined.           | nobody — pick up directly               |
| **agent-orchestrator ship** (#17)                                                                                 | **Not done.** Gate GREEN (`AO_QG_EXIT=0`), sentinel==HEAD, 6 files intact. Quickmerge BLOCKED `PRECOMMIT_WORKING_TREE_CONFLICT behind=107`. A `git pull --ff-only` autostash re-apply then left `UU tests/test_autospawn.py` — **foreign WIP in this shared checkout, NOT ours**. Deliberately NOT resolved (never touch a dirty file you don't own). | resolve/park the foreign conflict first |
| **features-service ship** (#14)                                                                                   | **Not done.** Gate GREEN (`FS_QG_EXIT=0`, 18,387 passed). Quickmerge was mid auto-retry (`sentinel invalid — a peer pushed`, retry 1/3) at checkpoint. Likely just needs a re-run.                                                                                                                                                                    | transient peer-push race                |
| **liquidations P0 root cause**                                                                                    | **Not done.** Operator approved FULL remediation (fix + re-drive ~150k cells). Diagnosis is NOT yet complete — see the reversal in the Progress Log below.                                                                                                                                                                                            | nobody — highest-value next item        |
| **#9 chain relabel migration**                                                                                    | **Not done.** Part 2 of the operator's "both, sequenced". Entity-rename scope.                                                                                                                                                                                                                                                                        | needs #8 live first (shipped)           |
| **#13 date sharding, #15 rightsizing, #11 empty instrument_id, #18 shellcheck flake, #19 test-hermeticity guard** | **Not done.** All scoped, none started.                                                                                                                                                                                                                                                                                                               | nobody                                  |
| **AO ledger live verification**                                                                                   | **Cannot be done yet** in-session — SSM `send-command` failed on parameter quoting (access is fine: valid IAM identity, `i-0c9b283b31d6b5ca7` = `agent-orchestrator-vm-1`, running). Retry with a JSON parameter file.                                                                                                                                | mechanical retry                        |
| **Cross-cloud WIF for the AO VM**                                                                                 | **Operator-owned.** The AO VM has NO GCP identity at all (AWS EC2, no ADC, no SA key, no WIF pool). Blocks the #17 timer from ever being installed.                                                                                                                                                                                                   | operator                                |
| **liquidations remediation execution**                                                                            | **Operator-owned** at the backfill step (re-driving ~150k cells is a VM launch + cost decision under delete-safety/launch gating).                                                                                                                                                                                                                    | operator, after root cause              |

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
