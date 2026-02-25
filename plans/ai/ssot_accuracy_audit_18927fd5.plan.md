---
name: SSOT Accuracy Audit
overview: "The SSOT index has 4 categories of issues: broken file paths, count drift, critical codex-vs-implementation conflicts, and missing/duplicate SSOT documents. This plan fixes the index and the underlying sources to make SSOT claims accurate."
todos:
  - id: fix-ssot-index
    content: "Fix 00-SSOT-INDEX.md: correct 4 paths (docs/→specs/), update counts (venues 22→25, services 14→15, repos 35→38, api-contracts 18→14), remove duplicate quickmerge entry, fix PM yaml paths, fix quickmerge-architecture.md reference"
    status: pending
  - id: fix-lifecycle-events
    content: "Fix 03-observability/lifecycle-events.md (P0): replace all deprecated setup_cloud_logging + unified_cloud_services.observability imports with unified_events_interface patterns; update code template; align event counts (batch=11, live=12)"
    status: pending
  - id: create-external-import-standards
    content: "Create 06-coding-standards/external-import-standards.md: document top-level import rule with correct/wrong examples, resolving stale cursor rule reference"
    status: pending
  - id: create-quickmerge-architecture
    content: "Create 05-infrastructure/quickmerge-architecture.md: consolidate quickmerge pipeline docs from cursor rules and plans, fixing the broken SSOT reference cited by 2 entries in the index"
    status: pending
  - id: fix-nested-imports-services
    content: "Fix nested imports across all 14 services: change from unified_config_interface.core.config import UnifiedCloudConfig → top-level; same for unified_events_interface; use parallel agents per service + quickmerge each"
    status: pending
  - id: fix-pm-yaml-gap
    content: "Resolve PM yaml gap: update SSOT index to point to unified-trading-codex/11-project-management/ (where actual content lives) instead of empty unified-trading-pm repo, OR create the 3 missing yaml files"
    status: pending
isProject: false
---

# SSOT Accuracy Audit — Fix Plan

## Findings Summary

### Category 1: Broken Paths in 00-SSOT-INDEX.md

The index points to files that don't exist or exist at wrong paths:

- `unified-trading-pm/mvp-universe.yaml` → **PM repo is empty** — these 3 yaml files (`mvp-universe.yaml`, `service-registry.yaml`, `venue-support-matrix.yaml`) DO NOT EXIST. Actual content (if any) is in `unified-trading-codex/11-project-management/`
- `features-delta-one-service/docs/FEATURE_SPECIFICATION.md` → actually `specs/FEATURE_SPECIFICATION.md`
- `strategy-service/docs/STRATEGY_MODES.md` → actually `specs/STRATEGY_MODES.md`
- `ml-training-service/docs/MODEL_CATALOG.md` → actually `specs/MODEL_CATALOG.md`
- `05-infrastructure/quickmerge-architecture.md` → **file does not exist** (codex `05-infrastructure/` dir was inspected)
- `05-infrastructure/quickmerge-architecture.md` is listed **twice** (lines 20 + 24)

### Category 2: Count Drift (Numbers Are Wrong)


| Claim                    | Actual                                                 |
| ------------------------ | ------------------------------------------------------ |
| 22 MVP venues            | 25 in venues.yaml (9 CEFI + 6 TRADFI + 10 DEFI)        |
| 14-service chain         | 15 in dependencies.yaml (includes `corporate-actions`) |
| 35 repos                 | 38 in WORKSPACE-MANIFEST.json                          |
| 18 venue API directories | 14 in api-contracts/                                   |


### Category 3: Critical Codex-vs-Implementation Conflicts (P0)

1. `**[03-observability/lifecycle-events.md](unified-trading-codex/03-observability/lifecycle-events.md)`** still shows **deprecated patterns**:
  - Shows `from unified_cloud_services import setup_cloud_logging`
  - Shows `from unified_cloud_services.observability import log_event`
  - Cursor rules correctly require `from unified_events_interface import setup_events, log_event`
  - The actual library exports the new API — the codex template is stale
2. **All 5 sampled services violate external import standard** — use nested import paths:
  - `from unified_config_interface.core.config import UnifiedCloudConfig` (instruments, strategy, MTDH, MDPS, features)
  - `from unified_events_interface.core.events import log_event, setup_events` (instruments-service)
  - Should be: `from unified_config_interface import UnifiedCloudConfig`
  - The cursor rule `.cursor/rules/external-import-standards.mdc` mandates top-level imports
3. **Event count ambiguity** — cursor rule says "12 lifecycle events required" but codex says batch=11, live=12

### Category 4: Missing/Duplicate SSOTs

- `**06-coding-standards/external-import-standards.md`** — referenced by cursor rule but does not exist
- `**05-infrastructure/quickmerge-architecture.md`** — SSOT for CI/CD but does not exist
- **Duplicate GCS naming** — both `deployment-v3/docs/GCS_AND_SCHEMA.md` and `unified-trading-codex/02-data/bucket-naming-and-config.md` cover bucket naming
- **Duplicate config SSOT** — index points to `persistence.py` (implementation) but `06-coding-standards/configuration.md` is the doc-level SSOT

---

## Fix Tasks

### Task 1: Fix `00-SSOT-INDEX.md` paths + counts

File: `[unified-trading-codex/00-SSOT-INDEX.md](unified-trading-codex/00-SSOT-INDEX.md)`

- Fix 4 `docs/` → `specs/` path corrections
- Fix venue count from 22 → 25 (or note 22 = MVP-committed, 3 DEFI post-MVP)
- Fix service count from 14 → 15 (or note `corporate-actions` is ops-mode of instruments)
- Fix repo count from 35 → 38
- Fix API contracts from 18 → 14
- Remove duplicate `quickmerge-architecture.md` entry
- Replace `unified-trading-pm/` paths with `unified-trading-codex/11-project-management/` OR note PM yaml files must be created
- Update `quickmerge-architecture.md` reference to existing doc (either create it or point to `05-infrastructure/ci-cd.md`)
- Clarify the GCS naming SSOT hierarchy (deployment-v3 = bucket definitions, codex 02-data = naming conventions)

### Task 2: Fix `03-observability/lifecycle-events.md` (P0 codex conflict)

File: `[unified-trading-codex/03-observability/lifecycle-events.md](unified-trading-codex/03-observability/lifecycle-events.md)`

- Replace all occurrences of `from unified_cloud_services import setup_cloud_logging` with `from unified_events_interface import setup_events`
- Replace all occurrences of `from unified_cloud_services.observability import log_event` with `from unified_events_interface import log_event`
- Update the code template block to use `setup_events(service_name=..., mode="batch|live")` instead of `setup_cloud_logging(...)`
- Fix the event count: clarify batch=11, live=12 (cursor rule says "12" without qualification — align both)

### Task 3: Create `06-coding-standards/external-import-standards.md`

File to create: `[unified-trading-codex/06-coding-standards/external-import-standards.md](unified-trading-codex/06-coding-standards/external-import-standards.md)`

- Document the top-level import rule
- Show correct patterns vs anti-patterns
- Reference the cursor rule `.cursor/rules/external-import-standards.mdc`
- This resolves the stale reference in the cursor rule

### Task 4: Create `05-infrastructure/quickmerge-architecture.md`

File to create: `[unified-trading-codex/05-infrastructure/quickmerge-architecture.md](unified-trading-codex/05-infrastructure/quickmerge-architecture.md)`

- Consolidate content from `.cursor/rules/always-use-quickmerge.mdc`, `.cursor/plans/code_optimizations_and_ci_cd_alignment/00-MASTER-CICD-PLAN.md`
- Document pipeline stages, `--dep-branch` flag, Act simulation, PR creation
- This fixes the broken SSOT reference (the file is cited by 2 entries in SSOT index and by cursor rules)

### Task 5: Fix nested imports across all services (multi-repo)

Using parallel agents across services to fix:

- `from unified_config_interface.core.config import UnifiedCloudConfig` → `from unified_config_interface import UnifiedCloudConfig`
- `from unified_events_interface.core.events import log_event, setup_events` → `from unified_events_interface import log_event, setup_events`
- Affects: instruments-service, strategy-service, market-tick-data-handler, market-data-processing-service, features-delta-one-service (plus any others in the full 14-service set)
- Each service uses quickmerge to commit

### Task 6: Resolve PM yaml file gap

Either:

- Option A: Create `mvp-universe.yaml`, `service-registry.yaml`, `venue-support-matrix.yaml` in the unified-trading-pm repo (likely empty)
- Option B: Update SSOT index to point to `unified-trading-codex/11-project-management/` where the actual content lives

Recommendation: **Option B** (less risky) — the codex 11-pm directory already has the content; just fix the SSOT pointer.

---

## Execution Order

1. Tasks 1, 2, 3, 4 can run in **parallel** (all codex, no service changes)
2. Task 5 runs after Task 1 is done (imports across 14 services — parallel agents per service)
3. Task 6 runs last (depends on what's found in codex 11-pm)

## Files Not Changing

- `deployment-v3/docs/GCS_AND_SCHEMA.md` — keep as deployment-level SSOT
- `02-data/bucket-naming-and-config.md` — keep but clarify it's naming conventions (note both exist with different scopes)
- `persistence.py` — keep as SSOT for ConfigStore implementation (it's correct)
- All cursor rules — mostly accurate, only event-logging count needs 1-line clarification
