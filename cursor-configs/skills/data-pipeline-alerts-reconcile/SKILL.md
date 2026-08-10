---
name: data-pipeline-alerts-reconcile
description:
  Reconcile the `#data-pipeline-alerts` Slack channel to actually-quiet, at the root cause — not just re-reading the
  alert text. Cross-checks every DP-* alert against the failure-mode registry (`codex/05-infrastructure/data-pipeline-
  alerts.md` + `.registry.yaml`), classifies each by root cause (genuine detector-caught failure / routing-or-dedup bug
  / self-heal actuator gap / the fix's OWN deploy path is broken / already self-resolved / registry-unregistered event
  falling through to the wrong channel), fixes each at the root the same way this workspace's background agents already
  do, verifies against LIVE infra state (not just "the code looks right"), and appends any newly-discovered
  silent-failure class to the registry per its own anti-pattern rule. Modeled on `/ci-reconcile`; built from the
  2026-08-06/07 session that chased one alerting-service fix through a PagerDuty-crash dedup bug, a CONSOLIDATOR_DOWN
  refire storm, and then SEVEN separate CI/CD/IAM/deploy-pipeline bugs just to get that fix actually running live — the
  alert code being "fixed" and the fix being LIVE are different claims and must both be verified. Trigger on
  `/data-pipeline-alerts-reconcile`, "resolve the data pipeline alerts", "fix these DP alerts at the root", "why do we
  keep getting alerted about X", "check the data-pipeline-alerts channel", "reconcile the data pipeline alerts", "clear
  the DP alert backlog".
---

# /data-pipeline-alerts-reconcile — data-pipeline alert reconciliation and root-cause fix

Answers one question with evidence, then fixes what's actually broken: **is `#data-pipeline-alerts` actually quiet, and
where exactly is it not — at the root, not the symptom?** Companion to `/ci-reconcile` (same shape, different domain).
SSOT: `/codex/05-infrastructure/data-pipeline-alerts.md` (the DP-`<CATEGORY>`-`<NNN>` registry, human-readable) +
`data-pipeline-alerts.registry.yaml` (same dir, machine-readable — what the router rules actually load).

**Always auto-fixes.** Not a diagnose-and-wait skill. Ship every root-caused fix the way this workspace already does
(`quality-gates.sh` → `quickmerge.sh --agent --files`, live `gcloud`/Terraform for infra gaps per the IAM/cloud-identity
self-service rule, a registry-entry append for a newly-discovered class), then verify against live state, then report.
The findings-triage HARD RULE (in-your-file → fix in same commit; outside-plan small+clear → ≤30 min) covers the
judgment calls; escalate only a genuinely big/cross-repo/ambiguous finding per that rule.

## 0. Ground truth first — read the LIVE channel programmatically, never require a paste

**Never act on what a pasted alert says happened, and never make Slack-reading a manual copy/paste step** — a paste
doesn't scale, goes stale the moment you read it, and structurally can't be what AO (agent-orchestrator) dispatches this
skill against, since AO has no Slack access of its own and nothing can be pasted into a dispatched worker. Pull the
channel directly instead:

```bash
cd unified-trading-pm
python3 scripts/dev/slack-read-channel.py data-pipeline-alerts 24
# On a fresh macOS Python.org install this may hit SSL: CERTIFICATE_VERIFY_FAILED (missing CA bundle,
# unrelated to the Slack token/auth itself) — fix by pointing at certifi's bundle, don't skip verification:
#   SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())") python3 scripts/dev/slack-read-channel.py ...
```

This resolves `SLACK_ALERTS_READER_BOT_TOKEN` via GCP Secret Manager over `gcloud` ADC (no OAuth, no browser, never
touches disk/argv) and works identically from any identity with `secretmanager.versions.access` on that secret — an
operator's laptop, a slot worker, or (once granted) AO's own service account. **AO cannot run this skill autonomously
today** — confirm/grant AO's SA that specific IAM binding before dispatching this skill to it; until then, this is an
interactive-session-only skill, unlike `/ci-reconcile` (which needs no Slack access at all because every CI signal has a
directly-queryable `gh`/`gcloud` system of record — the data-pipeline domain has no such non-Slack equivalent for many
of these events).

The script writes raw JSON to `slack-<channel>-<hours>h.json` in the CWD (grep/re-analyze without re-fetching) and
prints a rendered timeline to stdout. **Re-run it fresh each time** — its answer has a date on it, same as any other "is
it currently broken" check in this workspace.

**Slack silence is not evidence of health — cross-check live GCP infra state as its OWN ground-truth source, not just a
follow-up to a Slack hit.** A 2026-08-07 parallel audit of Cloud Run Jobs/Services + the GCE VM fleet found 11 real,
currently-active production failures (OOM crash-loops, dead-image jobs, a 19-month-broken min-instances service, a GCS
429 storm) — a follow-up cross-reference found **zero of the 11 had ever fired a Slack alert**, and most had **no
registry rule that could have fired one even in principle** (`no-rule-exists`, not a routing bug — see classification
(f) below). Compute/infra failures (Cloud Run OOM, crash-loop, dead scheduler target, stale image) are a structurally
different domain from the DP-`*` data-pipeline events this registry covers, and today nothing bridges them. Before
concluding "the channel is quiet, nothing to do," run (or ask for the results of) an infra-health sweep alongside the
Slack read:

```bash
# Cloud Run Jobs: recent execution failures across the fleet (per-job, all regions in use)
gcloud run jobs list --project=central-element-323112 --format="table(metadata.name)" # then per-job:
gcloud run jobs executions list --job=<name> --region=<region> --project=central-element-323112 --limit=20 \
  --format="table(metadata.name,status.startTime,status.completionTime,status.conditions[0].status)"

# Cloud Run Services: traffic pinning + error-severity logs
gcloud run services list --project=central-element-323112 --format="table(metadata.name,status.traffic)"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="<name>" AND severity>=ERROR' \
  --project=central-element-323112 --freshness=24h --limit=20

# GCE VMs: preemption-without-resume, dead heartbeat while still billably RUNNING
gcloud compute instances list --project=central-element-323112 --format="table(name,zone,status,creationTimestamp)"
gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/PROGRESS.json   # last-updated vs now

# Zombie Cloud Scheduler jobs: firing at a Cloud Run Job that no longer exists (found 38 of these in one sweep)
gcloud scheduler jobs list --project=central-element-323112 --location=<region> \
  --format="table(name,schedule,state,httpTarget.uri)"   # cross-check each target against `gcloud run jobs list`
```

If this turns up something, it's classification (f) below, not (a)-(e) — don't force-fit it into the DP-registry
categories, and don't skip the fix just because it didn't come from Slack.

Then cross-check what you found against the registry and live infra state — an alert fired hours ago may already be
routine noise, self-resolved, or superseded by a downstream fix:

```bash
# The registry itself — never eyeball-classify an event, look it up
grep -A8 "event: <DP_EVENT_NAME>" codex/05-infrastructure/data-pipeline-alerts.registry.yaml

# Is this event even registered? An unregistered DP_* event falls through the router's generic
# catch-all and pages the WRONG channel (#uts-live-alerts) instead of mirroring here — this exact
# class of bug already happened twice (2026-07-27, 2026-07-31, see the codex doc's fix notes)
grep -n "'<DP_EVENT_NAME>'\|\"<DP_EVENT_NAME>\"" alerting-service/alerting_service/rules/data_pipeline_rules.py

# Live fleet-monitor state (not the log tail) — exit-code / heartbeat / meta sweeps
cd deployment-service && python -m deployment_service.data_pipeline_monitors.cli --mode meta --dry-run

# Is the thing the alert is ABOUT actually still broken right now? (examples — pick per alert)
gcloud run jobs describe <consolidator-job> --region=... --format="value(status)"
gcloud scheduler jobs describe <cron-name> --location=... --format="value(state)"
```

**Distinguish routine heartbeat noise from a real failure before reading further** — `DP_FLEET_MONITOR_RUN_STARTED`/
`_COMPLETED` (DP-DIGEST-003/004) are `⚪` INFO telemetry that should never even reach the live channel (fixed 2026-08-07
— they now carry `mirror_live=False` on their `DataPipelineAlertRule`; if you see them firing live again, that IS a
regression worth root-causing, not routine noise to skip past). Only `DP_FLEET_MONITOR_RUN_FAILED` (DP-WATCHER-003) or
an actual `DP-*` failure-mode row is work. If you don't already know which is which, check the registry's `severity` AND
`mirror_live` fields — don't infer from tone.

## 1. Classify each still-live alert before touching it

- **(a) Genuine detector-caught failure** — the registry row's own `fires:` condition is true right now (checked against
  live state per § 0, not the alert's timestamp). Fix per its own `escalation` tier (§ 2).
- **(b) Routing/dedup/alert-accuracy bug** — the alert is noise or mis-routed, not a real failure. Tells:
  - **Missing secret/capability crashes the notifier itself** — a `try`/raise on an absent SM secret (e.g. PagerDuty
    routing key) instead of a graceful capability probe + fallback. Symptom: `ALERT_DISPATCH_FAILED` spam, not the
    underlying condition. Fix: an `lru_cache`-wrapped capability probe + a documented fallback channel (email/Telegram)
    — see `alerting_service/notifiers/pagerduty.py` + `email.py` for the shipped pattern.
  - **Same condition re-fires every tick, but it's a REAL failure that should eventually stop** — the event isn't in
    `_RECURRING_ALERT_COOLDOWNS` (`alerting_service/notifiers/router.py`) or its cooldown is shorter than the detector's
    own cadence (the codex doc's wiring caveat: DP-`*` bypasses the real incident gateway and relies on this cooldown
    map as its de facto dedup layer). Fix: add/raise the event's cooldown ≥ detector cadence.
  - **Same event fires every tick BY DESIGN and is never going to stop** (routine per-sweep telemetry, not a failure) —
    a cooldown is the wrong tool here (it would still spam, just less often); the event needs to never reach the live
    channel at all. Fix: set `mirror_live=False` on its `DataPipelineAlertRule` (UAC
    `canonical/crosscutting/alerting/rules.py`) — this keeps the event registered (so it can't regress into the
    wrong-channel bug below) while the router (`route_event`'s `if dp_rule.mirror_live:` gate) skips the actual
    Slack/page dispatch but still logs `ALERT_SENT` for audit. Shipped 2026-08-07 for DP-DIGEST-003/004
    (`DP_FLEET_MONITOR_RUN_STARTED`/`_COMPLETED`) — use that commit as the pattern.
  - **Registered under the wrong registry ID** — two distinct events sharing one `DP-WATCHER-00N` id (happened twice,
    see the codex doc's 2026-07-27/07-31 fix notes) means one of them has no exact-match rule and falls through to the
    generic catch-all, paging the wrong channel entirely. Fix: assign the unregistered event its own id in BOTH the
    `.md` table and `.registry.yaml`, add its `DATA_PIPELINE_ALERT_RULES` exact-match entry.
- **(c) Self-heal actuator gap** — `escalation: auto_recover` in the registry, but the actual dispatch degraded to
  `file_issue` (check `escalation.py`'s `_ACTUATORS_AVAILABLE` probe / `_DP_RECOVERY_ACTIONS` map). Known standing gap
  (codex doc, "OPEN GAP (P1)"): `scripts/recovery/` + `scripts/vm/` are not in the deployment-api Cloud Run image, so
  `auto_recover` can never actually actuate from there — confirm whether this is that already-known gap (don't
  re-diagnose it) or a NEW actuator-resolution bug (e.g. `launcher_registry.py`'s prefix map missing an entry for the
  failing VM prefix — see § 3).
- **(d) The alert's OWN fix isn't live yet** — the code that would resolve this alert was already shipped to a repo but
  never reached the running service. **This is not a hypothetical** — it is exactly what happened chasing
  `alerting-service@4e252b4` this session: a correct code fix sat unrunning behind a provenance-marker bug, a SIT-stamp
  bug, a backmerge chicken-and-egg, a stranded self-hosted-runner pool, and two deploy-API bugs (IAM +
  Artifact-Registry-path), each masquerading as "the fix didn't work" until root-caused individually. See § 4 — this
  gets its OWN verification pass, not an assumption that a green quickmerge means the alert will stop.
- **(e) Watch-the-watchers gap** — the meta-monitor, the zombie-watchdog, the consolidator, or the deadman
  (`uts-prod-monitoring-deadman`) itself is the thing that's down (DP-WATCHER-00`N`/DP-CATALOG-001). Verify the
  watcher's OWN liveness signal directly (its GCS census-blob freshness, its Cloud Scheduler job state) — don't trust
  its own silence as "healthy," per the codex doc's "watching the watchers" section.
- **(f) Infra failure with no alerting coverage at all** — a real, currently-broken Cloud Run Job/Service or GCE VM that
  NEVER shows up in `#data-pipeline-alerts` because the failure class isn't a registered DP-`*` event at all (not a
  routing bug — there is genuinely no rule that could fire). Found this way, 2026-08-07: an OOM crash-loop, a
  10-month-stale service reading a bucket retired 4 months earlier, ~38 Cloud Scheduler jobs firing daily at deleted
  Cloud Run Jobs, and a real GCS-429 storm inside `dp-alerting-subscriber` itself. Sub-patterns worth checking by name
  (each recurred, not one-off):
  - **Dual/orphaned consumer** — two Cloud Run resources (a Service + a legacy Job, or two Jobs) independently pulling
    the SAME Pub/Sub subscription or targeting the SAME resource; one is a never-decommissioned predecessor. Tell:
    `resource.labels.job_name`/`service_name` in Cloud Logging for the SAME event shows up under a name you didn't
    expect. Grep other Cloud Run resources' env vars/args for the same subscription/topic/bucket name before assuming a
    single-consumer fix is sufficient — see `uts-prod-alerting-paging` (2026-08-07) for the template.
  - **Zombie scheduler** — a Cloud Scheduler job whose HTTP target job name no longer resolves
    (`gcloud run jobs describe <target>` → not found), still firing on schedule into a 404/NOT_FOUND void, sometimes for
    over a year. Cross-check EVERY scheduler's target against the live job list, not just the one you're chasing — this
    is a cheap, mechanical, whole-fleet check (`gcloud scheduler jobs list ... --format="table(name,httpTarget.uri)"`
    against `gcloud run jobs list`), and it tends to cluster (found 38 in one pass, not 1).
  - **Rule exists but the code doesn't use it** — the registry HAS a matching event/rule (e.g. `DP_GCS_429_THRASH`), but
    the actual failing code path routes through a DIFFERENT, generic handler (e.g. a catch-all `SERVICE_ERROR` →
    Telegram-only) instead of emitting the specific registered event. This is NOT the same bug as § 1(b)'s "registered
    under the wrong id" — here the id is right and unused, not colliding. Grep the actual `raise`/`except` site that
    produces the log line against what event name it emits, not what the registry SAYS should exist. For any (f)
    finding: fix it the normal way for its domain (Terraform/gcloud config for infra, `quality-gates.sh` →
    `quickmerge.sh --agent --files` for code), THEN treat closing the alerting gap itself as a separate, real follow-up
    — either wire a genuinely new DP-`*` event + registry entry (§ 6) if the failure class is common enough to deserve
    standing coverage, or explicitly document in the issue doc why it's NOT worth a standing alert (e.g., a one-time
    cleanup that shouldn't recur). Don't silently leave (f) findings uncovered going forward just because you fixed the
    instance you found.

## 2. Fix (a) directly, per its registry `escalation` tier

- **`auto_recover`**: the actuator should already exist (`_DP_RECOVERY_ACTIONS` in `escalation.py`) — if it's firing but
  failing, root-cause the actuator script itself (`deployment-service/scripts/recovery/*.py`); if it's not firing at
  all, that's § 1(c).
- **`file_issue`**: confirm a `plans/active/issues/<slug>_<date>.md` actually got filed with actionable frontmatter (not
  a plain non-actionable doc — check for the `assigned_vm`/`parent_epic` fields the `PlanRegenLoop` needs to pick it
  up). If the file-issue path itself silently no-op'd, that's a bug in `escalation.py::_write_issue_doc` — fix it the
  same way as any other code bug (standard `quality-gates.sh` → `quickmerge.sh --agent --files` path).
- **`page_operator`**: this tier is CRITICAL-only and protective by design — confirm the underlying condition is
  genuinely un-auto-recoverable (credential-blocked, safety-relevant) before treating the page itself as a bug to
  silence. If it's paging for something that DOES have a safe auto-recover path, that's a registry mis-classification —
  fix the `escalation:` field, not the page mechanism.

## 3. Fix (b) and (c) — the alerting-service / self-heal layer itself

Standard single-repo fix path in `alerting-service` (dedup/routing/capability-probe bugs) or `deployment-service`
(actuator/launcher-registry bugs): root-cause, fix, `bash scripts/quality-gates.sh --no-fix`,
`quickmerge.sh "fix: …" --agent --files '<paths>'`, then move to § 4 for live verification — a green quickmerge is NOT
the same claim as "the fix is running."

## 4. Fix (d) — verify the fix's OWN deploy chain, don't assume a shipped commit is a running fix

This is the step `/ci-reconcile` doesn't need and this skill does, because alerting-service fixes specifically flow
through the FULL LDR→main→Cloud-Build→Cloud-Run chain before they affect what Slack actually receives. After shipping
any alerting-service/deployment-service fix meant to change alert behavior:

```bash
# Did the fix actually reach main, not just LDR?
git -C alerting-service merge-base --is-ancestor <fix-sha> origin/main   # may be false-negative on squash — see below
# On a squash-merge, ancestry can lie — check by CONTENT instead:
git -C alerting-service show origin/main:<changed-file> | grep '<the fix's distinguishing line>'

# Did a fresh Cloud Build actually run against that content?
gcloud builds list --project=central-element-323112 --filter="substitutions._SERVICE_NAME=alerting-service" --limit=3

# Is the LIVE Cloud Run revision actually the fresh one, not a stale pin?
gcloud run services describe dp-alerting-subscriber --region=asia-northeast1 --project=central-element-323112 \
  --format="value(status.latestReadyRevisionName)"
gcloud run revisions describe <rev> --format="value(metadata.creationTimestamp,status.conditions[0].status)"
gcloud run services describe dp-alerting-subscriber --region=asia-northeast1 --project=central-element-323112 \
  --format="value(status.traffic)"   # green revision ≠ live traffic — a stray pin can freeze deploys at 0%
```

If any link in that chain is broken, treat it as its own bug (same classification/fix/verify loop as § 1-3, just in a
different repo) — do not report the alert "fixed" until the LIVE revision demonstrably carries the fix. Expect this to
occasionally surface an entire OTHER layered chase (provenance gates, SIT-stamp bugs, stranded runner pools, deploy-API
IAM/path gaps all recurred in one real session) — each layer gets its own dated issue doc
(`plans/active/issues/<slug>_<date>.md`) per findings-triage, cross-linked back to a tracking doc, same pattern
`/ci-reconcile` uses for a fleet-wide template rollout.

## 5. Verify — re-sweep, don't declare victory on the alert you started with

Re-run § 0's ground-truth checks. For a routing/dedup fix, confirm the SAME condition (re-triggered live if safe to do
so, e.g. by re-firing the actual dispatch event) now routes/dedupes correctly. For an auto-recover actuator fix, confirm
a real trigger actually invokes it end-to-end (not just that the code compiles). For a deploy-chain fix (§ 4), confirm
via the live revision check above — this is the same "runtime verification, never done without running the code" HARD
RULE as everywhere else in this workspace.

## 6. Registry hygiene — append, don't let a new class go unmonitored

**Every genuinely new silent-failure class gets an entry in BOTH `data-pipeline-alerts.md`'s table AND
`.registry.yaml`** before this pass is done — this is the codex doc's own explicit anti-pattern rule ("a new
silent-failure class fixed as a point-bug without an `append` to this registry ... recurs unmonitored"). Assign the next
`DP-<CATEGORY>-<NNN>` id in sequence for that category; never reuse or collide with an existing id (the exact bug class
fixed twice already, 2026-07-27/07-31). If the fix changes a failure mode's lifecycle status (verbose → baselined →
zeroed per the "million → zero" discipline), update the `Status` column too.

## 7. Report

For each alert/class handled: registry id + classification (§ 1's letter), evidence (log/Slack excerpt, live-state check
output), root cause, what was shipped (repo + sha, or registry diff), and post-fix live verification. Explicitly call
out: (1) any alert that was already stale/routine-noise/self-resolved by the time you looked, (2) any deploy-chain bug
found under § 4 and its own fix, (3) any registry entries appended, (4) anything that could NOT be resolved this pass —
file it per findings-triage, never leave it as an unlogged "still broken."

## Under `/autonomous`

**Completion criterion (operator ruling, 2026-08-07): 60 consecutive minutes with ZERO new alerts that are not
auto-resolved within that same 60-minute window.** Not "the channel looks empty right now" — a single quiet snapshot
proves nothing (this is the same "is it actually running" discipline as everywhere else in this workspace). Track it as
a rolling clock: every time a genuinely NEW alert appears (not a repeat/dup of one already handled) and it does NOT
auto-resolve inside the same 60-minute window, the clock resets to zero from that alert's timestamp. Re-run § 0's
ground-truth sweep (Slack + the infra-health cross-check) periodically to advance the clock — don't just poll Slack in a
tight loop; space checks sensibly (e.g. every 10-15 min) and let the harness's own notification/wakeup mechanism carry
you between checks rather than busy-waiting.

**Don't idle through a quiet window if there's already visible work** — if § 0's sweep finds live alerts or infra
findings RIGHT NOW, audit and fix them immediately (parallel sub-agents per independent finding, same pattern as § 2-4)
rather than waiting out a passive timer first. The 60-minute clock is the STOP condition, not a reason to delay
starting. Only once you've worked through everything currently visible does "wait and watch the clock" become the
correct mode.

After the channel-wide sweep clears and § 4's deploy-chain verification confirms every fix is actually live, don't stop
at the first quiet moment — hold for the full 60-minute window, re-sweeping periodically (a routing/dedup fix can look
correct and still not survive the next real trigger, and an infra fix (f) can regress on the next deploy). This is still
on-demand reconciliation bounded by the 60-minute stability check, not a permanent standing watcher — continuous
monitoring past that point is the fleet-monitor/deadman's job, not this skill's.

**Promotion-chain check (§ 4) gotcha**: never `gh workflow run ldr-to-main-promote-fleet.yml` yourself to check whether
a fix promoted — it's a shared, single-concurrency-slot workflow, and ad-hoc dispatches from multiple concurrent
agents/sessions checking their own promotion starve it (measured 2+ hour livelock, 2026-08-07,
`plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`). Read
`scripts/cicd/promotion_lag_monitor.py`'s live output or `gh pr list --search "chore(promote)"` instead — never dispatch
the shared promoter just to poll it.

## What this skill does NOT do

Does not silence a persistent alert instead of fixing its root cause (the alert IS the work item — the codex doc's
"million → zero" discipline). Does not treat a green `quickmerge` as proof the alert will stop (§ 4 is mandatory for any
alerting-service/deployment-service change). Does not build the known "actuators not in the deploy image" gap's full fix
speculatively — confirm it's actually blocking THIS alert's auto-recovery before touching image packaging, and if it is,
that's a real, separately-scoped infra fix, not a quick patch. Does not page or silence a `page_operator` tier alert to
make the channel quiet — that tier exists because the condition genuinely needs a human. Codex SSOTs this skill leans
on: `/codex/05-infrastructure/data-pipeline-alerts.md`, `.registry.yaml` (same dir),
`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/05-infrastructure/deployment-observability.md`.
