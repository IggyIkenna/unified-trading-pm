---
doc_type: codex-ssot
title: CI Alerting — the ci-failures channel dedup + cooldown contract
summary:
  The contract for what reaches the ci-failures Slack channel. Every GHA-originated CI alert routes through ONE reusable
  carrier (notify-slack.yml) that reads back the GCS alert ledger and turns "re-page while a condition stays true" into
  "page on transition + a re-remind interval". Standing conditions carry a dedup_key + cooldown_min; genuine per-event
  transitions leave dedup_key blank; green all-clears are suppressed unless marked a recovery. Dedup is fail-open — it
  never swallows a real alert on a ledger/auth error.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [alerts, slack, ci-cd, dedup, observability, notifications]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/05-infrastructure/quickmerge-architecture.md,
    /plans/archive/2026_07/deployment_alerts_ingestion_completeness_2026_07_20.md,
  ]
created: 2026-07-13
authoritative_for:
  [
    ci-failures Slack alert routing,
    notify-slack.yml dedup contract,
    CI-alert cooldown selection,
    unified alerts ledger normalised schema,
    alerts-page diagnostic-surface principle,
  ]
referenced_by:
owner:
last_reviewed: 2026-07-21
code_refs:
  - .github/workflows/notify-slack.yml
  - .github/workflows/branch-health.yml
  - .github/workflows/python-quality-gates-v2.yml
  - .github/workflows/ci-status-update.yml
  - unified_api_contracts/canonical/crosscutting/alerting/ledger.py
  - deployment-api/deployment_api/routes/_repo_ci_alerts.py
  - deployment-ui/src/pages/Alerts.tsx
  - deployment-ui/tests/smoke/alerts-page.spec.ts
---

# CI Alerting — the #ci-failures channel

`#ci-failures` is the CI/CD Slack channel. It is the GHA-side sibling of `#agent-orchestrator-alerts` (see
[agent-orchestrator-alerting.md](agent-orchestrator-alerting.md)) — **same philosophy** (page on a state transition, not
on every tick a condition stays true), **different transport**: here the dedup lives in a reusable GitHub Actions
workflow that reads a GCS ledger; there it lives in the AO server's `dedup_state.py`.

## The one place dedup lives — `notify-slack.yml` (the carrier)

Every CI alert is posted by calling the reusable workflow `.github/workflows/notify-slack.yml`. A caller never posts to
the webhook directly — it passes inputs and the carrier decides whether to post. This is the single structural fix
(`alert_quality_audit_2026_06_18`): the ledger used to be write-only and the carrier posted unconditionally; now it
**reads the ledger back** before posting, so the whole GHA fleet converts "re-page while true" → "page on transition" in
one place.

Carrier inputs that govern noise:

| Input          | Meaning                                                                                                                                                                                                                                                                                                                             |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dedup_key`    | Stable identity of the **standing condition** this alert reports (e.g. `promotion-lag`, `qg-fail:<repo>:<branch>`). When set, the carrier SKIPS the post if the same key was seen within `cooldown_min`. **Leave blank** for a genuine per-event alert (each distinct CI-failure transition) that must never be suppressed.         |
| `cooldown_min` | Suppress a repeat of the same `dedup_key` posted within this many minutes. **No effect unless `dedup_key` is set.** Default 240 (4h). A RESOLVED bookend passes a **shorter** cooldown (or a distinct key) so closure is never swallowed by the open-condition's cooldown.                                                          |
| `recovery`     | Marks a genuine all-clear. A green INFO post (conclusion `success`/`neutral`) is **suppressed** unless `recovery: true` OR the message carries a recovery marker (`RECOVERED` / `RESOLVED` / `:large_green_circle:` / `:ballot_box_with_check:`). Failures/warnings/no-conclusion advisories are never affected — they always post. |
| `severity`     | `INFO` / `WARNING` / `CRITICAL` — header styling only; does not gate posting.                                                                                                                                                                                                                                                       |

**Fail-open (HARD invariant):** dedup only runs on the GCP path (the ledger lives in GCS `unified-trading-cicd-events`).
A missing/failed GCP auth, or the AWS/other path, **posts anyway** — dedup must never swallow a real alert on an infra
error. The gate suppresses only when it can PROVE the key is within its cooldown window.

> **Gotcha — the ledger access must be AUTHENTICATED gsutil (incident 2026-07-14).** The read/write use `gsutil`, but
> `google-github-actions/auth@v3` only exports ADC — `gsutil` **ignores ADC and runs anonymous** unless
> `google-github-actions/setup-gcloud@v2` runs after `auth`. Without it the read 401s ("Anonymous caller … does not have
> storage.objects.list access"), the gate sees an empty ledger → "key not seen → post", and **every** `dedup_key` alert
> fires on every run (PR#1008: 67 QG-failed pages in ~3h despite the correct stable `qg-fail:<repo>:<branch>` key; the
> promotion-lag re-remind over-fired the same way). The carrier now runs `setup-gcloud` after `auth`. When touching the
> carrier, keep that step — `auth@v3` alone silently breaks the whole channel's dedup.

## The reporters — who calls the carrier (as-shipped)

| Reporter (workflow · job)                        | Fires on                                                                                                        | `dedup_key`                 | `cooldown_min` | Notes                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- | --------------------------- | -------------: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `branch-health.yml` · `lag-notify`               | promotion lag (LDR↔staging↔main stuck > threshold)                                                              | `promotion-lag`             |            120 | re-remind ≈ every 3 real promote cycles (WS-1, 2026-07-13); see cadence note below                                                                                                                                                                                                                                                                                                                |
| `branch-health.yml` · `lag-notify-resolved`      | lag cleared                                                                                                     | `promotion-lag-cleared`     |             30 | shorter than the open cooldown so the all-clear is never swallowed                                                                                                                                                                                                                                                                                                                                |
| `branch-health.yml` · `ar-lag-notify`            | Artifact-Registry dep-publish lag                                                                               | `ar-dep-publish-lag`        |             60 | fail-open (GCP auth errors → no lag reported)                                                                                                                                                                                                                                                                                                                                                     |
| `python-quality-gates-v2.yml` · `notify-qg-fail` | a QG slice failed / cancelled                                                                                   | `qg-fail:<repo>:<ref_name>` |            120 | **per-branch, not per-sha** (WS-3, 2026-07-13): a still-red branch pages once per red-period, not per failing push; a new failure after the cooldown still re-alerts                                                                                                                                                                                                                              |
| `ci-status-update.yml` · `notify`                | a repo's CI **went red** (`client_payload.status=='FAILING'`)                                                   | _(none — per-transition)_   |            n/a | green `CI-RECOVERED` / SIT-pass all-clears are NOT posted (WS-2, 2026-07-13); Firestore CAS + `is_stale_write` order the transitions; Firestore + GCS-ledger writes are unchanged                                                                                                                                                                                                                 |
| `glue-pool-starvation-monitor.yml`               | a `glue`-labelled job `queued` past threshold while `in_progress == 0` (self-hosted runner pool total collapse) | `glue-pool-starved`         |             60 | SHIPPED 2026-08-09 (`ci_satellite_ao_dispatch_batch1_2026_07_26.md` — archived, see `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md`, `unified-trading-pm@80f397278`); decision logic in `scripts/cicd/glue_pool_starvation_monitor.py`; runs on a hosted runner (never `glue` itself, by design — a starved `glue` pool must not also starve its own monitor); cron `*/15` |

## Why the three QG/CI-failure reporters show different counts

A recurring question — three workflows report CI failure and their Slack counts never match. They report at **different
granularities**, so different counts is correct, not a bug:

- **`python-quality-gates-v2.yml` · `notify-qg-fail`** — per **run** (a QG-slice failure on a push/PR). After WS-3 it is
  deduped per `<repo>:<branch>`, so a still-red branch collapses many failing pushes into one page per red-period.
- **`ci-status-update.yml` · `notify`** — per **transition** (the moment a repo's aggregate CI status flips to
  `FAILING`). This is the Firestore-SSOT `ci_status` lifecycle; it is the "went-red" signal, one per red episode.
- **`ldr-ci-monitor`** — an **hourly** LDR sweep (a periodic health poll), independent of the above two.

Per-run ⊇ per-transition (a branch can fail many runs in one red episode), and the hourly sweep is on its own clock.

## The rules (apply when adding or tuning a CI alert)

1. **Standing condition** (stays true across ticks — lag, a red branch, an AR gap) → set a `dedup_key` + a
   `cooldown_min` → page on the false→true transition + re-remind on the cooldown, never every tick.
2. **Genuine per-event transition** (each distinct went-red) → leave `dedup_key` blank → never suppressed.
3. **Green all-clear** → `recovery: true` (or a recovery marker in the message), else it is dropped. The channel shows
   OK only when it follows a problem (operator requirement 2026-06-22).
4. **RESOLVED bookend cooldown < open-condition cooldown** (or use a distinct key) so closure is never swallowed.
5. **Dedup is fail-open** — never rely on it to suppress; it exists to reduce noise, and it drops to post-anyway on any
   ledger/auth error.
6. **Cooldown tracks the REAL cadence of the condition, not the declared cron.** An earlier measurement put GitHub's
   `schedule:` cron throttle at ≈37% of the declared rate — the promote gate declares `*/15` but the **measured**
   cadence over 60 runs was avg **41.5 min** (median 33, max 93). A later, broader re-measurement
   (`github_actions_self_hosted_runner_migration_2026_07_15.md`,
   `github_actions_operator_gated_followups_2026_07_17.md`, both 2026-07-17) found hourly crons landing 9/10 and `*/30`
   landing 16/20 — **≈80-90% delivery, not ≈37%** — and flagged the 37% figure as likely stale, though it did NOT
   independently re-verify the `*/15` promote-gate's specific 41.5-min figure (both docs recommend re-checking it before
   tuning any cooldown to it). So a promotion-lag that is merely waiting for a throttled promote should not re-page
   hourly: the 120-min cooldown was sized against the OLDER, likely-too-pessimistic 41.5-min figure — re-measure before
   relying on it. When picking a cooldown, measure the condition's true period first
   (`gh api …/actions/workflows/<wf>/runs`), don't assume the cron.

## The unified alerts ledger (`/alerts` page) — a diagnostic surface, not a paging surface

`#ci-failures` (above) and `#agent-orchestrator-alerts`
([agent-orchestrator-alerting.md](agent-orchestrator-alerting.md)) are the **paging** tier — Slack, actionable-only,
page-on-transition. The deployment-ui `/alerts` page (backed by deployment-api's `GET /api/alerts`) is a **separate,
wider tier**: a diagnostic surface for filtering/sorting/drilling into alert history, not something meant to page
anyone. The actionable-only rule constrains Slack; showing MORE on the page than pages Slack is the intent, not a
violation (`deployment_alerts_ingestion_completeness_2026_07_20.md`, operator ruling 2026-07-20).

**The persist-vs-page distinction**: an alert source can persist to the ledger without ever posting to Slack (e.g.
INFO/WARN-tier `alerting-service` events — see `alerting_service/rules/data_pipeline_rules.py`, which intentionally
keeps those Slack-channel-only and never calls `_persist_delivery_record()` for them; only `CRITICAL` reaches the
incident/persist path). Conversely, the page's job is to show what's cheap to mirror from already-Slack-bound sources,
not to become a new source of truth that requires its own write path. **Principle: mirror the alert sources that already
flow to Slack and are cheap to copy** — don't build new emitters for the page; read the durable stores that already
exist (GHA's `cicd/events/`, deployment-api's own `cicd/alerts/`, alerting-service's `alerting/history/`, the VM
zombie-watchdog's reap events, the kill-switch audit log) into one normalised feed.

### The normalised alert schema

SSOT is code, not this table: `NormalizedAlertRow` / `AlertSourcePlane` / `FieldCoverage` / `FIELD_COVERAGE` in
`unified-api-contracts` `unified_api_contracts/canonical/crosscutting/alerting/ledger.py`, imported via the
`unified_api_contracts.alerting` facade (never the deep path). Every mirrored source writes into this union shape;
deployment-api's `_repo_ci_alerts.py` is the reader that merges all five planes into one response.

Legend: **P** = populated today · **p** = populatable (value exists at the emit site, wiring may still be catching up) ·
**—** = structurally absent (the concept doesn't exist for that source — a permanent gap, not a bug).

| field               | gha_ci_events | deployment_api | alerting_service | zombie_watchdog | kill_switch_audit |
| ------------------- | :-----------: | :------------: | :--------------: | :-------------: | :---------------: |
| `timestamp`         |       P       |       P        |        P         |        p        |         P         |
| `subject_repo`      |       P       |       P        |        —         |        —        |         —         |
| `emitting_repo`     |       —       |       P        |        p         |        p        |         p         |
| `severity`          |       —       |       P        |        P         |        —        |         —         |
| `alert_class`       |       —       |       P        |        P         |        P        |         P         |
| `message`           |       —       |       P        |        P         |        P        |         P         |
| `service`           |       —       |       —        |        p         |        —        |         p         |
| `deployment_target` |       —       |       p        |        p         |        P        |         —         |
| `run_url`           |       p       |       P        |        —         |        —        |         —         |
| `dedup_key`         |       —       |       P        |        —         |        p        |         p         |
| `resolved_state`    |       —       |       —        |        —         |        —        |         P         |

Notes that don't fit the matrix:

- **`gha_ci_events`** (`.github/actions/persist-event` → `cicd/events/{repo_name}/{date}/events.jsonl`): each caller
  reports on itself, so `subject_repo` = `repo_name` with no separate `emitting_repo` concept on this plane.
- **`deployment_api`**'s ledger (`cicd/alerts/{date}/*.jsonl`) is the reader-merge target for the other 3 non-GHA planes
  too — `_repo_ci_alerts.py::_read_ledgers_sync()` walks `cicd/alerts/{date}/` (its own writer, `_persist_alert()`) AND
  separately reads `alerting/history/date=…/` (alerting-service) and the kill-switch parquet audit log, merging all
  three into one response. `subject_repo` on the GHA/ci-failures path is threaded from the caller (default: the calling
  workflow itself; ~18 confirmed cross-repo callers pass the real subject explicitly) — see `subject_repo` vs
  `emitting_repo` below.
- **`subject_repo` vs `emitting_repo`**: the repo an alert is ABOUT vs the repo whose workflow emitted it. These differ
  for ~6 fleet-wide watchers running IN `unified-trading-pm` that report on ANOTHER repo via a `repository_dispatch`
  payload (e.g. `ci-status-update.yml`, ~14.3k runs/30d). Filtering by repo on the page filters by `subject_repo` —
  filtering by the emitter would silently misattribute those cross-repo alerts.
- **`P` means the code contract writes the field, not that every historical object already carries it.** A live
  `alerting/history/` sample taken 2026-07-21 found only ~23% of that day's objects carrying the enriched
  `alert_class`/`severity`/`message`/`service`/`deployment_target` shape — the rest are the pre-enrichment
  delivery-status-only rows, mixed throughout the same day (not a clean before/after cutover). The reader tolerates both
  shapes; don't assume 100% enrichment from a spot-check without re-measuring against the live bucket.
- **`zombie_watchdog`** (`deployment-service/scripts/vm/vm_zombie_watchdog.py`) has no repo/severity concept — it's
  VM-scoped, not repo- or paging-tier-scoped, so those fields stay structurally `—`.
- **`kill_switch_audit`** is a read-only projection of the UTL parquet audit log (`kill_switch/audit_log.py`);
  `resolved_state` maps naturally (null while armed, set from `recovery_mode` on disarm). Its writer path is
  intentionally untouched by this ingestion work — the page mirrors, never alters, a write path.

### Retention + pagination policy

The ledger reads are **bounded day-partitioned walks** (never a whole-corpus scan — single-walk discipline applies here
same as data pipeline reads). `/api/alerts` and `/api/repo-ci/alerts` accept `days` / `offset` / `limit` query params:
default + max window is 30 days, default page size 400 / max 2000. A response that has more rows past the current page
sets `capped: true` explicitly — there is no silent truncation. The per-request entries cache is keyed by the `days`
window, so paginating within one window costs no extra reads. `health_overview`'s alerts health tile pins an explicit
`days=2` rather than inheriting the wider default, since its "recent" semantics predate the 30-day widening and would
otherwise read near-permanently critical.

### The `/alerts` page UI contract (deployment-ui, `pages/Alerts.tsx`)

Plan B (`deployment_ui_alerts_page_rebuild_2026_07_20.md`, shipped 2026-07-21) built the diagnostic-surface UI on top of
Plan A's normalised schema above. Every filter/sort/date-range param is **client-side and URL-backed** (deep-linkable,
no new backend query surface beyond the existing `days`/`offset`/`limit` from the retention section) — the page fetches
the full `days`-windowed response once, then narrows/reorders in-memory.

- **Filter dimensions** — `kind` (source, e.g. `alert`→"CI", `vm_down`→"VM") and `severity` (the
  `severity ?? conclusion ?? "info"` bucket) are multi-select (`?kind=a,b`, comma-joined, empty = no filter); `repo` and
  `service` (`workflow_name`) are single-select dropdowns. Options are derived from the LOADED alert set, not a
  hardcoded vocabulary — a kind/repo/service that never appears in the window never shows as a dead option.
- **Sort** — 4 columns (timestamp / severity / source / subject), click-to-cycle asc → desc → default (newest-first),
  URL-backed (`?sort_key=&sort_dir=`).
- **Date-range** — `?alert_from=&alert_to=` filters the already-loaded window by `timestamp` date. The retention-floor
  honesty banner ("No alerts before `<date>`") derives its boundary from the response's own `days` field
  (`today − (days − 1)`), never a hardcoded frontend constant — if the backend's retention window changes, the banner
  moves with it automatically.
- **Drill-down link map** — `deployment_target` → internal `/deployments/:name` (React Router `Link`) AND the shared
  `?logs=<target>` sub-param `AlertsLogsTab.tsx` already owns (swaps in `StreamingLogsPanel`, same target); `run_url` →
  external GHA run (new tab). No row carries a `runbook` field in the schema today (checked `AlertEntryDict` +
  `RepoCiAlertEntry` + the frontend mock) — that link is unimplemented until a future ingestion todo adds the field.
- **Shared-primitive reuse** (`deployment_ui_date_range_filter_and_search_2026_07_20.md` owns the extraction) —
  `FilterSelect`/`StatusFilterChips`+`chipTone`/`useColumnSort`/`compareByColumn` (`src/components/filters/`,
  `src/hooks/useColumnSort.ts`, `src/lib/columnSort.ts`) are imported, not re-derived; `Deployments.tsx`'s own
  `KindFilterChips` was generalized into a new shared `MultiChipFilter` (Set-backed multi-select chip row) reused by
  both pages. The alert-specific sort-key union/`columnSortValue`, and the date-range picker (`AlertDateRangeFilter`),
  stayed **local** to `Alerts.tsx` — the date-range widget wasn't extracted because the two pages' backends have
  different contracts (Deployments queries an explicit server-side `date_from`/`date_to`; alerts only has the
  `days`-back window above, filtered client-side), so sharing it would force a false abstraction over two different
  backend shapes.
- **Layout** — the Streams section (per repo/workflow current-vs-previous, worst-first) stays a visible, compact
  single-line-per-stream **summary** above the Timeline, which is the primary/full-width filterable+sortable surface.
  The Timeline rows deliberately stayed flex-divs, not a real `<table>` — "filterable/sortable" is behavior (state +
  handlers), not markup, and a table conversion was rejected as the highest-risk change to the testid-stability contract
  for no required benefit (operator/main ruling, BLK-de39d214, 2026-07-21).

## Cross-references

- Pipeline mechanics + the workflow inventory: [ci-cd-flow.md](/codex/08-workflows/ci-cd-flow.md) § "CI health monitor +
  branch-health" and § "Central CI watcher — auto-recover vs escalate, and the RESOLVED bookend".
- The sibling AO channel contract (same page-on-transition philosophy, server-side transport):
  [agent-orchestrator-alerting.md](agent-orchestrator-alerting.md).
- The `/alerts` page's `pw:L2` regression contract: `deployment-ui/tests/smoke/alerts-page.spec.ts` (23 cases as of
  2026-07-21 — filter/sort/date-range/drill-down/layout, each individually plus one deliberately combined case). See
  [ui-testing-layers.md](/codex/06-coding-standards/ui-testing-layers.md) for how this fits deployment-ui's own testing
  surface.
