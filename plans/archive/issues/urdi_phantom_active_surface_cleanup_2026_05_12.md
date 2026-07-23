---
doc_type: issue
title: URDI phantom references in active surface — cleanup sweep
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
author: ikenna-slot8
source:
  [
    cursor-configs/CLAUDE.md line 479 (FIXED this session),
    "codex/GLOSSARY.md:99-100 (correct — declares URDI ELIMINATED 2026-03-26)",
    workspace-manifest.json (no URDI repo; sports-reference-data-service merged into instruments-service 2026-03-01),
    SP-5 / SP-10 / SP-12 sub-agent confusion (operator-flagged 2026-05-12),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# URDI phantom references in active surface — cleanup sweep

> **Severity**: P1 — pre-cutover audit hygiene; not blocking May-23 but causing sub-agent confusion (operator-flagged
> 2026-05-12 during sports catalogue audit). **Owner**: governance / codex-maintainer; not slot 4 / slot 5 / slot 8
> scope per Findings Triage Discipline collision-risk rule. **Effort**: ~1-2 cal AI-days (mechanical doc fixes +
> cross-ref re-anchoring).

## What I found

**URDI (`unified-reference-data-interface`) is a phantom name** in the workspace. Facts:

1. **No repo exists** — `ls unified-reference-data-interface` returns nothing; absent from `workspace-manifest.json`
   active list.
2. **Already eliminated** — `codex/GLOSSARY.md:99-100` correctly declares:
   `URDI – unified-reference-data-interface; formerly a T1/T2 library providing reference data adapters, instrument definitions, IBKR corp actions. ELIMINATED 2026-03-26 — merged into instruments-service.`
3. **Sports reference data lives in `instruments-service`** (sports module, merged from sports-reference-data-service
   2026-03-01 per workspace-manifest notes).
4. **33 active-surface URDI references** still exist across:
   - `cursor-configs/CLAUDE.md` — line 479 key-repo-mapping ✅ **FIXED THIS SESSION** at pm@<this-commit> (corrected to
     "sports reference → `instruments-service`" + explicit phantom-name annotation).
   - `codex/GLOSSARY.md` ✅ already correct (declares ELIMINATED 2026-03-26).
   - `codex/10-audit/repos/unified-reference-data-interface.yaml` — STALE repo-readiness yaml for a non-existent repo.
   - `/codex/06-coding-standards/feature-service-pattern.md` — T1-library table lists URDI as active 🟡 STALE.
   - `/codex/06-coding-standards/service-orchestration-patterns.md` — present-tense "URDI adapters read their own URLs"
     🟡 STALE.
   - `/codex/07-security/testing-with-api-keys.md` — needs verification.
   - `codex/10-audit/REPO_READINESS_CHECKLIST.yaml` — needs verification.
   - `/codex/06-coding-standards/integration-testing-layers.md` ✅ already uses "formerly URDI" framing (correct).
   - ~25 more refs across active plans + codex docs — mostly historical-ok but mixed.

## Why it matters

**2026-05-12 incident**: sub-agent doing `catalogue_audit_sports` reported SP-5 / SP-10 / SP-12 needed a "URDI-side
worktree audit" — the agent had read the stale CLAUDE.md key-repo-mapping (`sports reference → URDI`) and looked for a
URDI worktree, didn't find one, and surfaced a gap that doesn't exist. **The audit targets are actually
`instruments-service` (sports module) + `execution-service` (sports module)** — both present in the workspace.

Sub-agents reading the workspace inherit drift from CLAUDE.md / codex when they spawn. Every URDI present-tense
reference is a tripwire for future agents.

## Recommended decision

### Phase 1 — Authoritative SSOTs (✅ done in this session)

- ✅ `cursor-configs/CLAUDE.md:479` — fixed to declare `sports reference → instruments-service` + explicit phantom-name
  annotation for URDI.
- ✅ `codex/GLOSSARY.md:99-100` — already correct (ELIMINATED 2026-03-26).

### Phase 2 — Active codex sweep (next-cycle owner; mechanical)

For each of the ~25 remaining active-surface refs:

1. **If the doc treats URDI as a LIVE library** (present tense, T-tier table entry, "URDI adapter") → rewrite to point
   at `instruments-service` (sports module) OR `execution-service` (DeFi module) per the consolidation map at
   `workspace-manifest.json` sports notes.
2. **If the doc treats URDI as HISTORICAL** ("formerly URDI", "post-collapse") → leave as-is (GLOSSARY framing is
   correct).
3. **Archive stale repo-readiness yamls** — `codex/10-audit/repos/unified-reference-data-interface.yaml` for a
   non-existent repo can be moved to `codex/10-audit/repos/archive/` with a banner.

### Phase 3 — Successor SP-5 / SP-10 / SP-12 audit dispatch (operator decision)

The original SP-5 / SP-10 / SP-12 sub-agent findings are UNVERIFIED because the agent looked at the wrong target.
Re-dispatch from a worktree that has `instruments-service` (sports module) + `execution-service` (sports module) checked
out. ~2-4 hours per the operator's brief.

Audit targets:

- (a) `classify_venue_error()` wiring in sports adapters
- (b) `ADAPTER_FETCH_FAILED` emission
- (c) typed `EMPTY_CONFIRMED_REASONS` in record_empty() calls
- (d) cluster-validation kwargs on bundle writers (sports per-fixture bundles)
- (e) capability-decl-vs-method match
- (f) shard-level failure isolation

**✅ Phase 3 SHIPPED 2026-05-12** (ikenna-sports-re-audit-sp-5-10-12 slot 8 sub-agent) — re-audit complete; verdicts in
`plans/active/issues/catalogue_audit_sports_2026_05_12.md` re-audit banner + updated SP-5 / SP-10 / SP-12 rows + new
SP-12 per-axis verdict table + new **SP-13 BIG-FINDING** (MTDS `market_interface/sports/registry.py:23-40`
`_ADAPTER_PATHS` imports 18 sportsbook adapters from the phantom `unified_sports_execution_interface.*` package — will
`ModuleNotFoundError` at runtime, silently breaking MTDS sports market-data ingestion for every one of those 18 venues).
Net verdicts: SP-5 REAL-GAP (bet365 wired wrong + DK/FD missing scrapers); SP-10 REAL-GAP (0 hits for cluster kwargs
workspace-wide); SP-12 MIXED per axis; SP-13 new P0 critical-path May-23 issue. All four folded into
`plans/epics/sports_master_2026_05_07.md`.

## Composes with

- `plans/active/codex_vs_citadel_infrastructure_audit_2026_05_10.md` Phase 1.G Instruments — folds this sweep into the
  broader audit.
- `plans/active/codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` Sweep 1 — codex-doc currency sweep
  should absorb the ~25 active codex URDI refs.
- `plans/active/cross_asset_group_catalogue_audit_2026_05_10.md` Phase 1D — sports catalogue audit (SP-5/10/12 origin).

## Resolution status

🟡 OPEN — Phase 1 ✅ shipped this session; Phase 2 (~25 active codex refs) folded into post_cutover currency sweep;
**Phase 3 ✅ shipped 2026-05-12 by ikenna-sports-re-audit-sp-5-10-12 slot 8 sub-agent — re-audit verdicts in
`plans/active/issues/catalogue_audit_sports_2026_05_12.md`; new SP-13 surfaced as P0 critical-path May-23 issue (MTDS
phantom-import-path bug); fold into sports_master_2026_05_07**.
