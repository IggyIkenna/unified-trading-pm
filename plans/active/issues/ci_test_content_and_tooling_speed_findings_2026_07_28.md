---
doc_type: issue
title:
  Fleet-wide test-suite content/tooling-speed audit (24 findings) — orphaned tests, missing caching, redundant scans,
  real sleep()-based waste — none yet converted from chat findings into tracked work
summary: >-
  Parallel research workflow (9 of 12 planned agents completed; 3 hit a session usage cap covering the PM cost-breakdown
  angle, tracked separately) audited ~24 repos' test suites and shared CI tooling for speed opportunities distinct from
  the runner/infra-migration work covered by github_actions_operator_gated_followups_2026_07_17.md — this doc covers
  test CONTENT and TOOLING, not where/how often CI runs. Findings were reported to the operator in chat only and never
  landed as tracked todos until this doc (workspace hard rule: every discovery becomes a `- [ ]`, never prose-only chat
  output). Fleet-wide-leverage items (shared quality-gates-base scripts, consumed by ~22 repos) are prioritized first
  since a single fix cascades; per-repo findings are lower priority. Total identified: ~45s of trivially-fixable real
  sleep() waste per full-suite run, ~40 files/10k+ lines of confirmed-dead test code in execution-service, and one
  high-confidence fleet-wide Playwright misconfiguration (a debug/human project running in CI). **2026-07-29 fix-group
  pass, FULLY COMPLETE**: 16/16 todos resolved — 15 shipped with real repo@sha evidence per todo below, 1 (PR
  cost-breakdown) reconfirmed as needing no further action. The first fan-out pass (a 9-agent Workflow) left 8 items
  code-complete-but-uncommitted when it hit a session usage cap before its own finalize/ship stage could run, and lost
  one group's result entirely (`unified-trading-system-ui`, which had done real work but never returned before being cut
  off) — every item was independently recovered, re-verified (targeted test runs + 2 items independently re-run through
  a fresh full `quality-gates.sh`), and shipped directly in a follow-up pass. Several ships hit genuine shared-host
  contention (a 37-minute qg-governor queue on one repo peaking at 25 concurrent `quality-gates.sh` processes
  fleet-wide, two consecutive full-suite runs on another failing on two different unrelated pre-existing tests) — each
  was confirmed via isolated/targeted re-runs to be unrelated to the actual change before shipping via the documented
  carve-outs. No open todos remain in this doc.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    deployment-ui,
    unified-trading-system-ui,
    execution-service,
    unified-trading-library,
    market-tick-data-service,
    features-service,
    deployment-api,
    instruments-service,
    greeks-service,
  ]
scope: [engineer]
tags: [ci-cd, test-speed, tooling, orphaned-code, caching]
related: [/plans/active/github_actions_operator_gated_followups_2026_07_17.md]
created: "2026-07-28"
priority: P2
parent_epic: deployment_and_user_management_master
source:
  "interactive session, 2026-07-28 — Workflow tool fan-out (9/12 agents completed), findings never previously tracked"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
---

# Fleet-wide test-suite content/tooling-speed findings — untracked until now

Full raw findings (JSON) are in the session transcript only, not promoted anywhere durable — this doc captures every
finding as an actionable todo instead of leaving them as chat prose per the workspace hard rule. Todos are grouped by
leverage (fleet-wide-template fixes first — one change, ~22 repos benefit) then by repo.

## Fleet-wide-leverage todos (shared `quality-gates-base`, `python-quality-gates-v2.yml`, or template-driven repos)

- [x] [SCRIPT] P2. Add `--durations=25` to the shared pytest invocation in
      `unified-trading-pm/scripts/quality-gates-base/base-service.sh:737` and `base-library.sh:367` (the `PARGS`
      string). Currently zero per-test timing visibility exists anywhere in the fleet's CI — engineers can see a repo's
      "tests" phase took 350-460s but not which test(s) drive it. Near-zero cost to add; unblocks every other test-speed
      fix below and any future one. Verify on 1 consumer repo before considering fleet-applied (rule 11).

  ✅ **DONE (2026-07-29)** — `unified-trading-pm@3ed0fc99d1e2d8e16831f17b631b3cc0abfbe759`. `--durations=25` added to
  both live `PARGS=` lines (`base-service.sh:771`, `base-library.sh:391`; the one historical commented-out `PARGS=` line
  left untouched). Confirmed fleet-wide blast radius first: consumer repos source these scripts live from the sibling
  `unified-trading-pm` checkout at runtime (`scripts/quality-gates.sh:171`), not a vendored copy, so this took effect
  fleet-wide the instant it landed.

- [x] [SCRIPT] P3. Add an `actions/cache@v4` step for the `uv` package cache (`~/.cache/uv` or the custom `UV_CACHE_DIR`
      set in base-service.sh/base-library.sh) in `python-quality-gates-v2.yml` — currently `.venv` is rebuilt from
      scratch on every single run fleet-wide (confirmed: `actions/checkout@v4`'s default `clean: true` wipes any
      leftover `.venv` before `uv sync` runs, even on persistent self-hosted runners). Biggest payoff on any repo NOT
      yet on `self-hosted-qg-repos.txt` (still GitHub-hosted, no incidental host-persistence benefit). Size the actual
      savings first (compare a cold vs warm `uv sync` timing) before committing to the cache-key design — self-hosted
      host persistence may already be absorbing some of this for free.

  ✅ **DONE (2026-07-29)** — `unified-trading-pm@3ed0fc99d1e2d8e16831f17b631b3cc0abfbe759`. Sized first: cold (~2m07s
  for ~393 packages) vs warm (9.4s) `uv sync --frozen`, a real ~118s/run win. Checked the self-hosted-persistence
  hypothesis: 22/24 Python repos are already self-hosted (persistence already absorbs this incidentally); only
  `unified-trading-library` is currently GitHub-hosted (a temporary revert-off-self-hosted). Added `actions/cache@v4`
  (path `~/.cache/uv`, key on `uv.lock`+python-version+`runner.os`, restore-keys fallback) to the real reusable-workflow
  SSOT `.github/workflows/python-quality-gates-v2.yml`. Validated via `yaml.safe_load` + a clean local `actionlint` run.
  Watch the next `unified-trading-library` CI run's cache hit/restore timing to confirm the measured local number holds
  in real GH Actions.

- [x] [SCRIPT] P3. `unified-trading-pm/scripts/quality_gates/check_ruff_rule_ratchet.py` (`run_ruff_count()`, lines
      ~208-227) runs a separate full-source-tree `ruff check --no-cache` invocation PER RULE GROUP (currently 2: dtz,
      tid251) in STEP 5.95, on top of the primary `[2/6] LINT` pass that already runs `ruff check` once with caching.
      Low absolute cost (ruff is fast) but a clean, mechanical fix: merge the rule groups into one `--select` invocation
      sharing one `--config`, and drop `--no-cache` unless there's a real correctness reason for it (check the script's
      own `--isolated` comment first — that flag is load-bearing, `--no-cache` may not be).

  ✅ **DONE (2026-07-29)** — `unified-trading-pm@3ed0fc99d1e2d8e16831f17b631b3cc0abfbe759`. Merged the dtz+tid251 groups
  into one `run_ruff_count_all()` sharing one `--config`; dropped `--no-cache` (confirmed pure waste, not correctness —
  `--isolated` is the load-bearing flag, `RUFF_CACHE_DIR` is already host-shared). Preserved the TID251-only
  cloud_interface exemption by re-expressing it as a `lint.per-file-ignores` entry (a naive merge via `--extend-exclude`
  would have silently dropped that path from DTZ scanning too). Empirically verified behavior-preservation: ran the
  merged function directly against `unified-trading-pm` (dtz=7, tid251=4) and `unified-trading-library` (dtz=10,
  tid251=3), confirmed both match the checked-in `ruff_rule_ratchet_baseline.yaml` exactly. Full
  `quality-gates.sh --no-fix` green before shipping.

## `unified-trading-system-ui` (public repo — no GH billing impact, but real wall-clock/orchestrator-VM-contention impact)

- [x] [UI] P2. **Highest-confidence finding in the whole audit.** Playwright E2E (`package.json:40` → `pnpm test:e2e` →
      `playwright test` with no `--project` filter) runs ALL THREE configured projects every CI run
      (`playwright.config.ts:42-84`) — including a `widgets` project and a THIRD project configured with
      `headless: false, slowMo: 700` (a human-debug project that should never run in CI). Scope the CI invocation to
      `--project=chromium` (the codex-sanctioned `pw:L2` command already does this) — roughly a 2-3x E2E-time cut.

  ✅ **DONE (2026-07-29)** — `unified-trading-system-ui@085f8464`. `ci.yml`'s E2E step changed to
  `pnpm exec playwright test --project=chromium`. This group's result was lost in the first fan-out pass (the agent did
  the real work but never returned before a session cap cut it off) — recovered directly from the intact working tree,
  independently reviewed, and shipped.

- [x] [UI] P3. No `actions/cache` for the Playwright browser-binary directory in the e2e job
      (`.github/workflows/ci.yml:66-67`, `pnpm exec playwright install --with-deps chromium` runs unconditionally).
      Currently low-impact since this repo's real CI is already self-hosted (persistent host likely caches browsers
      incidentally) — but add explicitly rather than relying on that, since it'd become a real multi-minute cost if ever
      moved to an ephemeral runner.

  ✅ **DONE (2026-07-29)** — `unified-trading-system-ui@085f8464`. Added an `actions/cache@v4` step keyed on the
  installed `@playwright/test` version for `~/.cache/ms-playwright`, with the install step conditioned on a cache miss
  (falls back to `playwright install-deps` on a hit, since OS deps still need installing even when the browser binary
  itself is cached).

- [x] [UI] P3. `eslint .` (`package.json:26`) scans ~2080 files vs. ~1587 in the actual `app+components+lib+hook` tree —
      `eslint.config.mjs`'s ignore list excludes `_reference/**` etc. but NOT `archive/**` (25 files, 652KB, name
      signals dead code) or `tooling-templates/**`. Add both to the ignore list; also add `--cache` to the lint script.

  ✅ **DONE (2026-07-29)** — `unified-trading-system-ui@085f8464`. Added `archive/**` + `tooling-templates/**` to
  `eslint.config.mjs`'s ignore list; `--cache` added to the `lint` script; `.eslintcache` added to `.gitignore`. Full
  `quality-gates.sh --no-fix` had one pre-existing, unrelated failure (UAC `capability-manifest.json` bundle-hash drift
  in `parity-gates.test.ts`) — confirmed via `git stash` to fail identically on unmodified HEAD, shipped via the
  dirty-deps direct-push carve-out.

## `deployment-ui`

- [x] [UI] P3. `vitest.config.ts:24` uses `environment: "jsdom"` instead of `happy-dom` — the repo's own comments
      (`scripts/quality-gates.sh:20-26`) already document raising `STEP_TIMEOUT_TEST` 120s→300s specifically citing "75+
      test files × jsdom env overhead," and `vitest.config.ts:51-60` separately raised test/hook timeouts citing CPU
      contention from jsdom + coverage + the `forks` pool. `happy-dom` is commonly 2-3x faster for DOM-heavy component
      tests. With 782 tests already near the 300s budget, this is a credible multi-minute win that would let the timeout
      budgets come back down instead of needing to ratchet up further.

  ✅ **DONE (2026-07-29)** — `deployment-ui@ee269ec999950315651ecc419b10ba43174c217d`. Switched vitest environment
  jsdom→happy-dom, installed `happy-dom` devDep; fixed 2 genuine env-gap test files (`DeployMissingButton.test.tsx` x2,
  `ArtifactPipeline.test.tsx` pinned back to jsdom via `// @vitest-environment jsdom`). Verified full suite green 3x
  (1101/1101 tests, same count as jsdom baseline) with a real ~30% wall-time win (24-25s vs 33-34s baseline). Full
  `quality-gates.sh --no-fix` green.

- [x] [UI] P3. Package manager is `npm` (`package-lock.json`) while the sibling UI repo already standardized on `pnpm`.
      Small absolute win (15 deps + 23 devDeps) but free consistency with the fleet pattern and a real per-run speedup
      on the one UI repo whose CI genuinely runs on ephemeral `ubuntu-latest`.

  ✅ **DONE (2026-07-29)** — `deployment-ui@de5b7af2bd3523e0a483f65badce7523976be8a1`. Migrated npm→pnpm (`pnpm import`,
  fresh install verified clean); updated `.github/workflows/ui-quality-gates-v2.yml` to `pnpm/action-setup` +
  `cache:pnpm`; also fixed 2 real production-infra npm dependents that would have broken the next Cloud Build image push
  (`Dockerfile`, `cloudbuild.yaml`'s quality-gates step). typecheck/lint/test/ build all pass under pnpm; full
  `quality-gates.sh --no-fix` green.

## Real `sleep()`-based test waste (all trivially fixable by mocking the clock instead — zero behavior risk)

- [x] [SCRIPT] P2. `market-tick-data-service/tests/unit/engine/test_sports_catalog_reader_timeout.py:88` — imports the
      REAL production constant `_BLOB_TIMEOUT_SECS` (=30) and does a real `time.sleep(35)` inside a background thread.
      **The single largest item found: ~30s of unnecessary real wall time on every run of this one test.** Fix:
      monkeypatch `_BLOB_TIMEOUT_SECS` down to e.g. 0.05s for the test.

  ✅ **DONE (2026-07-29)** — `market-tick-data-service@4aaeab6981093a310c5d6bdba3ec37272c6d6285`. Monkeypatched the
  module-level `_BLOB_TIMEOUT_SECS` down to 0.1s (read fresh per-call inside `_download_blob_timed`, so it genuinely
  changes the `Future.result(timeout=...)` wait, not just a label); added a caplog-based genuineness assertion (the
  module's own "stalled >Xs — skipping shard" warning must appear) so the test provably exercises the real
  timeout-firing path, not a vacuous pass. Direct `pytest` run: both tests pass in 5.57s (down from ~30s dominated by
  the real `sleep(35)`). The last of the 16 todos to land — queued ~37 minutes on the shared-host qg-governor (25
  concurrent `quality-gates.sh` processes fleet-wide observed at peak) before its full-suite run finally got a token and
  passed clean.

- [x] [SCRIPT] P3. `unified-trading-library`: 4 tests in `tests/unit/test_manifest_freshness.py` each `sleep(1.1)`
      (~4.4s total, lines 324/468/515/570); `tests/unit/recovery/test_agent_action.py` sleeps 1.5s
      (`test_loop_detector_window_expires`); `tests/events/test_pipeline_heartbeat_timer.py` sums to ~5.75s across 7
      tests (one single test alone is 3.5s, line 180). All read the clock via a directly-patchable
      `time.monotonic()`/`import time` call — no production refactor needed, just `patch(...time.monotonic)` in each
      test. Combined ~11.65s/run in this one repo.

  ✅ **DONE (2026-07-29)** — `unified-trading-library@2e39d98b0f73eab56eccecdfa85daded3baa2600`. Code complete across
  all 3 files as described. `test_manifest_freshness.py`: patched `manifest_freshness._time.monotonic` via a
  `_FakeMonotonic` helper in 3 of the 4 tests (the 4th sleep removed outright — it precedes an explicit
  `cache.refresh()` that bypasses TTL entirely, so it was already a no-op). `test_agent_action.py`: patched
  `recovery.agent_action.time.monotonic`. `test_pipeline_heartbeat_timer.py`: confirmed `threading.Event.wait()`'s
  timeout is a C-level lock primitive, not patchable, so instead trimmed the two dominant real sleeps (3.5s→1.0s,
  1.0s→0.4s). Full `quality-gates.sh --no-fix` green before shipping (also batched
  `tests/config_interface/unit/test_persistence.py`, the dead-test deletion below).

- [x] [SCRIPT] P3. `features-service/tests/sports/unit/test_feature_cache.py` — 2 tests `sleep(1.1)` each (~2.2s total)
      waiting out a 1s TTL on `LiveFeatureCache`; this directory IS part of the QG-gated pytest run (dynamic glob picks
      up every `tests/*/unit/` dir), so this runs on every CI invocation.

  ✅ **DONE (2026-07-29)** — `features-service@9506b5e2c2395aa34b716759afc139c79e1fc223`. Replaced both real
  `sleep(1.1)` calls with a monkeypatched, advanceable `_MockClock` (`LiveFeatureCache` only ever calls
  `datetime.now(tz)`, so patching the module's `datetime` symbol suffices) — TTL expiry is still genuinely exercised via
  the fake clock's elapsed-time delta, zero wall-clock cost. Isolated diagnostic run confirmed 13/13 tests pass, twice,
  before shipping. Two consecutive full-suite `quality-gates.sh --no-fix` runs on this repo failed on two different,
  unrelated pre-existing tests (a `calendar`/`volatility` module batch, then a timeout in `test_no_lookahead_pit.py`) —
  the qg-governor confirmed genuine severe shared-host contention (210s+ queue depth on other repos concurrently); this
  specific file independently verified clean both times, shipped via the direct-push carve-out.

- [x] [SCRIPT] P3 (batch, low individual value — do together or skip). `deployment-api` (~0.5s across 2 files,
      `test_data_status_cache.py:89,276` and `test_route_deployments_inventory.py:2069` — the latter is a legitimate
      concurrency-proof pattern, probably not worth changing), `instruments-service`
      (`tests/unit/test_base_adapter_cache.py:83`, ~20ms), `greeks-service`
      (`tests/unit/inputs/test_instrument_reader.py:100`, ~10ms). Negligible individually; noted for completeness since
      they're the literal anti-pattern this todo group targets.

  ✅ **DONE (2026-07-29)** — all 3 actionable repos shipped: `deployment-api@23516a78c8ead8b523c094342a6c69a7c39722db`
  (mocked `time.monotonic` in
  `test_data_status_cache.py::test_expired_entry_returns_none`/`test_exec_expired_returns_none`; full QG run hit 1
  unrelated pre-existing flake in `test_artifact_pipeline.py`, confirmed via `git stash` against clean HEAD, an issue
  doc was filed for it, shipped via the dirty-deps/pre-existing-corpus-violation direct-push carve-out);
  `instruments-service@91991d399bdc0b9b38a0603896d1adf9d1fc756e` (mocked `time.monotonic` in
  `test_base_adapter_cache.py::test_cache_expired_refetches`, full QG clean, dirty-deps carve-out used for an unrelated
  `unified-trading-library` uncommitted-changes block on quickmerge's pre-flight);
  `greeks-service@758cccdc122aa4b972a4ee4dd789fa2a3e8dbb8d` (mocked `time.monotonic` in
  `test_instrument_reader.py::test_expired_entry_re_fetches`, same dirty-deps carve-out). **Confirmed-intentional
  no-op**: `test_route_deployments_inventory.py:2069`'s `sleep(0.2)` was re-read and re-confirmed as the todo's own
  guess — a genuine concurrency-proof for a bounded worker pool, not a lazy anti-pattern — and left unchanged, matching
  this todo's own parenthetical.

## Orphaned/dead test code (not a current CI-speed cost — these aren't gated — but real maintenance debt)

- [x] [SCRIPT] P3. `execution-service`: ~40 files / ~10,082 lines across `tests/live/`, `tests/context7/`,
      `tests/validation/`, `tests/scripts/` import a pre-refactor module path (`execution_service.live.*` —
      oms/orchestrator/positions/risk/router/trading_node/factory/order_converter/config/persistence.*,
      `execution_service.venues.cefi`, `execution_service.catalog_manager`) that no longer exists. Confirmed not
      currently collected/gated (0 CI-minutes cost today) — but 10k+ lines of confirmed-dead code is real debt and a
      landmine for any future attempt to broaden test collection scope. Verify still-dead (grep for the import paths
      resolving to nothing) before deleting, since this audit is now hours old.

  ✅ **DONE (2026-07-29)** — `execution-service@21486f89026c79b509fec6906ee5146028f1b716`. Re-verified fresh (grep +
  `pytest --collect-only`) — the original audit was substantially correct, with one refinement: `tests/validation/` is
  NOT wholly dead, it contains `test_freshness_gate.py` which imports a real, existing module and collects 8 real
  passing tests. Only `tests/validation/verify_live_infrastructure.py` (non-`test_`-prefixed, never pytest-collected
  anyway) actually imports the dead `execution_service.live.*` paths. Independently re-confirmed the whole set myself
  before shipping (fresh grep for the 3 dead module paths — zero hits anywhere in the source tree;
  `pytest --collect-only` on a clean stashed HEAD showed "no tests collected" for `tests/live/`, `tests/context7/`,
  `tests/scripts/`, and confirmed `tests/validation/` still collects its 8 real tests post-deletion). Final set: 51
  confirmed-dead files / 13,955 lines deleted (all of `tests/live/`, `tests/context7/`, `tests/scripts/`, plus only
  `verify_live_infrastructure.py` from `tests/validation/`) — `tests/validation/test_freshness_gate.py` and
  `tests/validation/__init__.py` untouched. Full `quality-gates.sh --no-fix` hit one unrelated pre-existing flaky test
  on the first attempt (`test_rate_limit_bucket.py`, a timing-sensitive rate-limiter test under host-load/xdist-parallel
  contention — confirmed passing in isolation, and the same run's own log independently flagged an unrelated test as an
  existing XFAIL for the identical "flaky under parallel execution" reason); a second full re-run came back fully green
  (1573s, sentinel matched HEAD) before shipping.

- [x] [SCRIPT] P3. `unified-trading-library/tests/config_interface/unit/test_persistence.py:284` —
      `TestConfigReloaderReplayAt` imports `ConfigReloader` from `unified_trading_library.config_interface`, a path that
      no longer exports it (moved to top-level `unified_trading_library.ConfigReloader`, already correctly used
      elsewhere). Already `@pytest.mark.skip`-marked so zero current cost — trivial dead-code cleanup only.

  ✅ **DONE (2026-07-29)** — `unified-trading-library@2e39d98b0f73eab56eccecdfa85daded3baa2600`. Confirmed genuinely
  dead — `unified_trading_library.config_interface.reloader` no longer exists on disk, `ConfigReloader` import from that
  path fails live, the working replacement (`unified_trading_library.ConfigReloader`) is already used elsewhere; grepped
  the whole repo for any other reference — none. Deleted the 34-line skip-marked class; confirmed no unused-import
  fallout. Shipped in the same commit as the sleep-mocking todo above.

- [x] [SCRIPT] P3. `e2e-testing/scripts/{tradfi,cefi,sports,prediction}/run-full-pipeline.sh` — `SERVICES` arrays still
      list pre-merge repo/module name pairs for the archived `features-*-service` split repos (e.g.
      `"features-sports-service:features_sports_service:..."`). Not wired into CI (zero test-time cost) — a
      correctness/dead-reference cleanup in operator-run pipeline scripts, not a speed item.

  ✅ **DONE (2026-07-29)** — `e2e-testing@2d2f3ac3c3c671ba4202f017ccd9e85ca53cbdd1`. Repointed every stale `repo:module`
  pair in all 4 pipeline scripts to `features-service:features_service.<family>` (the consolidated repo, one sub-package
  per family), matching the existing `python -m ${module}` convention. Also fixed calendar's extra-args field
  (features_service.calendar's CLI accepts neither `--feature-group` nor `--asset-group` — discovered during the
  mandated read-and-verify pass). Verified via `--dry-run` against all 4 scripts plus real
  `python -m features_service.<family>` invocations from features-service's own `.venv` confirming zero "unrecognized
  arguments" errors. `shellcheck` clean, `quality-gates.sh --no-fix` green. Landed via the dirty-deps direct-push
  carve-out (execution-service, a path dependency, carried unrelated uncommitted test-file deletions).

## What did NOT surface a finding (say so explicitly — audited ~22 repos total for orphaned tests, only 2 hit)

Clean, per the audit's cluster reports: `agent-orchestrator`, `alerting-service`, `batch-live-reconciliation-service`,
`client-reporting-api`, `deployment-api` (orphaned-test angle only — see sleep() finding above), `deployment-service`,
`e2e-testing` (orphaned-test angle only — see dead-reference finding above), `ml-service`, `strategy-service`,
`system-integration-tests`, `trading-agent-service`, `unified-api-contracts`, `unified-trading-api`,
`fund-administration-service`, `ibkr-gateway-infra`, `market-data-processing-service`. The fleet's test suites are
meaningfully cleaner than the audit's working hypothesis assumed going in.

## Not covered by this pass (tracked so it isn't silently dropped)

- [x] [REVIEW] P3. **DONE-AS-NO-ACTION 2026-07-30 (re-confirmed a 3rd time).** The PM cost-breakdown angle of the
      original audit (why `unified-trading-pm` specifically is 41% of measured fleet spend) hit a session usage cap
      mid-workflow. **Superseded**: the interactive session that followed did this manually via direct `gh api` calls
      (not the stalled workflow) and found the real answer — see
      `github_actions_operator_gated_followups_2026_07_17.md`'s 2026-07-28 evening Progress Log entry
      (`ci-health`/`branch-health` job-body slowness, not cron frequency). The practical question is already answered;
      only "resume the stalled 3-agent workflow" remains as a low-priority, not-currently-wanted option — closing rather
      than leaving an actionless checkbox open indefinitely.

  **Confirmed (2026-07-29 pass)**: still accurate, no code work needed this pass. Remains exactly what it says —
  superseded/answered elsewhere, low priority, only "resume the stalled workflow" left if a fuller breakdown is ever
  wanted. Left as-is.
