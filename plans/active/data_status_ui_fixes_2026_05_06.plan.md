---
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-06
owner: harsh
last_updated: 2026-05-06
---

# Data-status UI fixes — MTDS/MDPS rendering + Deploy page CLI preview

## Context

Two distinct user-facing problems flagged by Harsh on 2026-05-06:

1. **MTDS and MDPS data-status pages are broken** — UI renders garbled data (data_types labeled as venues, missing-date
   drilldowns empty, /turbo hangs >90s on 1-day windows). The `instruments-service` view works fine; user wants
   MTDS/MDPS to be at least functional, not redesigned.
2. **Deploy page CLI preview is fictional** — emits `python -m unified_trading_deployment.cli deploy` but that package
   never existed. User has been hand-running shell launchers under `deployment-service/scripts/vm/launch-*.sh` as
   workaround.

Two parallel audits ran 2026-05-06 (`a57c557062bccab29` + `ab0742176b5f5347d`). Findings below. This doc tracks the
surgical fix plan.

## Findings — MTDS/MDPS UI audit

Both pages render through `deployment-ui/src/components/DataStatusTab.tsx` (5,788 lines) branched on `serviceName`.
instruments-service / MTDS / MDPS all live in `MANIFEST_MODE_SERVICES` (`client.ts:1268`) and hit
`/api/data-status/manifest`. The render tree at lines 4095-4772 walks
`asset_groups → venues → data_types → instrument_types`.

7 problems found, ranked by user impact:

| #   | Severity | File                                                  | Bug                                                                                                                                                                                                                                                                                   |
| --- | -------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | HIGH     | `deployment-api/.../data_status_service.py:4431-4545` | MDPS `_maybe_group_by_data_type` regroups manifest rows (with `venue=""`) by data_type but stuffs result back into `venues_dict` **without flipping `breakdown_axis` to `"data_type"`**. UI labels data_types as venues — drilldowns empty, schema links broken. Single backend line. |
| 2   | HIGH     | `DataStatusTab.tsx:4717-4760`                         | Click-on-missing-date passes `venue=name, data_type=dtName` — for MDPS `name` is actually a data_type. Needs branch on `breakdown_axis`.                                                                                                                                              |
| 3   | HIGH     | `client.ts:1256,1271`                                 | MDPS appears in BOTH `TURBO_MODE_SERVICES` and `MANIFEST_MODE_SERVICES`; turbo path hangs >90s on 1-day window. Remove from turbo list.                                                                                                                                               |
| 4   | HIGH     | `DataStatusTab.tsx:1306-1358`                         | "Deploy Missing" forwards ticked rows as `venues` even when they're data_types. Branch on axis.                                                                                                                                                                                       |
| 5   | MEDIUM   | `DataStatusTab.tsx:4255-4284`                         | Schema-link builds modal with `venue=name` for MDPS rows — `name` is a data_type. Same fix shape as #2.                                                                                                                                                                               |
| 6   | MEDIUM   | `DataStatusTab.tsx:4581-4656`                         | MTDS `instrument_types → data_types` block shows completion bars but **no expandable missing-date list** (the level user actually needs). Backend gap: `TurboInstrumentTypeStatus.data_types` lacks `dates_found_list` / `missing_dates`.                                             |
| 7   | LOW      | various                                               | `category` vocabulary leak (cosmetic; CLAUDE.md asset-group SSOT).                                                                                                                                                                                                                    |

## Findings — Deploy page CLI preview audit

`unified_trading_deployment` package **does not exist** anywhere in the workspace (zero find/grep results). The real CLI
is `python -m deployment_service` with subcommands
`calculate / deploy-missing / live / cluster / batch / schedule / data-status / info / list-services / venues / sports-trigger`.
**No `deploy` subcommand exists.**

The deploy POST itself works — it routes:

```
deployment-ui POST /api/deployments
  → deployment-api/routes/deployments.py:332 create_deployment
    → deployment_manager.create_deployment(...)
      → HTTP POST to ${DEPLOYMENT_SERVICE_URL} (default http://localhost:9000)
        → deployment-service/api/routes/state.py:165
          → DeploymentOrchestrator → invokes launch-*.sh
```

The fictional CLI string is purely cosmetic (`cli_command` field returned to UI). Three files reference fake
invocations:

| #   | File                                                                    | Fictional string                                  |
| --- | ----------------------------------------------------------------------- | ------------------------------------------------- |
| 1   | `deployment-ui/src/components/CLIPreview.tsx:87`                        | `python -m unified_trading_deployment.cli deploy` |
| 2   | `deployment-api/.../deployment_manager.py:253-290` `_build_cli_command` | `python -m deployment deploy`                     |
| 3   | (consumers of the cosmetic field)                                       | inherit whichever string                          |

**Caveat**: the deploy form's actual POST still requires `deployment-service` running on port 9000. If user has been
manually running launcher scripts, the HTTP daemon may not be running. Verify before declaring "deploy works".

## Phased fix plan

### Phase 1 — Backend MDPS fix + UI turbo bypass (HIGH-impact, smallest blast radius)

- [ ] [DEPLOY-API] Flip `breakdown_axis` to `"data_type"` and move grouped dict from `venues_dict` to `data_types` when
      `_maybe_group_by_data_type` fallback fires for MDPS. File:
      `deployment-api/deployment_api/services/data_status_service.py:4431-4545`. Result: MDPS renders structurally
      identical to SPORTS (which already works). UI branching at `data-status-helpers.ts:21-29` already handles this
      discriminator correctly — no UI change needed for MDPS to start displaying real data.

- [ ] [UI] Remove `"market-data-processing-service"` from `TURBO_MODE_SERVICES` list at
      `deployment-ui/src/api/client.ts:1271`. MDPS is already in `MANIFEST_MODE_SERVICES` (`:1268`) so the manifest path
      is the right one; the turbo entry causes 90s hangs.

- [ ] Manual smoke: open UI MDPS tab → asset_group=CEFI → check page renders structured data_type list (book_snapshot_5,
      ohlcv_1m, etc.) with completion bars per asset_group.

**Phase 1 success criteria:** MDPS data-status tab renders something readable for at least CEFI and DEFI asset_groups
within ~5s. No regression on instruments-service or SPORTS view.

### Phase 2 — UI axis-aware drilldowns (deferred unless user requests)

- [ ] [UI] Branch click-handlers in `DataStatusTab.tsx:4717-4760` on `breakdown_axis` so MDPS drilldowns pass
      `data_type=name` instead of `venue=name`.
- [ ] [UI] Branch "Deploy Missing" forwarding in `DataStatusTab.tsx:1306-1358` on `breakdown_axis` so ticked rows go to
      `data_types[]` not `venues[]` for MDPS.
- [ ] [UI] Same branch fix for schema-link modal at `DataStatusTab.tsx:4255-4284`.

### Phase 3 — Deploy page CLI preview (deferred unless user requests)

- [ ] [UI] Rewrite `buildCLICommand` in `CLIPreview.tsx:87` to emit a real invocation. The best analogue for "show me
      what would run" is `python -m deployment_service calculate` (sharding preview) or surface the actual launcher
      path.
- [ ] [DEPLOY-API] Fix `_build_cli_command` in `deployment_manager.py:253-290` to return the same honest string.
- [ ] Verify: with deployment-service running on port 9000, clicking Deploy actually enqueues a VM launch via the
      existing HTTP path.

### Phase 4 — Deferred (out of scope today)

- Fix #6 (MTDS `instrument_types` missing-date drilldown) — requires backend change to populate `dates_found_list` on
  `TurboInstrumentTypeStatus.data_types`. Larger surface.
- Fix #7 (category → asset_group vocabulary) — cosmetic.

## Reference files

- `deployment-ui/src/components/DataStatusTab.tsx` (5,788 lines, branched on serviceName)
- `deployment-ui/src/components/DataStatusDrilldown.tsx`
- `deployment-ui/src/components/ShardDetailModal.tsx`
- `deployment-ui/src/lib/data-status-helpers.ts` (`getAssetGroupBreakdown` honours `breakdown_axis`)
- `deployment-ui/src/api/client.ts` (TURBO_MODE_SERVICES at 1256, MANIFEST_MODE_SERVICES at 1268)
- `deployment-api/deployment_api/services/data_status_service.py` (4431-4545)
- `deployment-api/deployment_api/services/deployment_manager.py` (253-290)
- `deployment-ui/src/components/CLIPreview.tsx` (line 87)

## Audit transcripts

- MTDS/MDPS UI agent: `a57c557062bccab29`
- Deploy CLI agent: `ab0742176b5f5347d`
