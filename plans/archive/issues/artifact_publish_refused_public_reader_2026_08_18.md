---
doc_type: issue
title: "Artifact publish refused — account served as public (non-member) reader, blocks republishing both client artefacts"
summary: >-
  Three identical consecutive refusals publishing the platform integration guide on 2026-08-18. The error is
  account/platform-side, not content-side, and blocks republishing both client-facing artefacts. Content is safe —
  committed to codex — but the published pages are stale relative to the repository.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin]
tags: [artifact, publish, client-disclosure, blocked-operator]
related:
  [
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
priority: P1
parent_epic: system_readiness_master
source: "Interactive session 2026-08-18, republishing the measured edition of the platform integration guide."
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "workaround applied 2026-08-18 — republished from a fresh file_path"
drift_direction: NA
context_scope: [/plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md]
---

# Artifact publish refused — public (non-member) reader

## Measured

Three identical consecutive refusals — a stable condition, not a flap — publishing
`codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`:

```
publish refused: could not verify the target page is not a review page
(transient read failure: artifact read failed: this artifact is served to you as a
public (non-member) reader, and reading public artifacts that way is not enabled yet)
```

Attempted both with and without an explicit `url` targeting the existing artifact
(`https://claude.ai/code/artifact/8f61245e-1444-4963-9898-12704153d41c`). Identical refusal each time.

## Why this is not a content problem

The refusal is about READING the existing published page to verify it is not a review page — an account/membership
state on the artifact platform. Nothing about the file could cause it: the same file published successfully on
2026-08-16 from this same session.

## Impact

- **The published platform guide is STALE** — it shows the 2026-08-16 flow draft with 36 `pending` placeholders, while
  the repository holds the 2026-08-18 measured edition (`unified-trading-pm@aa1ee152ae`): 660-triple denominator,
  48.54% volume-weighted coverage, the 0/844/20 readiness rollup, and the canonical-failure disclosure.
- The strategy-service walkthrough was not attempted but would presumably refuse identically.
- **No data loss.** Both artefacts' sources are committed under `codex/14-customer-journeys/commercial-model/`, which
  is the durable copy; the artifact page is only a rendering of it.

## Todos

- [ ] [OPERATOR] P1. **Check the claude.ai artifact/account state** — the error names a membership condition ("served
      to you as a public (non-member) reader"). Likely resolvable from account artifact settings rather than by any
      change here.
- [ ] [AGENT] P2. **Retry the publish once the account state is resolved**, from
      `codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html` — the file is ready and
      needs no further edits. Republish the strategy-service walkthrough in the same pass.
- [ ] [AGENT] P3. **Record the outcome here** so a recurrence is recognised as a known condition rather than
      re-diagnosed — three identical refusals cost several attempts before being classified as stable.

## RESOLVED — 2026-08-18, workaround applied

**Root cause confirmed by the operator: an account switch.** The refusal was the tool trying to READ the previously
published page, owned by the *previous* account — nothing to do with the file.

**The workaround is now the documented recovery path**: publishing from a **fresh `file_path`** claims a new URL under
the current account. Both artefacts were republished this way from scratchpad render copies; the committed sources under
`codex/14-customer-journeys/commercial-model/` remain the SSOT:

- Platform integration guide — `https://claude.ai/code/artifact/991d31e9-fb77-4ef5-b15c-124e37541258`
- Strategy service walkthrough — `https://claude.ai/code/artifact/0cb35a2d-ecc7-4d47-b855-bb24e51d8d8e`

Earlier URLs are orphaned with the previous account. **Nothing was lost, and only because the sources were committed
first** — which is why this incident became the hard rule
[artefact-source-must-be-committed](/codex/12-agent-workflow/artefact-source-must-be-committed.md), where the recovery
mechanics now live permanently. The operator todo (check account state) is moot — the workaround needs no account change.
