---
title: "DP_* events have no end-to-end PubSub→subscriber→router path — cron/monitor alerts never reach #data-pipeline-alerts"
created: 2026-06-22
source:
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
  - DP-WATCHER (delivery substrate)
locked_by: live-defi-rollout
priority: P2
status: active
---

# DP\_\* event delivery gap — cron/monitor emits never reach Slack

## What I found

The Phase-0/Wave-3 substrate routes a DP\_\* event to `#data-pipeline-alerts` ONLY once it reaches the
alerting-service `route_event()`. `route_event()` is reached **exclusively** through the PubSub subscriber loop
(`alert_subscriber.stream()` → `route_event`). There is **no HTTP ingest** for ad-hoc events.

Two breaks make the cron/monitor → Slack chain non-functional today:

1. **Emitter side**: the e2e daily digest (`data_pipeline_daily_digest.py`) calls `setup_events(mode="local")`.
   In `mode="local"`, UTL `log_event` only logs to stdout (`_writer=None` branch) — it does **NOT** publish to
   any PubSub topic. So `emit_dp_event(DP_DAILY_DIGEST)` never leaves the container. The deployment-service
   monitors' `escalation.route_finding` calls `log_event(DP_*)` with **no `setup_events` at all** → in a real
   finding it would hit the `else: raise RuntimeError("Event logging not initialized")` branch (the monitors only
   ran clean today because the live fleet produced zero findings).
2. **Subscriber side**: a live `log_event` (mode="live") publishes to topic `lifecycle-events` (UTL
   `get_event_sink` default). The alerting-service `_ALERT_SUBSCRIPTIONS` tuple has **no `lifecycle-events`
   subscription** (only `risk_alerts_circuit_breaker_triggers` / `balance_discrepancy_alerts` /
   `order_rejection_spikes` / `service_error_events` / `margin-events` / `defi_data_quality_alerts`). So even a
   correctly-published DP\_\* event on `lifecycle-events` is never consumed → never routed → never mirrored.

The same gap latently affects **CONSOLIDATOR_DOWN**: its watchdog calls `log_event(CONSOLIDATOR_DOWN)` with no
`setup_events`, and the subscriber has no `lifecycle-events` subscription — so that page has likely never actually
delivered to Slack either (it has just never fired because no bucket went DOWN).

## Why it matters

The operator's explicit mandate for `data_pipeline_hardening_self_monitoring_2026_06_22.md` is "make the
data-pipeline alerts ACTUALLY FIRE … to #data-pipeline-alerts." The watcher/monitor Cloud Run Jobs + the 3 daily
audits are now deployed, but with this gap **no DP\_\* event reaches the channel** — the substrate is wired
emitter→router→Slack on paper, but the emitter→subscriber PubSub hop is missing. This is a data-pipeline
self-monitoring correctness gap (the alerts are the work item; they must fire).

## Recommended decision (being executed autonomously 2026-06-22, full authority)

Close both breaks, lowest-risk:

1. **alerting-service** — add a `lifecycle-events`-sourced subscription to `_ALERT_SUBSCRIPTIONS` (create
   `lifecycle-events-sub` in GCP if absent). DP\_\* + CONSOLIDATOR_DOWN published on `lifecycle-events` then reach
   `route_event()` → `_route_data_pipeline_event` → `#data-pipeline-alerts`. Redeploy the alerting subscriber.
2. **emitters** — the cron/monitor emitters must `setup_events(mode="live", sink=get_event_sink(mode="live",
   service_name=…, topic="lifecycle-events"))` (UTL helper) so `log_event` publishes. e2e digest/hygiene/reprobe +
   deployment-service `escalation.route_finding`.
3. Verify with a real `gcloud run jobs execute` of the digest → DP_DAILY_DIGEST visible in #data-pipeline-alerts.

This issue archives once (1)+(2) ship and the digest run posts to the channel.

## Resolution (2026-06-22, executed autonomously)

**Break-2 (subscriber) — SHIPPED + DEPLOYED.** `alert_subscriber.py` `_ALERT_SUBSCRIPTIONS` now includes
`lifecycle-events-sub` (alerting-service@`fdc2af7`). The alerting-quietness-baseline VM was reshipped (rebuilt
`alerting-service-code.tar.gz` from the new commit + relaunched) — the running subscriber NOW initialises with
`lifecycle-events-sub` in its tuple (verified in `run.log`). DP_* / CONSOLIDATOR_DOWN published on `lifecycle-events`
now reach `route_event()`.

**Break-1 (emitters) — partially SHIPPED.**

- deployment-service `escalation.route_finding` now calls `_ensure_live_events()` → `setup_events(mode="live",
  sink=PubSubEventSink(topic="lifecycle-events"))` before `log_event` (deployment-service@`5d07bb1`-successor). Verified
  type-clean + QG-green.
- e2e `_dp_common.py` `_ensure_live_events()` fix is VERIFIED working locally (a real
  `data_pipeline_daily_digest.py --asset-group cefi` run logs `Event logging initialized: mode=live`). Its quickmerge is
  blocked only by an unrelated dirty MTDS dep (separate cefi WIP); it has **no runtime effect until the digest/hygiene/
  reprobe Cloud Run crons deploy (Wave-4b)**, so it ships with that unit. Tracked.

**Two NEW findings surfaced during the reship (would have blocked alerting fleet-wide):**

1. **`defi_data_quality_alerts` subscription never existed in GCP** (the subgraph tf provisioned only the *topic*). The
   running subscriber predated commit `b6cbb2f` (which added it to `_ALERT_SUBSCRIPTIONS`), so it never hit it; the
   reship exposed a hard crash on startup — `404 NotFound (resource=defi_data_quality_alerts)` → whole subscriber
   exits rc=1 → VM self-deleted → ALL alerting offline. FIXED: created the subscription
   (`gcloud pubsub subscriptions create defi_data_quality_alerts --topic=defi_data_quality_alerts`).
2. **`AlertSubscriber.stream()` had no per-subscription error isolation** — one bad/missing subscription crashed the
   entire round-robin loop. HARDENED: wrapped `subscribe_once` in try/except → log + skip that subscription this round,
   self-heals once provisioned (alerting-service@`b87ccc1`). A missing sub can no longer take down all alerting.
3. **`launch-alerting-quietness-baseline.sh` metadata bug** — leading-whitespace on the `--metadata="\`-continuation
   lines produced invalid metadata keys (`  CODE_BUCKET`), so `gcloud instances create` 400-errored. FIXED (stripped
   indentation; shipped with escalation.py).

4. **IAM 403 on `lifecycle-events-sub` AND `defi_data_quality_alerts`** — the VM's default compute SA
   (`1060025368044-compute@developer.gserviceaccount.com`) had `roles/pubsub.subscriber` on the 5 original subs but
   NOT on these two (empty IAM policy on `lifecycle-events-sub`; freshly-created `defi_data_quality_alerts` had no
   binding). The reship's subscriber pulled them → `403 IAM_PERMISSION_DENIED` (the crash-resilience hardening caught +
   skipped, so the subscriber stayed up, but DP events were still not consumed). FIXED: granted `roles/pubsub.subscriber`
   to the compute SA on both subs (mirroring the `margin-events` binding). CONFIRMED LIVE: last 403 at 18:16:01,
   zero 403s for 11+ min after (subscriber now pulls `lifecycle-events-sub` cleanly → DP_DAILY_DIGEST consumed +
   routed). The grant is on the SUBSCRIPTION (persistent) → survives VM relaunches.

**RELAY NOW LIVE END-TO-END (2026-06-22 18:27Z)**: emit (mode=live → lifecycle-events) → subscriber consumes
lifecycle-events-sub (no 403) → route_event → _route_data_pipeline_event → #data-pipeline-alerts (webhook verified 200,
DP_DAILY_DIGEST INFO rule live in UAC).

5. **Alerting VM stall-watchdog self-delete loop (the recurring "no alerts" cause)** — the alerting subscriber runs
   under the batch-VM wrapper (`setup-data-pipeline-vm.sh`), whose stall-watchdog SIGKILLs (exit 137 → VM self-delete)
   when the on-VM log doesn't grow for `STALL_TIMEOUT_SEC` (default 1800s). A **quietness-baseline is meant to be
   quiet**, so a quiet subscriber was killed every ~30 min → alerting offline most of the time. FIXED:
   `launch-alerting-quietness-baseline.sh` now sets `STALL_TIMEOUT_SEC=190800` (>48h run) so quiet ≠ stall-kill. The fix
   is LIVE on the running VM (launched from the edited launcher); the LDR ship is dirty-MTDS-dep-blocked (tracked).
   PROPER durable fix (standing item): run alerting as a permanent long-lived service (systemd / Cloud Run min-instances=1),
   not under the batch stall-watchdog.

**Monitor-image gap (automated VM-issue alerts):** the 3 DP fleet-monitor Cloud Run jobs run `deployment-api:latest`
built 14:29 (pre the 17:52 escalation emit-fix). The emit path is PROVEN (a real `route_finding(DP_VM_EXIT_NONZERO)`
from fixed code returned `emitted:True` + routed), but until `deployment-api:latest` rebuilds with the escalation fix
(draining LDR→main) + the 3 jobs are re-pointed, an automated finding is detected-but-not-posted. Next step: rebuild
image (or wait for promotion) → `gcloud run jobs update` the 3 monitors.

**Remaining (tracked, NOT blocking the relay — it is live):**
- (a) e2e `_dp_common.py` ship (Wave-4b, currently dirty-MTDS-dep-blocked; no runtime effect until the crons deploy).
- (b) Deploy the 3 daily-audit Cloud Run crons (digest/hygiene/reprobe) for routine *cadence* — needs image packaging (Wave-4b).
- (c) **Durability — codify in terraform**: `lifecycle-events-sub` + `defi_data_quality_alerts` subscriptions AND their
  `roles/pubsub.subscriber` IAM bindings for the alerting VM SA are currently HAND-CREATED (the subgraph tf provisions
  only the `defi_data_quality_alerts` *topic*). They survive VM relaunches (subs are persistent) but a `terraform apply`
  or fresh-project bootstrap would drop them. Add to `deployment-service/terraform/gcp/` (alerting pubsub tf): both
  `google_pubsub_subscription` + `google_pubsub_subscription_iam_member` resources.
