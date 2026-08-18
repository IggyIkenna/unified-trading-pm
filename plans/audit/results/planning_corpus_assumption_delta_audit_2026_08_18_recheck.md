---
doc_type: audit-result
title: Planning corpus assumption/delta audit — re-check after LDR code pull (2026-08-18)
summary: >-
  Follow-up to /plans/audit/results/planning_corpus_assumption_delta_audit_2026_08_17.md, triggered by new code
  landing on live-defi-rollout (the instrument_type axis, both Tuesday dump skills) — underlying DATA unchanged, so
  this pass re-verifies only the code-dependent claims/findings from the prior audit and runs the two now-shipped
  dump skills for a fresh authoritative snapshot, rather than re-doing the full audit.
status: partial
nature: record
audited_scope: >-
  Re-verification of the prior audit's code-dependent claims (archetype declaration count, DeFi connector
  reachability) and doc-level findings (venue_readiness's normalisation-rule prose, the three-way parent-epic
  conflict, the stale Nick AI "5/59" archetype figures, the epic-vs-gate-register dump-skill checkbox gap) against
  the state of the repos after the 2026-08-17/18 LDR pulls. Includes fresh live runs of the readiness-state-dump and
  honest-coverage-dump skills.
date: 2026-08-18
auditor: >-
  Interactive session (Agent 3 — assumption/delta audit, re-check pass), direct source reads + live skill runs, no
  sub-agents dispatched this pass (scope was narrow enough for direct verification).
severity: P2
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts, execution-service, instruments-service]
scope: [engineer, admin]
tags: [assumption-audit, delta-audit, measurement-claims-discipline, planning-corpus, system-readiness]
related:
  [
    /plans/audit/results/planning_corpus_assumption_delta_audit_2026_08_17.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
  ]
created: 2026-08-18
source: >-
  Operator direction 2026-08-18: "re audit because stuff came in from ldr (the code part the data is unchanged)."
context_scope:
  [
    /plans/audit/results/planning_corpus_assumption_delta_audit_2026_08_17.md,
    /cursor-configs/skills/readiness-state-dump/SKILL.md,
    /cursor-configs/skills/honest-coverage-dump/SKILL.md,
  ]
---

# Re-check after LDR code pull — 2026-08-18

> Read [`planning_corpus_assumption_delta_audit_2026_08_17.md`](/plans/audit/results/planning_corpus_assumption_delta_audit_2026_08_17.md)
> first — this doc only covers what could have moved because CODE landed. Data-derived claims from that audit
> (coverage percentages' underlying capture counts, the GCS non-canonical/`.bak` sample, the catalogue emptiness
> finding) are not re-touched here; the section below on the two dump skills explains why the code landing did not
> in fact change the coverage numbers either, despite first appearances.

## What landed (confirmed via `git log`)

- `unified-api-contracts@d19866d339` — **"land instrument_type axis on the venue coverage denominator"** (W3,
  operator ruling 2026-08-17). Re-ran `generate_venue_universe_denominator.py` fresh: the real denominator is now
  **660 (venue, instrument_type, data_type) triples** (was 353 (venue, data_type) pairs), with 12 unresolved cells
  disclosed rather than dropped, and the 8-undeclared-DeFi-venue gap unchanged.
- `unified-trading-pm@5b3dbf99bd` — **both Tuesday dump skills shipped**: `cursor-configs/skills/readiness-state-dump/`
  and `cursor-configs/skills/honest-coverage-dump/`. Both are real, run against live prod data, not scaffolding.

## Re-verified: does the axis landing actually change the coverage numbers? No — and this is itself a finding worth citing

The gate-register plan (`data_pipeline_completion_2026_08_21.md`, "Re-ran both dumps after the axis landed and
diffed against the Tuesday output," done 2026-08-18) already investigated this directly and found: **neither dump's
numbers moved because of the axis landing.** `expected_universe.py` (Layer-1's real EXPECTED-set builder) has always
read `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` directly, never `VenueCapabilityRecord` — so it was never blocked
on the axis, and the coverage.json's 3-tuple grain (3,960 shards) predates the axis commit by ~19 hours. **The axis
landing only feeds `generate_venue_universe_denominator.py`'s standalone 660-triple figure — it does not yet feed
either dump.** This matters for this audit specifically because it confirms the operator's framing ("the data part is
unchanged") is correct at a mechanism level, not just a coincidence: independently re-running the honest-coverage-dump
skill below reproduces a coverage percentage within 0.14 points of the 2026-08-17 audit's figure, which is exactly
what "same data, same effective grain" predicts.

## Fresh live snapshots (both skills run today, read-only, no data re-measurement)

**`honest-coverage-dump` (summary)**: grain `instrument_type`, 3,960 shards in scope, **reachable coverage 48.54%**
(denominator = captured + attempted_failed + expected_unattempted = 119,500,618) — consistent with the prior audit's
independently-re-derived **48.40% volume-weighted** figure (Part 1 claim 1); the ~0.14-point difference is fully
explained by the finer grain, not new data, per the mechanism finding above. Per-AG stray/hole counts (cefi 82/4,
defi 700/22, prediction 4/0, sports 755/13, tradfi 70/10) are notably **higher** on defi/sports/tradfi than the
2026-07-03 codex baseline the gate-register plan compared against (defi 128→700, sports 24→755, tradfi 52→70) — real
~6-week data drift already identified and being root-caused by that plan's own new P2 follow-up ("root-cause the
stray-tuple count growth"), not re-litigated here since it's already tracked and outside this audit's code-only scope.

**`readiness-state-dump` (summary)**: 288 venues × 3 modes = 864 rows. **Overall rollup: ready=0, not_ready=844,
unverified=20.** Per-leg breakdown shows `strategy` passes only 24/864 (consistent with the 40/60 archetype
declaration rate confirmed below — most rows fail because no declared archetype's full input set is satisfiable from
that venue, not because the check is missing) and `execution_instruction` is **100% unverified (864/864)** — a real,
now-measurable statement that the execution-instruction leg of the readiness contract has zero machine checks wired
anywhere in the fleet yet. Worth surfacing to the operator as a concrete gap the epic's Definition-of-done doesn't
currently name.

## Part 1 code-dependent claims — re-verified against current code, unchanged

| Claim | 2026-08-17 verdict | 2026-08-18 re-check | Verdict |
| --- | --- | --- | --- |
| `ARCHETYPE_FEATURE_GROUPS` declaration count | 60 total / 40 declared / 20 undeclared | Re-imported `StrategyArchetype` + `ARCHETYPE_FEATURE_GROUPS` live: **60 / 40 / 20**, identical | **UNCHANGED** |
| DeFi connector reachability | 19 of 31 unreachable (gate green) | Re-ran `check_reachability_gate.py` live: `[OK] execution-service:defi_protocols: 19 unreachable (== baseline)` | **UNCHANGED** |

## Part 2/3 findings from the prior audit — current status

| # | Finding | 2026-08-17 status | 2026-08-18 status | Evidence |
| --- | --- | --- | --- | --- |
| Ruling-propagation gap #4 | `venue_readiness_and_registry_hardening_2026_08_16.md`'s normalisation-rule prose still omits ML as a valid processed-data source (epic already self-corrected this) | GAP FOUND | **STILL OPEN** | Line 162 unchanged: "It reads through features-service or market-data-processing-service" — no ML mention. One-sentence fix, still cheap. |
| Contradiction #1 | Three-way live parent-epic ownership conflict (`system_readiness_master` claims plans whose own `parent_epic` field points elsewhere) | [OPERATOR] flagged | **STILL OPEN** | Re-checked all 4 `parent_epic:` fields directly — unchanged: `nick_ai_platform_disclosure_artifact` and `venue_readiness_and_registry_hardening` → `infrastructure_master`; both Elysium docs → `client_isolation_and_governance_master`. |
| Contradiction #3 | Nick AI pre-audit's readiness tables still cite the stale "5/59" archetype figure the real 60/40 count corrects | Flagged as highest-value finding, cheap fix | **STILL OPEN, now >24h stale** | `nick_ai_platform_disclosure_artifact_2026_08_16.md:278` and `nick_ai_platform_disclosure_pre_audit_2026_08_16.md:108,204` all still read "5 of 59" / "5/59" verbatim. The real count has been 60/40 since 2026-08-16 evening — these cells have now been wrong for over a day, and the "Build the artifact" todo is still open/unblocked. **Escalating urgency, not new** — worth a direct operator nudge given it feeds a not-yet-built client-facing document. |

## New finding this pass — epic vs. gate-register checkbox drift on the two dump skills

`data_pipeline_completion_2026_08_21.md`'s "Tuesday dumps" section already records both skills as `✅ Shipped —
unified-trading-pm@5b3dbf99bd`, with live-verification evidence for each. **`system_readiness_master.md` (the parent
epic) has not been updated to match**: W1's "Build a readiness state-dump skill" (line 156) and W20's "Readiness
state dump" / "Strategy capability audit" (lines 369-370) are all still `- [ ]` unchecked, even though the first two
are demonstrably done (the third, strategy-capability-audit, is a distinct skill not yet built — that one is
correctly still open). This is the same class of gap as the na-eligibility-audit's own "misleading pointer" rule:
cheap to fix (flip 2 of the 3 checkboxes in the epic with a citation to the child plan's evidence), and it is the
kind of drift that compounds the longer it sits, since the epic is the doc `related_plans` and dashboards are most
likely to be read from.

## Progress Log

**2026-08-18 — re-check complete.** Triggered by new code landing on live-defi-rollout (the instrument_type axis,
both Tuesday dump skills) with the operator's explicit note that underlying data is unchanged. Confirmed both
code-dependent numeric claims from the 2026-08-17 audit are unchanged (60/40/20 archetypes, 19/31 unreachable
connectors), ran both newly-shipped dump skills live for a fresh snapshot (48.54% fleet-wide reachable coverage,
consistent with the prior 48.40% figure; readiness rollup 0 ready / 844 not_ready / 20 unverified across 864
venue×mode rows), and confirmed the axis landing does not yet feed either dump (already independently discovered and
recorded by the concurrent agent in the gate-register plan). Three of the prior audit's open findings remain open and
unchanged; one new small propagation gap found (epic vs. gate-register checkbox drift on the dump skills). No todos
flipped in any doc other agents are actively working — findings recorded here only, per the same scope discipline as
the prior pass.
