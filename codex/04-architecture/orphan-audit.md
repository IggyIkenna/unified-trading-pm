---
doc_type: codex-ssot
title: Orphan-Route Audit Policy
summary:
  Policy for the UI orphan-route scanner (routes with no nav-surface reachability) — 3-phase advisory→fix-all→blocking
  rollout, 6-source reachability union, and the 3 acceptable whitelist reason prefixes (MACHINE-ONLY / API-HANDLER /
  UNAUTHENTICATED-FUNNEL); wired into quickmerge + orphan-audit.yml for both Next.js and React-Router UIs.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, unified-trading-system-ui]
scope: [engineer]
tags: [ui, audit, orphan-route, reachability, quality-gates, refactor]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
    /codex/09-strategy/architecture-v2/dashboard-services-grid.md,
  ]
created: 2026-04-21
authoritative_for: [UI orphan-route audit policy, orphan-audit whitelist reason prefixes]
referenced_by: [/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Orphan-Route Audit Policy

> **Status:** canonical (2026-04-21) **Owner:** UI Architecture **SSOT for:**
> `unified-trading-system-ui/scripts/orphan-audit.ts`, `unified-trading-system-ui/scripts/.orphan-audit-baseline.json`,
> `unified-trading-system-ui/scripts/.orphan-audit-whitelist.json`,
> `unified-trading-system-ui/.github/workflows/orphan-audit.yml`. **Plan:**
> [`plans/archive/orphan_audit_policy_2026_04_21.plan.md`](../../plans/archive/orphan_audit_policy_2026_04_21.plan.md)

---

## §1 — The problem

Successive refactors (Phase-11 nav collapse, dashboard 11→5 tile collapse, Strategy Catalogue 3-tier rebuild) have a
failure mode: the route file at `app/some/route/page.tsx` still exists, but no navigation surface links to it any more.
The page silently orphans.

This costs us three ways:

1. **Maintenance tax.** Engineers keep updating a page that no user will ever find.
2. **Security surface.** Orphaned pages may lack entitlement gating that the nav surfaces enforce upstream.
3. **UX + demo risk.** Orphans only surface via direct URL typing. A demo-mode dry-run can miss them; a prospect who
   lands on one via a stale bookmark sees a page disconnected from the shell.

User directive (2026-04-21): _"prefer more tabs than less so filters hide them, not orphan them."_ Translation: when in
doubt between deleting a route and adding another navigation hook, **add the hook**. Filters can collapse a long tab
list; orphans cannot.

---

## §2 — The 3-phase rollout

| Phase | Mode     | Scanner behaviour                                                 | Quickmerge gate |
| ----- | -------- | ----------------------------------------------------------------- | --------------- |
| 1     | Advisory | Walk `app/`, compute reachability, emit report; always exit 0     | None            |
| 2     | Fix-all  | Humans triage every current orphan → wire / delete / whitelist    | None            |
| 3     | Blocking | Scanner exits 1 on new orphans vs baseline; wired into quickmerge | Blocks merge    |

The phases ship sequentially. **Do not** skip Phase 2 and go straight to blocking — the scanner will fail every
quickmerge until the backlog is triaged. Phase 2 brings the baseline to 0 non-whitelisted orphans; Phase 3 freezes that
state.

---

## §2.5 — Whitelist Triage Rule

The whitelist is for routes that are NOT and CANNOT BE human-navigable from any nav surface. Reviewers rejecting a
whitelist PR MUST apply this test:

> Can a human user (any persona) gain from seeing this page? If yes, it does NOT belong in the whitelist — it needs a
> nav surface.

### Acceptable whitelist reasons

- **`MACHINE-ONLY`** — consumed by k8s / Cloud Run / monitoring as a liveness/readiness probe. Example: `/health`. No
  human should ever navigate there; it returns JSON to a machine caller.
- **`API-HANDLER`** — Next.js `route.ts` endpoint invoked via `fetch()` from a component. Example:
  `/api/accounts/transfer-history`. Not a page; the UI that uses it IS reachable.
- **`UNAUTHENTICATED-FUNNEL`** — the user literally cannot act on the page until an OAuth redirect or session-establish
  flow completes. Examples: `/login`, `/signup`, `/pending`. These self-bootstrap from direct URL entry or OAuth
  callback.

### Unacceptable whitelist reasons (these need NAV wiring instead)

- **"Admin-only, no public nav by design"** — wire into the Admin & Ops tile sub-routes. Admin is a role gate, not a
  reachability reason.
- **"Deep-link from another page's click handler"** — if the other page is reachable and clicks through to this one, the
  scanner should detect it. If the scanner misses programmatic navigation (`router.push` / `window.location`), fix the
  scanner — don't whitelist.
- **"Query-param driven drilldown"** — add an explicit `<Link>` (even if the canonical entry is via POST-then-redirect)
  so a tab-handover or back-button nav works.
- **"Internal tool"** — internal roles still navigate. Wire it into an internal-only tile sub-route.

### Reason string format (enforced by reviewer + test)

Each whitelist entry's `reason` field MUST start with one of: `MACHINE-ONLY`, `API-HANDLER`, or
`UNAUTHENTICATED-FUNNEL`. If your reason doesn't fit one of those three prefixes, the page belongs in a nav surface, not
the whitelist. The executable enforcement lives in
[`unified-trading-system-ui/__tests__/scripts/orphan-audit-detection.test.ts`](../../../unified-trading-system-ui/__tests__/scripts/orphan-audit-detection.test.ts)
— a vitest run fails if a whitelist entry uses a disallowed reason prefix.

### Programmatic-navigation detection

Before adding an entry with an "admin deep-link" or "programmatic redirect" excuse, remember the scanner now recognises:

- `<Link href="/path">` (static + template-literal form)
- `router.push("/path")` / `router.replace("/path")` (any identifier, not just `router`)
- `redirect("/path")` (Next.js server actions)
- `window.location.href = "/path"` / `window.location.assign("/path")` / `window.location.replace("/path")`
- `path: "/path"` / `href: "/path"` entries in nav config object literals
- `source: "/x"` / `destination: "/y"` redirect entries in `next.config.{mjs,js,ts}`
- Any generic `"/foo"` / `` `/foo` `` literal in `app/`, `components/`, `hooks/`, `lib/`

If your deep-link pattern still isn't caught, extend the scanner regex — don't whitelist the route.

---

## §3 — Scanner behaviour

### What counts as a route

- Any `app/**/page.tsx` or `app/**/route.ts` file.
- Path resolved by Next routing rules: route groups `(foo)` are stripped; dynamic segments `[id]` resolve as a
  parameterised route. Dynamic routes are treated as reachable if a static parent link passes an `[id]` via
  `<Link href={`/foo/${id}`}>`.

### What counts as a reachability source

A route is **reachable** if at least one of the following references it:

1. **`SERVICE_REGISTRY`** — any tile's `href` or any `subRoutes[].href` in `lib/config/services.ts`.
2. **`NAV_ITEMS`** — lifecycle-nav item declared in `lib/lifecycle-mapping.ts`.
3. **Shell breadcrumbs** — `components/shell/breadcrumbs.tsx` declared paths.
4. **QuickActions / side-rail** — any persistent shell shortcut in `components/shell/`.
5. **Transitive `<Link>` closure** — a regex scan for `href="/..."` or `href={`/...`}` on already-reachable pages;
   recursed to a fixed point. This catches in-page cross-links (a /dashboard card linking to /foo/bar).
6. **Explicit whitelist** — `.orphan-audit-whitelist.json` entries (see §4).

Reachability is the **union** of all six sources. A route needs **one** hit to be considered reachable.

### What the scanner outputs

```
scripts/.orphan-audit-report.json
  {
    "orphans": ["/foo/bar", "/baz"],
    "reachable": ["/dashboard", "/services/trading/overview", ...],
    "reachable_count": 142,
    "total_count": 145,
    "whitelist_used": ["/pending", "/auth/callback"],
    "timestamp": "2026-04-21T14:23:00Z"
  }
```

Also prints a human-readable table to stdout:

```
 ORPHAN AUDIT — 3 orphan(s) / 145 routes
 ───────────────────────────────────────
 ✗ /services/strategy/old-builder     (no reachability)
 ✗ /admin/legacy/users                (no reachability)
 ✗ /docs/v1-api                       (no reachability)
 ───────────────────────────────────────
```

### Exit codes

| Flag               | Behaviour                                                          |
| ------------------ | ------------------------------------------------------------------ |
| `--advisory`       | Always exit 0. Used in Phase 1.                                    |
| `--write-baseline` | Write current orphan set to `.orphan-audit-baseline.json`; exit 0. |
| `--blocking`       | Exit 1 if `orphans ⊄ baseline` (i.e. any NEW orphan introduced).   |

`--blocking` deliberately tolerates pre-existing baselined orphans — Phase 3 freezes the state the team shipped; only
**new** orphans are gated. (Phase 2 clears the baseline to 0 or to a whitelisted-only set.)

---

## §4 — Whitelist rules

`.orphan-audit-whitelist.json`:

```json
{
  "whitelist": [
    {
      "route": "/pending",
      "reason": "Generic pending screen — reachable only by direct redirect from server actions",
      "added": "2026-04-21",
      "owner": "platform-ui"
    },
    {
      "route": "/auth/callback",
      "reason": "OAuth callback — reachable only via provider redirect",
      "added": "2026-04-21",
      "owner": "auth"
    }
  ]
}
```

**Whitelist is only for intentional orphans.** See §2.5 Whitelist Triage Rule for the reviewer test and the three
acceptable reason prefixes (`MACHINE-ONLY`, `API-HANDLER`, `UNAUTHENTICATED-FUNNEL`). If your reason doesn't start with
one of those, the page needs nav wiring, not a whitelist entry. Every entry requires:

- `route` — the URL path.
- `reason` — **must begin with** `MACHINE-ONLY` / `API-HANDLER` / `UNAUTHENTICATED-FUNNEL` (see §2.5).
- `added` — ISO date.
- `owner` — team / persona responsible.

Whitelisted entries **still count in `total_count`** but are subtracted from `orphans` in the report — they don't fail
the blocking gate.

### Common legitimate whitelist cases

- OAuth / auth callbacks reachable only via provider redirect.
- Generic status pages (`/pending`, `/unauthorized`) hit via server-side redirects only.
- Deep-link-only diagnostic tools used by ops with shared URLs, not via nav.
- A/B variant pages routed by a feature flag at the edge.

### Non-legitimate cases

- "We'll wire it up later." → Either wire it now or delete.
- "It's linked from an admin email." → Still not reachability; put the link in the admin tile.
- "It's used in tests." → Test routes should live under `__tests__/`, not `app/`.

---

## §5 — How refactor PRs demonstrate compliance

Every PR that touches navigation, routing, or page structure MUST show orphan-audit clean in its CI comment. The Phase 3
GHA workflow (`.github/workflows/orphan-audit.yml`) posts a comment:

```
🟢 Orphan audit: 0 new orphans
   145 routes / 142 reachable / 3 whitelisted
```

or:

```
🔴 Orphan audit: 2 NEW orphan(s)
   - /services/strategy/old-builder
   - /admin/legacy/users
   Action: wire via SERVICE_REGISTRY / lifecycle-nav, delete the route, OR
   add a whitelist entry with reason in scripts/.orphan-audit-whitelist.json
```

PRs cannot merge with a red status. Three legitimate responses:

1. **Wire** — add the route to `SERVICE_REGISTRY` or equivalent nav surface. Most refactor PRs use this path.
2. **Delete** — remove the `app/foo/page.tsx` directory entirely. Clean break; no deprecation shim.
3. **Whitelist** — add to `.orphan-audit-whitelist.json` with a reason that survives review.

### Encouraged pattern (per user directive): "prefer more tabs"

When a page's logical owner is unclear during a refactor, prefer wiring it as a sub-route chip on the closest
`SERVICE_REGISTRY` tile (add a chip rather than orphan). Chips can later be hidden behind filters / persona gates via
`persona-dashboard-shape.ts` — but they stay reachable, auditable, and demo-safe.

---

## §6 — Wiring into quickmerge

The blocking gate is pre-flight in `scripts/base-ui.sh`:

```bash
# unified-trading-system-ui/scripts/base-ui.sh (Phase 1: lint + typecheck + orphan audit)
npm run orphan-audit -- --blocking
```

Exit 1 fails the gate; quickmerge exits before commit. The exact phase insertion matches the existing lint/type slot —
running before commit means authors see failures locally, not only in CI.

### `npm run orphan-audit` wiring

```json
{
  "scripts": {
    "orphan-audit": "tsx scripts/orphan-audit.ts"
  }
}
```

Flags:

- Bare `npm run orphan-audit` (Phase 1 advisory): `--advisory` implied, exit 0.
- `npm run orphan-audit -- --write-baseline` (Phase 2 tool): refresh baseline after triage.
- `npm run orphan-audit -- --blocking` (Phase 3 gate): exit 1 on new orphans.

---

## §7 — CI workflow

`.github/workflows/orphan-audit.yml` runs on every PR to main:

```yaml
name: orphan-audit
on:
  pull_request:
    branches: [main]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run orphan-audit -- --blocking
      - name: PR comment
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const report = require('./scripts/.orphan-audit-report.json');
            // post formatted comment per §5
```

---

## §8 — Porting to sibling UIs

| UI                          | Status                 | Framework                                                                                                      | Scanner location                                                                          |
| --------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `unified-trading-system-ui` | ✅ shipped             | Next.js app/                                                                                                   | `scripts/orphan-audit.ts` (discovers via filesystem walk of `app/**`)                     |
| `deployment-ui`             | ✅ shipped 2026-04-22  | Vite + React Router v6                                                                                         | `scripts/orphan-audit.ts` (React Router variant — discovers via `<Route path="...">` JSX) |
| `user-management-ui`        | 🗄️ archived 2026-04-21 | n/a (folded into unified-trading-system-ui /ops/admin per `ui_unification_v2_sanitisation_2026_04_20` Phase 6) | —                                                                                         |

The React Router variant is a near-twin of the Next.js variant: same whitelist / baseline / blocking contract, same
`--advisory` / `--blocking` / `--write-baseline` CLI, same policy doc (this file). The one variant-specific wrinkle: the
scanner must scrub `<Route path="...">` declarations from content before the generic path-literal harvest, otherwise the
declaration's own path literal satisfies the self-reachability check and every declared route appears reachable via
itself. This was caught during port (2026-04-22) via a stub-route regression test.

Porting cost to a hypothetical future UI is low — copy the scanner that matches the framework, update the whitelist /
baseline stubs, run `--write-baseline`, triage the surfaced orphans, add the 3 npm scripts.

---

## §9 — Cross-references

- `unified-trading-system-ui/scripts/orphan-audit.ts` — implementation.
- [`/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`](/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md)
  §8 — example refactor that ships orphan-audit-compliant.
- [`/codex/09-strategy/architecture-v2/dashboard-services-grid.md`](/codex/09-strategy/architecture-v2/dashboard-services-grid.md)
  — `SERVICE_REGISTRY` is the primary reachability source.
- `memory/feedback_orphan_audit_3_phase_rollout.md` — the user's preference that shaped this policy.
