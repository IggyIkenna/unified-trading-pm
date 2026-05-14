---
title: alerting-service D.5+D.7 codex compliance violations (schema provenance + fail-fast)
created: 2026-05-14
author: slot-6 (Harsh)
source:
  - alerting-service QG STEP 5.xx codex-compliance check
  - alerting-service@cbaf8d8 (D.5 stablecoin_issuer_pause_subscriber + D.7 governance_forum_watcher commits)
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

## What I found

Running QG on alerting-service after fixing N802 lint violations revealed 4 codex compliance
violations introduced by the D.5+D.7 commit (`alerting-service@cbaf8d8`):

```
❌ Raw response.json() — parse through Pydantic model_validate()
   alerting_service/subscribers/governance_forum_watcher.py (SnapshotForumPoller.fetch_proposals, TallyForumPoller.fetch_proposals)
   alerting_service/subscribers/stablecoin_issuer_pause_subscriber.py

❌ Empty string fallback — fail fast
   alerting_service/subscribers/governance_forum_watcher.py
   alerting_service/subscribers/stablecoin_issuer_pause_subscriber.py

❌ Empty dict/list fallback — fail fast
   alerting_service/subscribers/governance_forum_watcher.py
   alerting_service/subscribers/stablecoin_issuer_pause_subscriber.py

❌ Schema provenance: local BaseModel/TypedDict/dataclass found (should import from UAC or UIC)
   alerting-service:alerting_service/subscribers/governance_forum_watcher.py:GovernanceProposal
   alerting-service:alerting_service/subscribers/stablecoin_issuer_pause_subscriber.py:IssuePauseEvent
```

**Root cause**: D.5 (`stablecoin_issuer_pause_subscriber.py`) and D.7 (`governance_forum_watcher.py`)
were implemented with local `@dataclass` definitions (`GovernanceProposal`, `IssuePauseEvent`) and
raw `response.json()` parsing without Pydantic validation. These are codex violations that require
UAC schema definitions for the domain types.

All 451 unit tests pass. The N802 lint is clean. Only the codex-compliance QG step fails.

## Why it matters

**Severity: P1** — prevents alerting-service from reaching QG-clean status on the full QG run.
The codex violations are structural:

1. **Schema provenance** (`GovernanceProposal`, `IssuePauseEvent` as local dataclasses): CLAUDE.md
   requires domain types in UAC (`unified_api_contracts.internal` for internal types). Local definitions
   create a divergence risk — if another service later needs these event shapes, they'd duplicate them.

2. **Raw `response.json()` without Pydantic**: QG STEP enforces `model_validate()` to ensure schema
   drift surfaces at parse-time rather than silently producing `None`/empty values downstream.

3. **Empty string/dict/list fallbacks**: QG `no-empty-fallbacks.mdc` rule requires fail-fast on
   unexpected empty rather than silently swallowing gaps — consistent with the honest-absence SSOT.

**Scope**: Fixes require cross-repo changes:
- `unified-api-contracts`: add `GovernanceProposal` + `IssuePauseEvent` to UAC internal schemas
- `alerting-service`: replace local dataclasses with UAC imports; wrap raw JSON parsing in Pydantic

## Recommended decision

**Option A** (recommended): Add `GovernanceProposal` + `IssuePauseEvent` as Pydantic models to
`unified_api_contracts.internal.alerting` (or new module `unified_api_contracts.alerting.events`),
then update the two subscriber files to import from UAC and use `model_validate()`.

**Option B**: Grant a temporary `# noqa` exemption with a named successor plan + explicit
`## Temporary states` section. This keeps QG clean short-term while UAC schema work is scheduled.

**Slot 6 context**: UAC is not in slot 6's owned repos for this task brief. Recommending operator
assign UAC schema addition to an Ikenna slot (cross-repo design work) with alerting-service consumer
update paired.

**Successor plan**: This issue should resolve to `deployment_and_qg_strategy_implementation_2026_05_13.md`
Phase D.5+D.7 follow-up or a new `plans/active/alerting_service_schema_provenance_2026_05_14.md`.
Target resolution: ≤7 days per Findings Triage discipline.
