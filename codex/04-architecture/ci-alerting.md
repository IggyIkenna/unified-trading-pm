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
  [../08-workflows/ci-cd-flow.md, agent-orchestrator-alerting.md, ../05-infrastructure/quickmerge-architecture.md]
created: 2026-07-13
authoritative_for: [ci-failures Slack alert routing, notify-slack.yml dedup contract, CI-alert cooldown selection]
referenced_by:
owner:
last_reviewed: 2026-07-13
code_refs:
  - .github/workflows/notify-slack.yml
  - .github/workflows/branch-health.yml
  - .github/workflows/python-quality-gates-v2.yml
  - .github/workflows/ci-status-update.yml
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

| Reporter (workflow · job)                        | Fires on                                                      | `dedup_key`                 | `cooldown_min` | Notes                                                                                                                                                                             |
| ------------------------------------------------ | ------------------------------------------------------------- | --------------------------- | -------------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `branch-health.yml` · `lag-notify`               | promotion lag (LDR↔staging↔main stuck > threshold)          | `promotion-lag`             |            120 | re-remind ≈ every 3 real promote cycles (WS-1, 2026-07-13); see cadence note below                                                                                                |
| `branch-health.yml` · `lag-notify-resolved`      | lag cleared                                                   | `promotion-lag-cleared`     |             30 | shorter than the open cooldown so the all-clear is never swallowed                                                                                                                |
| `branch-health.yml` · `ar-lag-notify`            | Artifact-Registry dep-publish lag                             | `ar-dep-publish-lag`        |             60 | fail-open (GCP auth errors → no lag reported)                                                                                                                                     |
| `python-quality-gates-v2.yml` · `notify-qg-fail` | a QG slice failed / cancelled                                 | `qg-fail:<repo>:<ref_name>` |            120 | **per-branch, not per-sha** (WS-3, 2026-07-13): a still-red branch pages once per red-period, not per failing push; a new failure after the cooldown still re-alerts              |
| `ci-status-update.yml` · `notify`                | a repo's CI **went red** (`client_payload.status=='FAILING'`) | _(none — per-transition)_   |            n/a | green `CI-RECOVERED` / SIT-pass all-clears are NOT posted (WS-2, 2026-07-13); Firestore CAS + `is_stale_write` order the transitions; Firestore + GCS-ledger writes are unchanged |

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
6. **Cooldown tracks the REAL cadence of the condition, not the declared cron.** GitHub throttles `schedule:` crons to
   ≈37% of the declared rate — the promote gate declares `*/15` but the **measured** cadence over 60 runs was avg **41.5
   min** (median 33, max 93). So a promotion-lag that is merely waiting for a throttled promote should not re-page
   hourly: the 120-min cooldown ≈ 3 real promote cycles. When picking a cooldown, measure the condition's true period
   first (`gh api …/actions/workflows/<wf>/runs`), don't assume the cron.

## Cross-references

- Pipeline mechanics + the workflow inventory: [ci-cd-flow.md](../08-workflows/ci-cd-flow.md) § "CI health monitor +
  branch-health" and § "Central CI watcher — auto-recover vs escalate, and the RESOLVED bookend".
- The sibling AO channel contract (same page-on-transition philosophy, server-side transport):
  [agent-orchestrator-alerting.md](agent-orchestrator-alerting.md).
