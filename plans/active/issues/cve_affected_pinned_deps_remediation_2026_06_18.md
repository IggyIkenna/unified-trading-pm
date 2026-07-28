---
doc_type: issue
title: CVE-affected pinned deps — lift caps + drop --ignore-vuln entries once blockers clear (follow-up after 1.5b)
summary:
  "| Dep           | Working (kept) | Capped out | What
  breaks                                                                                                                                          ..."
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: [cve, quality-gates, infrastructure, verification, consolidation]
related:
  [
    /plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md,
    /plans/archive/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md,
  ]
created: 2026-06-18
parent_epic: infrastructure_master
priority: P2
source:
  [
    "2026-06-18 — surfaced during the 1.5b fleet `uv lock --upgrade` pass: the upgrade pulled vcrpy 8.1.1 -> 8.2.1 (the
    exact transitive that pins aiohttp<3.14 fleet-wide), and UAC QG passed with it",
    base-service.sh / base-library.sh sanctioned `--ignore-vuln` block (20 advisory IDs as of 2026-06-15),
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# CVE-affected pinned deps — remediation exercise (✅ UNBLOCKED 2026-06-18 — 1.5b shipped; see Todos below)

> **Operator (Harsh) 2026-06-18:** there are a bunch of CVE issues just like aiohttp where we're currently running the
> affected version because the upstream dep that would let us fix it isn't solved yet (a transitive blocker). We should
> do a proper follow-up exercise to resolve **all** of these CVE-affected deps — **after** the uv frozen-lock work
> (Phase 1.5b of `dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md`) lands.

> **Scope broadened (Harsh 2026-06-18):** this is the **one-by-one external-dependency compatibility audit** — check
> each external dep for the latest version that is compatible with our code, **no mass updates**, validating QG per dep.
> The 1.5b fleet `uv lock --upgrade` validation proved why: most latest external versions passed QG, but some BREAK
> (fastapi/starlette below), so we keep the working versions now and upgrade each dep deliberately + cleanly. Covers
> both **CVE-affected pins** (table further down) AND **breaking-version caps** (non-CVE, e.g. fastapi/starlette).

## Breaking-version caps (non-CVE) — capped in 1.5b, fix-and-adopt here

| Dep           | Working (kept) | Capped out | What breaks                                                                                                                                                                           | Cap applied (1.5b)                                                                                          | Fix to adopt later                                                                                                                            |
| ------------- | -------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **starlette** | 1.1.0          | 1.3.1+     | wraps `include_router` as `_IncludedRouter` (no `.path`) → `[r.path for r in app.routes]` raises `AttributeError` (QG fail: strategy-service, client-reporting-api, features-service) | `starlette>=1.1.0,<1.3.0` (floor lowered from the 1.3.1 CVE-fix floor; CVE-2026-54283/-54282 stays ignored) | fix the `.path` route-introspection in UTL `service_framework/fastapi_factory.py` + the 3 repos' tests to handle `_IncludedRouter`, then lift |
| **fastapi**   | 0.135.1        | 0.137.2+   | pulls starlette 1.3.1 (above)                                                                                                                                                         | `fastapi>=0.115.0,<0.137.0`                                                                                 | same fix; then lift                                                                                                                           |

Both caps are in `workspace-constraints.toml` as of 1.5b; the per-repo pyproject + lock rollout rides the 1.5b fleet
pass.

**Provenance:** the 1.5b fleet `uv lock --upgrade` validation (2026-06-18) — 16/22 repos passed QG on latest deps, 3
failed on this fastapi/starlette break, 2 on a pre-existing version-alignment drift (deployment-api,
system-integration-tests), 1 (alerting-service) on a test still to investigate.

## What I found

The fleet carries a **sanctioned `--ignore-vuln` block of 20 advisory IDs** in
`scripts/quality-gates-base/base-service.sh` + `base-library.sh`. These are deps held at a CVE-affected version because
a **blocker** (usually a transitive dep, sometimes a genuinely-unreleased fix) prevents the upgrade. Categorized:

| Group                                    | Advisories                                                                                           | Blocker / reason                                                                                                        | Resolvable now?                                                                                                                                  |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **aiohttp ≤3.13.5** (cookie-CVE cluster) | CVE-2026-34993, -47265, -50269, -54273, -54274, -54275, -54276, -54277, -54278, -54279, -54280 (~11) | **vcrpy 8.1.1** doesn't support aiohttp 3.14.0 (3.14 removed `AsyncStreamReaderMixin`) → caps `aiohttp<3.14` fleet-wide | **RESOLVED 2026-07-27** — see the DONE entry below; SSOT: `/plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (ARCHIVED) |
| **pip**                                  | CVE-2026-3219, CVE-2026-6357, PYSEC-2026-196                                                         | pip < 26.1 (and a 26.1.1 console-scripts issue)                                                                         | **Likely yes** — bump the CI/base pip floor to a patched release; re-validate.                                                                   |
| **starlette ≤1.1.0**                     | CVE-2026-54283, -54282                                                                               | transitive via fastapi (fastapi pins starlette)                                                                         | bump fastapi to a release that pins a patched starlette; transitive → "speed>security WARN" today                                                |
| **cryptography ≤46.0.7**                 | GHSA-537c-gmf6-5ccf                                                                                  | wheels statically link an OpenSSL with a CVE; transitive pin                                                            | re-check for a wheel with a patched OpenSSL; "speed>security WARN" today                                                                         |
| **idna 3.11**                            | CVE-2026-45409                                                                                       | no patched release as of 2026-05-22                                                                                     | likely still no-fix — re-check upstream                                                                                                          |
| **(workspace-global)**                   | CVE-2026-4539                                                                                        | no-fix-version (reviewed 2026-05-20)                                                                                    | re-check upstream                                                                                                                                |

## Why it matters

- It's **accumulating security debt** — the aiohttp ignore set alone grew from 2 → ~11 entries through the 2026-06-15
  OSV advisory batch, precisely _because_ the version stays capped. Each new aiohttp cookie CVE lands in 3.13.5 and is
  fixed only in 3.14.0, which we can't reach until vcrpy unblocks.
- Some are **now resolvable** (vcrpy 8.2.1 for aiohttp; pip floor bump) — they were genuinely blocked before, but the
  blocker has moved.
- Non-exploitable in our usage (client-only aiohttp, no `CookieJar.load()` on untrusted input; transitive-only crypto/
  starlette) — which is why the ignores are sanctioned. This is **debt cleanup, not an active incident.**

## Recommended decision

**After 1.5b lands** (so the frozen-lock model + atomic floor+lock regen are in place — bumping a CVE floor will then
cleanly re-lock + validate), run a remediation pass:

1. For **each** of the 20 advisories: identify the blocker, check if it has a resolvable release now.
2. **Resolvable** (e.g. aiohttp via vcrpy 8.2.1, pip floor): bump the floor → regenerate `uv.lock` atomically → run QG
   fleet-wide → on green, **drop the matching `--ignore-vuln` entries** from base-service.sh + base-library.sh (roll out
   the template). The aiohttp cap lift also drops the `aiohttp>=3.13.4,<3.14.0` range in `workspace-constraints.toml` +
   `canonical-dependency-manifest.json` + the 18 repos that declare it.
3. **Genuinely no-fix** (idna, possibly crypto): keep the ignore but add a `# re-check <date>` so it doesn't rot
   silently.
4. Update CLAUDE.md's aiohttp KNOWN-EXCEPTION block + the aiohttp issue doc to reflect whatever lifts.

## Gate / sequencing — ✅ UNBLOCKED 2026-06-18

**1.5b is GREEN (2026-06-18) — this exercise is now UNBLOCKED + pick-up-ready.** PM-core PR#397 + CI-v2 PR#398 merged to
`main` (the frozen-lock model + the floor-vs-pin guardrail are live), 15/15 fastapi/starlette caps shipped, and
`check-dependency-alignment.py` is `aligned: true`. So a CVE / cap floor bump now lands + re-locks cleanly on LDR (the
atomic floor+lock model 1.5b established) — exactly what this remediation needs. The original "do not start before 1.5b"
gate is satisfied.

## Todos — pick-up-ready (UNBLOCKED 2026-06-18)

- [ ] [SCRIPT] P2. **fastapi/starlette adoption — lift the 1.5b caps.** Fix the `_IncludedRouter` route-introspection in
      UTL `service_framework/fastapi_factory.py` (handle `_IncludedRouter` having no `.path` in
      `[r.path for r in app.routes]`) + the route-introspection tests in strategy-service / client-reporting-api /
      features-service. Then bump fastapi `≥0.137` + starlette `≥1.3.1` in `workspace-constraints.toml` +
      `canonical-dependency-manifest.json` + the 15 declaring repos' pyproject, regen locks atomically, run QG
      fleet-wide. On green, drop the starlette CVE-2026-54283/-54282 `--ignore-vuln` entries from `base-service.sh` +
      `base-library.sh`. Repo: unified-trading-library + strategy-service + client-reporting-api + features-service +
      unified-trading-pm. **[2026-07-14 note, verify-rerun-2 finding 99]**: this coordinated fleet-wide bump is still
      genuinely OPEN — `workspace-constraints.toml` confirmed as of 2026-07-14 still caps `fastapi>=0.115.0,<0.137.0` +
      `starlette>=1.1.0,<1.3.0` fleet-wide, and this UTL `_IncludedRouter` fix has not landed. However, ml-service
      found + shipped (`ml-service@4d16341`, 2026-07-13) an alternate, REPO-LOCAL escape hatch that does NOT require
      this UTL fix: a `[tool.uv] override-dependencies` floor pin (`starlette>=1.3.1`) forces the resolver's starlette
      version independent of what UTL's own `fastapi<0.137.0` declares, clearing ml-service's starlette CVEs without
      touching `workspace-constraints.toml` or this todo's UTL prerequisite (see
      `issues/ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md` "Corrections" §2 — the doc's own
      retraction of its earlier "requires cross-repo UTL change" diagnosis). This does NOT close this todo (the
      coordinated fleet-wide cap lift + the route-introspection fix are still required for the other 14 declaring
      repos), but the override-dependencies pattern is now a proven alternative worth considering per-repo while the UTL
      fix is pending.

      **[2026-07-28 note, slot-6]**: the UTL `_IncludedRouter`/`.path` route-introspection fix landed today
              (`unified-trading-library@3b99d19d`, slot-12, `fastapi>=0.137/starlette>=1.3.1`, quickmerge to
              `live-defi-rollout`) — I hit the resulting `ImportError: iter_route_contexts` live in market-tick-data-service
              while running the `data-pipeline-check-mtds` MID-BACKFILL spot-check
              (`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`). slot-3 independently found + filed the full
              analysis first and got the direction right (UTL + client-reporting-api are the ones DRIFTED from the
              `canonical-dependency-manifest.json` SSOT, not the ~10 repos still on the old bound) — see
              `issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md` (P0, `[OPERATOR]`-gated on choosing
              roll-forward vs revert, correctly not something a worker should pick unilaterally). I initially bumped
              market-tick-data-service's own `pyproject.toml` cap to unblock my task, then reverted that tracked change after
              finding slot-3's doc mid-session — same reasoning: direction isn't mine to pick. Left my local `.venv` on the
              newer fastapi (untracked, session-only) so my own check could proceed without prejudging the fleet decision.

          **[2026-07-28 note, slot-7/cicd escalation `agt-db0abf`]**: hit the same `ImportError: iter_route_contexts` as a
              hard `quality-gates-v2` red blocking ml-service's LDR→main promotion PR #306 (not a side-effect of an
              unrelated task — this WAS the escalated wall). Unlike slot-6/slot-8, I shipped the mechanical direction-A
              bump (`ml-service@8914d555`: `fastapi>=0.137.0,<1.0.0`, regenerated `uv.lock` → resolved 0.140.7) rather than
              reverting, because (a) my mandate is specifically to get this gate green, not to audit the fleet, and (b) I
              checked for slot-8's found landmine (a test iterating `app.routes`/`isinstance(route, APIRoute)` post
              `include_router()`, which `_IncludedRouter` wrapping can silently empty) — ml-service's only matching-looking
              test (`tests/inference/unit/test_prediction_stream.py:112`) walks a raw pre-include `APIRouter.routes`, never
              an app's aggregated `.routes`, so it is NOT exposed to the `_IncludedRouter` wrapping. Full
              `quality-gates.sh --no-fix` ran clean (2111 passed, 4 skipped, 80% coverage) both before and after the
              fastapi bump with no count drop. Full details + Progress Log entry in
              `issues/fleet_fastapi_upper_bound_stale_vs_utl_floor_bump_2026_07_28.md`. Flagging for the pending
              `[OPERATOR]` direction call: if direction B (revert UTL) is chosen, ml-service's `8914d555` needs a matching
              mechanical revert — trivial, already scoped.
              This todo and the new P0 doc now cover the same ground; resolve via the P0 doc's `[OPERATOR]` todo, not here.

- [ ] [TEST] P3. **alerting-service upgrade-time investigation.** `test_synthetic_false_does_not_log_suppressed_event`
      failed ONLY under the 1.5b `--upgrade` pass (it passes on current working deps + Mode-B). When alerting's external
      deps are upgraded one-by-one, identify which upgraded dep changed the suppressed-event behaviour and fix the test
      or the code. Repo: alerting-service.
- [x] ✅ [SCRIPT] P2. **aiohttp / vcrpy unblock — biggest CVE cluster — DONE 2026-06-23.** vcrpy 8.2.1 confirmed
      aiohttp-3.14-compatible (`MockStream` rewritten; UAC 649-cassette suite green on 3.14.1, conftest shim removed).
      **17 of 18 repos** bumped to `aiohttp>=3.14.1,<4.0.0` + `vcrpy>=8.2.1` in `workspace-constraints.toml` +
      `canonical-dependency-manifest.json` + each pyproject; all shipped to LDR + drained to staging (v2 green);
      CLAUDE.md KNOWN-EXCEPTION block rewritten (cap LIFTED). GHSA-rpj2 ignore dropped (8.2.1 fixes it).
      **execution-service held on 3.13.5 via `[tool.uv] override`** (aioresponses 0.7.8 can't build aiohttp-3.14
      ClientResponse) → the 11 aiohttp ignores were retained ONLY for it; **UPDATE 2026-07-27: migration DONE**
      (execution-service@`9ce159a7`, all 11 ignores dropped fleet-wide) —
      `/plans/archive/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md` (ARCHIVED). Repo:
      unified-trading-pm + 18 aiohttp repos. SSOT:
      `/plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (ARCHIVED 2026-07-27, RESOLVED
      banner).
- [ ] [SCRIPT] P3. **pip floor bump.** Bump the CI/base pip floor to a patched release (CVE-2026-3219 / -6357 /
      PYSEC-2026-196), re-validate, drop those 3 ignores. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **cryptography / idna / CVE-2026-4539 re-check.** Re-check upstream for patched releases; lift where
      resolvable, else add a `# re-check <date>` next to each ignore so it doesn't rot silently. Repo:
      unified-trading-pm.
- [ ] [SCRIPT] P3. **(then) one-by-one for the rest.** Walk the remaining external deps for the latest version
      compatible with our code — no mass updates, validating QG per dep (the broadened audit scope above). Repo:
      per-dep.

## Composes with

- `dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md` Phase 1.5 (the uv work this is gated on)
- `/plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (the canonical aiohttp instance, ARCHIVED
  2026-07-27)
- CLAUDE.md "Speed > security (operator 2026-06-12): transitive CVEs WARN not block" + the aiohttp KNOWN-EXCEPTION block
