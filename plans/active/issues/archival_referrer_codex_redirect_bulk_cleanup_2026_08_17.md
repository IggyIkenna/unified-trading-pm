---
doc_type: issue
title: "Bulk-cleanup dispatch — 925 active-plan related: entries still cite an archived plan instead of codex"
summary: >-
  New rule (2026-08-17, `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` step 5, sharpened): when a
  plan is archived, its durable content moves to codex, and every referrer's `related:` entry gets repointed at codex —
  never left citing the archived plan itself, which quietly turns it into the fact's only home. Mechanically enforced
  going forward by `scripts/plan-hygiene/check_active_refs_archived_plans.py` (a shrinking ratchet, `--only`-scoped into
  `quality-gates.sh` at zero added cost on unrelated pushes), seeded at a 925-hit corpus-wide baseline — real
  pre-existing debt predating the rule by months, not new breakage. This doc tracks working that baseline down and
  carries the dispatch prompt for the cleanup pass (§ "Dispatch prompt" below).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archival, codex, ratchet]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
created: "2026-08-17"
author: claude
priority: P2
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
locked_by:
source: >-
  Discovered live 2026-08-17 while root-causing a recurring PM QG failure class (check_reference_paths /
  check_ag_closeout_linkage tripping repeatedly on docs whose referenced target had been archived by a concurrent
  commit) — root cause traced one level deeper: nothing was redirecting referrers to codex at archival time in the
  first place, so a plan's durable content had no home once its own doc archived. Operator ruling (2026-08-17): "if you
  archive a plan, the information for that plan goes into codex — plans that used to refer to archived plans start
  referring to codex, and people can archive safely."
resolved_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    scripts/plan-hygiene/check_active_refs_archived_plans.py,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/infra_satellite_ao_dispatch_batch19_2026_08_18.md,
  ]
---

# Bulk-cleanup dispatch — active-plan referrers still citing archived plans directly

## The rule (see the codex SSOT for the full ritual)

Archiving a plan is not just a `git mv`. Its durable content — a ruling, a measured number, a design decision, a recipe
another doc will need — must be captured in a codex SSOT (existing or new) as part of the SAME archival work, and every
OTHER doc's `related:` entry that pointed at the now-archived plan gets repointed at that codex doc instead. This is
never a reason to skip archiving a done plan — archive it, just fix the referrers as part of the same pass.

## The ratchet

`scripts/plan-hygiene/check_active_refs_archived_plans.py`:

- Scans `plans/active/**/*.md` + `plans/epics/*.md` `related:` frontmatter ONLY (not document prose — citing an
  archived plan as historical evidence, e.g. "root-caused in `plans/archive/issues/<slug>.md`", is the correct end-state
  this rule produces once the fact is migrated to codex citing its source, not a violation).
- `--only <files>` mode is wired into `quality-gates.sh`'s already-scoped doc-tree section (reuses the same staged-file
  list the neighbouring frontmatter check already computes — no added file-discovery cost on a push that doesn't touch
  `plans/`/`codex/`).
- Corpus-wide baseline mode (`scripts/plan-hygiene/active_refs_archived_plans_baseline.yaml`) is a standard shrinking
  ratchet: seeded 2026-08-17 at **925**, never hand-raise it, `--update-baseline` lowers it as each batch of fixes
  lands.

## Dispatch prompt

Hand this to a fresh agent session (or run it yourself) to work the baseline down. Runs safely in batches — each batch
is independently shippable, no need to clear all 925 in one pass.

> Run `python3 scripts/plan-hygiene/check_active_refs_archived_plans.py` in `unified-trading-pm` to get the live list of
> `related:` entries in active plans that still cite an archived plan directly (currently ~925, baseline in
> `scripts/plan-hygiene/active_refs_archived_plans_baseline.yaml`). Work through them in batches of ~20-30 at a time,
> per entry:
>
> 1. Read the archived plan the `related:` entry points at (`plans/archive/...`). Identify what durable fact/ruling/
>    number/recipe it established that the REFERRING doc actually needs — not the whole plan's history, just the part
>    that's still load-bearing.
> 2. Check whether that fact ALREADY lives in a codex SSOT (grep codex first — many archived plans' content has already
>    been migrated by a prior pass; don't duplicate). If it does, repoint the `related:` entry at that codex doc
>    directly.
> 3. If it doesn't, write it into the most appropriate existing codex doc (prefer extending a relevant existing SSOT
>    over creating a new file) as a short, dated section — then repoint the `related:` entry there.
> 4. If the archived plan's content genuinely has nothing a live doc still needs (its own archival banner + supersession
>    already covers it, the referring `related:` entry was just leftover clutter), the SAFE fix is to drop the
>    `related:` entry entirely rather than force a codex migration for content nobody actually needs — use judgment,
>    don't manufacture a codex doc just to satisfy the ratchet.
> 5. After each batch, re-run the checker, confirm the count dropped, then `--update-baseline` and ship via
>    `quickmerge.sh --agent --files` scoped to the touched plan + codex files (never `git add -A` — many other sessions
>    are concurrently editing this repo). Flip this issue doc's own progress here as you go (cite the new count each
>    batch).
> 6. Under `/autonomous`: keep looping batches until the count hits 0, or until you hit genuinely ambiguous cases that
>    need an operator call — file those as their own small issue docs rather than guessing, and keep going on the rest.
>
> This is corpus-hygiene work, not a design task — most entries will be mechanical (the codex doc already exists,
> or the archived plan's content is genuinely superseded/moot). Don't overthink individual entries; the goal is
> shrinking the ratchet steadily, not perfection on the first pass.

## Progress log

- 2026-08-17 (claude): rule sharpened in codex, ratchet built + wired into `quality-gates.sh` (`--only`-scoped, zero
  added cost on unrelated pushes), baseline seeded at 925. This doc filed as the tracked dispatch target — cleanup work
  itself not yet started.
- **na-eligibility-audit 2026-08-18** (infra tranche) [body-hash:92cf28bc44690cc6]: RECLASSIFY (per-todo split) —
  todo 1 is a self-contained, bounded batch-cleanup task (its own "Dispatch prompt" section already specifies the
  full mechanical procedure, incl. an autonomous-mode ambiguous-case escape hatch) — extracted to
  `infra_satellite_ao_dispatch_batch19_2026_08_18.md` item 1 (conflict-check clear: only this doc referenced the
  mechanism, first dispatch). Todo 2 (P3, consider `--diff-base` mode once the baseline reaches 0) stays
  `assigned_vm: NA` — small forward-looking design question, not independently actionable yet.
- **2026-08-18 (later same day)**: a session tracking 5 unrelated ship-blocked GCS-compliance fixes (see
  `/plans/active/issues/utl_gcs_client_upload_from_string_silent_write_failure_2026_08_18.md`) found
  `unified-trading-pm/scripts/catalogue/sync-to-mock.py`'s fix specifically blocked by 10 of this ratchet's 925
  citations across 6 docs. Added a priority sub-note to `infra_satellite_ao_dispatch_batch19_2026_08_18.md`'s todo
  1 naming the exact 6 docs — see that doc for detail. Did not attempt the fix itself: confirmed (via the actual
  checker script, not the `--only` shortcut) each citation's required remedy is a genuine per-citation codex-home
  research task (the checker rejects ANY `/plans/archive/...` path, not just the pre-archival one — a mechanical
  "point at the new path" does not satisfy it), and all 6 target docs were simultaneously dirty with other
  sessions' own unrelated uncommitted WIP at the time — not a safe or genuinely "cheap" fix to force in a tracking
  pass.
- **context-scout 2026-08-19**: populated context_scope (4 entries).
- **slot-13 2026-08-20**: `infra_satellite_ao_dispatch_batch19_2026_08_18.md` item 1, first execution batch —
  worked the 6 highest-count referring docs (117 citations), ratchet baseline lowered 925 → 761 (live count was
  already 878 at pickup). See that plan's own Progress Log for the full per-entry method. The 10-citation/6-doc
  ship-blocker this doc's prior note flagged is confirmed already resolved (those docs no longer appear in the
  live violation list). 761 citations remain; not yet at 0.

- **slot-21 2026-08-20**: Follow-up batch removed 22 redundant archived-plan `related:` citations from three active documents, lowering the measured live count and baseline 761 → 740. Each removed entry was retained as an inline/body citation in its referring document; no codex migration was needed. The cleanup todo remains open.

- **slot-21 2026-08-20 (ship-gate follow-up)**: Quickmerge exposed 19 scoped archive-safety violations after a peer fast-forward. Removed the 13 entries owned by this cleanup batch (2 CeFi + 11 corpus-hygiene); excluded 6 unrelated `tradfi_master.md` entries. `--only` is clean; measured corpus count/baseline is now 711.

- **slot-21 2026-08-20 (third execution batch)**: Removed 16 redundant `related:` citations from the prediction and cross-cutting consolidated closeout docs after verifying body/source evidence; restored two non-redundant pointers. Live checker count/baseline is now 710. The cleanup todo remains open.

- **slot-21 2026-08-20 (fourth execution batch)**: Removed 22 redundant archived-plan `related:` citations from four clean active documents after confirming each basename was already retained in document-body/source evidence; no codex migration was needed. The live checker and ratchet baseline are now 704 citations. The cleanup todo remains open.

- **slot-21 2026-08-20 (refreshed-branch batch)**: Reapplied the verified frontmatter-only cleanup after a concurrent fast-forward swept the prior working copy. Removed 16 redundant archived-plan `related:` citations (prediction closeout 7; cross-cutting closeout 9); preserved the two entries without body evidence. Live checker/baseline is now 688 after concurrent peer cleanup. The cleanup todo remains open.

- **slot-21 2026-08-20 (pointer-review follow-up)**: The scoped gate exposed five remaining entries without body repetitions. Each archived plan was read; all five were resolved or already represented by existing referring-document evidence, so the stale historical pointers were dropped rather than manufacturing codex content. `--only` is clean; live checker count/baseline is 681.

## Todos

- [x] ✅ **EXTRACTED 2026-08-18 (na-eligibility-audit, infra tranche) →
      `infra_satellite_ao_dispatch_batch19_2026_08_18.md` item 1.** Not yet executed — tracked there. ~~Work the
      `check_active_refs_archived_plans.py` baseline down from 925 toward 0, per the dispatch prompt above —
      batches of ~20-30, `--update-baseline` + ship after each batch.~~
- [ ] [SCRIPT] P3. Once the baseline reaches 0, consider whether `--diff-base` mode (same shape as
      `check_reference_paths.py`'s) is worth adding for CI-side high-velocity-branch resilience — not needed while the
      baseline is still actively shrinking.

- **slot-22 2026-08-20 (fifth execution batch)**: Removed 25 redundant archived-plan `related:` citations from three clean active plans after verifying each archived basename was already retained in the referring document body: prediction closeout (9), cross-cutting closeout (9), and observability closeout (7). The live checker measured 668 citations, below the prior 671 ratchet, and `--update-baseline` lowered the baseline to 668. The cleanup todo remains open; no codex migration was needed.
- **slot-22 2026-08-20 (sixth execution batch)**: Removed 4 redundant archived-plan `related:` citations from four clean active plans after confirming each archived basename was already retained in the referring document body, source, or dependency context; no codex migration was needed. The isolated ship tree contains this batch only; the verified batch count is 653 (657 → 653). The cleanup todo remains open.

- **slot-22 2026-08-20 (seventh execution batch)**: Removed 26 redundant archived-plan `related:` citations from 12 clean active plans after the scoped gate exposed three additional stale pointers in `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`; each basename remained in prose, source, or dependency evidence, and no codex migration was needed. The live checker measured 631 citations and `--update-baseline` lowered the ratchet 634 → 631; the cleanup todo remains open.
