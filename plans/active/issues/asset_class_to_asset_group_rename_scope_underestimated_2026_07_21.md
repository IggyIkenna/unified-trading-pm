---
doc_type: issue
title:
  AssetClass → AssetGroup rename is far larger and riskier than scoped — needs a dedicated plan, not a P3 mechanical
  sweep
summary: >-
  Investigating dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md's todo C ("Execute the
  AssetClass → AssetGroup rename repo-wide") found the real scope is 9+ repos (not 2), the target name collides with a
  semantically-distinct LedgerAssetClass enum, and `asset_class` is a persisted LedgerRow field name — a schema change,
  not a pure code rename. Filing this before executing anything, per findings-triage (cross-repo + possible
  data-correctness impact = notify-operator territory).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-api-contracts,
    unified-trading-system-ui,
    client-reporting-api,
    execution-service,
    greeks-service,
    instruments-service,
    strategy-service,
    unified-trading-library,
  ]
scope: [engineer]
tags: [plan-discipline, asset-class-rename, cross-repo, scope-correction]
related: [plans/active/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [dart_ui_capability_manifest_and_catalogue_formatting_gaps-003]
resolved_by:
locked_by:
depends_on: []
---

# What I found

Picked up `dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`'s todo C ("Execute the `AssetClass`
→ `AssetGroup` rename repo-wide (UAC: ~20 files; UI: ~19+15 files/identifiers)") and surveyed the actual footprint
before touching anything:

1. **Blast radius is 9+ repos, not 2.** `grep -rl 'AssetClass'` across every slot repo shows real hits (imports of
   `unified_api_contracts.AssetClass` or its ledger sibling) in `client-reporting-api` (5 files), `execution-service`
   (2), `greeks-service` (2), `instruments-service` (10), `strategy-service` (3), `unified-trading-library` (3), and
   `unified-trading-pm` (3, script/test tooling) — on top of 21 files in `unified-api-contracts` itself and 45 files in
   `unified-trading-system-ui` (the issue doc estimated ~20 and ~19+15 respectively; actual UI count alone is already 45
   for the class name, before counting the additional ~79 files with `asset_class`/`assetClass` lowercase-form
   identifiers).
2. **Two semantically distinct `AssetClass` concepts exist and only one is what "AssetGroup" means.**
   `unified_api_contracts/__init__.py:167-184` explicitly aliases the ledger one as `LedgerAssetClass` "to avoid name
   collision with the domain AssetClass (crypto/equity/fx/commodity/fixed_income)." The ledger enum's values are
   fine-grained instrument buckets (`spot_token/option/perp/lst/…`) — a different taxonomy than "asset group." The issue
   doc's todo does not disambiguate which enum it means; a blind text-sweep of `AssetClass` would rename both,
   incorrectly conflating them.
3. **`asset_class` is a persisted field name**, not just an in-memory identifier:
   `unified_api_contracts/canonical/crosscutting/ledger/_ledger_row.py:259` — `asset_class: AssetClass` on `LedgerRow`,
   a canonical structure. Renaming this field changes the row schema for whatever this gets serialized to (ledger
   writes/reads, likely disk/GCS-persisted) — this is schema-migration territory, not a pure code rename, and falls
   under the data-pipeline-correctness hard rule.
4. **No incremental path exists under this workspace's rules.** CLAUDE.md bans backward-compat shims ("delete deprecated
   code, no shims"), so a partial rename landed in `unified-api-contracts` alone would immediately break imports (and
   quality-gates) in all 7 downstream consumer repos until each one is updated in the same atomic commit set. That is a
   large, carefully-sequenced, multi-repo coordinated change — not something to force through a P3/1-hour task.

# Why it matters

The original todo (P3, est. 1h, scoped to 2 repos) massively undersells the real effort and risk. Executing it as scoped
would either (a) silently touch only 2 of 9 repos and break QG everywhere else, or (b) require an unplanned, unreviewed
multi-repo breaking change executed under a mechanical-rename mental model, risking a conflated rename of two distinct
enums and an undocumented schema change to persisted ledger data.

# Recommended decision

Do NOT execute the rename under the original P3 todo. Instead:

- Re-scope into a dedicated plan (not an issue-doc todo) with `sequential: true` phases: (1) confirm which `AssetClass`
  this is actually about (domain-level only, almost certainly — NOT `LedgerAssetClass`) with the operator/main; (2)
  rename in `unified-api-contracts` + update every one of the 7 downstream consumer repos' imports in one coordinated
  landing so nothing sits broken; (3) UI-side rename (`unified-trading-system-ui`, ~45+79 files) as a separate,
  independently-shippable phase since it has no cross-repo import dependency; (4) the codex terminology sweep (P11.1.4)
  mentioned in the parent issue doc, gated on (2)+(3).
- If `LedgerRow.asset_class` does need to move to `asset_group` too, treat that as an explicit, called-out
  schema-migration decision (with a migration/backfill plan for any persisted data), not folded silently into the
  code-identifier rename.

## Todos

- [x] ✅ [PLANNING] P2. Author a dedicated `asset_class_to_asset_group_rename` plan (sequential, cross-repo,
      `assigned_vm: planning`) per the phased approach above; supersede todo C in
      `dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md` with a pointer to the new plan. (repo:
      unified-trading-pm) — filed BLK-87fc93e4 first per the plan-destination HARD RULE (this todo's own text assumed
      `assigned_vm: planning`, but that recommendation came from this issue doc itself, not the operator — main ruled B:
      human plan, `assigned_vm: NA`, `execution_scope: local-only`, exactly because this is the risk class the
      default-to-human bias protects). Authored `plans/active/asset_class_to_asset_group_rename_2026_07_21.md` (6 todos,
      `sequential: true`, 8 repos) with a corrective finding vs. this doc's own risk read: re-traced
      `LedgerRow.asset_class`'s actual import (`_ledger_row.py` imports `AssetClass` from the LOCAL `._enums` — the
      ledger-scoped module re-exported publicly as `LedgerAssetClass` — not from `_instrument_enums`, the domain module
      this rename targets), so the persisted field does NOT need a schema migration, provided the rename stays correctly
      scoped to the domain enum only — encoded as the new plan's own Todo 1 (re-verify independently, don't inherit on
      trust). Superseded todo C in `dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md` with a
      `BLOCKED-SUPERSEDED` marker + pointer to both this doc and the new plan.

## Codex SSOTs

`codex/04-architecture/tier-and-import-architecture.md` (no service↔service deps; UAC as shared dependency),
`codex/02-data/availability-manifest-and-data-status.md` (persisted-schema-change caution).
