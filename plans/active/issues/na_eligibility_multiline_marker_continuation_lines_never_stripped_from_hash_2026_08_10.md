---
doc_type: issue
title:
  "/na-eligibility-audit's body_content_hash strips only the FIRST line of its own multi-line verdict marker — every
  substantive (multi-line) marker permanently breaks incremental_skip for that doc from the moment it's written"
summary: >-
  `generate_na_doc_tranche_inventory.py`'s `_VERDICT_MARKER_LINE_RE` is `^[^\n]*\*\*(?:...) \d{4}-\d{2}-\d{2}[^\n]*\n?`
  with `re.MULTILINE` — `[^\n]*` cannot cross a newline, so this only strips the SINGLE line carrying the
  `**na-eligibility-audit YYYY-MM-DD**` date stamp, never the indented continuation lines that follow it. Nearly every
  real verdict marker in this corpus is multi-line (a one-line "KEEP-NA, valid" with no reasoning is the exception, not
  the norm — every example sampled across the 2026-08-10 tradfi-tranche run's 19 touched docs was 2-6 lines). The moment
  a multi-line marker is written with a declared `[body-hash:H]` (H = hash of the body BEFORE that marker existed), the
  file now contains that marker's own continuation lines, which are NOT stripped by future hash computations — so
  recomputing the hash even immediately after writing produces a DIFFERENT value than H, permanently (every later pass's
  "current body" includes these continuation lines forever, while the STORED hash never did). Empirically verified with
  a minimal repro (2 lines total of real content, 1 three-line marker): hash before marker written vs. hash recomputed
  immediately after writing that exact marker (with its own correct pre-write hash embedded) — different every time.
  This is a MORE GENERAL version of `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` (fixed
  via the "sibling-marker family" line-strip list) — that fix only strips a SINGLE line per marker occurrence for BOTH
  na-eligibility-audit's own markers and context-scout's, so it never actually fixed the self-inflicted half of the
  problem: an na-eligibility-audit marker's OWN continuation lines were never covered by that fix either, because the
  fix operates on the same single-line-only regex. Practical impact, measured live on the 2026-08-10 tradfi-tranche run:
  of 24 in-scope docs, essentially every doc carrying a substantive prior marker (most dated just 1 day earlier,
  2026-08-09) showed `incremental_skip: false` despite the hunter-confirmed verdict being unchanged in most cases — the
  incremental mode Phase 0 exists specifically to avoid is being defeated corpus-wide, every ~2-hour scheduled fire, for
  every doc that has ever received a real (multi-line) verdict. Not a correctness bug (no doc gets mis-verdicted; worst
  case is an unnecessary full Phase-1 re-read), but a significant, silently-compounding efficiency regression across all
  10 tranches that undermines the stated purpose of the whole incremental-diff mechanism.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    plan-hygiene,
    na-eligibility-audit,
    incremental-diff,
    false-positive,
    measurement-correctness,
    body-content-hash,
    efficiency,
  ]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/2026_08/issues/na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-10"
author: unknown
last_updated: "2026-08-10"
parent_epic: plan_hygiene_master
priority: P2
source:
  "/na-eligibility-audit tranche=tradfi, autonomous scheduled run 2026-08-10 (dispatch agt-a70469) — found while
  building a hash-computation helper (importing body_content_hash directly, not reimplementing it) to embed correct
  [body-hash:...] tags in this run's own new markers; noticed recomputed hashes never matched prior markers' stored
  values even on docs with zero real content drift, traced to the root cause below"
assigned_vm: planning
resolved_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [/cursor-configs/skills/na-eligibility-audit/SKILL.md, scripts/plan-hygiene/generate_na_doc_tranche_inventory.py]
---

# na-eligibility-audit's body_content_hash never strips a multi-line marker's own continuation lines

## What I found

While computing hashes for this run's own new verdict markers (via a small helper importing `body_content_hash()`
directly from `generate_na_doc_tranche_inventory.py`, not a reimplementation), I noticed that recomputing the hash of a
doc immediately after adding a marker — even one whose declared `[body-hash:...]` was computed correctly, one step
earlier, from the exact same body — never matches. Traced to `_VERDICT_MARKER_LINE_RE`:

```python
_VERDICT_MARKER_LINE_RE = re.compile(
    r"^[^\n]*\*\*(?:" + _BOOKKEEPING_MARKER_ALTERNATION + r") \d{4}-\d{2}-\d{2}[^\n]*\n?",
    re.MULTILINE,
)
```

`[^\n]*` cannot cross a newline. In `re.MULTILINE` mode, `^` anchors to the start of each line, so this pattern only
ever matches — and strips — the ONE line that carries the `**na-eligibility-audit YYYY-MM-DD**` (or
`**context-scout YYYY-MM-DD**`) date stamp. Every indented continuation line that follows (the actual reasoning/evidence
prose, which is most of a real marker's content) is left untouched in the "stripped body" used for hashing.

## Minimal repro

```python
body0 = "# doc\n\nSome real content.\n\n## Progress Log\n\n- 2026-08-01: doc created.\n"
h0 = body_content_hash(body0)  # e.g. 4db2e4d261ae0d92

marker1 = (
    f"- **na-eligibility-audit 2026-08-09** [body-hash:{h0}]: **KEEP-NA, valid --\n"
    "  a two-line continuation\n"
    "  explaining why.**\n"
)
body1 = body0 + marker1
h1 = body_content_hash(body1)  # c6b1510381d29128 -- DIFFERENT, despite h0 being h1's own declared "before" hash
assert h1 != h0  # true every time a marker has >1 line
```

The declared hash is only ever correct for the instant before the marker itself is written — the very next read of the
file (including THIS SAME run's own incremental-skip check on a future pass) already sees a body that includes the
marker's continuation lines, which the regex never strips.

## Why this is a superset of the already-filed context-scout issue

`na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` fixed the case where context-scout's OWN
single-line bookkeeping marker survived into the hash, by adding `"context-scout"` to `_BOOKKEEPING_MARKER_SKILL_NAMES`
so its line also matches the strip regex. That fix is correct as far as it goes (context-scout's marker genuinely is
always exactly one line), but it operates on the SAME single-line-only regex — so it never addressed
na-eligibility-audit's OWN markers' continuation lines, which is the dominant real-world case (nearly every substantive
verdict is multi-line; a bare one-liner with no reasoning is rare and was not observed once across the 19 markers this
run wrote).

## Measured impact (2026-08-10 tradfi-tranche run)

Of 32 candidate docs in Phase 0's tradfi inventory, 24 were flagged in-scope (`incremental_skip: false`). Of those, 17
carried a marker dated just 1 day earlier (2026-08-09) — and per this run's own Phase-1 hunters' full re-reads, the
overwhelming majority had ZERO real content drift since that marker (pure re-confirmations, several explicitly noting
"the ONLY intervening change is the context-scout line directly above" — i.e., THIS bug plus the already-partially-fixed
context-scout case compounding). The incremental-diff mechanism Phase 0 exists to provide is, in practice, close to a
no-op for any doc that has ever received a real audit pass — every scheduled fire re-reads close to the full candidate
population instead of only genuinely-changed docs.

## Recommended fix (not attempted here — shared script, concurrent sibling-tranche audits were actively running

against it during this session; a hasty regex change mid-run is not worth the risk)

Strip the WHOLE marker block, not just its first line — e.g. match from a line starting `- **<marker-name> YYYY-MM-DD**`
through to (but not including) the next line that either (a) starts a new top-level `- ` bullet at the same indentation,
or (b) is blank, or (c) is a markdown section header (`## `). A non-greedy `(?:\n(?:[ \t]+\S.*|\n))*` continuation-lines
clause appended to the existing pattern (matching only indented/blank continuation lines, stopping at the next
un-indented bullet or header) should cover the real corpus shape observed in this run — verify against a sample of the
~40+ existing multi-line markers across this corpus before shipping, since indentation/blank-line conventions were not
perfectly uniform in the docs this pass touched.

## Todos

- [x] ✅ [SCRIPT] P2. Fix `_VERDICT_MARKER_LINE_RE` (or replace with a proper multi-line-block strip) in
      `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` so a marker's full continuation-line span is excluded
      from `body_content_hash()`, not just its first line. Add a regression test asserting
      `body_content_hash(body_before_marker) == body_content_hash(body_before_marker + <the marker written with that exact hash>)`
      for a multi-line marker — this is the invariant that is currently violated. Verify against a sample of real
      multi-line markers already in the corpus (this run alone added 19 examples across `plans/active/tradfi_*` and
      `plans/active/issues/tradfi_*`) to confirm the new regex's stop condition doesn't over-strip into the NEXT bullet
      or under-strip a trailing continuation line. — unified-trading-pm@PENDING_SHA (extended `_VERDICT_MARKER_LINE_RE`
      with a `(?:[ \t]+\S[^\n]*\n?)*` continuation clause that stops at the first non-indented line — a blank line, a
      new top-level `- ` bullet, or a `## ` header — matching the corpus' observed marker-block convention; added
      `test_body_content_hash_stable_across_multiline_marker` asserting the exact invariant this todo calls for, incl. a
      sibling-marker-not-swallowed check)
- [ ] [SCRIPT] P3. Once fixed, spot-check a handful of docs with old (pre-fix) markers to confirm the NEXT
      na-eligibility-audit run against them correctly reports `incremental_skip: true` when no real content changed
      since — i.e. confirm the fix actually restores the intended corpus-wide skip rate, not just that the unit test
      passes.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-08-10 (na-eligibility-audit, tradfi tranche, dispatch agt-a70469): filed while building this run's own
  hash-computation helper; empirically verified via a minimal repro importing the real function (not a
  reimplementation). Not fixed this pass — shared script, concurrent sibling-tranche audits (observed: slot 29 running
  the `prediction` tranche concurrently) were actively invoking it during this session.
