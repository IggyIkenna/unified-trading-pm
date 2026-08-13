---
doc_type: issue
title:
  Slot service venvs installed below their own declared fastapi floor — blocks every PM commit via a swallowed
  ImportError
summary: >-
  20 of the 21 fastapi-carrying venvs in slot 5 (23 venvs across 31 repos) have fastapi 0.136.3 installed while both
  unified-trading-library and strategy-service declare `fastapi>=0.137.0,<1.0.0`. UTL's service_framework imports
  `fastapi.routing.iter_route_contexts`, which does not exist below 0.137 — so PM's capability-gap scanner fails to
  import, SWALLOWS the ImportError into an empty schema, and 6 PM unit tests fail on `assert 0 >= 29`. That hard-fails
  quickmerge Stage 3, blocking every PM commit from the slot. Referenced as background noise in 9 active docs; owned and
  tracked by none, with zero open todos in the corpus.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library, strategy-service]
scope: [engineer, admin]
tags: [dependency-management, quality-gates, quickmerge, venv, fastapi, silent-failure]
related:
  [
    /plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md,
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md,
    /plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md,
    /plans/active/quality_gates_quickmerge_timing_baseline_2026_07_31.md,
  ]
created: 2026-08-11
author: ikennaigboaka
parent_epic: infrastructure_master
priority: P1
source:
  [
    "2026-08-11 — surfaced while shipping an unrelated cursor-configs/settings.json cleanup: quickmerge Stage 3 re-gate
    hard-failed with `6 failed, 1961 passed in 33.21s`, none of the failures related to the staged file",
  ]
assigned_vm: planning
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-11
context_scope:
  [
    unified-trading-library/unified_trading_library/service_framework/fastapi_factory.py,
    unified-trading-pm/scripts/openapi/_capability_gaps.py,
    unified-trading-pm/tests/unit/test_capability_param_schema.py,
    workspace-constraints.toml,
    canonical-dependency-manifest.json,
    /codex/06-coding-standards/dependency-management.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
locked_by:
locked_since:
---

# Stale service venvs below their own declared fastapi floor

## What I measured

All figures from slot 5 (`.tabs/5`) on 2026-08-11. **Other slots and the AO VM were not checked** — see todo 3.

| Surface                                                           | Value                                                |
| ----------------------------------------------------------------- | ---------------------------------------------------- |
| `unified-trading-library/pyproject.toml:56` declared pin          | `fastapi>=0.137.0,<1.0.0`                            |
| `strategy-service/pyproject.toml:76` declared pin                 | `fastapi>=0.137.0,<1.0.0`                            |
| repos in slot 5 (dirs with `.git`)                                | 31                                                   |
| of those, carrying a `.venv`                                      | 23                                                   |
| venvs carrying fastapi at all                                     | 21 (`unified-api-contracts` + one archive have none) |
| fastapi **installed** in 20 of those 21 venvs                     | **0.136.3** — below both declared floors             |
| of the 20, `.stale-pre-history-rewrite-*` archive dirs            | 4 — dead weight, not live repos (todo 6)             |
| **live repos actually needing the re-sync**                       | **16** (strategy-service + 15)                       |
| fastapi installed in `unified-trading-pm/.venv`                   | 0.141.1 — the only conforming venv                   |
| `def iter_route_contexts` present in 0.141.1 `fastapi/routing.py` | yes                                                  |
| `def iter_route_contexts` present in 0.136.3 `fastapi/routing.py` | **no**                                               |

The pins are correct. **The installed environments are stale** — they were built before the `>=0.137.0` bump and never
re-synced. This is an environment-provisioning defect, not a dependency-resolution one, which is why `uv lock`-oriented
reads of the symptom (see the related docs) never landed on it.

## The failure chain

1. `unified-trading-library/unified_trading_library/service_framework/fastapi_factory.py:24` does
   `from fastapi.routing import APIRoute, iter_route_contexts`.
2. Any import of UTL's `service_framework` from a 0.136.3 venv raises
   `ImportError: cannot import name 'iter_route_contexts' from 'fastapi.routing'`.
3. PM's `scripts/openapi/_capability_gaps.py` reaches into **strategy-service's** venv to enumerate capability params.
   It catches that ImportError, logs `WARNING param schema GAP: …` at `_capability_gaps.py:864`, and returns an
   **empty** schema.
4. `tests/unit/test_capability_param_schema.py` then fails 5 tests on the empty dict
   (`assert 0 >= 29  where 0 = len({})`, plus `KeyError: 'CARRY_STAKED_BASIS'` / `'ARBITRAGE_PRICE_DISPERSION'` /
   `'VOL_CARRY'`), and `test_capability_verdict_matrix.py::test_fixture_matches_live_engine_registry` fails alongside
   them.
5. `quality-gates.sh` fails → `quickmerge.sh` Stage 3 re-gate hard-fails → **no PM commit can ship from this slot**,
   regardless of what is staged.

## Why it matters beyond the 6 tests

**The swallowed ImportError is the more serious defect.** Step 3 converts "your venv is stale" into "the schema is
empty", so the operator-facing symptom is `assert 0 >= 29` — a number that looks like a content regression in the
strategy registry. Diagnosing it costs a full quickmerge cycle (~2 min of gates) plus a manual read of the captured log
to find the buried WARNING. A loud fail at the import site would have named the cause immediately. This matches the
workspace's standing rule against silent placeholders in `/codex/02-data/data-pipeline-correctness-hard-rule.md` — the
same anti-pattern, applied to a gate scanner.

Second-order: because the gate fails for _everyone_ committing PM from this slot, it converts a local environment
problem into a shared shipping outage, and the failure text gives no hint that re-syncing a venv fixes it.

## Prior art — referenced 9 times, owned by nobody

`iter_route_contexts` appears in 9 active docs, every one of them treating it as pre-existing background noise en route
to a different objective:

- `/plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md` (3 mentions — closest to an owner; scoped to
  lifting CVE `--ignore-vuln` entries, not to venv staleness)
- `/plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` — correctly identifies
  `fastapi_factory.py` as the importer
- `/plans/active/issues/docs_reconcile_autonomous_sweep_2026_07_30.md` — records the exact `param schema GAP` warning
- `/plans/active/issues/sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` — reports a stale **0.135.1** (a
  third version, so the staleness is not uniform across slots/time)
- `/plans/active/issues/uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md`,
  `/plans/active/issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`,
  `/plans/active/issues/orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md` — each calls it "pre-existing"
  and moves on
- `/plans/active/quality_gates_quickmerge_timing_baseline_2026_07_31.md` — notes quickmerge "correctly hard-failed
  rather than ship on" these failures

**Zero open `- [ ]` todos anywhere in `plans/active/` mention fastapi.** Per the CLAUDE.md hard rule that every
follow-up is a tracked todo and never prose, that is the gap this doc closes. This doc is the SSOT for the staleness
itself; the CVE doc keeps ownership of the `--ignore-vuln` allowlist.

## Todos

- [x] [SCRIPT] P0. Re-sync every stale repo venv in slot 5 to its declared floor (`uv sync` per repo), then prove the
      fix: `iter_route_contexts` imports from a service venv, and PM `quality-gates.sh` goes green with
      `test_capability_param_schema.py` reporting a non-empty schema (≥29 rows). Evidence = the passing gate output, not
      the sync command's exit code. ✅ 2026-08-11 — `uv sync --frozen` across all 16 live stale repos: strategy-service
      first (0.136.3 → 0.140.7, `from fastapi.routing import iter_route_contexts` OK), then 15 more (synced=15 failed=0
      repos_left_dirty=0). `--frozen` was deliberate: every lockfile already resolved fastapi to 0.140.7, so no
      `uv.lock` was rewritten and no tracked file was dirtied — confirming the diagnosis that the venvs were stale
      against their OWN locks, not that the pins were wrong. **Evidence**: unified-trading-pm@9307f909af + PM
      `bash scripts/quality-gates.sh --no-fix` exit code **0** (was `6 failed, 1961 passed` before the sync). Final
      spread: 15 venvs @ 0.140.7, 2 @ 0.141.1, and 0.136.3 remaining ONLY in the 4 `.stale-pre-history-rewrite-*`
      archive dirs (todo 6).
- [x] [SCRIPT] P0. Make the swallowed ImportError loud in `unified-trading-pm/scripts/openapi/_capability_gaps.py`
      (~line 864): an ImportError while probing a sibling venv must fail the gate with the underlying message and the
      offending venv path, never degrade to an empty schema that surfaces as `assert 0 >= 29`. ✅ 2026-08-13 —
      unified-trading-pm@c7c237d804 + a5182bdbfc. `_SERVICE_PROBE` now catches ImportError separately and tags it
      `import_error`; `extract_param_schema` raises a RuntimeError naming the offending venv path + underlying message
      instead of degrading to `{}`. Unit test `test_import_error_fails_loud` added. Also rescued a pre-existing
      BATS_HARD_FAIL red (`test_prettier_autostage_advisory_mode.bats` test 2 asserted the npx-absent marker; npx now
      ships in /usr/bin) that blocked every PM commit. QG `--no-fix` exit 0.
- [x] ✅ [INVESTIGATE] P1. Measure whether the other slots and the AO VM carry the same staleness — this doc's numbers
      cover `.tabs/5` only, and a third version (0.135.1) is on record from 2026-08-01, so do not assume uniformity.
      Report the per-slot installed-vs-declared table. ✅ 2026-08-13 — swept ALL 33 slots (239 fastapi-carrying venvs) +
      the AO VM's own runtime venv: **ZERO below the `>=0.137.0` floor**. Every fastapi venv is 0.140.7
      (`unified-trading-pm` 0.141.1 in 25 slots); `iter_route_contexts` present in the installed 0.140.7. The 0.136.3
      staleness was slot-5-only and is gone fleet-wide. Full per-slot table in Progress Log.
- [x] ✅ [SCRIPT] P1. Add a preflight/QG check that fails when an installed distribution is below the floor its own
      `pyproject.toml` declares. The 20-venv drift persisted for weeks precisely because nothing compares installed
      versions against declared pins. ✅ 2026-08-13 — unified-trading-pm@45d9248d68. Added
      `scripts/quality_gates/check_installed_satisfies_pyproject.py` (runs with the target venv's own python so
      `importlib.metadata` reads that venv's actual installed set) and wired it into `base-service.sh` +
      `base-library.sh` right after the existing frozen-lock floor gate; blocks by default,
      `INSTALLED_FLOOR_GATE_WARN=1` to downgrade. **Bonus finding**: the pre-existing frozen-lock floor gate
      (`check_lock_satisfies_pyproject.py`'s wiring) had a latent bug — it checked `$REPO_ROOT/uv.lock` /
      `$REPO_ROOT/.venv`, but in this codebase's `qg-common.sh` convention `REPO_ROOT` is the WORKSPACE/slot dir, not
      the repo root (that's `PROJECT_ROOT`) — so it had been silently no-op'ing for every repo, fleet-wide, since it was
      added, never actually firing. Fixed both gates to use `PROJECT_ROOT`. Verified green end-to-end on
      unified-trading-pm (base-service.sh path, `✅ Frozen-lock floor gate` + `✅ Installed-distribution floor     gate`
      both now print) and unified-trading-library (base-library.sh path), plus a synthetic negative-case smoke test
      (`.venv/bin/python check_installed_satisfies_pyproject.py --repo <fake-repo-with-impossible-floor>` → exit 1,
      correctly names the violating package).
- [x] ✅ [DOCS] P2. Once todo 1 lands, add a one-line pointer to this doc from the 9 referencing docs listed above so
      the next agent who hits the ImportError finds the owner instead of re-diagnosing it. ✅ 2026-08-13 — slot-6. Added
      the pointer to **9 of the 10** active referencing docs (8 listed in the Prior-art section +
      `data_pipeline_reconciliation_skill_2026_07_20.md` + `fleet_venv_drift_after_pull_no_resync_2026_08_11.md`, both
      found via a fresh corpus grep for `iter_route_contexts`): `cve_affected_pinned_deps_remediation_2026_06_18.md`,
      `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`, `docs_reconcile_autonomous_sweep_2026_07_30.md`,
      `uac_venue_to_asset_group_defi_registry_gap_2026_08_09.md`,
      `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`,
      `orchestrator_vm_disk_io_contention_runner_burst_2026_07_28.md`,
      `quality_gates_quickmerge_timing_baseline_2026_07_31.md` (7 shipped in `unified-trading-pm@d351f3ceb7`) +
      `data_pipeline_reconciliation_skill_2026_07_20.md` + `fleet_venv_drift_after_pull_no_resync_2026_08_11.md` (2
      shipped in the same commit; the SSOT flip itself also landed there). Each got
      `> **Owner for the stale-venv / \`iter_route_contexts\` ImportError**:
      /plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md` at its mention site.     **`sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md`is the ONE exception — pointer NOT added this     pass**: that doc's prettier-canonical form is 1008 lines > the 1000-line HARD plan cap (HEAD is 998L but     non-canonical), so staging ANY edit to it (even a pure pointer append) triggers a prettier reflow over the cap and     hard-fails plan-hygiene's`check_line_caps`.
      Its pointer is tracked as the P3 todo below (split/fold the doc under the cap, then add the pointer).
- [ ] [DOCS] P3. `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` is over the 1000-line plan hard cap in its
      prettier-canonical form (1008L; HEAD 998L non-canonical) — any staged edit hard-fails `check_line_caps`. Split or
      fold that doc below 1000L (e.g. fold the closed-out "Live-verification gotchas" and older Progress Log entries
      into an archive sibling), then add the `> **Owner for the stale-venv / \`iter_route_contexts\` ImportError**:
      /plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md` pointer at the Venv gotcha
      (~line 888) that todo 5 could not land. Repo: unified-trading-pm.
- [ ] [INVESTIGATE] P3. Three `*.stale-pre-history-rewrite-20260805T112453Z/` sibling directories (execution-service,
      instruments-service, market-data-processing-service, unified-trading-library) still carry their own 0.136.3 venvs
      in the slot. Confirm they are dead weight from the 2026-08-05 history rewrite and can be removed, or document why
      they are retained.

## Progress Log

**2026-08-13 (slot 18, todo 3)** — Fleet-wide staleness measurement: **the staleness is NOT present elsewhere.** Swept
all 33 slots on the planning VM (`.tabs/1`–`.tabs/33`) + the AO VM's own runtime venv. 239 fastapi-carrying venvs total,
**0 below** the `>=0.137.0` floor each repo's `pyproject.toml` declares.

| Surface                                                                                         | Result                                                                                              |
| ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Slots 1–33, fastapi-carrying venvs                                                              | 239                                                                                                 |
| Below declared `>=0.137.0` floor                                                                | **0**                                                                                               |
| Installed distribution spread                                                                   | 0.140.7 (all service / UTL / AO venvs) · 0.141.1 (`unified-trading-pm`, 25 slots)                   |
| AO VM runtime venv (`agent-orchestrator/.venv`, uvicorn :8765)                                  | 0.140.7 — conforms                                                                                  |
| Root-clone `agent-orchestrator/.venv`                                                           | 0.140.7 — conforms                                                                                  |
| `iter_route_contexts` in installed 0.140.7 `fastapi/routing.py`                                 | present (AO runtime, strategy-service, PM venvs)                                                    |
| `instruments-service` / `market-data-processing-service` / `e2e-testing` / `unified-trading-pm` | don't declare fastapi (transitive dep) — no floor to violate                                        |
| `.stale-pre-history-rewrite-*` archive dirs (slots 1–16)                                        | **no fastapi present** — supersedes todo 1's "0.136.3 remains in 4 archive dirs" note; feeds todo 6 |

Conclusion: the 2026-08-11 slot-5-only staleness is fully resolved fleet-wide (todo 1 re-synced slot 5's 16 live venvs
on 2026-08-11; every other slot's venvs were built after the `>=0.137.0` bump). No uniform 0.135.1 anywhere today — the
2026-08-01 third-version data point is historical, not a live fleet condition. Todo 4's preflight/QG check remains the
standing prevention.

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

**2026-08-11** — Filed. Surfaced while shipping an unrelated `cursor-configs/settings.json` cleanup: `quickmerge.sh`
Stage 3 re-gate returned `6 failed, 1961 passed, 11 skipped in 33.21s` with none of the failures touching the staged
file. PM HEAD unchanged at `7fc33cbff9`; the settings change remains uncommitted in the slot and cannot ship until todo
1 clears. Diagnosis measured the installed-vs-declared table above and confirmed `iter_route_contexts` exists in 0.141.1
and not in 0.136.3. Conflict check found 9 prior references and 0 tracked todos, so this doc was created rather than
folded into an existing one; the CVE-remediation doc retains ownership of the `--ignore-vuln` allowlist.
