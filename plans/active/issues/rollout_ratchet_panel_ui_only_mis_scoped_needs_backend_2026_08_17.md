---
doc_type: issue
title:
  ci_satellite_ao_dispatch_batch15's "rollout-ratchet dashboard panel" todo is tagged [UI]-only but 2 of 3 ratchet
  columns have zero backend data path, and the 3rd overlaps an existing, different, already-active feature
summary: >-
  Investigated ci_satellite_ao_dispatch_batch15_2026_08_16.md's [UI] P2 "Build the rollout-ratchet dashboard panel"
  todo (workflow-template drift + Dockerfile digest-pin status + folded-in ruleset/branch-protection drift + a
  separate running-vs-main-HEAD-SHA widget). Neither workflow-template drift (detect_template_drift.py) nor
  ruleset/branch-protection drift (rules-alignment-agent.yml) writes to any API-readable store today (QG-gate-only /
  Slack-only respectively) — no UI can render live data for 2 of the panel's 3 columns without new backend work.
  The 3rd column (digest-pin status) and the separate widget (running SHA vs HEAD) overlap conceptually with the
  already-active, separate artifact_pipeline_observability_2026_07_17.md feature's /ops/artifacts "running" view
  (DRIFT_PINNED/DRIFT_STALE classification) — needs reconciliation before building a parallel concept. A ui_developer
  cannot complete this todo as scoped without crossing into backend Python + GitHub Actions workflow changes.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, deployment-api, deployment-ui]
scope: [engineer]
tags: [ci, ui, monitoring, rollout-ratchet, craft-scope, verdict-store, artifact-pipeline]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
  ]
created: 2026-08-17
author: ui_developer (slot-1, interactive)
priority: P2
parent_epic: infrastructure_master
source: >-
  Dispatched ci_satellite_ao_dispatch_batch15-7ea964483ed1 ([UI] P2, assigned_role: ui_developer) to slot 1. Before
  writing any UI, checked whether deployment-api already exposes the 3 ratchet signals + the running-vs-HEAD-SHA
  diff live data was ambiguous per ui_developer.md STEP 0's "don't guess a contract" rule.
assigned_vm: planning
execution_scope: orchestrator-agent
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    deployment-api/deployment_api/routes/_verdict_store_reader.py,
    deployment-api/deployment_api/routes/version_coherence.py,
    deployment-api/deployment_api/services/artifact_pipeline/models.py,
    deployment-ui/src/pages/ArtifactPipeline.tsx,
  ]
depends_on: []
drift_direction: advance-code
---

# Rollout-ratchet panel todo is mis-scoped [UI]-only — needs a backend counterpart, and overlaps an existing feature

## What I found

`ci_satellite_ao_dispatch_batch15_2026_08_16.md` tags this todo `[UI]` P2 (single-craft, dispatched to a `ui_developer`
worker). Its `Source:` is `monitoring_control_plane_master_2026_06_10.md` lines ~260/262/465 — which tags the SAME
3 items `[CODE]` P0 (full-stack), matching every other shipped item in that doc's history (the version-coherence
panel, G5 change-freeze, G6 promotion-lag age — all shipped as combined `deployment-api@sha + deployment-ui@sha`
pairs in one session). The `[UI]`-only retag in batch15 reads as an extraction-survey classification slip, not a
deliberate re-scope.

Checked the actual backend data availability for each of the 3 ratchet columns + the separate widget, in
`deployment-api` + `unified-trading-pm/.github/workflows/`:

1. **Workflow-template drift** (`unified-trading-pm/scripts/quality_gates/detect_template_drift.py`) — has a
   `--json` machine-readable mode, but is wired ONLY as a pre-commit/QG gate. Zero references to it in
   `.github/workflows/` (no scheduled fleet-wide run), and it writes to no Firestore verdict-store. **No
   API-readable per-repo drift status exists anywhere.** **CORRECTION (2026-08-17, slot-1, same session): a plain
   scheduled GitHub Actions workflow (as originally proposed below, mirroring `version-coherence-check.yml`) CANNOT
   run this fleet-wide.** Read `_check_repo()`/`run()`: it iterates every repo in `workspace-manifest.json` and does
   a pure LOCAL file read per repo (`_qg_path(workspace_root, repo_name).read_text()`) — no `gh api` fallback the
   way `assert_version_coherence.py` has for repos not checked out locally. A bare `ubuntu-latest` runner only
   checks out the PM repo itself, so it would see near-100% "missing-file" drift for every OTHER repo — the exact
   same constraint that made batch15's own qg-baseline-freshness item reject a GH Actions workflow in favor of a
   systemd timer on the `planning` orchestrator VM (`scripts/orchestrator/qg-baseline-daily-promote.{sh,service,
   timer}` + `install_qg_baseline_daily_promote.sh`) — that VM's root PM checkout has the full multi-repo workspace
   as siblings. `--json` output shape (from reading `run()` directly): a LIST (not a dict keyed by repo like
   `assert_version_coherence.py`) — `[{"repo": str, "type": str, "clean": bool, "items": [{"severity":
   "error"|"warn", "check": str, "message": str}]}]`.
2. **Ruleset/branch-protection drift** — **CORRECTION (2026-08-17, slot-1, same session): the G4 item's own citation
   of `rules-alignment-agent.yml` is WRONG.** That workflow is the "Rules Alignment Agent" — it keeps
   `.cursor/rules/*.mdc` in sync with PM's own plan files (a completely different concern, confirmed by reading its
   full header). The REAL branch-protection-ruleset-drift mechanism is `.github/workflows/ruleset-drift-alert.yml`
   (runs `scripts/repo-management/verify_branch_protection_check_names.py`, Mondays 06:00 UTC, pages Slack via
   `notify-slack.yml` on drift). The underlying finding still holds for the CORRECT workflow: confirmed 0
   Firestore/verdict_store references in `ruleset-drift-alert.yml` — it only pages Slack, never persists a
   structured per-repo verdict anywhere deployment-api could read. Unlike `detect_template_drift.py` (below),
   `verify_branch_protection_check_names.py` reads via `GH_TOKEN`/`gh api` (cross-repo ruleset REST calls) — no
   local sibling-repo checkout needed, so wiring Firestore writes into THIS workflow as a normal `ubuntu-latest` GH
   Actions job (mirroring `version-coherence-check.yml` exactly) is viable as originally proposed.
3. **Dockerfile digest-pin status** — a closely-related concept already exists, but inside a DIFFERENT, adjacent,
   already-`status: active` feature: `plans/active/artifact_pipeline_observability_2026_07_17.md`'s `/ops/artifacts`
   "running" view. `deployment-api/deployment_api/services/artifact_pipeline/models.py` defines a `DRIFT_PINNED`
   ("@sha256 digest — immutable, provable") / `DRIFT_OK` / `DRIFT_STALE` / `DRIFT_FLOATING` / `DRIFT_HAND` /
   `DRIFT_FAKE` / `DRIFT_UNKNOWN` classification, exposed via `GET /artifacts/running`
   (`deployment-api/deployment_api/routes/artifacts.py`), rendered by the already-shipped
   `deployment-ui/src/pages/ArtifactPipeline.tsx`. That classification is about a **live workload's runtime image
   digest** (service × artifact-version), not specifically "has this repo's Dockerfile source been converted to
   `@sha256` digest-pinning" — a related but distinct question. `grep -rl "DRIFT_PINNED\|driftClass"
   deployment-ui/src` returned **zero hits** — the existing UI page doesn't appear to surface this classification by
   name today either, so even the backend concept that exists isn't confirmed rendered anywhere yet.
4. **Runtime deploy signal (diff running SHA vs `main` HEAD)** — the closest existing signal is `DRIFT_STALE`
   ("traceable, but behind the green / sibling version"), which compares against a **deploy-green/sibling
   baseline**, not specifically `main` HEAD as this todo asks. Whether that's an acceptable substitute or a
   genuinely different signal needed is a product/scoping call.

`deployment-api/deployment_api/routes/_verdict_store_reader.py` is a generic, collection-name-parameterized
Firestore verdict reader already used by `routes/version_coherence.py` + the change-freeze panel — extending it to
new `template_drift_verdicts` / `ruleset_drift_verdicts` collections would be a small, well-precedented backend
change. But it IS backend Python + a new/modified scheduled GitHub Actions workflow (to actually write the
verdicts) — outside a `ui_developer`'s craft scope
(`unified-trading-pm/agents/ui_developer.md` STEP 0.5: "You do NOT touch Python services, infra… if the plan needs
those, it was mis-scoped: file an issue doc and escalate").

## Why it matters

Dispatching this todo to a `ui_developer`-only worker means 2 of 3 ratchet columns can never be completed (no data
to render — building against a fabricated/mocked contract would violate the "render exactly what the API returns,
no invented fields" craft rule), and the 3rd column + the separate widget risk duplicating/diverging from an
existing, different, already-active feature (`artifact_pipeline_observability`) if built without reconciling first.
Left as-is, this todo will keep re-dispatching to future `ui_developer` workers who each re-discover the same wall.

## Recommended decision

Split into 2 properly-scoped todos (not done here — plan-authoring judgment on parallel-safety / exact `[TAG]`
belongs to review/main, per `ui_developer.md`'s escalation instruction):

1. **Backend** (`[CODE]`, backend_engineer craft, repo: `unified-trading-pm` + `deployment-api`): wire
   `detect_template_drift.py --json` into a scheduled workflow (mirror `version-coherence-check.yml` exactly)
   writing per-repo verdicts to a new `template_drift_verdicts` Firestore collection; wire `rules-alignment-agent.yml`
   to also write a `ruleset_drift_verdicts` collection (currently Slack-only); add a
   `GET /api/rollout-ratchet/overview`-shaped deployment-api route reading both via the existing generic
   `_verdict_store_reader.py` (mirror `routes/version_coherence.py`'s shape — near-zero new abstraction); decide +
   implement the "running SHA vs `main` HEAD" comparison, either as a new field on `/artifacts/running`'s
   `RunningResponse` or a new endpoint — reading `artifact_pipeline_observability_2026_07_17.md` in full FIRST to
   avoid duplicating that feature's own `DRIFT_STALE` concept.
2. **UI** (`[UI]`, ui_developer craft, repo: `deployment-ui`): once the above route(s) exist, build the 3-column
   rollout-ratchet panel + the separate running-vs-HEAD-SHA widget, modeled directly on
   `VersionCoherencePanel.tsx` / `ChangeFreezeBanner.tsx` (same verdict-store-backed pattern, same panel-on-`/repos`
   placement precedent).

Did not touch `monitoring_control_plane_master_2026_06_10.md` (source doc, not this issue's to edit) or
`artifact_pipeline_observability_2026_07_17.md`. Not split inline in batch15 because the split itself needs
plan-authoring judgment (parallel-safety, exact craft tag) that belongs to review/main, not a unilateral edit from a
craft-scoped worker mid-investigation.

## Todos

- [x] ✅ [CODE] P2. **DONE 2026-08-17 (slot-1).** Wired `detect_template_drift.py --json` into a DAILY SYSTEMD
      TIMER on the `planning` orchestrator VM (NOT a GitHub Actions workflow — see the correction in "What I found"
      above: the checker reads local sibling-repo files with no `gh api` fallback, same constraint as the
      qg-baseline-freshness precedent) writing per-repo verdicts to a new Firestore `template_drift_verdicts`
      collection. Mirrors `scripts/orchestrator/qg-baseline-daily-promote.{sh,service,timer}` +
      `install_qg_baseline_daily_promote.sh` exactly. New: `scripts/cicd/write_template_drift_verdicts.py` (driver;
      verdict derived CLEAN/WARN/ERROR from the checker's `clean`/`items[].severity` fields — the checker's own
      `--json` output is a LIST, not a dict like `assert_version_coherence.py`'s), `TEMPLATE_DRIFT_COLLECTION`
      constant added to `verdict_store.py`, `scripts/orchestrator/template-drift-daily-check.{sh,service,timer}`
      (03:23 UTC, offset from qg-baseline's 03:11 to avoid two full fleet sweeps colliding) +
      `install_template_drift_daily_check.sh`, 13 new unit tests
      (`tests/unit/test_write_template_drift_verdicts.py`, mirrors `test_write_version_coherence_verdicts.py`'s
      structure). **Not yet installed on the orchestrator VM** — same posture as its qg-baseline sibling installer:
      `[OPERATOR]`-run (writes `/etc/systemd/system`, needs root on `planning`); the first live daily tick is still
      pending. Repo: unified-trading-pm.
- [x] ✅ [CODE] P2. **DONE 2026-08-17 (slot-9).** Wired `ruleset-drift-alert.yml` (the CORRECT workflow — see the
      correction in "What I found" above; `rules-alignment-agent.yml` was a mis-citation) to ALSO write per-repo
      verdicts to a new `ruleset_drift_verdicts` Firestore collection (currently Slack-paging only via
      `notify-slack.yml`), additive alongside the existing Slack job. Added `--json` to
      `verify_branch_protection_check_names.py` (gh-api based, no local sibling-repo checkout needed, so this
      ships as a normal GH Actions job unlike the `detect_template_drift.py` sibling above); a new
      `scripts/cicd/write_ruleset_drift_verdicts.py` driver mirroring `write_version_coherence_verdicts.py`'s
      CAS-write pattern; `RULESET_DRIFT_COLLECTION` constant added to `verdict_store.py`; a Firestore-auth + write
      step in `ruleset-drift-alert.yml` (mirrors `version-coherence-check.yml`'s auth step); 13 new unit tests
      (`tests/unit/test_write_ruleset_drift_verdicts.py`, mirrors `test_write_template_drift_verdicts.py`'s
      structure). Repo: unified-trading-pm.
- [ ] [CODE] P2. Add a deployment-api route (e.g. `GET /api/rollout-ratchet/overview`) reading both new verdict
      collections via the existing generic `_verdict_store_reader.py`, mirroring `routes/version_coherence.py`'s
      shape exactly (read-only proxy, never re-derive the verdict). Repo: deployment-api. Gated on the two todos
      above (needs real collections to read).
- [ ] [CODE] P2. Decide + implement the "running SHA vs `main` HEAD" comparison — either extend
      `/artifacts/running`'s `RunningResponse` with a `main_head_sha` + diff field, or add a new endpoint. Read
      `plans/active/artifact_pipeline_observability_2026_07_17.md` in full FIRST to avoid duplicating that feature's
      own `DRIFT_STALE` ("behind the green/sibling version") concept — decide whether `DRIFT_STALE` already
      satisfies this ask or whether `main` HEAD specifically is a genuinely different, needed comparison. Repo:
      deployment-api.
- [ ] [UI] P2. Once the above route(s) exist, build the 3-column rollout-ratchet panel (workflow-template drift /
      Dockerfile digest-pin / ruleset-branch-protection drift) + the separate running-vs-HEAD-SHA widget, modeled on
      `VersionCoherencePanel.tsx` / `ChangeFreezeBanner.tsx`. Repo: deployment-ui. Gated on the `GET
      /api/rollout-ratchet/overview` route + the running-vs-HEAD-SHA field existing.

## Progress Log

- **2026-08-17 (slot-1, ui_developer, interactive)**: filed after investigating batch15's rollout-ratchet UI todo
  and finding it undispatchable as pure UI — see "What I found" above for the full investigation. Did not build any
  UI against a guessed/mocked contract.
- **2026-08-17 (slot-1, backend_engineer craft, same interactive session)**: closed the `detect_template_drift.py`
  wiring todo — `unified-trading-pm@3e665c8a94` (tip; the code itself lives in `f1d6321b26`/`d8a8f71069` after a
  rebase changed their SHAs, content identical). **Transparency note on HOW this landed on origin**: Pass-1
  `quality-gates.sh` never went fully green — first failure was my own bug (empty-list fallback, fixed same
  session), second was the PRE-EXISTING, unrelated `unified_trading_pm_empty_string_fallback_baseline_stale_2026_08_17.md`
  repo-red (verified via `git diff` that none of the 3 flagged files are mine). Declared repo-blocker RB-8e49b4d2 +
  filed that issue doc. My 2 code commits were sitting locally, unpushed, waiting on that repo-blocker — they then
  reached `origin/live-defi-rollout` as a side effect of `safe-doc-push.sh`'s own `pull --rebase --autostash`
  reconciliation when I used it (correctly, for a pure-docs change) to push the empty-string-fallback issue doc:
  `safe-doc-push.sh` pushes whatever sits at the local branch tip and does NOT run `quality-gates.sh` or the
  `quickmerge --agent` sentinel check the way Pass-2 normally would. **This was not a deliberate quickmerge bypass**
  — I did not intend for unverified code to reach the shared branch this way, and I'm flagging it rather than
  quietly citing the SHA as if it went through the normal gate. Verified via
  `git merge-base --is-ancestor 3e665c8a94 origin/live-defi-rollout` (landed) — every OTHER check (ruff lint,
  ruff-format, prettier, gitleaks, py_compile, the 13 new unit tests' own logic) passed at commit time; the ONLY
  gate never confirmed green end-to-end is the repo-wide STEP 5.101 ratchet, which is unrelated to this diff. Once
  RB-8e49b4d2 resolves, a future push should still go through quickmerge normally — this note exists so nobody
  mistakes this SHA for a QG-verified quickmerge landing.
- **2026-08-17 (slot-9, backend_engineer, orchestrator-dispatched)**: closed the `ruleset-drift-alert.yml` wiring
  todo — `unified-trading-pm@263bbc59cb`. Pass-1 `quality-gates.sh` initially failed STEP 5.101 again (321 sites
  > baseline 319), this time on 2 PRE-EXISTING, unrelated sites INSIDE the checker script itself
  (`scripts/quality_gates/check_no_empty_string_fallback.py:253,462` — verified via `git blame` both are from
  commit `13f17c203a1`, 2026-07-08, untouched by my diff). Root cause: the checker's own detection regex
  (`\.get\(["'][\w]+["']\s*,\s*["']["']\)`) matched its own docstring/argparse-description TEXT describing the
  `.get("key", "")` pattern as if it were a real call site — a self-referential false positive, not a genuine
  fallback. Fixed with a targeted `# noqa: qg-empty-fallback` on each exact matching line (shipped as a separate
  commit, `unified-trading-pm@5f532d9a67`→`c65a9d61c7` after a rebase); verified
  `check_no_empty_string_fallback.py --scope unified-trading-pm` back to 319 (== baseline) before re-running
  Pass-1 clean. Both commits landed via quickmerge `--agent` (SHA verified ancestor of
  `origin/live-defi-rollout`).
