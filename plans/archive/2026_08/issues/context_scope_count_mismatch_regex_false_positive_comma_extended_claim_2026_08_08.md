---
doc_type: issue
title:
  COUNT_MISMATCH false positive when a marker's own count claim is a comma-extended parenthetical -- window scan picks
  up an unrelated LATER match instead
summary: >-
  While running the daily `/context-scout` sweep (2026-08-08, context_scout_auditor dispatch agt-acfb90, slot 6), Phase
  0's `generate_context_scope_inventory.py` flagged
  `plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` -- the doc that is ITSELF the
  SSOT for the COUNT_MISMATCH verdict -- as COUNT_MISMATCH (claimed 5, live 4). Direct inspection (calling
  `_latest_marker_info`/`_marker_claimed_count` from a REPL against the live file) showed this is a false positive: the
  doc's actual latest marker reads "context-scout 2026-08-07**: refreshed context_scope (4 entries, written and counted
  with extra care ...)" -- 4 matches the live list exactly. `COUNT_RE = r"\((\d+)\s+entr(?:y|ies)\)"` requires the
  closing paren IMMEDIATELY after "entries", so the comma-extended form "(4 entries, written and counted...)" does not
  match at all. `_marker_claimed_count`'s window (from the bullet's `\n- ` start to the next bullet or 2000 chars)
  extends past this non-matching claim and `.search()` finds the NEXT strict `(N entries)` occurrence in the window
  instead -- which in this specific doc happens to be a quoted excerpt of a DIFFERENT doc's stale marker
  ("`context-scout 2026-08-01 (5 entries)`", quoted later in the same bullet's prose) -- producing claimed=5 instead of
  the correct answer (no confident claim / None). Verified via direct function calls, not by re-reading source alone.
status: archived
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, context-scout, context_scope, count_mismatch, regex, false-positive, mvi]
related:
  [
    /plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md,
    /scripts/plan-hygiene/generate_context_scope_inventory.py,
    /cursor-configs/skills/context-scout/SKILL.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
author: context_scout_auditor (dispatch agt-acfb90, slot 6)
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.18
assigned_role: data_engineering
drift_direction: advance-process
depends_on: []
locked_by:
locked_since:
resolved_by: unified-trading-pm@fd8c843533
source: >-
  Found incidentally during the 2026-08-08 daily `/context-scout` sweep (context_scout_auditor, dispatch agt-acfb90,
  slot 6), Phase 0 inventory step, while triaging the run's 2 COUNT_MISMATCH-verdict docs before dispatching Phase 1
  scouting sub-agents. The other COUNT_MISMATCH doc in the same run
  (`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`, claimed 6 / live 8) is a GENUINE mismatch by the
  same manual-verification method -- only this one doc's flag is a tooling false positive, which is itself notable: the
  false positive landed on the exact doc that documents this verdict's own bug history, because that doc's prose
  necessarily quotes OTHER docs' `(N entries)` marker text as evidence.
context_scope:
  [
    /scripts/plan-hygiene/generate_context_scope_inventory.py,
    /plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md,
    /cursor-configs/skills/context-scout/SKILL.md,
  ]
---

> **ARCHIVED 2026-08-15** — sole todo resolved. `_marker_claimed_count` hardened against window spillover
> (comma-extended-claim regex + backtick-quoted-span exclusion); verified live against the corpus
> (`context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` now reads UP_TO_DATE, not COUNT_MISMATCH). See
> Progress Log for full detail. `unified-trading-pm@fd8c843533`.

# COUNT_MISMATCH false positive: comma-extended count claim + window spillover

## What I found

Repro (run from `unified-trading-pm/`, any Python 3 with PyYAML):

```python
import importlib.util
spec = importlib.util.spec_from_file_location("csi", "scripts/plan-hygiene/generate_context_scope_inventory.py")
csi = importlib.util.module_from_spec(spec); spec.loader.exec_module(csi)

path = csi.PM / "plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md"
fm, body = csi.ds.parse_frontmatter(path.read_text())
info = csi._latest_marker_info(body)              # -> ('2026-08-07', 30717)
csi._marker_claimed_count(body, info[1])           # -> 5  (WRONG -- the marker itself says "4 entries")
len(fm["context_scope"])                            # -> 4  (correct, matches the marker's actual prose)
```

The live doc's latest marker line is:

> `- **context-scout 2026-08-07**: refreshed context_scope (4 entries, written and counted with extra care given this doc's own subject matter) -- swapped the now-fixed \`lst_rate_honest_coverage_2026_07_21.md\`
> ... plus \`check_line_caps.sh\`. Live-checked \`data_completion_defi_2026_07_15.md\` at write time: still 1000L, still
> carries the stale \`context-scout 2026-08-01 (5 entries)\` marker, ...`

`COUNT_RE = re.compile(r"\((\d+)\s+entr(?:y|ies)\)")` demands the closing `)` land immediately after "entries" — the
real claim, `(4 entries, written and counted with extra care ...)`, has a comma and trailing prose before its own
closing paren, so it never matches. `_marker_claimed_count`'s window (bullet start to the next `\n- `/`\n## `/2000
chars, whichever first) is wide enough to reach the QUOTED "`context-scout 2026-08-01 (5 entries)`" text later in the
same bullet — a strict match — and `COUNT_RE.search()` returns THAT one instead, since it's the first (and only)
regex-conformant match in the window. Result: claimed=5 vs. live=4 → false COUNT_MISMATCH.

## Why this is a distinct bug from the one this doc's sibling already tracks

`context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md`'s own history is about the COUNT_MISMATCH verdict
NOT existing yet (entry-drop and write-time-miscount going undetected). This is the opposite direction: the verdict NOW
exists and fires on a doc whose real content is fine, because of how the window search interacts with prose that quotes
another doc's marker text verbatim. Both are real, but this one produces a false ALARM rather than a false CLEAR — lower
severity (see Impact), but still worth fixing since it will keep re-triggering an unnecessary re-scout of this specific
doc (and any future doc whose Evidence section quotes another doc's `(N entries)` marker text) every run.

## Impact: LOW, self-healing

A false COUNT_MISMATCH only costs one extra Phase-1 re-scout pass on the affected doc(s) — Phase 1 always verifies
against the LIVE frontmatter + a fresh read of the doc, never trusts Phase 0's verdict label blindly, so no incorrect
`context_scope` content can result from this bug. It is a wasted-work/noise issue, not a correctness/data-integrity
issue. Not escalating to the operator on this basis (CLAUDE.md's "big finding" bar -- data-correctness / critical path /
cross-repo / SSOT contradiction / kill-switch / batch≠live -- does not apply here).

## Todos

- [x] ✅ [SCRIPT] P3. **Harden `_marker_claimed_count` against window spillover.** Two independent, combinable fix
      directions -- pick after weighing regression risk against the corpus's existing fixture suite (4 unit helpers + 4
      end-to-end fixtures per `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md`'s Progress Log,
      2026-08-06 slot-11 entry): (a) extend `COUNT_RE` to also accept a comma-extended claim, e.g.
      `\((\d+)\s+entr(?:y|ies)\b` matched against just the text immediately after the marker's colon (not paren-closed),
      so the REAL claim is found instead of skipped; and/or (b) narrow the search window to the marker's own sentence
      (up to the first `)`, `.`, or newline after the marker date) rather than the whole bullet up to the next
      bullet/2000 chars, so a LATER quoted excerpt in the same bullet can never be mistaken for the current doc's own
      claim. Add a fixture case reproducing this exact doc's shape (a marker with a comma-extended count claim, followed
      later in the same bullet by a different, strict-form `(N entries)` string) to the existing test suite. **Done
      when**: the new fixture passes, all existing COUNT_MISMATCH/UP_TO_DATE fixtures still pass unchanged, and
      re-running Phase 0 against the live corpus no longer flags
      `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` as COUNT_MISMATCH (assuming its frontmatter
      is still internally consistent at fix time -- re-verify live, don't assume this doc's own state hasn't moved).

## Progress Log

- **2026-08-08 (context_scout_auditor, dispatch agt-acfb90, slot 6)**: filed during the daily `/context-scout` sweep's
  Phase 0 triage, per the `/pre-compact` ritual's Step 3 ("every deferral becomes a `- [ ]` todo, never prose") --
  running in autonomous/AO-dispatched mode with no interactive operator to relay findings to in chat, so this doc IS the
  durable write. Deliberately filed as a SEPARATE doc rather than appended to
  `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` (topically the closest fit) because that doc is
  itself inside this same session's Phase-1 scouting corpus (202 in-scope docs) and will receive its own
  `context_scope` + marker refresh through the normal per-doc scouting flow -- editing its body separately in the same
  session would double-touch one file for two different reasons in a way that's harder to audit than two small,
  cross-referenced docs. Not fixing the regex myself this session: `generate_context_scope_inventory.py` has an existing
  dedicated fixture suite (1720 passed / 0 failed per the sibling doc's history) that a same-session, time-boxed fix
  risks regressing without dedicated test-writing attention, and the finding is non-blocking (Impact: LOW, self-healing)
  for this run's own Phase 1-3 completion -- diagnosed in full (exact repro, exact root cause, two concrete fix
  directions) rather than left as an unscoped "should investigate" note, per findings-triage's diagnose-both-sides
  allowance for a non-blocking, ambiguous-regression-risk fix.
- **2026-08-08 (context_scout_auditor, dispatch agt-acfb90, slot 6) -- related corroboration, not filed separately**:
  this same session's first `Workflow` launch (Phase 1 scouting fan-out, ~25KB combined `args` payload: a ~9.8KB rules
  string + a ~15.6KB batches array) hit the exact failure already tracked in
  `/plans/active/issues/workflow_tool_object_args_param_undefined_in_script_2026_08_08.md` (`args` arriving `undefined`
  inside the script body) -- a second data point at a similar payload size to that issue's original ~20.6KB repro,
  supporting its open "payload-size-gated" hypothesis (todo 1, still unowned). Not filed as a separate issue or edited
  into that doc directly (same double-touch reasoning as above -- it is also inside this run's Phase-1 scouting corpus);
  recorded here instead since this doc is this session's durable pre-compact checkpoint. Workaround (inline JS literals
  instead of top-level `args`) applied and confirmed working -- the workflow ran successfully after the rewrite.
- **na-eligibility-audit 2026-08-08 (cross-cutting tranche)**: RECLASSIFY, conflict-cleared -- the sole open todo is a
  bounded, single-file regex/window-spillover fix in `_marker_claimed_count`
  (scripts/plan-hygiene/generate_context_scope_inventory.py) with a concrete done-when (new fixture passes, all existing
  COUNT_MISMATCH/UP_TO_DATE fixtures unchanged, live corpus no longer false-flags the cited doc); the choice between the
  two stated fix directions (a)/(b) is ordinary bounded engineering judgment, not an open design call -- flipped
  `assigned_vm: NA -> planning`, `execution_scope: local-only -> orchestrator-agent`. `assigned_role: data_engineering`
  (already correctly set at filing, validated against the live `agents/*.md` registry) left unchanged. Conflict-check
  clear (`ao-dispatch-batch-naming-and-conflict-check.md` § 3): the doc's own text already distinguishes this bug from
  its sibling `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` (opposite failure direction -- that
  doc is about a missing COUNT_MISMATCH verdict, this one is a false-positive AFTER the verdict shipped); the 2 other
  grep hits sharing terminology (`ao_satellite_ao_dispatch_batch3_2026_07_31.md` -- corpus-wide `context_scope`
  BACKFILL, a different concern; `na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md` -- a
  disjoint script/regex, `generate_na_doc_tranche_inventory.py`'s `CHECKBOX_RE`, not
  `generate_context_scope_inventory.py`'s `COUNT_RE`) do not overlap; the only other currently-active
  `assigned_vm: planning` doc in `parent_epic: plan_hygiene_master` (`codex_vs_repo_docs_ssot_audit_2026_06_01.md`)
  mentions `context_scope` only in its own routine Progress Log scouting entries, no claim on this fix;
  `cross_cutting_consolidated_closeout_2026_07_25.md`'s own text has no overlap either. `doc_type: issue` --
  structurally exempt from the finalize-plan-coverage rule (`check_finalize_plan_coverage.py` only globs
  `plans/active/*.md`, non-recursive), so no companion finalize plan authored.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **2026-08-15 (data_engineering, slot 23)**: shipped fix direction (a)+(b) combined — `COUNT_RE` now
  `\((\d+)\s+entr(?:y|ies)\b` (accepts a comma-extended claim, no longer requires the closing paren immediately after
  "entries"), and `_marker_claimed_count` skips any match landing inside a backtick-quoted span in its window (this
  corpus's convention for citing another doc's marker text verbatim — the exact mechanism that produced the false
  positive). A pure "narrow the window to the first `)`/`.`/newline" approach (direction (b) alone) was tried first and
  rejected: this doc's own body has real parenthetical count claims that legitimately span a soft-wrapped newline
  mid-sentence, and a naive first-`(`-only match broke a real, currently-passing marker elsewhere in this same doc (the
  2026-08-09 marker above, whose real "(5 entries)" claim is NOT the first parenthetical in its bullet) — backtick-span
  exclusion was the fix that handled both without regressing either. Added 1 unit test (`_marker_claimed_count`
  reproducing this exact comma-extended + backtick-quoted-trap shape) + 1 end-to-end fixture. Full PM QG: 2039 passed,
  17 skipped. Verified live: `context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md` now reads `UP_TO_DATE`
  (was the confirmed COUNT_MISMATCH false positive) via a fresh `generate_context_scope_inventory.py --json` run against
  the live corpus post-ship. Shipped unified-trading-pm@fd8c843533.
