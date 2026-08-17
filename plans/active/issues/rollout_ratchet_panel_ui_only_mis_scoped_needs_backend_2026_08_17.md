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
   API-readable per-repo drift status exists anywhere.**
2. **Ruleset/branch-protection drift** (`.github/workflows/rules-alignment-agent.yml`) — a live, real workflow (per
   the G4 item's own description: "pages WARNING… no UI"); confirmed 0 Firestore/verdict_store references, 4 Slack
   references. **It only pages Slack — never persists a structured per-repo verdict anywhere deployment-api could
   read.**
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

- [ ] [CODE] P2. Wire `detect_template_drift.py --json` into a scheduled GitHub Actions workflow (mirror
      `version-coherence-check.yml`'s cadence/shape) writing per-repo verdicts to a new Firestore
      `template_drift_verdicts` collection. Repo: unified-trading-pm.
- [ ] [CODE] P2. Wire `rules-alignment-agent.yml` to ALSO write per-repo verdicts to a new
      `ruleset_drift_verdicts` Firestore collection (currently Slack-paging only, per G4's own framing in
      `monitoring_control_plane_master_2026_06_10.md`). Repo: unified-trading-pm.
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
