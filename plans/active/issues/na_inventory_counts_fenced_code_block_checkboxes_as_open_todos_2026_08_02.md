---
doc_type: issue
title:
  "generate_na_doc_tranche_inventory.py (and the NA-corpus ratchet it feeds) counts `- [ ]` lines inside fenced code
  blocks as real open todos — one doc reports 5 open todos when it has 0"
summary: >-
  `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py`'s `CHECKBOX_RE` is applied to the whole document body with
  no awareness of fenced (```) regions, so a checkbox line QUOTED inside a code block — e.g. an issue doc reproducing
  the upstream plan's todo list as evidence — is counted as one of that doc's own open todos. Measured live 2026-08-02
  across the full `assigned_vm: NA` + `status ∈ {active, open}` population (356 deduped docs): inventory reports 1,317
  open todos, the real count is 1,310 — 7 phantom todos across 2 docs, both in the `ao` tranche. Small in aggregate
  (0.5%) but not harmless per-doc: `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` reports **5 open
  todos when it genuinely has 0** (both its real todos are `- [x]` shipped; all 5 matches are the upstream plan's todos
  quoted in a code block), which makes it read as the tranche's second-largest open doc and masks that it is a
  completion/archival-review candidate. `check_na_corpus_ratchet.py` imports the same population helper, so the
  baselined `max_na_open_todos` figure carries the same overcount — the ratchet is measuring a number 7 higher than
  reality. Same bug class as the two membership/parsing defects this script's own module docstring already records
  (multi-line YAML values, `* [ ]` star bullets): a regex sweep over markdown that does not model markdown structure.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, na-eligibility-audit, ratchet, checkbox-parsing, markdown-fence, measurement-correctness]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md,
    /plans/archive/2026_08/issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md,
    /plans/active/issues/na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md,
  ]
created: "2026-08-02"
author: unknown
last_updated: "2026-08-02"
parent_epic: plan_hygiene_master
priority: P2
source:
  "/na-eligibility-audit tranche=ao, autonomous scheduled run 2026-08-02 — found while completeness-checking each
  in-scope doc's reported verdict count against `grep -cE '^- \\[ \\]'` per the skill's Phase-1 verification rule"
assigned_vm: planning # reclassified NA -> planning 2026-08-02 (na-eligibility-audit, infra tranche) — conflict-check CLEAR
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
sequential: true # 2026-08-10 (plan_reconciler infra shard, agt-716973): todo 3 explicitly must not run before
# todos 1+2 land (own text: "DO NOT RUN until todos 1+2 have landed") but had no machine enforcement -- see Progress Log
context_scope:
  [
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    scripts/plan-hygiene/check_na_corpus_ratchet.py,
    scripts/plan-hygiene/check_todo_format.sh,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
---

# NA inventory counts fenced-code-block checkboxes as real open todos

## What I found

`scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` computes a doc's open-todo count as:

```python
CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[ \]", re.MULTILINE)
...
open_todos = len(CHECKBOX_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
```

The regex is correct for its stated purpose (it already handles the `* [ ]` star-bullet variant that burned a previous
sweep). The gap is that it runs over the **entire document body**, including fenced code blocks. An issue doc that
quotes another plan's todo list as evidence — a normal, encouraged authoring pattern in this corpus — has every quoted
`- [ ]` line counted as one of its own open todos.

## Measurement (live, 2026-08-02, full NA population)

Re-derived over the same population the script itself selects (`assigned_vm: NA` + `status ∈ {active, open}`, both doc
trees), deduping the multi-tranche rows:

| Metric                                  | Count |
| --------------------------------------- | ----- |
| NA docs (deduped)                       | 356   |
| Open todos as reported by the inventory | 1,317 |
| Open todos excluding fenced regions     | 1,310 |
| **Phantom (counted inside a fence)**    | **7** |

Both affected docs are in the `ao` tranche:

| Doc                                                                       | Reported | Real  | Phantom |
| ------------------------------------------------------------------------- | -------- | ----- | ------- |
| `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`  | 5        | **0** | 5       |
| `issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md` | 3        | 1     | 2       |

## Why it matters

- **It misclassifies a doc's lifecycle stage.** `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` has
  both of its real todos `- [x]` (shipped: `agent-orchestrator@13a5dd8` + `@bd522d0` + `@c34b560`). Reported as 5 open
  todos it looks like the second-largest open doc in the `ao` tranche; at its real 0 it is a completion/archival-review
  candidate whose only residual is a prose hypothesis. Every audit that sorts or triages by open-todo count sees the
  wrong doc at the wrong position.
- **The ratchet inherits it.** `check_na_corpus_ratchet.py` sums `r["open_todos"]` over the same records, so the
  baselined `max_na_open_todos` in `scripts/plan-hygiene/na_corpus_baseline.yaml` is pinned to an inflated number. A
  future genuine 7-todo reduction could be silently absorbed as "no change" against the phantom headroom.
- **It is the third instance of the same bug class in this one script**, which its own module docstring already warns
  about twice (a multi-line YAML `assigned_vm` value; a `* [ ]` star bullet). Both prior fixes were "make the regex
  smarter"; the durable fix here is to stop scanning regions that markdown says are not content.

## Recommended fix

Strip or skip fenced regions before counting. A minimal, dependency-free pass (toggle a `in_fence` flag on any line
matching `^\s*```` `) is sufficient and matches how the count is already consumed — this does not need a markdown
parser. Apply it in `generate_na_doc_tranche_inventory.py` so every consumer (the inventory, the ratchet, and the
`/na-eligibility-audit` skill's Phase-0 split) inherits the correction from one place, rather than each re-deriving it.

**A second consumer is already confirmed affected, not just suspected.** `scripts/plan-hygiene/check_todo_format.sh`
independently reports the exact same three fenced lines as malformed todos:

```
plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md:66: - [ ] [BACKEND]  P1. Fix the messari_basic subgraph query ...
plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md:67: - [ ] [DATA]     P1. Live-test whether 2022-era pool metadata is still indexed ...
plans/active/issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md:68: - [ ] [BACKEND]  P1. Re-backfill dex_pool_state for curve/sushiswap/velodrome_v2/trader_joe_v2 ...
```

Those lines are a verbatim quote of the UPSTREAM plan's todo list (double-spaced for alignment inside the block), so the
"malformed" verdict is a false positive from the same root cause — the checker is linting quoted evidence as if it were
this doc's own todos. That makes this a shared plan-hygiene parsing gap across at least two gates, not a single-script
bug, which is why the fix belongs in a shared helper rather than patched per-script. The same
`CHECKBOX_RE`-over-whole-body shape likely also exists in `count_open_tasks.py`,
`generate_ag_closeout_audit_candidates.py`, and `generate_context_scope_inventory.py` — grep as part of the fix.

## Todos

- [ ] [SCRIPT] P2. Make `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py`'s open-todo count skip `- [ ]` lines
      inside fenced code blocks. **Done when**: a fresh `--tranche ao --json` run reports `open_todos: 0` for
      `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` and `open_todos: 1` for
      `issues/ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`, the corpus total drops 1317 → 1310, and
      a unit test pins the fenced-vs-real distinction so this bug class cannot return a fourth time. (repo:
      unified-trading-pm)
- [ ] [SCRIPT] P2. Apply the same fence guard to `scripts/plan-hygiene/check_todo_format.sh`, which is **confirmed** to
      false-positive on the identical 3 quoted lines (evidence in "Recommended fix" above), then grep the remaining
      sibling counters (`count_open_tasks.py`, `generate_ag_closeout_audit_candidates.py`,
      `generate_context_scope_inventory.py`) for the same whole-body-`CHECKBOX_RE` shape. Prefer one shared
      fence-stripping helper over N per-script patches. **Done when**: `check_todo_format.sh` no longer flags
      `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md:66-68`, and each remaining script is either fixed
      or confirmed not to count checkboxes, with the disposition recorded here. (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. **DO NOT RUN until todos 1+2 have landed** (ordering NOT machine-enforced — no `sequential:` flag):
      re-run `check_na_corpus_ratchet.py --update-baseline` so `na_corpus_baseline.yaml`'s `max_na_open_todos` reflects
      the corrected count instead of the inflated one, and note the old → new numbers in the commit message (a baseline
      MOVE for a measurement fix, not a laundered regression). **Done when**: the baseline matches a fence-aware count.
      (repo: unified-trading-pm)

## Plan-destination note (resolved 2026-08-02)

Filed `assigned_vm: NA` per the ask-before-creating HARD RULE's default (this run is autonomous, no operator present to
answer). All three todos are bounded and worker-determinable — named files, named done-when, no design call — so this is
a clean AO-dispatch candidate the operator can flip to `assigned_vm: planning` without further scoping. Flagged rather
than flipped at filing time, because choosing the destination is the operator's call, not the auditor's — resolved below
by a subsequent `/na-eligibility-audit` pass applying that same self-assessment.

## Progress Log

- **2026-08-02** — Filed by `/na-eligibility-audit` (tranche `ao`, autonomous scheduled run). Found via the skill's
  Phase-1 completeness rule (compare `grep -cE '^- \[ \]' <doc>` against the reported per-doc verdict count): the two
  affected docs' counts could not be reconciled with their actual verdict sets, and the discrepancy traced to quoted
  checkboxes inside code fences rather than to an under-read. Measured corpus-wide before filing (356 docs) so the blast
  radius is a number, not an estimate.
- **na-eligibility-audit 2026-08-02 (infra tranche, dispatch agt-fe5e17)**: RECLASSIFY — `assigned_vm: NA -> planning`.
  All 3 todos are bounded/worker-determinable (named files, exact done-when checks, fix approach already decided in this
  doc's own "Recommended fix" section) per the dispatch-scope-eligibility bar
  (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § 5). Conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) run against: (a) active
  `assigned_vm: planning` docs in `parent_epic: plan_hygiene_master` — none claim the fenced-code-block checkbox-count
  bug specifically (grepped `fenced`/`CHECKBOX_RE`/`in_fence` corpus-wide; the only hits are unrelated docs that merely
  cite this doc's own two example filenames); (b) no sibling batch/finalize doc drafted this run; (c)
  `infra_consolidated_closeout_2026_07_25.md` mentions `generate_na_doc_tranche_inventory.py` but for a disjoint bug
  (asset_group-vs-parent_epic tranche-membership mistagging, not checkbox counting). Clear — no conflict found. Also
  corrected `execution_scope: local-only -> orchestrator-agent` (was stale for a now-dispatchable doc). No finalize-plan
  companion authored: `doc_type: issue`, structurally exempt from the finalize-plan-coverage rule
  (`check_finalize_plan_coverage.py` only globs `plans/active/*.md` plan docs).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — added `check_todo_format.sh`, confirmed affected
  by the same fence-blindness bug per the doc's own "Recommended fix" evidence and todo 2.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **2026-08-10 (plan_reconciler infra shard, agt-716973)**: added `sequential: true` to frontmatter. Todo 3's own text
  already stated an ordering dependency on todos 1+2 ("DO NOT RUN until... ordering NOT machine-enforced") but no
  `sequential:`/`depends_on`+`gate_on_depends` backed it — per CLAUDE.md, same-plan todos run concurrently by default,
  so AO could have dispatched todo 3 (bake the corrected baseline) before todos 1+2 shipped (the fence-parsing fix),
  baking in the inflated baseline the fix exists to correct. Todo 3's own warning is now machine-enforced.
