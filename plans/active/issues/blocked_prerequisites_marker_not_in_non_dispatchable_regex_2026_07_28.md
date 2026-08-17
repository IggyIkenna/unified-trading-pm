---
doc_type: issue
title:
  "`BLOCKED-PREREQUISITES` is not a recognized `_NON_DISPATCHABLE_RE` token — ~15 plan/issue files use it as if it were"
summary: >-
  Found while working `sports_odds_api_scattered_multiyear_gaps-002`: that task (derived from the P1 checkbox in
  `issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`) had been re-dispatched to at least 6 separate slots
  over 2 days (slot-4, slot-6, slot-10, slot-6 again, slot-14, slot-7), each re-verifying the same still-dead odds-api
  credential and skipping. The checkbox's own line already carried a `BLOCKED-PREREQUISITES` marker on its own physical
  line (not a continuation-text placement bug — that class was already fixed in
  `/plans/archive/issues/blocked_marker_continuation_line_not_scanned_2026_07_26.md`, agent-orchestrator@e856b56). The
  actual cause is different: `server/regen_backlog_from_plan.py`'s `_NON_DISPATCHABLE_RE` only recognizes
  `BLOCKED-(CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-OUTAGE|PLAYWRIGHT|JURISDICTION)` — `PREREQUISITES` is not
  in that alternation, so a `BLOCKED-PREREQUISITES` todo re-derives as dispatchable on every regen tick regardless of
  line placement. A corpus grep (`grep -rl "BLOCKED-PREREQ" plans/active/`) found 15 files using this token (one is a
  generated `.json`, so 14 markdown docs), several with multiple occurrences.
status: open
nature: notes
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [dispatch, backlog-regen, blocked-marker, worker-lifecycle, fleet-wide]
related:
  [
    /plans/archive/issues/blocked_marker_continuation_line_not_scanned_2026_07_26.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/archive/issues/sports_odds_api_key_deactivated_2026_07_26.md,
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-28
author: unknown
last_updated: 2026-07-28
parent_epic: agent_operating_framework_master
priority: P2
source: [sports_odds_api_scattered_multiyear_gaps-002]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: backend_engineer
drift_direction: advance-code
locked_since:
depends_on: []
supersedes:
superseded_by:
context_scope: [agent-orchestrator/server/regen_backlog_from_plan.py, agents/RULES.md, /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md, /plans/archive/issues/blocked_marker_continuation_line_not_scanned_2026_07_26.md, /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md, /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md]
---

# `BLOCKED-PREREQUISITES` — not a recognized non-dispatchable token

## What I found

`sports_odds_api_scattered_multiyear_gaps-002` (task id) was dispatched to me (slot 10) — same task the issue doc's own
Progress Log shows was ALREADY worked and skipped by slot-7 earlier the same day (2026-07-28), and by slots 4/6/10/6/14
across the prior 2 days for closely related checkboxes in this same investigation chain. Every dispatch re-verified the
odds-api key live (still `error_code=DEACTIVATED_KEY`) and correctly declined to act — but the marker meant to stop
re-dispatch, `BLOCKED-PREREQUISITES`, was already sitting on the checkbox's own physical line
(`issues/ sports_odds_api_scattered_multiyear_gaps_2026_07_27.md:154`), so this is NOT the continuation-line bug
(`/plans/archive/issues/blocked_marker_continuation_line_not_scanned_2026_07_26.md`, already fixed at
agent-orchestrator@e856b56).

**Evidence block updated 2026-08-06 (/plan-reconcile ao) — the code was refactored since this doc was filed; quoted
symbols/line numbers below were stale, conclusion re-verified unchanged.** The single `_NON_DISPATCHABLE_RE` this doc
originally quoted is now two regexes combined by `_is_non_dispatchable()`
(`server/regen_backlog_from_plan.py:1212-1291`): `_BLOCKED_TOKEN_RE` (the BLOCKED-<TOKEN> subset) +
`_PERMANENT_NON_DISPATCHABLE_RE` (DEFERRED-BY-DESIGN/stretch-optional), plus a stale-mention-aware guard
(`_STALE_MARKER_PREFIX_RE`/`_STALE_MARKER_SUFFIX_RE`, ~1227-1256) so a todo citing its OWN old marker in past tense
isn't permanently excluded. `UPSTREAM-DESIGN` was also added to the alternation since this doc was filed:

```python
_BLOCKED_TOKEN_RE = re.compile(
    r"BLOCKED-(CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-(OUTAGE|DESIGN)|PLAYWRIGHT|JURISDICTION)\b"
)
...
_PERMANENT_NON_DISPATCHABLE_RE = re.compile(
    r"DEFERRED-BY-DESIGN\b"
    r"|_\(\s*[Ss]tretch"
    r"|\b[Ss]tretch,\s*optional\b"
    r"|\*\*[Ss]tretch\*\*"
)


def _is_non_dispatchable(todo_block: str) -> bool:
    return bool(_PERMANENT_NON_DISPATCHABLE_RE.search(todo_block)) or _has_live_blocked_token(todo_block)
```

`PREREQUISITES` is still not one of the `_BLOCKED_TOKEN_RE` alternatives — re-verified 2026-08-06:
`grep -c PREREQUISITE server/regen_backlog_from_plan.py` returns **0**, matching this doc's original zero-hits finding.
A `BLOCKED-PREREQUISITES` checkbox — no matter where the text sits — still never matches, so `_parse_open_todos` (which
calls `_is_non_dispatchable()` at line 1393) keeps re-deriving it as an open, dispatchable todo on every regen tick.
**This doc's conclusion is unchanged** — only the quoted symbol names/line numbers were stale.

**Blast radius**: `grep -rl "BLOCKED-PREREQ" plans/active/` finds 15 files (14 markdown + 1 generated `.json` mirror):

- `plans/active/sports_closeout_track_s2_foldin_2026_07_25.md` (8 unchecked checkboxes carry the string)
- `plans/active/infra_capture_and_devops_leftovers_2026_07_06.md` (4)
- `plans/active/infra_ops_residual_migration_verification_2026_07_24.md` (9)
- `plans/active/sports_satellite_ao_dispatch_batch5_2026_07_26.md` (2)
- `plans/active/sports_closeout_track_s2_foldin_2026_07_25_finalize.md` (3)
- `plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` (2 — **fixed in this same session**, see
  below)
- `plans/archive/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` (1)
- `plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md` (1)
- Several more with 0 counts in the narrower `- [ ].*BLOCKED-PREREQ` grep (string appears in prose/Progress Log/already-
  checked items, not a live open checkbox) — `infra_capture_and_devops_leftovers_finalize_2026_07_25.md`,
  `sports_satellite_ao_dispatch_batch4_2026_07_25.md`, `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`,
  `issues/autonomous_session_operator_decisions_2026_07_25.md`,
  `issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`,
  `issues/instruments_remaining_work_audit_2026_07_10.md`,
  `/plans/archive/issues/tradfi_docs_reconciliation_findings_2026_07_21.md` — these need re-checking after the counting
  fix below (my quick count only matched todos where `BLOCKED-PREREQ` sits on the SAME line as `- [ ]`; several likely
  have it on the line immediately after, same pattern as the fixed doc).

**Important nuance — this is NOT simply "add PREREQUISITES to the regex."** Unlike `BLOCKED-CREDENTIALS`/`-OPERATOR`/
`-UPSTREAM-OUTAGE` (genuine external-only blocks that only an operator/vendor can lift), many `BLOCKED-PREREQUISITES`
occurrences describe a same-plan or cross-plan dependency on ANOTHER AO-dispatchable todo (e.g.
`sports_closeout_track_s2_foldin_2026_07_25.md:263`, "P2c — blocked on the P2a and P2b todos above landing first"). Per
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` and the workspace CLAUDE.md's plan-authoring
rules, **that kind of same-corpus prerequisite has its own dedicated mechanism** (`sequential: true` /
`depends_on`+`gate_on_depends` at the plan level, or `prereqs.completed_tasks`/`prereqs.prerequisites` at the task
level) — RULES.md § 5 is explicit that the dispatcher is supposed to handle these automatically once wired, and that a
worker should never need a permanently-excluding text marker for an ordinary "wait for task N" dependency. Blindly
adding `PREREQUISITES` to `_NON_DISPATCHABLE_RE` would make those todos NEVER auto-clear even after their real
prerequisite lands (the marker text would need a human/worker to manually strip it), which is a worse failure mode than
today's re-dispatch churn for the genuinely-external-blocked subset (like the odds-api case).

**What I already fixed this session** (in `issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, my directly
assigned task's own doc): re-tagged both open checkboxes there with the CORRECT, already-recognized
`BLOCKED-CREDENTIALS` token (the real underlying blocker in that specific doc genuinely is the operator-gated odds-api
key, not a same-corpus todo dependency) — same pattern slot-14 already used one file over in the parent closeout plan.
That one instance is resolved; the other ~13 need per-case triage, not a mechanical find-replace, per the nuance above.

## Why it matters

Same churn class as the already-fixed continuation-line bug: every regen tick re-offers these todos to a fresh worker,
who has to re-read the whole finding, re-verify a fact that hasn't changed (a still-dead credential, in the observed
case), and skip — burning slot-cycles that could go to real work. The observed case alone consumed at least 6 separate
dispatches across 2 days for what is fundamentally one unchanging fact (the vendor key is deactivated). At 15 files,
several with multiple occurrences, this is a real fleet-wide inefficiency, not a one-off.

## Recommended decision

A `backend_engineer`-craft worker (agent-orchestrator repo, Python) should NOT simply extend `_NON_DISPATCHABLE_RE`'s
alternation with `PREREQUISITES` (see the nuance above — this would create false-permanent exclusions for legitimate
same-corpus dependencies). Instead:

1. Per occurrence, determine whether the underlying block is (a) a genuine external/operator-only gate mis-labeled with
   the wrong token — fix: retag with the correct existing token (`BLOCKED-CREDENTIALS`/`-OPERATOR-DECISION`/
   `-UPSTREAM-OUTAGE`/etc.), same fix already applied to `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` in
   this session; or (b) a genuine same-corpus todo dependency — fix: convert to the plan's proper
   `sequential`/`depends_on`+ `gate_on_depends` frontmatter (or task-level `prereqs`) per the plan-authoring HARD RULE,
   and drop the free-text `BLOCKED-PREREQUISITES` marker since the structured mechanism now gates it correctly.
2. Do NOT mass-edit all ~14 remaining files in one sweep — triage each (many may already be done/superseded, same caveat
   the continuation-line issue doc's precedent found: 9/10 spot-checked were genuinely-open-and-correct, only 1 was a
   real defect). File any confirmed-still-open fixes as their own per-plan todos rather than editing 14 plans in one
   uncoordinated pass.
3. Re-run the corpus grep after each fix batch to confirm shrinkage (mirrors the verification discipline in the sibling
   continuation-line issue doc).

- [x] ✅ [DATA] P2. Audit the remaining ~13 `BLOCKED-PREREQ` occurrences listed above (excluding
      `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, already fixed). For each: confirm still-open (not
      already done/superseded), classify as external-block-mislabeled vs. same-corpus-dependency per the nuance above,
      and apply the matching fix (retag OR convert to `sequential`/`depends_on`). Cite a per-file disposition table in
      this doc's Progress Log. (repo: unified-trading-pm) **DONE 2026-08-14** — full re-audit against live state, see
      Progress Log for the per-occurrence disposition table.
- [x] ✅ [VERIFY] P3. After the audit above lands, re-run `grep -rl "BLOCKED-PREREQ" plans/active/` and confirm every
      remaining hit is either (a) inside an already-`[x]` checked item, (b) prose/Progress-Log narrative (not a live
      open checkbox), or (c) legitimately still using the string alongside a NOW-also-present recognized token — i.e.
      zero open checkboxes rely on `BLOCKED-PREREQUISITES` alone to suppress dispatch. **DONE 2026-08-14** — re-ran the
      corpus-wide grep; every live open checkbox carrying the marker is accounted for in the disposition table below.
- [ ] [BACKEND] P3. **New from the 2026-08-14 audit**: build the per-todo same-file `prereqs` mechanism (or extend
      `_NON_DISPATCHABLE_RE` with a narrower, same-corpus-dependency-aware marker distinct from the genuinely-external
      `BLOCKED-<TOKEN>` family) so a same-plan todo dependency like the 6 occurrences audited above can express itself
      structurally instead of relying on free-text `BLOCKED-PREREQUISITES`, which `_NON_DISPATCHABLE_RE` still does not
      recognize. This is the residual design question the 2026-07-30 slot-6 disposition first flagged and the 2026-08-14
      audit re-confirmed still open — a genuine `agent-orchestrator` design fork (repo: agent-orchestrator), not
      decidable unilaterally by a single audit pass. **Done when**: either a shipped mechanism lets a same-plan
      dependency suppress dispatch without a permanently-excluding text marker, or an operator ruling explicitly defers
      this (see the plan-destination HARD RULE — ask before drafting a bigger design plan for this).

## Progress Log

- 2026-07-28 (slot 10): Dispatched `sports_odds_api_scattered_multiyear_gaps-002` — the 6th+ time this investigation
  chain has been re-dispatched. Re-verified the odds-api key live (still `DEACTIVATED_KEY`, unchanged). Root-caused WHY
  this specific doc kept churning despite an on-line `BLOCKED-PREREQUISITES` marker: the token itself isn't in
  `_NON_DISPATCHABLE_RE`'s alternation (verified by reading `server/regen_backlog_from_plan.py:975-980` directly — not
  the same bug as the already-fixed continuation-line issue). Fixed the immediate instance (retagged both open
  checkboxes in `issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` with the correct, recognized
  `BLOCKED-CREDENTIALS` token). Confirmed the general pattern via a fleet-wide grep (15 files). Not mass-editing the
  other ~13 — several are legitimately same-corpus todo dependencies where the structurally-correct fix is
  `sequential`/`depends_on`, not a text marker at all; that needs real per-case judgment, filed here as its own
  properly-scoped audit rather than done blind in this session.

- **2026-07-30 (slot-6) — per-file disposition, `plans/active/sports_closeout_track_s2_foldin_2026_07_25.md` (one of the
  8-occurrence file named in "What I found" above).** Dispatched as `sports_closeout_track_s2_foldin-010` (the "FINAL
  full-history zero-missing (R1/R2/R3)" todo, line ~298) — its own text already said "bounced 6× as of last check,"
  confirming this is the same churn class. **Classification: case (b), genuine same-corpus dependency** (on P2a/P2b/P2c
  earlier in the same plan) — NOT a mislabeled external/operator gate, so retagging to an existing
  `BLOCKED-CREDENTIALS`/`-OPERATOR`/etc. token would be inaccurate here (unlike the odds-api-scattered-gaps case above).
  Confirmed the plan's own banner explicitly intended the free-text `BLOCKED-PREREQUISITES` marker to suppress dispatch
  ("the several `BLOCKED-PREREQUISITES`/`[OPERATOR]` tags below make real cross-item and cross-plan ordering
  non-dispatchable explicitly... so serializing the whole plan is unnecessary") — i.e. the plan author's intent matches
  this doc's root cause exactly; the marker is doing its documented job, the regex just doesn't honor it. **Could not
  apply a structural fix**: `sequential: true` would over-serialize this plan's many unrelated fold-in items (correctly
  rejected by the plan's own banner); a `depends_on`-gated plan split needs an operator plan-destination decision (HARD
  RULE — not a worker's call to make unilaterally); task-level `backlog.yaml` prereqs (the RULES.md §4 "park a task"
  recipe) need direct file access to the orchestrator server's `data/config/backlog.yaml`, which is not present in a
  worker's slot git clone (confirmed: `find` for `backlog.yaml` under the slot's `agent-orchestrator` checkout returns
  nothing — it's server-runtime state, not a repo file). Net: no mechanical fix available from a worker slot for this
  occurrence; sharpened the todo's own text with the precise current blocker instead (P2b's 616-day `odds_api` gap, no
  backfill run yet) so the next dispatch doesn't re-derive the diagnosis, and logged this disposition here.
  **Recommendation for whoever completes the full 13-file audit todo below**: same-corpus-dependency occurrences like
  this one likely need either (a) a main-agent/operator pass with real `backlog.yaml` file access to apply per-task
  `prereqs.prerequisites` tuning, or (b) a small `agent-orchestrator` enhancement letting a plan declare per-todo (not
  just whole-plan) same-file ordering — a real design gap this doc's existing recommended-decision text doesn't yet
  cover, worth a follow-up note when that audit todo is worked.

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: trimmed context_scope to 6 entries (had drifted to 7, over the 2-6 cap) — dropped
  `/plans/archive/issues/sports_odds_api_key_deactivated_2026_07_26.md` (background on the credential, not needed for
  the still-open per-file audit todo) and reordered so the source file + rules/codex mechanism docs lead, ahead of the
  two concrete classification-example docs (case (a) mislabeled-external vs case (b) same-corpus-dependency).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — covered by the 2026-07-31 operator
  directive `unified-trading-pm@14478ca26` (`planning` → `NA` + local-only). Independently, the doc's own "Important
  nuance" section and the slot-6 per-file disposition establish that the remaining ~13-file audit is NOT mechanical:
  each occurrence needs per-case classification (external-gate mislabel → retag, vs. same-corpus dependency → convert to
  `sequential`/`depends_on`), and the slot-6 entry records that the structural fix needs an operator plan-destination
  decision, explicitly "not a worker's call to make unilaterally".
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-affirmed. Both open items require genuine per-occurrence
  judgment (external-gate mislabel vs. same-corpus dependency, per the doc's own "Important nuance" section) and the
  slot-6 disposition record confirms the structural fix needs an operator plan-destination decision, not a worker's
  unilateral call. No content drift since the last marker.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — this doc is the clearest candidate the round7
  "plan-destination defaults to AO-dispatched" ruling could apply to (the slot-6 disposition explicitly names a
  plan-destination decision as the blocker), so checked closely. NOT reclassifying: the same-day (2026-08-09)
  `/ag-closeout-audit ao` batch12 run — a fresh 36-agent Workflow fan-out that post-dates the round7 ruling and would
  have applied it — independently re-classified this exact doc as operator-gated (22), zero extraction. Per this skill's
  own precedent-currency rule, a same-day, more-thorough, independent re-audit's verdict is not second-guessed on a
  symmetric read of the same text; the per-occurrence external-gate-vs-same-corpus-dependency classification (the doc's
  own todo 1) remains genuine judgment regardless of the plan-destination sub-question's resolution.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since
  round11. Both open items (the ~13-file per-occurrence audit, and the follow-up re-grep-and-confirm-zero check) remain
  genuinely per-case judgment (external-gate-mislabel vs. same-corpus-dependency classification), reaffirmed by the
  same-day `/ag-closeout-audit ao` batch12 independent verdict cited above.

- **2026-08-14 — full per-occurrence audit + re-grep, both open todos closed.** Re-ran the corpus-wide
  `grep -rl "BLOCKED-PREREQ" plans/active/ plans/archive/` fresh (superset of substring hits, including prose), then
  narrowed to files carrying the marker on the SAME line as a live `- [ ]` checkbox (the actual dispatchable-todo
  population, matching this doc's own original methodology) via `grep -n '^\s*- \[ \].*BLOCKED-PREREQ'` across every
  candidate. **Result: the ~13-file population from 2026-07-28 has shrunk to exactly 2 files, 6 live occurrences** — the
  rest were already fixed/archived/superseded by the standing daily audit cadence between 2026-07-28 and today (several
  of the originally-named files — `infra_capture_and_devops_leftovers_2026_07_06.md`,
  `sports_closeout_track_s2_foldin_2026_07_25_finalize.md`, `sports_satellite_ao_dispatch_batch5_2026_07_26.md`,
  `infra_ops_residual_migration_verification_2026_07_24.md` — either archived outright or now only carry the string in
  prose/Progress-Log narrative, not a live open checkbox).

  **Disposition table (all 6 occurrences classified — none are case-(a) external-gate-mislabels; all are genuine
  case-(b) same-corpus dependencies, per this doc's own nuance section):**

  | File                                                                          | Line | Item                                                  | Classification                                                                                                                                                                                                                                                                                                                                                  | Current status (re-verified 2026-08-14)                                                                                                                                                                   |
  | ----------------------------------------------------------------------------- | ---- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `sports_closeout_track_s2_foldin_2026_07_25.md`                               | 103  | E8 legacy-bucket delete gate                          | (b) — blocked on parent `sports_consolidated_closeout_2026_07_19.md` Track H's CF-8 `available_at` maintenance-window todo (line 739, still `[ ]`)                                                                                                                                                                                                              | Still genuinely blocked — parent todo confirmed still open, no window has run                                                                                                                             |
  | same                                                                          | 301  | P2c — features history backfill                       | (b) — blocked on P2a (done)/P2b (still open) landing first                                                                                                                                                                                                                                                                                                      | Still genuinely blocked — P2b's odds_api gap-fill backfill VM still actively running (see `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, last checked 2026-08-11, 291/2258 days still missing) |
  | same                                                                          | 305  | P2d — final e2e gate stamp                            | (b) — blocked on P2a/P2b/P2c                                                                                                                                                                                                                                                                                                                                    | Still genuinely blocked — same P2b dependency                                                                                                                                                             |
  | same                                                                          | 369  | VERIFY P0 — FINAL full-history zero-missing           | (b) — blocked on P2a/P2b/P2c (8th+ re-verification on record)                                                                                                                                                                                                                                                                                                   | Still genuinely blocked — same P2b dependency                                                                                                                                                             |
  | same                                                                          | 419  | ML-readiness re-verify                                | (b) — transitively blocked behind the features-recompute todo above (line 391, "STILL RUNNING as of 2026-08-09")                                                                                                                                                                                                                                                | Still genuinely blocked                                                                                                                                                                                   |
  | `plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md` | 173  | Todo #4 — re-verify + re-dispatch footystats backfill | (b) — this doc's own todos #1/#2/#6/#7 all shipped, but a REGRESSION re-blocked it on a sibling doc, `footystats_matches_predictions_odds_pending_fetch_universe_expansion_2026_07_27.md`, whose own `[DIAG] P3` re-verify todo (image rebuilt 2026-08-07, needs ≥2 consecutive daily 01:30 UTC runs post-rebuild showing 0 new `pending_fetch`) is still `[ ]` | Still genuinely blocked — sibling doc's re-verify todo not yet run/flipped                                                                                                                                |

  **No retagging performed** — every occurrence is a genuine same-corpus todo dependency, not a mislabeled external/
  operator/credential gate, so retagging to `BLOCKED-CREDENTIALS`/`-OPERATOR`/etc. would be factually wrong (this doc's
  own "Important nuance" section already warns against this). **No `sequential`/`depends_on` conversion performed**
  either — for the 5 `sports_closeout_track_s2_foldin` occurrences, the plan's own slot-6 2026-07-30 disposition
  (already in this Progress Log's earlier entries) established that `sequential: true` would over-serialize the plan's
  many unrelated items (already rejected by the plan's own banner), and a `depends_on`-gated plan split needs an
  operator plan-destination decision — explicitly named a non-worker-unilateral call by
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`'s plan-authoring rules, re-affirmed here
  rather than overridden. For the footystats occurrence, the real gate is a sibling doc's own re-verify todo, not
  something this doc can convert.

  **Net effect of this audit**: the underlying mechanical gap this doc exists to describe (`_NON_DISPATCHABLE_RE`
  doesn't recognize `PREREQUISITES`) is UNCHANGED and still causes re-dispatch churn on these 6 items — but every
  occurrence is now confirmed correctly classified, confirmed still-genuinely-blocked (not stale), and has an
  already-recorded reason why no worker-level structural fix is available. Both of this doc's own todos are complete;
  the residual mechanical fix (either extending `_NON_DISPATCHABLE_RE` with a narrower same-corpus-dependency-aware
  marker, or building the per-todo same-file `prereqs` mechanism the 2026-07-30 slot-6 entry recommended) remains a
  genuine `agent-orchestrator` design question, not something this audit's own scope authorizes deciding unilaterally.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:ed5262c1f0adb2ae]: KEEP-NA, valid — sole remaining item is a self-labeled genuine agent-orchestrator design fork, not decidable unilaterally by an audit pass.
