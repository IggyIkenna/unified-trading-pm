---
type: plan
companion_handover: shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
locked_by: live-defi-rollout
locked_since: 2026-05-06
status: phase-0-audit-in-progress
owner: harsh
auditor: claude
---

# Shard-Granularity SSOT Propagation — Plan

**Branch:** `live-defi-rollout` **Status:** Phase 0 audit in progress (started 2026-05-06).
**Companion handover:** `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`

---

## Context

Most of the v5 manifest + shard-granularity work already shipped across prior plans. **This plan is a redo-and-test
verification pass to confirm end-to-end consistency, not greenfield.** Goal: every shard atom is identical across
(a) writer atomicity, (b) manifest row key, (c) data-status display, (d) downstream pre-flight gate, (e) deployment-UI
drill-down. Drift between any two = silent correctness bug.

Triggering incidents (see handover for detail):

- TradFi MVP partial bundles (ES.OPT 18/839 historical bundles passed manifest as captured)
- MDPS empty-placeholder bars (1440 NaN OHLC bars/day/venue for years)
- Databento per-schema silent drop on 429

Co-evolving streams (do NOT duplicate — handover Items 1/2/3):

1. Cluster-aware bundle validation (lands in UTL `ManifestWriter.record_captured`)
2. Databento 429 silent-drop fix (MTDS `databento_adapter.download_batch_df`)
3. VIX forward-poll wiring (`umi_tick_provider.py`)

**Coordination rule:** if audit findings overlap Items 1 or 2, comment in this plan + continue auditing — don't ship a
parallel fix.

---

## Phase 0 — Per-Service Audit (in progress)

Audit only. No code changes in this phase. Findings appended to `## Audit Findings` below as each service completes.
Format per service:

- ✓ items that match target shape
- ❌ items that don't match (writer / pre-flight / available_at / write-gate / migration / UI)
- 🔀 items implemented in the wrong layer
- ❓ items where verification needs codex pointer or clarification

### Audit DAG

```
Phase 0.1 (sequential, anchors row-key shape)
    └── instruments-service

Phase 0.2 (parallel after 0.1 establishes baseline)
    ├── market-tick-data-service (MTDS)
    ├── market-data-processing-service (MDPS)
    └── features-onchain-service / features-sports-service / features-delta-one-service

Phase 0.3 (synthesis)
    ├── Consolidated migration list (manifest drift instances + estimated shape)
    ├── Consolidated UTL-lift list (utilities currently duplicated per-service)
    └── Prediction canonical-question-group SSOT check in UAC
```

### Phase 0 Todos

- [ ] [AUDIT] P0. instruments-service — writer / pre-flight / available_at / write-gates / dual-vocab probe / per-instrument
      progress events
- [ ] [AUDIT] P0. market-tick-data-service — same checklist + scan every adapter for `except: continue` swallowing
      per-schema/per-instrument failures (skip databento_adapter.py — being fixed in parallel)
- [ ] [AUDIT] P0. market-data-processing-service — same + reader-vs-writer drift (1440-empty-bars incident pattern)
- [ ] [AUDIT] P0. features-onchain-service — same + LookaheadBiasError coverage + DAG-input pre-flight granularity
- [ ] [AUDIT] P0. features-sports-service — same + sports temporal availability stamping rules (lineups / injuries /
      pre-match odds / post-match / weather)
- [ ] [AUDIT] P0. features-delta-one-service — same + LookaheadBiasError coverage
- [ ] [AUDIT] P0. UAC prediction canonical-question-group SSOT — verify mapping raw Polymarket market_id →
      canonical question group exists; flag as build item if missing
- [ ] [AUDIT] P0. Consolidated migration list — manifest drift instances per service + estimated migration shape
- [ ] [AUDIT] P0. Consolidated UTL-lift list — cross-service utilities currently inlined per-service

### QG between phases

- [ ] Phase 0 → Phase 1: handover sign-off on audit findings; user converts findings into per-service fix todos in
      Phase 1 below.

---

## Phase 1 — Per-Service Fixes (TBD pending audit)

Phased fix work derived from Phase 0 findings. Each fix is tagged with placement layer (`[UAC]`, `[UTL]`,
`[per-service]`, `[deployment-api]`, `[deployment-ui]`). Items overlapping co-evolving Items 1/2 stay in the parallel
stream — not added here.

_To be populated after audit completes. Owner: harsh routes findings into ordered fix DAG._

---

## Phase 2 — Validation (TBD)

- [ ] All affected downstream consumers updated in this plan (no "fix later")
- [ ] Manifest reads + writes use same shard key for every (service, data_type)
- [ ] Data-status surfaces match writer granularity (audit report only — UI fix tracked separately)
- [ ] No fallback paths remain for migrated manifests
- [ ] Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud
- [ ] `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
      `available_at > kickoff - 24h`
- [ ] QG green per repo touched

---

## Audit Findings

_Findings appended per service as audit progresses. Each section follows the ✓ / ❌ / 🔀 / ❓ structure._

<!-- AUDIT_FINDINGS_INSERT_BELOW -->
