---
doc_type: plan
title:
  deployment-ui observability & UX — workstream TRACKER (cost accuracy · date-range · search · VM logs · alerts overhaul
  · resource timeline)
summary: >-
  Operator-driven tracker for the next round of deployment-ui work, captured 2026-07-17 so nothing is lost — to be SPLIT
  into per-workstream AO plans before dispatch. WS-1 Cost/day column accuracy (root cause CONFIRMED by code trace — the
  figures are already real billing; the bugs are the 7d-average divisor, the 24h-projection semantics, and AWS
  attribution). WS-2 date-range filter on the Deployments tab ("what ran between dates A–B" — registry lifecycle stamps
  make this accurate for managed rows; last-run fallback for the rest). WS-3 service filter + target search box. WS-4 VM
  drill-down logs — populate the tail reliably, show log size, cap the tail at ~200–500 lines, working download. WS-5
  Alerts & Logs page overhaul — filters/sort/date-range/linkability + an alert-coverage audit. WS-6 durable
  resource-metrics timeline — persist the 30s host-metric samples every VM already produces (like logs, same lifecycle),
  for historic CPU/RAM/disk analysis and VM right-sizing per service × asset_group × mode; design decision deliberately
  deferred.
status: draft
nature: process
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, deployment-service, unified-trading-library]
scope: [engineer]
tags: [deployment-ui, tracker, cost, billing, filters, search, logs, alerts, resource-timeline, observability]
related:
  - deployment_observability_expansion_2026_07_08.md
  - deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md
  - deployment_ui_cost_per_day_accuracy_2026_07_20.md
  - deployment_ui_date_range_filter_and_search_2026_07_20.md
  - deployment_ui_vm_log_viewer_2026_07_20.md
  - deployment_alerts_ingestion_completeness_2026_07_20.md
  - deployment_ui_alerts_page_rebuild_2026_07_20.md
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 7.2
assigned_role: backend_engineer
model_tier: opus-required
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator dictation 2026-07-17 (interactive session — six deployment-ui workstreams captured as a tracker)
---

# deployment-ui observability & UX — workstream TRACKER

> **🟡 TRACKER — DO NOT DISPATCH THIS FILE, EVER.** Operator 2026-07-17 — _"its going to be a tracker for now and we
> will split them once we are done."_ This file exists to capture every workstream NOW so nothing is missed; it stays
> `status: draft` (never ingested) and **must never flip `active` itself** — it exceeds the 10–20-todo AO cap by design.
> When the operator finalises, SPLIT per the "Split map" section into per-WS AO plans (one plan = one agent), then this
> tracker archives with pointers. Frontmatter carries AO fields (`assigned_vm: planning`) per operator instruction so
> the split children inherit them.
>
> **PUSHED TO REMOTE (operator 2026-07-17)** so it's durable and visible to the team — still `draft`, still never
> dispatched. The split into per-WS plans happens after the open decisions land and the scope is finalised.

> **Dispatch (post-split):** children are AO plans — `assigned_vm: planning`, `execution_scope: orchestrator-agent`,
> per-task `[TAG]` craft roles, `sequential: true` where flagged. Open operator decisions are marked
> `BLOCKED-OPERATOR-DECISION` / `[OPERATOR]` so they are never auto-dispatched (task_template §3).

---

## WS-1 — Cost/day column accuracy (root cause CONFIRMED — ready to split first)

> **✅ SPLIT 2026-07-20** — all four open decisions confirmed with the operator; the executable plan is
> [`deployment_ui_cost_per_day_accuracy_2026_07_20.md`](deployment_ui_cost_per_day_accuracy_2026_07_20.md) (kept
> `status: draft` deliberately — operator is mid-change on AO, dispatch held until that settles). The section below
> stays as the root-cause record; decisions + todos now live in the split plan.

### The symptom (operator, 2026-07-17)

The Deployments table (`/deployments`) Cost/day column shows, for one machine:

```
$4.4
7d $0.63 · 24h $4.4
```

Suspicious two ways — (1) "actual"
($4.4) is IDENTICAL to the 24h projection, and (2) it is ~7× the 7-day average
($0.63). The operator's ask — the column
must show (i) actual billed cost for this machine from the real Athena/BigQuery billing table, (ii) actual average cost
over the last 7 days, (iii) estimated cost if it ran a full day; and reuse the billing data the costs page already
downloads.

### What the three figures are SUPPOSED to be (contract already matches the ask)

The frontend schema + `CostCell` already define exactly those semantics — the contract is right, only the data is wrong:

- **`cost_actual_usd`** — net cost on the most recent complete billing day → operator (i).
- **`cost_avg_7d_usd`** — trailing-7-day average daily net cost → operator (ii).
- **`cost_projected_24h_usd`** — projected $/day if it runs 24h → operator (iii).

Frontend needs NO display change: [`Deployments.tsx` `CostCell`](../../deployment-ui/src/pages/Deployments.tsx) reads
the three fields; `DeploymentItem` carries them
([`deploymentApi.ts:804-806`](../../deployment-ui/src/api/deploymentApi.ts)). Primary line = `actual ?? avg ?? proj`;
sub-line = `7d {avg} · 24h {proj}`; `—` when all three null (honest absence).

### Backend root cause (CONFIRMED via code trace 2026-07-17)

**Surprise finding that changes the framing — the three figures ALREADY come from the real billing export**, the same
one the `/ops/costs` page uses. There is NO rate card in this path. The operator's "use the real billing" is already
happening; the defects are in the AGGREGATION semantics and in AWS attribution.

Path:
[`deployments_inventory.py:1678` `_attach_costs`](../../deployment-api/deployment_api/routes/deployments_inventory.py) →
`CostObservabilityService().per_resource_daily(days=7)` (line 1689) → copies `rc.actual_usd` / `rc.avg_7d_usd` /
`rc.projected_24h_usd` onto each item by `item.name == billing resource_id` (lines 1697-1699). Computation:
[`services/cost_observability/service.py:291-328` `per_resource_daily`](../../deployment-api/deployment_api/services/cost_observability/service.py)
— DuckDB over the cached billing snapshot —
`SELECT resource_id, day, SUM(cost + credit) FROM cost_records GROUP BY resource_id, day` (313-314). Per resource
(`daily = list(day_net.values())`):

- **`actual_usd = round(day_net[latest], 2)`** — net on the most recent COMPLETE billing day
  (`latest = max(complete_days)`, day < today; falls back to the latest partial day when no complete day exists). **REAL
  and correct** — the `$4.4` IS the true billed cost for that day.
- **`avg_7d_usd = round(sum(daily) / days, 2)`** where `days` is the **hard-coded window length 7** — **NOT the number
  of days the resource actually had billing rows. ← BUG #1.** A resource with 1 billing day in the window reports `X/7`
  — the misleading `$0.63`. Under-reports by exactly the fraction of the window the resource existed.
- **`projected_24h_usd = round(max(daily), 2)`** — the PEAK single observed daily net (line 326, explicitly "no
  rate-card"). **← ISSUE #2** — this is "the most expensive day we've seen", not "estimated cost if it ran a full 24h".
  For a 1-day resource `max([X]) = X` → coincidentally equals `actual`.

**Real billing source (both clouds, GBP→USD server-side in the GCP query):**

- GCP — BigQuery **resource-level** export
  `{project}.billing_export.gcp_billing_export_resource_v1_016B25_109840_AF2ACB` (deployment_api_config.py:143-152).
  `resource_id = COALESCE(resource.name,'')`; `_short_name()` takes the last path segment of
  `projects/<n>/instances/<name>` → the **bare instance / Cloud Run name** (providers.py:76-79,135) — **GCP joins
  correctly on the friendly name.** Business labels (`purpose/category/venue/asset_group`) are also extracted.
- AWS — Athena over the CUR (`aws_billing.cur_uts_cost_usage`), `resource_id = line_item_resource_id` (queries.py:114) —
  **an ARN / instance-id which never matches a friendly deployment name → most AWS rows stay `None` ("—"). ← BUG #3 (AWS
  attribution).**
- Serving path is a periodic GCS **parquet snapshot** of the exports queried via DuckDB (snapshot worker +
  `/costs/snapshot-run`), not a live per-request cloud query — cheap to extend.

**The exact `$4.4 / 7d $0.63 · 24h $4.4` explained** — a resource with billing rows for only ONE day in the 7-day window
(created ~1 day ago). `actual = X = $4.4` (real), `projected = max([X]) = $4.4` (coincidental), `avg = X/7 = $0.63`
(divides by 7, not days-present). The `$4.4` is accurate; the misleading parts are the average and the "24h" label.

### Design decisions the operator should confirm (drive the todos)

1. **7-day average divisor** — divide by the count of days the resource actually had billing rows (`len(day_net)`),
   capped at the window → a 1-day VM reads `~$4.4`, not `$0.63`. (Alternative — amortise over the full window incl. days
   it didn't exist — REJECTED as more misleading for a "typical daily cost" read.)
2. **24h projection semantics** — (a) most recent COMPLETE billing day (a real observed 24h); (b) normalise a partial
   day to 24h (`day_cost / hours_billed × 24`); (c) machine-type rate card × 24 (current design explicitly avoids rate
   cards). Recommend (a) with (b) as the partial-day fallback.
3. **AWS attribution** — map CUR `line_item_resource_id` (ARN/instance-id) → friendly VM name via the AWS census
   (instance-id ↔ Name tag), or join on the business tags. Until then AWS Cost/day stays honestly blank.

### WS-1 todos

- [ ] [OPERATOR] P0. Confirm the three design decisions above. BLOCKED-OPERATOR-DECISION.
- [ ] [REVIEW] P0. Reproduce + record the defect on live data — query `per_resource_daily(days=7)` for the VM showing
      `$4.4 / 7d $0.63 / 24h $4.4`; confirm it has exactly one billing day in the window; capture the `day_net` dict in
      the Progress Log as ground truth. No code change.
- [ ] [BACKEND] P0. **Fix BUG #1 — the 7-day-average divisor.** In `per_resource_daily` (service.py:319-327), divide by
      the number of days the resource actually has billing rows (`len(day_net)`), not the fixed window length. Sync the
      field docs (`models.py:73-83`, `deployments_inventory.py:425`). Empty case → `None` (honest absence).
- [ ] [BACKEND] P0. **Fix ISSUE #2 — the 24h projection.** Replace `max(daily)` with the operator-chosen full-day basis
      (default — most recent COMPLETE billing day; fall back to normalising a partial day). Document the chosen
      definition on the field. A legitimate `actual == projected` (a VM that ran exactly one complete day) is correct.
- [ ] [DATA] P0. **Fix BUG #3 — AWS attribution.** Build the instance-id/ARN → friendly-name mapping (AWS census the
      inventory already loads, or the CUR resource Name tag) and apply it in the join so AWS VMs get real cost. No
      mapping → stay `None`, never `$0`.
- [ ] [BACKEND] P1. Partial-vs-complete-day honesty for `cost_actual_usd` — today it silently falls back to the latest
      PARTIAL day when no complete day exists (service.py:321-322). Either mark it partial (tooltip "so far today") or
      hold `None` until a complete day lands — operator's call; record in the field doc.
- [ ] [REVIEW] P1. Unit tests — (a) 1-day-in-window → avg == actual (regression for the reported symptom); (b) N active
      days → avg == sum/N; (c) 24h basis is complete-day/normalised, not `max`; (d) AWS ARN→name mapping attributes a
      known CUR row; (e) unmapped stays `None`. `bash scripts/quality-gates.sh` green in deployment-api.
- [ ] [UI] P1. IF a "partial day" / "normalised" basis lands, add the `cost_basis`-style marker on `CostCell` so billed
      vs derived figures are distinguishable; else no UI change. `pw:L2 ✓` + cited spec if touched.
- [ ] [INFRA] P1. Ship (quickmerge `--agent --files`, cite `<repo>@<sha>`) + flip todos same turn (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the Cost/day attribution contract (three definitions, active-days
      average, 24h basis, GCP-name/AWS-ARN join) in `codex/05-infrastructure/deployment-observability.md`.

### WS-1 success criteria

- `cost_avg_7d_usd` averages over days the resource actually had billing rows — `$4.4 · 7d $0.63` becomes
  `$4.4 · 7d ~$4.4` for a 1-day VM.
- `cost_projected_24h_usd` is a defined full-day estimate, not "most expensive day we happened to see".
- AWS VMs get real Cost/day via ARN→name mapping, or an honest "—" — never a fabricated `$0`.
- Source unchanged — still the real BigQuery/Athena billing snapshot; no silent rate card for actual/avg.

---

## WS-2 — Deployments tab date-range filter ("what was running between dates A–B")

> **✅ SPLIT 2026-07-20** — live audit run (not gated as a separate plan, per operator decision), combined with WS-3
> into
> [`deployment_ui_date_range_filter_and_search_2026_07_20.md`](deployment_ui_date_range_filter_and_search_2026_07_20.md)
> (kept `status: draft` — dispatch held pending AO changes settling). Audit found the archive is 30-day-TTL'd (not the
> endpoint's self-imposed 7-day cap), a heartbeat-staleness gap in the naive "still running" formula (219 registry rows
> read `running` vs 12 actually running), and that `CLOUD_RUN_SERVICE` carries no timestamp field at all. Section below
> stays as the pre-audit record.

### Operator ask (2026-07-17)

Filter the Deployments table by a date range — "which services or VMs were running on this particular date / between
these dates". The operator suspects we may not know when a VM was launched or deleted; if accurate lifecycle data is NOT
available, fall back to filtering on the **Last run** column. If it CAN be done accurately, do that audit first and
write clear instructions in the plan.

### What we already know (pre-audit facts — accurate filtering IS feasible for managed rows)

- Registry entries carry **`started_at`, `last_heartbeat_at`, `completed_at`**
  ([`unified_trading_library/deployment_registry.py` `DeploymentRegistryEntry`](../../unified-trading-library/unified_trading_library/deployment_registry.py))
  — so for every registry-tracked VM the lifecycle interval IS known.
- Archived entries are partitioned by completion day — `deployments/archive/<YYYY-MM-DD>/<id>.json` (`ARCHIVE_PREFIX`);
  readers use `list_recent_archive(days=N)` (monitors use 3, `get()` uses 14). Day-partitioned prefixes mean a
  date-bounded archive read is a BOUNDED listing, not a whole-corpus walk (single-walk discipline holds).
- The inventory unions registry rows + live-GCE "unmanaged"/adhoc rows — **unmanaged rows have NO lifecycle stamps** →
  they are the fallback population for `last_run_at ∈ [A,B]` (exactly the operator's stated fallback).
- Correct overlap semantics for managed rows — running-during-[A,B] ⇔
  `started_at ≤ B AND (completed_at ≥ A OR completed_at is null/still-running)`.

### WS-2 todos

- [ ] [REVIEW] P1. **Accuracy audit (operator-mandated, before build).** Quantify lifecycle coverage — % of inventory
      rows with `started_at`/`completed_at`, split by kind (VM / Cloud Run job / service) and `launched_by`
      (deployment-api / control-plane / adhoc). Measure archive retention depth (how far back
      `deployments/archive/<day>/` actually goes — any bucket lifecycle rule?). Define per-kind date semantics (a Cloud
      Run SERVICE has no run interval; a JOB does). Output — a coverage table + the per-kind filter rule, written into
      the split plan as the "clear instructions" the operator asked for.
- [ ] [BACKEND] P1. Inventory endpoint accepts `date_from`/`date_to`; evaluates interval overlap on
      `started_at`/`completed_at` where present (incl. reading the day-partitioned archive for the range — bounded
      listing only); falls back to `last_run_at ∈ [A,B]` where lifecycle is absent; response marks WHICH rule matched
      per row (a basis field) so the UI can label approximate rows.
- [ ] [UI] P1. Date-range picker on `/deployments` — URL-backed (`?date_from=&date_to=` per the plain-routes contract),
      an "approx (last-run)" marker on fallback rows, and a clear empty-state. `pw:L2 ✓` + cited regression spec.

---

## WS-3 — Service filter + Target search box (Deployments tab)

> **✅ SPLIT 2026-07-20** — folded into the WS-2 plan above (same filter bar, same surface):
> [`deployment_ui_date_range_filter_and_search_2026_07_20.md`](deployment_ui_date_range_filter_and_search_2026_07_20.md).
> Also picked up a new item from this session: the existing `kind` filter becomes multi-select.

### Operator ask (2026-07-17)

A **filter on top for Service** and a **search bar for the Target column**.

### What we already know

- After the plain-routes refactor (deployment-ui@079b29e) every filter is URL-backed —
  `?umbrella=&cloud=&status=&asset_group=&kind=&launched_by=&region=`. There is NO service filter and NO name search
  today.
- The inventory returns ~300 rows (measured 295 this week) — client-side filtering is fine at this scale.

### WS-3 todos

- [ ] [UI] P2. Service dropdown filter — options derived from the loaded inventory's distinct `service` values,
      URL-backed (`?service=`), client-side filter, same filter-bar row as the existing dropdowns.
- [ ] [UI] P2. Target search box — free-text, matches the Target column (`item.name`, substring, case-insensitive),
      URL-backed (`?q=`), debounced, clears with an ✕. `pw:L2 ✓` + a cited regression spec covering both (a deep-link
      with `?service=&q=` applies both — same URL-filter contract the plain-routes refactor established).
- [ ] [BACKEND] P3. _(stretch, optional)_ server-side `q=`/`service=` params if row counts ever outgrow client-side.

---

## WS-4 — VM drill-down logs (populate · size · capped tail · download)

> **✅ SPLIT 2026-07-20** — live repro audit run, findings reframed the whole workstream:
> [`deployment_ui_vm_log_viewer_2026_07_20.md`](deployment_ui_vm_log_viewer_2026_07_20.md) (kept `status: draft` —
> dispatch held pending AO changes settling). The audit found `run.log` content is **never fetched into the browser at
> all today** — the "Live log tail" panel is a mislabeled lifecycle-events stream from a different bucket, and
> "Download" saves those events as CSV, not the log. The archive-path lookup 404s live for real VMs (dated by
> `completed_at`, but the archiver actually keys by cron-run date). Section below stays as the pre-audit record.

### Operator ask (2026-07-17)

Clicking a VM should show its logs in the popup — the operator doesn't think logs populate properly today. Logs are
already saved in GCS, so they should be available there. Show the **log size** in the popup (a log can be 20–30 MB). The
tail should show only the last **~200–500 lines** so the UI doesn't crash. The **download button must work**.

### What we already know

- Every VM streams `gs://deployment-scripts-{project}/vm-logs/{vm}/run.log` every 30s (heartbeat daemon; the `vm-logs/`
  prefix carries a 14-day delete lifecycle); durable copies land under `log-archive/` (snapshot + daily rolling, no
  TTL). Path SSOTs — `vm_log_stream_uri` / `vm_log_archive_uri` / `vm_run_log_rolling_uri` in UTL
  `deployment_registry.py`.
- The drill-down surface is `DeploymentDetail` (the `/deployments` slide-over via `?detail=` + the full page at
  `/deployments/:name`) — it has a `run.log` link + a log-tail area + the events timeline (`detail-run-log`,
  `vm-events-timeline` testids).
- GCS object ops MUST go through the UTL wrappers (`gcs_describe_object` for size/metadata; byte-range reads) — never
  subprocess `gcloud`/`gsutil` (QG-enforced; `codex/05-infrastructure/gcs-object-operations.md`).

### WS-4 todos

- [ ] [REVIEW] P1. **Repro audit first** — click through N live + N archived VMs; record which show a tail vs blank;
      identify the exact read path (endpoint) and the failure mode (wrong path for archived VMs? auth? size timeout?
      live-vs-rolled path divergence after the 14-day TTL?). Findings → the split plan.
- [ ] [BACKEND] P1. Log metadata on the detail response — object **size** + last-modified via `gcs_describe_object`;
      resolve live (`vm-logs/`) vs archived (`log-archive/`) location per the audit and label which one is shown.
- [ ] [BACKEND] P1. Bounded tail endpoint — read ONLY the last ~64–256 KB via a byte-range read, split to the last
      200–500 lines (cap configurable). NEVER stream a whole 20–30 MB object into the API or the browser for the tail.
- [ ] [UI] P1. Popup shows — size (human units), the capped tail with a "last N lines of X MB" label, and a working
      **Download** (signed URL or streaming proxy; must not freeze the tab on 30 MB). Honest states — "no log yet" /
      "live log expired (14-day TTL), showing archive" / errors surfaced, never swallowed. `pw:L2 ✓` + cited regression
      spec.
- [ ] [INFRA] P1. Ship + flip (`docs(plans):`).

---

## WS-5 — Alerts & Logs page overhaul (filters · sort · date-range · proper view · coverage audit)

> **✅ SPLIT 2026-07-20** — coverage + UX audits run live; reframed from "add filters" to "the ledger is starved." Split
> into TWO gated plans (both `status: draft`, dispatch held pending AO settling):
> [`deployment_alerts_ingestion_completeness_2026_07_20.md`](deployment_alerts_ingestion_completeness_2026_07_20.md)
> (Plan A, P0 — mirror the Slack alert sources into the ledger) and
> [`deployment_ui_alerts_page_rebuild_2026_07_20.md`](deployment_ui_alerts_page_rebuild_2026_07_20.md) (Plan B, gated on
> A — filters/sort/date-range/drill-down). Audit headline: **181 alert rows lifetime vs thousands of real Slack alerts
> in a 10-day window**; the entire alerting-service plane (~20 classes) is invisible to deployment-api. Operator
> reframed the page as a **diagnostic surface** (mirror cheap-to-copy Slack sources), and **deferred all
> agent-orchestrator alerts** (AO has its own alert machinery + UI). Section below stays as the pre-audit record.

### Operator ask (2026-07-17, near-verbatim)

The page shows data but there are **no filters, no sorting, no date range**. "The data is there, some of it, but it's
not usable" — needs a **proper view**. Sorting + filtering on **where the alert came from** and **what it is about**;
**clickable links** to drill into an alert's details. Also — the page may show only a few alerts; we need **more
thorough alert coverage** — do that audit first, then write the plan.

### What we already know

- `/alerts` (plain route post-079b29e) renders `AlertsLogsTab` — a Slack-bound alert ledger + the unified SSE log stream
  (`GET /api/logs/stream/{ref}`), with a `?logs=<target_ref>` deep-link param the tab owns.
- Alert rows already deep-link a `deployment_target` to `/deployments/{target}` (pinned by `alerts-page.spec.ts`).
- Alerting policy SSOTs exist and constrain the design — `agent-orchestrator-alerts` is actionable-only; CI alerts route
  via the `notify-slack.yml` carrier with dedup keys/cooldowns (`codex/04-architecture/ci-alerting.md`,
  `…/agent-orchestrator-alerting.md`). Candidate feeds to audit against the ledger — ci-failures, AO alerts, kill-switch
  events, consolidator staleness, data-status RED, VM zombie-watchdog reaps, cost anomalies.

### WS-5 todos

- [ ] [REVIEW] P1. **Coverage audit (operator-mandated, before build).** Inventory every alert SOURCE that exists today
      (channels, watchdogs, CI carriers, kill-switch, consolidator/data-status verdicts) vs what the `/alerts` ledger
      actually ingests; produce a coverage table + gap list; propose which feeds belong on the page and their normalised
      shape (source, class/severity, target, service, time, message, link).
- [ ] [REVIEW] P1. **UX audit.** Define the proper table from the audited fields — sortable columns, filters (source,
      class/severity, target/service, date-range), URL-backed params (plain-routes contract), per-row deep-links (target
      → `/deployments/:name`, log stream → `?logs=`, runbook when present). A short design note in the split plan.
- [ ] [UI] P1. Rebuild the alerts table per the audits — sorting, filtering, date range, linked drill-downs, proper
      layout. `pw:L2 ✓` + cited regression spec.
- [ ] [BACKEND] P1. Whatever the coverage audit requires — normalise the missing feeds into the ledger (respect the
      dedup/actionable-only policies in the alerting SSOTs; the PAGE may show more than what PAGES Slack).
- [ ] [INFRA] P1. Ship + flip (`docs(plans):`).

---

## WS-6 — Durable resource-metrics timeline (design first — decision deferred by operator)

> **✅ RESOLVED + SPLIT 2026-07-21** — write-path decided: **event-spine → BigQuery** (operator chose it over
> GCS-batched / Ops-Agent; the VM just publishes an event, cost ~$0). Expanded beyond resource stats to THREE durable
> signals — VM resource stats + a run-ledger (fixes the live-confirmed 30-day archive TTL) + idle/orphan-spend trend —
> all in one BigQuery dataset. **No live interactive timeline chart** (operator: nice-to-have, dropped); analysis =
> download + local DuckDB. **Git-health snapshot history DROPPED** (not necessary). Executable plan:
> [`deployment_durable_operational_data_bigquery_2026_07_21.md`](deployment_durable_operational_data_bigquery_2026_07_21.md)
> (kept `draft`). Section below stays as the pre-decision record + the three write-path options considered.

### Operator ask (2026-07-17, near-verbatim)

Resources today are a current snapshot — good for now. In future we want a **durable** record of the ~30-second resource
samples, saved like logs, so we can plot **disk/CPU/RAM on a timeline**, see how the spikes looked, and understand how
much resource each service uses — to allocate bigger or lighter VMs on the next runs, find the right shape per service,
and catch outliers / OOM / disk hiccups. Requirements dictated —

- Every VM **already produces** this data today; save it durably.
- **Same lifecycle policy as logs** — plain replace when a new one comes in; NO soft-delete, NO versioning.
- Account for the **cost** of writing / storing / querying at design time.
- Query-time view TBD — likely a **dedicated page** to compare N VMs across **service × asset_group × mode
  (live/batch/paper)** (asset_group only where applicable — instruments-service yes, deployment-ui no).
- The live/current view already exists (the Resources column via the registry read path — Firestore-first once the
  dual-write flag lands); this WS is **HISTORY only** (e.g. "a VM that ran three days ago — what did it use?").
- Where to save + what writes it = **OPEN — operator will decide when free.** ("Very useful but not something I want to
  do in a hurry.")

### What we already know (facts)

- The heartbeat daemon samples every ~30s — the D.1 vector (`cpu_pct`, `mem_pct`, `mem_slope`, `disk_pct`,
  `io_write_rate_bytes_sec`, `net_recv_rate_bytes_sec`, `workload_alive`) — but only the last **~10 samples** persist
  (`host_metrics_window` on the registry entry, a fixed-size popover trend). The timeline is LOST when the entry
  archives. Keeping full history inside the registry entry is a non-starter (a 7-day backfill VM ≈ 20k samples ≈ ~2 MB →
  breaks the 1 MiB Firestore doc limit + rewrites the whole growing blob on every heartbeat).
- Scale math (cost input) — ~100 VMs × 30s × ~10 fields ≈ 288k samples/day ≈ single-digit MB/day compressed ≈ ~1 GB/yr.
  **Storage is trivial; the real cost drivers are object-count / write-op patterns and the query shape** — which is
  exactly why the write-path choice is THE decision.

### Options on the table (recorded from the 2026-07-17 session discussion — NOT decided)

- **(a) GCS-batched** — sample at 30s, buffer in the daemon, flush a batch object every 5–15 min + on SIGTERM (SPOT
  preemption safety; the daemon's SIGTERM handler already exists). Simple and log-like; the failure mode is OBJECT COUNT
  (the same class of problem that broke the registry census at ~3k blobs) — per-sample objects would be 2,880
  objects/VM/day; batching cuts it to 24–288. Any reader must honour single-walk discipline.
- **(b) Event-spine** — samples ride the existing UTL `EventTransport`/Pub/Sub path (the daemon already publishes
  DEPLOYMENT_* events) → a native BigQuery subscription lands them queryable with NO consolidator to own; TTL =
  declarative partition expiration (no lifecycle cron); query by vm/service/asset_group/mode/time is a WHERE clause;
  dual-cloud via the same facade. (CLAUDE.md "live = batch event-log spine" makes this the architecturally aligned
  option.)
- **(c) Check the wheel first** — GCE Ops Agent / Cloud Monitoring may already capture host metrics fleet-wide with
  dashboards + retention built in. If it is already on the VMs, the honest question is whether this becomes a Monitoring
  query behind deployment-api instead of storage we own (counter-arguments — custom retention caps, and we want it in
  OUR UI, joined to service/asset_group/mode).

### WS-6 todos

- [ ] [OPERATOR] P0. Decide the write path — (a) GCS-batched / (b) event-spine→BigQuery / (c) Ops-Agent-backed (or a
      hybrid). BLOCKED-OPERATOR-DECISION — explicitly deferred by the operator 2026-07-17.
- [ ] [REVIEW] P1. Pre-decision audit for (c) — is the Ops Agent (or any host-metric export) already running on the
      fleet VMs? What retention/granularity does it give, and can deployment-api query it per VM name? A yes here may
      delete most of the build.
- [ ] [BACKEND] P1. Decision doc for the operator — per option: writes/day, objects/day, storage/mo, query-cost model,
      lifecycle spec (mirror the vm-logs TTL semantics; plain replace, no soft-delete/versioning — operator
      requirement), sample schema (D.1 fields + `vm_name`/`service`/`asset_group`/`mode`/`deployment_id` keys), SPOT
      flush-on-SIGTERM behaviour, and the dual-cloud answer. Feeds the operator decision above.
- [ ] [BACKEND] P2. (post-decision) Writer on the heartbeat-daemon path per the chosen design (batch/flush cadence;
      SIGTERM flush; NEVER blocks the authoritative heartbeat/registry write — same best-effort contract as the
      dual-write mirror).
- [ ] [BACKEND] P2. Read/query API — a VM's full-run timeline + a cross-VM comparison slice (filter service /
      asset_group / mode / time window).
- [ ] [UI] P2. Historic timeline chart in the VM drill-down (CPU/RAM/disk over the run, spike/OOM markers) + a
      **dedicated comparison page** — overlay N VMs filtered by service × asset_group × mode (the operator's
      right-sizing workflow — "ten different VMs running instruments-service — what were their resources?"). `pw:L2 ✓` +
      cited regression spec.
- [ ] [REVIEW] P2. End-to-end verify on a real backfill VM incl. a SPOT preemption — flush-on-SIGTERM works; sample loss
      bounded to the buffer window; TTL/replace lifecycle behaves.

---

## Split map (when the operator finalises — before ANY dispatch)

| Child plan                   | Contents                                                                                                                                 | Readiness                                                                                           |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| WS-1 cost accuracy           | ✅ split — `deployment_ui_cost_per_day_accuracy_2026_07_20.md`                                                                           | 🟢 **ACTIVE 2026-07-21** — dispatched to AO (reliability test, must-do fixes applied)               |
| WS-2 + WS-3 filters & search | ✅ split — `deployment_ui_date_range_filter_and_search_2026_07_20.md`                                                                    | 🟢 **ACTIVE 2026-07-21** — dispatched to AO (reliability test; owns the Deployments.tsx extraction) |
| WS-4 VM logs                 | ✅ split — `deployment_ui_vm_log_viewer_2026_07_20.md`                                                                                   | done — repro audit reframed scope (no viewer existed); kept `draft`, dispatch held                  |
| WS-5 alerts overhaul         | ✅ split — ingestion (Plan A, P0) + rebuild (Plan B, gated); AO alerts deferred                                                          | done — both audits run live; reframed to ingestion-first; kept `draft`, dispatch held               |
| WS-6 resource timeline       | ✅ resolved — `deployment_durable_operational_data_bigquery_2026_07_21.md` (event-spine→BQ; +run-ledger +idle-spend; git-health dropped) | done — write-path decided; kept `draft`, dispatch held                                              |

Per task_template §4 — each child gets 10–20 todos, one plan = one agent, audits separable, draft-gated phases where a
build depends on an audit/decision.

## Progress Log

- **2026-07-17 (slot 5, Opus — drafting)** — Plan opened from the operator's Cost/day observation. Confirmed the
  FRONTEND is already correct (`CostCell` + `DeploymentItem` carry the exact three figures wanted, honest-absence
  included). Two code-trace agents pinned the backend.
  - **Hypothesis flipped** — the operator (and I) assumed inferred rate-card numbers and wanted "the real billing" wired
    in. The trace found the figures ALREADY come from the real billing export (GCP BigQuery resource-level + AWS Athena
    CUR) via a purpose-built `per_resource_daily(days=7)` the inventory already calls. Source is correct.
  - **Real defects (3)** — (1) `avg_7d_usd` divides by a hard-coded 7, not days-actually-billed → a 1-day VM reports 1/7
    of its real daily cost (the `$0.63`); (2) `projected_24h_usd = max(daily)` is "peak observed day", not a full-day
    estimate; (3) AWS CUR keys on ARN/instance-id → never matches a friendly name → AWS Cost/day blank. The
    `$4.4 · 7d $0.63 · 24h $4.4` is fully explained by a ~1-day-old resource × bug (1).
  - Three operator design decisions surfaced (avg divisor / 24h semantics / AWS mapping).
- **2026-07-17 (slot 5, Fable — tracker conversion, operator dictation)** — Operator — this is not just the cost fix; it
  becomes the TRACKER for the next round of deployment-ui work, split into per-WS plans later; keep `draft` + local.
  Renamed `deployment_ui_cost_per_day_accuracy_from_billing_2026_07_17.md` →
  `deployment_ui_observability_ux_tracker_2026_07_17.md` (file was untracked — plain `mv`, no git surgery). Captured
  five new workstreams from dictation — **WS-2** date-range filter (pre-audit facts recorded: registry
  `started_at`/`completed_at` + the day-partitioned archive make accurate interval filtering feasible for managed rows;
  `last_run_at` fallback for adhoc rows — exactly the operator's stated fallback); **WS-3** service filter + target
  search box; **WS-4** VM drill-down logs (repro audit + size + 200–500-line capped tail via byte-range reads
  - working download; the vm-logs 14-day TTL vs log-archive divergence flagged as the likely blank-tail suspect);
    **WS-5** alerts & logs overhaul (coverage + UX audits first, then the filters/sort/date-range/linkability rebuild);
    **WS-6** durable resource-metrics timeline (operator requirements + the three write-path options from this session's
    earlier discussion + scale math recorded; decision explicitly BLOCKED-OPERATOR-DECISION per "not in a hurry"). Read
    `plans/active/task_template.md` before restructuring (HARD RULE) — tracker stays `draft` / never dispatched, with a
    split map; children inherit the AO frontmatter.
- **2026-07-20 (interactive session)** — Operator confirmed `todays-work.md` (2026-07-17 dictation, pre-tracker) is
  fully folded into this tracker except two items: "speed" (deferred by operator — caching pass planned after the
  remaining WS land) and "image overview / does the consolidator have images" (operator already has a separate agent
  working that page — out of this tracker's scope). Then walked WS-1's four open decisions to closure and split it out —
  see `deployment_ui_cost_per_day_accuracy_2026_07_20.md`.
- **2026-07-20 (interactive session, continued)** — WS-2 + WS-3: operator chose to combine both into one plan and run
  the accuracy audit live rather than gate it as a separate plan. Audit (read-only, live ADC creds) found: archive GCS
  lifecycle TTL is 30 days (endpoint's own read cap is a separate, tighter 7-day limit); 219 registry rows read
  `status=running` vs only 12 GCE instances actually running — a heartbeat-staleness gap the naive
  `completed_at: null ⇒ still running` overlap formula would have gotten wrong; `CLOUD_RUN_SERVICE` carries no timestamp
  field at all (asymmetric vs its AWS `ECS_SERVICE` twin). Operator decided: always-on kinds get a last-deployed proxy
  timestamp, sort last, distinct "always-on" visual treatment; `kind` filter becomes multi-select (new item, not in the
  original dictation); approx/fallback rows reuse the WS-1 colour-only convention; out-of-range requests get an explicit
  banner. Split out to `deployment_ui_date_range_filter_and_search_2026_07_20.md` (kept `draft`).
- **2026-07-20 (interactive session, continued)** — WS-4: ran a live repro audit rather than gating as a separate plan.
  Reframed the workstream — `run.log` is never fetched into the browser today; "Live log tail" is a mislabeled events
  panel on a different bucket; "Download" saves events as CSV, not the log; the archive-path lookup 404s live for real
  VMs (`af-backfill-20260627-151733` confirmed) because it guesses a date instead of matching the archiver's actual
  daily-rolling-folder key. Operator decided: fix at the writer (durable single final snapshot on VM completion, no more
  date-guessing), read `vm-logs/` first regardless of completion status (14-day TTL from last write, not from VM start),
  keep the events panel but rename it honestly, add a genuinely new run.log panel, and use a signed URL for download.
  Split out to `deployment_ui_vm_log_viewer_2026_07_20.md` (kept `draft`).
- **2026-07-20 (interactive session, continued)** — WS-5: ran both operator-mandated audits live (coverage + UX), with
  `SUB_AGENT_MANDATORY_RULES.md` injected. Reframed from "add filters" to "the ledger is starved" — 181 alert rows
  lifetime (10 date partitions ever) vs thousands of real Slack alerts in a single 10-day export window; the entire
  alerting-service plane (~20 classes, 29 partitions current through today) is invisible to deployment-api. Also found:
  the `repo` field records the emitter not the subject (repo filtering currently wrong), a hardcoded-bucket QG
  violation, a known unlocked read-modify-write row-drop race, the zombie-watchdog webhook persists nothing, and
  cost-anomaly alerts (a tracker candidate feed) have NO emitter — a build, not a gap. An initial audit claim (persist
  coupled to Slack-post) was self-corrected: persistence is ad-hoc, and 6 AO notifiers page CRITICAL but persist
  nothing. Operator reframed the page as a **diagnostic surface** (mirror the Slack alert sources cheap to copy; "done"
  = a clear page) and **deferred ALL agent-orchestrator alerts** (AO already has its own alert machinery + UI; the AO
  findings are recorded in Plan A's Deferred section for a later workstream). Split into two gated plans:
  `deployment_alerts_ingestion_completeness_2026_07_20.md` (Plan A, P0) and
  `deployment_ui_alerts_page_rebuild_2026_07_20.md` (Plan B, `depends_on` A + the date-range plan, which owns the shared
  filter/sort-primitive extraction from `Deployments.tsx`). Both kept `draft`.

- **2026-07-21 (interactive session)** — WS-6 resolved. Design discussion compared three write paths; operator chose
  **event-spine → BigQuery** (simpler write path — the VM just publishes an event, no GCS flush/layout/compaction/
  object-count machinery — and cost ~$0 at fleet scale, verified: ~4 GB / 6 months for 100 VMs at 1/min, queries within
  the 1 TB/mo free tier). Scope expanded to THREE durable signals (resource stats + run-ledger + idle-spend), all in one
  BQ dataset; **no live timeline chart** (dropped as nice-to-have — analysis via download + local DuckDB); **git-health
  snapshot history dropped**. Live-confirmed the `deployments/archive/` 30-day TTL (the run-ledger fixes it). Split to
  `deployment_durable_operational_data_bigquery_2026_07_21.md` (kept `draft`). NB: also authored the Fleet-tab
  consolidation plan (`deployment_ui_fleet_tab_consolidation_2026_07_21.md`) this session — not a tracker WS, but
  related deployment-ui cleanup.
- **2026-07-21 (AO reliability test)** — Operator activated the FIRST TWO plans (`WS-1` cost accuracy + `WS-2/3`
  filters+search) — flipped `status: active`, must-do review fixes applied, pushed. These are independent, no cross-plan
  gating, and WS-2/3 is the upstream owner of the `Deployments.tsx` shared-primitive extraction — a good first pair. All
  remaining plans (WS-4, WS-5A, WS-5B, Fleet consolidation, durable-operational-data) STAY `draft` until these two
  complete and AO looks stable. Fleet + durable-operational-data pushed to remote as durable drafts.

## Codex SSOTs

- `codex/05-infrastructure/deployment-observability.md` — deployment inventory + (to add) the cost-attribution contract
  (WS-1) and the resource-timeline contract (WS-6, post-decision).
- `codex/05-infrastructure/gcs-object-operations.md` — GCS ops via UTL wrappers (WS-4 size/tail/download; WS-6 option
  a).
- `codex/06-coding-standards/ui-testing-layers.md` — the UI gate (pw:L2 + cited spec, every `[UI]` todo).
- `codex/04-architecture/ci-alerting.md` + `codex/04-architecture/agent-orchestrator-alerting.md` — alert feed / dedup /
  actionable-only policies WS-5 must honour.
- `codex/02-data/live-data-persistence-and-event-log.md` — the event-spine (WS-6 option b).
