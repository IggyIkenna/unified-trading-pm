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
author: unknown
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/quality_gates/check_doc_body_links.py,
    scripts/quality_gates/doc_body_link_baseline.yaml,
    /plans/archive/2026_07/docs_retrieval_layer_reconcile_2026_07_23.md,
  ]
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

- [x] [SCRIPT] P1. ✅ **SCOPE DECIDED (round5 ao investigation) — go with P2 (narrow, below), not this broad option, for
      the FIRST cut.** The doc's own blocker was "needs the new violation count measured before anyone can say how large
      the baseline-seed will be" — measured directly: a read-only scan reusing `check_doc_body_links.py`'s own
      `_resolve()`/`_is_checkable()` logic (imported, not reimplemented) against a second regex matching backtick-quoted
      `.md`/`.mdc` paths found **14,729 distinct citations corpus-wide, 3,726 unresolved** — a baseline addition roughly
      3× the size of the ORIGINAL markdown-link checker's entire violation count at seed time, and a material fraction
      is placeholder/illustrative noise (angle-bracket placeholders like `<archetype>.md`/`<NN-section>/<doc>.md`,
      generic example filenames inside `no-summary-docs.mdc`'s own illustration list like `ARCHITECTURE.md`/`DESIGN.md`)
      that a real implementation would need real placeholder-exclusion logic to avoid drowning the baseline in false
      positives — genuinely sizeable, exactly as flagged, not a same-day extension. Left unchecked as an implementation
      task (still real, bounded follow-up work, not a design question) — see the codex-scoped item below for the
      recommended first landing.
- [x] [SCRIPT] P2. ✅ **Implemented** — only match backtick-paths that begin with `codex/` or `/codex/` (the
      retrieval-layer-critical subset this skill's own charter cares about most), leaving plans-corpus and other
      backtick citations for a later pass (the P1 item above, once its placeholder-exclusion logic exists). **Measured
      2026-08-08 (round5 ao investigation)**: only 2,254 codex/-prefixed backtick citations exist corpus-wide, of which
      just **14 are unresolved** — several of those are themselves angle-bracket/ellipsis placeholders (e.g.
      `codex/09-strategy/architecture-v2/archetypes/<archetype>.md`, `/codex/<NN-section>/<doc>.md`,
      `codex/.../block-list.md`), so the real broken-citation count needing a genuine fix (not just a baseline entry) is
      likely closer to 6-8. This confirms the doc's own framing — "smaller, faster to land" — with real numbers: a
      same-day-sized change, not an open scope question. Reuse `_resolve()` unchanged; seed
      `doc_body_link_baseline.yaml` via `--update-baseline` immediately after landing (do not ship zero-tolerance day
      one, matching how the original markdown-link checker itself was seeded 2026-07-23). **Shipped 2026-08-08**:
      `_BACKTICK_CODEX_RE` added to `check_doc_body_links.py` (`` `(/?codex/[^`\s*]+\.(?:md|mdc))` `` — the `*`
      exclusion is a real fix found during implementation, not anticipated by the investigation: a wildcard-glob
      illustration `` `codex/**.md` `` in `cross-reference-path-convention.md` matched the naive pattern and crashed
      `_resolve()`'s archive-fallback `glob()` on a bare `**` segment; excluding `*` from the path charclass avoids it
      without touching `_resolve()`). Live corpus scan post-landing found 16 unresolved (close to the 14 measured, two
      more docs landed since the investigation) — baseline seeded via `--update-baseline` (28 total `known_broken`
      entries, +17 net new vs. the pre-existing 11 markdown-link entries) per this item's own instruction; the
      individual unresolved citations are unfixed debt now tracked in the baseline, not silently swept. 7 new unit tests
      added covering resolve/broken/non-codex-scope/fence-exclusion/glob-safety.
- [x] ✅ [DOCS] P3. Regardless of which script fix is chosen: once shipped, re-run `/docs-reconcile`'s Phase 0/1 against
      the newly-widened checker to catch whatever real breakage the wider scan surfaces. — Re-ran 2026-08-10 (slot-23
      infra): full-corpus Phase 0 green (2045 docs, zero NEW broken inline links); the 24-entry baseline triaged — 1
      stale dropped (`--update-baseline`, 24→23), ~10 placeholder/illustrative noise (the P1 placeholder-exclusion
      path), 13 genuine dead refs already tracked in `docs_reconcile_remaining_broken_links_2026_08_02.md`.

## Progress Log

- 2026-08-02 (docs_reconciler, dispatch agt-0b4ee1): filed during the autonomous docs-reconcile sweep. 12 concrete
  instances of exactly this blind spot were hand-verified and fixed in the same sweep (unified-trading-pm@809a28c97)
  despite the checker not catching them — proof this is a real, exploitable gap, not a theoretical one.
- **na-eligibility-audit 2026-08-02** (infra tranche, dispatch agt-fe5e17): KEEP-NA, valid — the doc's own "Options"
  present P1 (broad `_LINK_RE` extension) and P2 (narrower `codex/`-only first cut) as genuine alternatives, not a
  checklist, and P1 is explicitly flagged as needing a live violation-count measurement before its baseline-seed size is
  known. Choosing between them is a real scope/risk judgment call on a change to shared QG infra, not a bounded,
  worker-determinable outcome — stays NA.
- **context-scout 2026-08-03**: refreshed context_scope (3 entries) — added
  `/plans/archive/2026_07/docs_retrieval_layer_reconcile_2026_07_23.md`, the checker's own origin doc named in this
  doc's "Why this matters" section.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-affirmed (first `ao`-tranche
  marker on this doc; prior marker was the `infra` tranche, 2026-08-02, same verdict). The doc's own "Options" still
  present a genuine P1-vs-P2 scope/risk fork on a shared QG-infra checker with no live-violation-count measurement taken
  yet — a real judgment call, not a bounded worker-determinable outcome. Content unchanged since the last marker.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY → `assigned_vm: planning`. The prior
  "genuine P1-vs-P2 scope/risk fork" that kept this KEEP-NA is now resolved — the 2026-08-08 round5 ao investigation
  measured the P2 (narrow, `codex/`-prefix-only) option live (2,254 candidates, 14 unresolved, several of those
  themselves placeholders) and explicitly closed the scope question ("no longer an open scope question... a
  same-day-sized change"). The remaining 2 open items (`[SCRIPT] P2` implement + seed the baseline; `[DOCS] P3` re-run
  `/docs-reconcile` after) are both bounded implementation/verification work with a concrete plan already written out
  in-doc, no remaining judgment call. Conflict-check clear: grepped `plans/active/*.md` for
  "backtick"/`codex/.*backtick`/this doc's own filename — the only hits are unrelated docs listing this issue in a
  "referenced, discoverability" digest (`ag_closeout_audit_rollout_2026_07_25.md`,
  `ao_satellite_ao_dispatch_batch3_2026_07_31.md`, `cross_cutting_consolidated_closeout_2026_07_25.md`,
  `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md`, `tradfi_phase_d_terminal_gate_2026_07_24.md`), none claim
  the implementation itself. `execution_scope: local-only → orchestrator-agent`, `assigned_role: infra` (unchanged,
  already correct). Companion gated finalize:
  `doc_body_link_checker_blind_to_backtick_citations_2026_08_02_finalize_2026_08_08.md`.
- **2026-08-08 (slot-28, infra worker)**: P2 shipped. Added `_BACKTICK_CODEX_RE` to
  `scripts/quality_gates/check_doc_body_links.py` and wired it into `_extract_links()`, reusing `_is_checkable()`/
  `_resolve()` unchanged. Found + fixed one real bug surfaced by the widened scope during implementation (not
  anticipated by the investigation): a wildcard-glob illustration `` `codex/**.md` `` in
  `/codex/11-project-management/cross-reference-path-convention.md` matched the naive backtick pattern and crashed
  `_resolve()`'s archive-fallback `Path.glob("**/<name>")` call on a bare `**` path segment — fixed by excluding `*`
  from the backtick path charclass (a real citation never contains one). Added 7 unit tests in
  `test_check_doc_body_links.py` (resolve / broken / non-codex-scope-excluded / fence-excluded / leading-slash /
  glob-safety). Seeded `doc_body_link_baseline.yaml` via `--update-baseline` immediately after landing (28
  `known_broken` entries total, +17 net new from the widened backtick scan) — matches this item's own instruction to
  absorb pre-existing debt rather than ship zero-tolerance day one. `[DOCS] P3` (re-run `/docs-reconcile` against the
  widened checker) is left open — different `[TAG]`/craft, out of this task's scope.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **2026-08-10 (slot-23, infra worker)**: `[DOCS] P3` executed — re-ran `/docs-reconcile` Phase 0/1 against the
  P2-widened checker. Phase 0: full-corpus `check_doc_body_links.py` green (2045 docs, zero NEW broken inline links
  beyond the ratchet). Phase 1.5 triage of the 24-entry `doc_body_link_baseline.yaml`: 1 entry STALE (the
  `sports-canonical-league-cup-registry` citation was removed from
  `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — registry work now tracked as plan
  todos, lines 206/468) → dropped via `--update-baseline` (ratchet 24→23); ~10 entries are angle-bracket/ellipsis
  placeholders or audit self-classified FALSE-POSITIVEs (honest noise, the P1 placeholder-exclusion path); the remaining
  13 genuine dead references (`/codex/04-architecture/README.md` ×4 +
  `/codex/04-architecture/batch-live-architecture.md`, `/codex/06-coding-standards/README.md` ×3,
  `/codex/06-coding-standards/ui-testing-layers.md`, `/codex/09-strategy/architecture-v2/README.md`,
  `/codex/14-customer-journeys/shared-core/strategy-version-governance.md`, `/codex/README.md`, `mega_audit` R14) are
  ALREADY open todos in `docs_reconcile_remaining_broken_links_2026_08_02.md` — no new findings to file. Confirms the
  widened scan surfaces no NEW breakage beyond what P2 baselined + tracked.
