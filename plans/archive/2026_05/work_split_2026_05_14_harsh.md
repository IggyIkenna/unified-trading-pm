---
doc_type: plan
title: Harsh's daily work-split — 2026-05-14 (Day-3 of density push, pre-freeze-gate close-out)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    features-service,
    instruments-service,
    strategy-service,
    unified-trading-library,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-14
type: coordination-doc
deadline: 2026-05-23 (live DeFi cutover)
horizon: 1 day (closeout for tomorrow's 2026-05-15 Phase 1 freeze gate)
companion_to: plans/active/work_split_2026_05_12_ikenna.md (Ikenna's 4-day cycle plan; Day-3 of 4)
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

# Harsh's daily work-split — 2026-05-14 (Day-3, freeze-gate eve)

> **Cycle context**: Day-3 of 4-day density-push cycle (2026-05-12 → 2026-05-15). Phase 1 freeze gate fires **tomorrow
> (2026-05-15)**. Today's scope is a mix of (a) finishing Harsh-side carry-forward debris, (b) absorbing 2 of the 4
> slots Ikenna asked us to allocate (`batch_live_symmetry` 2 slots; `defi_recursive_borrow` DESCOPED per operator), (c)
> closing the P0 orphan-assigned `api_football_phase_3b_3c` whose deadline is **TODAY EOD**.
>
> **Operator decisions baked into this split**:
>
> - `batch_live_symmetry` → **2 Harsh slots assigned** (slots 5 + 8 take Tabs 1-3 codex + UAC + QG)
> - `defi_recursive_borrow_archetypes` Solidity + execution halves → **DESCOPED**. Master plan only commits
>   `carry_staked_basis` + `arbitrage_price_dispersion` for May-23 live. Ship archetype documented + Phase 2-3 in
>   successor plan; slot 9 files the successor.
> - AWS bucket Phase 2.6 GCE VM prep → **DROPPED** (AWS migration deferred past May-23 per 2026-05-13 operator
>   direction). May-23 ships GCP-only.
> - defi 604k reclassification → Ikenna-side scope (slots 2+9 own it); no Harsh slot needed.
>
> **Density target**: ~40-60 cal AI-days side. Higher than my pre-correction draft because we've absorbed Ikenna's
> `batch_live_symmetry` ask. All 8 implementer slots used; slot 10 stays ✅ DONE idle.

---

## Cycle context

- Day-1 (2026-05-12) and Day-2 (2026-05-13) shipped clean. All 6 Harsh-side implementor slots closed ✅ DONE Wave 2/3/4
  per `harsh_orchestrator/LEDGER.md` § "2026-05-13 PM shift end — final closeout".
- **Force-push incident yesterday** (resolved): `semver-rollout[bot]` Ikenna-side bot pattern force-pushed 4× on PM + 2×
  on UAC + ≥1× on instruments-service. All Harsh-side casualties recovered. Operator flagged to Ikenna directly.
- **Ikenna audit batch PM@`e1e67656`** (2026-05-13 14:50 UTC) settled key uncertainties:
  - Cloud HSM CMK ✅ live (10 GCP CMKs, asia-northeast1, 90d rotation)
  - Copper/CEFFU → client-side, NOT our blocker
  - AWS migration → DEFERRED past 2026-05-23 (priority P0→P1, deadline 2026-05-23 → 2026-06-04)
  - 3 orphan plans assigned: **`api_football_phase_3b_3c_smoke_forward_poll_2026_05_13` to sports_master, P0, deadline
    TODAY 2026-05-14 EOD**
  - Slot reallocation ask: 2 slots `batch_live_symmetry`, 2 slots `defi_recursive_borrow` OR descope
- **Ikenna Day-3 reassignment** (informational, no Harsh action): wallet_treasury post-cutover Phase 1+3 pulled forward
  to pre-May-15; Ikenna slots 2+9 own defi 604k classifier crossref + reclassification.

---

## Today's slot assignments

**Working model**: 8 implementer slots active (Model A thematic), slot 1 main, slot 10 ✅ DONE idle. No held-in-reserve
today — full slot use to absorb `batch_live_symmetry` ask + finish carry-forward debris.

| Slot | Theme                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Plan-of-record                                                                                                                                                                                 | Cal AI-days        |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| 1    | **Main orchestrator** (continuous) — freeze-gate close monitoring, LEDGER + ping triage, work-split adjustments, decision relays                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | (this work-split + LEDGER + master plan continuous-verification column)                                                                                                                        | —                  |
| 2    | 🔴 **api_football Phase 3b/3c smoke + forward-poll** (P0, deadline TODAY EOD per Ikenna audit batch). Run the smoke harness; flip Phase 3.B/3.C checkboxes against actuals; file blocker docs if any; ensure forward-poll integration green                                                                                                                                                                                                                                                                                                                                                                                   | [`api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md`](../archive/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md)                                                            | ~1.0 (infra)       |
| 3    | **117 UTL test-fixture sweep** — `ManifestWriter.record_empty()` `pipeline_mode` kwarg added in UTL@`547ff3c` (Phase 4.DEFAULT-REMOVAL); test fixtures across UTL test suite call the old signature. Sweep tests under `unified-trading-library/tests/`; add `pipeline_mode="batch"` per UAC `PipelineMode` enum + run full QG. Surface any non-mechanical failures as issue docs                                                                                                                                                                                                                                             | UTL@`547ff3c` API drift (file issue doc if root cause needs design) + [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) Phase 4 follow-up | ~1.5 (refactor)    |
| 4    | **2-of-17 remaining strategy-service test failures** (Findings Triage HARD RULE diagnose-first: read both sides of the contract, fix code if code-stale, fix test if test-stale, file issue if genuinely ambiguous)                                                                                                                                                                                                                                                                                                                                                                                                           | strategy-service test suite + slot 4's Wave 4 follow-on at strategy-service@`114f8b2`                                                                                                          | ~1.0 (research)    |
| 5    | 🟠 **batch_live_symmetry Tabs 1-2** (codex docs half) — write `/codex/02-data/cefi-batch-live.md` + `/codex/06-coding-standards/mode-axis-discipline.md` per plan body; align with Ikenna's audit finding (0/70 done, 1 silent ServiceEmissionPolicy flip caught)                                                                                                                                                                                                                                                                                                                                                             | [`batch_live_symmetry_2026_05_10.md`](batch_live_symmetry_2026_05_10.md) Tabs 1-2                                                                                                              | ~2.5 (design)      |
| 6    | **Phase 1 freeze-gate readiness audit** — workspace-wide grep + verification that items #1-#6 are actually green (not just plan-flipped). Items #3 (PipelineMode 37-callsite) and #6 (LookaheadBiasError strict-mode features-\*) flag any GAP between plan-flip and on-disk reality. Read-only audit; file issue docs if mismatch                                                                                                                                                                                                                                                                                            | [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) "Phase 1 freeze-gate items status" section + writegate plan Phase 4                                                   | ~1.5 (research)    |
| 7    | **Slot 7 Wave 4 carry-forward sweep** — (a) UI `ui-reference-data.json` copies in `unified-trading-system-ui` need TRADER_JOEV2 producer-side update (consumer half of slot 7's Wave 4); (b) cross_asset Phase 6C UI-drilldown half — start deployment-stack to verify what works pre-cutover; (c) ICE US softs (CT/CC/KC/SB/OJ/DX) dataset disambiguation between `tradfi_symbology.py` (IFUS.IMPACT) and `tradfi_instrument_universe.py` (GLBX.MDP3). DF-5 sDAI split DEFERRED post-cutover per master plan scope.                                                                                                          | [`cross_asset_group_catalogue_audit_2026_05_10.md`](../archive/cross_asset_group_catalogue_audit_2026_05_10.md) Phase 6C + Phase 1D consumer migration                                         | ~2.0 (mixed)       |
| 8    | 🟠 **batch_live_symmetry Tab 3 + UAC + QG STEPs** (enforcement half) — write batch-live UAC contract + QG STEP ratchet that bans live-only data_types diverging from batch shape. Pair with slot 5's codex docs                                                                                                                                                                                                                                                                                                                                                                                                               | [`batch_live_symmetry_2026_05_10.md`](batch_live_symmetry_2026_05_10.md) Tabs 3+ + new QG STEP                                                                                                 | ~2.5 (design + QG) |
| 9    | **defi_recursive_borrow descope-reversal ack + cross-ping** — Frontmatter reversal shipped (2026-05-13 audit slot). **Phases 4-11 implementation MOVED TO IKENNA** per operator 2026-05-14 direction. Slot 9 scope: (a) verify plan-body descope banner is not contradicting `status: active` frontmatter; (b) verify `defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` status annotation is correct (scope-narrowed — only post-cutover items remain); (c) cross-ping Ikenna slot 2 via `plans/active/_agent_pings.md` with operator direction verbatim + Phase 4-11 handoff context so Ikenna slots can absorb. | [`defi_recursive_borrow_archetypes_2026_05_10.md`](defi_recursive_borrow_archetypes_2026_05_10.md) plan-body verification only                                                                 | ~0.5 (research)    |

**Total Harsh-side scope**: ~10.5 nominal AI-days × ~0.55 mixed multiplier ≈ **~5-6 effective cal AI-days/side today**.

**Slot 10** stays ✅ DONE idle (yesterday's `dex_perp_and_venue_data_expansion` shipped; no new theme).

---

## Cross-side handshakes today

- **Ikenna slot 2 ↔ Harsh slot 9**: defi 604k classifier crossref work in flight Ikenna-side. Slot 9 (descope writer)
  should NOT touch defi_classifier — read-only awareness only.
- **Ikenna slot 6/7 (wallet_treasury Phase 1+3 pull-forward) ↔ Harsh side**: no handshake required; wallet_treasury
  Phase 1 + 3 are Ikenna-side scope.
- **Ikenna freeze-gate close (items #3 + #6) ↔ Harsh slot 6**: slot 6 audits, files issue doc if mismatch found.
- **Cross-side ping ledger** (`plans/active/_agent_pings.md`) — slot 1 main monitors every 5 min; 4 active entries from
  yesterday still pending Ikenna-side action (Phase 6.3 ack already auto-closed at `features-service@d7514a08`,
  LDR-alignment cadence mirror, GMX/DRIFT direction correction).

---

## Spawn prompts

(Same pattern as yesterday's split — lean spawn prompt that points to LEDGER for full brief.)

```text
You are slot N (Harsh side). Do this in order, nothing else until done:

1. Read unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md (git discipline, LDR-alignment HARD RULE, fetch-first
   HARD RULE, pre-commit check, sub-agent rules).
2. Read unified-trading-pm/harsh_orchestrator/LEDGER.md § "Day-3 task briefs — 2026-05-14" for your slot's full task.
3. Read your plan-of-record (named in your brief) — scan open `- [ ]` todos for your phase.
4. Append boot ack to unified-trading-pm/harsh_orchestrator/pings/slot_N.md using `date -u` for timestamp, then start
   work.

Cadence: FF-push per shippable unit (not end-of-session). Half-1 (commit+push) + Half-2 (plan-flip) + Half-3 (deferred-
work scoreboard at session end) per CLAUDE.md.
```

---

## Done-definition (today's shift end)

- **Slot 2**: `api_football_phase_3b_3c` plan body Phase 3.B + 3.C checkboxes flipped against actuals; smoke run +
  forward-poll integration verified; DONE-2026-05-14 block written.
- **Slot 3**: 117 UTL tests pass via `bash scripts/quality-gates.sh`; pre-existing-foreign issues (non-mechanical) filed
  as issue docs with owner-tag.
- **Slot 4**: 2 remaining strategy-service tests EITHER fixed OR filed as issue doc with explicit "needs design call"
  diagnosis.
- **Slot 5**: `cefi-batch-live.md` + `mode-axis-discipline.md` codex docs shipped + plan body Tabs 1-2 flipped.
- **Slot 6**: Phase 1 freeze-gate audit report appended to master plan or filed as issue doc; items #3 and #6 verified
  green-on-disk or gap surfaced.
- **Slot 7**: UI `ui-reference-data.json` copies updated; 6C UI-drilldown status reported; ICE US softs disambiguation
  resolved or filed as issue doc.
- **Slot 8**: `batch_live_symmetry` UAC contract + QG STEP shipped; plan body Tab 3 + QG tabs flipped.
- **Slot 9**: `defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` successor plan filed; current plan annotated
  with descope; master plan + dashboard updated.
- **Slot 1 main**: end-of-day LEDGER refresh + 1+ STATUS-2026-05-14 ping per active slot.

---

## Deferred / not-in-scope today

- AWS bucket Phase 2.6 prep — AWS migration deferred past May-23 per operator (Ikenna audit batch PM@`e1e67656`).
- defi 604k reclassification implementation — Ikenna slots 2+9 own it.
- Telegram OPS chat_id — operator-only.
- DF-5 sDAI protocol-attribution split — DEFERRED post-cutover per master plan scope.
- Slot 6 api_football 3 deferred items from yesterday — operator-executable post-cutover.

---

## Open questions

(None at draft time. Will populate as slot work progresses.)
