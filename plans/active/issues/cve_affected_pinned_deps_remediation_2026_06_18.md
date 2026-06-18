---
title: "CVE-affected pinned deps — lift caps + drop --ignore-vuln entries once blockers clear (follow-up after 1.5b)"
created: 2026-06-18
status: active
priority: P2
locked_by: live-defi-rollout
parent_epic: infrastructure_master
source:
  - "2026-06-18 — surfaced during the 1.5b fleet `uv lock --upgrade` pass: the upgrade pulled vcrpy 8.1.1 -> 8.2.1 (the exact transitive that pins aiohttp<3.14 fleet-wide), and UAC QG passed with it"
  - "base-service.sh / base-library.sh sanctioned `--ignore-vuln` block (20 advisory IDs as of 2026-06-15)"
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

| Group                                    | Advisories                                                                                           | Blocker / reason                                                                                                        | Resolvable now?                                                                                                                                                                                                                                     |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **aiohttp ≤3.13.5** (cookie-CVE cluster) | CVE-2026-34993, -47265, -50269, -54273, -54274, -54275, -54276, -54277, -54278, -54279, -54280 (~11) | **vcrpy 8.1.1** doesn't support aiohttp 3.14.0 (3.14 removed `AsyncStreamReaderMixin`) → caps `aiohttp<3.14` fleet-wide | **MAYBE — vcrpy 8.2.1 now released** (pulled by the 1.5b --upgrade). CHECK if 8.2.1 supports aiohttp 3.14; if yes → lift the cap + bump aiohttp 3.14.0 + drop these ~11 ignores. SSOT: `issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` |
| **pip**                                  | CVE-2026-3219, CVE-2026-6357, PYSEC-2026-196                                                         | pip < 26.1 (and a 26.1.1 console-scripts issue)                                                                         | **Likely yes** — bump the CI/base pip floor to a patched release; re-validate.                                                                                                                                                                      |
| **starlette ≤1.1.0**                     | CVE-2026-54283, -54282                                                                               | transitive via fastapi (fastapi pins starlette)                                                                         | bump fastapi to a release that pins a patched starlette; transitive → "speed>security WARN" today                                                                                                                                                   |
| **cryptography ≤46.0.7**                 | GHSA-537c-gmf6-5ccf                                                                                  | wheels statically link an OpenSSL with a CVE; transitive pin                                                            | re-check for a wheel with a patched OpenSSL; "speed>security WARN" today                                                                                                                                                                            |
| **idna 3.11**                            | CVE-2026-45409                                                                                       | no patched release as of 2026-05-22                                                                                     | likely still no-fix — re-check upstream                                                                                                                                                                                                             |
| **(workspace-global)**                   | CVE-2026-4539                                                                                        | no-fix-version (reviewed 2026-05-20)                                                                                    | re-check upstream                                                                                                                                                                                                                                   |

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
      unified-trading-pm.
- [ ] [TEST] P3. **alerting-service upgrade-time investigation.** `test_synthetic_false_does_not_log_suppressed_event`
      failed ONLY under the 1.5b `--upgrade` pass (it passes on current working deps + Mode-B). When alerting's external
      deps are upgraded one-by-one, identify which upgraded dep changed the suppressed-event behaviour and fix the test
      or the code. Repo: alerting-service.
- [ ] [SCRIPT] P2. **aiohttp / vcrpy unblock — the biggest CVE cluster (~11 ignores).** vcrpy 8.2.1 is now released (the
      1.5b `--upgrade` pulled it). CHECK whether 8.2.1 supports aiohttp 3.14.0 (the removed `AsyncStreamReaderMixin`). If
      yes: bump aiohttp `≥3.14`, regen locks, run the VCR cassette suites (UAC / UTL / execution-service / MTDS); on
      green drop the ~11 aiohttp `--ignore-vuln` entries + the `aiohttp>=3.13.4,<3.14.0` range in
      `workspace-constraints.toml` + `canonical-dependency-manifest.json` + the 18 declaring repos + the CLAUDE.md
      KNOWN-EXCEPTION block. Repo: unified-trading-pm + the 18 aiohttp repos. SSOT:
      `issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md`.
- [ ] [SCRIPT] P3. **pip floor bump.** Bump the CI/base pip floor to a patched release (CVE-2026-3219 / -6357 /
      PYSEC-2026-196), re-validate, drop those 3 ignores. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **cryptography / idna / CVE-2026-4539 re-check.** Re-check upstream for patched releases; lift where
      resolvable, else add a `# re-check <date>` next to each ignore so it doesn't rot silently. Repo: unified-trading-pm.
- [ ] [SCRIPT] P3. **(then) one-by-one for the rest.** Walk the remaining external deps for the latest version
      compatible with our code — no mass updates, validating QG per dep (the broadened audit scope above). Repo: per-dep.

## Composes with

- `dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md` Phase 1.5 (the uv work this is gated on)
- `plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` (the canonical aiohttp instance)
- CLAUDE.md "Speed > security (operator 2026-06-12): transitive CVEs WARN not block" + the aiohttp KNOWN-EXCEPTION block
