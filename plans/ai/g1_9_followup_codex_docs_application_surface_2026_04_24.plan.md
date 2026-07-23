---
title: G1.9 follow-up — Codex docs application surface (full /docs build-out)
status: active
priority: P1
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-24
depends_on:
  - plans/archive/refactor_g1_9_codex_scope_registry_2026_04_20.plan.md (parent — codex scope-manifest infra)
  - plans/active/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md (Phase A done, Phases B-E pending — this
    plan is independent of B-E)
# Wave: standalone follow-up. Not part of G1 wave structure (G1 is fully archived).
---

# G1.9 follow-up — Codex docs application surface

## Context

G1.9 shipped the codex scope registry as **codex-tooling-only** infrastructure: rule 11 (5-audience enum), the `scope:`
frontmatter convention applied to ~770 codex docs, the `_generated/scope-manifest.json` regen tooling, the SSOT-INDEX
entry, and a CI gate that fails if docs lack a `scope:` field. Per the original G1.9 plan that was the correct scope.

This follow-up turns that codex-side infrastructure into running **application code**: a renderable `/docs` surface in
`unified-trading-system-ui` that **filters codex docs by the viewer's persona / audience** and lets prospects, demo
clients, investors, engineers, and admins see only the docs they're allowed to. Today the /docs route exists as a
hard-coded developer integration guide — useful, but blind to scope-manifest. We extend (not replace) it with a dynamic
codex-doc surface.

**Why now:** scope-manifest data sits unused; G3.6 visibility-slicing already gates features per persona; we lack a
similar gate for documentation. Onboarding flows (G2.1 / G2.7) and prospect demos benefit from "show this person the
docs they should see, hide the rest" without rewriting docs themselves.

## Pre-audit findings (recon 2026-04-24, Explore agent `a24eaef134dab726e`)

- **`/docs` route exists** at `unified-trading-system-ui/app/(public)/docs/{page,layout}.tsx` (~919 LOC). Hard-coded TS
  objects (CATALOGUES, PATHS, UAC_FACADES, API_REFERENCES). No `[slug]`, no markdown, no scope-manifest awareness. Gated
  by `BriefingAccessGate` (light-auth, access-code).
- **scope-manifest.json** at `unified-trading-pm/codex/14-playbooks/_generated/scope-manifest.json` (770 entries, 5
  audiences: `sales`, `engineer`, `admin`, `prospect`, `investor`). Regen via
  `codex/14-playbooks/_tools/build-scope-manifest.sh` (bash → `build_scope_manifest.py`).
- **No markdown library installed.** `package.json` has zero `remark` / `rehype` / `react-markdown` / `mdx` /
  `gray-matter` / `marked`. Briefings render via hard-coded TS + `renderWithTerms()` (glossary-token substitution) +
  `linkify()`. Briefings DO NOT render markdown.
- **Persona system** at `unified-trading-system-ui/lib/auth/personas.ts` (~482 LOC, 30+ demo personas with `role` +
  `entitlements`). Today entitlements gate FEATURES (tiles via G3.6 matrix), not CONTENT audiences. No persona has an
  `audiences: Audience[]` field yet.
- **Cross-repo doc pipeline:** none. Existing PM→UI propagation scripts at
  `unified-trading-pm/scripts/propagation/sync-*.sh` cover data fixtures (archetype-capability, questionnaire-response,
  restriction-profiles), not docs.
- **Search:** `lib/help/help-search.ts` (~197 LOC) is a reusable custom tokenize-+-synonym-+-weighted-score pattern. No
  `flexsearch` / `lunr` / `fuse.js`.

## Decisions locked with user (2026-04-24)

| Decision                              | Chosen                                                                                                                                                                                                           | Source                                       |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| Extend `/docs` (don't replace)        | Keep existing developer integration guide as static `/docs` index. Add **dynamic `/docs/[...slug]`** for codex doc rendering + a "Knowledge base" sidebar section listing audience-visible docs.                 | User: "avoid duplication"                    |
| Markdown rendering                    | Install `react-markdown` + `remark-gfm` + `gray-matter`. ~770 codex docs are real markdown (tables, code, headings) — TS-object conversion is impractical. Briefings keep their TS-object pattern.               | Pragmatic for codex content shape            |
| Cross-repo sync mechanism             | NEW `unified-trading-pm/scripts/propagation/sync-codex-docs-to-ui.sh` mirrors existing sync-pattern. Walks `codex/**/*.md`, parses frontmatter, emits `lib/docs/codex-fixture.json` (committed in UI).           | Matches `sync-archetype-capability-to-ui.sh` |
| Audience determination                | Add `audiences: readonly Audience[]` to each persona in `personas.ts`. Mapped: `admin` role → all 5 audiences; `client` role → `prospect` + `investor` (subset by entitlements); anon visitor → `prospect` only. | Closest fit to existing entitlements model   |
| Codex doc gating                      | If a doc's `scope` array intersects the viewer's `audiences`, render it; else 404. Server-side gate (RSC), not client-side hide. Engineer-only docs are NEVER fetched for prospect personas.                     | Security: hidden ≠ filtered                  |
| Search                                | Reuse `help-search.ts` tokenize/synonym/score pattern; new `lib/docs/codex-search.ts` indexes the audience-filtered fixture at module load. No external lib.                                                     | Reuse pattern                                |
| `BriefingAccessGate`                  | Keep; `/docs/*` stays light-auth gated. Same per-prospect access-code flow.                                                                                                                                      | Existing                                     |
| Build-time vs runtime audience filter | **Build-time:** sync script can emit per-audience pre-filtered bundles (`codex-fixture.{prospect,engineer,admin}.json`) for tree-shaking, but **runtime gate is the SSOT**. Build-time is optimisation.          | Defence in depth                             |

## Cross-references

- **Parent plan (archived):** `plans/archive/refactor_g1_9_codex_scope_registry_2026_04_20.plan.md`
- **Visibility-slicing engine (reuse):** `unified-trading-system-ui/lib/stores/scope-helpers.ts` +
  `lib/stores/global-scope-store.ts` — for _org/client/strategy_ scope (different axis; documented for clarity, not
  consumed by this plan)
- **Persona system:** `unified-trading-system-ui/lib/auth/personas.ts`
- **Briefings pattern (reuse):** `unified-trading-system-ui/app/(public)/briefings/{page,[slug]/page}.tsx`,
  `lib/briefings/content.ts`, `components/marketing/render-with-terms.tsx`
- **Existing /docs page (extend):** `unified-trading-system-ui/app/(public)/docs/page.tsx`
- **Help-search pattern (reuse):** `unified-trading-system-ui/lib/help/help-search.ts`
- **Sync-script pattern (reuse):** `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh`
- **Scope-manifest tooling (consume):** `unified-trading-pm/codex/14-playbooks/_tools/build-scope-manifest.sh` +
  `_generated/scope-manifest.json`
- **Rule 11 enum (consume):** `/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md`

## Mandatory read-set

1. `unified-trading-system-ui/app/(public)/docs/page.tsx` — full
2. `unified-trading-system-ui/app/(public)/docs/layout.tsx` — full
3. `unified-trading-system-ui/app/(public)/briefings/[slug]/page.tsx` — full (rendering pattern)
4. `unified-trading-system-ui/lib/briefings/content.ts` — first 200 lines (authoring shape)
5. `unified-trading-system-ui/components/marketing/render-with-terms.tsx` — full (string post-processing)
6. `unified-trading-system-ui/lib/auth/personas.ts` — full (audience mapping target)
7. `unified-trading-system-ui/lib/help/help-search.ts` — full (search pattern to clone)
8. `unified-trading-pm/codex/14-playbooks/_ssot-rules/11-codex-scope-registry.md` — full
9. `unified-trading-pm/codex/14-playbooks/_generated/scope-manifest.json` — top + bottom + 1 sample per audience
10. `unified-trading-pm/codex/14-playbooks/_tools/build-scope-manifest.sh` + the `.py` it invokes
11. `unified-trading-pm/scripts/propagation/sync-archetype-capability-to-ui.sh` — pattern to mirror
12. 3 sample codex docs (one heavy: `/codex/04-architecture/share-class-architecture.md`; one short:
    `/codex/14-playbooks/glossary.md`; one with code blocks: `/codex/06-coding-standards/quality-gates.md`)

## Out of scope

- **Markdown editing UI** — codex stays authored as `.md` files in PM repo; UI is read-only.
- **Real-time codex sync** — fixture is regenerated by sync script + committed. No live-fetch of PM at runtime.
- **Search across non-codex content** — help-tree, briefings, marketing pages stay separate.
- **Backlinking / wiki-style** — render docs as standalone pages; cross-references stay as raw markdown links.
- **Versioning / diff view** — git history on PM is the version source.
- **Replacing the existing /docs developer guide** — keep its hard-coded content; ADD codex docs alongside.
- **Unauthenticated access to admin/engineer docs** — `BriefingAccessGate` covers light-auth; scope filter handles
  audience.
- **Migrating briefings to markdown** — briefings stay as TS objects (curated voice).
- **Implementing G2.6 staging Firebase wiring** — independent; codex docs work today against demo personas.

## Phase breakdown

### Phase 1 — Cross-repo sync pipeline (PM → UI)

- [ ] [AGENT] P0. Create `unified-trading-pm/scripts/propagation/sync-codex-docs-to-ui.sh` (bash wrapper, ~50 LOC)
      mirroring `sync-archetype-capability-to-ui.sh` shape: `--check` (diff exit 1), `--write` (regen fixture), default
      = check.
- [ ] [AGENT] P0. Create `unified-trading-pm/scripts/propagation/sync_codex_docs_to_ui.py` (~200 LOC). Walks
      `codex/**/*.md` from workspace root, parses frontmatter (PyYAML), emits one JSON file:
      `unified-trading-system-ui/lib/docs/codex-fixture.json`. Schema:
      `{ docs: [{ slug, path, title, scopes,     excerpt, headings, body_markdown }] }`. Slug = doc path without `.md`,
      slashes → hyphens (e.g. `/codex/02-data/partitioning.md` → `02-data-partitioning`). Excerpt = first ~200 chars of
      body. Headings = flat list of H2/H3 anchors for TOC. body_markdown = raw markdown including frontmatter-stripped
      body.
- [ ] [AGENT] P0. Add AUTO-GEN banner to `codex-fixture.json` (first key `_generated_at`, `_source_commit`,
      `_total_docs`). Hook git commit SHA via `git rev-parse HEAD` from PM repo.
- [ ] [AGENT] P0. Wire into `unified-trading-system-ui/scripts/quality-gates.sh` as a check step (mirror G1.8 pattern):
      `bash "${WORKSPACE_ROOT}/unified-trading-pm/scripts/propagation/sync-codex-docs-to-ui.sh" --check`. Fails QG if
      fixture is stale; hint: "run --write to regen".

### Phase 2 — Audience mapping in personas

- [ ] [AGENT] P0. Add `Audience` type literal union to `unified-trading-system-ui/lib/auth/audiences.ts` (NEW):
      `"sales" | "engineer" | "admin" | "prospect" |     "investor"`. Source enum from rule 11.
- [ ] [AGENT] P0. Extend `Persona` type in `lib/auth/personas.ts` with `audiences: readonly Audience[]`. Backfill all
      30+ existing personas with reasonable defaults:
  - `role: "admin"` → all 5
  - `role: "internal"` → `["engineer", "admin", "sales"]`
  - `role: "client"` (paying) → `["prospect", "investor"]` (clients are still in the prospect-comms loop)
  - Demo prospects → `["prospect"]`
  - Investor personas → `["investor", "prospect"]`
- [ ] [AGENT] P0. New helper `getViewerAudiences(persona | null): readonly Audience[]` in `lib/auth/audiences.ts`. Anon
      (null persona) returns `["prospect"]`. Convenience wrapper used by RSC.

### Phase 3 — Markdown renderer dependency

- [ ] [AGENT] P0. Add `react-markdown` (^9), `remark-gfm` (^4), `gray-matter` (^4) to
      `unified-trading-system-ui/package.json`. Run `pnpm install` and commit lockfile.
- [ ] [AGENT] P0. New `components/docs/codex-doc-renderer.tsx` (NEW, ~80 LOC). Wraps
      `<ReactMarkdown remarkPlugins={[remarkGfm]}>` with: typography classes matching briefings, `<a>` resolved through
      existing `linkify()` for cross-doc refs, `<code>` styled with existing prose classes. Passes through
      glossary-token detection if any are encountered.
- [ ] [AGENT] P0. Smoke test: 3 sample codex docs render without runtime error (heavy / short / code-blocks).

### Phase 4 — Dynamic `/docs/[...slug]` route

- [ ] [AGENT] P0. Create `app/(public)/docs/[...slug]/page.tsx` (NEW, ~120 LOC). RSC. Loads codex-fixture.json, finds
      doc by slug, runs scope intersection check, renders or 404s. `generateStaticParams()` returns all audience-visible
      slugs at build time (build-time pre-filter for performance + crawler safety; runtime gate is authoritative).
- [ ] [AGENT] P0. Create `lib/docs/codex-fixture-reader.ts` (NEW, ~60 LOC). Exports `getCodexDocBySlug(slug)`,
      `listCodexDocsForAudiences(audiences)`, `getAllSlugsForAudiences(audiences)`. Reads fixture via
      `import codexFixture from "./codex-fixture.json"` (Next.js handles JSON imports).
- [ ] [AGENT] P0. Server-side scope check helper:
      `audienceCanReadDoc(viewer: readonly Audience[], doc: {scopes:     readonly Audience[]}): boolean` — returns true
      if intersection non-empty. Test: prospect cannot read engineer-only doc; admin reads everything; investor reads
      sales+investor docs.
- [ ] [AGENT] P0. 404 path: when slug missing or audience denied, render Next.js `notFound()`. Do not leak existence of
      denied docs.

### Phase 5 — `/docs` index extension (knowledge base sidebar)

- [ ] [AGENT] P0. MODIFY `app/(public)/docs/page.tsx`. Keep existing CATALOGUES / PATHS / UAC_FACADES / API_REFERENCES
      sections unchanged. ADD a new "Knowledge base" sidebar section + scroll anchor that lists the first ~50
      audience-visible codex docs grouped by codex sub-system (00-SSOT-INDEX, 01-domain, 02-data, 14-playbooks/...).
      Link each to `/docs/<slug>`.
- [ ] [AGENT] P0. Sidebar nav entry: "Knowledge base ▶" expands to a tree of audience-visible doc titles. Reuses
      existing scroll-section nav component.
- [ ] [AGENT] P0. Empty state: anon visitors (audience = `["prospect"]`) see whatever prospect-scoped codex docs exist
      (count + sample); fallback message if 0 visible.

### Phase 6 — Codex doc search

- [ ] [AGENT] P0. Create `lib/docs/codex-search.ts` (NEW, ~150 LOC) cloning `help-search.ts` shape: tokenize,
      synonym-expand, weighted score (title 5x, headings 3x, excerpt 2x, body 1x), top-5 results. Index the
      audience-filtered fixture at module load.
- [ ] [AGENT] P0. Search box on `/docs` page header. Submitting redirects to `/docs/search?q=...` or shows top-5 inline
      (decide during implementation). Falls back gracefully if zero results.

### Phase 7 — Playwright + QG

- [ ] [AGENT] P0. New durable spec `tests/e2e/playbooks/refactor/g1-9-followup-codex-docs.spec.ts`: seed 4 personas
      (anon, prospect-im, engineer-internal, admin), navigate to `/docs`, assert: (a) Knowledge base section visible per
      persona, (b) doc count delta between prospect and admin, (c) `/docs/<engineer-only-slug>` returns 404 for
      prospect, 200 for admin, (d) search returns audience-filtered hits, (e) AUTO-GEN banner present in fixture.
- [ ] [AGENT] P0. Wire spec into `scripts/quality-gates.sh`.
- [ ] [SCRIPT] P0. Run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — full pass.
- [ ] [SCRIPT] P0. Run `cd unified-trading-pm && bash scripts/quality-gates.sh` — full pass on the new sync script.

## Critical files to be modified

PM repo:

- `unified-trading-pm/scripts/propagation/sync-codex-docs-to-ui.sh` — NEW
- `unified-trading-pm/scripts/propagation/sync_codex_docs_to_ui.py` — NEW

UI repo:

- `unified-trading-system-ui/package.json` — MODIFY (3 deps)
- `unified-trading-system-ui/pnpm-lock.yaml` — REGENERATED
- `unified-trading-system-ui/lib/auth/audiences.ts` — NEW
- `unified-trading-system-ui/lib/auth/personas.ts` — MODIFY (audiences field on every persona)
- `unified-trading-system-ui/lib/docs/codex-fixture.json` — GENERATED, COMMITTED
- `unified-trading-system-ui/lib/docs/codex-fixture-reader.ts` — NEW
- `unified-trading-system-ui/lib/docs/codex-search.ts` — NEW
- `unified-trading-system-ui/components/docs/codex-doc-renderer.tsx` — NEW
- `unified-trading-system-ui/app/(public)/docs/page.tsx` — MODIFY (add Knowledge base section)
- `unified-trading-system-ui/app/(public)/docs/[...slug]/page.tsx` — NEW
- `unified-trading-system-ui/scripts/quality-gates.sh` — MODIFY (sync-check + spec wire)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/g1-9-followup-codex-docs.spec.ts` — NEW

## Execution DAG

```
Phase 1 (PM sync script + fixture) ────┐
                                       ├──> Phase 4 (/docs/[...slug] route) ──> Phase 5 (/docs index extension) ──> Phase 7 (QG + Playwright)
Phase 2 (audiences + persona field) ───┤                                                                                ▲
                                       │                                                                                │
Phase 3 (markdown renderer) ───────────┘                                                                                │
                                                                                                                        │
                                            Phase 6 (search) ───────────────────────────────────────────────────────────┘
```

Phase 1, 2, 3 can run in parallel. Phase 4 needs all three. Phase 5 needs Phase 4 (uses `listCodexDocsForAudiences`).
Phase 6 can run in parallel with Phase 5. Phase 7 gates the merge.

## Verification

1. `bash unified-trading-pm/scripts/propagation/sync-codex-docs-to-ui.sh --check` exits 0 after `--write`.
2. `unified-trading-system-ui/lib/docs/codex-fixture.json` contains all 770 codex docs with parsed frontmatter +
   audience tags.
3. Anon visitor on `/docs` sees only prospect-scoped codex docs in the Knowledge base sidebar; admin sees all 5
   audiences' docs combined.
4. `/docs/02-data-partitioning` renders the markdown of `unified-trading-pm/codex/02-data/partitioning.md` with tables +
   code blocks intact.
5. Engineer-only doc URL returns Next.js 404 for prospect persona, 200 for admin persona.
6. Search box on `/docs` returns top-5 audience-filtered hits per query.
7. Playwright spec 5/5 green across 4 personas.
8. QG green on both repos.

## Handoff

Unblocks:

- Internal engineering onboarding (engineer audience can read codex inside the running app, not just the repo).
- Prospect-demo content depth: prospects can be pointed to specific codex docs that survive sales-handoff.
- Future "audience-aware help drawer" — search index can be reused.

Does not block:

- G2.6 staging Firebase Phase B-E (independent).
- Marketing site IA work (different surface).

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (tier-1) as 4 personas via `seed-persona.ts`. Walk the canonical
click-path: navigate to `/docs`, expand Knowledge base, click a doc title, verify body renders, return, search, click
result, verify scope-deny on engineer-only-as-prospect.

**Durable spec:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/g1-9-followup-codex-docs.spec.ts`. Seeds each
persona; asserts visibility-slicing per audience formula (intersection of `persona.audiences` × `doc.scopes` non-empty);
asserts `/docs/<denied-slug>` returns 404 (orphan-reachability negative case); asserts AUTO-GEN banner present so
fixture-staleness is caught.

Wire into `scripts/quality-gates.sh`.

## What NOT to do (verbatim guardrails)

- Do NOT replace the existing hard-coded `/docs` developer guide. Keep its CATALOGUES / PATHS / UAC_FACADES /
  API_REFERENCES sections; ADD a Knowledge base section beside them.
- Do NOT migrate briefings to markdown. They stay as TS objects (curated voice, tone-controlled).
- Do NOT bypass the runtime audience gate. Build-time pre-filtering is optimisation only — every request still re-checks
  `audienceCanReadDoc(viewer, doc)` server-side.
- Do NOT leak doc existence to denied audiences. 404 must be indistinguishable from "doc doesn't exist".
- Do NOT live-fetch PM repo at runtime. Fixture is committed.
- Do NOT hardcode codex paths in app code outside the fixture reader. The fixture is the single source.
- Do NOT introduce a new search library. Reuse `help-search.ts` pattern.
- Do NOT touch G2.6 staging Firebase wiring. Independent.
- Do NOT bundle codex docs of audience X into the build bundle for audience Y (defence-in-depth tree-shaking
  optimisation in Phase 1).
- Do NOT skip pre-commit hooks. If conventional-commit hook rejects scope-with-slash, use `docs(plans)` style.

## AGENT EXECUTION PROMPT

**Copy-paste below this line into a new agent session to execute G1.9 follow-up.**

---

You are executing **G1.9 follow-up — Codex docs application surface** for the Unified Trading System at Odum Research.
This is a feature build, not a refactor. Plan Mode is **ON** because the dependency footprint (`react-markdown` +
cross-repo sync) is non-trivial.

### Pre-flight check

```bash
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git fetch origin && git checkout live-defi-rollout && git pull
ls plans/active/g1_9_followup_codex_docs_application_surface_2026_04_24.plan.md
ls codex/14-playbooks/_generated/scope-manifest.json
ls ../unified-trading-system-ui/app/\(public\)/docs/page.tsx
```

### Mandatory rules injection

Read these before any action:

- `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- `unified-trading-pm/plans/PLAN_FORMAT.md`
- This plan file in full (especially §Pre-audit findings, §Decisions, §Out of scope, §What NOT to do)

WORKSPACE_ROOT = `/Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Plan-mode discipline (Plan Mode ON)

Before writing code, draft a micro-execution plan into `## Micro-execution plan (sub-agent Phase 1)` appended to this
plan file: file × line ranges × commit sequence × Playwright assertions × dependency-resolution risk (react-markdown /
remark-gfm peer-dep alignment with Next.js version). Commit:
`bash scripts/quickmerge.sh "docs(plans): G1.9-followup micro-execution plan" --agent --files "plans/active/g1_9_followup_codex_docs_application_surface_2026_04_24.plan.md"`.
Fallback if quickmerge blocked: `git add <file> && git commit && git push origin live-defi-rollout`. Then RETURN with
micro-plan SHA + open questions. Do NOT execute code yet.

### Lessons from earlier waves (bake these in)

1. Quickmerge is blocked branch-wide by 65 dep-alignment drifts. Skip it; direct push.
2. Pre-commit prettier reformats; re-stage and re-commit on rejection.
3. Conventional-commit hook rejects scopes with slashes. Use `docs(plans)` not `docs(plans/active)`.
4. Plan prose drifts from reality. Verify file paths before consuming.
5. Canonical ports: tier-0 = 3000... wait, tier-1 = `localhost:3000`, tier-0 = `localhost:3100`. Playwright uses tier-1
   (3000).
6. UI repo carries ~30 modified files from concurrent agents. Stage ONLY explicit file lists. Never `git add -A`.
7. Commit incrementally. Push each phase. Don't batch.
8. Stream watchdog kills after 600s idle. Each shell command <60s.

### Read-set (mandatory)

Per §Mandatory read-set above (12 files / sample docs).

### Deliverables

Per §Critical files (13 files across PM + UI). 7 commits expected (one per phase).

### Commit strategy

- Phase 1 (PM): `feat(scripts/propagation): sync-codex-docs-to-ui pipeline (G1.9 follow-up Phase 1)` — PM commit
- Phase 2 (UI): `feat(ui/auth): add audience field to personas (G1.9 follow-up Phase 2)` — UI commit
- Phase 3 (UI): `chore(deps): add react-markdown + remark-gfm + gray-matter (G1.9 follow-up Phase 3)` — UI commit
- Phase 4 (UI): `feat(ui/docs): dynamic /docs/[...slug] codex doc route (G1.9 follow-up Phase 4)` — UI commit
- Phase 5 (UI): `feat(ui/docs): Knowledge base section in /docs index (G1.9 follow-up Phase 5)` — UI commit
- Phase 6 (UI): `feat(ui/docs): audience-filtered codex search (G1.9 follow-up Phase 6)` — UI commit
- Phase 7 (UI): `test(playbooks): G1.9-followup durable spec + QG wire (G1.9 follow-up Phase 7)` — UI commit
- Final PM: `docs(plans): G1.9-followup checkbox flips + final SHAs` — PM commit

### Success criteria

Per §Verification (8 items).

### Report back

- Each phase's commit SHA on origin/live-defi-rollout
- Playwright pass/fail
- Any persona-mapping decisions that changed during implementation
- Total LOC delta + bundle-size impact (`pnpm next build` size delta acceptable: <100 KB growth on /docs route)
- Open follow-ups (e.g. CI hook for sync-script auto-run on PM push)
