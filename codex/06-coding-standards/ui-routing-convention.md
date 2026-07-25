---
doc_type: codex-ssot
title: UI routing convention — one URL scheme, plain routes only
summary:
  Every screen in a UI repo gets exactly one canonical URL via a plain top-level React Router route (`/deployments`,
  `/fleet`, ...). Query-param-driven view switching (`?tab=`) is banned as a top-level navigation scheme — it makes the
  shell own the URL, so embedded panes cannot own their own query params without colliding, which silently breaks filter
  deep-linking. Shared chrome persists across routes by living above `<Routes>`; a layout route + `<Outlet/>` is only
  needed when panes share cross-route state (e.g. a prefetch context), not for chrome alone.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, unified-trading-system-ui]
scope: [engineer]
tags: [ui, routing, url-scheme, react-router, deep-link, refactor]
related:
  [
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/06-coding-standards/ui-service-separation.md,
    /codex/05-infrastructure/deployment-ui-architecture.md,
  ]
created: 2026-07-24
authoritative_for: [UI top-level routing/URL-scheme convention]
referenced_by:
owner:
last_reviewed: 2026-07-24
code_refs:
  - deployment-ui/src/App.tsx
  - deployment-ui/src/components/NavMenu.tsx
  - deployment-ui/scripts/orphan-audit.ts
  - deployment-ui/tests/smoke/nav-menu-dedup.spec.ts
sources: [/plans/active/deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md]
---

# UI routing convention — one URL scheme, plain routes only

## The rule

A screen gets **exactly one canonical URL**, expressed as a plain top-level route (`/deployments`, `/fleet`, `/alerts`,
...). Do not gate top-level navigation behind a query param (`/cockpit?tab=deployments`) — if two URL forms reach the
same screen, pick the plain one and retire the other, don't let both live.

**Why this is a hard rule, not a style preference.** A query-param-owned view scheme means the SHELL owns the URL. An
embedded pane can then no longer own its own query params without colliding with the shell's `?tab=` key — the concrete
bug this fixed in deployment-ui: `Deployments.tsx` forked into a `localStatus` (embedded) vs
`searchParams.get("status")` (standalone) dual-path because `?tab=deployments&status=failed` couldn't disambiguate "tab"
from "the pane's own filter." Deep-linking (`/deployments?status=failed`) silently dropped filters the moment the pane
was embedded under a tab shell. Collapsing to one scheme deletes the dual-path entirely — there is only ever one URL, so
there is only ever one source of truth for a pane's state.

## Shared chrome: layout route is optional, not automatic

Moving off `?tab=` does **not** by itself require a React Router layout route (`<Outlet/>` + nested routes). Check which
is actually true first:

- **Chrome only** (header, top nav bar, no cross-pane data) → mount it **above** `<Routes>` in `App.tsx`. Each pane is
  then a plain top-level `<Route>` with its own `<main>`; the chrome persists for free because it was never inside the
  routed subtree to begin with. This is what deployment-ui does — verified on inspection there was no cross-pane state
  to preserve, so no layout route was needed at all.
- **Cross-pane state** (a shared prefetch context, tab-group-scoped cache, etc.) → THAT needs a layout route so the
  provider mounts once per group instead of once per pane. Don't reach for a layout route by default; add one only when
  a real cross-pane dependency forces it.

## Enforcement

- `deployment-ui/scripts/orphan-audit.ts` fails any declared route with no inbound `<Link>`, and its whitelist has **no
  "compat redirect" category** — nav entries and routes must move together in the same change. A legacy path that must
  keep working needs a real `<Navigate to="..." replace />` redirect route (e.g. `/repos` → `/ci`, `/infra` → `/fleet`),
  not a silent removal from nav while the route lingers unlinked.
- Testids split by origin, not by current shape: `cockpit-tab-<id>` for panes that were always top-level cockpit tabs,
  `cockpit-navlink-<id>` for screens that predate the cockpit shell — both map onto plain routes via a route→tabId
  lookup so existing Playwright specs keep driving the nav bar without a rewrite.
  (`deployment-ui/src/components/NavMenu.tsx`.)
- `pw:L2 ✓` + a cited regression spec covers every route change per [`ui-testing-layers.md`](ui-testing-layers.md) — for
  routing specifically, a deep-link test (load the URL with query params already set, assert the pane reflects them) is
  the proof a `?tab=`-style regression can't reappear silently.

## Reference implementation

deployment-ui (`deployment-ui@079b29e`, 2026-07-21) retired its `/cockpit?tab={health,deploy,deployments,fleet,...}`
scheme (10 tabs) down to plain top-level routes, deleting `searchParams.get("tab")` / `VALID_TABS` / `onTabChange` and
the `embedded ?` dual-path in `Deployments.tsx` (7 branches) — proof: the deep-link assertions in
`deployments-page.spec.ts` pass unweakened, where they previously failed honestly under the tab scheme. Full history:
[`deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md`](/plans/active/deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md)
(not yet archived as of 2026-07-24 — corrected from a premature archive-path reference).

`unified-trading-system-ui` has not needed this migration as of this doc's authoring — this convention applies to it too
if a similar query-param-gated view scheme grows there.

## Cross-references

- [`ui-testing-layers.md`](ui-testing-layers.md) — the `pw:L2 ✓` + cited-regression-spec gate every route change must
  satisfy; this doc covers the URL-scheme convention the testing layer verifies, not the test layers themselves.
- [`ui-service-separation.md`](ui-service-separation.md) — the broader UI/service repo-boundary rule this convention
  sits alongside.
- [`/codex/05-infrastructure/deployment-ui-architecture.md`](/codex/05-infrastructure/deployment-ui-architecture.md) —
  deployment-ui's tab-shell SSOT (which screens exist); this doc covers how they're addressed by URL, not which ones
  exist.
