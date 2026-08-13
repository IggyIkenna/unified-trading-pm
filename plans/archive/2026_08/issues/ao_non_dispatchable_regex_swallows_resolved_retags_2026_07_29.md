---
doc_type: issue
title:
  "regen_backlog_from_plan.py's _NON_DISPATCHABLE_RE silently swallows already-ruled todos whose resolution note
  restates the old BLOCKED-* marker in past tense — 27 confirmed cases invisible to AO right now"
summary:
  "Operator question 2026-07-29 -- will orchestrator/workers understand the retagged form vs the canonical tag id, or
  hit the same confusion during a manual corpus grep. Verified against the real parser
  (agent-orchestrator/server/regen_backlog_from_plan.py), not just theorized. Two distinct markers exist and only ONE is
  correctly guarded -- (1) the [OPERATOR] bracket tag: _OPERATOR_TAG_PREFIX_RE anchors to the todo's leading [TAG] P<N>.
  cluster only, so a todo's prose mentioning [OPERATOR] while explaining it is NOT gated (e.g. Retagged from
  [OPERATOR]... RULED) does NOT falsely re-gate it -- confirmed correct, and the code comment at line ~101-106
  explicitly names this exact scenario as the reason the anchor exists. (2) the BLOCKED-CREDENTIALS /
  BLOCKED-OPERATOR-DECISION markers: _NON_DISPATCHABLE_RE.search(todo_block) scans the ENTIRE checkbox + continuation
  block with NO equivalent guard. When this session's 2026-07-28 gate-cleanup/decision-apply pass resolved a todo and
  phrased the resolution note as 'was BLOCKED-OPERATOR-DECISION' / 'no longer BLOCKED-OPERATOR-DECISION' / 'retagged
  from BLOCKED-CREDENTIALS' (restating the literal old marker string in past tense, which reads as resolved to a human),
  the regex still matches on the bare substring and _parse_open_todos drops the todo from the backlog ENTIRELY -- unlike
  [OPERATOR]-tagged todos (which are still ingested as operator_gated=true, visible in the dashboard and surfaced as a
  blocked-queue entry), a BLOCKED-* match is excluded before a BacklogTask is ever created. The todo is not
  deprioritized: it is invisible to AO, the dashboard, and every worker, indefinitely, until someone manually re-reads
  the plan file. Corpus-wide replay of the real regexes across every open todo in plans/active found 2,242 open todos
  total, 93 excluded via the BLOCKED-* path, and 27 of those (across 21 files) also contain RETAGGED/RULED/RESOLVED
  language in the same block -- almost certainly already-actioned-and-ready-to-work todos AO can never see. Full detail
  in the body."
status: resolved
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog-dispatch, regex-parsing, operator-gate-retag, dispatch-correctness, false-exclusion]
related:
  [
    /plans/archive/2026_08/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-29
author: unknown
priority: P1
parent_epic: agent_operating_framework_master
source:
  "Operator question 2026-07-29 (interactive session), verified against
  agent-orchestrator/server/regen_backlog_from_plan.py"
resolved_by: ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29
locked_by:
assigned_vm: NA
execution_scope: local-only
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    /plans/archive/2026_08/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
    /cursor-configs/CLAUDE.md,
  ]
---

# `_NON_DISPATCHABLE_RE` swallows already-ruled todos that restate the old `BLOCKED-*` marker in past tense

## Evidence (reproduced 2026-07-29)

Confirmed real match on the actual compiled regex from `agent-orchestrator/server/regen_backlog_from_plan.py` (not a
hand-approximation) against real file content:

```
plans/active/infra_capture_and_devops_leftovers_2026_07_06.md:70
  - [ ] [DATA] P1. **RETAGGED 2026-07-28 (was `🚧 BLOCKED-OPERATOR-DECISION`) — RULED, see the 2026-07-28 note
        appended at the end of this task's history below.** Register + launch the ASTER live connector — ...
  _NON_DISPATCHABLE_RE.search() -> MATCH "BLOCKED-OPERATOR-DECISION" -> todo EXCLUDED, never ingested
```

Contrast with the correctly-handled `[OPERATOR]`-tag case (same file family, same 2026-07-28 pass):

```
plans/archive/2026_07/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md:395
  - [ ] [DATA] P2. **Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)** — the operator ruling below is
        the standing approval this todo needs...
  _OPERATOR_TAG_PREFIX_RE.match(description) -> "[DATA] P2. " (leading cluster only) -> "[OPERATOR]" NOT in it
  -> operator_gated=False -> todo correctly ingested as a normal dispatchable task
```

Corpus-wide replication (`_parse_open_todos` logic, all of `plans/active/**/*.md`, 2,242 open todos):

| Metric                                                                                   | Count  |
| ---------------------------------------------------------------------------------------- | ------ |
| Total open (`- [ ]`) todos                                                               | 2,242  |
| Excluded as non-dispatchable (any `BLOCKED-*`/stretch marker in block)                   | 93     |
| Of those, block ALSO contains RETAGGED/RULED/RESOLVED language (suspect false-exclusion) | **27** |

The 27 span 21 files across cefi/defi/tradfi/sports/prediction/cross-cutting — this is not localized to one AG's retag
pass; it's a structural gap in the parser that will recur every time a `BLOCKED-*` marker is resolved by restating it in
past tense rather than deleting it outright.

## Why this matters

- `BLOCKED-*` exclusion ≠ `[OPERATOR]`-tag exclusion. An `[OPERATOR]`-tagged todo stays visible (dashboard + operator
  blocked-queue). A `BLOCKED-*`-matched todo is dropped **before a `BacklogTask` object is even constructed** — it does
  not appear anywhere in AO, not even as a gated/blocked item. The only way to discover one is a manual full-corpus grep
  of the plan files themselves (which is how this was found).
- Every one of the 27 already went through an operator ruling. The operator's decision is real and recorded; the work is
  genuinely ready. It just cannot reach a worker through the normal backlog path.
- The gap will keep recurring: nothing in the retag convention (CLAUDE.md's "the moment an `[OPERATOR]`/
  `BLOCKED-OPERATOR` tag resolves, retag to the reflecting tag in the SAME edit") currently says the literal marker
  substring must be _removed_, not _restated in past tense_ — and "was `BLOCKED-X`" reads as perfectly resolved to a
  human reviewer, which is exactly why it wasn't caught until this session's parser-level verification.

## Todos

- [x] ✅ [DATA] P1. **Rephrase the 27 confirmed-affected resolution notes to drop the literal `BLOCKED-CREDENTIALS`/
      `BLOCKED-OPERATOR-DECISION`/`BLOCKED-OPERATOR` substring** (keep the same meaning — e.g. "previously required an
      operator decision, now resolved" instead of "was `BLOCKED-OPERATOR-DECISION`") so these 27 todos become
      immediately dispatchable. Safe, mechanical, no design judgment — confirm each is genuinely resolved (not a false
      positive from this heuristic) before editing. **RE-CHECKED 2026-08-12 (/plan-reconcile) — all 27 accounted for,
      closing**: `unified-trading-pm@6edd4486a` (commit message, `git show --stat`) rephrased 24 mentions across 15
      files AND explicitly documents investigating the remaining 3: "3 candidates from the original heuristic were
      verified (by reading full context) to be genuinely still blocked under a different, unrecognized custom marker
      (`BLOCKED-DATA-CORRECTNESS`, `BLOCKED-UPSTREAM` re-diagnosis) and were deliberately left untouched — rephrasing
      them would have incorrectly made them dispatchable." 24+3=27, matching this doc's original finding exactly — no
      leftover unaddressed mentions. The 24 rephrased ones were themselves independently spot-checked in two later
      passes (2026-07-29 slot-9, 2026-07-30 slot-13 — see Progress Log below), finding 2 real corrections (already
      fixed) and confirming the remaining 21 clean. Combined with the shipped code-level guard
      (`agent-orchestrator@8fdc302`, `_has_live_blocked_token()`) that now protects against this failure class
      regardless of exact wording, this todo's full scope is closed.
- [x] ✅ [OPERATOR] P1. **Operator-ruled (interactive session): (c) both.** Decide the structural fix for
      `agent-orchestrator/server/regen_backlog_from_plan.py`'s `_NON_DISPATCHABLE_RE` — pick between: (a) add a
      resolution-language exclusion (negative lookbehind/context check for "was", "no longer", "retagged from",
      "auto-resolved... retagged from" immediately around the marker — mirrors the existing `_OPERATOR_TAG_PREFIX_RE`
      guard, but prose-heuristic regexes on free text risk false negatives the other way); (b) codify a hard convention
      instead — retag workflows/agents MUST NEVER restate the literal `BLOCKED-*` token in a resolved todo, full stop
      (simpler, zero regex risk, but relies on discipline instead of enforcement); (c) both — convention as the primary
      fix, regex guard as defense-in-depth. **Shipped**: regex guard — `agent-orchestrator@8fdc302`
      (`_has_live_blocked_token()` + `_STALE_MARKER_PREFIX_RE`, 3 new tests, 150 total passing). Convention — see the
      `[DOCS]` todo below.
- [x] ✅ [DOCS] P2. **Shipped 2026-07-29** — added the "never restate the literal `BLOCKED-*` token past-tense" rule to
      CLAUDE.md's existing resolve-and-retag hard rule (Governance + safety HARD RULES § Findings triage), citing this
      issue doc by slug (`unified-trading-pm`, `cursor-configs/CLAUDE.md`, within the file's tight size-cap headroom — 3
      bytes to spare). If (b) or (c) above is chosen, add the "never restate the literal BLOCKED-* token past-tense"
      rule to CLAUDE.md's existing resolve-and-retag hard rule (Governance + safety HARD RULES § Findings triage) so
      future retag passes don't reintroduce this.
- [x] ✅ [DATA] P1. **Spot-check the other 23 of the 24 mentions rephrased by `unified-trading-pm@6edd4486a`** — DONE
      2026-07-30 (slot 13, data_engineering). Fanned out 7 parallel research agents (one per file-pair, 14 files, all 23
      remaining mentions) to independently re-verify the underlying fact behind each rephrased marker — not just re-read
      the prose. Result: **2 genuine findings, 21 mentions confirmed clean.** See Progress Log for the full breakdown
      and the fixes shipped. (repo: unified-trading-pm)

## Progress Log

- 2026-07-29: Filed. Verified via direct regex replication against the live `regen_backlog_from_plan.py` source (not
  assumed) — see Evidence. Corpus-wide count is a point-in-time measurement on a fast-moving branch; re-run before
  treating the 27/21 figures as current beyond this session.
- 2026-07-29 (slot 9, data_engineering): **False-positive found in the first todo's already-executed rephrase pass**
  (`unified-trading-pm@6edd4486a`). `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`'s item 1
  checkbox was rephrased from `BLOCKED-CREDENTIALS` to "credential gate cleared 2026-07-28 (slot 6)" — but live
  re-verification (fresh `gcloud secrets versions access` + direct `the-odds-api.com` curl, this session) confirmed the
  underlying `odds-api-key` credential is still `DEACTIVATED_KEY`, unchanged since 2026-07-26, and the operator's
  2026-07-28 ruling on that separate doc explicitly declines to fix it. The rephrase conflated two distinct gates on the
  same todo: an operator's LAUNCH-DECISION ruling (genuinely resolved — "yes, do it") and a CREDENTIAL gate (never
  resolved). Text-pattern matching on "RETAGGED/RULED/RESOLVED language in the same block" caught the decision-ruling
  language but didn't verify the credential fact underneath it. Restored the marker on that file
  (`unified-trading-pm@<pending>`, see that doc's own Progress Log for detail). **Implication for this doc's own P1 todo
  #1** ("confirm each is genuinely resolved... before editing"): that check was evidently not applied live/fact-checked
  for at least this 1 of the 24 originally-touched mentions — the other 23 in the 15 already-edited files should get the
  same live-fact spot-check before being trusted as correctly rephrased, not just re-read for prose plausibility. Not
  re-auditing the other 23 myself (outside this task's scope); flagging here so whoever owns this doc's remaining todos
  knows the first pass already shipped had a proven-live gap.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **2026-07-30 (slot 13, data_engineering): full 23-mention spot-check complete.** Dispatched 7 parallel research
  agents, one per file-pair, covering all 14 remaining files `6edd4486a` touched (excluding the sports file already
  handled above). Each agent independently traced the rephrased "RULED"/"retagged"/"no longer BLOCKED-*" claim back to
  its real evidentiary basis — a specific operator quote, a codex standing rule, a cross-referenced commit SHA, or a
  live code/data check — rather than trusting the prose. Also checked whether any file was further touched by the two
  LATER commits `dae3f1341` (odds-api-key rotation) or `1be175ce8` (2026-07-30 credential/external-blocked re-triage),
  since those could have superseded the state `6edd4486a` captured.
  - **CONFIRMED-RESOLVED / CORRECT-AS-IS (12 files, 21 items)**: `cefi_satellite_ao_dispatch_batch3_2026_07_26.md` (now
    archived at /plans/archive/2026_07/), `infra_capture_and_devops_leftovers_2026_07_06.md`,
    `/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`,
    `mtds_available_at_cross_asset_backfill_2026_07_13.md` (8 items — all trace to the same real CLAUDE.md
    maintenance-window ruling), `prediction_phase_ab_residuals_2026_07_24.md`,
    `sports_live_availability_and_source_latency_2026_07_24.md` (correctly updated in-place by the later key-rotation
    commit), `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`,
    `tradfi_manifest_content_recovery_completion_2026_07_24.md` (2 items),
    `issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md` (already shipped + independently verified),
    `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` (2 items),
    `tradfi_satellite_ao_dispatch_batch4_2026_07_26.md`, `defi_migration_audit_log_2026_07_24.md` (2 items — the
    per-venue source mapping's technical premise was independently re-verified against
    `market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py`: Marginfi/Solend really do
    fetch via DeFiLlama and Orca/Raydium via their own REST APIs as claimed, so this is a mechanically-determinable
    label-correction, not a fabricated operator ruling). One file, `v2_engine_venue_buildout_2026_06_15.md`, had a minor
    doc-hygiene gap (not a false positive): the Smarkets `DEFERRED-BY-DESIGN` item was still `[ ]` even though
    `_PERMANENT_NON_DISPATCHABLE_RE` already keeps it non-dispatchable regardless of checkbox state — flipped to `[x]`
    (`unified-trading-pm`, this commit).
  - **FALSE-POSITIVE (1 file, 1 item, FIXED this commit)**:
    `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`'s `[DATA] P3` blank-`data_type` reclassify
    item. The "RULED 2026-07-28" note claimed a "14-row (bare `OKX`×7 + bare `COINBASE`×7)" population was "the SAME
    14-row population" as a cross-cutting doc's COINBASE(7)+OKX(7) figure — but this doc's OWN §(3) measurement (same
    file) found bare `venue == "COINBASE"` = **0 rows** across the full live index, and its own §(5) venue breakdown of
    the 9,750-row population sums exactly using only `COINBASE-SPOT` (suffixed) + bare `OKX`×7 — no bare-COINBASE row
    exists anywhere in this population. Unlike the sports case, this wasn't an operator-decision-vs-technical-gate
    conflation (the decision to split backfill/reclassify per the operator's general theme is real and correctly
    applied) — it was a plain arithmetic/data error baked into the ruling text that would have misled whoever executes
    the reclassify step into hunting for 7 nonexistent bare-COINBASE rows. Corrected the row counts (9,743 backfill / 7
    reclassify, not 9,736/14) and added an explicit correction note in BOTH this doc and its cross-referencing sibling
    `cefi_satellite_ao_dispatch_batch3_2026_07_26.md` (now archived at /plans/archive/2026_07/; which had copied the
    same wrong figures into its own promoted todo + its provenance-record "Deferred" section) — the cross-cutting doc's
    separate COINBASE(7) half is now flagged as a DIFFERENT, older measurement (`audit_index_vs_gcs_spellings.py`,
    2026-06-18) not shown to be satisfied by this todo, rather than silently assumed closed. No `BLOCKED-*` marker
    restoration was needed since the underlying operator-decision gate itself was never wrong — only the row-count math
    was.
  - **Net result**: of the full 24 originally-rephrased mentions (23 here + the 1 sports item from the prior pass), 2
    needed a correction (1 credential-marker restoration done previously, 1 numeric-fact correction done this session)
    and 1 file got a minor doc-hygiene checkbox flip; the remaining 21 mentions across 13 files are genuinely
    dispatchable as rephrased. Shipped: `unified-trading-pm` (this commit, files listed above).
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged) — verified all still accurate and
  resolve.
- **context-scout 2026-08-03 (re-pass, updated methodology)**: re-verified, unchanged (4 entries) — still the right
  minimal set for the sole open todo (rephrase the 27 confirmed-affected resolution notes).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — **this doc's own 2026-07-30
  RECLASSIFY→`planning` (infra tranche, agt-30721a, recorded above) was REVERTED** by the 2026-07-31 operator directive
  `unified-trading-pm@14478ca26` ("work these interactively now rather than queue behind AO's current busy backlog"),
  which flipped it back to `assigned_vm: NA` + `execution_scope: local-only`. Per
  `/cursor-configs/skills/na-eligibility-audit/SKILL.md` Phase 1 citation class (b), a revert is a standing ruling, not
  a stale data point to re-evaluate fresh — not re-litigated.
- **Counting note (2026-08-02)**: real open-todo count is **1** (the `[DATA] P1` rephrase-the-27 item), not the 3 the NA
  inventory reports — the other 2 `- [ ]` matches are illustrative examples inside fenced code blocks in the Evidence
  section. See `/plans/active/issues/na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md`.
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. Confirmed only 1 of the 3 grep hits is
  a real todo of this doc; the other 2 are fenced-code quoted excerpts from other files (per the doc's own Counting note
  above). The one real item was `RECLASSIFY`'d once (2026-07-30) then explicitly reverted by a dated operator directive
  the next day (`unified-trading-pm@14478ca26`) — per this skill's own citation class (b), a revert is a standing
  ruling, not re-litigated.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (4 entries), still accurate.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — citation re-checked and real: the sole real open item (the other
  2 grep hits are fenced-code excerpts, per the doc's own 2026-08-02 Counting note) was RECLASSIFY'd 2026-07-30 then
  explicitly REVERTED by the dated `unified-trading-pm@14478ca26` operator directive, a standing ruling not
  re-litigated.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked "plan-destination defaults to AO-dispatched
  going forward" (round7 ruling) against this doc specifically: that is a default for cases NEVER explicitly decided,
  and this exact item already has a dated, explicit, case-specific operator revert (`unified-trading-pm@14478ca26`) — a
  specific ruling is not overridden by a later general default, same logic the 2026-08-07 marker already applied. No
  other round7-10 precedent applies. Not re-litigated.
- **/plan-reconcile 2026-08-12 (Section 1 re-check)**: closed the sole remaining open todo with a direct citation to
  `unified-trading-pm@6edd4486a`'s commit message (git show --stat, evidence above) — all todos in this doc are now
  `[x]`. Doc is archive-eligible (unlocked, all todos done+verified) but NOT archived in this pass — it has ~15 corpus
  referrers (active + archived docs, `grep -rl`) and full referrer-repoint is out of this pass's assigned scope;
  flagging as a follow-up archival candidate for a dedicated pass.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -c '^- \[ \]'` = **3** (2 fenced-
  code-block false positives + the 1 real `[DATA] P1` item, per this doc's own long-standing 2026-08-02 Counting note).
  The sole real item's own dated, explicit operator revert (`unified-trading-pm@14478ca26`) is a standing ruling, not
  re-litigated — same specific-ruling-beats-later-default logic already applied across every prior pass on this doc
  (2026-08-02 through round11).

- **ag-closeout-audit 2026-08-13**: All open todos verified genuinely resolved on independent re-read (not just trusting
  the automated verdict -- cross-checked evidence: target-doc state, shipped commits, or explicit self-description as
  no-action-needed). Archiving now per the plan-completion-and-archival HARD RULE.
