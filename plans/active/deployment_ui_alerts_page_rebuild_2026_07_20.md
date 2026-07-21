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
- [ ] [UI] P1. **Sortable columns** — make the timeline table columns sortable (timestamp, severity, source, subject)
      using the shared `useColumnSort` hook + `compareByColumn`, supplying an alert-specific sort-key union and
      `columnSortValue`. Default order stays newest-first / worst-first (regression spec); user sort overrides it.
      URL-backed sort key + direction.
- [ ] [UI] P1. **Filter bar** — source/plane, severity, subject-repo, service filters using the extracted `FilterSelect`
      (multi-select where it helps), URL-backed. Options derived from the loaded normalised alert set.
- [ ] [UI] P1. **Date-range picker** — URL-backed `?alert_from=&alert_to=`, wired to the ledger's widened retention
      window from Plan A. Explicit "no data before `<date>`" state when the range exceeds retention (same honesty
      pattern as the deployments date-range plan).
- [ ] [UI] P1. **Drill-down links** — per-row deep-links: `deployment_target` → `/deployments/:name` (preserve the
      pinned href shape), `run_url` → the external run, log stream → `?logs=<target>`, runbook link where the normalised
      row carries one. A row with an `alert_class`/source that has a detail view links to it.
- [ ] [UI] P2. **Layout / "proper view"** — restructure the two-card layout into a usable table-first view per the
      operator's "not proper right now" complaint; keep the streams summary but make the timeline the primary,
      filterable/sortable surface. Preserve every `data-testid` the regression spec depends on.
- [ ] [REVIEW] P1. **Regression + new specs** — extend `tests/smoke/alerts-page.spec.ts` (or a sibling) to cover the new
      filter/sort/date-range/deep-link behaviour while keeping every existing assertion in that spec green. `pw:L2 ✓`
      with the spec cited. No tick without it.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'`) + flip todos same turn (`docs(plans):`).
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
