---
doc_type: issue
title:
  "MTDS's DEPLOYMENT_ENV test-pollution race (bc5d1490's fix) reproduces even under PYTEST_WORKERS=1 — the 'multi-
  worker is a necessary condition' claim is falsified by direct counter-evidence"
summary: >-
  `market-tick-data-service@bc5d1490` (2026-07-23, another slot) pinned `PYTEST_WORKERS=1` to work around
  `test_websocket_streaming_handler.py::test_prediction_stays_prod_without_is_test_run` and
  `test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware` both leaking a
  `DEPLOYMENT_ENV=dev` value that should have reverted at another test's teardown, on the claim that "-n 2 (multi-
  worker) is a NECESSARY condition every observed failure shares... it has NEVER once been observed, all session, in any
  single-worker/serial invocation." **Direct counter-evidence, same day, later**: shipping an unrelated 2-line fix
  (`_is_bundled_chain_shard`'s CBOE mixed-venue correction, `scripts/pipeline_e2e_check.py`) hit the IDENTICAL failure
  signature (same 2 tests, same `prd`->`dev` leak) TWICE via `quickmerge.sh`'s own re-gate, both times with `created:
  1/1 worker` explicitly printed in the pytest header (confirming `PYTEST_WORKERS=1` was honored, genuinely serial). A
  THIRD run of the exact same tree (`bash scripts/quality-gates.sh --no-fix`, no quickmerge wrapper) passed cleanly. A
  4th run (quickmerge retry, no code change from the 3rd) shipped clean. So the race reproduces serially too —
  intermittently, not deterministically either way — meaning `PYTEST_WORKERS=1` reduces but does not eliminate exposure;
  it is a mitigation, not the structural fix the commit message claims.
status: open
nature: notes
asset_group: [ci]
stage: [meta]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [pytest, flake, deployment-env, test-pollution, ci, cross-agent-followup]
related:
  [
    /plans/archive/issues/pytest_posixpath_str_drv_attributeerror_flake_2026_07_17.md,
    /plans/active/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md,
  ]
created: 2026-07-23
author: unknown
parent_epic: infrastructure_master
priority: P2
source:
  "Found autonomously (2026-07-23 continuation of tradfi_consolidated_closeout_2026_07_18) while shipping an unrelated
  CBOE chain-classification fix in market-tick-data-service — quickmerge's re-gate hit the exact failure signature
  bc5d1490 (a different slot, same day, earlier) had just claimed to structurally fix via PYTEST_WORKERS=1. Two more
  full-suite runs on the identical tree (one direct quality-gates.sh, one quickmerge retry) both passed clean with no
  code change, confirming intermittency survives serial execution too."
assigned_vm: NA
execution_scope: local-only
locked_by:
context_scope:
  [
    /plans/active/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md,
    /plans/archive/issues/pytest_posixpath_str_drv_attributeerror_flake_2026_07_17.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py,
  ]
resolved_by:
drift_direction: advance-code
depends_on: []
---

# MTDS DEPLOYMENT_ENV race survives `PYTEST_WORKERS=1` — not fully structural

## What's confirmed across both investigations (mine + bc5d1490's)

- The leak is real: `resolve_bucket_name`'s ambient `os.environ.get("DEPLOYMENT_ENV")` fallback reads `"dev"` when it
  should read unset/`"prd"`, inside exactly two tests
  (`tests/unit/test_websocket_streaming_handler.py::TestResolveLiveBucketPrediction::test_prediction_stays_prod_without_is_test_run`,
  `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py::test_adapter_resolves_canonical_cefi_bucket_is_test_run_aware`).
- The only known `DEPLOYMENT_ENV=dev` setter in-repo is `test_prediction_universe_prod_catalogue_gating.py`'s
  monkeypatch-scoped parametrized case, which should auto-revert at teardown.
- bc5d1490's own investigation (10+ full-suite repros, a 40x isolated 2-file xdist loop, pid+thread instrumentation
  across 8 more attempts) never pinned the exact leak mechanism, and claimed the failure NEVER reproduced in any
  single-worker/serial run that session — concluding `-n 2` was a necessary precondition, and shipped `PYTEST_WORKERS=1`
  as what the commit calls "a structural fix rather than a further blind test-level patch."

## What's new here: single-worker mode reproduces it too

This session (a different slot, same day, ~4 hours later), shipping an unrelated 2-line `scripts/pipeline_e2e_check.py`
change (CBOE venue classification — zero contact with `resolve_bucket_name`, `DEPLOYMENT_ENV`, or any prediction/cefi
bucket-tier code path), the identical 2-test failure fired **twice** via `quickmerge.sh`'s own re-gate, both runs
explicitly printing `created: 1/1 worker` in the pytest header — i.e. genuinely serial, `PYTEST_WORKERS=1` honored, not
a multi-worker race. Bisection performed:

1. Production-fix-only tree, direct `bash scripts/quality-gates.sh --no-fix` → **clean** (0 failures).
2. Same tree, same file, via `quickmerge.sh`'s internal re-gate (which first pulls latest + cascades ancestor repos) →
   **2 failures**, identical signature.
3. Retried step 2 again, no code change → **2 failures** again, identical signature.
4. Retried step 2 a third time, no code change → **clean** (0 failures), shipped successfully.

So across 4 consecutive runs of materially-the-same tree, the outcome was clean/dirty/dirty/clean — non-deterministic
under serial execution, contradicting "never once observed in single-worker." The one variable that DID differ between
the clean direct run (1) and the dirty quickmerge runs (2, 3) is quickmerge's own pre-gate pull/cascade step, which
touches `unified-api-contracts` and `unified-trading-library` ancestor checkouts before re-running MTDS's suite — worth
investigating whether the cascade step itself (or whatever it pulls) is part of the trigger, not pure pytest-internal
state.

## Recommendation

Don't re-open bc5d1490's `PYTEST_WORKERS=1` mitigation — it's still a reasonable harm-reduction step (fewer workers =
smaller race surface even if not zero) and reverting it would be a regression. But the commit's own "revert once the
underlying leak is root-caused AND independently verified fixed under -n 2" framing implicitly assumed serial mode was
already fully safe — it is not. Next investigation should focus on quickmerge's cascade/pull step specifically (its
interaction with ancestor-repo state), not further pytest-internal instrumentation, since that's the one concrete
difference this session's bisection identified between clean and dirty runs.

## Update (2026-07-24, same continuation, later) — stronger evidence for the cascade-step correlation

Shipping the same CBOE fix hit this **5 more times in a row** via `quickmerge.sh` (identical 2-test signature,
`1/1 worker` confirmed serial each time). Ruled out as a lead: grepped both `market-tick-data-service` and
`unified-trading-library` for any raw `os.environ["DEPLOYMENT_ENV"] = ...` write that bypasses `monkeypatch` (the only
kind that could survive a test's teardown) — found none; the sole hit
(`unified-trading-library/tests/cloud_interface/unit/test_bucket_naming.py:580`) is prose in a docstring describing a
_historical banned pattern_, not live code, and that test itself uses `monkeypatch.setenv`. No `conftest.py` autouse
fixture sets `DEPLOYMENT_ENV` in MTDS either.

**New, cleaner bisection**: immediately after the 5th quickmerge failure, ran `bash scripts/quality-gates.sh --no-fix`
directly (bypassing quickmerge entirely, same uncommitted tree, same process) → **clean** (exit 0, full green, 6888-item
suite). Retried `quickmerge.sh` again immediately after (same tree, no code change) → **landed clean** on this 6th
attempt. So the pattern across this session is now 5 dirty-via-quickmerge / 1 clean-via-quickmerge / 1
clean-via-direct-QG — reinforcing, not just suggesting, that whatever quickmerge's cascade/pull step does differently
from a bare `quality-gates.sh --no-fix` run is the actual trigger surface, not generic pytest flakiness. This session
did not have time to instrument the cascade step itself (e.g. diffing `os.environ` before/after `STAGE 0: Cascade`
completes, or checking whether the ancestor repos' own `setup.sh`/dependency-install step executes any Python in the
same shell) — that instrumentation is the concrete next step, not another blind retry loop.

## Update (2026-07-30) — a look-alike failure that is NOT this leak, root-caused and closed

While widening `PYTEST_UNIT_DIR` (`ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 11), a full
`bash scripts/quality-gates.sh --no-fix` run failed
`tests/market_interface/adapters/tradfi/test_databento_write_pipeline.py::test_bucket_resolution_uses_category_tradfi`
(a file that was NEVER gated before this todo) with a bucket ending `...-prd-test-account` instead of the test's
expected `...-prd-test-project`. Initially looked like a sibling of this doc's leak on a different variable
(`GCP_PROJECT_ID`) — but a direct repro
(`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true GCP_PROJECT_ID=test-project AWS_ACCOUNT_ID=test-account .venv/bin/python -c '...get_tick_data_bucket(...)'`,
i.e. the exact env this repo's own `tests/conftest.py` sets for EVERY test, no other test involved) reproduced the
"failing" value byte-for-byte on the very first call in a brand-new process. **Root cause: not a leak at all.**
`tests/conftest.py` sets `CLOUD_PROVIDER=local` for the whole suite, and its own comment there says exactly why: "under
CLOUD_PROVIDER=local `_active_cloud()` resolves to aws" — so `get_market_data_bucket` always takes the AWS template
(`${AWS_ACCOUNT_ID}` -> conftest's `test-account` default), never the GCP one. The test's own
`bucket.endswith("-test-project")` assertion simply assumed the GCP branch, which was never actually this suite's
default — a plain stale/wrong assertion, unrelated to any ambient-state race. Fixed by pinning
`unified_config.cloud_provider`/`.gcp_project_id` (the live singleton attributes — `monkeypatch.setenv` doesn't reach
them, since `unified_config` is built once at import and doesn't re-read `os.environ`) directly in the test via
`monkeypatch.setattr`, so it explicitly forces + asserts the GCP branch rather than depending on which branch happens to
be ambient-default. **Does not touch or explain this doc's actual DEPLOYMENT_ENV race** — left exactly as still open
below.

## Todos

- [ ] [INFRA] P2. **Instrument quickmerge's cascade/pull step** — diff `os.environ` before/after `STAGE 0: Cascade` and
      check whether ancestor repos' dependency-install steps execute Python in the same shell; per "Recommendation,"
      this is the concrete next step to root-cause the race, not another blind retry loop.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid —
`/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` Deferred **E7** (2026-07-29) explicitly rules
this class NOT bounded as currently framed: five independent investigation sessions have failed to pin the leak
mechanism, and this doc plus `/plans/active/issues/mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`
are to be "read together, do not duplicate investigation". Stays parked on that single shared blocker.

**na-eligibility-audit 2026-07-31** (tranche `ci`, autonomous): **CONFIRMS the verdict above, unchanged.** The "Update
(2026-07-30)" section added since documents a LOOK-ALIKE failure (`test_bucket_resolution_uses_category_tradfi`, a
`CLOUD_PROVIDER=local` test-suite-default assertion bug) that was root-caused as NOT the same leak and fixed separately
(not tracked as a checkbox here) — the section explicitly states it "does not touch or explain this doc's actual
DEPLOYMENT_ENV race — left exactly as still open below". Cross- verified against the live
`ci_satellite_ao_dispatch_batch2_2026_07_29.md`: todo 11 (`[x]` done) cites this doc to avoid confusion with "that
still-open, unrelated leak"; Deferred **E7** remains open/parked, unchanged. Independently corroborated by the sibling
`/ag-closeout-audit ci` skill's same-day draft `ci_satellite_ao_dispatch_batch4_2026_07_31.md` (row D4-12):
"genuinely-unbounded investigation... same as batch1 D3(3) / batch2 E7." No reclassification.

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): **CONFIRMS the verdict above, unchanged.**
Re-read end-to-end; only change since the last marker is mechanical (referrer-path repoint), no substantive content
movement. Specifically stress-tested the sole open todo ("instrument quickmerge's cascade/pull step") against the
RECLASSIFY bar since it reads more action-shaped than a pure root-cause hunt — it doesn't clear it: near-identical
instrumentation (print-based env/pid tracing) is already documented as tried and clean across 8 runs in the sibling
monkeypatch-leak doc, and this doc's own bisection found non-deterministic clean/dirty outcomes even under confirmed-
serial execution. Surface-bounded, substance-unbounded — stays KEEP-NA. No RECLASSIFY, no ARCHIVE.

## Progress Log

- **context-scout 2026-08-03**: re-verified context_scope, still accurate (4 entries) — no changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — non-deterministic race, substance-unbounded, prior verdicts stand

**round-11 RECLASSIFY sweep 2026-08-09** (tranche `ci`): KEEP-NA, valid — re-checked against today's accumulated
precedents (IAM self-service, D16 all-repos, S5.1 tiering, AO-dispatch-by-default, escalation-N=3-days,
reversibility-qualified deletes, Option B retired, GSM secret + 5 Slack webhooks); none apply. The sole open todo
("instrument quickmerge's cascade/pull step") was already explicitly stress-tested against the RECLASSIFY bar 2026-08-03
and did not clear it — near-identical instrumentation is already documented as tried and clean across 8 runs in the
sibling monkeypatch-leak doc, and this doc's own bisection found non-deterministic clean/dirty outcomes even under
confirmed-serial execution. Surface-bounded, substance-unbounded — unchanged. No RECLASSIFY, no satellite-extraction. No
ARCHIVE.

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:16fa1446d8159ec7]: KEEP-NA,
valid — grep confirms exactly 1 open todo (line 146), matching the phase0 figure. Sibling doc to the monkeypatch-leak
issue -- documents that the sibling doc's own 'PYTEST_WORKERS=1 is a structural fix' claim is empirically false
(identical leak reproduced under confirmed serial '1/1 worker' execution; clean/dirty/dirty/clean across 4 consecutive
runs of materially the same tree). The sole open todo ('instrument quickmerge's cascade/pull step') was explicitly
stress-tested against the RECLASSIFY bar on 2026-08-03 and found NOT to clear it -- near-identical print-based
instrumentation is already documented as tried-and-clean across 8 runs in the sibling doc, and this doc's own bisection
found non-deterministic clean/dirty outcomes even under confirmed-serial execution ('surface-bounded,
substance-unbounded').
