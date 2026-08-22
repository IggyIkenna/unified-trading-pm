---
doc_type: issue
title: "na_marker_helper.py hardcodes the root PM-clone path -- forces every slot session to either violate the read-only root-clone guardrail or hand-roll a workaround"
summary: >-
  `scripts/plan-hygiene/na_marker_helper.py` (the sanctioned tool for appending a correctly-hashed
  na-eligibility-audit/context-scout verdict marker, built specifically to eliminate hand-computed-hash errors) has
  `PM = Path("/home/ubuntu/unified-trading-system-repos/unified-trading-pm")` as a module-level constant -- the
  ROOT PM clone, not whichever slot's checkout the caller is actually running from. Every slot session's
  RULES.md/CLAUDE.md contract says root-clone reads are READ-ONLY and all writes happen only inside the caller's
  own `.tabs/<N>/` slot -- so this script, as shipped, cannot be run directly from a slot session without either
  writing into the read-only root clone (a guardrail violation) or hand-rolling a per-session wrapper that
  monkey-patches the module's `PM`/`INVENTORY_SCRIPT` constants after import (what this issue's own discovery
  session did, disposably, in scratchpad -- not promoted, since the real fix belongs in the script itself). Its
  sibling scripts in the same directory (`generate_na_doc_tranche_inventory.py`, `check_na_corpus_ratchet.py`) do
  NOT have this problem -- both were run directly via relative paths from a slot cwd this same session and
  correctly operated against that slot's own checkout, confirming they already resolve paths dynamically rather
  than hardcoding the root.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, na-eligibility-audit, script, slot-safety, tooling-bug]
related:
  [
    /plans/active/issues/na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
parent_epic: plan_hygiene_master
created: "2026-08-18"
last_updated: "2026-08-18"
author: claude-code (na_eligibility_auditor, slot 28, DISPATCH_ID=agt-7e78e2, tranche=cross-cutting) -- found during
  /pre-compact's Step-1 loss audit
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    scripts/plan-hygiene/na_marker_helper.py,
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
source: >-
  na_eligibility_auditor dispatch agt-7e78e2, slot 28, 2026-08-17 -- discovered while writing 17 correctly-hashed
  verdict markers this same session: the sanctioned `append`/`batch` CLI could not be invoked directly without
  writing into the read-only root PM clone, so a disposable slot-scoped wrapper (monkey-patching `PM`/
  `INVENTORY_SCRIPT` after import) was used instead and never promoted, per the /pre-compact "don't dump a scratch
  tool as-is" guidance -- the real fix belongs in this file, not a wrapper around it.
---

# na_marker_helper.py hardcodes the root PM-clone path

## What was found

`scripts/plan-hygiene/na_marker_helper.py` line 36:

```python
PM = Path("/home/ubuntu/unified-trading-system-repos/unified-trading-pm")
```

This is a literal absolute path to the **root** PM clone. Every worker-lifecycle contract in this workspace
(`unified-trading-pm/agents/RULES.md` § 1, `/codex/05-infrastructure/per-tab-worktrees.md`) is explicit that root
clones are **READ-ONLY** for any dispatched session -- all writes happen only inside the caller's own
`.tabs/<slot>/` checkout. `na_marker_helper.py`'s `append_one()`/`main()` both resolve every target path as
`PM / rel_path` before writing, so invoking `append`/`batch` from a slot session as documented would write directly
into the root clone -- a guardrail violation -- not the slot's own checkout.

**This defeats the tool's own stated purpose.** Its own docstring explains it exists specifically to eliminate
hand-computed-hash errors (`body_content_hash()` must be byte-exact or Phase 0's incremental-skip detection breaks
silently). A slot session that can't safely invoke the sanctioned tool is pushed back toward the exact
hand-written-marker risk the tool was built to close.

**Confirmed NOT a problem for its sibling scripts.** This same session ran
`scripts/plan-hygiene/generate_na_doc_tranche_inventory.py --tranche cross-cutting --json` and
`scripts/plan-hygiene/check_na_corpus_ratchet.py`, both via relative paths from a slot cwd (`.tabs/28/unified-trading-pm`),
and both correctly read/reported against THAT slot's own checkout (438 docs / 1393 open todos, matching the
slot's live state, not the root clone's). So the fix is narrowly scoped to `na_marker_helper.py`'s own two
module-level constants (`PM`, `INVENTORY_SCRIPT`) -- it is the outlier, not the pattern.

## Workaround used this session (not promoted -- disposable, scratchpad-only)

A small wrapper script loaded `na_marker_helper.py` via `importlib`, then monkey-patched
`mod.PM = Path("<this slot's PM checkout>")` and `mod.INVENTORY_SCRIPT` to match before calling `append_one`/
`_load_inventory_module()`. This worked correctly (17/17 markers appended with verified-correct hashes) but is a
workaround, not a fix -- every future slot session hits the identical problem and would need to re-derive the same
wrapper from scratch, or worse, skip the tool and hand-write a marker (reintroducing the exact bug class the tool
exists to prevent).

## Todos

- [ ] [SCRIPT] P3. **Derive `PM` (and `INVENTORY_SCRIPT`) dynamically instead of hardcoding the root clone path.**
      The simplest correct fix: derive from the script's own location, e.g.
      `PM = Path(__file__).resolve().parents[2]` (this file lives at `<repo>/scripts/plan-hygiene/na_marker_helper.py`,
      so two `.parent`s up from the script's own directory is the repo root -- verify the exact depth against the
      real layout rather than assuming), matching however
      `generate_na_doc_tranche_inventory.py`/`check_na_corpus_ratchet.py` already resolve their own paths (read
      those first — do not invent a second convention). This makes the tool work correctly from ANY checkout
      (root clone for main/review sessions, any slot's `.tabs/<N>/` for a dispatched worker) with zero caller-side
      workaround needed. Done-when: `python3 scripts/plan-hygiene/na_marker_helper.py hash <rel_path>` run from two
      different checkouts (e.g. root clone and any slot) each report the hash of THAT checkout's own file content,
      never the other's; a unit test (or a documented manual repro) proves it.
- [ ] [SCRIPT] P3. **Audit whether any other script under `scripts/plan-hygiene/` has the same hardcoded-root-path
      pattern** -- this session only directly exercised 3 of the family (`generate_na_doc_tranche_inventory.py`,
      `check_na_corpus_ratchet.py`, `na_marker_helper.py`); the other importers named in
      `na_eligibility_body_hash_unstable_across_marker_appends_2026_08_17.md`'s summary
      (`check_extracted_checkbox_citation.py`, `generate_context_scope_inventory.py`,
      `generate_tranche_doc_inventory.py`) were not checked for this specific pattern. Done-when: each is confirmed
      clean or fixed the same way as the todo above.

## Progress Log

- **2026-08-18 (na_eligibility_auditor, dispatch agt-7e78e2, slot 28, via /pre-compact Step 1)**: filed. Full
  repro + the exact workaround used (not promoted) captured above so a future fix session does not have to
  re-derive either.
- **na-eligibility-audit 2026-08-18 (dispatch agt-4d9716, slot 19)**: RECLASSIFY (whole-doc) -- both open todos are
  bounded/deterministic with a cited existing pattern (sibling scripts in the same directory already resolve paths
  dynamically; explicit done-when criteria). Conflict-checked against the one other corpus hit for
  `na_marker_helper` (`cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md` items 3-4): that item audits this
  same file for a DIFFERENT, unrelated bug (hash/marker-parsing-logic reimplementation), not this hardcoded-path
  bug -- no claim overlap. Flipped `assigned_vm: NA -> planning`, `execution_scope: local-only -> orchestrator-agent`.
  Issue doc -- structurally exempt from the finalize-plan-coverage rule (`check_finalize_plan_coverage.py` only
  globs `plans/active/*.md`, not `plans/active/issues/`), so no companion finalize doc authored. Cross-cutting
  tranche audit.
- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
