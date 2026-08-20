---
doc_type: codex-ssot
title: Epic HTML report format
summary: The universal per-epic HTML report template `/plan-reconcile <epic_slug>` generates and publishes — generalized
  from the "AO Provider Dispatch Ledger" built by hand for the agent-orchestrator epic on 2026-08-18. Defines the
  section structure, what data backs each section, and the design-token approach so every epic's report reads as
  the same system without being visually identical (content picks the palette, not a shared stylesheet file).
status: current
nature: spec
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [epics, html-artifact, plan-reconcile, dataviz]
related:
  [
    /codex/11-project-management/epic-taxonomy-2026-08-18.md,
    /plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md,
    cursor-configs/skills/plan-reconcile/SKILL.md,
    scripts/plan-hygiene/count_open_tasks.py,
  ]
created: 2026-08-18
authoritative_for: [epic HTML report structure, epic artifact storage/publish convention]
referenced_by: []
code_refs:
owner:
last_reviewed: 2026-08-18
---

# Epic HTML report format

## Why this exists

The AO Provider Dispatch Ledger (built 2026-08-18, hand-authored for one epic-adjacent audit) proved a shape that
reads well: a scannable ops ledger, not a document — headline numbers first, then structure that encodes real state
(operator-blocked vs. AO-eligible vs. already-done), then concrete next actions (dispatch prompts). This doc
generalizes that shape so `/plan-reconcile <epic_slug>` can regenerate it for any epic without re-deriving the
design each time, while leaving room for genuine per-epic variation (an epic with no operator-blocked items just
omits that section — never pad it out with "none").

## Storage + publish convention

- **Local file**: `plans/epics/html/<epic_slug>.html` (new directory, sibling to `plans/epics/*.md`) — the repo copy
  of record, committed alongside the epic doc it describes.
- **Published artifact**: the same content, published so a shareable link exists. On a re-run for the same epic,
  republish to the SAME artifact (don't mint a new URL each time) — store the artifact URL in the epic `.md` file's
  own frontmatter or a dedicated `## Report` section so a future run knows which URL to update rather than creating
  a duplicate.
- **Freshness**: the local HTML's own generation timestamp (embedded as an HTML comment near the top, not relied on
  for logic) should be newer than the epic doc's `last_updated` — this is what
  `check_epic_html_freshness.py` (see the epic-taxonomy restructure plan's Phase 5) checks.

## Section structure

Not every section applies to every epic — an epic with a clean backlog and no operator-blocked items should have a
short report, not a padded one. Sections, in order:

1. **Masthead** — epic name as the page title (a name, not a category label — "CI Pipeline Ledger", not "CI Epic
   Report"), one-sentence dek stating what the epic covers and the report's generation date.
2. **In-scope / excluded chips** (OMIT if the epic has no meaningful exclusion set — most won't). Only include when
   the epic genuinely has an adjacent-but-explicitly-out-of-scope population worth naming, the way the AO ledger
   named Kimi as an excluded provider. Don't force this section to exist for epics with no such boundary.
3. **Headline stat strip** — 3-5 tiles: open todos (deduped, aggregator-excluded, matching `/open-task-count`'s
   methodology), done todos, count of operator-blocked/human-only items, and any epic-specific count worth
   surfacing (e.g. excluded-scope count, if section 2 applies).
4. **Plan-by-plan breakdown** — one card per child plan (found via `parent_epic: <slug>`, not the broken
   filename-substring inventory-script definition — see the restructure plan's Why). Each card: title, file path,
   open/done counts as a small bar, key `[OPERATOR]`-tagged todo quoted verbatim if one exists, one-line summary.
   Aggregator plans (batch/satellite/consolidated/closeout/tracker-named) get flagged as non-double-counted, same
   convention as `/open-task-count`.
5. **On the operator's desk** — a table of every open item gated on human action (subscription/credential decisions,
   standing "handled elsewhere" redirect banners, doc-level human-plan rulings) with what it's gated on. OMIT if
   empty — an epic with nothing operator-blocked just doesn't have this section.
6. **Needs extra scoping** — items found genuinely ambiguous or under-specified during the reconcile pass (per
   `/plan-reconcile`'s own contradiction-hunter classes) that don't fit neatly into "open" or "operator-blocked" —
   OMIT if the reconcile pass found nothing like this.
7. **Closed out this pass** — what `/plan-reconcile` itself flipped to done this run (with evidence citations), so
   the report doubles as a diff of what changed, not just a snapshot.
8. **Parallel-tab flow for what's left** — a table dividing remaining open, non-operator-blocked work into up to 5
   lanes (this workspace's own parallel-agent ceiling), each with its owned files, so two lanes never collide on the
   same file. State plainly when full parallelism isn't achievable yet (e.g. everything touches one shared file) —
   don't claim more parallel lanes than the file boundaries actually support.
9. **Dispatch prompts** — one self-contained, copy-pasteable prompt per lane from section 8, each carrying the
   sub-agent mandatory-rules floor at the top (a fresh tab/agent inherits nothing) and the same "implement + verify
   QG genuinely green + stop, don't ship" discipline used everywhere else in this workspace, unless the epic's own
   content is docs-only (no code to gate).
10. **Notes & methodology** — corpus-wide baseline for context, any assumption/inference flagged plainly (the way
    the AO ledger flagged its "Nye = Gemini" inference), and a pointer back to `/open-task-count`'s dedup
    methodology since the stat strip in section 3 must match it, not invent a competing definition.

## Design-token approach (not a shared stylesheet)

Each epic's report picks its OWN 4-6 color tokens, type pairing, and layout concept — grounded in that epic's actual
subject matter, the same way the AO ledger's palette (bone/ink-green neutrals, brass accent, dispatch-board framing)
was chosen for a fleet-dispatch subject rather than reused from a generic template. Do not literally copy the AO
ledger's CSS file for every epic — that produces the "every report looks the same" AI-generated-design smell this
workspace's own `artifact-design` skill warns against. Load `artifact-design` fresh for each epic's report and let
the epic's actual subject (CI pipelines, market-data ingestion, strategy archetypes, whatever) suggest its own
palette and layout concept, while keeping the SECTION STRUCTURE above consistent across all of them. Structure is
what makes these "the same system" — visual identity is what makes each one feel considered rather than templated.

Universal fundamentals that DO carry over to every epic's report regardless of palette (from `artifact-design`,
restated here because a report-generation pass shouldn't have to re-derive them each time): both light and dark
theme defined properly (token-level, not literal colors inside media queries), `overflow-x: auto` on any wide
table, `text-wrap: balance` on headings, tabular-nums on any column of digits, a real `<title>` (the epic's name, not
"Epic Report").

## Data sourcing — what must be measured, not assumed

- Open/done counts: derive the same way `scripts/plan-hygiene/count_open_tasks.py` does (aggregator-plan exclusion,
  `assigned_vm` split) — don't hand-count from a partial grep.
- `parent_epic` membership: `rg "^parent_epic: <slug>$"` against real frontmatter, never the filename-substring
  method `regenerate_active_plan_inventory.py` uses (see the restructure plan's Why for exactly why that's wrong).
- Anything presented as "verified" or "confirmed" must have actually been checked this run — CLAIM ≤ MEASUREMENT
  applies to a generated report exactly as much as to a chat reply. A stat that can't be freshly measured this run
  should say so rather than carry forward a stale number silently.
