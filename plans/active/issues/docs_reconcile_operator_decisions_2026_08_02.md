---
doc_type: issue
title:
  "docs-reconcile 2026-08-02 — 2 genuine operator-decision parks (cursor-rules/ purpose; a locked doc's broken source
  field)"
summary: >-
  Two findings from the 2026-08-02 docs-reconcile autonomous sweep that the skill's own contract requires parking for
  the operator rather than auto-fixing: (1) what the 25-file `cursor-rules/` tree is actually FOR today, now that it's
  confirmed NOT synced to the real canonical `.cursor/rules/` tree (150 files, 0 overlap) -- an authority call about
  intent, not a correctness call; (2) `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md` carries
  `locked_by: live-defi-rollout`, so its broken `source:` frontmatter entry (a brace-expansion path with a redundant
  `unified-trading-pm/` prefix) cannot be auto-fixed per the HARD RULE against editing a locked doc's frontmatter
  without sign-off.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, operator-decision, cursor-rules, locked-doc, retrieval-layer]
related: []
created: 2026-08-02
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md,
    /plans/active/issues/docs_reconcile_remaining_broken_links_2026_08_02.md,
    /plans/active/issues/doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md,
    scripts/workspace/setup-cursor-rules-symlink.sh,
  ]
supersedes:
superseded_by:
depends_on:
source: [docs-reconcile autonomous sweep, dispatch agt-0b4ee1, 2026-08-02]
assigned_role: infra
drift_direction: advance-docs
---

# docs-reconcile 2026-08-02 — 2 operator-decision parks

Both items below were found during the 2026-08-02 autonomous `/docs-reconcile` sweep. Per the skill's own
autonomous-mode contract, a genuine authority call is parked here rather than decided unilaterally. Everything else the
sweep found was either auto-fixed (4 commits shipped, see Progress Log) or filed as a separate report-only issue doc
(see `related` analogues: `doc_body_link_checker_blind_to_backtick_citations_2026_08_02.md`,
`docs_reconcile_remaining_broken_links_2026_08_02.md`).

## 🚧 BLOCKED-OPERATOR-DECISION 1 — what is `cursor-rules/` for?

- [ ] [DOCS] P2. **What is the 25-file `cursor-rules/` tree's purpose today, and should it be kept, repurposed, or
      archived?**

  Verified fact (not in question): `cursor-rules/` (25 `.mdc` files, top-level dir) and `.cursor/rules/` (150 `.mdc`
  files, dot-dir) have **zero file overlap** — confirmed via basename spot-check across both trees. The real, current
  sync mechanism (`scripts/workspace/setup-cursor-rules-symlink.sh`) treats `.cursor/rules/` as the canonical,
  git-tracked source, symlinked OUT to sibling repos — its own header says "No sync scripts needed." Three docs
  previously claimed `cursor-rules/` syncs to `.cursor/rules/`; that claim was false and has been corrected
  (unified-trading-pm@c9dc2cfb5) to state the true mechanism without asserting what `cursor-rules/` is for, since that
  part is genuinely unknown from the evidence gathered.

  An archived plan (`plans/archive/agent_ci_prototype.plan.md:70`) shows a THIRD, even earlier wiring scheme
  (`.cursor/rules/` <- symlink <- `cursor-rules/`, the reverse direction) — so the mechanism has changed at least twice,
  and `cursor-rules/` may be a leftover from an earlier iteration that was never cleaned up.

  **A: Archive `cursor-rules/`** — if nothing reads from it today (grep confirms no script/CI job references the bare
  `cursor-rules/` path as a live input), it's dead weight from a superseded wiring scheme. [RECOMMENDED — simplest, and
  the evidence gathered so far didn't surface a live consumer, though this wasn't exhaustively proven] B: **Keep it as a
  staging/draft area** — e.g. new rules are authored in `cursor-rules/` first, then promoted into `.cursor/rules/` by a
  manual step not yet automated. If true, this should be documented explicitly (the "no sync scripts needed" comment on
  the symlink script would then need a caveat). C: **Something else** — a genuinely distinct, currently-undocumented
  purpose (e.g. a different tool consumes it, or it's scoped to a specific IDE/agent that isn't Cursor). Other: operator
  can type a custom answer.

## 🚧 BLOCKED-OPERATOR-DECISION 2 — locked doc's broken `source:` field

- [ ] [DOCS] P3. **Fix (or authorize fixing) the broken `source:` frontmatter entry in
      `plans/active/issues/macro_micro_econ_data_capture_audit_2026_06_05.md`.**

  That doc carries `locked_by: live-defi-rollout` in its own frontmatter — per the workspace HARD RULE, any edit
  touching a `locked_by:` doc's frontmatter needs operator sign-off, so this was NOT auto-fixed even though the fix
  itself is mechanical and low-risk.

  The defect: `source:` (line 24) contains
  `"unified-trading-pm/codex/02-data/{mtds-data-source-coverage-matrix,tradfi-data-types-catalog,defi-data-types-catalog,sports-data-source-coverage-matrix,prediction-data-types-catalog,honest_coverage_baseline_2026_05}.md"`
  — a brace-expansion shorthand for 6 files, all of which exist, but the literal string (a) carries a redundant
  `unified-trading-pm/` prefix (the citing doc is already inside that repo) and (b) uses shell brace-expansion syntax no
  path-existence checker can literally resolve, so it's permanently flagged broken regardless of the prefix fix.

  A: **Expand the one brace-syntax string into 6 separate `/codex/02-data/<filename>.md` leading-slash entries** in the
  `source:` list. [RECOMMENDED — matches how every other multi-file citation in this corpus is written, and each of the
  6 targets was independently verified to exist] B: Leave as-is (the baseline already tolerates it as pre-existing debt;
  low real-world cost since `source:` is a provenance field, not a navigation aid). Other: operator can type a custom
  answer.

## Progress Log

- 2026-08-02 (docs_reconciler, dispatch agt-0b4ee1): filed. 4 other commits from this same sweep already shipped
  (unified-trading-pm@7de163bf1, @50f2e668b, @c9dc2cfb5, @809a28c97) covering everything that WAS auto-fixable — see the
  sweep's Phase 5 report for the full breakdown.
- **na-eligibility-audit 2026-08-02** (infra tranche, dispatch agt-fe5e17): KEEP-NA, valid — both items are explicit
  `BLOCKED-OPERATOR-DECISION` authority calls (A/B/C options, no evidence-determined single answer) per this doc's own
  title and framing. Textbook KEEP-NA, no re-derivation needed.
- **docs-reconcile 2026-08-03** (dispatch agt-fd4e6d) — NOT resolving BLOCKED-OPERATOR-DECISION 1 myself, but flagging
  strong circumstantial evidence it may already be moot: commits `unified-trading-pm@b45eab084` /`@d4f7fab9d`
  (2026-08-02 23:26-23:27, "apply operator rulings on 2026-08-02 scheduled-audit-batch operator-decision queue") deleted
  the top-level `cursor-rules/` tree entirely and moved all 25 files verbatim into
  `plans/archive/cursor-rules_2026_08_02/` — the exact action Option A here recommended, under a matching archive-date
  slug. Neither commit message names this issue doc explicitly, so this is circumstantial, not proof (hence not
  auto-closing the checkbox) — but if the operator confirms that archival WAS the intended resolution, this item and
  `pm-repo-context.mdc`'s "unresolved — flagged for operator review" note (line 29) both need a one-line update to say
  RESOLVED instead of leaving both artifacts stale.
- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-03** (ao tranche): ARCHIVE-eligible on content, still PARKED — not archiving this run.
  Independently re-verified BOTH items resolved on disk: item 1 — the entire top-level `cursor-rules/` tree is confirmed
  physically absent (`find`), moved verbatim to `plans/archive/cursor-rules_2026_08_02/` by
  `unified-trading-pm@b45eab084`/`@d4f7fab9d`, exactly Option A. Item 2 —
  `macro_micro_econ_data_capture_audit_2026_06_05.md`'s `source:` field brace-expansion string is confirmed expanded
  into 6 separate `/codex/02-data/<filename>.md` leading-slash entries (full diff read, not just `git blame`), exactly
  Option A. BUT went one step further than the 2026-08-03 docs-reconcile entry above and checked
  `plan_reconcile_parked_operator_decisions_2026_08_02.md` — the doc both commits' messages point to as the "2026-08-02
  scheduled-audit-batch operator-decision queue" source of truth — for an explicit ruling entry on either item: **zero
  hits for "cursor-rules", "macro_micro_econ", or this doc's own filename.** Separately, item 2's fix landed as a side
  effect of a BROADER 3-string brace-expansion cleanup in the same commit (2 of the 3 expanded strings — the
  `unified-api-contracts` registry ones — were never even flagged by this issue), not a targeted fix — further weakening
  the "this was a deliberate ruling on THIS item" reading vs. "a general mechanical cleanup pass happened to also
  satisfy it." Three independent read-only passes now (docs-reconcile 2026-08-03, this audit) agree the evidence is
  strong but not traceable to a recorded ruling, and item 2 involves a `locked_by:` doc's frontmatter edit with no
  sign-off record found — staying conservative on a semi-irreversible action (archival = `git mv` + corpus-wide referrer
  rewrites) rather than resolving the ambiguity myself. Leaving `.cursor/rules/pm-repo-context.mdc:29`'s "unresolved"
  note untouched too, for the same reason — let one operator confirmation trigger both updates together, as this doc's
  own 2026-08-03 entry already anticipated. **Escalating for explicit confirmation:**

  Should this doc be archived now, given both BLOCKED-OPERATOR-DECISION items appear resolved on disk but neither traces
  to a recorded ruling?

  A: Confirm both resolutions ARE the intended outcome — archive this doc now (6-step ritual). [Evidence supports this,
  but item 2 touching a locked doc's frontmatter without a traceable sign-off record makes it genuinely the operator's
  call, not a worker inference.] B: The resolutions are coincidental/unrelated to this doc's specific asks — reopen with
  corrected framing reflecting what actually happened. C: Something else — operator has context these three read-only
  passes don't. Other: operator can type a custom answer.
