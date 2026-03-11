# Epic Readiness Checklists — MVP Plan

# Status: COMPLETE (2026-03-11)

## Context

The system has per-repo readiness checklists (CR/DR/BR stages in `10-audit/repos/{repo}.yaml`) and an
`mvp-universe.yaml` defining MVP scope across asset classes. However there was no concept of "epic-level readiness"
that:

- Defines which repos collectively constitute a DeFi / CeFi / TradFi / Sports epic
- Exposes per-repo asset-class-specific data availability, feature groups, ML models, and branch status
- Aggregates across repos into an epic % complete
- Is visible in the deployment UI via the codex SSOT

**MVP target**: DeFi epic to 100% complete. CeFi / TradFi / Sports epics: structure defined, repos populated, completion
not enforced.

**Business invariant**: PnL at minimum for any epic → maps to BR5 (backtest confirms positive PnL contribution) being
required for all service repos in the epic.

**Branch gate for MVP complete**: every required repo must have reached `main` with QG passed (`CR4`) and quickmerged
(`CR5`).

---

## Completion Summary

### Stream 1 — Schema: Extend per-repo YAML template ✅

- `unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml` — added `asset_class_readiness` section

### Stream 2 — Epic definitions in codex ✅

- `unified-trading-codex/11-project-management/epics/epic-schema.yaml` — schema legend
- `unified-trading-codex/11-project-management/epics/defi-epic.yaml` — 14 required repos, mvp_priority: 1
- `unified-trading-codex/11-project-management/epics/cefi-epic.yaml` — mvp_priority: 2
- `unified-trading-codex/11-project-management/epics/tradfi-epic.yaml` — mvp_priority: 3
- `unified-trading-codex/11-project-management/epics/sports-epic.yaml` — mvp_priority: 4

### Stream 3 — Populate asset_class_readiness for DeFi repos ✅

Ten per-repo YAMLs updated with `asset_class_readiness` blocks:

- unified-defi-execution-interface, features-onchain-service, unified-api-contracts
- unified-trading-library, unified-domain-client, instruments-service
- strategy-service, execution-service, pnl-attribution-service, risk-and-exposure-service
- elysium-defi-system (new stub YAML created)

### Stream 4 — Epic aggregation script ✅

- `unified-trading-pm/scripts/compute-epic-readiness.py` — reads all repo YAMLs + epic defs, writes
  `{epic_id}-status.yaml` per epic with `epic_pct`, `blocking_repos`, `completed_repos`

### Stream 5 — Deployment API `/api/epics` endpoint ✅

- `deployment-api/deployment_api/routes/epics.py` — GET /api/epics + GET /api/epics/{epic_id}
- `deployment-api/deployment_api/utils/service_utils.py` — `get_epics_dir()`
- `deployment-api/deployment_api/lifespan.py` — `app.state.epics_dir` init
- `deployment-api/deployment_api/main.py` — router registered at `/api/epics`

### Stream 6 — Deployment UI Epic Dashboard ✅

- `deployment-ui/src/types/index.ts` — EpicSummary, EpicDetail, EpicRepoStatus, EpicBranchStatus, EpicAssetClassData,
  EpicOptionalRepo
- `deployment-ui/src/api/client.ts` — getEpics(), getEpicDetail()
- `deployment-ui/src/hooks/useEpics.ts` — useEpics(), useEpicDetail()
- `deployment-ui/src/components/EpicReadinessView.tsx` — 4 epic cards, radial progress, expandable repo table
- `deployment-ui/src/App.tsx` — "Epics" tab added to the no-service-selected Overview/Epics switcher

### SSOT Registration ✅

- `unified-trading-codex/00-SSOT-INDEX.md` — 3 new entries registered
