---
doc_type: plan
title: deployment-ui — Alerts page rebuild (WS-5 Plan B — filters, sort, date-range, drill-down)
summary: >-
  Rebuild the /alerts page into a usable diagnostic view — sortable columns, filters on source/severity/subject/
  service, a date-range picker, and clickable drill-downs — reusing the filter/sort primitives extracted into shared
  components by the date-range-filter plan (no second edit of Deployments.tsx). Draft-gated on the ingestion plan (Plan
  A): the page can only filter/sort on fields that actually arrive, so this stays draft until Plan A lands the
  normalised schema and mirrors the alerting-service sources. Two cheap wins independent of Plan A: the timeline drops
  workflow_name and truncates the timestamp to HH:MM (hiding the date) — both are already in the payload.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-ui, alerts, filters, sort, observability]
related:
  - deployment_ui_observability_ux_tracker_2026_07_17.md
  - deployment_alerts_ingestion_completeness_2026_07_20.md
  - deployment_ui_date_range_filter_and_search_2026_07_20.md
created: "2026-07-20"
last_updated: "2026-07-20"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2
assigned_role: ui_developer
drift_direction: advance-code
sequential: true
depends_on:
  - deployment_alerts_ingestion_completeness_2026_07_20.md
  - deployment_ui_date_range_filter_and_search_2026_07_20.md
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: split from deployment_ui_observability_ux_tracker_2026_07_17.md WS-5, UX audit + operator decisions 2026-07-20
---

# deployment-ui — Alerts page rebuild (Plan B)

> **🟢 Activated gated (operator 2026-07-21)** — `status: active` + `gate_on_depends: true`. AO ingests this plan now
> but **machine-holds every task** until BOTH prerequisites complete: Plan A
> (`deployment_alerts_ingestion_completeness_2026_07_20.md`, the normalised alert schema + alerting-service mirror) and
> the date-range-filter plan (`deployment_ui_date_range_filter_and_search_2026_07_20.md`, which OWNS the shared
> filter/sort primitive extraction — already landed at `deployment-ui@1cf191b`). The page can only filter/sort on fields
> that actually arrive, so the gate is the correctness guarantee, not just ordering.

## Context — UX audit findings (2026-07-20, read-only)

- **Page structure** — the `/alerts` route → `CockpitAlerts` → `AlertsLogsTab` (`components/cockpit/AlertsLogsTab.tsx`),
  which stacks two independent sections: `cockpit-alerts-section` (the ledger, `AlertsContent` from `pages/Alerts.tsx`)
  and `cockpit-logs-section` (a target input driving `StreamingLogsPanel` via SSE, controlled by `?logs=`). Grep the
  component names to locate them — do not trust line numbers.
- **`AlertsContent` (`pages/Alerts.tsx`)** has two cards: `alert-streams` (per repo/workflow current-vs-previous,
  worst-first) and `alert-timeline` (raw newest-first list).
- **No filter / sort / date-range / URL params today** beyond `?logs=`. Only interactive state: a refresh button + 60s
  auto-poll. The complaint is exactly accurate.
- **Field availability** (the `RepoCiAlertEntry` type in `api/client.ts`) — the type is thin: `kind`, `timestamp`,
  `repo`, `workflow_name`, `severity`, `conclusion`, `message`, `run_url`, `deployment_target`. No backend field is
  entirely unrendered, so there's no big "just show the hidden data" win — **but two cheap ones exist**: `workflow_name`
  is rendered in the streams card yet **dropped from the timeline rows**, and `timestamp` is truncated to `HH:MM` (in
  the timeline-row render inside `AlertsContent` — grep for the `HH:MM` / `toLocaleTimeString` formatting) so the **date
  is invisible** in the timeline. Both are already in the payload — no backend change needed for these two.
- **Any filter/sort dimension beyond the current thin fields needs Plan A** to land it in the normalised schema — which
  is why this plan is gated.
- **Shared primitives — ALREADY EXTRACTED** by the date-range-filter plan (`deployment-ui@1cf191b`, refactor: "extract
  shared filter/sort primitives"). Import them; do NOT re-edit `Deployments.tsx` or re-derive them. Grep each module by
  its export name — never a line number:
  - `FilterSelect` → `src/components/filters/FilterSelect.tsx`
  - `StatusFilterChips` + its `StatusChip` interface (generalized to take a computed `chips[]` prop) →
    `src/components/filters/StatusFilterChips.tsx`; tone classes `ChipTone`/`TONE_CLASSES` →
    `src/components/filters/chipTone.ts`
  - the click-to-sort state machine `useColumnSort` (returns `{ sort, onHeaderClick }`, generic over a sort-key type) →
    `src/hooks/useColumnSort.ts`
  - the nulls-last / tie-break column comparator `compareByColumn` → `src/lib/columnSort.ts`

  The deployment-specific plug-ins (`SortKey`, `columnSortValue`, `defaultHierarchyCmp`, the always-on `forceLast`
  override) stayed LOCAL in `Deployments.tsx` as example callbacks — the alerts page supplies its OWN equivalents (an
  alert sort-key union + an alert `columnSortValue`) into the generic utilities. The URL-param read/write convention
  (`searchParams.get/set` + `setSearchParams(fn,{replace:true})`) is replicated with non-colliding param names alongside
  the existing `?logs=`.

- **Regression spec** — `tests/smoke/alerts-page.spec.ts` pins (grep the file for the CURRENT set — do NOT assume a
  count, tests get added): cockpit-tile routing; the `alerts-page`/`alert-streams`/`alert-timeline` testids; worst-first
  stream order + newest-first timeline; `run_url` href shape `actions/runs`; the domain chip on every row; the source
  badge (+ "MOCK" in mock mode); and the `deployment_target` deep-link (`a[href="/deployments/..."]`). **The rebuild
  MUST keep every existing assertion in that spec green** — it is the regression contract.

## Decisions (operator, 2026-07-20)

1. **Diagnostic view** — the page is for filtering/sorting/drilling to find root causes; "done" is a _clear_ page.
   Prioritise the dimensions that help diagnosis: source, severity, subject-repo/service, time.
2. **Reuse, don't duplicate** — consume the shared filter/sort components the date-range plan extracts; do not re-edit
   `Deployments.tsx`, do not fork a parallel filter bar.
3. **URL-backed** — every filter/sort/date-range param is URL-backed and deep-linkable (plain-routes contract), with
   non-colliding names alongside `?logs=`.

## Todos

- [x] ✅ [UI] P1. **Cheap wins, independent of Plan A** — render `workflow_name` in the timeline rows; show the full
      date (not just `HH:MM`) on timeline entries so the date component is visible. Both fields already exist in the
      payload. `pw:L2 ✓`. — `deployment-ui@17fbb72`: extended the existing timestamp slice to `YYYY-MM-DD HH:MM` (was
      `HH:MM`-only) and added a `workflow_name` span next to `repo` in the timeline row (previously only rendered in the
      streams card). New spec `tests/smoke/alerts-page.spec.ts` § "timeline entries show the full date... and the
      workflow name" pins both on the newest-first `entry-0` row; every pre-existing assertion in that spec stays green
      (9/9 pass). `quality-gates.sh` green.
- [x] ✅ [UI] P1. **Sortable columns** — make the timeline table columns sortable (timestamp, severity, source, subject)
      using the shared `useColumnSort` hook + `compareByColumn`, supplying an alert-specific sort-key union and
      `columnSortValue`. Default order stays newest-first / worst-first (regression spec); user sort overrides it.
      URL-backed sort key + direction. — `deployment-ui@c631ef5`: `useColumnSort` gained an optional `initial` param
      (backward-compatible — `Deployments.tsx`'s existing no-arg call unaffected) so `Alerts.tsx` can seed the hook from
      `?sort_key=&sort_dir=` on mount; `alertColumnSortValue` maps `timestamp`/`severity` (rank)/`source`
      (`kindLabel`)/`subject` (`repo`) to a comparable value, ties broken by the existing newest-first default via
      `compareByColumn`'s tie-break contract. A header click cycles asc → desc → back to default (clears both URL
      params). New `pw:L2` spec pins the click-to-cycle behaviour + URL persistence; every existing
      `alerts-page.spec.ts` assertion and `deployments-page.spec.ts` (shared-hook regression check) stay green.
      `quality-gates.sh` green.
- [x] ✅ [UI] P1. **Filter bar** — source/plane, severity, subject-repo, service filters using the extracted
      `FilterSelect`, URL-backed. Options derived from the loaded normalised alert set. — deployment-ui@e6234d16. New
      `MultiChipFilter` (generic Set-backed multi-select chip row, generalizing Deployments.tsx's `KindFilterChips`) for
      kind/severity (multi-select, comma-joined URL param); `FilterSelect` reused as-is for repo/service
      (single-select). `?kind=&severity=&repo=&service=` all URL-backed via the existing `setParam` pattern; a
      `filteredAlerts` memo ANDs all four dimensions before the existing sort; result-count + clear-filters affordances;
      new `alerts-filter-empty` state distinguishes "0 alerts match filters" from "0 alerts in ledger". 7 new `pw:L2`
      cases added to `tests/smoke/alerts-page.spec.ts` (chip toggle + URL persistence, multi-select additivity, dropdown
      filtering, clear-filters, filtered-empty-vs-ledger-empty) — all 9 pre-existing assertions in that spec stay green
      (16/16 passed). `quality-gates.sh` green (sentinel ddecdec).
- [x] ✅ [UI] P1. **Date-range picker** — URL-backed `?alert_from=&alert_to=`, wired to the ledger's widened retention
      window from Plan A. Explicit "no data before `<date>`" state when the range exceeds retention (same honesty
      pattern as the deployments date-range plan). — deployment-ui@89cf1f87. Local `AlertDateRangeFilter` (mirrors
      Deployments.tsx's `DateRangeFilter` UX — atomic clear, no artificial `min`/`max` blocking a pick — but stayed
      local rather than joining the shared `filters/` primitives, since the two pages' backends have different
      contracts: deployments queries an explicit server-side `date_from`/`date_to`, alerts only has a `days`-back window
      (`_DEFAULT_DAYS = _MAX_DAYS = 30`, deployment-api@cda7a89), so `[alert_from, alert_to]` filters client-side over
      the already-loaded 30-day window instead). `RepoCiAlerts`/`UnifiedAlerts` client type gained the
      `days`/`total_count`/`returned_count`/`offset`/`limit`/`capped` fields the backend has served since Plan A
      (previously unread by the frontend) — `days` is the honesty source for the retention-floor banner
      (`retentionFloorDate = today − (data.days − 1)`) rather than a hardcoded "30" that could drift from the backend's
      own constant. 4 new `pw:L2` cases in `tests/smoke/alerts-page.spec.ts` (inclusive-bounds narrowing, banner fires
      only when `alert_from` predates the floor, the widget's own atomic clear, page-level clear-filters also clears the
      date range) — all 16 pre-existing assertions stay green (20/20 passed). `quality-gates.sh` green (sentinel
      e6234d16).
- [x] ✅ [UI] P1. **Drill-down links** — per-row deep-links: `deployment_target` → `/deployments/:name` (preserve the
      pinned href shape), `run_url` → the external run, log stream → `?logs=<target>`, runbook link where the normalised
      row carries one. A row with an `alert_class`/source that has a detail view links to it. — deployment-ui@fe767f19.
      The `/deployments/:name` link and the external `run_url` link were already shipped (parity #4 + the original
      page). New: a "Stream logs" button on any row carrying `deployment_target`, calling the page's own `setParam` to
      set the SAME `?logs=<target>` sub-param `AlertsLogsTab.tsx` already owns and reads (its own header comment
      described this exact deep-link as the intended contract — `AlertsContent` is always rendered inside
      `AlertsLogsTab`, so both components observe the one shared `useSearchParams()` location; setting `?logs=` here
      correctly swaps `cockpit-logs-empty` for the live `StreamingLogsPanel`). Runbook link: grepped the full
      `AlertEntryDict` (backend TypedDict), `RepoCiAlertEntry` (frontend type), and `mockRepoCiAlerts()` — no
      `runbook`/`runbook_url` field exists in any of the three, so no row can ever carry one today; not implemented (a
      speculative field nothing populates), left for whichever future ingestion todo adds it. 1 new `pw:L2` case in
      `tests/smoke/alerts-page.spec.ts` (click → `?logs=` set → empty-state placeholder replaced) — all 20 pre-existing
      assertions stay green (21/21 passed). `quality-gates.sh` green (sentinel 32a14ebb).
- [x] ✅ [UI] P2. **Layout / "proper view"** — restructure the two-card layout into a usable table-first view per the
      operator's "not proper right now" complaint; keep the streams summary but make the timeline the primary,
      filterable/sortable surface. Preserve every `data-testid` the regression spec depends on. —
      deployment-ui@f47d0ac1. Filed BLK-de39d214 (todo was subjective operator language with no concrete spec) covering
      two independent calls: (1) how to visually demote Streams vs Timeline, (2) whether the Timeline markup should
      become a real `<table>`. Main answered: (1) Streams stays a visible compact single-line-per-stream summary strip
      (dropped Card/CardHeader/CardContent chrome, `text-xs`, tighter padding — same DOM position above Timeline, zero
      reorder) — option A of 3, chosen because C ("no change") ignores the operator's stated dissatisfaction and B
      (collapsed `<details>`) violates "streams STAYS a summary" by hiding it. (2) Do NOT convert Timeline rows to a
      `<table>` — "filterable/sortable" is behavior (state + handlers), not markup, and a flex-div→table rewrite is the
      highest-risk change to the preserve-every-testid constraint for zero required benefit; added `role="table"`/
      `role="row"` to the existing flex divs instead (semantic a11y, zero testid churn). A first attempt at the
      `<table>` conversion was built, verified (21/21 pw:L2 green), then fully reverted per this answer before shipping
      — the shipped commit only contains the Streams compaction + ARIA roles. New `pw:L2` case in
      `tests/smoke/alerts-page.spec.ts` pins the visual-hierarchy contract main required (Streams summary label + DOM
      order before Timeline; Timeline keeps its CardTitle; every pre-existing testid resolves) — all 21 pre-existing
      assertions stay green (22/22 passed). `quality-gates.sh` green (sentinel fe767f19).
- [x] ✅ [REVIEW] P1. **Regression + new specs** — extend `tests/smoke/alerts-page.spec.ts` (or a sibling) to cover the
      new filter/sort/date-range/deep-link behaviour while keeping every existing assertion in that spec green.
      `pw:L2     ✓` with the spec cited. No tick without it. — deployment-ui@4aa865c4. Each dimension already got
      isolated coverage as its own todo shipped (filter bar +7 cases, date-range +4, drill-down +1, layout +1 — 13 cases
      across 4 prior commits, all still green); this todo's own contribution is the one deliberately COMBINED case that
      was genuinely missing — kind-filter + date-range + column-sort all active at once, proving the independent
      `useMemo` layers (filter → sort) compose correctly instead of one clobbering another. Note on
      `assigned_role:     review`: `agents/review.md` describes a persistent, non-committing UAT daemon
      (`does_not: Edit / commit code`) — incompatible with this todo's own text (a concrete "extend the spec file"
      change) and its `done_definition: "Checkbox flipped in plan + code shipped"`; treated the `[REVIEW]` prefix as the
      per-task tag convention (routes-the-todo, not "become the daemon") and shipped it as a normal worker task. Full
      spec now 23/23 green. `quality-gates.sh` green (sentinel f47d0ac1).
- [x] ✅ [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'`) + flip todos same turn (`docs(plans):`). —
      already cumulatively satisfied: every one of the 7 preceding todos was shipped via `quality-gates.sh` →
      `quickmerge.sh --agent --files '<paths>'` → same-turn `docs(plans):` checkbox flip + push, individually
      (deployment-ui@17fbb72/c631ef5/e6234d16/89cf1f87/fe767f19/f47d0ac1/4aa865c4). No new commit — nothing outstanding
      to ship at this checkpoint.
- [ ] [REVIEW] P2. Post-phase codex audit — document the rebuilt alerts-page contract (diagnostic surface, the
      filter/sort/date-range dimensions, the shared-primitive reuse, the drill-down link map) in
      `codex/06-coding-standards/ui-testing-layers.md` cross-ref + `codex/04-architecture/ci-alerting.md`.

## Success criteria

- The alerts timeline is filterable (source, severity, subject, service), sortable by column, and date-range bounded —
  all URL-backed and deep-linkable.
- Every row drills through to its detail (deployment, run, log stream, runbook) — an alert is a clickable pointer to a
  root cause, not a dead line of text.
- The two cheap wins land regardless of Plan A: `workflow_name` visible in the timeline, full date shown.
- Every existing `alerts-page.spec.ts` assertion stays green; new behaviour has its own cited regression spec.
- No re-edit of `Deployments.tsx`; the shared filter/sort primitives are imported, not duplicated.

## Progress Log

- **2026-07-20** — Split from `deployment_ui_observability_ux_tracker_2026_07_17.md` WS-5 as Plan B of two. UX audit
  found: no filters/sort/date-range exist today; the type is thin so there's no big hidden-field win, but two cheap wins
  (timeline drops `workflow_name`, truncates the timestamp to `HH:MM`); the filter/sort primitives are local to
  `Deployments.tsx` and unexported. Operator: reuse the primitives the date-range plan extracts (one owner of that
  file), keep the page a diagnostic surface, URL-back everything. Gated on Plan A (ingestion) because the filter
  dimensions depend on the normalised schema and the mirrored sources landing first.

## Codex SSOTs

- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited regression spec), every `[UI]` todo.
- `codex/04-architecture/ci-alerting.md` — the alert data contract Plan A defines; this plan renders it.
