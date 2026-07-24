---
doc_type: plan
title: ────────────────────────────────────────────────────────────────────────────
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

---

name: orphan-audit-policy-2026-04-21 overview: 3-phase rollout of an orphan-route audit in the UI repo. Phase 1 =
advisory report of Next `app/` routes unreachable from any declared navigation surface (lifecycle-nav, tile sub-routes,
chip hrefs, shell links, breadcrumbs). Phase 2 = fix all current orphans (add reachability OR delete). Phase 3 = block
quickmerge if a new orphan is introduced. User directive 2026-04-21: "prefer more tabs than less so filters hide them,
not orphan them." type: mixed epic: epic-code-completion status: active locked_by: live-defi-rollout locked_since:
2026-04-21

completion_gates: code: C2 deployment: D0 business: none

repo_gates:

- repo: unified-trading-system-ui code: C0 deployment: D0 business: none
- repo: unified-trading-pm code: C0 deployment: none business: none

depends_on: []

# ────────────────────────────────────────────────────────────────────────────

# CONTEXT

# ────────────────────────────────────────────────────────────────────────────

#

# During refactors (Phase 11 nav collapse, dashboard 11→5 tile collapse, Plan B

# strategy-catalogue rebuild), routes can silently orphan — the file still

# exists at `app/some/route/page.tsx` but no nav surface links to it. This:

# - wastes engineering effort (we keep "maintaining" unreachable pages)

# - creates security surface (routes with no access control)

# - surfaces only via direct URL typing (bad UX + demo risk)

#

# User's 3-phase policy:

# 1. Detect — scanner lists all orphans; report in CI but don't block.

# 2. Fix — resolve every current orphan (add reachability or delete).

# 3. Block — scanner exits 1 on new orphans; quickmerge pre-flight gate.

#

# Reachability sources (a route is "reachable" if ANY of these link to it):

# - lifecycle-nav items (`lib/lifecycle-mapping.ts` NAV_ITEMS)

# - SERVICE_REGISTRY `href` + `subRoutes[].href`

# - shell breadcrumbs

# - persistent side-rail/QuickActions

# - in-page `<Link>`s from already-reachable pages (transitive closure)

# - documented intentional exceptions whitelist

#

# ────────────────────────────────────────────────────────────────────────────

todos:

# ──────────────────────────────────────────────────────────────────────

# PHASE 1 — Advisory scanner (SEQUENTIAL, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p1-scanner-script content: |
  - [x] [AGENT] P0. Create `unified-trading-system-ui/scripts/orphan-audit.ts`: (a) Walk `app/` recursively; enumerate
        every `page.tsx|route.ts` → resolve to URL path (e.g. `app/(platform)/services/foo/page.tsx` → `/services/foo`).
        (b) Collect reachable routes from: SERVICE_REGISTRY (hrefs + subRoutes), lifecycle-mapping NAV_ITEMS, shell
        breadcrumbs, QuickActions shortcuts, plus a transitive `<Link>` closure (simple regex on `href="..."` in
        already-reachable pages). (c) Diff = orphans. Write `scripts/.orphan-audit-report.json` with
        `{orphans: string[], reachable_count, total_count, timestamp}`. (d) Allow a `.orphan-audit-whitelist.json` for
        documented intentional exceptions (auth callbacks, pending pages, deep-link-only tools). status: done

- id: p1-npm-script content: |
  - [x] [AGENT] P0. Add `npm run orphan-audit` to `package.json` invoking the scanner with `--advisory` flag (exits 0
        regardless, prints report). Add `--blocking` flag (exits 1 on new orphans vs a baseline file). status: done

- id: p1-baseline-snapshot content: |
  - [x] [AGENT] P0. Generate initial baseline: `npm run orphan-audit -- --write-baseline`. Writes
        `scripts/.orphan-audit-baseline.json` — the snapshot of "currently known orphans" that Phase 3 will gate on.
        status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 2 — Fix-all-current (SEQUENTIAL after Phase 1, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p2-triage-current-orphans content: |
  - [x] [AGENT] P0. Read the baseline report. For each orphan, triage: (a) KEEP + WIRE — page has legitimate purpose;
        add to a nav surface (lifecycle-nav, tile sub-route, or transitive link from a parent page). Document decision
        inline in scanner whitelist. (b) DELETE — page is obsolete (old POC, archived flow, superseded surface). Remove
        the directory. (c) WHITELIST — intentional direct-URL-only (e.g. `/pending`, auth callbacks). Add to
        `.orphan-audit-whitelist.json` with reason string. status: done

- id: p2-rebaseline content: |
  - [x] [SCRIPT] P0. After Phase 2 triage, re-run baseline generation. Baseline should now contain 0 orphans (or only
        whitelisted entries). status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 3 — Blocking gate (SEQUENTIAL after Phase 2, P1)

# ──────────────────────────────────────────────────────────────────────

- id: p3-wire-into-quickmerge content: |
  - [x] [AGENT] P1. Edit `unified-trading-system-ui/scripts/base-ui.sh` (or wherever pre-flight audit lives) to call
        `npm run orphan-audit -- --blocking` as part of the Phase-1 lint/type gate. Exit code 1 fails quickmerge.
        status: done

- id: p3-ci-workflow content: |
  - [x] [AGENT] P1. Add `.github/workflows/orphan-audit.yml` — runs scanner on every PR to main; posts comment with
        report. Fails on new orphans. status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 4 — Codex + propagation (PARALLEL, P1)

# ──────────────────────────────────────────────────────────────────────

- id: p4-codex-orphan-audit-doc content: |
  - [x] [AGENT] P1. Create `/codex/06-coding-standards/orphan-audit.md`: policy (3-phase rollout), scanner behaviour,
        whitelist rules, how refactoring PRs demonstrate compliance. status: done

- id: p4-propagate-to-other-uis content: |
  - [x] [AGENT] P1. Consider porting the scanner to `deployment-ui` — same 3-phase rollout. `user-management-ui` dropped
        from scope 2026-04-21: GitHub repo archived (gh repo archive), readiness YAML flipped to status=archived,
        workspace-manifest entry already marked archived. The code was folded into unified-trading-system-ui /ops/admin
        per plan ui*unification_v2_sanitisation_2026_04_20 Phase 6. Only deployment-ui remains as a port target;
        deferred until unified-trading-system-ui baseline proves stable (≥ 2 weeks green CI). *(archived 2026-04-22 —
        port still optional.)\_ status: deferred

# ────────────────────────────────────────────────────────────────────────────

# SUCCESS CRITERIA

# ────────────────────────────────────────────────────────────────────────────

# - `npm run orphan-audit` runs; outputs advisory report on current baseline

# - All current orphans triaged: wired / deleted / whitelisted

# - Baseline regenerated to 0 non-whitelisted orphans

# - quickmerge pre-flight + GHA both block new orphans (Phase 3)

# - Codex doc + clear whitelist-update policy

# ────────────────────────────────────────────────────────────────────────────
