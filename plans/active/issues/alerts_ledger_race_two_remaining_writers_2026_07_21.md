---
doc_type: issue
title:
  Two more writers into cicd/alerts/{date}/alerts.jsonl still do the unlocked read-modify-write after todo 6 fixed
  deployment-api's own writer — notify-slack.yml and semver-agent.yml.tmpl (fleet-wide)
summary: >-
  deployment_alerts_ingestion_completeness_2026_07_20.md todo 6 fixed the read-modify-write row-drop race
  (persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md) for exactly the two instances it named: the
  persist-event composite action (events ledger) and deployment-api's `_persist_alert()` (alerts ledger). While
  investigating (b), a workspace-wide search for other writers into the same `cicd/alerts/{date}/alerts.jsonl` object
  surfaced TWO more writers doing the identical unlocked cp-down->append->cp-up dance, neither named in todo 6 and
  therefore not fixed by it: `unified-trading-pm/.github/workflows/notify-slack.yml`'s own "Persist alert to ledger"
  step (its own comment says "KNOWN-LOSSY under concurrency — the open D2 ledger-race decision" — i.e. this was already
  a KNOWN, deliberately-deferred instance of the same bug, just not named in the 2026-07-17 issue doc or todo 6), and
  `semver-agent.yml.tmpl`'s "Persist CRITICAL pages to alert ledger" step (rolled out fleet-wide via
  `rollout-workflow-templates.sh` to every service repo's `semver-agent.yml`). Both write the same `event_type:
  "slack_alert"` row shape deployment-api's reader already parses — no reader compatibility question, unlike the
  original issue's "who reads this" open question. The fix is the SAME pattern already applied twice (one object per
  write instead of a shared per-day filename), just not yet applied to these two remaining writers.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, event-ledger, gcs, race-condition, data-loss, read-modify-write, alerts]
related:
  [
    plans/active/deployment_alerts_ingestion_completeness_2026_07_20.md,
    plans/active/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md,
  ]
created: 2026-07-21
parent_epic: observability_master
priority: P2
source:
  deployment_alerts_ingestion_completeness_2026_07_20.md todo 6 (slot 7, 2026-07-21) — found while fixing
  deployment-api's `_persist_alert()` read-modify-write race; a workspace-wide grep for other writers into the same
  `cicd/alerts/{date}/alerts.jsonl` object surfaced these two.
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-21
locked_by:
resolved_by:
depends_on: []
---

# Two more writers into the alerts ledger still race

## What I found

`cicd/alerts/{date}/alerts.jsonl` (GCP; `unified-trading-cicd-events` bucket) has THREE independent writers doing an
unlocked read-modify-write onto the SAME shared per-day object, only one of which (`deployment-api::_persist_alert()`)
has been fixed to write a unique object per call instead:

1. **`unified-trading-pm/.github/workflows/notify-slack.yml`** ("Persist alert to ledger (best-effort)" step, ~lines
   391-443):
   `gsutil cp "$GCS_URI" "$LOCAL_FILE" ... ; echo "$ALERT_JSON" >> "$LOCAL_FILE" ; gsutil cp "$LOCAL_FILE" "$GCS_URI"`.
   Its own comment: "History append (best-effort; KNOWN-LOSSY under concurrency — the open D2 ledger-race decision.
   Dedup deliberately does NOT depend on this object.)" — this is the SAME bug, already known and explicitly deferred
   when the 2026-07-17 dedup-marker fix (`cicd/alerts/dedup/<key>.json`, atomic overwrite) was scoped to the dedup axis
   only, not the history append.
2. **`unified-trading-pm/scripts/workflow-templates/semver-agent.yml.tmpl`** ("Persist CRITICAL pages to alert ledger"
   step, ~lines 864-895 in the rendered per-repo copy): identical `gsutil cp down -> cat >> -> gsutil cp up` pattern,
   rolled out fleet-wide to every service repo's own `semver-agent.yml`. This one was NOT previously documented anywhere
   — it surfaced only from a workspace-wide grep for other writers into the same object while implementing todo 6(b).

Both write `event_type: "slack_alert"` rows deployment-api's `_repo_ci_alerts.py::_parse_line()` already parses
identically to the now-fixed `_persist_alert()` path — there is no reader-compatibility question here (unlike the
original 2026-07-17 issue's open "who reads this ledger" question, which is now answered: deployment-api's
`_read_ledgers_sync()`, which already does a prefix walk over `cicd/alerts/{date}/`, not a fixed filename).

## Why it matters

Fixing only `deployment-api::_persist_alert()` (todo 6b, `deployment-api@dbeb5c9`) makes deployment-api's OWN
alert-persist contribution race-free, but does NOT close the alerts-ledger race overall: notify-slack.yml and
semver-agent.yml.tmpl still clobber EACH OTHER (and always did — this is not a regression from todo 6, just an unfixed
pre-existing condition). Any alert posted by either of these two writers can still be silently dropped if another write
to the same date-partition lands in the same few-second window — exactly the mechanism the 2026-07-17 issue doc measured
(21 alerts/day survived on 2026-07-17 against ~11 known promotion-lag posts, implying most of the day's writes were
clobbered).

## Recommended decision

Apply the SAME fix already proven twice in this session (`.github/actions/persist-event/action.yml`'s events-ledger
write, and `deployment-api::_persist_alert()`'s alerts-ledger write): write each alert straight to its own
never-overwritten object (e.g. `cicd/alerts/{date}/{unique-id}.jsonl`) instead of the shared `alerts.jsonl` filename. No
reader change needed — `_read_ledgers_sync()` already globs the whole `cicd/alerts/{date}/` prefix.

- [ ] [DEVOPS] P2. Fix `notify-slack.yml`'s "Persist alert to ledger" step to write to a unique object per call (e.g.
      `cicd/alerts/{date}/{dedup_key-or-random}-{run_id}.jsonl`) instead of the shared `alerts.jsonl`, matching the
      pattern in `persist-event/action.yml`'s GCS/S3 write steps. Do NOT touch the dedup-marker write
      (`cicd/alerts/dedup/<key>.json`) — that one is already a single-object-per-key atomic overwrite and is not part of
      this race. (repo: unified-trading-pm)
- [x] ✅ [DEVOPS] P2. Fix `semver-agent.yml.tmpl`'s "Persist CRITICAL pages to alert ledger" step the same way, then
      re-run `rollout-workflow-templates.sh --template semver-agent.yml.tmpl` to propagate the fix fleet-wide to every
      service repo's rendered `semver-agent.yml`. (repo: unified-trading-pm) — unified-trading-pm@963daa611 (template
      fix: writes each run's queued pages to a unique `cicd/alerts/{date}/{run_id}-{job_id}-{ts}-{rand}.jsonl` object
      instead of the shared read-modify-write onto `alerts.jsonl`) + rollout-workflow-templates.sh re-run propagated the
      rendered `.github/workflows/semver-agent.yml` to all 24 service repos, each committed + pushed to
      `live-defi-rollout` individually: alerting-service@358aff4, batch-live-reconciliation-service@d03249d,
      client-reporting-api@55b42a6, deployment-api@c4f4500, deployment-service@1369fea, execution-service@d584ab3,
      features-service@e26db5f, fund-administration-service@c2b34d1, greeks-service@2b51324, ibkr-gateway-infra@2592941,
      instruments-service@274e6d9, market-data-processing-service@bf2ea29, market-tick-data-service@c918381,
      ml-service@29601a0, strategy-service@d206a2c, system-integration-tests@d91ce2a, trading-agent-service@9ccd80d,
      unified-api-contracts@61b5b11, unified-trading-library@0d1bf0c4, unified-trading-api@067c271,
      unified-trading-system-ui@d10b373, deployment-ui@51cbeda, e2e-testing@1d3a6ad, agent-orchestrator@162762e.
