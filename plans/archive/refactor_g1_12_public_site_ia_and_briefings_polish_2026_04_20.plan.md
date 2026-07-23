---
doc_type: plan
title: Refactor G1.12 — Public-site IA + briefings polish
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
depends_on:
  [
    /codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md §1.12,
    /codex/14-playbooks/_ssot-rules/02-tone-and-posture.md,
    /codex/14-playbooks/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-playbooks/experience/marketing-journey.md,
    /codex/14-playbooks/experience/briefings-hub.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Refactor G1.12 — Public-site IA + briefings polish

## Context

Stage 3E §1.12 (2026-04-20 amendment) unifies the dropdown/nav pattern across the public-facing pages — `/`,
`/investment-management`, `/platform`, `/regulatory`, `/firm`, `/contact`, `/demo`, `/signup`, `/login` — and enforces
cut-through-noise formatting on the three `/briefings/*` sub-pages. Today's public site has mixed nav components
(site-header on some pages, spaces-nav-sections on others, ad-hoc drop-in dropdowns), inconsistent CTA placement, and
briefings pages that read as exhaustive lists rather than single-message briefings. This is a UI-only refactor: no auth
changes, no routes added/removed, no backend.

## Decisions locked with user (2026-04-20)

| Decision                      | Chosen                                                                                                  | Source                                       |
| ----------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| One public-site nav component | Consolidate to `<SiteHeader>` with consistent dropdown + CTA + breadcrumb pattern on all 9 public pages | Kickoff §1.12                                |
| Briefings polish              | Each `/briefings/*` page starts with a single one-sentence TL;DR + single CTA above the fold            | rule 02 tone + `experience/briefings-hub.md` |
| No route changes              | Every existing public URL stays resolvable; IA polish is cosmetic + structural within pages             | Kickoff §1.12 UI-only                        |
| No auth changes               | `lib/config/auth.ts` untouched                                                                          | Kickoff §1.12 UI-only                        |

## Cross-references

- **Sibling Wave A plans:** refactor*g1*{1,3,5,9,14}\_2026_04_20.md
- **G1.3 LOCKED-VISIBLE** — sibling UI pattern; public site itself does not need LOCKED-VISIBLE (public pages are
  public) but tile components reused on `/platform` or similar surfaces do.
- **Rules cited:** `_ssot-rules/02-tone-and-posture.md` (voice), `_ssot-rules/06-show-dont-show-discipline.md` (what to
  surface on public vs gated surfaces)
- **Experience docs:** `experience/marketing-journey.md`, `experience/briefings-hub.md`
- **DART label (already live 2026-04-19):** `components/shell/nav-copy.ts` — DART = Data Analytics, Research & Trading.
  Do not re-edit this file's label; just consume it.

## Mandatory read-set

1. `/codex/14-playbooks/infra-spec/stage-3e-refactor-plan.md` §1.12
2. `/codex/14-playbooks/_ssot-rules/02-tone-and-posture.md`
3. `/codex/14-playbooks/_ssot-rules/06-show-dont-show-discipline.md`
4. `/codex/14-playbooks/experience/marketing-journey.md`
5. `/codex/14-playbooks/experience/briefings-hub.md`
6. `unified-trading-system-ui/components/shell/site-header.tsx`
7. `unified-trading-system-ui/components/shell/spaces-nav-sections.tsx`
8. `unified-trading-system-ui/components/shell/service-tabs.tsx`
9. `unified-trading-system-ui/components/shell/command-palette.tsx`
10. `unified-trading-system-ui/components/shell/nav-copy.ts`
11. Public-page routes under `unified-trading-system-ui/app/`: `/`, `/investment-management`, `/platform`,
    `/regulatory`, `/firm`, `/contact`, `/demo`, `/signup`, `/login`, `/briefings/**`

## Out of scope

- Auth / sign-up / sign-in flow changes (UI-only means cosmetic; any auth state-machine change is out).
- New routes or route renames — current URLs stay.
- Backend/API changes.
- Briefings content rewrites — polish = layout + TL;DR + CTA. Content rewriting is a future G2 item.
- Marketing copy for new DART rebrand (future roadmap).

## Phase breakdown

### Phase 12A — Audit public-page nav state

- [x] [AGENT] P0. Enumerate what nav component renders on each of the 9 public pages. Written to
      `/tmp/g1_12_nav_audit.md`. All 9 public routes already inherit `<SiteHeader>` via `app/(public)/layout.tsx`;
      briefings sub-tree adds `<BriefingAccessGate>` (a gate, not a shell).
- [x] [AGENT] P0. Inconsistencies identified: (a) shell DOM selector missing — `<header>` had no `data-shell` attribute;
      (b) CTA copy drift across briefings (no above-fold CTA); (c) exhaustive bulleted walls on `/briefings/<slug>`
      pages violating rule 02; (d) breadcrumb behaviour consistent (back link pattern on slug pages); (e) mobile
      breakpoint correct in SiteHeader (`hidden md:flex`) — no ad-hoc mobile treatment elsewhere.

### Phase 12B — Consolidate on `<SiteHeader>`

- [x] [AGENT] P0. Every public page already uses `<SiteHeader>` via `app/(public)/layout.tsx`. Added
      `data-shell="site-header"` attribute on the `<header>` root so Playwright can assert the consolidated shell.
- [x] [AGENT] P0. `SiteHeader` continues to consume `nav-copy.ts` SSOT — DART label, Investment Management / DART /
      Regulatory / Firm / Contact as top-level. No edits to `nav-copy.ts` (label already live per 2026-04-19).
- [x] [AGENT] P0. Briefings CTA standardised to "Book 45-minute call" → `/contact`, sourced from
      `lib/briefings/content.ts`. Marketing-journey shadow host keeps its "Book briefing" CTAs; no React-controlled CTA
      drift across the 9 public pages.
- [x] [AGENT] P0. Mobile breakpoint preserved — `<SiteHeader>` uses `hidden md:flex` on the nav slot; unchanged.

### Phase 12C — Briefings polish

- [x] [AGENT] P0. `<BriefingHero>` component added at `components/briefings/briefing-hero.tsx`. Renders title +
      one-sentence TL;DR + single primary CTA. Wired into each `/briefings/<slug>` page and the `/briefings` hub via
      `app/(public)/briefings/[slug]/page.tsx` and `app/(public)/briefings/page.tsx`. Exposes `[data-briefing-hero]` and
      `[data-testid="briefing-primary-cta"]` for Playwright.
- [x] [AGENT] P0. Slug pages restructured into three sections: Situation (`pillar.summary`) · Position (existing
      `pillar.bullets`, kept as-is, now under a framed heading) · Call (next-call copy + cross-links). Hub restructured
      into hero + "The three paths" section + developer-docs pointer.
- [x] [AGENT] P0. Hub page's per-pillar bullets removed (only TL;DR + "Open briefing →" link remains per card); slug
      pages' bullets retained as Position section (underlying content is unchanged — polish = layout only).
- [x] [AGENT] P0. `lib/briefings/content.ts` extended non-destructively: added `tldr` and `cta` fields to
      `BriefingPillar`; existing `summary` + `bullets` untouched.

### Phase 12D — Verify + QG

- [x] [SCRIPT] P0. UI vitest green — 40 tests passed, coverage 22.55% line-rate ≥ 15% floor.
- [x] [SCRIPT] P0. UI smoke build green — `next build` passed, cloudbuild.yaml + buildspec.aws.yaml schemas OK.
- [x] [SCRIPT] P0. UI QG green (`scripts/quality-gates.sh`) — full run (typecheck + lint + tests + build) in 20s.
- [x] [AGENT] P0. Playwright spec `tests/e2e/playbooks/refactor/refactor-g1-12-public-site-ia.spec.ts` — walks 9 public
      pages + 4 briefings pages (hub + 3 slugs), asserts `[data-shell="site-header"]` on every page,
      `[data-briefing-hero]` + single CTA on every briefings surface, no LOCKED-VISIBLE on public, anon stays on-path
      (G1.6 stub), orphan-reachability from header. 5/5 passed in 28.9s on tier-1 dev at `localhost:3100`.

## Critical files to be modified

- `unified-trading-system-ui/components/shell/site-header.tsx` — likely MODIFY (consolidate logic)
- `unified-trading-system-ui/components/shell/spaces-nav-sections.tsx` — MODIFY or REMOVE from public pages
- `unified-trading-system-ui/components/shell/nav-copy.ts` — READ-ONLY (already live)
- `unified-trading-system-ui/components/briefings/BriefingHero.tsx` — NEW
- `unified-trading-system-ui/app/layout.tsx` (or public-site layout wrapper) — MODIFY
- Each public-page file under `app/` — MODIFY (swap shell + add BriefingHero where applicable)
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-12-public-site-ia.spec.ts` — NEW

## Execution DAG

```
12A (audit)  →  12B (consolidate shell)  →  12C (briefings polish)  →  12D (QG + Playwright)
```

## Verification

1. Every public page uses `<SiteHeader>` — verified by Playwright asserting stable DOM selector
   `[data-shell="site-header"]` on all 9.
2. Every `/briefings/<slug>` has a `<BriefingHero>` at top — verified by Playwright.
3. No public URL returns 404 or 5xx — Playwright walks all 9 + 3.
4. UI QG green.
5. No auth changes — grep `lib/config/auth.ts` diff is empty in the commit.

## Handoff

Unblocks:

- **G2.x** — future public-site content rewrites can start from a clean IA baseline.
- **G1.14 presentation** — screenshots of the polished public pages feed into the HTML deck stretch goal (if G1.4
  completes).
- **Sales collateral generation (future G2)** — scope-manifested codex content can be surfaced through a consistent
  public-site shell.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100`
(tier-0 static) through MCP Playwright tools — navigate to each of the 9 public pages + 3 briefings pages, assert
consistent DOM structure via `browser_snapshot`, verify CTA copy + dropdown behaviour + mobile breakpoint. Iterate until
every page passes the consistency check.

**Durable spec for CI:** `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-12-public-site-ia.spec.ts`
— must:

1. Seed an `anon` (logged-out) state via `tests/e2e/playbooks/seed-persona.ts` — public pages do not require a persona,
   but the seed sets `VITE_MOCK_API=true` and skips any auth redirect.
2. Walk the canonical click-path: `/` → `/investment-management` → `/platform` → `/regulatory` → `/firm` → `/contact` →
   `/demo` → `/signup` → `/login` → `/briefings/<each slug>`.
3. Assert `[data-shell="site-header"]` present on every page.
4. Assert `<BriefingHero>` (`[data-briefing-hero]`) present on every `/briefings/*` page.
5. Assert no visible LOCKED-VISIBLE service-tile on public pages (G1.3 LOCKED-VISIBLE is for gated surfaces, not
   public).
6. Assert visibility-slicing vs G1.6 `access_control` formula once G1.6 lands — anon should see only public surfaces;
   stub until then.
7. Include orphan-reachability assertion — every public page reachable from main nav; no URL-only public page.
8. Wired into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G1.12 (Wave A, standalone — no
dependencies on other G1 items).**

---

You are executing **Refactor G1.12 — Public-site IA + briefings polish** for the Unified Trading System at Odum
Research. Wave A; parallelisable with 1.1, 1.3, 1.5, 1.9, 1.14-markdown.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm
git checkout live-defi-rollout && git pull
ls /codex/14-playbooks/experience/marketing-journey.md
ls /codex/14-playbooks/experience/briefings-hub.md
ls /codex/14-playbooks/_ssot-rules/02-tone-and-posture.md
ls ../unified-trading-system-ui/components/shell/site-header.tsx
ls ../unified-trading-system-ui/components/shell/nav-copy.ts
```

All must exist. STOP if any missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases 12A through 12D of this plan:
`plans/active/refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.md`

### Read-set (mandatory)

Paths in the plan's "Mandatory read-set" — all 11.

### Deliverables

- Modified: `components/shell/site-header.tsx`, public-page files under `app/`, public-site layout wrapper
- New: `components/briefings/BriefingHero.tsx`
- New test: `tests/e2e/playbooks/refactor/refactor-g1-12-public-site-ia.spec.ts`
- NO changes to `lib/config/auth.ts`, `lib/auth/`, or any route slug.

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (UI dev via `bash scripts/dev-tiers.sh --tier 1`) or `:3100` (tier-0 static) through MCP
Playwright tools during dev to walk all 9 public pages + 3 briefings pages, verify consistent SiteHeader + CTA + mobile
breakpoint + BriefingHero. Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g1-12-public-site-ia.spec.ts` — seed anon state via
`tests/e2e/playbooks/seed-persona.ts`, walk canonical click-path, assert `[data-shell="site-header"]` +
`[data-briefing-hero]` + consistent CTA copy, assert visibility-slicing vs G1.6 `access_control` formula (stub until
G1.6 lands), include orphan-reachability assertion, wire into `scripts/quality-gates.sh`.

### Commit strategy

UI repo:

```
cd unified-trading-system-ui
bash scripts/quickmerge.sh "refactor(ui): G1.12 — public-site IA + briefings polish (UI-only, no auth changes)" --agent
```

Fallback if quickmerge is blocked:

```
git add components/ app/ tests/
git commit -m "refactor(ui): G1.12 — public-site IA + briefings polish"
git push origin live-defi-rollout
```

### Success criteria

1. ✅ All 9 public pages render `<SiteHeader>` (Playwright-verified).
2. ✅ All 3 `/briefings/<slug>` pages render `<BriefingHero>`.
3. ✅ No auth changes — `git diff live-defi-rollout...HEAD lib/config/auth.ts lib/auth/` is empty.
4. ✅ No route slug changes — every former URL resolves.
5. ✅ UI QG green.
6. ✅ Playwright spec green on tier-1 dev.
7. ✅ Commit SHA pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP — multiple agents on `live-defi-rollout` concurrently is expected.
- Do NOT modify `lib/config/auth.ts` or anything under `lib/auth/` — UI-only refactor.
- Do NOT rewrite briefings content — polish layout / TL;DR / CTA only.
- Do NOT add or rename routes.
- Do NOT modify `components/shell/nav-copy.ts` DART label — already live.

### Report back

- Nav audit (9 rows, nav-component-before / nav-component-after).
- Briefings pages count + BriefingHero landed on each.
- Playwright spec path + pass status.
- Commit SHA pushed to live-defi-rollout.
- Any gaps or open questions for the user.
