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
- [ ] [SCRIPT] P1. **Fix `setup-data-pipeline-vm.sh`'s `mdps-features-live` exec-dispatch branch** (~line 2474,
      `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`) to invoke MDPS via the REAL entry-point contract:
      `MDPS_OPERATION=streaming-aggregation MDPS_SHARD_SPEC=<ag>:<venue>:<data_type> "$VENV/bin/python" -m     market_data_processing_service --operation process --mode live --start-date ... --end-date ...`
      (env vars set in the subshell that backgrounds each worker, NOT
      `process --operation streaming-aggregation --shard-spec ...` as positional/flag argv the way it's written today) —
      depends on the todo above shipping first (shard-spec bridge must exist before the launcher can rely on it). Verify
      locally (no VM needed) by running the exact generated command against a real checkout before the next live-VM
      pilot. Repo: deployment-service.
- [ ] [BACKEND] P1. **Root-cause and fix the features-service `--mode live` calendar/commodity path running as a
      one-shot batch job instead of a persistent stream subscriber.** `Batch processing complete` /
      `exiting with code 1` after ~15-70s directly contradicts the "operationally launch a live consumer" premise —
      determine whether `calendar`/`commodity`'s live wiring was ever actually implemented as a subscribe-loop (per
      `features_service/common/live_cross_cutting.py`) or whether it silently falls back to the batch entrypoint when
      `--mode live` is passed without a supporting subscribe loop. Repo: features-service.
- [x] ✅ [BACKEND] P2. **Fix the `delta_one` live subscriber's unhandled Pub/Sub `subscribe_once` traceback**
      (`unified_trading_library/cloud_interface/providers/gcp.py:592`, surfaced via
      `features-service --feature-family delta_one --mode live`) — full traceback captured in this session's
      `/tmp/tradfi_run.log` scratch capture (not committed; re-triggerable by re-running the exact pilot command). Repo:
      unified-trading-library (or features-service, depending on root cause). — unified-trading-library@c50b3b89:
      `subscriber.pull()` raises `RetryError`/`DeadlineExceeded` on an empty poll (not a failure — expected outcome of
      `LiveDataSource.stream()`'s ~100ms polling loop); now caught and treated as empty-poll instead of crashing the
      async generator, and `subscribe_once()`'s timeout param is now actually forwarded to `pull()`.
- [ ] [BACKEND] P3. Fix `commodity`'s `publish_signal`:
      `[MEDIUM] validation error: asdict() should be called on     dataclass instances`. Repo: features-service.
- [ ] [OPERATOR] P1. **Decide the process-topology fix for CEFI (117 shards, confirmed OOM at e2-standard-8) and DeFi
      (3,535 shards — infeasible as one-process-per-shard on any single VM).** The 2026-07-29 topology ruling (option
      (a): one OS process per `(venue, data_type)` MDPS shard) does not scale past TradFi's 14 shards. Real options: (i)
      consolidate multiple shards into fewer async/threaded worker processes instead of 1 process per shard (bigger code
      change, most scalable), (ii) split each asset_group's cluster across N VMs by shard range (simpler, more VMs =
      more cost), (iii) a much larger single machine type per asset_group sized to shard count (doesn't fix DeFi's 3,535
      — no single VM RAM size makes 3,535 separate Python processes with full import overhead viable). This is a genuine
      architecture decision, not a lookup — needs operator sign-off before any CEFI/DeFi launch is re-attempted.
      Reference: this doc's Evidence section for the OOM proof + exact shard counts.
- [ ] [DATA] P2. **Once the above land, re-pilot TradFi first (lowest risk, 14 shards)** with the same monitoring
      approach this session used (serial-console OOM watch + full `run.log` fetch + GCS events-bucket check for real
      `candle_computed`/`features_computed` output), then re-attempt CEFI only after TradFi is confirmed genuinely live
      (persistent subscriber, not one-shot batch). Repo: deployment-service (+ market-data-processing-service,
      features-service read-only verification).
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
