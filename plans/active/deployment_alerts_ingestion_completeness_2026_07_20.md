---
doc_type: plan
title: deployment alerts — ingestion completeness (WS-5 Plan A — mirror the Slack alert sources to the ledger)
summary: >-
  Coverage audit 2026-07-20 found the /alerts ledger has ingested 181 rows in its entire lifetime across 10 date
  partitions, while a single 10-day Slack export window shows thousands of real alerts with ZERO ledger objects for that
  period. The alerts page is a DIAGNOSTIC surface, not a paging one — Slack is the primary alert channel but has no
  filter/sort/date-range, so we mirror the alert sources that already flow to Slack and are cheap to copy into the
  ledger, where they can be filtered and drilled into to find root causes. Highest-leverage: ingest the alerting-service
  store (its own bucket, 29 date partitions current, ~20 alert classes feeding #uts-live-alerts/#data-pipeline-alerts) —
  one change closes ~12 gaps. Plus fix the emitting-vs-subject repo defect, the hardcoded-bucket QG violation, the
  read-modify-write row-drop race, retention wide enough for a real date range, and persistence for the zombie-watchdog
  webhook that currently records nothing. Agent-orchestrator alerts are explicitly DEFERRED (AO has its own alert
  machinery + UI). The page rebuild is Plan B, gated on this.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [alerts, observability, ingestion, deployment-ui]
related:
  - deployment_ui_observability_ux_tracker_2026_07_17.md
  - deployment_ui_alerts_page_rebuild_2026_07_20.md
  - issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md
created: "2026-07-20"
last_updated: "2026-07-20"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  split from deployment_ui_observability_ux_tracker_2026_07_17.md WS-5, coverage audit + operator decisions 2026-07-20
---

# deployment alerts — ingestion completeness (Plan A)

> **🟢 ACTIVE (operator 2026-07-21)** — second-wave dispatch to AO (throughput ramp). Must-do review fixes applied
> before activation: the ingest todo now handles the `resolve_bucket_name()` gap (no registry entry for the
> alerting-service bucket → add one first); the race-fix todo now covers BOTH the `cicd/events/` race (issue doc) AND
> the unaddressed `cicd/alerts/` `_persist_alert` race.
>
> **Plan A of two.** Plan B (`deployment_ui_alerts_page_rebuild_2026_07_20.md`) rebuilds the page UI and is draft-gated
> on this plan — Plan B stays `draft` until this completes (its filter dimensions depend on the normalised schema
> landing here).

## The framing (operator, 2026-07-20)

**The alerts page is a diagnostic surface, not a paging surface.** Alerts exist so we can diagnose and fix root causes —
the end goal is a _clear_ alerts page, which only happens once the underlying problems are solved. Slack is the primary
alert channel today, but Slack has no filter / sort / date-range. So this workstream **mirrors the alert sources that
already flow to Slack into the ledger** — at least the ones cheap to copy — so they become filterable/sortable/drillable
in the UI. This is not about making the page page you; AO and PagerDuty already do that.

## Context — coverage audit findings (2026-07-20, read-only)

**The ledger is starved, not merely unfiltered.**

- `/alerts` → `GET /api/alerts` → `deployment-api/deployment_api/routes/unified_alerts.py:30` →
  `_repo_ci_alerts.py:load_alerts_payload()`. Source is GCS only:
  `gs://unified-trading-cicd-events/cicd/alerts/{date}/alerts.jsonl`. No Slack API, no Firestore, no DB.
- **Live-verified volume**: 10 date partitions have ever existed; **181 rows lifetime**. The `_DEFAULT_DAYS = 2` window
  (`_repo_ci_alerts.py:31`, `_MAX_ITEMS = 400` at `:32`) renders **14 rows** today. "Only a few alerts" is literally
  correct.
- **The high-leverage source — alerting-service — is invisible.** It has its own bucket
  (`alerting-service-central-element-323112`), its own store (`alerting/history/date=…/*.jsonl`,
  `persistence/storage_store.py:72-77`), **29 date partitions current through 2026-07-20**, ~20 alert classes, feeding
  `#uts-live-alerts` / `#data-pipeline-alerts` / PagerDuty / Twilio. Nothing in deployment-api reads it
  (grep-confirmed). This is exactly the "already on Slack, cheap to copy" population — it's an existing durable store;
  we just read it. Its ~20 classes: consolidator-down, data-status RED / DP_* watchers, VM preemption/exit-nonzero,
  recon freeze/drift, risk-rule fired, margin events, service circuit-open / SERVICE_ERROR, CeFi ML staleness, DeFi
  feature (AAVE/funding/weETH/stale), and more.
- **Defect — `repo` is the emitting repo, not the subject.** A `unified-trading-library` CI regression is stored
  `repo=unified-trading-pm`, so filtering by repo today returns wrong answers. Needs a distinct `subject_repo`.
- **Defect — hardcoded bucket** at `_repo_ci_alerts.py:27` and `deployments_inventory.py:342` bypasses
  `resolve_bucket_name()` (QG 5.69 violation; test asserts the literal at
  `tests/unit/test_route_deployments_inventory.py:854`).
- **Defect — row-drop race**: unlocked read-modify-write silently drops concurrent rows, documented in
  `plans/active/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md`. A contributing cause of the
  starvation on the KEPT ci-failures path.
- **zombie-watchdog reaps record nothing** — `deployment-service/scripts/vm/vm_zombie_watchdog.py:247` fires a raw Slack
  webhook with **no durable persist at all**. A real VM-lifecycle diagnostic that vanishes after the Slack message
  scrolls away.
- **alerting-service stores delivery status only** — its history rows are
  `alert_id, channel, status, response_detail, event_name, timestamp`, with **no severity, message body, or target**.
  Mirroring them usefully requires persisting the full payload at the source (decision 2).
- **Policy check (resolved)** — `codex/04-architecture/agent-orchestrator-alerting.md:31-32,47-48`: the actionable-only
  rule constrains **Slack only**; the page is the designated _fuller_ diagnostic surface. Showing more on the page than
  pages Slack is the intent, not a violation.
- **Correction to the tracker**: cost-anomaly alerts **do not exist** — no emitter anywhere. They are a build, not an
  ingestion gap. Out of scope.

## Decisions (operator, 2026-07-20)

1. **Two plans** — ingestion (this, P0) and page rebuild (Plan B, draft-gated on it). The page's filter/sort dimensions
   are determined by what fields actually arrive.
2. **alerting-service** — change the emitter to persist the **full alert payload** (severity, message, target) alongside
   delivery status, rather than joining back to source events at read time in deployment-api. Its stored history is
   currently delivery-status only, which is just as detail-poor for any other consumer; fix the record at the source.
3. **Agent-orchestrator alerts — DEFERRED entirely.** AO already has extensive alert machinery in its backend and its
   own UI surfaces the alerts the operator acts on. The AO-alert ingestion (including the 6 page-verdict notifiers that
   page but don't persist, and the broader persist/post situation the audit found) is a **later workstream**, not this
   one. No AO code is touched here.

## Todos

- [x] ✅ [REVIEW] P0. **Define the normalised alert schema** — the union shape every mirrored source writes to. Fields:
      `timestamp`, `source_plane` (gha / deployment-api / alerting-service), `subject_repo` (the repo the alert is ABOUT
      — see the defect), `emitting_repo`, `severity`, `alert_class`, `message`, `service`, `deployment_target`,
      `run_url`/`link`, `dedup_key`, `resolved_state` (nullable). Document per-source which fields are populatable and
      which are structurally absent — this table is the contract Plan B builds its filters against, so it is the gating
      deliverable. — `unified-api-contracts@9f51c058`: `NormalizedAlertRow` + `AlertSourcePlane` + `FIELD_COVERAGE` in
      `unified_api_contracts/canonical/crosscutting/alerting/ledger.py`, exported from the
      `unified_api_contracts.alerting` facade; closed-set tests in `tests/internal/unit/test_alert_ledger_schema.py`.
      Human-readable coverage table below (§ "Normalised alert schema (contract)"). Widened `source_plane` to 5 values
      (added `zombie_watchdog` + `kill_switch_audit`) so the P1/P2 ingestion todos below don't need a schema change
      later.
- [ ] [BACKEND] P0. **alerting-service — persist the full payload** (decision 2). Extend `persistence/storage_store.py`
      writes so `alerting/history/` carries severity, message body, target, and alert_class alongside the existing
      delivery-status fields, conforming to the normalised schema.
- [ ] [BACKEND] P0. **deployment-api — ingest the alerting-service store.** Read `alerting/history/date=…/*.jsonl` into
      the unified alerts response. **This single item mirrors ~12 alert classes at once** — the highest-leverage change
      in the workstream, and the cheapest (an existing durable store, just read it). **Bucket-resolution caveat
      (verified):** the alerting-service bucket (`alerting-service-{project}`, derived by alerting-service's own private
      `_bucket_name()`) has **no kind entry** in `deployment-service/configs/cloud-providers.yaml` today, so
      `resolve_bucket_name()` cannot resolve it as-is — FIRST add a `gcp.storage` kind entry for it to that config, THEN
      resolve via `resolve_bucket_name()`. Do NOT hardcode the literal (that recreates the QG 5.69 violation a sibling
      todo fixes). Bounded day-partitioned reads only (no whole-corpus walk).
- [ ] [BACKEND] P0. **Fix the emitting-vs-subject repo defect** — populate `subject_repo` distinctly from the emitting
      repo on the GHA/ci-failures path, so repo filtering returns correct results.
- [ ] [BACKEND] P1. **Fix the hardcoded bucket** (QG 5.69) — `_repo_ci_alerts.py:27` and `deployments_inventory.py:342`
      → `resolve_bucket_name()`. Update `tests/unit/test_route_deployments_inventory.py:854` which asserts the literal.
- [ ] [BACKEND] P1. **Fix the read-modify-write row-drop race — BOTH instances.** (a) The one in
      `issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md` (the GHA composite action
      `.github/actions/persist-event` writing `cicd/events/…` — a bash fix via the template +
      `rollout-workflow-templates.sh`, not a same-repo Python patch); AND (b) a structurally-identical,
      currently-UNADDRESSED race in `deployment_api/routes/deployments_inventory.py::_persist_alert` (~L604-609) writing
      `cicd/alerts/…` — right next to the hardcoded-bucket fix. Fix both. Close the issue doc when (a) is done; note (b)
      in the Progress Log.
- [ ] [BACKEND] P1. **Retention + window** — `_DEFAULT_DAYS = 2` / `_MAX_ITEMS = 400` cannot support the date-range
      filter Plan B needs. Implement a retention/window policy (proposed default: 30 days queryable via bounded
      day-partitioned reads, response paginated rather than truncated at a silent cap). A silent 400-item truncation
      must become an explicit "results capped" signal — never a silently short list.
- [ ] [BACKEND] P1. **zombie-watchdog reaps — add persistence.**
      `deployment-service/scripts/vm/vm_zombie_watchdog.py:247` fires a raw Slack webhook with no durable record; route
      it through the normalised persist path so the reap history survives on the page.
- [ ] [BACKEND] P2. **Kill-switch events (cheap read-only projection).** Surface arm/disarm from the existing parquet
      audit log (`gs://{pid}-kill-switch-audit-log/`, `UTL kill_switch/audit_log.py`) into the normalised feed — high
      diagnostic value, and cheap because it's a read-only projection of a store that already exists. Do not alter any
      kill-switch write path.
- [ ] [REVIEW] P1. Tests — (a) alerting-service persists the full payload; (b) deployment-api ingests and normalises it;
      (c) `subject_repo` is the subject, not the emitter, for a known cross-repo CI regression; (d) concurrent writes no
      longer drop rows; (e) retention/window returns the full requested range and signals capping explicitly; (f)
      buckets resolve via `resolve_bucket_name()`; (g) a zombie-watchdog reap lands a durable row.
      `bash scripts/quality-gates.sh` green in alerting-service, deployment-api, deployment-service.
- [ ] [REVIEW] P1. **Post-ingestion coverage re-measure** — re-run the audit's gap table against the live ledger and
      record before/after row counts and per-source coverage in the Progress Log. Success is MEASURED coverage, not
      "code shipped": a source counts as mirrored only when its rows are observably in the ledger.
- [ ] [INFRA] P1. Ship (`quickmerge.sh "msg" --agent --files '<paths>'` across the repos) + flip todos same turn
      (`docs(plans):`).
- [ ] [REVIEW] P2. Post-phase codex audit — document the normalised alert schema, the per-source coverage matrix, the
      "diagnostic surface / mirror-cheap-Slack-sources" principle, the persist-vs-page distinction, and the retention
      policy in `codex/04-architecture/ci-alerting.md`. Flip Plan B `draft` → `active` as the final act.

## Normalised alert schema (contract)

Landed 2026-07-21 (todo 1). SSOT is code, not this table: `NormalizedAlertRow` / `AlertSourcePlane` / `FieldCoverage` /
`FIELD_COVERAGE` in `unified-api-contracts` `unified_api_contracts/canonical/crosscutting/alerting/ledger.py`, imported
via the `unified_api_contracts.alerting` facade (never the deep path). This table is a read-only projection of
`FIELD_COVERAGE` for humans — if it ever disagrees with the code, the code wins; re-generate this table rather than
hand-editing around a drift.

Legend: **P** = populated today · **p** = populatable (value exists at the emit site, not wired yet — a sibling todo
below fixes it) · **—** = structurally absent (the concept doesn't exist for that source; a permanent gap, not a bug).

| field               | gha_ci_events | deployment_api | alerting_service | zombie_watchdog | kill_switch_audit |
| ------------------- | :-----------: | :------------: | :--------------: | :-------------: | :---------------: |
| `timestamp`         |       P       |       P        |        P         |        p        |         P         |
| `subject_repo`      |       P       |       p        |        —         |        —        |         —         |
| `emitting_repo`     |       —       |       P        |        p         |        p        |         p         |
| `severity`          |       —       |       P        |        P         |        —        |         —         |
| `alert_class`       |       —       |       P        |        p         |        p        |         p         |
| `message`           |       —       |       P        |        p         |        p        |         p         |
| `service`           |       —       |       —        |        p         |        —        |         p         |
| `deployment_target` |       —       |       p        |        p         |        p        |         —         |
| `run_url`           |       p       |       P        |        —         |        —        |         —         |
| `dedup_key`         |       —       |       P        |        —         |        p        |         p         |
| `resolved_state`    |       —       |       —        |        —         |        —        |         p         |

Notes worth surfacing beyond the matrix:

- **`gha_ci_events`** (`.github/actions/persist-event` → `cicd/events/{repo_name}/{date}/events.jsonl`): `subject_repo`
  maps from `repo_name` and is correct as-is here — each repo's workflow reports on itself, so there is no separate
  `emitting_repo` concept for this plane. The `repo`-vs-`repo_name` defect (todo 4) is specific to the OTHER ledger
  (`deployment_api`), where the field is misnamed `repo` and holds the emitter.
- **`deployment_api`**'s `_persist_alert()` currently takes `(alert_class, workflow_name, severity, message, dedup_key)`
  — no `deployment_target` param exists yet even though `_repo_ci_alerts.py`'s reader already knows how to extract
  `vm_name`/`deployment_id` from `details`. Both `subject_repo` (todo 4) and `deployment_target` need a writer-side
  change, not just a reader-side one.
- **`alerting_service`**'s delivery-record row (`channel, status, response_detail, event_name, timestamp`) is
  detail-poorer than its decision record (`severity, message` already present); todo 2 unifies both onto this schema.
  `service`/`deployment_target` are already computed in `notifiers/router.py` for the Slack payload — todo 2 is "persist
  what's already computed," not new derivation logic.
- **`zombie_watchdog`** has zero persistence today (todo 7 adds it); every field is either `p` (constructible from the
  existing `WatchdogVerdict` dataclass: `vm_name`, `zone`, `age_minutes`, `verdict` reason string) or `—` (no
  repo/severity concept — it's VM-scoped, not repo- or paging-tier-scoped).
- **`kill_switch_audit`** (todo, P2) is a read-only projection of the UTL parquet audit log — `resolved_state` maps
  naturally (null while armed, set from `recovery_mode` on disarm); `severity` has no native equivalent (armed/disarmed
  isn't a paging-tier axis) so stays `—` rather than inventing a synthetic mapping.

## Explicitly deferred (not in this plan)

- **All agent-orchestrator alerts** (decision 3) — including the 6 page-verdict notifiers the audit found that page
  CRITICAL but persist nothing (`notify_account_auth_failed:1490`, `notify_account_auth_recovered:1522`,
  `notify_setup_token_expiring:1461`, `notify_escalation_unresolved:1241`, `notify_slot_quarantined:1312`,
  `notify_gh_rate_limit_threshold:1715`, all in `agent-orchestrator/server/notifications/slack.py`), and the ~72%-signal
  log-only lifecycle pool (auto-respawn / respawn-FAILED / spawn-failure / unpushed-plans). Recorded here so the
  analysis isn't lost; a later AO-alerts workstream picks it up after the operator's AO changes land.
- **semver-agent account-dead alerts** — post via direct `curl` across ~21 repos
  (`agent-orchestrator/.github/workflows/semver-agent.yml`), so routing them through the persist path is a
  workflow-template rollout, not a cheap copy. Deferred with the AO work.
- **Cost-anomaly alerts** — no emitter exists; a build, not an ingestion gap.

## Success criteria

- Measured (not claimed) coverage: alerting-service's ~20 classes and the zombie-watchdog reaps are observably present
  in the ledger; every other source is either mirrored or explicitly listed as deferred with a reason.
- alerting-service rows carry severity, message, and target — not delivery status alone.
- Repo filtering returns alerts ABOUT a repo, not alerts emitted BY a repo.
- The ledger retains and serves a window wide enough for Plan B's date-range filter, with explicit capping signals
  rather than silent truncation.
- No hardcoded bucket literals; no silent row drops under concurrent writes.

## Progress Log

- **2026-07-20** — Split from `deployment_ui_observability_ux_tracker_2026_07_17.md` WS-5 as Plan A of two. Ran the
  operator-mandated coverage audit live (read-only). Headline: the ledger holds 181 rows lifetime against thousands of
  real Slack alerts in a single 10-day sample window, with the alerting-service plane (~20 classes, current through
  today) entirely invisible to deployment-api. Operator reframed the goal: the alerts page is a DIAGNOSTIC surface —
  mirror the Slack alert sources that are cheap to copy so they become filterable/drillable, not a new paging surface.
  **All AO alerts deferred** (AO has its own alert machinery + UI; the audit's AO findings — 6 page-verdict notifiers
  that page but don't persist, plus the ~72%-signal log-only lifecycle pool — are recorded in the Deferred section for a
  later workstream). Confirmed via codex the actionable-only policy constrains Slack only. Also found: the `repo` field
  records the emitter not the subject (repo filtering currently wrong), a hardcoded-bucket QG violation, and that
  cost-anomaly alerts have no emitter at all. Decided: fix alerting-service at the emitter (persist full payload) rather
  than joining at read time.

- **2026-07-21** — Todo 1 (normalised alert schema) shipped: `NormalizedAlertRow` / `AlertSourcePlane` /
  `FIELD_COVERAGE` landed in `unified-api-contracts` (`canonical/crosscutting/alerting/ledger.py`, exported via the
  `unified_api_contracts.alerting` facade) with closed-set tests. Widened `source_plane` from the 3 named in the todo
  brief to 5 (added `zombie_watchdog`, `kill_switch_audit`) since todos 7 and the P2 kill-switch item both need to stamp
  a source plane and re-touching the enum later would be a breaking change to an already-shipped contract. Per-source
  coverage table added to this doc (§ "Normalised alert schema (contract)") as the human-readable read-only projection
  of `FIELD_COVERAGE` — code is the SSOT, table is generated-by-hand today (no codegen yet; keep them in sync manually
  until/unless that becomes a real drift risk). Key finding carried into the remaining todos:
  `deployment_api._persist_alert()` needs a writer-side signature change for BOTH `subject_repo` (todo 4) and
  `deployment_target` (not previously called out as needing a writer change) — the reader (`_repo_ci_alerts.py`) already
  knows how to parse `deployment_target` from `details`, but nothing writes `details` today.

## Codex SSOTs

- `codex/04-architecture/ci-alerting.md` — the `notify-slack.yml` carrier, dedup keys/cooldowns, fail-open reads; (to
  add) the normalised alert schema, the diagnostic-surface principle, and the retention policy.
- `codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only policy (Slack-scoped), the ledger as the
  fuller surface.
- `codex/05-infrastructure/bucket-isolation-model.md` + `codex/05-infrastructure/gcs-object-operations.md` —
  `resolve_bucket_name()` and UTL GCS wrappers (QG 5.69).
- `codex/02-data/availability-manifest-and-data-status.md` — single-walk discipline (bounded day-partitioned reads).
