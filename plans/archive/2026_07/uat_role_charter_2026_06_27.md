---
doc_type: plan
title: UAT / QA role charter — the review agent as PR gate
summary:
  Formalize the existing `review` agent as the UAT/QA registry row that gates every PR -- write its charter (model
  sonnet / thinking high / lifecycle persistent), name its /pr-check skill, document the two-tier light (impl-vs-plan
  done_definition) / heavy (enhanced tests + opus escalation on a major bump) decision, and land a regression spec
  proving the gate fires. Additive -- no change to the live PR-review flow.
status: complete
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [role-registry, uat, qa, review, pr-gate, charter, archived]
related:
  [
    ../epics/agent_operating_framework_master.md,
    /plans/archive/2026_07/role_registry_schema_and_broker_mvp_2026_06_25.md,
    /plans/archive/2026_07/pm_role_charter_formalization_2026_06_25.md,
  ]
created: 2026-06-27
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-16
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: role_registry_schema_and_broker_mvp_2026_06_25
source:
assigned_role: review
drift_direction: advance-code
---

# UAT / QA role charter — the review agent as PR gate

> **🗄️ ARCHIVED 2026-07-16 — core delivered + live (operator decision).** The UAT/QA charter (Phase 0) is DONE and in
> daily use: `unified-trading-pm/agents/review.md` carries the full `agent-role` registry row (`role: review`,
> `model: sonnet`, `thinking: high`, `lifecycle: persistent`, triggers/does/does_not/escalation_to/temperament_base),
> loads in `role_registry.py`, and is `docspec`-green (schema SSOT `scripts/docs/docspec.py`; `role-registry.md` codex
> doc deleted 2026-07-16). Phase 1 `/pr-check` shipped at **MVP** (documented boot-prompt command in
> `review.md § Available skills`); Phase 2's two-tier light/heavy + major-bump→opus-review decision is documented in
> `review.md` (§ "Your job is UAT/QA … TWO-TIER") + this plan's Locked design. The remaining "fuller" scope — a backend
> `/pr-check` light-JSON endpoint + a synthetic-PR regression spec — is **NOT REQUIRED**: it's the deferred "real
> skill-dispatch framework", and this is one of the role pilots `agent_operating_framework_master` defers to next
> quarter.

> **W6 role instance** of `agent_operating_framework_master` — the **UAT/QA** role on the spine. UAT = the existing
> `review` agent, formalized as a first-class registry row whose job is to **gate every PR**. Mostly
> **making-explicit**: `agents/review.md` already runs as a persistent reviewer; this plan writes its charter, names its
> `/pr-check` skill, documents the two-tier (light/heavy) decision, and lands a regression check that proves the gate
> actually fires.

## Why

Every PR toward the integration branch needs an automatic acceptance check that the implementation matches the plan it
claims to satisfy — not just that the code compiles. The `review` agent already performs this UAT/QA function, but it is
not yet a _registry row_: there is no machine-readable charter declaring its model/thinking/lifecycle/triggers/
escalation, and its on-demand review verb is not packaged as a named skill. Formalizing it (a) validates the spine
(`role_registry_schema_and_broker_mvp`) against the QA boundary, and (b) makes "ask the review role to gate this PR" a
broker lookup like any other. This is additive — the live reviewer keeps running; we add its charter + skill around it.
SSOTs: `unified-trading-pm/agents/review.md` (the `review` registry row) + `scripts/docs/docspec.py` (`agent-role`
schema; the `role-registry.md` codex doc was retired 2026-07-16), `/codex/06-coding-standards/model-tier-selection.md`.

## Locked design (operator, 2026-06-27)

- **UAT gates EVERY PR with a two-tier check.**
  - **Light tier (any PR)**: verify the implementation against the plan's `done_definition` (the per-todo `Gate:`
    acceptance criteria) AND against the actual code/diff — does the diff do what the plan said it would, with a cited
    regression spec where one is required.
  - **Heavy tier (major version bump only)**: additionally run the enhanced test suite. A **major bump** here means a
    breaking/`feat!` change graduating the major version (the human-override breaking marker), not a 0.x-minor /
    docstring / refactor (which are content-non-breaking). A heavy review **escalates to an opus reviewer** — the
    synthesis-layer model tier per `model-tier-selection` — because a major-version gate is the highest-stakes review.
- **`review` is a persistent role**: `lifecycle: persistent`, `model: sonnet`, `thinking: high` (the standing default in
  the role registry). The heavy-tier opus escalation is a per-PR model override at the major-bump decision, not a change
  to the role's base model.
- **No PR-flow behavior change**: the reviewer continues to read the diff + plan checkboxes and reject unflipped /
  evidence-missing ticks exactly as today. The charter _describes_ the gate; it does not alter quickmerge / the
  `quality-gates-v2` server gate.

## Phased execution DAG

### Phase 0 — UAT/QA charter row [depends: spine Phase 1]

- [x] ✅ [DOCS] P1. Schematize `unified-trading-pm/agents/review.md` as the UAT/QA registry row: `role: review`,
      `model: sonnet`, `thinking: high`, `lifecycle: persistent`, `triggers` (any PR opened/updated, plan-checkbox
      flip), `does`/`does_not` (gates PRs; does NOT author plans or ship code), `escalation_to` (opus reviewer on a
      major bump; operator for ambiguous acceptance), `temperament_base` (rigorous). **Note**: this is being done now
      under the AO MVP. **Gate**: `docspec --check` clean; loads in `role_registry.py` as `role=review`. — DONE
      `agent-orchestrator@acbf930` (review.md agent-role row + 2-tier UAT prompt: light impl-vs-plan / heavy
      enhanced-tests + opus escalation).

### Phase 1 — /pr-check skill (the on-demand review verb) [depends: P0]

- [ ] [CODE] P1. `/pr-check <pr>` skill → diff vs `done_definition` + plan: load the PR diff and the plan's per-todo
      `Gate:` criteria, return light JSON `{ matches_plan, missing_gates, missing_regression, verdict }`. Reuses the
      existing review-agent read paths (plan checkboxes + diff). **Gate**: returns valid JSON for a known PR; verdict
      matches a hand-checked PR. — MVP-DONE as a documented boot-prompt command (`review.md § Available skills`); the
      backend light-JSON endpoint is deferred (real skill-dispatch framework). NOT REQUIRED for archival.

### Phase 2 — two-tier light/heavy decision [depends: P0]

- [ ] [DOCS] P1. Document the 2-tier light/heavy decision: what counts as a "major bump" (breaking/`feat!` major-version
      graduation, content-based per `detect_breaking_change.py` — a 0.x-minor / docstring / refactor is NOT a major
      bump) → triggers the heavy enhanced-test tier → escalates to an **opus** reviewer. Cross-link the spine + the
      model-tier SSOT. **Gate**: decision doc states the major-bump trigger + the opus escalation; no new gate code. —
      Substantively DONE: the 2-tier decision + major-bump→opus escalation is documented in `review.md` (§ "Your job is
      UAT/QA … TWO-TIER") + this plan's Locked design; a codex cross-link into `model-tier-selection.md` is deferred
      (nice-to-have). NOT REQUIRED for archival.

### Phase 3 — regression spec proving the gate fires [depends: P1]

- [ ] [CODE] P1. A regression spec / check that the gate fires on a PR: a synthetic PR whose diff violates a plan
      `Gate:` (e.g. a missing regression spec) MUST produce a non-passing `/pr-check` verdict. **Gate**: the check fails
      on the violating synthetic PR and passes on a conforming one; QG green. — DEFERRED pilot scope (not built;
      requires the backend `/pr-check` endpoint from Phase 1). Not on the make-AO-usable critical path per the epic;
      next quarter.

## Success criteria

- `review.md` carries a valid `agent-role` charter row; the UAT/QA role is loadable + routable via the broker
  `(role=review, domain=*)`.
- `/pr-check` returns light JSON (diff vs `done_definition`); the two-tier light/heavy decision is documented with the
  major-bump → opus escalation rule.
- The regression spec proves the gate fires (fails on a violating PR, passes on a conforming one).
- **Zero change** to the live PR-review flow (the reviewer still rejects unflipped / evidence-missing ticks) — verified
  by running the reviewer against a real PR.

## Codex SSOTs

- `unified-trading-pm/agents/review.md` is the UAT/QA worked-example registry row (`role=review`, `model=sonnet`,
  `thinking=high`, `lifecycle=persistent`); the `agent-role` schema is enforced by `scripts/docs/docspec.py` and the
  `/codex/04-architecture/role-registry.md` doc was retired 2026-07-16.
- `/codex/06-coding-standards/model-tier-selection.md` — the opus-on-major-bump escalation is a model-tier decision; the
  heavy review tier follows the synthesis-layer opus policy.

## Progress Log

- 2026-06-27: Plan created as the UAT/QA role instance on the spine. Mostly making-explicit — the `review` agent already
  gates PRs; this plan writes its charter, names `/pr-check`, documents the two-tier (light impl-vs-plan on every PR /
  heavy enhanced-tests + opus escalation on a major bump) decision, and adds a regression check that the gate fires.
  Human-driven (`assigned_vm: NA`, `execution_scope: local-only`). Depends on `role_registry_schema_and_broker_mvp`.
- 2026-07-16: **ARCHIVED** (operator decision). UAT/QA charter (Phase 0) delivered + live — `agents/review.md` is the
  running review agent's `agent-role` registry row (`role: review`, sonnet/high/persistent), loads in
  `role_registry.py`, docspec-green (schema SSOT now `scripts/docs/docspec.py`;
  `/codex/04-architecture/role-registry.md` deleted 2026-07-16). Phase 1 `/pr-check` at MVP (documented command in
  `review.md`); Phase 2 two-tier decision documented in `review.md`. Phase 3 regression spec = deferred pilot scope
  (next quarter, per `agent_operating_framework_master`). No live gap — clean archive. Moved to
  `plans/archive/2026_07/`.
