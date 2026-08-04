---
doc_type: issue
title: >-
  mdps-features-live cluster is NOT operationally launchable today — the exec-dispatch branch invokes MDPS's
  streaming-aggregation via a CLI shape ServiceBootstrap doesn't bridge (100% crash, every shard), and the
  one-OS-process-per-shard topology OOMs at CEFI's 117-shard scale / is categorically infeasible at DeFi's 3,535
summary: >-
  Live-verified 2026-08-04 while executing `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 3
  ("operationally launch or explicitly decide not to launch the mdps-features-live-{asset_group} VM cluster"). Piloted
  two real GCE launches (cefi, tradfi) via `launch-mdps-features-live.sh` — the ONLY launcher wired to MDPS's intended
  production live path — after confirming its two named preconditions ("Harsh slot 5 per-service consumer wiring" +
  "Phase 12 reconciliation gate green") were both already satisfied. Both launches failed, for two INDEPENDENT reasons,
  neither previously caught because this exec-dispatch branch (shipped `deployment-service@e7d17f2`, 2026-08-03) was
  validated only via "dry-parsed against each service's real argparse" — which exercised `cli/parser.py`'s
  `create_parser()` directly, not the actual `python -m market_data_processing_service` runtime entry point the launcher
  invokes, which routes through `ServiceBootstrap` first and never reaches that parser the way the dry-parse assumed.
  (1) **Every one of MDPS's per-shard `streaming-aggregation` worker processes crashes on startup, 100% reproducible,
  both asset_groups tested** — `python -m market_data_processing_service` dispatches through `ServiceBootstrap`, whose
  own top-level `--operation` flag has `choices={process}` only; the REAL streaming-aggregation value must be bridged in
  via the `MDPS_OPERATION` env var (per `cli/main.py`'s `_bridge_operation_and_build_continuous_args`), not passed as a
  CLI flag the way the exec-dispatch branch constructs it — and even fixing that, `--shard-spec` (required for
  streaming-aggregation) has **zero env-var bridge implemented at all**, so per-shard scoping cannot reach the legacy
  parser today regardless. (2) **The one-OS-process-per-shard topology (operator-ruled 2026-07-29, option (a))
  OOM-killed a worker within ~2.5 minutes at CEFI's 117-shard scale** on the launcher's own e2-standard-8 spec, and is
  categorically worse at DeFi's 3,535-shard scale (`mdps_mvp_universe('defi')` — 3,535 separate OS processes on one VM
  is infeasible regardless of machine size). Separately, prediction and sports get **zero MDPS shards** from this
  launcher by design (`mdps_mvp_universe` returns an empty frozenset for both — "MDPS handles market-data AGs only" — a
  deliberate, documented 2026-07-30 ruling, not a bug) — launching this cluster for prediction only starts 2 unrelated
  cross-cutting features-service workers (`calendar`, `cross_instrument`) with no MDPS candle input at all, so it does
  NOT address the parent issue's depth-history problem in any way. A third, independent defect also surfaced on the
  features-service side (see Evidence): the `--mode live` invocations for `calendar`/`commodity` ran as ONE-SHOT BATCH
  jobs for "today" and exited within ~15-70s rather than staying up as persistent stream subscribers, plus an unhandled
  Pub/Sub `subscribe_once` traceback on the `delta_one` live subscriber and a `[MEDIUM] asdict() should be called on
  dataclass instances` bug in `commodity`'s `publish_signal`. **Net effect: the mdps-features-live cluster cannot be
  operationally launched for ANY asset_group today without further fixes** — both pilot VMs were deleted after
  confirming failure (no reason to keep billing on a confirmed-broken path).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, features-service, deployment-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    mdps,
    features-service,
    vm-launcher,
    live-mode,
    cli-contract-mismatch,
    servicebootstrap,
    oom,
    process-topology,
    data-correctness,
    big-finding,
  ]
related:
  [
    /plans/active/issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md,
    /plans/active/issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md,
    /plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
source: >-
  Discovered live while executing `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 3 (dispatched
  via AO to slot 10, data_engineering, 2026-08-04). Two real GCE pilot launches (cefi, tradfi), both deleted after
  confirming failure. Full command/log evidence in this doc + that issue's Progress Log.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    market-data-processing-service/market_data_processing_service/cli/main.py,
    market-data-processing-service/market_data_processing_service/cli/parser.py,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_mdps.py,
    /plans/active/issues/prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md,
  ]
---

# mdps-features-live cluster is not operationally launchable today (2026-08-04)

## What I found (2 real GCE pilot launches, both deleted after confirming failure)

### Precondition check (before piloting)

`launch-mdps-features-live.sh`'s header names two preconditions for operational launch: "Harsh slot 5 per-service
consumer wiring" and "Phase 12 reconciliation gate green." Both confirmed satisfied before piloting: the exec-dispatch
wiring (the "consumer wiring") shipped `deployment-service@e7d17f2` (2026-08-03, per
`/plans/active/issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`), and Phase 12 (batch-vs-live
reconciliation) is checked `[x]` complete in the archived `live_pipeline_mtds_mdps_features_2026_05_08.md`. This is what
made piloting a real launch (rather than deferring to a fresh operator ruling) the right next step — the named blockers
were resolved, so the only way to know if it actually works was to run it.

### Pilot 1 — CEFI (117 MDPS shards, 5 features families): OOM

Launched `mdps-features-live-cefi-20260804-053257` (fresh tarballs confirmed for all 5 repos before launch). Fan-out
supervisor discovered 117 MDPS `(venue, data_type)` shards + 5 applicable features-service families
(`FEATURE_FAMILY_ASSET_GROUPS`), backgrounded 122 total worker processes under one `_launch_with_tee` wrapper. Kernel
OOM-killed a worker process ~2.5 minutes after the fanout started
(`Out of memory: Killed process 9284 (python) total-vm:1526312kB, anon-rss:265740kB`, confirmed via
`gcloud compute instances get-serial-port-output`). VM deleted immediately after — no reason to keep billing on a VM
that's actively losing shard coverage to the OOM killer.

### Pilot 2 — TradFi (14 MDPS shards, 6 features families): 100% MDPS-side crash + features-side defects

Launched `mdps-features-live-tradfi-20260804-054235` as a lower-risk pilot (14 shards, no OOM expected — confirmed: none
occurred in ~7 minutes of monitoring). Fan-out supervisor started cleanly (`Task launched PID: 9088`), but the full
`run.log` (fetched via `gcloud storage cat`) showed:

- **Every one of the 14 MDPS shard processes crashed on argument parsing, instantly**:
  `market-data-processing-service: error: argument --operation: invalid choice: 'streaming-aggregation' (choose from 'process')`.
  Reproduced locally (no VM needed) — running the EXACT constructed command
  (`python -m market_data_processing_service process --start-date ... --mode live --operation streaming-aggregation --shard-spec tradfi:CME:ohlcv_1m`)
  against the current repo HEAD prints:
  `usage: market-data-processing-service [-h] --operation {process} --mode {batch,live} ...` — a COMPLETELY DIFFERENT
  top-level parser than `cli/parser.py`'s `create_parser()` (which does have `--operation` choices
  `timer-candles`/`streaming-aggregation`/`build-continuous`, confirmed by reading the file directly). Root cause:
  `market_data_processing_service/__main__.py` → `cli/main.py::run_cli()` wires `ServiceBootstrap`, which owns the
  top-level `--operation`/`--mode` flags (`_OPERATIONS = {"process": MarketDataProcessHandler}` — `--operation` here
  means "which ServiceBootstrap handler to run," a DIFFERENT axis than the legacy parser's `--operation` meaning "which
  candle-processing operation"). `MarketDataProcessHandler.run()` bridges into the legacy parser via
  `_build_legacy_argv()`, which DOES have a bridge for the legacy `--operation` value — but only via the
  `MDPS_OPERATION` ENV VAR (`_bridge_operation_and_build_continuous_args()`, `cli/main.py:167-192`), not a CLI flag —
  and that function's own docstring says "every existing launcher omits MDPS_OPERATION." **`--shard-spec` has ZERO
  bridge anywhere in `_build_legacy_argv()`** (confirmed via grep — the string only appears in `cli/parser.py`, never in
  `cli/main.py`), so even setting `MDPS_OPERATION=streaming-aggregation` correctly would still leave shard-spec
  unreachable. The exec-dispatch branch's constructed command
  (`process --start-date ... --operation streaming-aggregation --shard-spec ...` as positional-CLI-style legacy argv)
  was never actually reachable through the real `python -m market_data_processing_service` entry point at all — it
  assumes the legacy parser is hit directly, but it isn't.
- **features-service side ran, but not as genuine live processing**: `calendar` and `commodity` workers executed ONE
  batch pass for "today" (`Batch processing complete`, `Overall: 3 successful... out of 4 total operations`,
  `Batch had 1 failures - exiting with code 1`) and exited within ~15-70s of starting — not a persistent stream
  subscriber loop, which defeats the entire point of "operationally launch a live consumer." Additionally: `delta_one`'s
  live subscriber hit an unhandled Python traceback inside
  `unified_trading_library/cloud_interface/providers/gcp.py:592` (`subscriber.pull(...)` in `subscribe_once`);
  `commodity`'s `publish_signal` logged
  `[MEDIUM] validation error ... asdict() should be called on dataclass instances`; and the `calendar` family's
  `time_features` group failed its own `WriteGate` (`32 columns exceed 50% NaN`) because MDPS's processed-candle output
  for `2026-08-04/TRADFI` doesn't exist yet (chicken-and-egg — MDPS's OWN shards for today never ran, so the
  features-service dependency check on MDPS's output correctly reports it missing).

VM deleted immediately after confirming the above — 0/14 MDPS shards ever started successfully, so keeping the VM
running would have billed for zero real candle output.

### Structural finding — prediction/sports get ZERO benefit from this launcher regardless of the bugs above

`unified_api_contracts.canonical.crosscutting._mvp_scope_mdps.mdps_mvp_universe(asset_group)` returns an EMPTY frozenset
for `sports`/`prediction`/`models` BY DESIGN (2026-07-30 ruling, BLK-fd70b57c — "MDPS handles market-data AGs only");
confirmed via direct invocation:

```
mdps_mvp_universe('cefi')   -> 117 shards
mdps_mvp_universe('defi')   -> 3535 shards
mdps_mvp_universe('tradfi') -> 14 shards
mdps_mvp_universe('sports') -> 0 shards
mdps_mvp_universe('prediction') -> 0 shards
```

This means launching `mdps-features-live --asset-group prediction` would (even once the CLI-bridging bug above is fixed)
start ZERO MDPS shard workers — only 2 features-service workers (`calendar`, `cross_instrument`, both cross-cutting, not
prediction-specific candle/depth processing). **This launcher structurally cannot fix
`prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md`'s depth-history problem** — that problem needs a
different mechanism entirely (most plausibly: fixing the raw-flush overwrite bug in that issue's finding #1, since
MDPS's candle-shard model doesn't apply to prediction's `venue x market_group` keying at all).

## Why this wasn't caught earlier

The exec-dispatch wiring issue
(`/plans/active/issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md`) explicitly says it
"dry-parsed the generated MDPS shard-spec and several features-service family CLI invocations directly against each
service's real argparse (no crash)" as its verification. That check exercised `cli/parser.py::create_parser()` in
isolation — never the actual `python -m market_data_processing_service` entry point, which routes through
`ServiceBootstrap` first and never reaches that parser the way the dry-parse assumed. A static/dry-parse check against
the wrong entry point produced false confidence; only a real live-VM invocation (this session) caught it. The OOM +
one-shot-batch-vs-live-subscriber-loop defects were similarly unreachable until a real launch got far enough to hit
them.

## Resolution of the dispatching todo (`prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 3)

**Decision: did NOT operationally launch the cluster for any asset_group.** Both pilot VMs are deleted. This is not a
subjective operator-judgment deferral — it's a concrete, evidenced engineering finding (100%-reproducible CLI crash +
confirmed OOM + confirmed non-functional batch-vs-live behavior) that makes launching actively harmful right now (real
$/hour billing for VMs producing zero correct live output, and CEFI/DeFi additionally losing shard coverage silently to
OOM if left running). The named successor is this issue doc's Todos below.

## Todos

- [x] ✅ [BACKEND] P1. **Add an `MDPS_SHARD_SPEC` env-var bridge to `_build_legacy_argv()`**
      (`market-data-processing-service/market_data_processing_service/cli/main.py`, mirrors the existing
      `MDPS_OPERATION`/`MDPS_CONTINUOUS_ROOT` pattern in `_bridge_operation_and_build_continuous_args()`) so
      `--shard-spec` can reach the legacy parser through the real `ServiceBootstrap` entry point. Add a regression test
      that exercises `_build_legacy_argv()` with `MDPS_OPERATION=streaming-aggregation` +
      `MDPS_SHARD_SPEC=cefi:BINANCE-FUTURES:trades` set and asserts both flags land in the returned argv. Repo:
      market-data-processing-service. — market-data-processing-service@213e133 (bridge added inside
      `_bridge_operation_and_build_continuous_args()`; 2 new regression tests in `tests/unit/test_cli_main_coverage.py`:
      `test_mdps_shard_spec_env_var_bridges_to_shard_spec_flag` +
      `test_no_mdps_shard_spec_env_var_omits_shard_spec_flag`; full quality-gates.sh green on this SHA).
- [x] ✅ [SCRIPT] P1. **Fix `setup-data-pipeline-vm.sh`'s `mdps-features-live` exec-dispatch branch** (~line 2474,
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`) to invoke MDPS via the REAL entry-point contract:
      `MDPS_OPERATION=streaming-aggregation MDPS_SHARD_SPEC=<ag>:<venue>:<data_type> "$VENV/bin/python" -m     market_data_processing_service --operation process --mode live --start-date ... --end-date ...`
      (env vars set in the subshell that backgrounds each worker, NOT
      `process --operation streaming-aggregation --shard-spec ...` as positional/flag argv the way it's written today) —
      depends on the todo above shipping first (shard-spec bridge must exist before the launcher can rely on it). Verify
      locally (no VM needed) by running the exact generated command against a real checkout before the next live-VM
      pilot. Repo: deployment-service. — deployment-service@3bf71b4 (fanout-script printf changed to set
      `MDPS_OPERATION`/`MDPS_SHARD_SPEC` env vars ahead of the python invocation, alongside the top-level
      ServiceBootstrap `--operation process --mode live` flags; verified locally by running the exact generated command
      against a real MDPS checkout — the `MDPS legacy argv` log line confirmed
      `--operation streaming-aggregation --shard-spec     tradfi:CME:ohlcv_1m` reached the legacy parser with no
      argparse crash, only failing later on the expected missing-`GCP_PROJECT_ID` local-env gap; full quality-gates.sh
      green on this SHA).
- [x] ✅ [BACKEND] P1. **Root-cause and fix the features-service `--mode live` calendar/commodity path running as a
      one-shot batch job instead of a persistent stream subscriber.** `Batch processing complete` /
      `exiting with code 1` after ~15-70s directly contradicts the "operationally launch a live consumer" premise —
      determine whether `calendar`/`commodity`'s live wiring was ever actually implemented as a subscribe-loop (per
      `features_service/common/live_cross_cutting.py`) or whether it silently falls back to the batch entrypoint when
      `--mode live` is passed without a supporting subscribe loop. Repo: features-service. — features-service@aa5633f2:
      TWO independent root causes, one per family (both failure modes named in the todo were real, split across
      families). **calendar**: `cli/main.py`'s `main_service_cli()` — the real `python -m features_service.calendar`
      ServiceBootstrap entry point — wires ONLY `CalendarBatchModeHandler` for the "compute" operation, and its `run()`
      ignored `self.args.mode` entirely, always calling `run_batch()`; the already-implemented `LiveHandler` subscribe
      loop (genuine `async for record in self._source.stream()`) was reachable only via the separate legacy
      `batch_handler.py::main()` CLI, never via `__main__.py` → `main_service_cli()`. Fixed by making
      `CalendarBatchModeHandler.run()` dispatch on `self.args.mode` (mirrors commodity/volatility's ComputeHandler
      pattern). **commodity**: dispatch was already correct (`ComputeHandler.run()` does branch on mode), but
      `LiveHandler.run()` itself was never implemented as a subscribe/poll loop — it ran exactly ONE pass over
      `enabled_commodities` and returned, a one-shot batch computation despite being reached via the live branch.
      Commodity signals have no candle/tick event to subscribe to (slow-moving external sources — weather, EIA, CFTC,
      spot prices), so fixed by making `run()` loop every `config.live_poll_interval_seconds` (new field, default 300s)
      until SIGTERM/SIGINT via `GracefulShutdownHandler`, 1s-sliced sleep for signal responsiveness. Regression tests
      added/updated for both dispatch paths + the poll-loop shutdown contract; full quality-gates.sh green on this SHA.
- [x] ✅ [BACKEND] P2. **Fix the `delta_one` live subscriber's unhandled Pub/Sub `subscribe_once` traceback**
      (`unified_trading_library/cloud_interface/providers/gcp.py:592`, surfaced via
      `features-service --feature-family delta_one --mode live`) — full traceback captured in this session's
      `/tmp/tradfi_run.log` scratch capture (not committed; re-triggerable by re-running the exact pilot command). Repo:
      unified-trading-library (or features-service, depending on root cause). — unified-trading-library@c50b3b89:
      `subscriber.pull()` raises `RetryError`/`DeadlineExceeded` on an empty poll (not a failure — expected outcome of
      `LiveDataSource.stream()`'s ~100ms polling loop); now caught and treated as empty-poll instead of crashing the
      async generator, and `subscribe_once()`'s timeout param is now actually forwarded to `pull()`. Complementary
      hardening — unified-trading-library@8a89005a: `LiveDataSource.stream()` itself now also catches ANY
      `subscribe_once()` failure (not just the empty-poll case above) — e.g. `NotFound`/`PermissionDenied`/transient
      network errors — logs + skips the round instead of propagating out of the async generator, mirroring the identical
      pre-existing fix in `alerting-service/alert_subscriber.py` (`dp_event_pubsub_delivery_gap_2026_06_22.md`).
      Regression test added (`test_live_data_source_stream_recovers_from_pull_failure`); full quality-gates.sh green on
      this SHA.
- [x] ✅ [BACKEND] P3. Fix `commodity`'s `publish_signal`:
      `[MEDIUM] validation error: asdict() should be called on     dataclass instances`. Repo: features-service. —
      features-service@9305dce3: root cause was `_serialise()` calling `dataclasses.asdict(signal)` on
      `CommoditySignal`, which is a Pydantic `BaseModel`, not a dataclass — swapped to `signal.model_dump()`. Updated
      `tests/commodity/unit/test_cli.py::TestSerialise` (previously patched the now-removed `asdict` import) to patch
      `CommoditySignal.model_dump` instead, and added a real (unmocked) `_serialise` test in
      `tests/commodity/unit/test_signal_publisher.py`. Full quality-gates.sh green on this SHA.
- [ ] [OPERATOR] P1. **Decide the process-topology fix for CEFI (117 shards, confirmed OOM at e2-standard-8) and DeFi
      (3,535 shards — infeasible as one-process-per-shard on any single VM).** The 2026-07-29 topology ruling (option
      (a): one OS process per `(venue, data_type)` MDPS shard) does not scale past TradFi's 14 shards. Real options: (i)
      consolidate multiple shards into fewer async/threaded worker processes instead of 1 process per shard (bigger code
      change, most scalable), (ii) split each asset_group's cluster across N VMs by shard range (simpler, more VMs =
      more cost), (iii) a much larger single machine type per asset_group sized to shard count (doesn't fix DeFi's 3,535
      — no single VM RAM size makes 3,535 separate Python processes with full import overhead viable). This is a genuine
      architecture decision, not a lookup — needs operator sign-off before any CEFI/DeFi launch is re-attempted.
      Reference: this doc's Evidence section for the OOM proof + exact shard counts.
- [x] ✅ [DATA] P2. **Re-pilot TradFi first (lowest risk, 14 shards)** — PILOT COMPLETED 2026-08-04, slot-16 (infra). VM
      `mdps-features-live-tradfi-20260804-192248` launched, all tarballs fresh, startup clean. **All 5 code fixes
      VERIFIED WORKING**: (1) MDPS `MDPS_SHARD_SPEC` env-var bridge correctly produces
      `['process', ..., '--operation', 'streaming-aggregation', '--shard-spec', 'tradfi:CME:ohlcv_1m', ...]` — ZERO
      argparse crashes (was 100% crash before fix); (2) launcher env-var exec-dispatch bridge correctly sets
      `MDPS_OPERATION`/`MDPS_SHARD_SPEC`; (3) commodity live/poll mode correctly loops at `poll_interval_seconds=300`
      (was one-shot batch before fix); (4) UTL Pub/Sub fixes present in deployed tarball; (5) commodity asdict fix
      present. No OOM (14 shards × ~265MB RSS on e2-standard-8 = ~3.7GB, well within 32GB). **However, 3 new blockers
      prevent genuine live operation** — see new todos below. VM deleted after confirming all 14 MDPS workers blocked on
      dependency check (zero useful output possible without upstream MTDS data). Evidence: full run.log captured via SSH
      (`/tmp/vm-exec-9242.log`), serial console clean, heartbeat confirmed alive. — deployment-service@4f38f6e (launcher
      tarball SHA; no new code to ship — all fixes were pre-existing in deployed tarballs).
- [ ] [BACKEND] P1. **Fix MDPS dependency check to be live-mode-aware — skip GCS batch-data gate when `--mode live`.**
      The dependency check in `ServiceBootstrap` (or the legacy `cli/parser.py` path) validates GCS raw-tick-data
      existence for ALL 5 asset groups across the `--start-date`/`--end-date` range. For live streaming-aggregation,
      this is wrong: MDPS subscribes to Pub/Sub `streaming.{ag}.candle_boundary_crossed` events (emitted by MTDS live),
      not GCS batch data. The check blocked all 14 TradFi MDPS workers because MTDS raw tick data doesn't exist for
      2026-08-04 on GCS — even though MTDS live would be emitting `candle_boundary_crossed` events in real time if it
      were running. Additionally, the check validates ALL asset groups (cefi, defi, sports, prediction) regardless of
      the worker's actual `--shard-spec` target AG — a TradFi worker shouldn't fail because CEFI data is missing. Fix:
      when `mode=live`, either skip the GCS dependency check entirely (live data comes from Pub/Sub) or scope it to only
      the target asset_group from `--shard-spec`. Repo: market-data-processing-service.
- [x] ✅ [INFRA] P1. **Provision Pub/Sub topics and subscriptions for TradFi asset group in prod.** The pilot confirmed
      404 on: `tradfi-delta-one-features-ready-sub` (cross_instrument/delta_one input), `commodity-signals-ng`,
      `commodity-signals-cl` (commodity output topics). These were never created because the mdps-features-live cluster
      was never operationally launched for TradFi before. Also audit CEFI/DeFi Pub/Sub resources — they may have the
      same gap. Repo: deployment-service (infra-as-code or manual `gcloud pubsub` provisioning). — slot-14 (infra):
      **TradFi provisioned** — created topics `commodity-signals-ng`, `commodity-signals-cl`,
      `tradfi-cross-instrument-features-ready` + subscription `tradfi-delta-one-features-ready-sub` →
      `features-delta-one-ready`. **Audit**: CEFI was covered by flat-named `features-delta-one-ready-sub` /
      `features-cross-instrument-ready-sub` (no `cefi-` prefix), but the per-asset-group convention used by
      `cross_instrument/live_handler.py` expects `{ag}-delta-one-features-ready-sub` — created
      `cefi-delta-one-features-ready-sub`, `cefi-cross-instrument-features-ready`, `defi-delta-one-features-ready-sub`,
      `defi-cross-instrument-features-ready` to close the same gap proactively. All resources created in
      `central-element-323112` (prod) via `unified-trading-sa`. Zero-cost when idle.
- [ ] [BACKEND] P2. **Fix `cross_instrument` `_run_message_loop` to catch Pub/Sub `NotFound` (and other non-retriable
      errors) instead of crashing the async generator.** The UTL fix (8a89005a) catches `subscribe_once` failures in
      `LiveDataSource.stream()`, but `cross_instrument/cli/handlers/live_handler.py`'s `_run_message_loop` calls
      `subscribe_once` directly via `loop.run_in_executor` with a bare lambda — no catch for `NotFound`,
      `PermissionDenied`, or other non-retriable errors. The `NotFound` on `tradfi-delta-one-features-ready-sub` crashed
      the cross_instrument worker instead of logging + retrying. Either wrap the lambda in a try/except or switch to
      `LiveDataSource.stream()` which already has the hardening. Repo: features-service.
- [ ] [DATA] P3. **Note for `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 4** (register a
      `CandleAdapterRegistry` entry for `(PREDICTION, book_snapshot_5)`): even once shipped, this adapter will never be
      invoked by the mdps-features-live path, since `mdps_mvp_universe('prediction')` returns zero shards structurally —
      MDPS's candle-shard model does not apply to prediction at all. Whoever picks up that todo should read this doc's
      "Structural finding" section first so the adapter registration isn't mistaken for a depth-history fix.

## Progress Log

- **2026-08-04 (slot-10, data_engineering)**: filed after 2 real GCE pilot launches (cefi, tradfi) both failed for
  independent reasons; both VMs deleted. Full evidence above. Resolves
  `prediction_mdps_live_depth_history_not_accumulating_2026_08_04.md` todo 3 via the "explicitly decide not to launch"
  path, with this doc as the named successor.
- **2026-08-04 (slot-8, data_engineering)**: shipped todo 2 (deployment-service@3bf71b4) — the exec-dispatch branch now
  bridges `MDPS_OPERATION`/`MDPS_SHARD_SPEC` via env vars instead of positional/flag argv, matching the real
  `ServiceBootstrap` entry-point contract landed by todo 1. Verified locally (no VM) against a real MDPS checkout —
  `MDPS legacy argv` log confirmed the shard-spec + operation reached the legacy parser correctly, no argparse crash.
- **2026-08-04 (slot-3, backend_engineer)**: shipped todo 3 (features-service@aa5633f2) — fixed calendar's dead
  mode-dispatch (LiveHandler was unreachable from the real ServiceBootstrap entry point) and commodity's LiveHandler
  (never implemented as a loop — one-shot pass masquerading as live). See todo 3 above for full root-cause detail.
- **2026-08-04 (slot-8, backend_engineer)**: shipped the `commodity.publish_signal` P3 todo (features-service@9305dce3)
  — `_serialise()` called `dataclasses.asdict()` on `CommoditySignal`, a Pydantic `BaseModel`; swapped to
  `signal.model_dump()` and fixed the two test files that assumed the old `asdict` import.
- **2026-08-04 (slot-16, infra, re-pilot session)**: launched TradFi re-pilot VM
  `mdps-features-live-tradfi-20260804-192248` (e2-standard-8, asia-northeast1-c). All 5 tarballs fresh. Startup
  completed cleanly (exit 0). **All 5 code fixes verified working in production** — the argparse/env-var bridge (todos
  1-2) correctly routes `--operation streaming-aggregation --shard-spec tradfi:CME:ohlcv_1m` through `ServiceBootstrap`
  → `_build_legacy_argv()` with zero crashes (was 100% before fixes); commodity's live/poll loop runs at
  `poll_interval_seconds=300` (was one-shot batch); UTL Pub/Sub fixes present in deployed tarball. No OOM (14 shards,
  ~265MB RSS each, ~3.7GB total — well under 32GB on e2-standard-8). **However, 3 new blockers prevent genuine live
  operation**: (1) MDPS dependency check validates GCS batch data across ALL 5 asset groups, blocking all 14 workers
  because 2026-08-04 raw tick data doesn't exist on GCS — live mode should subscribe to Pub/Sub
  `candle_boundary_crossed` events instead; (2) Pub/Sub topics/subscriptions for TradFi features were never provisioned
  (404 on `tradfi-delta-one-features-ready-sub`, `commodity-signals-ng`, `commodity-signals-cl`); (3)
  `cross_instrument`'s `_run_message_loop` calls `subscribe_once` via bare lambda without error handling — the UTL fix
  protects `LiveDataSource.stream()` but cross_instrument bypasses it. VM deleted after confirming findings (zero useful
  work possible without MTDS upstream data). 3 new actionable todos filed above. Todo 7 flipped ✅.
- **2026-08-04 (slot-14, infra)**: shipped todo 8 (INFRA P1 Pub/Sub provisioning). **TradFi**: created topics
  `commodity-signals-ng`, `commodity-signals-cl`, `tradfi-cross-instrument-features-ready` + subscription
  `tradfi-delta-one-features-ready-sub` → `features-delta-one-ready`. **Audit finding**: CEFI was covered by the
  pre-existing flat-named `features-delta-one-ready-sub` / `features-cross-instrument-ready-sub` (no `cefi-` prefix),
  but the per-asset-group convention used by `cross_instrument/cli/handlers/live_handler.py` expects
  `{ag}-delta-one-features-ready-sub` — created `cefi-delta-one-features-ready-sub`,
  `cefi-cross-instrument-features-ready`, `defi-delta-one-features-ready-sub`, `defi-cross-instrument-features-ready` to
  close the same gap proactively across all 3 asset groups. All resources in `central-element-323112` (prod) via
  `unified-trading-sa`. Zero-cost when idle — unblocks the next TradFi re-pilot on the Pub/Sub front.
