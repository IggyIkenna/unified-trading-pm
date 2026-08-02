---
doc_type: issue
title:
  check_doc_body_links.py's link-extraction regex only matches [text](path) markdown links, missing the corpus's other
  equally-common backtick-citation convention
summary: >-
  check_doc_body_links.py exists specifically to close the "frontmatter checker never looked at doc bodies" gap
  (2026-07-23), but its `_LINK_RE` regex only matches real markdown-link syntax `[text](path)`. This corpus's other
  dominant cross-reference convention -- a bare backtick-quoted path in prose, e.g. "SSOT: `codex/foo.md`" / "Plan:
  `plans/active/bar.md`" -- is structurally invisible to it (no `[...]()` wrapper for the regex to match). Quantified
  corpus-wide (codex/ + cursor-rules/ + agents/ + .cursor/rules/): 6409 backtick-path citations vs 5121 real markdown
  links -- the backtick style is MORE common, not an edge case. This means roughly half the corpus's actual
  cross-references are unchecked for existence by any automated gate, and the checker's "zero NEW broken" clean passes
  give false confidence about that other half. Found by 2026-08-02 docs-reconcile; NOT auto-fixed (extending detection
  scope is a consequential change to shared QG infra needing an immediate baseline-seed of however many newly-detected
  violations surface -- out of scope for a doc-content fix pass). 12 concrete instances of this exact blind spot
  (backtick citations inside cursor-rules/*.mdc pointing at stale/moved targets) WERE hand-verified and fixed in this
  same sweep despite the checker's blindness (unified-trading-pm@809a28c97) -- this issue is about the checker's
  coverage gap itself, not those 12 fixes.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, quality-gates, retrieval-layer, broken-links, coverage-gap]
related: []
created: 2026-08-02
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
resolved_by:
locked_by:
locked_since:
context_scope: [scripts/quality_gates/check_doc_body_links.py, scripts/quality_gates/doc_body_link_baseline.yaml]
supersedes:
superseded_by:
depends_on:
source: [docs-reconcile autonomous sweep, dispatch agt-0b4ee1, 2026-08-02]
assigned_role: infra
drift_direction: advance-code
---

# check_doc_body_links.py is blind to backtick-citation links

## Evidence

`scripts/quality_gates/check_doc_body_links.py:51`:

```python
_LINK_RE = re.compile(r'\[[^\]\n]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
```

This ONLY matches `[text](path)`. It does not, and structurally cannot, match a line like:

```
Semver rule: `unified-trading-pm/cursor-rules/core/semver-v1-hardening.mdc`
```

— which was a real, broken (wrong-tree) citation found by hand during the 2026-08-02 docs-reconcile sweep, invisible to
`check_doc_body_links.py` despite `**/*.mdc` being in its scanned `DOC_TREES`. Confirmed by direct count (see the
sweep's scratch notes, reproducible via `grep -rEo` for both patterns across
`codex/ cursor-rules/ agents/ .cursor/rules/`):

| Pattern                                           | Count |
| ------------------------------------------------- | ----- |
| `[text](path.md\|mdc)` (real markdown links)      | 5121  |
| `` `path.md\|mdc` `` (backtick-quoted bare paths) | 6409  |

## Why this matters

The whole point of `check_doc_body_links.py` (per its own origin, `docs_retrieval_layer_reconcile_2026_07_23.md`) was
closing the gap where a dead markdown link (link text, then the target path in parens) inside a doc's prose was
invisible to every existing gate. It closed that gap for ONE citation style and left the other, more common style
exactly as invisible as before. A "zero NEW broken" clean pass from this checker is not evidence the corpus's
backtick-citations are healthy — it never looked at them.

## What this is NOT

Not a bug in the checker's existing logic for what it DOES check (frontmatter refs + markdown links are both handled
correctly, per the 2026-08-02 sweep's Phase 0/2 verification). This is a scope gap: an entire citation convention this
corpus actually uses was never brought into the checker's purview.

## Options

- [ ] [SCRIPT] P1. **Extend `_LINK_RE` (or add a second regex pass) to also match backtick-quoted bare paths ending in
      `.md`/`.mdc`**, reusing the existing `_resolve()` fallback chain (doc-dir-relative -> PM-root-relative ->
      `plans/archive/**` basename fallback) unchanged. Immediately follow with `--update-baseline` to seed whatever
      pre-existing backtick-citation breakage surfaces as tolerated debt (mirroring how the original markdown-link
      checker was seeded 2026-07-23) — do NOT ship this as a zero-tolerance gate on day one, that would immediately
      hard-block every commit touching a doc with pre-existing backtick-citation rot. [Likely the right long-term fix,
      but sizeable: needs the new violation count measured before anyone can say how large the baseline-seed will be.]
- [ ] [SCRIPT] P2. **Alternative — narrower first cut**: only match backtick-paths that begin with `codex/` or `/codex/`
      (the retrieval-layer-critical subset this skill's own charter cares about most), leaving plans-corpus and other
      backtick citations for a later pass. Smaller, faster to land, doesn't fully close the gap.
- [ ] [DOCS] P3. Regardless of which script fix is chosen: once shipped, re-run `/docs-reconcile`'s Phase 0/1 against
      the newly-widened checker to catch whatever real breakage the wider scan surfaces.

## Progress Log

- 2026-08-02 (docs_reconciler, dispatch agt-0b4ee1): filed during the autonomous docs-reconcile sweep. 12 concrete
  instances of exactly this blind spot were hand-verified and fixed in the same sweep (unified-trading-pm@809a28c97)
  despite the checker not catching them — proof this is a real, exploitable gap, not a theoretical one.
- **na-eligibility-audit 2026-08-02** (infra tranche, dispatch agt-fe5e17): KEEP-NA, valid — the doc's own "Options"
  present P1 (broad `_LINK_RE` extension) and P2 (narrower `codex/`-only first cut) as genuine alternatives, not a
  checklist, and P1 is explicitly flagged as needing a live violation-count measurement before its baseline-seed size is
  known. Choosing between them is a real scope/risk judgment call on a change to shared QG infra, not a bounded,
  worker-determinable outcome — stays NA.
