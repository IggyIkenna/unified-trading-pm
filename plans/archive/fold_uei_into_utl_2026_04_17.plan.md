---
doc_type: plan
title: fold-uei-into-utl
summary: Consolidate unified-trading-library into unified_trading_library.events (new sub-package name, aggregate of both
  divergent packages), migrate all consumers off the old paths, archive the UEI repo.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-service, e2e-testing]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-17'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-library, code: C5, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: execution-service, code: C0, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C0, deployment: none, business: none}
- {repo: alerting-service, code: C0, deployment: none, business: none}
- {repo: batch-live-reconciliation-service, code: C0, deployment: none, business: none}
- {repo: client-reporting-api, code: C0, deployment: none, business: none}
- {repo: deployment-api, code: C0, deployment: none, business: none}
- {repo: deployment-service, code: C0, deployment: none, business: none}
- {repo: e2e-testing, code: C0, deployment: none, business: none}
- {repo: features-calendar-service, code: C0, deployment: none, business: none}
- {repo: features-commodity-service, code: C0, deployment: none, business: none}
- {repo: features-cross-instrument-service, code: C0, deployment: none, business: none}
- {repo: features-delta-one-service, code: C0, deployment: none, business: none}
- {repo: features-multi-timeframe-service, code: C0, deployment: none, business: none}
- {repo: features-onchain-service, code: C0, deployment: none, business: none}
- {repo: features-sports-service, code: C0, deployment: none, business: none}
- {repo: features-volatility-service, code: C0, deployment: none, business: none}
- {repo: ibkr-gateway-infra, code: C0, deployment: none, business: none}
- {repo: instruments-service, code: C0, deployment: none, business: none}
- {repo: market-data-processing-service, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: ml-inference-service, code: C0, deployment: none, business: none}
- {repo: ml-training-service, code: C0, deployment: none, business: none}
- {repo: pnl-attribution-service, code: C0, deployment: none, business: none}
- {repo: risk-and-exposure-service, code: C0, deployment: none, business: none}
- {repo: strategy-service, code: C0, deployment: none, business: none}
- {repo: system-integration-tests, code: C0, deployment: none, business: none}
- {repo: trading-agent-service, code: C0, deployment: none, business: none}
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-trading-api, code: C0, deployment: none, business: none}
- {repo: unified-trading-pm, code: C0, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: phase-1-aggregate-schemas, content: "- [x] [HUMAN+AGENT] P0. **Phase 1 / SEQUENTIAL** — In `unified-trading-library`, create new sub-package `unified_trading_library/events/` with aggregated content. **DONE** (commit `4da72fc0`). Split into `schemas.py` (dataclasses + base sets + MiFID compliance) and `event_types.py` (domain event constants + STANDARD_LIFECYCLE_EVENTS augmentation) because single 987-line schemas.py hit the 900-line QG limit.\n  - Create `events/__init__.py`, `events/schemas.py`, `events/sink.py`.\n  - `schemas.py` = UNION of both divergent schemas. Must include:\n    - From UEI: `AUTO_DELEVERAGE_TRIGGERED`, `AUTONOMOUS_RECOVERY_EVENT_TYPES`, `CEX_INTERNAL_TRANSFER_COMPLETED`, `CIRCUIT_BREAKER_OPEN`, `DUAL_FAILURE_DETECTED`, `POSITION_DRIFT_DETECTED`, `POSITION_DRIFT_EVENT_TYPES`, `RECON_DEGRADED_CLOSE`, `TRANSFER_INITIATED`, `TRANSFER_LIFECYCLE_EVENT_TYPES`, `TREASURY_REBALANCE_NEEDED`, `VENUE_CASCADE_DETECTED`.\n    - From UTL mirror: `BALANCE_DISCREPANCY_DETECTED`,\
    \ `BALANCE_RECONCILIATION_COMPLETED`, `BRIDGE_COMPLETED`, `BRIDGE_FAILED`, `BRIDGE_INITIATED`, `DEFI_POSITION_LIQUIDATED`, `DEFI_TX_SIMULATION_FAILED`, `DEVIATION_AUTO_RECONCILED`, `DEVIATION_CONFIRMED`, `DEVIATION_ESCALATED`, `ETH_BALANCE_DEBT`, `FILL_COMPLETED`, `GAS_FEE_DATA_STALE`, `PNL_RECONCILIATION_COMPLETED`, `RECONCILIATION_EVENT_TYPES`, `STRATEGY_POSITION_UPDATED`, `TRANSFER_EVENT_TYPES`, `TRANSFER_RECONCILIATION_MISMATCH`, `TRANSFER_SUBMITTED`.\n  - `__init__.py` `__all__` must export union of both. Resolve name collisions with a single canonical definition; no duplicates.\n  - `sink.py` — take the newer formatting from UTL mirror.\n  - Verify via `diff -u` that no event constant present in either original file is missing from the aggregate.\n", status: done, note: Committed in 4da72fc0. Split into schemas.py + event_types.py.}
- {id: phase-1-port-tests, content: "- [x] [AGENT] P0. **Phase 1 / SEQUENTIAL** — Port UEI tests into UTL under `tests/events/`. **DONE** (commit `4da72fc0`).\n  - Source: `unified-trading-library/tests/` (whatever exists).\n  - Merge with existing `unified-trading-library/tests/events_interface/` (preserve the reconciliation + freshness + cicd-agent-error tests).\n  - Rename imports in ported tests from `unified_trading_library.events` → `unified_trading_library.events`.\n  - Final location: `unified-trading-library/tests/events/`.\n", status: done, note: tests/events/ ported with all imports rewritten to new path.}
- {id: phase-1-wire-top-level-exports, content: "- [x] [AGENT] P0. **Phase 1 / SEQUENTIAL** — Update `unified_trading_library/__init__.py` to re-export from new path. **DONE** (commit `4da72fc0`).\n  - Replace all `from unified_trading_library.events_interface import ...` with `from unified_trading_library.events import ...` (currently 4 blocks at lines ~143, 297, 300, 303).\n  - Add any new event type exports that exist in the aggregate but weren't previously surfaced at the top level (audit after schema merge).\n", status: done, note: 'Top-level re-export surface expanded with all new constants (AUTONOMOUS_RECOVERY_*, TRANSFER_LIFECYCLE_*, POSITION_DRIFT_*, BRIDGE_*, etc.). Plus 19 internal UTL source files rewritten.'}
- {id: phase-1-fix-dependency-check, content: '- [x] [AGENT] P0. **Phase 1 / SEQUENTIAL** — Fix UTL `dependency_check.py` line 229: replace `from unified_trading_library.events import log_event` with `from unified_trading_library.events import log_event`. **DONE** (commit `4da72fc0`).

    ', status: done, note: Line 229 updated.}
- {id: phase-1-qg-utl, content: '- [x] [SCRIPT] P0. **Phase 1 QG / SEQUENTIAL** — `cd unified-trading-library && bash scripts/quality-gates.sh`. **DONE** — passed in 61s on first clean run (17s on re-run post-split). UTL quickmerged as `4da72fc0` to `live-defi-rollout` (PR #222). Deviated from plan''s "do not quickmerge yet" because (a) consumers pull UTL from git not local editable install, so UTL must be published before consumer QGs, and (b) the old `events_interface/` sub-package is retained in parallel, so no migration break window exists.

    ', status: todo, note: ''}
- {id: phase-2a-migrate-execution-service, content: "- [ ] [AGENT] P0. **Phase 2 / PARALLEL with phase-2b…phase-2ad** — `execution-service`: replace `from unified_trading_library.events import` → `from unified_trading_library.events import` across 9 source files.\n  - Files: [execution-service/execution_service/engine/pnl_monitor.py](execution-service/execution_service/engine/pnl_monitor.py), [engine/venue_failover.py](execution-service/execution_service/engine/venue_failover.py), [engine/order_priority.py](execution-service/execution_service/engine/order_priority.py), [engine/transfers/confirmation_poller.py](execution-service/execution_service/engine/transfers/confirmation_poller.py), [engine/orphan_monitor.py](execution-service/execution_service/engine/orphan_monitor.py), [engine/recon_gate.py](execution-service/execution_service/engine/recon_gate.py), [engine/venue_cascade_monitor.py](execution-service/execution_service/engine/venue_cascade_monitor.py), [engine/handlers/transfer_handler.py](execution-service/execution_service/engine/handlers/transfer_handler.py),\
    \ [tests/conftest.py](execution-service/tests/conftest.py).\n  - Also remove `unified-trading-library` from `pyproject.toml` if pinned there.\n  - Replace `unified_trading_library.events_interface` → `unified_trading_library.events` across the 37 files that use the UTL mirror path.\n  - Run `cd execution-service && bash scripts/quality-gates.sh`. Must pass.\n", status: todo, note: ''}
- {id: phase-2b-migrate-position-balance, content: "- [ ] [AGENT] P0. **Phase 2 / PARALLEL** — `position-balance-monitor-service`: replace `from unified_trading_library.events import` → `from unified_trading_library.events import` across 3 source files.\n  - Files: [position_balance_monitor_service/core/position_drift_monitor.py](position-balance-monitor-service/position_balance_monitor_service/core/position_drift_monitor.py), [core/dual_failure_detector.py](position-balance-monitor-service/position_balance_monitor_service/core/dual_failure_detector.py), [core/treasury_monitor.py](position-balance-monitor-service/position_balance_monitor_service/core/treasury_monitor.py).\n  - Also migrate `unified_trading_library.events_interface` → `unified_trading_library.events` in the 6 files that use mirror path.\n  - Remove `unified-trading-library` from `pyproject.toml` if pinned.\n  - QG pass.\n", status: todo, note: ''}
- {id: phase-2-migrate-mirror-consumers, content: "- [ ] [SCRIPT] P0. **Phase 2 / PARALLEL** — Bulk rename `unified_trading_library.events_interface` → `unified_trading_library.events` across remaining 28 repos using UTL mirror path. QG each.\n  - Repos: alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api, deployment-service, e2e-testing, features-calendar-service, features-commodity-service, features-cross-instrument-service, features-delta-one-service, features-multi-timeframe-service, features-onchain-service, features-sports-service, features-volatility-service, ibkr-gateway-infra, instruments-service, market-data-processing-service, market-tick-data-service, ml-inference-service, ml-training-service, pnl-attribution-service, risk-and-exposure-service, strategy-service, system-integration-tests, trading-agent-service, unified-api-contracts, unified-trading-api, unified-trading-system-ui.\n  - Tool: per-repo sed/ast rewrite OR parallel Agent tool\
    \ sub-agents (one per repo).\n  - Per-repo QG after rewrite; no repo proceeds until its QG passes.\n  - Quickmerge each repo with `bash scripts/quickmerge.sh \"refactor: unified_trading_library.events → unified_trading_library.events\" --agent`.\n", status: todo, note: ''}
- {id: phase-3-delete-old-utl-mirror, content: "- [ ] [AGENT] P0. **Phase 3 / SEQUENTIAL** — Delete old `unified_trading_library/events_interface/` sub-package (directory + __init__.py + schemas.py + sink.py + tests/events_interface/ if anything remained).\n  - Verify nothing imports from `unified_trading_library.events_interface` anywhere in workspace before deletion: `grep -r \"unified_trading_library.events_interface\" --include=\"*.py\" --exclude-dir=\".venv*\"` must return zero hits outside archive/.\n  - QG UTL.\n", status: todo, note: ''}
- {id: phase-3-delete-uei-imports, content: "- [ ] [AGENT] P0. **Phase 3 / SEQUENTIAL** — Verify no `unified_trading_library.events` imports remain in workspace source.\n  - Command: `grep -r \"unified_trading_library.events\\b\" --include=\"*.py\" --exclude-dir=\".venv*\" --exclude-dir=\"archive\"` must return zero hits.\n  - If any remain, fix them in the owning repo, re-QG, then proceed.\n", status: todo, note: ''}
- {id: phase-4-update-qg-templates, content: "- [ ] [HUMAN+AGENT] P0. **Phase 4 / PARALLEL with phase-4b** — Update QG templates that reference UEI.\n  - Canonical template: [unified-trading-pm/codex/06-coding-standards/quality-gates-service-template.sh](unified-trading-pm/codex/06-coding-standards/quality-gates-service-template.sh).\n  - UI mirror: [unified-trading-system-ui/context/codex/06-coding-standards/quality-gates-service-template.sh](unified-trading-system-ui/context/codex/06-coding-standards/quality-gates-service-template.sh).\n  - `base-service.sh` if it hard-codes UEI checks.\n  - Per-repo `scripts/quality-gates.sh` copies across 15 service repos (rollout via `bash unified-trading-pm/scripts/propagation/` or per-repo edit — pick whichever is SSOT).\n  - Other shell scripts: [deployment-service/scripts/setup-cloud-build-triggers.sh](deployment-service/scripts/setup-cloud-build-triggers.sh), [deployment-service/scripts/run-all-quality-gates.sh](deployment-service/scripts/run-all-quality-gates.sh),\
    \ [unified-trading-pm/scripts/workspace/setup-dev-environment.sh](unified-trading-pm/scripts/workspace/setup-dev-environment.sh), [unified-trading-pm/scripts/agents/run-parallel-agents.sh](unified-trading-pm/scripts/agents/run-parallel-agents.sh), [unified-trading-pm/plans/tasks/claude-code/orchestrator-*.sh](unified-trading-pm/plans/tasks/claude-code/).\n  - Action per script: remove any UEI-specific enforcement; replace path refs `unified_trading_library.events` → `unified_trading_library.events`; remove `unified-trading-library` from any repo allowlists.\n", status: todo, note: ''}
- {id: phase-4-update-docs-rules, content: "- [ ] [HUMAN+AGENT] P0. **Phase 4 / PARALLEL with phase-4a** — Update docs, rules, and codex for 256 markdown/mdc references.\n  - [.claude/CLAUDE.md](../../../.claude/CLAUDE.md): replace rule `from unified_trading_library.events import setup_events, log_event — no fallbacks` with `from unified_trading_library.events import setup_events, log_event — no fallbacks`.\n  - [.cursorrules](../../.cursorrules): workspace + per-repo copies (`unified-trading-pm` canonical).\n  - `.cursor/rules/*.mdc` files — bulk rewrite `unified_trading_library.events` → `unified_trading_library.events`, `unified-trading-library` → `unified-trading-library` in narrative prose.\n  - Codex docs under `unified-trading-pm/codex/` — same rewrite.\n  - Prefer scripted rewrite (e.g., `rg --files-with-matches`, then batched `sed -i`) with a single review pass before committing.\n", status: todo, note: ''}
- {id: phase-5-archive-uei-repo, content: "- [ ] [HUMAN+AGENT] P0. **Phase 5 / SEQUENTIAL** — Archive UEI repo.\n  - `mv unified-trading-library/ archive/unified-trading-library/` (workspace root).\n  - Update [unified-trading-pm/workspace-manifest.json](unified-trading-pm/workspace-manifest.json) — remove all 9+ `unified-trading-library` entries (top-level repo map at line 90, cluster refs at lines 424/1320/1667/1870/1979/2130/2186, full repo def at line 1819).\n  - Update workspace code-workspace files (`.cursor/workspace-configs/*.code-workspace`) to drop the UEI folder entry.\n  - GitHub: archive the remote repo via `gh repo archive IggyIkenna/unified-trading-library` (HUMAN step — not run by agent).\n", status: todo, note: ''}
- {id: phase-5-verify-no-dangling-refs, content: "- [ ] [SCRIPT] P0. **Phase 5 / SEQUENTIAL after archive** — Workspace-wide verification that zero live refs remain.\n  - `grep -r \"unified_trading_library.events\\b\" . --include=\"*.py\" --include=\"*.sh\" --include=\"*.yaml\" --include=\"*.yml\" --include=\"*.toml\" --include=\"*.json\" --exclude-dir=\".venv*\" --exclude-dir=\"node_modules\" --exclude-dir=\"archive\"` returns empty.\n  - `grep -r \"unified-trading-library\" . --include=\"*.md\" --include=\"*.mdc\" --include=\"*.sh\" --include=\"*.yaml\" --include=\"*.toml\" --include=\"*.json\" --exclude-dir=\".venv*\" --exclude-dir=\"node_modules\" --exclude-dir=\"archive\"` returns empty.\n  - `grep -r \"unified_trading_library.events_interface\" . --include=\"*.py\" --exclude-dir=\".venv*\" --exclude-dir=\"archive\"` returns empty.\n", status: todo, note: ''}
- {id: phase-6-workspace-qg, content: '- [ ] [SCRIPT] P0. **Phase 6 / FINAL** — Run `bash scripts/quality-gates.sh` in every repo listed in `repo_gates` above. Every repo must pass before the plan is archived. Each repo''s QG is the C4 gate; quickmerge to staging/main is C5.

    ', status: todo, note: ''}
isProject: false
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. UTL events sub-package shipped;
> UEI repo absent from workspace; CLAUDE.md has canonical import path; consumer cleanup confirmed across MTDS/FSS
> pyproject. Ready for [unlock-plan] + archive. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

## Context

### Decision

- **New sub-package name:** `unified_trading_library.events` (NOT the existing `events_interface`). This forces a
  workspace-wide import-path update, which is the whole point — old and new paths have different names, so no consumer
  can accidentally keep using the stale mirror during migration. Once Phase 2 completes, any surviving
  `events_interface` reference is an import error, not silent bit-rot.
- **Content:** aggregate (union) of UEI and the existing UTL `events_interface/` mirror. Both have drifted. Neither is a
  strict superset.
- **No backwards-compat shims.** No re-export of the old paths from the new one. Clean break per
  `.cursor/rules/no-empty-fallbacks.mdc` and Citadel planning standards §3.

### Pre-Audit Manifest (blast radius)

**Packages being merged:**

| Location                                                            | Files                                                            | Notes                                                                       |
| ------------------------------------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `unified-trading-library/unified_trading_library.events/`           | `__init__.py` (14.7KB), `schemas.py` (33.8KB), `sink.py` (1.6KB) | Has recent autonomous-recovery + transfer lifecycle + position drift events |
| `unified-trading-library/unified_trading_library/events_interface/` | `__init__.py` (15.2KB), `schemas.py` (33.7KB), `sink.py` (1.6KB) | Has recent reconciliation + DeFi + bridge + fill events                     |

**Event types ONLY in UEI (must be preserved in aggregate):** `AUTO_DELEVERAGE_TRIGGERED`,
`AUTONOMOUS_RECOVERY_EVENT_TYPES`, `CEX_INTERNAL_TRANSFER_COMPLETED`, `CIRCUIT_BREAKER_OPEN`, `DUAL_FAILURE_DETECTED`,
`POSITION_DRIFT_DETECTED`, `POSITION_DRIFT_EVENT_TYPES`, `RECON_DEGRADED_CLOSE`, `TRANSFER_INITIATED`,
`TRANSFER_LIFECYCLE_EVENT_TYPES`, `TREASURY_REBALANCE_NEEDED`, `VENUE_CASCADE_DETECTED`

**Event types ONLY in UTL mirror (must be preserved in aggregate):** `BALANCE_DISCREPANCY_DETECTED`,
`BALANCE_RECONCILIATION_COMPLETED`, `BRIDGE_COMPLETED`, `BRIDGE_FAILED`, `BRIDGE_INITIATED`, `DEFI_POSITION_LIQUIDATED`,
`DEFI_TX_SIMULATION_FAILED`, `DEVIATION_AUTO_RECONCILED`, `DEVIATION_CONFIRMED`, `DEVIATION_ESCALATED`,
`ETH_BALANCE_DEBT`, `FILL_COMPLETED`, `GAS_FEE_DATA_STALE`, `PNL_RECONCILIATION_COMPLETED`,
`RECONCILIATION_EVENT_TYPES`, `STRATEGY_POSITION_UPDATED`, `TRANSFER_EVENT_TYPES`, `TRANSFER_RECONCILIATION_MISMATCH`,
`TRANSFER_SUBMITTED`

**Consumer repos importing `unified_trading_library.events` directly (Python source only, excl. archive/tests/.venv):**

| Repo                                                     | Files |
| -------------------------------------------------------- | ----- |
| execution-service                                        | 9     |
| position-balance-monitor-service                         | 3     |
| unified-trading-library (self, in `dependency_check.py`) | 1     |

**Consumer repos importing `unified_trading_library.events_interface`:** alerting-service (4),
batch-live-reconciliation-service (4), client-reporting-api (8), deployment-api (13), deployment-service (6),
e2e-testing (1), execution-service (37), features-calendar-service (3), features-commodity-service (3),
features-cross-instrument-service (2), features-delta-one-service (2), features-multi-timeframe-service (3),
features-onchain-service (2), features-sports-service (2), features-volatility-service (3), ibkr-gateway-infra (1),
instruments-service (4), market-data-processing-service (4), market-tick-data-service (3), ml-inference-service (4),
ml-training-service (2), pnl-attribution-service (2), position-balance-monitor-service (6), risk-and-exposure-service
(7), strategy-service (7), system-integration-tests (14), trading-agent-service (3), unified-api-contracts (1),
unified-trading-api (2), unified-trading-library (40 — own source + tests), unified-trading-pm (8),
unified-trading-system-ui (1).

**Shell scripts referencing UEI (15+):** `client-reporting-api/scripts/quality-gates.sh`,
`market-data-processing-service/scripts/quality-gates.sh`, `deployment-service/scripts/quality-gates.sh`,
`deployment-service/scripts/setup-cloud-build-triggers.sh`, `deployment-service/scripts/run-all-quality-gates.sh`,
`features-delta-one-service/scripts/quality-gates.sh`,
`unified-trading-system-ui/context/codex/06-coding-standards/quality-gates-service-template.sh`,
`system-integration-tests/scripts/quality-gates.sh`, `features-commodity-service/scripts/quality-gates.sh`,
`features-cross-instrument-service/scripts/quality-gates.sh`, `ibkr-gateway-infra/scripts/quality-gates.sh`,
`features-multi-timeframe-service/scripts/quality-gates.sh`, `features-volatility-service/scripts/quality-gates.sh`,
`instruments-service/scripts/quality-gates.sh`, `strategy-service/scripts/quality-gates.sh`,
`unified-trading-pm/plans/tasks/claude-code/orchestrator-test.sh`,
`unified-trading-pm/plans/tasks/claude-code/orchestrator-simple.sh`,
`unified-trading-pm/codex/06-coding-standards/quality-gates-service-template.sh`,
`unified-trading-pm/scripts/workspace/setup-dev-environment.sh`,
`unified-trading-pm/scripts/agents/run-parallel-agents.sh`.

**Markdown/rule/codex references:** ~256 files (bulk rewrite in Phase 4).

**Workspace manifest entries to remove:** 9+ occurrences in `unified-trading-pm/workspace-manifest.json` (version pin,
repo def, cluster refs).

**CLAUDE.md rule to update:** `from unified_trading_library.events import setup_events, log_event — no fallbacks` → new
path.

### Execution DAG

```
Phase 1: UTL consolidation (SEQUENTIAL internally)
  phase-1-aggregate-schemas  →  phase-1-port-tests  →  phase-1-wire-top-level-exports
                                                    ↘  phase-1-fix-dependency-check
                                                    →  phase-1-qg-utl  ✓
          │
          ▼ (QG gate)
Phase 2: Consumer migration (PARALLEL across repos, 30 repos)
  phase-2a-execution-service  ║  phase-2b-position-balance  ║  phase-2-migrate-mirror-consumers (28 repos)
          │
          ▼ (every repo QG passes)
Phase 3: Delete old paths (SEQUENTIAL)
  phase-3-delete-old-utl-mirror  →  phase-3-delete-uei-imports  (verification sweep)
          │
          ▼
Phase 4: Docs & QG templates (PARALLEL)
  phase-4-update-qg-templates  ║  phase-4-update-docs-rules
          │
          ▼
Phase 5: Archive UEI repo (SEQUENTIAL)
  phase-5-archive-uei-repo  →  phase-5-verify-no-dangling-refs
          │
          ▼
Phase 6: Workspace-wide QG (FINAL)
  phase-6-workspace-qg  → C5 for all 32 repos
```

### Parallelisation strategy

- Phase 2 is the only heavyweight parallel stage. 30 repos can be edited concurrently via Agent sub-agents (one agent
  per repo). Each performs the same mechanical rewrite: `unified_trading_library.events` →
  `unified_trading_library.events` and `unified_trading_library.events_interface` → `unified_trading_library.events`,
  then runs its local QG. Failed QG blocks that repo only; others continue.
- Phases 1, 3, 5, 6 are sequential by construction (UTL-single-repo, deletion after proof, archive after verification,
  final QG after everything).
- Phase 4 (docs + QG templates) can be split across two agents working on disjoint files.

### Success criteria

| Phase | Pass condition                                                                                                                                                                                          |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | UTL QG clean; aggregate schemas cover every event type from both originals; top-level `__init__.py` still re-exports everything it used to.                                                             |
| 2     | Every one of the 30 consumer repos passes local QG after rewrite. No `unified_trading_library.events` or `unified_trading_library.events_interface` import remains anywhere in source (excl. archive/). |
| 3     | UTL QG clean with old mirror deleted. Workspace-wide `grep` for old paths returns empty (outside archive/).                                                                                             |
| 4     | CLAUDE.md, .cursorrules, 256 codex/rule files, 20 shell scripts all reference new path only.                                                                                                            |
| 5     | UEI repo physically moved to `archive/`, removed from `workspace-manifest.json`, remote archived. Verification greps empty.                                                                             |
| 6     | `quality-gates.sh` passes in all 32 repos. Every repo advances from C0 → C5 via quickmerge.                                                                                                             |

### Risks & mitigations

- **Aggregate schema merge conflicts** — two branches of the same file have drifted in formatting and content.
  Mitigation: do the merge once in Phase 1 with human review; automated diff verification that no constant was dropped.
- **UTL top-level `__init__.py` re-exports** — dozens of consumers rely on top-level imports
  (`from unified_trading_library import log_event`). Mitigation: keep the re-export surface stable; only the internal
  re-export path changes.
- **GHA / Cloud Build failures mid-migration** — a repo merged without a dep version bump of UTL will fail import after
  UTL's new events/ sub-package lands but before the consumer re-points. Mitigation: bump UTL version at the end of
  Phase 1, then update each consumer's UTL floor in Phase 2 alongside the import rewrite.
- **workspace-manifest.json structural drift** — the manifest is the SSOT for CI/CD. Mitigation: update in Phase 5 only
  after all consumers compile against the new path.
- **Accidental import-path collision** — chose `events/` precisely because it doesn't collide with `events_interface/` —
  migration errors surface as `ImportError`, not runtime surprises.

### SSOT references

- CLAUDE.md events rule: `from unified_trading_library.events import setup_events, log_event` — must be updated.
- Pre-1.0.0 semver: adding new event types = `feat:` = MINOR bump on UTL (currently 0.3.167). Removing an import path =
  not a public API break pre-1.0.0 (all consumers updated in-plan). Semver-agent handles bumps automatically on merge.
- Quickmerge: every repo change uses `bash scripts/quickmerge.sh "<msg>" --agent` per CLAUDE.md.
