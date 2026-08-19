---
doc_type: codex-runbook
title: CI/CD daily health log
summary:
  "Dated, append-only log of the daily /ci-reconcile habit — persistent (non-auto-resolving) alerts, GH Actions spend +
  self-hosting migration candidates, and CI VM resource health, one entry per run with a delta-since-last-run line so
  the operator can scan for what changed without re-deriving state from scratch. Written by /ci-reconcile itself when
  run in daily-report mode (SKILL.md §7b) — never hand-edit past entries, append a new dated ## section instead."
status: current
nature: process
asset_group: [cross-cutting, ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [runbook, ci-reconcile, ci-cd, billing, self-hosted, vm-health, daily]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/ci-alerting.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
created: "2026-08-18"
authoritative_for: [
    daily CI/CD fleet health tracking — persistent alerts,
    GH Actions spend,
    self-hosting migration status,
    CI VM
    resource health,
  ]
referenced_by: []
owner: operator (daily, human-run)
cadence: daily
verifier:
  "a new dated ## section exists for today with all four subsections populated (persistent alerts / ci-reconcile ran /
  spend / VM health) and a delta line against the prior entry"
last_executed: "2026-08-19"
code_refs:
  [cursor-configs/skills/ci-reconcile/SKILL.md, scripts/generate-workflow-catalog.py, scripts/dev/slack-read-channel.py]
audience: operator / dev
last_updated: "2026-08-19"
execution:
  {
    owner: "operator (daily, human-run)",
    cadence: "daily",
    verifier:
      "a new dated ## section exists for today with all four subsections populated (persistent alerts / ci-reconcile
      ran / spend / VM health) and a delta line against the prior entry",
    last_executed: "2026-08-19",
  }
---

# CI/CD daily health log

Append-only. One `## <date>` section per day `/ci-reconcile` runs in daily-report mode. Read the PREVIOUS entry before
running, diff key figures into a **Delta since last run** line at the top of the new one. Never edit a past entry — if
something reported that day turns out wrong, correct it in the NEXT entry, not retroactively.

## 2026-08-18

**Delta since last run**: n/a — first entry.

- **Persistent alerts (non-auto-resolving)**: none. Two real incidents overnight (5 Dockerfile digest-pin conflicts
  across execution-service/features-service/instruments-service; a lag-monitor ETag staleness bug) — both root-caused
  and fixed same-session, confirmed landed.
- **ci-reconcile ran**: yes (this session, ad-hoc — not yet on a standing daily timer).
- **GH Actions spend**: real numbers pulled from `deployment-api`'s `/api/costs/breakdown` (GitHub Enhanced Billing,
  Plan-scoped token via GSM — `gh api .../settings/billing/actions` 404's on an ordinary token, this is the correct
  source, see §8's updated recipe). Last 10 days, net USD/day after credit: 08-09 $6.56 · 08-10 $6.64 · 08-11 $2.76 ·
  08-12 $3.63 · 08-13 $3.80 · 08-14 $16.01 · 08-15 $40.88 · 08-16 $21.59 · 08-17 $10.09 (operator's "quiet day"
  reference point — matches exactly) · 08-18 $0.08 so far (partial, provisional). 10-day total $112.03, avg
  ~$11.20/day, but swings 15x (\$2.76–\$40.88) tracking commit/promote velocity directly — 08-15's spike lines up with
  the heaviest promote-PR churn window this session. Consistent gross→net discount of 70-90% (a prepaid/included
  allowance draining faster on busy days). Structural finding unchanged: the expensive per-push test/typecheck/lint
  work is ALREADY on the self-hosted glue-runner pool (`[self-hosted, glue]`) on every private repo checked
  (execution-service, features-service, instruments-service, market-tick-data-service, strategy-service,
  deployment-service). `unified-trading-pm` itself (source of most high-frequency `*/15`–`*/30` scheduled monitors)
  is PUBLIC — those cost nothing regardless of cadence. Remaining GH-hosted jobs per private repo
  (`notify-slack.yml`, `plan-alignment-agent.yml`, `version-registry-notify.yml`, `publish-package.yml`,
  `image-build-gate.yml`'s dispatch/poll legs, a few repo-specific ones) are individually lightweight — no single
  obviously-misplaced expensive workflow found. The day-by-day spend swing confirms the real driver is commit/promote
  _volume_, not runner placement — a quiet day already costs ~$3-7, a heavy one $20-40+ regardless of what's
  self-hosted.
- **CI VM resource health** (`i-042a6332509482556`, `m8i.2xlarge`, 8 vCPU/32GB, glue-runner pool): 24h sample (17,277
  points) — CPU avg 13.3%/max 99.9%, load-avg-1m avg 1.3/max 15.2 (real oversubscription at peak, ~1.9x core count),
  iowait avg 0.8%/max 44.1%, swap avg 0.5%/max 9.5%. Verdict: correctly sized, not over-provisioned — the low average
  masks genuine burst demand that would get worse on a smaller box. No watchdog alerts fired in 24h. Not a finding.

## 2026-08-18 (second pass, agt-d23e6a, scheduled hourly sweep)

**Delta since last run**: new persistent alert found (PM promote-PR corpus-ratchet block) and partially fixed;
2 transient CRITICAL alerts confirmed self-healed; spend/VM health not re-run this pass (unchanged from above).

- **Persistent alerts (non-auto-resolving)**: `unified-trading-pm`'s `checks` QG slice was blocking every LDR→main
  promote PR (#3457, #3459, #3460, #3461 — visible live in `GET /api/escalations/active` as a chain of
  `promote_qg_failure` escalations) on 3 unrelated hard-fail ratchets: (1) `check_reference_paths` existence 35 vs
  baseline 34 — root cause: `plans/active/issues/ag_closeout_audit_ci_parked_2026_08_16.md` cited a target doc that
  had since been archived (active→archive move, stale path never updated) — **fixed**, repointed to
  `/plans/archive/issues/...`; (2) `check_ag_closeout_linkage` 1 orphan — `defi_perp_daily_ctx_hl_forward_gap_since_
2026_06_02_2026_08_04_finalize_2026_08_08.md` had no body-mention in `defi_consolidated_closeout_2026_07_18.md` —
  **fixed**, citation added (had to trim the addition to stay under the 1000-line hard cap, doc was already at 997L);
  (3) `check_artefact_disclosure` 6 hard hits of the banned client name in `strategy-service-deep-dive.html` — **left
  alone**, already an open P0 todo in the actively-dispatched `plans/active/client_artefact_remediation_siblings_
2026_08_18.md` (line 68, `sequential: true`), fixing it here would risk colliding with that plan's in-flight work.
  Shipped `unified-trading-pm@8f916bd82f`, verified on origin; (1) and (2) confirmed clear locally post-fix. The
  promote PR will still show red until the sibling plan's ClearLoop redaction lands — expected, not a new gap.
- **Self-healed, confirmed via current green state**: `agent-orchestrator` QG-slice cancel/timeout (20:06Z);
  `trading-agent-service`/`market-tick-data-service`/`ml-service`/`unified-trading-library` QG-slice failures
  (21:07-21:15Z, all same-SHA retry-succeeded at 22:05Z — transient runner flake, no code fix needed, no open
  promote PRs on any of the 4); `deployment-service` main-branch FAILING→FEATURE_GREEN (ci-status-update, 22:09Z);
  Cloud Run traffic-pin on `signal-broadcast-smoke-receiver` (19:12Z) — live `gcloud run services describe` shows
  100% traffic on the latest revision, not pinned. No Slack RECOVERED post found for the traffic-pin specifically
  (asymmetric-alerting gap, § 0d) — worth a one-line note, not a new incident.
- **Coverage gap**: could not verify `glue-runner-crash-loop-watchdog`'s 20:01Z CRITICAL (`github-glue-runner-
unified-api-contracts@glue-1.service`, "10.2h active, current job's own start time not resolvable") via live SSM —
  `ikenna-worker` AWS identity lacks `ssm:SendCommand` on `i-042a6332509482556` and isn't one of the two ambient
  self-service identities this workspace's IAM self-grant rule covers, so no self-grant attempted. Indirect check:
  `unified-api-contracts`'s own GH Actions history shows zero in-progress runs and clean `success` completions both
  before and after 20:01Z — no evidence of an actually-hung job, consistent with the known `unit_active_seconds`
  false-positive class this skill already documents (the alert's own "current job's own start time not resolvable"
  phrase matches that failure mode exactly). Likely false alarm, not confirmed — flagging the SSM access gap itself
  as worth a fix (a read-only `ssm:SendCommand`/`ssm:GetCommandInvocation` grant scoped to this instance would let
  `/ci-reconcile` verify this class directly instead of inferring from GH Actions data).
- **ci-reconcile ran**: yes (second pass this UTC day, scheduled dispatch agt-d23e6a).
- **GH Actions spend**: not re-pulled this pass — see the first entry above, unchanged.
- **CI VM resource health**: not re-run this pass — see the first entry above, unchanged.

## 2026-08-19 (ad-hoc, interactive session)

**Delta since last run**: 3 genuine CI failures found and root-caused (vs. 0 open in the 08-18 second-pass entry) —
`deployment-service` and `unified-trading-pm` both red on `live-defi-rollout`, plus a mid-history provenance-gate
bypass discovered during the sweep's own verification pass, not present in the prior entry.

- **Persistent alerts (non-auto-resolving)**: none remaining — the original three plus one bypass found later in this
  same pass (item 4) are all fixed + verified below.
  1. **deployment-service `live-defi-rollout` red** (class b, genuine code regression, compounded by class g).
     `47cddc0b` (Phase-3 migration-script relocation from instruments-service/market-tick-data-service) landed with
     STEP 5.95 TID251 violations (`vm_log_archival_cron.py`/`vm_serial_capture_cron.py` importing
     `google.cloud.compute_v1` directly) — fail-fast meant STEP 5.101 (empty-string-fallback, 3 more sites in the
     SAME relocated migration scripts) never even got reached until the first fix cleared it. Root-caused: routed
     both cron scripts through UTL's already-existing `get_compute_engine_client().aggregated_list_instances()` +
     `.get_serial_port_output()` (exact pattern already established in `deployment_service/vm/gcp_instance_lister.py`
     — no wrapper needed to be invented), updated the 4 unit tests that mocked the old `compute_v1.InstancesClient`
     interface, and added justified `# noqa: qg-empty-fallback` to the 3 pre-existing migration-script sites (all
     genuinely benign — diagnostic markdown tables / GCS path segment building / DataFrame column-absence handling).
     Shipped `deployment-service@15b9c234`. Verified: local QG green, manually-dispatched `quality-gates-v2` on the
     exact sha → `success`, promote PR #1077 all-green.
  2. **unified-trading-pm `live-defi-rollout` red** (class b). `plans/active/ui_consolidated_closeout_2026_07_30.md`'s
     `related:` frontmatter cited an archived plan directly (`archive-safety-ratchet`, operator ruling 2026-08-17).
     The archived tracker's durable fact (6 deployment-ui observability workstreams, all split+shipped 2026-07-20→28)
     had no codex home — added a short entry to `plans/epics/observability_master.md`'s "Archived plans" section
     (mirroring its own existing pattern) and repointed the citation there. Shipped `unified-trading-pm@019c5544b6`.
  3. **`check_reference_paths` (existence) corpus-wide ratchet, 36 > baseline 34** — surfaced only because this pass
     manually dispatched a fresh `quality-gates-v2` run to verify (1)/(2) landed clean; NOT caused by either fix.
     Two concurrent-peer-introduced dangling refs: `ao_open_work_consolidated_tracker_2026_08_14.md:413` still cited
     a since-archived plan's pre-archival `/plans/active/issues/...` path (4-day-old debt, `slot-1`); and
     `migration_script_canonicalization_into_deployment_service_2026_08_18.md`'s own Phase-4 todo #1 claimed **DONE
     (2026-08-19)** "authored the `05-infrastructure` doc `migration-script-ssot.md`" — verified via `find` + `git log
--all` that the file has NEVER existed in this repo's history, and `script-homes.md` (its claimed cross-ref
     target) carries zero mention of it. A **false-progress finding** (todo #2 on the same plan, correcting
     `script-homes.md` item 4, is ALSO falsely claimed DONE — same pattern, not independently CI-blocking so left
     alone) — added a dated `> 🟡 [CORRECTION 2026-08-19]` banner re-opening the claim rather than silently
     rewriting or fabricating the missing doc (the plan's own "5-cluster operation-shape breakdown" / blocker-class
     specifics are real domain knowledge this session doesn't independently have). Also found + fixed in the same
     pass: an unrelated `ao_open_work_consolidated_tracker` `related:` block carrying 5 archived-plan citations
     (archive-safety-ratchet, tripped only because editing item #1 above put the whole file through `--only` mode) —
     dropped, since `ao_consolidated_closeout_2026_08_12.md` + 2 codex architecture docs already in the same list
     serve as the living pointers. Shipped `unified-trading-pm@dc8725be07` (3rd attempt — first two failed: isolated
     mode couldn't resolve `<repo>@<sha>` commit-evidence citations against sibling repos it doesn't have cloned
     alongside it in `/tmp/`, non-isolated mode then hit the 1000-line hard cap exactly at the edge, both real
     findings in their own right, not content bugs). Verified: `check_reference_paths` 34/34 locally + on origin,
     manually-dispatched `quality-gates-v2` on the shipped sha → `success`, fresh promote PR #3477 all-green.
  4. **Provenance-gate bypass** (`6817d944ec`, `feat(readiness-state-dump): extend to full surface x mode matrix`) —
     found during the final Slack re-poll (§6), not part of the original 3. Single commit, `[slot-6·laptop]` normal
     identity, feature work on skill scripts, no destructive/secret content — reprovenanced directly per §4's
     size/authorship gate. `scripts/cicd/reprovenance_bypass.sh 6817d944ec... --push` → `unified-trading-pm@9153539112`.
     Verified: `check_strict_quickmerge.py` clean.
- **Self-healed, confirmed via current green state**: `agent-orchestrator` + a second `deployment-service` QG-slice
  CANCELLED/TIMED-OUT (both ~04:15Z, ordinary concurrency-cancellation under the session's own high push velocity —
  both shas independently confirmed `success` on re-check); `unified-trading-pm` promote PR #3470 FAILED (03:26Z,
  predates this session, same archive-safety-ratchet class as finding 2); `branch-health` PROMOTION LAG WARNING
  citing stale promote PR #3473 (04:17Z) — self-resolved the moment #3477 was cut from the post-fix LDR tip.
- **Coverage confirmed** (not a gap this pass — the 08-17/08-18 SA-key access issue self-resolved, `gcloud auth
list` on this host shows the pinned `unified-trading-sa` key active): all 24 non-PM repos in the fleet registry
  swept clean (`success`); all 24 catalog-derived schedule+Slack standing monitors swept, all green with verified
  OUTCOME not just conclusion (`reconcile-release-tags`: 0 stalled; `sit-gate-stuck-detector`: 0 streaks); both
  host-dispatched watchdogs (`glue-runner-crash-loop-watchdog`, `ci-vm-resource-watchdog`) confirmed live via SSM
  journal, both genuinely healthy (0/16 glue-runners crash-looping, no box-down risk signal); final Slack re-poll
  immediately before writing this entry showed zero new alerts beyond what's covered above.
- **ci-reconcile ran**: yes (ad-hoc interactive session, not the scheduled dispatch).
- **GH Actions spend**: not re-pulled this pass — out of scope for a narrow alert-driven sweep, see 08-18 entry.
- **CI VM resource health**: not re-run this pass — see 08-18 entry; `ci-vm-resource-watchdog`'s own hourly tick
  (checked live above) shows no sustained pressure on the known CI/glue-runner host.

## 2026-08-19 (second pass, fleet-wide QG cascade recurrence)

**Trigger**: operator pasted 9 raw `#ci-failures` CRITICAL alerts (2026-08-18 evening) and asked whether these meant
agents were pushing without running QG. They were not — root cause is a recurrence of the shared-PM-validator single
point of failure first documented in
`plans/archive/2026_08/issues/fleet_wide_qg_cascade_pm_manifest_race_plus_silent_webhook_gap_2026_08_18.md`
(2026-08-18 morning incident, 13 repos, fixed via `unified-trading-pm@176ff63dab` — one retry: `pull --ff-only` +
`sleep 5`).

**What happened this time**: 7 repos (deployment-service, ml-service, trading-agent-service, strategy-service,
instruments-service, unified-trading-library, market-tick-data-service) failed within a ~20:33-21:14 UTC window, all
`uts-backmerge-bot` merge commits, 6 of 7 sharing the identical `"Production readiness validators FAILED (persisted
after re-pull + retry)"` signature — meaning the 08-18 fix's one retry ran and still wasn't enough. Every alerted
commit's own code was confirmed clean (current HEAD green on all 9 originally-alerted repos, before and after this
fix).

**New evidence beyond the archived doc**: bisected the exact PM commit (`304f95484`) that was `live-defi-rollout`
HEAD at both confirmed failure timestamps (instruments-service 21:13:20Z, strategy-service 21:14:15Z — same commit,
confirmed no other PM commit landed in that window) and replayed the identical CI-invoked validator script against
it in an isolated `git worktree`: clean pass. This rules out "PM content was transiently invalid" as the mechanism
for THIS occurrence (unlike the 08-18 incident, where that genuinely was the cause) — pointing instead at a
stale/dirty local PM clone surviving between jobs on the `[self-hosted, glue]` runners, which a soft `pull
--ff-only` doesn't reliably correct. **Not independently confirmed** (no runner-host filesystem access from this
session) — flagged as an open question with a P3 operator-owned follow-up todo.

**Fix shipped**: hardened the retry in `scripts/quality-gates-base/base-service.sh` + `base-library.sh` — force
`fetch` + `reset --hard origin/live-defi-rollout` + `clean -fdx` (instead of soft `pull --ff-only`), with 2 retries
(5s, 10s backoff) instead of 1. Safe regardless of the exact mechanism, since PM's CI-side clone is a disposable
dependency checkout. `bash -n` clean on both files.

Full writeup, evidence, and todos:
`plans/active/issues/fleet_wide_qg_cascade_pm_manifest_race_recurrence_2026_08_19.md`.

**Correction (found after the above was written)**: this is the SAME incident (identical 9 shas) already
independently investigated and archived same-day as
`pm_corpus_dangling_link_cascade_during_active_reconcile_sweep_2026_08_18` — a pre-task plan/issue-conflict-check
miss on my part. That doc has direct raw-log evidence (2 of 9 repos) of a genuinely persistent (~20-40min)
`plans/active/*.md` dangling-link break during concurrent `/plan-reconcile` sweeps, not an instant race — no retry
window shipped here claims to span that; the "runner-workspace-staleness" hypothesis above is now secondary, not
primary. Full reconciliation of both docs' evidence is in the issue doc's "Correction" section. Also shipped this
pass, at operator request: reordered `[6/6] PRODUCTION READINESS VALIDATORS` to run FIRST as `[0.5/6]` (right after
`[0/6] ENVIRONMENT`, before the repo's own lint/type-check/test/codex-compliance steps) in both base-service.sh and
base-library.sh — a pure fail-fast win independent of root cause, since the section only needs PM's already-cloned
checkout.

- **ci-reconcile ran**: yes (ad-hoc interactive session, continuation of the same-day sweep above).
- **GH Actions spend / CI VM resource health**: not re-pulled this pass — narrow recurrence-investigation scope, see
  08-18 entry for the last full check.

## 2026-08-19 (third pass, agt-bbf1cc, scheduled hourly sweep)

**Delta since last run**: fleet fully recovered from the second-pass QG-cascade recurrence — no new occurrences of the
`base-service.sh`/`base-library.sh` hardened-retry path being exercised found in this window. All items below were
already self-healed by the time this pass looked; nothing needed shipping.

**Sweep 1 (repo registry, `quality-gates-v2` on `live-defi-rollout`)**: all 25 repos in `workspace-manifest.json`
green on their latest run. `unified-trading-ci` correctly has zero direct `python-quality-gates-v2` runs — confirmed
by reading its own header comment: it hosts the _reusable_ workflow definition every other Python repo's
`quality-gates-v2.yml` calls via `uses:`, not a caller itself; its own CI is `lint.yml` (green). Not a gap.

**Sweep 2 (GH-Actions-native standing monitors, regenerated catalog)**: all ~23 `schedule(...)`+Slack workflows
checked directly (`branch-health`, `ci-health`, `ldr-ci-monitor`, `ldr-docs-gate`, `ldr-to-main-promote-fleet`,
`codex-freshness-sweep`, `cloud-build-failure-watcher`, `freeze-deferred-build-replay`, `readiness-verifier`,
`sit-debounce-trigger`, `reconcile-release-tags`, `cassette-drift-check`, `removed-symbols-workspace-sweep`,
`ruleset-drift-alert`, `secret-health-check`, `build-smoke-all-repos`, `cold-storage-cleanup`,
`fix-approval-timeout`, `overnight-agent-orchestrator`, `overnight-dead-man-switch`,
`promote-fleet-startup-failure-monitor`, `sit-gate-stuck-detector`, `stale-build-watcher`,
`version-coherence-check`) — every one's most recent run is `success`, on cadence.

**Sweep 3 (host-dispatched watchdogs, `i-042a6332509482556`)**: `glue-runner-crash-loop-watchdog.sh` +
`ci-vm-resource-watchdog.sh` enumerated via `grep repository_dispatch scripts/self-hosted-runners/*.sh`. Direct SSM
verification still structurally unavailable — confirmed the exact same `AccessDeniedException` for
`arn:...:user/ikenna-worker` (not the orchestrator's self-service `uts-orchestrator-epic-role`) already filed in
`plans/active/issues/ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md` — still open, still accurate, no
new diagnosis needed. Fallback indirect check: zero `glue-runner-health`/`ci-vm-resource-alert` `repository_dispatch`
events into `ci-health.yml` in the last 24h (only unrelated `ci-failure-alert` dispatches) — consistent with quiet,
**not independently confirmed** per the known coverage gap.

**Persistent alerts (non-auto-resolving)**: none. Everything found in the last-6h `#ci-failures` pull had already
cleared by inspection time: `unified-trading-pm` `ldr-docs-gate` frontmatter violation (09:10Z, on 2 same-day issue
docs) — frontmatter already complete, gate green again by 10:07Z; 4 separate `unified-trading-pm`
`python-quality-gates-v2` CRITICALs (04:23/07:26/08:52/09:24Z push+promote-PR) and 2 `agent-orchestrator` QG
CANCELLED/TIMED-OUT (06:10/08:11Z) — current HEAD green on both repos; `market-data-processing-service` RED→GREEN
and `deployment-service` `semver-agent` FAILED→RECOVERED — both have an explicit Slack recovery post (§0d
requirement met); `unified-api-contracts` v0.142.0 dependency-fanout HALT (no v-tag) — tag confirmed present now,
`update-repo-version` succeeded 09:02Z; `deployment-api`/`deployment-service` auto-merge ARM FAILED (09:02Z) — both
merged minutes later (PR #695, #1084) via the fleet bot's own retry, verified by actual merge outcome per §0d/(h),
not just conclusion. One item still **in progress, not stuck**: `agent-orchestrator` LDR→main promotion lag (14
commits, oldest ~331h) now has an open, clean/mergeable PR #821 (opened 10:09:42Z) with `auto_merge` not yet armed as
of 10:21Z — within the `*/15` fleet-promote cadence, no ARM FAILED alert fired for it, so treated as in-cadence
rather than a repeat of the deployment-api/-service pattern; re-check next pass if still unarmed.

**Sweep 4 (open promote PRs on repos touched)**: no fix shipped this pass, so N/A by the skill's own trigger — spot-
swept anyway: zero non-`CLEAN` open promote PRs found fleet-wide.

**Other observed, out of `/ci-reconcile` scope**: `codex-freshness-sweep` (06:12Z) flagged 4 codex docs >90d stale
(`defi-venue-protocol-catalogue.md`, `service-contract-audit-template.md`, `ui-architecture.md`,
`11-project-management/README.md`) — a docs-content review, not a CI/CD pipeline defect; left for `/docs-reconcile`
or the doc owners rather than fixed here.

- **ci-reconcile ran**: yes (scheduled hourly `ci_reconciler` dispatch, `agt-bbf1cc`, slot 28).
- **GH Actions spend / CI VM resource health**: not re-pulled this pass — narrow hourly-cadence scope; no rightsizing
  check has run against `i-042a6332509482556` in >24h per §9's own trigger, which is itself worth a future daily-mode
  pass rather than this one.
