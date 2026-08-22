---
doc_type: issue
title:
  body_content_hash() is not stable across repeated verdict-marker appends -- every same-day re-verify pass
  perpetually re-triggers Phase 0 "in scope" for docs that are actually already audited and unchanged
summary: >-
  `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py::body_content_hash()` is documented to be invariant to
  "verdict marker additions/updates" (its own docstring), but is measurably NOT: appending a new na-eligibility-audit
  marker leaves a residual blank-line delta in the hashed body (the leading blank-line separator between the new
  marker and the previous content/marker is stripped from neither occurrence cleanly), so the very next Phase 0 run
  sees a changed hash and re-flags an already-fully-audited, unchanged doc as "in scope". A SEPARATE bug compounds
  this: `_latest_verdict_marker()` breaks same-date ties by first-occurrence-wins (`date > best[0]`, strict), not
  last-occurrence-wins, so when 2+ markers share a date (the skill's own documented same-day "re-verify" pattern)
  the function can pick a STALE marker's hash to compare against even when a later, correct one exists in the same
  doc. Found live during a 2026-08-17 `na_eligibility_auditor` dispatch (tranche=prediction, DISPATCH_ID=agt-997289):
  all 10 prediction-owned "in scope" docs turned out to be false positives -- each had already been fully,
  correctly re-verified by an earlier same-day dispatch (~08:15 UTC) or, for one doc, 32 minutes earlier by a
  concurrent cefi-tranche worker -- confirmed via direct re-read of 4 of the 10 (the rest cross-checked via
  exhaustive grep) rather than blindly trusted. `body_content_hash()` is imported by at least 6 plan-hygiene scripts
  (`check_extracted_checkbox_citation.py`, `generate_context_scope_inventory.py`, `check_na_corpus_ratchet.py`,
  `generate_tranche_doc_inventory.py`, `na_marker_helper.py`, plus this file) -- this is shared, corpus-wide
  infrastructure, not a prediction-tranche-local issue.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags:
  [na-eligibility-audit, ag-closeout-audit, plan-hygiene, incremental-skip, body-content-hash, tooling-bug, script]
related:
  [
    /plans/active/na_docs_validity_and_ao_eligibility_audit_2026_07_26.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-17
last_updated: 2026-08-21
author: claude-code (na_eligibility_auditor, slot 14, DISPATCH_ID=agt-997289, tranche=prediction)
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
archive_exempt: true # 2026-08-21: 0 open todos after ruling D28 closed the sole remaining item, but this doc is the
  # standing diagnostic record for a shared, corpus-wide plan-hygiene tooling bug (body_content_hash instability)
  # cited by other audits (na-eligibility-audit, ag-closeout-audit) as the root-cause reference -- kept in place
  # rather than archived by this pass per the parent dispatch's explicit "do not archive yourself" instruction; a
  # future archival pass may still move it once it's no longer needed as a live citation target.
source: >-
  Live during the 2026-08-17 prediction-tranche na-eligibility-audit run. Phase 0 inventory
  (`generate_na_doc_tranche_inventory.py --tranche prediction --json`) reported all 10 prediction-owned in-scope docs
  as `incremental_skip: false` despite each already carrying a same-day (2026-08-17) verdict marker with a
  `[body-hash:...]` tag. Investigated by directly invoking `body_content_hash()` and `_latest_verdict_marker()`
  against live file content and specific git commits (see Progress Log for the exact repro).
context_scope:
  [
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
    scripts/plan-hygiene/na_marker_helper.py,
    scripts/plan-hygiene/check_na_corpus_ratchet.py,
  ]
depends_on: []
locked_by:
locked_since:
resolved_by: "0 open todos as of 2026-08-21 (D28 ruling closed the sole remaining item) -- flagged
  fully-resolved-for-archive; the physical archive move is deferred to a later pass (archive_exempt: true above),
  not performed by this chunk-8 dispatch per its own instruction not to archive."
drift_direction: advance-code
---

# body_content_hash() is not stable across repeated verdict-marker appends

## Confirmed repro (bug 1 -- residual blank-line delta)

Doc: `plans/active/prediction_phase_e_football_arb_live_2026_07_24.md`.

Commit `921636aa21` (2026-08-17T02:11:18Z, "na-eligibility-audit 2026-08-17 prediction tranche batch C") left the doc
with ONE na-eligibility-audit marker, hash `fd6de6563ae2fbd6`. Commit `603d1d1fef` (2026-08-17T08:15:05Z) appended a
SECOND marker (a "(prediction tranche, re-verify)" pass) whose own declared body-hash is `da3d38da5ff6c1be` -- and
that value IS exactly what `body_content_hash()` returns when run against the PARENT commit's content (i.e. the
marker's author computed it correctly, against the state right before appending their own marker):

```
hash of PARENT commit (921636aa21) content: da3d38da5ff6c1be   <- matches the marker's own declared value
hash of CURRENT (HEAD, after the marker was added) content:    dcaf644a50ddc941   <- does NOT match
```

The diff of commit `603d1d1fef` is clean -- it ONLY adds the 6-line marker block (1 leading blank + 5 marker
lines), nothing else in the doc changed. `body_content_hash()`'s own docstring says marker lines are stripped
specifically so appending one is a no-op for the hash. It is not: diffing the two `_VERDICT_MARKER_LINE_RE`-stripped
bodies (parent vs. current) shows exactly one residual line:

```
@@ -99,3 +99,4 @@
    (`prediction_phase_ab_residuals_2026_07_24` 7 open, `prediction_phase_d_formal_smoke_and_backfill_2026_07_24` 5 open)
    re-confirmed still open. No reclassification.

+
```

Mechanism: each marker append is conventionally preceded by exactly one blank line (the standard
Progress-Log-bullet separator). `_VERDICT_MARKER_LINE_RE` strips a marker's header + non-blank continuation lines,
but stops (by design) at the first blank line and does not consume that blank line itself. When a SECOND marker is
appended after the first, the blank line that used to separate "real content" from "marker 1" is now sandwiched
between two stripped marker blocks and survives stripping -- one extra blank line per marker ever appended to that
doc. This defeats the stated invariant ("two docs that differ only in ... verdict markers produce the same hash")
the instant a doc accumulates a second marker, which is exactly the shape the skill's own same-day "re-verify" step
produces routinely.

**Candidate fix (partially validated, NOT sufficient alone -- see below):** extend `_VERDICT_MARKER_LINE_RE` to also
consume one optional leading blank line immediately before the marker header:

```python
_VERDICT_MARKER_LINE_RE = re.compile(
    r"(?:^[ \t]*\n)?"                                    # <- new: swallow one preceding blank line
    r"^[^\n]*" + _BOOKKEEPING_MARKER_START + r"[^\n]*\n?"
    r"(?:(?![ \t]*\n)(?!-[ \t])(?!#)(?!" + _BOOKKEEPING_MARKER_START + r")[^\n]*\n)*",
    re.MULTILINE,
)
```

Verified this makes `prediction_phase_e_football_arb_live_2026_07_24.md`'s parent-vs-current hash match exactly
(`52e6fada8053cbf4` both sides).

## Confirmed repro (bug 2 -- same-date tie-break picks the FIRST marker, not the latest)

`_latest_verdict_marker()`:

```python
if best is None or date > best[0]:      # strict > -- a later same-date marker does NOT replace `best`
    best = (date, stored)
```

`re.finditer` yields matches in document order (top to bottom = chronological, since markers are always appended at
the end of the Progress Log). Two markers dated `2026-08-17` on the same doc means the SECOND (truly latest, and
the one whose hash is actually current) is discarded in favor of the FIRST, because `"2026-08-17" > "2026-08-17"` is
`False`. Fix is a one-character change, `>` to `>=`.

## Bug 1 fix + bug 2 fix together do NOT fully resolve the corpus (needs more investigation before shipping)

Re-ran both candidate fixes together against all 11 docs the prediction-tranche run flagged in-scope on 2026-08-17.
Result: **0 of 11 self-consistent** (worse than the single-doc test in isolation, which passed). This means there is
at least one MORE distinct cause of hash instability beyond the two above -- possibly: markers with no preceding
blank line (e.g. two markers appended back-to-back in the same commit with no separator), a marker whose
continuation text itself contains a line matching `_BOOKKEEPING_MARKER_START` partway through (breaking the
continuation-consumption early), or something specific to the "(prediction tranche, re-verify)" suffixed header
variant. **Do not ship either candidate fix as-is** -- across the whole corpus, EVERY existing marker's stored
`[body-hash:...]` was computed by the CURRENT (buggy) function, so changing the function invalidates every
historical hash at once, forcing a full unscoped re-audit on the next run of every tranche (the "dozens of
sub-agents, multi-hour" cost the skill's own Phase 0 section describes as the fallback for "after a long gap").
That is an acceptable one-time cost ONLY if the fix is actually complete -- shipping a partial fix pays that cost
without buying full correctness.

## Practical impact assessed this run (correctness, not just efficiency)

Despite the flag, the underlying verdicts were NOT wrong -- this is a Phase-0 SIGNAL bug (false "changed"), not a
Phase-1 CLASSIFICATION bug. Directly re-read 4 of the 10 prediction-owned flagged docs end-to-end
(`prediction_phase_ab_residuals_2026_07_24.md`, `prediction_live_clob_depth_capture_2026_07_24.md`,
`plans/active/issues/prediction_live_instrument_cache_never_refreshed_and_polymarket_catalog_gap_2026_08_14.md`,
`plans/active/issues/plan_reconciler_findings_prediction_2026_08_16.md`) and cross-checked the remaining 6 via their
already-recorded markers + a full open-checkbox re-grep; all 10 confirmed still accurate as of this run, nothing
reclassified, no new marker written (adding an 11th/12th marker on top of 2 already-present same-day markers would
only add more of the exact residual this issue describes, for zero new verdict information). Net cost of this bug
today: one dispatch's worth of redundant investigation time, not an incorrect corpus action.

## Todos

- [x] ✅ [SCRIPT] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md` item 3 (na-eligibility-audit 2026-08-17). Root-cause the remaining hash-instability cause(s) beyond bugs 1+2 above -- trace 2-3 more of the
      11 prediction-tranche mismatches the same way this doc traces
      `prediction_phase_e_football_arb_live_2026_07_24.md` (parent-commit hash vs. declared marker hash vs. current
      hash, diffed at the stripped-body level) until every case is explained, not just the first one found.
      Landed evidence reconciled: `unified-trading-pm@fc45e105a9` recorded the replay of snapshots `7913e469` and
      `921636aa` and its six-mismatch/no-third-cause conclusion in the batch16 plan.
- [x] ✅ [SCRIPT] P2. Extracted to `cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md` item 4 (na-eligibility-audit 2026-08-17). Once fully root-caused, implement the complete fix in
      `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` (`body_content_hash()` /
      `_VERDICT_MARKER_LINE_RE` / `_latest_verdict_marker()`), and audit the 5 other importers
      (`check_extracted_checkbox_citation.py`, `generate_context_scope_inventory.py`, `check_na_corpus_ratchet.py`,
      `generate_tranche_doc_inventory.py`, `na_marker_helper.py`) for any function that re-implements rather than
      imports the same hashing/marker-parsing logic (a duplicated, independently-drifted copy would need the same
      fix applied twice).
      Landed evidence reconciled: `unified-trading-pm@70fc5408f1` shipped the shared fix; the batch16 plan records
      QG evidence (`2155 passed, 17 skipped`) and the five-importer audit, with flip commit `dc4370f955`.
- [x] N. ✅ [OPERATOR] P3. **RULED 2026-08-21 (D28, ADOPTED-REC)**: accept the corpus-wide re-audit cost as bounded
      and already-incurred — the shared fix shipped without staggering (`unified-trading-pm@70fc5408f1`, see
      Progress Log below), and no warn/stagger mechanism is needed retroactively or going forward. No code change;
      disposition-only closure.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)

## Progress Log

- **2026-08-17 (na_eligibility_auditor, slot 14, tranche=prediction, DISPATCH_ID=agt-997289)**: filed. Full repro,
  both confirmed bugs, and the "not sufficient alone" finding are captured above with exact commit SHAs and hash
  values so a future fix session does not have to re-derive any of it.
- **na-eligibility-audit 2026-08-17** [body-hash:f0450de860bb8449]: RECLASSIFY (per-todo split) -- of 3 open todos, 2 are bounded/worker-determinable and extracted to cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md items 3-4: todo 1 (root-cause the remaining hash-instability cause(s) beyond the 2 already-confirmed bugs -- clear diagnostic method already demonstrated in-doc: diff parent-vs-current stripped-body hash per mismatch) and todo 2 (implement the complete fix once root-caused, audit the 5 other importers for a duplicated/drifted copy of the same hashing logic -- sequentially gated on todo 1 within the same batch item, which is ordinary plan structure, not a blocker). Doc stays assigned_vm: NA for its remaining item: todo 3 ([OPERATOR] P3, an explicit operator decision on whether/how to stagger the fix's corpus-wide one-time re-audit cost against other in-flight tranche dispatches). Conflict-check clear: no other active planning-assigned plan references body_content_hash/_VERDICT_MARKER_LINE_RE/_latest_verdict_marker; no overlap in the consolidated closeout or existing satellite batches. Meta note: this doc IS the bug several other docs in this same tranche run were re-flagged in-scope by today (a live, self-referential instance while auditing). Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-20 (cross-cutting finalize review)** [body-hash:caf3bc0cc91628b0]: KEEP-NA, valid — items 3 and 4 are now live and independently verified: root-cause replay landed at `unified-trading-pm@fc45e105a9`, and the shared hash fix plus five-importer audit landed at `unified-trading-pm@70fc5408f1` (QG evidence recorded in batch16; plan flip `dc4370f955`). The sole remaining todo is still the explicit `[OPERATOR]` P3 decision whether to warn/stagger the one-time corpus-wide re-audit, because the fix invalidates historical `[body-hash:...]` values and the next run of each tranche will re-audit its population once. Flagged for operator resolution; not resolved here. Cross-cutting finalize review.
- **2026-08-21 — ruling D28 (na-eligibility skill follow-ups)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority, AUTONOMOUS_AGENT_RULES rule 2): Approve both — the doc edit is cheap defense against the stale-Read class; the re-audit cost is bounded and already accepted. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger. All 3 todos now closed — 0 open items remain. Flagged fully-resolved for a future archival pass; `status` kept `open` (not `resolved`) and the physical archive move deliberately NOT performed by this chunk-8 dispatch (see `archive_exempt`/`resolved_by` notes in frontmatter) — a follow-up archival pass should flip status + git mv once picked up.
