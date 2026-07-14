---
doc_type: issue
title: unified-trading-pm QG RED — F47 verdict-matrix regression (21 unbuildable venue cells), blocks all PM pushes
summary: |
  test_capability_verdict_matrix.py::test_f47_unbuildable_venue_cells_are_not_available fails deterministically on
  current unified-trading-pm HEAD (confirmed on a byte-identical clean tree, single-worker, no xdist): 21 verdict-
  matrix cells report venue_buildable=False, including a suspicious generic venue id 'fx' rather than a specific
  named venue. The test's own docstring says Phase V (unified-api-contracts commit 7565c0cb, 2026-07-09) wired 9
  slot-token-unwired venues into KNOWN_VENUE_TOKENS specifically to make this assertion hold (zero unbuildable
  cells) — so either a later UAC commit re-introduced unwired venues, or eligible_venue_ids/fixture data upstream
  is producing a malformed venue id ('fx' looks like fixture/placeholder data, not a real venue name). This blocks
  quality-gates.sh for EVERY unified-trading-pm push, not just ones touching venue registries. Discovered because a
  prior "PASSED" QG round for this exact HEAD only ran a 6-test fast-path smoke subset via the .qg_content_sentinel
  unchanged-tree skip — it never actually re-validated the full suite, so this had already regressed silently
  before I ever touched anything.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts]
scope: [engineer]
tags: [qg-red, capability-verdict-matrix, f47, venue-tokens, repo-blocker]
related:
  [
    plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    tests/unit/test_capability_verdict_matrix.py,
    unified_api_contracts/internal/architecture_v2/venue_tokens.py,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source: slot-13, discovered while shipping an unrelated click-floor pip-audit fix, 2026-07-13
assigned_vm: planning
resolved_by: unified-api-contracts@c138145b
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: unclear
depends_on: []
---

## What I found

`.venv/bin/python -m pytest tests/unit/test_capability_verdict_matrix.py::test_f47_unbuildable_venue_cells_are_not_available -q -p no:xdist`
fails deterministically:

```
AssertionError: found 21 F47 unbuildable-venue cell(s) — add each venue's alnum-folded slot token to
KNOWN_VENUE_TOKENS in unified_api_contracts/internal/architecture_v2/venue_tokens.py
assert 21 == 0
 +  where 21 = len([{'available_algos': [], 'blocked_algos': [{'algo': 'ADAPTIVE_TWAP', 'reason': "venue 'fx' is
     not a buildable v2 slot ...SLOT) — cell demoted from AVAILABLE."}, ...], ...])
```

Verified this is NOT caused by my own diff: my only staged change was a one-line click-floor bump
(`workspace-constraints.toml`) plus this issue doc — `git stash` reported "No local changes to save" (my change was
already committed as the tip commit), and the failure reproduces identically on that exact committed HEAD. I did not
touch `tests/`, `unified-api-contracts`, or anything venue-related.

The venue id `'fx'` in the failure output looks like generic/placeholder fixture data rather than a specific named venue
(contrast with real venue names like `kraken`, `bitfinex` that Phase V explicitly wired in per
`unified-api-contracts@7565c0cb`). This makes the fix ambiguous: it could mean (a) `KNOWN_VENUE_TOKENS` is genuinely
missing 21 real venue tokens that should be added, or (b) upstream `eligible_venue_ids` construction is producing
malformed/placeholder venue ids that should never have reached the verdict matrix in the first place. I did not attempt
either fix myself — this needs someone with venue-registry context, and blindly adding 'fx' (and 20 similar entries) to
`KNOWN_VENUE_TOKENS` risks masking a real data-quality bug per option (b).

## Why this matters

- **Blocks every unified-trading-pm push** — this is a hard `quality-gates.sh` test failure, not a warn-only check.
- **Silently regressed** — the QG's own `.qg_content_sentinel` fast-path (skip full suite on unchanged tree) let a prior
  run report green while only running 6 tests, masking this for an unknown period. Worth a follow-up: should the
  content-sentinel fast-path exclude cross-repo integration tests like this one that depend on a live path dependency
  (`unified-api-contracts`) whose content isn't captured by PM's own tree-content hash?

## Todos

- [x] ✅ [BACKEND] P1. Root-cause the 21 unbuildable cells — RESOLVED by another slot, `unified-api-contracts@c138145b`
      ("fix(registry): add fx to KNOWN_VENUE_TOKENS + regenerate capability-verdict-matrix + venue-coverage-report").
      `fx` turned out to be a genuine (if oddly-named) venue token gap in the registry, not malformed fixture data —
      option (a) from the original write-up.
  - [x] ✅ [VERIFY] P0. `test_f47_unbuildable_venue_cells_are_not_available` passes with `-p no:xdist` on current HEAD
        (re-verified 2026-07-13, slot-13, after resuming this task).
- [x] ✅ [BACKEND] P2. Consider excluding cross-repo path-dependency-sensitive tests from the `.qg_content_sentinel`
      fast-path, or hashing the path-dependency's content into the sentinel too — this let a real regression hide behind
      a false-green for an unknown window. — **DONE, slot-13, `unified-trading-pm@11055b603cd6`.** Took the hashing
      option: added `_qg_editable_sibling_hash()` (`scripts/quality-gates-base/qg-common.sh`), which discovers every
      editable-installed workspace sibling via its dist-info `direct_url.json` (standard pip/uv metadata —
      `{"url":"file://...","dir_info":{"editable":true}}`, no jq dependency added) and folds each sibling's committed
      HEAD + uncommitted tracked diff into the content hash. Wired into both `_qg_content_hash()` implementations
      (`base-service.sh`, `base-library.sh` — every repo's `quality-gates.sh` sources one of these), so this closes the
      gap fleet-wide, not just for PM. Verified the fix actually changes the hash on a live uncommitted edit to
      `unified-api-contracts/.../venue_tokens.py` (reverted after verifying, no residual diff left in the sibling); full
      `quality-gates.sh` green afterward with the change wired in (multiple runs across 3 mid-flight rebases onto
      concurrent peer pushes on this hot repo — each re-verified with a fresh QG run before its push attempt).
