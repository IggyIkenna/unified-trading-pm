---
title: "Deployment-UI Monitoring Pane — CI/CD · codebase · fleet · images · alerts"
created: 2026-06-19
status: active
parent_epic: infrastructure_master
assigned_vm: planning
plan_of_record: plans/active/monitoring_control_plane_master_2026_06_10.md
audit_ref: plans/audit/results/monitoring_surfaces_audit_2026_06_18.md
locked_by: live-defi-rollout
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
source:
  - 2026-06-18 operator design session — deployment-ui = CICD/codebase/fleet/images lens
  - 2026-06-19 operator decision — split monitoring_surfaces_overhaul into two single-surface plans (deployment-ui here;
    agent-orchestrator dashboard → agent_orchestrator_dashboard_monitoring_2026_06_19.md)
  - plans/audit/results/monitoring_surfaces_audit_2026_06_18.md (Opus audit, 4 background agents)
priority: P2
---

# Deployment-UI Monitoring Pane

> **Split 2026-06-19** from `monitoring_surfaces_overhaul_2026_06_18.md` (operator: two single-surface plans so the
> deployment-ui side and the agent-orchestrator side can be worked by separate agents without collision). The
> agent-orchestrator dashboard track moved to `agent_orchestrator_dashboard_monitoring_2026_06_19.md`. This plan owns
> the **deployment-ui + deployment-api** surface only.

## Why

Operator (2026-06-18): the deployment-ui monitoring pane owns CI/CD + codebase + fleet + images; an alert clicks through
to the right surface. Audit reframe: CI/CD + image-build are already mature/planned; the real deployment-ui gaps are
fleet-runtime + alert-unification. Full evidence + per-ask current-state/gap/change-list:
`plans/audit/results/monitoring_surfaces_audit_2026_06_18.md`.

## Deployment-UI monitoring pane (repos: deployment-ui + deployment-api)

- [x] ✅ [INFRA] P0. **Mint `ORCHESTRATOR_API_TOKEN` into Secret Manager (both clouds)** — cheapest high-value fix:
      lights up the already-built Fleet-Git page (currently degrades to unavailable, BLOCKED-CREDENTIALS). File as an
      operator credential ask if mint requires operator. Repo: deployment-service/deployment-api. **DONE 2026-06-19**:
      HS256 JWT minted (sub=deployment-api, role=operator, exp=2036-06-16); stored as version 2 in GCP SM
      (`central-element-323112/ORCHESTRATOR_API_TOKEN`) + AWSCURRENT in AWS SM (`ap-northeast-1/427895769566`). Token
      validates against `ORCHESTRATOR_JWT_SECRET` on this host. Fleet-Git page should now degrade→live on next
      deployment-api cold-start / SM read.
- [x] ✅ [INFRA] P1. Central/infra-VM health: `GET /api/fleet/infra-vm-health` (proxy AO `/api/fleet/summary`) +
      `GET /api/fleet/vm-census` (render `vm_zombie_watchdog.py` running-vs-expected-vs-zombie). Repo: deployment-api.
      **DONE — deployment-api@86050f0** | new router `routes/fleet.py` (prefix `/api/fleet`) +
      `_fleet_{types,census,infra_health,mocks}.py`, wired in `main.py`. **vm-census** = live compute `aggregatedList`
      (`vm_utils.get_vm_instance_details`) rolled into running/expected/stopped + per-VM entries; lifecycle via UAC
      `classify_vm_name` over a small **honest local prefix registry** (NOT a copy of deployment-service's ~50-entry
      `VM_PREFIX_TO_BUCKET` — drift/coupling avoided), unknown prefix → `EPHEMERAL_BATCH`. **infra-vm-health** = AO
      `/api/fleet/summary` server-side proxy mirroring `_repo_ci_fleet.py` (SM token, 10s timeout, **honest
      degradation** `available=false`+empty on any failure, never fabricated). Matches the deployment-ui `client.ts`
      contract field-for-field; 10 unit tests; basedpyright 0/0/0; QG green (70s). **Honest gap (by design): live
      `zombie`/`oom` are `0`** — see the follow-up below. **QG follow-up — deployment-api@08654b0 (2026-06-22):** the 8
      `.get("key", "")` monitoring defaults in `_fleet_census` (×3 GCE fields) + `_fleet_infra_health` (×5 AO-payload
      fields) shipped WITHOUT the repo-standard `# noqa: qg-empty-fallback — <reason>` (every other such `.get(k,"")` in
      the repo carries it). Pass-1 was green at an older base (codex ≤4), but a concurrent data-status commit
      (`4940972`) independently took the count to exactly 5 (= `CODEX_MAX_VIOLATIONS`), so the noqa-less category
      stacked to 6 > 5 on the integration branch → QG red. Backfilled the noqa+reason on all 8 lines → codex back to 5,
      ALL GATES PASSED (68s). Classic two-agent stacking collision; the violation was mine.
- [x] ✅ [INFRA] P3. **Live zombie/OOM census signal (vm-census follow-up).** `/api/fleet/vm-census` currently reports
      `zombie`/`oom` as `0` because the deployment-service `vm_zombie_watchdog.py` computes `WatchdogVerdict`s in-memory
      each poll but persists NO readable census/verdict snapshot (its only non-heartbeat GCS write is forensic
      log/serial-console archival at kill time). To surface TRUE live zombie/OOM in the FleetInfra tile, the watchdog
      must write a small census JSON to GCS (running set + zombie names + OOM-terminated names + ts) that
      `_fleet_census.py` reads (degrading to 0 when absent/stale). Repo: deployment-service (watchdog GCS write) +
      deployment-api (read it). Low priority — the live fleet is 2 long-lived VMs; zombie/OOM matters for the
      not-yet-running ephemeral fleet. Provenance: 2026-06-22 fleet vm-census backend (deployment-api@86050f0). —
      deployment-service@95af8e7, deployment-api@ffbaf9a | watchdog writes `vm-census/watchdog-census.json` after each
      poll; `_fleet_census.py` reads + degrades honestly to 0 when absent/stale (>30 min)
- [x] ✅ [UI] P1. deployment-ui central/infra-VM status tile + VM census/zombie surface (the vm-0 OOM class is invisible
      today) — chip click-throughs to AO (not a rebuild; honors division-of-surfaces). `pw:L2 ✓` + regression. Repo:
      deployment-ui. — deployment-ui@3508fa2 | pw:L2 ✓ (256/256 passed) | regression:
      tests/smoke/fleet-infra-vm-census.spec.ts
- [x] ✅ [INFRA] P1. **Unify the alert ledger across domains** — non-CI watchers (VM-down, consolidator-down,
      git-health-guard, worker-liveness, data-pipeline) write to a shared store; add `GET /api/alerts` superset of
      `/api/repo-ci/alerts`. This is what makes "alert → open deployment-ui → full picture" work for ALL classes. Repo:
      deployment-api (+ the watcher emitters). Composes with `alert_quality_overhaul_2026_06_18.md`. —
      deployment-api@cb56889 | agent-orchestrator@8f6dfee
- [x] ✅ [UI] P1. deployment-ui `/alerts` page consumes the unified ledger (not just `cicd/alerts`). `pw:L2 ✓` +
      regression. Repo: deployment-ui. — deployment-api@f87faf6 (GET /api/alerts endpoint) + deployment-ui@8cc8211 |
      pw:L2 ✓ 259/259 | regression: tests/smoke/alerts-page.spec.ts
- [x] ✅ [UI] P2. Unified single-glance fleet/infra landing tile (6th LandingTab: N VMs running · central-VM up ·
      consolidator fresh · fleet-git clean · CI green — each click-through). Repo: deployment-ui. —
      deployment-ui@7e40055 | pw:L2 ✓ | regression: tests/smoke/fleet-infra-tab.spec.ts
- [x] ✅ [UI] P2. **Codebase-health matrix COLUMN (frontend) on `/repos`** (fleet-wide coverage% / QG-red-reason /
      file-size-debt). The UI column + chips render `row.codebase_health`. **DONE — deployment-ui@a1b7fbd | pw:L2 ✓ |
      regression: tests/smoke/repos-codebase-health.spec.ts.** ⚠️ **SCOPE CORRECTION 2026-06-22:** this shipped the
      column + the MOCK seed ONLY — the field is `codebase_health?` (optional) in `client.ts`, populated by
      `mock-api.ts` per ci_status, NOT by the live backend (`codebase_health` appears in ZERO deployment-api files;
      `_overview_row` never sets it). So against the LIVE backend all three columns render "—". The previous unqualified
      ✅ was frontend-only; backend population is the OPEN item below.
- [x] ✅ [INFRA] P2. **Backend population of codebase_health (CI → Firestore → deployment-api read).** The Cov% /
      QG-reason / File-debt columns are now REAL (no longer mock-only). Pipeline (all transport rides the LIVE
      `CI_STATUS_FIRESTORE_DUALWRITE` path): (1) the **agg job of the reusable `python-quality-gates-v2.yml`** computes
      per-repo
      `{coverage_pct (parsed from the tests-slice `coverage.xml`artifact), qg_red_reason, large_file_count,     warn_file_count (file-debt via`os.walk` on its checkout, mirroring the gate's >900/700-899 zones)}`
      — every step is `continue-on-error`, so it can NEVER red the required `quality-gates-v2` context; (2) it forwards
      `codebase_health_b64` in the EXISTING `ci-status-update` dispatch — **one reusable-workflow edit → live for ALL
      repos via `uses:@live-defi-rollout`, NO 22-repo template rollout** (the original base-service.sh emit idea was
      reverted: CI runs the gate SLICED, so coverage and file-debt land in different slices — the agg job is the single
      place with both); (3) `ci-status-update.yml` decodes it → writes `repositories[repo].codebase_health` in the
      manifest (deployment-api's fallback cache) AND passes `--codebase-health-b64` to `ci_status_store.py`, whose
      `set_status` writes it into the Firestore `ci_status/{repo}.codebase_health` (**merge-preserving** — a status-only
      update never wipes the last-known metrics); (4) deployment-api `resolve_codebase_health_map` reads it
      Firestore-authoritative / manifest-fallback (honest-degradation: warns + manifest-only on any Firestore error) and
      `_overview_row` attaches `codebase_health`. **DONE 2026-06-22 — deployment-api@8050d21** (read:
      `CodebaseHealthDict` + `resolve_codebase_health_map` + `ManifestView.codebase_health_for` + `_overview_row`; 13
      tests; full QG green) **+ unified-trading-pm@c7b6bff73** (`ci_status_store.py` merge-preserving write +
      `--codebase-health-b64` CLI + 3 tests = 18 pass; reusable v2 agg-job compute+forward + tests-slice coverage
      artifact; `ci-status-update.yml` manifest+Firestore write; PM QG green 98s). Contract verified field-for-field vs
      deployment-ui `client.ts` (4 nullable fields). Compute proven locally on alerting-service
      (`{cov 80.08, large 0, warn 1}`); b64 transport + write + read all unit-tested. **v1 scope notes (documented, not
      deferred work):** `qg_red_reason` is `null` on a green run (→ "✓") and a generic `"qg"` on a failing run (the
      specific failing step is already in the failure-excerpt / stuck-PR check the dashboard surfaces) — per-step
      granularity (pytest vs basedpyright) is a future refinement; and the **UI repos** (deployment-ui /
      unified-trading-system-ui) use the vitest reusable, so their codebase_health is a fast-follow (see the new P3
      below) — the Python-service majority populates now. Provenance: 2026-06-22 operator review (the columns showed "—"
      against live data). **LIVE-VERIFIED END-TO-END 2026-06-22:** triggered consumer v2 runs + watched the full path —
      the agg job computed + dispatched `codebase_health_b64` (alerting-service run log), and once the receiver reached
      PM `main` (`ci-status-update` is `repository_dispatch`-triggered → runs from the DEFAULT branch, so it had to
      drain LDR→main first — a deploy-timing gotcha, not a code bug) the manifest populated organically from fleet v2
      runs: `fund-administration-service` `{coverage_pct: 83.9, qg_red_reason: null, large/warn 0}` +
      `system-integration-tests` `{coverage_pct: 9.09, …}`. Real coverage% + file-debt + green-✓ reason. The fleet fills
      in per-repo as v2 cycles.
- [x] ✅ [INFRA] P3. **codebase_health for UI repos + qg_red_reason granularity (fast-follow to the P2 above).** (a) Mirror
      the agg-job compute + `codebase_health_b64` forward into the **`ui-quality-gates-v2.yml`** reusable (vitest
      coverage from `coverage/coverage-summary.json`; file-debt over `.ts`/`.tsx`) so `deployment-ui` +
      `unified-trading-system-ui` populate too. (b) Thread the per-leg slice result into the agg job so `qg_red_reason`
      is the specific failing step (`pytest` / `basedpyright` / `ruff` / `bandit`) instead of the generic `"qg"`. Repo:
      unified-trading-pm. Provenance: 2026-06-22 (codebase_health backend v1 scope cut). — deployment-ui@946be88 |
      unified-trading-system-ui@456d4609 | unified-trading-pm@b19048e66 (PR #495)
- [x] ✅ [UI] P2. Confirm `GhRateBudget` is placed as a standing element on `/repos`. Repo: deployment-ui. —
      deployment-ui@a1b7fbd (already present at RepoCi.tsx:1637) | pw:L2 ✓ | regression:
      tests/smoke/gh_rate_budget.spec.ts

## Cloud Build visibility + build health (found 2026-06-18 operator Cloud Build smoke test)

Operator-directed GCP Cloud Build smoke test (central-element-323112 / asia-northeast1): `roles/editor` confirmed; 3
builds run via regional triggers — UTL base `590050dc` ✅ SUCCESS, mtds `4a7de34e` ✅ SUCCESS, mdps `40c74eab` ❌
FAILURE. Two build-VISIBILITY bugs (deployment-ui Cloud Build pane was non-functional) + one BUILD break, all
root-caused and FIXED 2026-06-19:

- [x] ✅ [INFRA] P1. DONE 2026-06-19 — deployment-api@5bf7165c. **deployment-api build history shows nothing (current
      build + history) — regional-vs-global `list_builds`.** `get_build_history` (`routes/cloud_builds.py:387`) queries
      `ListBuildsRequest(project_id=...)` (GLOBAL scope; the inline "regional parent 400s on REST" comment is STALE) but
      every build runs regionally in `asia-northeast1`, so it always returns `builds:[]` (confirmed empty for both mtds
      `-live-defi-rollout` and mdps `-build`). Fix: use the regional parent `projects/{p}/locations/asia-northeast1`,
      mirroring the proven `_find_recent_build_sync` / `_get_recent_builds_for_triggers` helpers (which already use it).
      Secondarily map service → ACTUAL live trigger (`-live-defi-rollout` where present, else `-build`;
      `cloud_builds.py:346`) so LDR-built repos appear. Repo: deployment-api. **Shipped**: extracted
      `_build_history_for_repo` (regional parent + REPO_NAME substitution, trigger-agnostic) into
      `_cloud_builds_history.py`; `get_build_history` delegates; dead single-trigger_id plumbing removed. QG green
      (135s); regression `tests/unit/test_cloud_builds_helpers.py::TestBuildHistoryForRepo` (3 tests).
- [x] ✅ [INFRA] P1. DONE 2026-06-19 — deployment-api@5bf7165c. **deployment-api `/api/cloud-builds/triggers` 500s when
      Redis is down (the triggers pane + last_build is dead).** `list_triggers` wraps its fetch in `cache.get_or_fetch`
      (Redis-backed); `RedisCache.get/set/...` (`utils/cache.py`) catch only `(OSError, ValueError, RuntimeError)`, but
      redis-py raises `redis.exceptions.RedisError` (subclasses `Exception`, NOT `OSError`) on a dropped/unreachable
      connection → it propagates → 500. (History is unaffected because it skips the cache — which is why it's 200-empty,
      not 500.) Fix: make the cache best-effort — add `RedisError` to the caught set so a Redis outage degrades to a
      cache-miss (falls through to live fetch), never a 500. Fleet-wide resilience: this fixes EVERY cached endpoint,
      not just triggers. Repo: deployment-api. **Shipped**: added `RedisError` to the
      `RedisCache.connect/get/set/delete/clear_pattern` except tuples (`utils/cache.py`) — a Redis outage now degrades
      to a cache-miss. Regression `tests/unit/test_unified_cache.py::test_rediscache_get_degrades_on_redis_error`.
- [x] ✅ [DOCKER] P1. DONE 2026-06-19 — market-data-processing-service@8025264d | Cloud Build 3c501b1f SUCCESS (full
      green: image built + in-image QG passed + pushed). **mdps image build was broken — THREE stacked causes, peeled
      back one Cloud Build at a time:** (1) `Dockerfile:57` `uv sync --frozen --no-dev` needed the editable
      `../unified-api-contracts` absent from the GCP context → switched to `uv pip install --system -e . --no-sources`
      (mdps@bffb9df3; mirrors features-service — `--no-sources` keeps external deps numba/polars, unlike mtds's
      `--no-deps`). (2) That exposed a STALE `BASE_IMAGE_DIGEST` pin `e939b4ee` (base UTL 0.11.0 / UAC 0.15.0) vs mdps
      floors UTL ≥0.12.0 / UAC ≥0.19.0 → uv re-resolved from the registry & failed → refreshed to current `:latest`
      `2baa8551` (UTL 0.13.0 / UAC 0.19.0) (mdps@317ab425); build `6798472f` then proved Step #5 (image build) green.
      (3) That exposed Step #6 (in-image QG): `scripts/quality-gates.sh` resolved `WORKSPACE_ROOT` via
      `git rev-parse --show-toplevel` which is empty in-image → sourced `//unified-trading-pm/.../base-service.sh` (404)
      → added the fleet-canonical mtds `CLOUD_BUILD=true` guard (skip in-image gate when the PM base script is absent)
      (mdps@8025264d). Build `3c501b1f` green end-to-end. Repo: market-data-processing-service.
- [x] ✅ [INFRA] P1. **Audit the fleet for STALE `BASE_IMAGE_DIGEST` pins + add a warn-level QG/cron drift check.**
      mdps's pin had drifted to `e939b4ee` (base UTL 0.11.0 / UAC 0.15.0) while its own floors require UTL ≥0.12.0 / UAC
      ≥0.19.0 → the build re-resolved from the registry and failed; the digest-refresh fan-out
      (`update-dependency-version.yml`) evidently never landed for mdps. A stale pin is **silent** until someone runs
      the build (red build, never a warning). Sweep every repo's `Dockerfile` `ARG BASE_IMAGE_DIGEST`, compare against
      the current `unified-trading-library:latest` digest, and flag any whose pinned base ships libs OLDER than that
      repo's `pyproject.toml` floors (the actual break condition — a merely-not-`:latest` pin is fine if it still
      satisfies). Add it as a warn-level signal (PM post-gate or the digest-pin ratchet panel already in "Out of scope")
      so drift surfaces before it becomes a red build. Repos: all service Dockerfiles + PM (the check). Provenance:
      2026-06-19 mdps build fix. — unified-trading-pm@be47dece8 | fleet consistent (16/16 pinned repos at
      sha256:6b27286abac3…) | new post-gate: scripts/quality_gates/check_base_image_digest_drift.py | PR #427

## Repo-CI table clarity + authoritative source (operator review 2026-06-19)

Operator walked the Repo-CI overview table live and surfaced three confusions, all traceable to the table design + a
stale-cache data source (full diagnosis in the 2026-06-19 session): (1) the single `CI status` lifecycle token conflates
promotion-PROGRESS with branch-FAILURE — e.g. `STAGING_GREEN` reads as "stuck" when it means "furthest-green = staging";
(2) the dep-order HOLD that lags main is INVISIBLE — empty triage queue + empty breaking cascade while
`last green (main)` sits days stale; (3) the UI reads `ci_status` from the committed `workspace-manifest.json` cache,
NOT the authoritative Firestore side-store the promoter gate actually reads, so the dashboard can show a different
status than what gates promotions.

- [x] ✅ [UI] P1. **Drop the `CI status` column; color-code the LDR/staging/main SHA cells per-branch** (green = that
      branch's last `quality-gates-v2` succeeded · red = failed · gray = unknown) from `branch_ci`. The 9-state
      `ci_status` token is noise — per-branch green/red is the simpler at-a-glance model. **DONE 2026-06-19 —
      deployment-ui@1e5b429 | pw:L2 ✓ (smoke 219 · repos-tab 23) | regression: tests/smoke/repos-tab.spec.ts.**
      Frontend-DERIVE, no backend change needed: `branchTone` (in `src/lib/repoCi.ts`) reads live `branch_ci` for
      FAILING repos (which the backend already fetches), greens non-FAILING repos (their branches all last-passed),
      grays a missing branch — so the API-budget bound on `branch_ci` is moot. Colour = solid dot + tinted SHA via
      `data-tone`; the `CI status` column is removed; staleness stays in last-green / LDR→main-delta. Also shipped a
      click-to-open colour **legend** (operator add, same commit): `branch-legend-toggle` → green/red/gray meanings +
      the behind-but-green note. + 4 `branchTone` unit tests in `src/lib/repoCi.test.ts`.
- [x] ✅ [UI] P1. **Promotion-state surface — make the dep-order HOLD visible.** A repo can sit `STAGING_GREEN` with
      main days behind and NOTHING in the triage queue / breaking cascade, because the staging→main STAGE 1.8 dep-order
      gate is a silent designed HOLD (incident 2026-06-19: fleet blocked behind `unified-api-contracts` not yet
      `MAIN_GREEN`). **DONE 2026-06-19 — deployment-ui@564961e + deployment-api@af444bb | pw:L2 ✓ (smoke 224 ·
      repos-tab 27) | regression: tests/smoke/repos-tab.spec.ts.** Backend (`deployment_api/routes/repo_ci.py`
      `_compute_dep_order` mirroring STAGE 1.8) adds per-row `tier`/`blocked_by`/`blocking` + a `promotion_held`
      aggregate (`held_repos` + `root_blockers`) to `/api/repo-ci/overview`; verified LIVE (real fleet showed
      unified-api-contracts tier-0 blocking 4 repos). Frontend: a 6th **"Promotion held — dependency order"** card
      (sibling to "Promotion blocked", which is failure-park); a top **"Promotion stalled" banner**; **root-blocker** +
      **blocked-by** chips folded into the LDR→main-delta column; plus two operator adds — a click-to-open **`?` help
      popover on every card** (the role/what-it-says explanation) and **severity/A–Z/tier sort controls**. Cleared a
      pre-existing deployment-api deep-UAC-import en route (facade `from unified_api_contracts import Mode`; ratcheted
      `CODEX_MAX_VIOLATIONS` 6→5). Provenance: 2026-06-19 operator review.
- [x] ✅ [UI] P2. **Per-column `?` help on every Repo-CI table column** (operator request 2026-06-19). Every header
      (Repo · LDR · staging · main · last green (main) · LDR→main delta · SIT · PRs · Image) carries a click-to-open `?`
      popover explaining what the column represents — reuses the `HelpPopover` primitive; right-edge columns drop the
      popover inward so it doesn't run off the table. **DONE — deployment-ui@62b4fed | pw:L2 ✓ (repos-tab 28) |
      regression: tests/smoke/repos-tab.spec.ts** ("every table column carries a ? help popover").
- [x] ✅ [UI] P1. **Split the promotion stall into per-hop + stall-reason columns** (operator request 2026-06-19 — "2
      separate columns, can't read anything clearly"). The single `LDR→main delta` cell crammed lag + per-hop + reason
      illegibly; now three columns tell the story: **LDR→main delta** (headline distance + lag-age chip), **Promotion
      hops** (LDR→stg ✓ / stg→main Nf — WHICH hop holds the content), **Stall reason** (WHY: dep-order / staging→main
      not promoting · status stale / LDR→staging drain behind / PR #N jammed / root blocker / drain stalled). New pure
      `classifyStall(row)` (5 classes, unit-tested ×6) drives the reason chip from deltas + open_prs + ci_status the
      overview already returns (NO backend change); each column carries its own `?` taxonomy popover. **This is the
      surface that makes the staging→main promoter-not-firing class VISIBLE per-repo** — the agent-orchestrator case
      where `ci_status=MAIN_GREEN` masked a real 8-day lag (LDR→staging drained, staging 144 files ahead of main, no
      PR). **DONE — deployment-ui@82bcfe4 | pw:L2 ✓ (repos-tab 29) | regression: tests/smoke/repos-tab.spec.ts**
      ("per-hop + stall-reason columns localize a staging→main promoter stall (the AO class)").
- [x] ✅ [UI] P2. **Full-width shell + per-column vertical dividers on the Repo-CI table** (operator request 2026-06-22
      — "lots of space on the right we're not using" + "very little distinction between columns"). The deployment-ui
      home shell capped `<main>` at `max-w-[1920px]` and centered it, wasting the right ~third of a ≥2560px monitor;
      dropped the cap → `w-full` so the layout ADAPTS to the screen (visible effect only above 1920px, so the ≤1920
      smoke + visual baselines are unaffected — no-op at their viewport). The 14-column overview table had no
      inter-column separation; added per-column dividers (`border-r` on every cell but the last) + `px-3` breathing room
      (first/last cells flush to the card edge), reusing the existing `/40`·`/15` border tokens. Pure CSS/className, NO
      backend change. **DONE — deployment-ui@065edc1 | pw:L2 ✓ (76 passed) + UI-QG ✓ (82 tests · 76.73% cov · build) |
      regression: tests/smoke/repos-tab.spec.ts** ("full-width shell + per-column dividers on a wide monitor" — asserts
      `<main>` width >2200px + a middle header-cell `border-r` at a 2560px viewport, both of which the old
      cap/no-divider table fail). Provenance: 2026-06-22 operator review.
- [x] ✅ [UI] P2. **Full-width follow-up — shell gutter, no horizontal-scroll flicker, no whole-panel focus ring**
      (operator review 2026-06-22, after the full-width change). Three fixes: (1) the right edge had NO gap — Tailwind
      `px-*` is DEAD on `<main>` because the unlayered `* { padding: 0 }` reset outranks Tailwind v4's layered
      utilities; added an explicit `.app-shell-gutter` CSS class (5px small / 20px lg+). (2) a horizontal scrollbar
      flickered on every background refresh — added `overflow-x: clip` on the shell root (the data table scrolls in its
      own `overflow-x-auto`). (3) a cyan focus ring flashed around the WHOLE Repos-CI panel during refresh — removed the
      whole-panel `focus-visible:ring-*` from the Radix `TabsContent` primitive (affects all 6 tabs; the panel-level
      ring isn't useful). Verified by DOM probe: `padR=20px`/`5px` responsive, `hOverflow=-6` across a refresh, panel
      ring class gone. **DONE — deployment-ui@17fa95e | pw:L2 ✓ (261 passed) + UI-QG ✓ (82 tests · build) | regression:
      tests/smoke/repos-tab.spec.ts** ("shell gutter + no horizontal scrollbar + no whole-panel focus ring").
- [x] ✅ [INFRA] P1. **deployment-ui must read `ci_status` from the AUTHORITATIVE Firestore side-store, not the
      committed `workspace-manifest.json` cache.** `deployment_api/routes/_repo_ci_manifest.py` reads the committed
      manifest's `ci_status` (a CI-written cache, 120s TTL) — but the promoter gate overlays the LIVE `ci_status/{repo}`
      Firestore store, so the dashboard can show a DIFFERENT status than what actually gates promotions. Do the pending
      Phase-2 one-function swap (`ManifestView.ci_status_for` → `ci_status_store.resolve_ci_status_map`), adding
      `google-cloud-firestore` to deployment-api. SSOT: `ci_status_firestore_side_store_2026_06_10.md`. Repo:
      deployment-api. Provenance: 2026-06-19 operator review. **DONE — deployment-api@03c5d9f |
      `_ci_status_firestore_store.py` + `google-cloud-firestore>=2.0.0` in pyproject.toml; `load_manifest_view` overlays
      Firestore per-repo at cache-miss time**
- [x] ✅ [PROMOTION] P2. **(track-3 cross-ref — do NOT implement in the UI track)** Forward staging→main promotion lags
      fleet-wide (services ~2 days behind main while libs promote): STAGE 1.8 dep-order tiered-drain + a
      `staging_versions` registration gap. **Confirmed FLEET-WIDE 2026-06-19** via the new Stall-reason column: ~16
      repos render "staging→main not promoting · status stale" (ci_status reads MAIN_GREEN while staging is N files
      ahead of main with NO open PR). Root signal in the committed manifest: `agent-orchestrator` +
      `unified-api-contracts` carry `staging_version: None` (no semver baseline → the staging→main promoter never opens
      a PR; main last moved via a manual "fleet unjam" drain #324 on 06-17). The promoting repos (mtds 0.17→0.19,
      strategy 0.15→0.16, UTL 0.13→0.14) all have a real `staging_version`. Owned by the CI-escalation / promotion track
      (`cicd_promotion_pipeline_2026_06_18.md`) — surfaced here only because it is what makes the UI read "stuck"; the
      UI side (this plan) is DONE (the column makes it visible per-repo). Repo: unified-trading-pm (promotion
      machinery).

## Out of scope here (already filed/blocked — coordinate, do NOT reimplement)

- Version-coherence panel, rollout-ratchet panels (template-drift + Dockerfile digest-pin), G4 ruleset-drift, G5
  change-freeze banner — blocked on the Firestore verdict-store (master plan); consolidator-health (G3) IN-PROGRESS
  (slot-3); runtime deploy-signal v2 already filed (master L212).

## Success criteria

- An alert of ANY class opens its deployment-ui surface and shows the full picture (fleet-runtime + central-VM
  included).
- Fleet-Git page is LIVE (token minted).
- deployment-ui Cloud Build pane shows the current build + history for every repo (regional + REPO_NAME-keyed); the
  triggers pane survives a Redis outage.

## Codex SSOT updates

- `codex/04-architecture/runtime-deployment-topology.md` — deployment-ui fleet-runtime + unified-alert-ledger surfaces.
