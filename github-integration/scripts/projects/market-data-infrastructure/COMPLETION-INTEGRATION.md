# Market Data Infrastructure - Epic Completion and Codex Integration

**Epic:** Market Data Infrastructure (Project #8)
**Purpose:** Ensure epic learnings are properly integrated into Codex after completion
**When:** After all 4 subtasks complete (100% verified)

---

## Why This Matters

This epic creates 4 new foundational libraries that ALL future services will use. Without proper Codex integration:

- ❌ Developers won't know the new libraries exist
- ❌ Old patterns will continue (importing from unified-trading-services)
- ❌ Learnings from migration won't benefit future work
- ❌ Documentation will be outdated and misleading

**Goal:** Make the new architecture the **standard** for all future work.

---

## Integration Checklist

Use this after `bash 08-verify-completion.sh` shows 100% complete.

### Phase 1: Verification (30 min)

- [ ] **Run completion script:**

  ```bash
  cd unified-trading-codex/11-project-management/github-integration/scripts/projects/market-data-infrastructure
  bash 08-verify-completion.sh --issue-manifest issue-manifest.json
  ```

  - Verify: 51/51 (100%)
  - Verify: All phases 0-4 complete

- [ ] **Verify libraries published:**

  ```bash
  gcloud artifacts packages list \
      --repository=unified-libraries \
      --location=asia-northeast1 \
      --project=test-project
  ```

  - Verify: unified-events-interface (>=1.0.0)
  - Verify: unified-config-interface (>=1.0.0)
  - Verify: unified-market-interface (>=1.0.0)
  - Verify: unified-order-interface (>=1.0.0)

- [ ] **Verify backward compatibility:**

  ```bash
  cd instruments-service
  bash scripts/quality-gates.sh --no-fix
  ```

  - Verify: All tests pass
  - Verify: No code changes needed

### Phase 2: Create New Codex Documentation (2-3 hours)

#### A. Create Library Documentation Directory

```bash
cd unified-trading-codex
mkdir -p 05-infrastructure/unified-libraries
```

- [ ] **Create `05-infrastructure/unified-libraries/README.md`**
  - Purpose of each library
  - When to use which library
  - Architecture diagram (4 libraries → unified-trading-services → cloud providers)
  - Quick start examples

- [ ] **Create `05-infrastructure/unified-libraries/events-interface.md`**
  - Observability events (Cloud Logging)
  - Coordination events (PubSub, live only)
  - Control events (killswitch, resume)
  - Code examples for each event type
  - Testing patterns

- [ ] **Create `05-infrastructure/unified-libraries/config-interface.md`**
  - get_config() usage
  - BaseConfig schema
  - Config hot-reload (PubSub-based)
  - Versioned config reads
  - Testing with mock configs

- [ ] **Create `05-infrastructure/unified-libraries/market-interface.md`**
  - MarketDataFeed interface
  - Venue-specific adapters (Binance, Deribit, etc.)
  - Canonical schemas (Trade, OrderBook)
  - Normalization layer
  - Historical vs live feeds

- [ ] **Create `05-infrastructure/unified-libraries/order-interface.md`**
  - OrderClient interface
  - Order submission, cancel, amend
  - Fill event handling
  - Venue-specific adapters
  - Order validation and risk checks

#### B. Create Migration Guide

```bash
mkdir -p 11-project-management/migration-guides
```

- [ ] **Create `11-project-management/migration-guides/unified-libraries-migration.md`**
  - Overview: Why migrate?
  - Step-by-step guide (based on instruments-service proof of concept)
  - Before/after code examples
  - Estimated effort: ~30 min per service
  - Common issues and solutions
  - Testing checklist

### Phase 3: Update Existing Codex Documentation (1-2 hours)

- [ ] **Update `05-infrastructure/cloud-agnostic-migration.md`**
  - Add section: "Unified Libraries Architecture"
  - Update dependency diagram to show 4 new libraries
  - Explain transitive dependency strategy

- [ ] **Update `06-coding-standards/README.md`**
  - Update import examples to use new libraries:

    ```python
    # Preferred (new)
    from unified_events_interface import log_event
    from unified_config_interface import get_config

    # Deprecated (still works until Aug 2026)
    from unified_trading_services import log_event, get_config
    ```

  - Add note about 6-month backward compat window

- [ ] **Update `06-coding-standards/dependency-management.md`**
  - Document transitive dependency strategy
  - Explain how services get new libraries automatically
  - Code examples from pyproject.toml

- [ ] **Update `03-observability/lifecycle-events.md`**
  - Reference unified-events-interface as source of truth
  - Update event schema links
  - Clarify observability vs coordination events

- [ ] **Update `03-observability/batch/architecture.md`**
  - Clarify: Batch uses Cloud Logging only
  - Explain: No PubSub in batch (GCS is message bus)
  - Update examples to use unified-events-interface

- [ ] **Update `03-observability/live/architecture.md`**
  - Add: PubSub for coordination events
  - Explain: Service-to-service workflow (features → ML → strategy → execution)
  - Update examples to use unified-events-interface

- [ ] **Update `04-architecture/deployment-topology-diagrams.md`**
  - Update dependency diagrams to show 4 new libraries
  - Show data flow: Services → Libraries → unified-trading-services → Cloud

- [ ] **Update `02-data/schema-governance.md`**
  - Add: Event schemas owned by unified-events-interface
  - Add: Config schemas owned by unified-config-interface
  - Add: Market schemas owned by unified-market-interface
  - Add: Order schemas owned by unified-order-interface

### Phase 4: Create Lessons Learned (1 hour)

```bash
mkdir -p 11-project-management/completed-epics/market-data-infrastructure
```

- [ ] **Create `11-project-management/completed-epics/market-data-infrastructure/lessons-learned.md`**
  - Completion date
  - Duration (3 days planned vs actual)
  - Team (Ikenna + Harsh)
  - Metrics:
    - Lines of code added
    - Test coverage per library
    - Quality gate pass rate
    - Agent automation success rate
  - What went well
  - What could improve
  - Key decisions and rationale
  - Recommendations for future epics

### Phase 5: Archive Project Files (15 min)

- [ ] **Copy epic files to completed-epics:**

  ```bash
  cd unified-trading-codex/11-project-management

  # Copy files
  cp epics/market-data-infrastructure-epic.md \
     completed-epics/market-data-infrastructure/epic.md

  cp epic-breakdowns/epic-market-data-infrastructure.md \
     completed-epics/market-data-infrastructure/epic-breakdown.md

  cp ~/.cursor/plans/infrastructure-updates-for-library-refactor.md \
     completed-epics/market-data-infrastructure/infrastructure-updates.md
  ```

- [ ] **Update epic metadata to "Complete":**
  - Status: Planning → Complete
  - Completion date: [Date]
  - Link to completed-epics location

### Phase 6: Update Service Backlogs (30 min)

For each of the 11 remaining services (not yet migrated):

- [ ] **Create migration issue in each service repo:**
  - Title: `[Migration] Update to unified-libraries (direct imports)`
  - Label: `tech-debt`, `P2-medium`, `migration`
  - Description:

    ```markdown
    ## Context

    unified-trading-services has been split into 4 libraries (Feb 2026). This service currently uses backward-compat
    re-exports.

    ## Task

    Update imports to use new libraries directly.

    ## Migration Guide

    See: unified-trading-codex/11-project-management/migration-guides/unified-libraries-migration.md

    ## Estimated Effort

    ~30 min (based on instruments-service proof of concept)

    ## Deadline

    Aug 28, 2026 (6-month backward compat window)
    ```

**Services to create issues for:**

1. execution-service
2. strategy-service
3. market-data-processing-service
4. ml-training-service
5. ml-inference-service
6. features-delta-one-service
7. features-volatility-service
8. features-calendar-service
9. features-onchain-service
10. market-tick-data-handler
11. unified-trading-deployment-v2

### Phase 7: Close GitHub Project (15 min)

- [ ] **Update GitHub Project #8 description:**
  - Mark as complete
  - Add completion date
  - Link to Codex docs:

    ```
    Completed: Mar 10, 2026

    Split unified-trading-services into 4 focused libraries:
    - unified-events-interface
    - unified-config-interface
    - unified-market-interface
    - unified-order-interface

    Documentation: unified-trading-codex/05-infrastructure/unified-libraries/
    Migration Guide: unified-trading-codex/11-project-management/migration-guides/unified-libraries-migration.md
    Lessons Learned: unified-trading-codex/11-project-management/completed-epics/market-data-infrastructure/
    ```

- [ ] **Close project but keep for reference:**
  - Status: Open → Closed
  - Keep issues linked (historical record)

### Phase 8: Team Communication (30 min)

- [ ] **Send Slack/Email announcement:**
  - Epic complete
  - New libraries available
  - Link to documentation
  - Link to migration guide
  - Migration deadline (Aug 28, 2026)
  - Estimated migration effort per service (~30 min)

- [ ] **Update team wiki/handbook:**
  - New library architecture is now standard
  - Link to Codex docs
  - Migration guide for existing services

- [ ] **Create tech talk/demo:**
  - Show new library usage
  - Demo config hot-reload
  - Demo PubSub coordination (live mode)
  - Walk through migration example

### Phase 9: Final Sign-off (15 min)

- [ ] **Ikenna: Documentation complete**
  - All new docs created
  - All existing docs updated
  - Migration guide written
  - Lessons learned documented

- [ ] **Harsh: Documentation reviewed**
  - Technical accuracy verified
  - Code examples tested
  - Migration guide validated

- [ ] **Team: Onboarded**
  - Team announcement sent
  - Documentation accessible
  - Questions answered

---

## Success Verification

**Before marking epic as complete, verify:**

1. ✅ `bash 08-verify-completion.sh` shows 100%
2. ✅ All 4 libraries published and accessible
3. ✅ 5 new Codex docs created (unified-libraries/)
4. ✅ 8 existing Codex docs updated
5. ✅ Migration guide created and reviewed
6. ✅ Lessons learned documented
7. ✅ 11 service migration issues created
8. ✅ GitHub Project #8 closed with docs links
9. ✅ Team announced and onboarded
10. ✅ Sign-off complete (Ikenna + Harsh)

**ONLY THEN:** Epic is fully integrated into Codex and becomes the standard for all future work.

---

## Estimated Time: 6-8 hours

| Phase     | Task                           | Time          |
| --------- | ------------------------------ | ------------- |
| 1         | Verification                   | 30 min        |
| 2         | Create new docs (5 files)      | 2-3 hours     |
| 3         | Update existing docs (8 files) | 1-2 hours     |
| 4         | Lessons learned                | 1 hour        |
| 5         | Archive files                  | 15 min        |
| 6         | Service backlog issues (11)    | 30 min        |
| 7         | Close project                  | 15 min        |
| 8         | Team communication             | 30 min        |
| 9         | Final sign-off                 | 15 min        |
| **Total** |                                | **6-8 hours** |

**Assign this as final task of epic** - without it, the epic is not truly complete!

---

## Questions?

- See epic breakdown: `11-project-management/epic-breakdowns/epic-market-data-infrastructure.md`
- See project scripts: `11-project-management/github-integration/scripts/projects/market-data-infrastructure/`
- Ask: @ikenna or #engineering
