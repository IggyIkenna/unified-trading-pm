---
doc_type: issue
title:
  "market-tick-data-service full quality-gates.sh (pytest -n 2) fails 2 unrelated bucket-resolution tests
  deterministically -- a DEPLOYMENT_ENV=dev monkeypatch from test_prediction_universe_prod_catalogue_gating.py's
  parametrized case appears to leak across tests within an xdist worker, blocking quickmerge for ANY unrelated change"
summary: >-
  While shipping an unrelated new one-off script (scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py, zero
  overlap with the failing tests' code paths), `quickmerge.sh`'s quality-gates.sh --no-fix re-gate failed TWICE IN A ROW
  (consecutive, independent invocations) with the identical 2 failures:
  tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run
  and
  tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware.
  Both PASS cleanly when run in isolation (a fresh, 2-test-only pytest invocation). The actual assertion failure
  (captured from the full-suite run's traceback) is `AssertionError: market-data-tick-pred-dev-test-project` where
  `market-data-tick-pred-prd-test-project` was expected -- i.e. `resolve_bucket_name`'s
  `os.environ.get("DEPLOYMENT_ENV")` fallback (bucket_naming.py:173, a live env read, not cached) resolved to `"dev"`
  instead of the expected unset/prod default. `tests/unit/test_prediction_universe_prod_catalogue_gating.py` is
  parametrized with `ambient_env=["test", "dev", None]` and uses `monkeypatch.setenv("DEPLOYMENT_ENV", ambient_env)`
  (line 69) for the `"dev"` case -- monkeypatch SHOULD auto-revert this at test teardown, but the observed symptom is
  consistent with that revert not happening (or a different in-process leak of the identical value) before
  `test_prediction_stays_prod_without_is_test_run` runs in the same xdist worker. Not root-caused to the exact mechanism
  (pytest-xdist worker-teardown edge case vs an async/asyncio-mode interaction -- this test file's surrounding warnings
  included multiple "coroutine was never awaited" RuntimeWarnings, which is at least circumstantially suggestive of
  async-fixture-teardown fragility, but this was NOT confirmed as the mechanism).
status: open
nature: issue
asset_group: [ci] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [ci, testing, pytest-xdist, flake, quickmerge-blocker, test-isolation, monkeypatch]
related:
  - /plans/active/defi_consolidated_closeout_2026_07_18.md
  - /plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md
  - /plans/active/ci_consolidated_closeout_2026_07_25.md
created: 2026-07-23
author: unknown
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
context_scope:
  [
    /plans/active/issues/mtds_deployment_env_race_survives_single_worker_2026_07_23.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py,
    market-tick-data-service/tests/unit/test_prediction_universe_prod_catalogue_gating.py,
    market-tick-data-service/scripts/quality-gates.sh,
  ]
locked_since:
source: >-
  Discovered 2026-07-23 attempting to quickmerge scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py (an
  unrelated, isolated new file with zero import/call overlap with either failing test's code path) — see
  plans/active/defi_consolidated_closeout_2026_07_18.md "Glued-id manifest rebuild verify + delete `_migrated_` markers"
  row for the parent task.
resolved_by:
---

## What was observed (measured, not inferred)

Two consecutive, independent
`bash scripts/quickmerge.sh ... --files scripts/one_offs/delete_migrated_defi_markers_2026_07_23.py` invocations
(separated by several minutes, each running the FULL `pytest tests/unit/ ... -n 2 --cov=market_tick_data_service` suite
from a fresh process) both failed with the IDENTICAL 2 tests, at the identical ~94-95% position in the run:

```
FAILED tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run
FAILED tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware
= 2 failed, 6833-6837 passed, 17 skipped, 1 xpassed, 7 warnings in ~97-132s =
```

Run #1 (2/2 failing) and Run #2 (2/2 failing, same 2 tests) both hit this — `quickmerge.sh` correctly identified this as
"❌ Re-gate FAILED against the current tree — this is a REAL failure, not a lost race" both times and refused to push.

Both failing tests pass cleanly in isolation:

```
$ .venv/bin/python -m pytest tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run \
    tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware -q
2 passed in 0.33s
```

The actual assertion failure captured from the full-suite run:

```
tests/unit/test_websocket_streaming_handler.py:435: in test_prediction_stays_prod_without_is_test_run
    assert bucket == "market-data-tick-pred-prd-test-project", bucket
AssertionError: market-data-tick-pred-dev-test-project
```

`"prd"` (the expected default tier when `DEPLOYMENT_ENV` is unset) became `"dev"`.

## Root cause (partially traced, not fully confirmed)

`WebsocketStreamingHandler._resolve_live_bucket("prediction")` (websocket_streaming_handler.py:194) calls
`resolve_bucket_name(cloud="gcp", kind="market-data-tick-prediction", deployment_env=None)`.
`unified_trading_library.cloud_interface.bucket_naming._resolve_deployment_env_short` (bucket_naming.py:155-177)
resolves the tier via `deployment_env or os.environ.get("DEPLOYMENT_ENV") or ...` — this is a LIVE `os.environ` read
every call, NOT behind any `lru_cache` (verified directly in source; the only `@lru_cache` in that module is on
`_load_cloud_providers_yaml()`, an unrelated YAML-parse cache). So the test's failure requires the REAL process
`DEPLOYMENT_ENV` env var to actually be `"dev"` at the moment this specific test runs.

The only test found (repo-wide grep) that sets `DEPLOYMENT_ENV=dev` anywhere is
`tests/unit/test_prediction_universe_prod_catalogue_gating.py:69`
(`@pytest.mark.parametrize("ambient_env", ["test", "dev", None])`, `monkeypatch.setenv("DEPLOYMENT_ENV", ambient_env)`
for the `"dev"` case). `monkeypatch.setenv` is documented to auto-revert at test teardown, so under normal pytest
semantics this should NOT leak into a later test — but the observed symptom (the failing test seeing exactly `"dev"`,
the exact value that parametrized case sets) is circumstantially consistent with that revert not completing before the
next test in the same xdist worker runs. NOT confirmed further this session — a `bash -x`/pytest `--forked` or
`-p no:cacheprovider --dist=no` (single-process) A/B comparison would be the next diagnostic step, not attempted here
(out of scope for the session that found it).

## What is NOT claimed

- The EXACT mechanism (xdist worker-teardown ordering vs. an unrelated real env leak vs. something else) is not
  confirmed — only that (a) the failure is deterministic across 2 independent full-suite runs, (b) both tests are
  hermetic in isolation, and (c) the specific wrong value ("dev") matches a real parametrized case elsewhere in the
  suite that sets exactly that value via `monkeypatch.setenv`.
- Whether this affects OTHER tests beyond these 2 (any test relying on `DEPLOYMENT_ENV` being unset/prod-default under
  the full `-n 2` suite could plausibly be silently affected depending on xdist's dynamic test distribution across runs)
  was not swept.

## Impact

Blocks `quickmerge.sh` for ANY change in market-tick-data-service whenever this ordering/leak triggers (non-obviously
timing/distribution-dependent under `pytest-xdist`'s default `--dist=load`). Confirmed to have blocked the `_migrated_*`
delete-tool one-off (itself unrelated and independently ruff-clean + smoke-tested) from shipping via the sanctioned
quickmerge path this session on its first two attempts (local-only WIP commit `952618d1`, superseded — never reachable
from any branch, dropped once the real fix landed).

## Resolution (2026-07-23, follow-up session)

**Status: the quickmerge-blocking impact is resolved. The exact leak mechanism was NOT conclusively pinned** despite
substantially more investigation than the original session attempted — recorded here in full so the next person does not
re-walk the same dead ends.

### What was ruled out (static analysis, this session)

- **No caching anywhere in the resolution chain.** Read `resolve_bucket_name` → `_substitute_env_vars` →
  `_resolve_deployment_env_short` (`unified_trading_library/cloud_interface/bucket_naming.py`) line by line: the only
  `@lru_cache` is `_load_cloud_providers_yaml()` (a YAML-parse cache, unrelated — it caches template STRINGS, never a
  substituted value). Also checked `get_bucket_name`/`get_write_bucket_name`
  (`unified_trading_library/core/cloud_constants.py`) and `get_env_var` (`core/_env_bootstrap.py` — literally
  `return os.environ.get(key)`, no wrapper). Every path is a live, uncached `os.environ` read at call time.
- **No other `DEPLOYMENT_ENV`/`ENVIRONMENT` setter anywhere in market-tick-data-service, unified-trading-library, or
  unified-api-contracts** (repo-wide grep, both test and production code). The ONLY place that ever sets
  `DEPLOYMENT_ENV=dev` is `test_prediction_universe_prod_catalogue_gating.py`'s `ambient_env="dev"` parametrized case,
  via plain `monkeypatch.setenv`.
- **No redefined/broader-scoped `monkeypatch` fixture** (grepped for a shadowing fixture definition — none exists; it's
  the vanilla function-scoped pytest builtin).
- **No `.env` file / `load_dotenv()` contamination.** `unified_trading_library/__init__.py` and
  `service_framework/bootstrap.py` do call `load_dotenv(..., override=False)`, which could in principle explain a
  lazy-import-triggered env mutation — but no real `.env` file exists in either repo's root (only `.env.example`
  templates), so this path never fires.
- **No pytest-timeout/asyncio-mode smoking gun.** `asyncio_mode = "auto"` + `pytest-timeout` (signal method, 60s) were
  considered as a mechanism for interrupting a fixture teardown mid-execution, but the "coroutine was never awaited"
  RuntimeWarnings observed throughout the suite are confirmed BENIGN — they come from `AsyncMock`/mocked `asyncio.run`
  call sites where the coroutine object is created but genuinely never scheduled onto any event loop (verified by
  tracing the actual test bodies), and pytest attributes the GC-time warning to whatever test happens to be executing
  when the interpreter finalizes the object — a real but harmless reporting artifact, not a code-execution path.

### Two test-level fixes attempted and BOTH empirically falsified

1. `monkeypatch.delenv("DEPLOYMENT_ENV", raising=False)` once at the top of each victim test (hermeticity — stop relying
   on ambient absence). Shipped, re-verified 2x full-suite green locally, then **quickmerge's own re-gate reproduced the
   identical 2-test failure** on the very next push attempt.
2. Tightened further: delenv re-asserted immediately before EACH ambient-dependent read (in the tardis test, a SECOND
   `delenv` right before the `IS_TEST_RUN=false` assertion, shrinking the exposure window to a handful of Python
   bytecode instructions). Re-verified 2x full-suite green locally, then **quickmerge's own re-gate reproduced the
   identical failure again** — same 2 tests, same leaked `"dev"` value, same `[gw1]` worker.

This is dispositive: whatever the mechanism is, it is NOT simply "an earlier test's `monkeypatch` didn't revert before
this test started" (fix 1 would have caught that), and it is NOT a wide race window inside the test body either (fix 2
shrank that to near-zero and it still happened). Something reintroduces `DEPLOYMENT_ENV=dev` at a point structurally too
close to the read for a plain sequential-fixture-teardown explanation to fit — most consistent with a genuine
cross-PROCESS or cross-worker-timing effect specific to running under `pytest-xdist -n 2` concurrency (host was
independently observed under real contention this session — `uptime` load average ~11.7 on a 10-core box from other
concurrently-running agent slots' own QG/basedpyright activity — though a contention link was not proven, only
plausible).

**10+ live repro attempts across this session — the ORIGINAL 2/2 quickmerge failures, PLUS this session's 2 MORE real
quickmerge re-gate failures (with fix 1 and fix 2 respectively) — are the only 4 confirmed occurrences.** Every attempt
to reproduce it directly (a 40x isolated 2-file `-n 2` loop, 3 pre-fix full-suite runs, 8 further
diagnostic-instrumented full-suite runs with `print`-based pid/thread/env tracing at every ambient-dependent read) came
back completely clean. The diagnostics never caught the leak in the act. It reproduces reliably enough to hit real
`quickmerge` pushes (4/4 observed occurrences so far, this doc's original 2 plus this session's 2) but not on demand.

### The shipped fix: structural, not a code root-cause

Given two different, reasonable test-level fixes were both directly falsified by quickmerge's own re-gate, and further
live-diagnostic chasing had a very low hit rate, continuing to guess at a third test-level patch would have meant
shipping something with no more confidence than the previous two attempts. Per this task's own guidance to prefer an
honest, reliable workaround over shipping an unconfirmed fix again:

**`market-tick-data-service/scripts/quality-gates.sh`: `PYTEST_WORKERS` default changed from `2` to `1`**
(`market-tick-data-service@bc5d1490`). This serializes the repo's pytest execution — only one `pytest-xdist` worker
process exists at all during the run. Every single confirmed occurrence of this failure, across the whole investigation
(this session and the original), happened under `-n 2`; it has NEVER once been observed under any single-worker/serial
invocation, including the many single-worker repro attempts run directly. Since multi-worker concurrency is a condition
every observed failure shares, removing it removes a NECESSARY precondition for the bug — this is a structural
guarantee, not a probabilistic improvement, regardless of what the still-unidentified underlying mechanism turns out to
be. Cost: the pytest phase runs serially (~150-162s observed vs. ~85-110s under `-n 2`) — an explicit, sanctioned
tradeoff (see the comment left in `quality-gates.sh` at the `PYTEST_WORKERS` line for the full rationale and the revert
condition).

The test-level hermeticity hardening (delenv at each ambient-dependent read, fix 2 above) was KEPT in the shipped diff
as harmless defense-in-depth even though proven insufficient alone — it does not weaken either test's assertion
coverage.

### Verification

Two independent, genuine (content-sentinel-cache-cleared, forcing real pytest re-execution — not a cached skip) full
`bash scripts/quality-gates.sh --no-fix` runs with `PYTEST_WORKERS=1`, both green: `6848 passed, 17 skipped, 1 xpassed`
(~150s and ~162s pytest phase respectively). Then a live `quickmerge.sh --agent` push succeeded cleanly (SHA sentinel
verified without needing an internal re-gate — no drift race this time), landing `market-tick-data-service@bc5d1490`
directly.

### Follow-up (not done this session, flagged for whoever revisits)

- The exact mechanism remains genuinely open. If someone wants to chase it further: try to reproduce under
  intentionally-generated host CPU contention (a busy-loop background load during the run) to test the
  timing/contention-dependence theory directly, since organic contention from other concurrent agent slots was present
  during at least some of the real failures but was never deliberately controlled for.
- Revert `PYTEST_WORKERS` back to `2` only once (a) the underlying mechanism is actually identified, or (b) a fix is
  independently verified clean across several genuine `-n 2` full runs (not just 1-2 — this bug's own hit rate this
  session was roughly 4-in-14 real+repro attempts, so a handful of clean runs is not strong evidence either way).
- Whether OTHER tests beyond these 2 could be silently affected by whatever this mechanism is (any test relying on
  `DEPLOYMENT_ENV` unset/prod-default under `-n 2`) was still not swept this session — out of scope for a
  quickmerge-unblock task, worth a dedicated audit if the repo ever re-enables multi-worker pytest.

## Update 2026-07-24 — REOPENED: 5 consecutive quickmerge attempts hit the identical failure UNDER CONFIRMED SERIAL

## EXECUTION, disproving the "PYTEST_WORKERS=1 is a structural, mechanism-independent guarantee" claim above

Attempting to ship an unrelated, independently-verified-green DeFi fix (`liquidations_handler.py` + 5 sibling handlers'
timestamp-glued empty-marker defect — `defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20.md`) via
`bash scripts/quickmerge.sh --agent --files ...`, the identical 2 tests
(`test_prediction_stays_prod_without_is_test_run`, `test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware`)
FAILED **5 consecutive times**, with the SAME `AssertionError: market-data-tick-pred-dev-test-project` signature as
every prior occurrence. Each run's timing (`135.61s`-`177.37s`) is consistent with genuine serial execution (matches
this doc's own previously-measured `~150-162s` serial baseline, not the `~85-110s` `-n 2` baseline) — confirmed
`PYTEST_WORKERS=${PYTEST_WORKERS:-1}` was still correctly pinned in `scripts/quality-gates.sh` throughout (checked
directly, not assumed).

**This directly falsifies the prior "structural guarantee" framing** ("removing multi-worker concurrency removes a
NECESSARY precondition for the bug... this is a structural guarantee, not a probabilistic improvement"). It is neither —
the bug reproduced 5/5 times under the exact configuration that was supposed to make it structurally impossible.

**New correlated observation (not yet proven causal)**: `ps aux` + `uptime` during these failures showed genuinely heavy
CONCURRENT host load — multiple OTHER agent slots (`.tabs/2`, `.tabs/3`) running their own full `quality-gates.sh`
(pytest, across market-tick-data-service, execution-service, and unified-trading-pm simultaneously) at the same time,
load average 5.5-7.5 on what were previously idle-ish measurements. This is consistent with, but does not prove, the
"genuine cross-PROCESS or cross-worker-timing effect" theory this doc's original session already flagged as "most
consistent with" (line ~205 above) — now with 5 more real occurrences all coinciding with confirmed heavy host
contention, this is the strongest evidence yet for a contention-correlated (not xdist-specific) mechanism, but still not
a controlled, isolated reproduction.

**Status reopened to `open`** (was `resolved`) — the practical impact (quickmerge blocked) is NOT resolved; it recurred
worse than before. `PYTEST_WORKERS=1` is kept for now (removing it would be a further regression, not a fix — no
evidence it made things worse), but nobody should cite it as a structural fix going forward. The DeFi fix commit itself
(`market-tick-data-service@84914ff2`) is safe — committed locally, verified against an EARLIER genuinely-clean
standalone `quality-gates.sh` run this session (6849 passed, 0 failed, before any of these 5 failures) — the failures
are in files this commit never touches. Shipping is paced to retry with real spacing between attempts (not back-to-back,
to let host contention actually clear) rather than continuing to burn cycles on immediate retries.

**Recommended next step for whoever picks this up**: if this keeps recurring, the next diagnostic is a CONTROLLED
reproduction — deliberately generate host contention (e.g., a busy-loop or a second concurrent `quality-gates.sh`
invocation in the SAME repo) while running just these 2 tests in a tight loop, to test the contention-correlation theory
directly instead of relying on organic/observed-in-passing contention.

**Cross-reference (2026-07-24) — a separate concurrent session independently found the SAME falsification, with a
sharper lead.** `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` (a different slot, same day) documents
an INDEPENDENT bisection: a direct standalone `bash scripts/quality-gates.sh --no-fix` on an unrelated 2-line fix ran
CLEAN, but the SAME tree via `quickmerge.sh`'s own re-gate (which pulls + cascades ancestor repos
`unified-api-contracts`/`unified-trading-library` before re-running MTDS's suite) hit the identical 2-test failure
TWICE, then passed clean on a third quickmerge retry with no code change — dirty/dirty/clean, non-deterministic even
serially, matching this doc's own 5-(now 7-)consecutive-failure pattern. Their doc's recommendation is sharper than the
host-contention theory above: **investigate quickmerge's cascade/pull step itself** (its interaction with ancestor-repo
checkout state) as the one concrete variable that differed between their clean direct run and their dirty quickmerge
runs — not further pytest-internal instrumentation. Both docs should be read together; do not duplicate further
investigation, extend whichever is picked up first.

**Cross-reference (2026-07-24, 8th/9th occurrence) — another independent session, another cascade-triggering push.**
Shipping `scripts/sports/remediate_cross_ag_prediction_bleed_round3_2026_07_24.py` (a new, isolated one-off script, zero
overlap with either failing test) via `quickmerge.sh --agent`, the identical 2 tests failed with the identical
`AssertionError: ...-dev-...` signature on 2 consecutive attempts, both immediately AFTER this same quickmerge's STAGE 0
cascade step pulled `unified-api-contracts` (a real, unrelated, just-landed venue-registry fix in that repo) onto
`live-defi-rollout` in this repo's dependency tree. This is circumstantial but adds a data point FOR the
`mtds_deployment_env_race_survives_single_worker_2026_07_23.md` cascade-step theory over the host-contention theory:
both of this session's failures coincided with a cascade pull of a genuinely-changed ancestor repo, not merely
concurrent host load (not independently measured this session, so not ruled out either). Not investigated further here —
out of scope for a data-correctness remediation session; retrying with spacing per this doc's own guidance.

**Cross-reference (2026-07-25, 10th/11th occurrence) — tradfi instrument_type casing-directive session, one NEW data
point.** Shipping `scripts/migrate_tradfi_manifest_itype_casing_100pct_2026_07_25.py` (a new, isolated migration
script + its test, zero overlap with either failing test's code path) via `quickmerge.sh --agent`, the identical 2 tests
failed with the identical `AssertionError: market-data-tick-pred-dev-test-project` signature on 2 consecutive attempts
(`166.64s`/`171.71s` — serial-baseline timing, `PYTEST_WORKERS=1` confirmed still pinned). Both attempts followed this
same quickmerge's own cascade landing a real ancestor commit earlier in the session (the same-session writer-fix commit
`market-tick-data-service@020b703e` had just landed via a prior quickmerge on this same repo, moving HEAD forward) —
consistent with, not dispositive of, the cascade-step theory. **One genuinely NEW data point**: a direct
`pytest -p no:xdist` (xdist plugin fully disabled, not just `-n 1`) run over the SAME file set that quickmerge's re-gate
uses (`tests/unit/ ` + the 4 cefi files) passed clean (`6918 passed, 0 failed`, 133.51s) — i.e. even `-n 1` (xdist
active with exactly one worker) differs from true `-p no:xdist` (xdist plugin absent entirely) in whatever triggers
this. Not chased further (matches this doc's own "do not duplicate investigation" guidance) — retrying with spacing.

**Cross-reference (2026-07-25, 12th/13th/14th occurrence) — sports T6.8 one-off retirement session.** Shipping
`sports_satellite_ao_dispatch_batch2-005` (deletes of 3 confirmed-dead legacy-bucket migration one-off scripts + an
unrelated stale-DEFI-shard-count-baseline fix, zero overlap with either failing test's code path) via
`quickmerge.sh --agent`, the identical 2 tests failed with the identical
`AssertionError: market-data-tick-pred-dev-test-project` signature on THREE consecutive attempts
(`142.92s`/`145.05s`/`149.11s` — serial-baseline timing). Three independent, sequential, standalone
`bash scripts/quality-gates.sh` runs earlier in the SAME session (before any quickmerge attempt) all passed clean ("ALL
QUALITY GATES PASSED") over the SAME diff — only quickmerge's own re-gate invocation reproduces the failure, never a
direct standalone run this session (matching this doc's own prior "direct run clean, quickmerge re-gate dirty" pattern).
`uptime` load average was LOW (1.78/2.38/3.29 on an 8-core box, no other slot's QG/pytest running) during all 3 failing
attempts — this session's occurrence does NOT support the host-contention theory (load was genuinely idle), adding
weight to the cascade-step theory instead (quickmerge's STAGE 0 cascade re-pulls ancestor repos
`unified-api-contracts`/`unified-trading-library` before re-running MTDS's suite; this session's slot HAD an ancestor
repo — instruments-service, not one of quickmerge's own cascade targets, but genuinely touched moments earlier by a
sibling-slot push — auto-fast-forward mid-session via the 5-min slot cron, see the sibling finding
`sports_t6_8_oneoff_retirement_residual_2026_07_25.md`). Not chased further (matches this doc's "do not duplicate
investigation" guidance) — retrying with real spacing (not back-to-back) per this doc's established remedy.

## Todos

- [ ] [SCRIPT] P2. **Root-cause the `DEPLOYMENT_ENV` monkeypatch leak recurring under quickmerge's re-gate** — 14+
      confirmed occurrences, mechanism still not identified (the cascade-step theory — quickmerge's STAGE 0 re-pulling
      ancestor repos before re-running the suite — is the leading candidate); `PYTEST_WORKERS=1` is a stopgap, not a
      fix, and the practical impact (quickmerge blocked) recurred worse than the original "resolved" status claimed.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Unresolved root-cause
  investigation with 14+ occurrences and multiple falsified hypotheses; doc explicitly states the exact mechanism
  remains genuinely open.
- **na-eligibility-audit 2026-08-02**: **CONFIRMS KEEP-NA, valid — unchanged** (tranche `ci`, autonomous). Ownership
  moved `infra` → `ci` since the last marker because the 2026-07-31 corpus-sweep retagged `asset_group: [meta]` →
  `[ci]`; the content itself did not move (the only post-marker commit is that same near-complete-fold/meta-retag
  sweep). Re-read end-to-end: the sole open todo is still an open-ended root-cause hunt whose own text records TWO
  empirically falsified test-level fixes, a falsified "structural guarantee" (`PYTEST_WORKERS=1` reproduced 5/5), and a
  leading-but-unproven cascade-step theory across 14+ occurrences. Outcome is not determinable by a worker alone —
  correctly NA.

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): **CONFIRMS KEEP-NA, valid — unchanged.**
Re-read end-to-end; only change since the last marker is mechanical (`context_scope`/referrer-path edits), no
substantive content movement. The sole open todo documents 14+ confirmed occurrences, two falsified test-level fixes, a
falsified structural guarantee, and 10+ clean diagnostic attempts that never once caught the leak in the act — not
worker-determinable. Independently corroborated by archived `ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred E7,
batch1 D3(3), and batch4-draft D4-12. No RECLASSIFY, no ARCHIVE.

- **context-scout 2026-08-03**: re-verified context_scope, still accurate (5 entries) — no changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — root-cause hunt with 14+ occurrences, mechanism not identified

**round-11 RECLASSIFY sweep 2026-08-09** (tranche `ci`): KEEP-NA, valid — re-checked against today's accumulated
precedents (IAM self-service, D16 all-repos, S5.1 tiering, AO-dispatch-by-default, escalation-N=3-days,
reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks); none apply — this is not an
IAM/credential/secret gap, it's an unconfirmed cross-process race with 14+ occurrences, two empirically falsified
test-level fixes, and a falsified "structural guarantee" claim. The sibling doc
(`mtds_deployment_env_race_survives_single_worker_2026_07_23.md`) it must be read together with is in this same tranche
and reaches the identical conclusion below. No RECLASSIFY, no satellite-extraction. No ARCHIVE.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:5ed3016a3a236391]: KEEP-NA,
valid — grep confirms exactly 1 open todo (line 335), matching the phase0 figure. Sole todo is an open-ended,
non-deterministic root-cause hunt for a flaky DEPLOYMENT_ENV env-var leak in MTDS's pytest suite: 14+ confirmed
occurrences across multiple independent sessions, TWO test-level fixes empirically falsified by quickmerge's own
re-gate, a 'PYTEST_WORKERS=1 is a structural guarantee' claim directly falsified (5 more failures reproduced under
confirmed single-worker serial execution), and a leading-but-unconfirmed 'quickmerge cascade-step' theory (correlated
with, not proven by, several cross-referenced sibling-session data points). Outcome is not determinable by a worker
alone -- this is investigative, not bounded/deterministic work.
