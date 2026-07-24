---
title:
  "Slack/orchestrator alert triage (2026-06-20) — alerts vs open PM plans; paper-trading channel split; 2 net-new gaps"
created: 2026-06-20
parent_epic: orchestrator_master
assigned_vm: harsh_pc
status: superseded
priority: P2
locked_by: live-defi-rollout
source:
  - 2026-06-20 operator paste — ci-failures + agent-orchestrator-alerts Slack dump
  - 3 Explore sub-agents (slot-3) — alert↔plan cross-reference + Slack-routing map
---

# Slack / agent-orchestrator alert triage (2026-06-20)

## What I found — every live alert theme mapped to its tracking plan (open vs done)

| Alert (channel)                                                                                   | Tracking plan / issue                                                                                                                                                                                   | Status                                                                              | Action                                                                                                    |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Worker heartbeat loop dead — slots 1/4/5/6, every ~10–15 min                                      | `alert_quality_overhaul_2026_06_18.md` (dedup→disk SHIPPED)                                                                                                                                             | TRACKED; **the absurd idle-minute values (5711, 1515) are a NET-NEW UNTRACKED BUG** | NEW todo ↓                                                                                                |
| Spawn failure — branch-state quarantine (slot 6, unified-trading-pm diverged, FM5/FM7)            | `alert_quality_overhaul_2026_06_18.md` Phase 3 (alert SHIPPED)                                                                                                                                          | TRACKED alert; **no auto-recovery (quarantine never auto-clears) = gap**            | NEW todo ↓                                                                                                |
| Context-burn suspected (slot 1, flag-only)                                                        | `alert_quality_overhaul_2026_06_18.md` Phase 3                                                                                                                                                          | TRACKED; flag-only BY DESIGN (kill gated off)                                       | none — expected                                                                                           |
| Orphan ping(s) detected (2)                                                                       | `issue_docs_remediation_sweep_2026_06_02.md` + `codex/11-project-management/plan-hygiene.md`                                                                                                            | TRACKED; process discipline                                                         | slot-1/harsh clear within cycle                                                                           |
| Slot N unpushed plan(s) (citadel…, master…)                                                       | `fleet_git_health_orchestrator_2026_06_10.md`                                                                                                                                                           | TRACKED; transient (Commit+Push+Flip)                                               | slot owner pushes                                                                                         |
| QG slice FAILED — market-tick-data-service PR#260 LDR→staging                                     | (live code failure, not a plan gap)                                                                                                                                                                     | OPEN — genuine red                                                                  | fix the failing test/code now (like execution-service 2026-06-17)                                         |
| promotion-lag-monitor — 24 branch-pairs un-propagated (ages to 7305m)                             | `issues/staging_to_main_promotion_starvation_2026_06_19.md` + `cicd_promotion_pipeline_2026_06_18.md` Bug#11 (P0) + `promotion_queue_conflict_wall_pileup_2026_06_17.md` (squash-noise P1s)             | TRACKED — but the **P0 root-cause fixes are OPEN**                                  | drive the open P0/P1 promote-flow todos; large age = commit-count noise + the 2 unfixed structural causes |
| plan-health doc-drift (5) + contradictions (6) — stale `tab/<op>/N` refs, IggyIkenna→OdumResearch | `cicd_quality_gates_2026_06_18.md` (AO worker.md/boot-prompt rewrite, P2) + `org_migration_to_odumresearch_2026_06_07.md` (Phase 5 sweep) + `issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md` | TRACKED; OPEN P2–P3                                                                 | unblock the Path-B AO doc rewrites                                                                        |
| **Paper-trading — "trades to do now"** (mis-routed to agent-orchestrator-alerts)                  | — none —                                                                                                                                                                                                | NET-NEW                                                                             | route to `#paper-trading-alerts` ↓                                                                        |

**Headline:** almost every alert is ALREADY tracked. The promotion-lag (P0 Bug#11 + the squash-noise/staging-merge-base
structural P1s) is the biggest open theme and is the same un-done work from 2026-06-17/19 — not new. Three things are
genuinely net-new and captured below.

## Net-new todos (the gaps the alerts surfaced)

- [x] ✅ [BUG] P2. **WorkerLivenessWatchdog bogus idle-minute calc** ("idle for 5711min"). **DONE** — G3c clamps the
      silence anchor to the CURRENT live session's age: `health.py` + the watchdog `max(...)` the heartbeat anchor with
      `session_created_at(tmux_session)` (a true lower bound), so a just-respawned worker no longer inherits a
      predecessor's ancient `last_spawned_at`/`last_ping`. — agent-orchestrator@68d27b5 ("no more 'idle for 5711min'").
- [x] ✅ [INFRA] P2. **Quarantined-slot auto-recovery** — a slot stuck in "branch-state quarantine" is now bounded
      auto-healed, not just alerted. **DONE** — `heal_dead_slot_branch_quarantine` (wired into `_do_spawn`) PRESERVES
      every commit not on `origin/<base>` to a durable `wip-preserve/...` ref FIRST, then realigns HEAD via
      `git checkout -B <base> origin/<base>` (a CHECKOUT, not `reset --hard` — audit-reflog-quiet), ONLY for a
      provably-DEAD slot (never stomps a live peer). — agent-orchestrator@8d728a8. **Verified live 2026-06-21**: after
      the central VM restart loaded the wiring, it auto-realigned slot-1's `strategy-service`
      (`wrong_branch →     live-defi-rollout`) with no human intervention. Composes with the orphan-wip realign
      root-cause fix (agent-orchestrator@9a09c42, `orchestrator_self_healing_hardening_2026_06_21.md`).
- [x] ✅ [INFRA] P2. **Split paper-trading "trades to do now" alerts into `#paper-trading-alerts`.** **DONE + VERIFIED
      2026-06-21.** PRODUCER LOCATED: the `⚡ Paper-trading — trades to do now` digest is emitted by `slack_alert()` in
      **`e2e-testing/scripts/paper_trading/paper_engine.py`**, which runs as the **GCP Cloud Run job
      `paper-trading-engine`** (`central-element-323112` / `asia-northeast1`, triggered by the daily
      `uts-prod-paper-engine-run-cron` 02:00 UTC) — NOT in any slot clone / central VM, which is why the 2026-06-20
      source search came up empty (it's a containerized Cloud Run job). The live job's `SLACK_WEBHOOK` is bound to the
      dedicated `agent-orchestrator-paper-trading-slack-webhook` secret (deploy reroute in `_engine_docker/deploy.sh` is
      the live revision, gen 11), so the digest now posts to `#paper-trading-alerts`, not `#agent-orchestrator-alerts`.
      The sibling `paper-signal-engine` 15-min job carries only `DB_API_KEY` (no Slack), so it is not a second producer.
      Verified end-to-end: secret value is a valid `hooks.slack.com` incoming-webhook; a labeled routing-test POST to it
      returned HTTP 200 (delivered to the channel). **Target:** Cloud Run job `paper-trading-engine` (already wired) —
      no code change needed; e2e-testing@21db7fa carries the rerouted deploy script.

## Paper-trading channel split — operator Slack setup (the answer to "what do I need to do")

**Slack reality:** a Slack-app **incoming webhook is bound to ONE channel at creation** — the `channel` field in the
payload is IGNORED for modern app webhooks. So you **cannot** "reuse the same webhook URL but a different channel." You
reuse the same Slack **app + the same backend notify code**, but you need a **separate webhook URL** for the new channel
(the current alerts post via a webhook URL env `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` / SM
`alerting-uts-live-alerts-slack-webhook`).

**Operator steps:**

1. Slack → the app that already posts to `#agent-orchestrator-alerts` → **Incoming Webhooks** → **Add New Webhook to
   Workspace** → pick **`#paper-trading-alerts`** → copy the new URL (`https://hooks.slack.com/services/T…/B…/…`).
2. Hand me the URL (or store it yourself) → I put it in Secret Manager as
   **`agent-orchestrator-paper-trading-slack-webhook`**.
3. I point ONLY the paper-trading "trades to do now" emitter at that webhook (the other agent-orchestrator alerts stay
   on the existing webhook/channel). One-line routing change once the emitter is located.

**Alternative (no new webhook):** if the backend is switched to a Slack **bot token** (`chat.postMessage` with a
`channel` param) the bot can post to any channel it's invited to — then you'd just `/invite` the bot to
`#paper-trading-alerts`. But today it's webhook-based, so the new-webhook path above is the route.

**✅ DONE 2026-06-20 — `papertrading-alerts` Slack app created + all creds stored in GCP Secret Manager**
(`central-element-323112`, values never in repo/chat-persisted): `agent-orchestrator-paper-trading-slack-webhook` (the
incoming webhook — the only one the emitter needs) +
`slack-papertrading-alerts-{app-id,client-id,client-secret,signing-secret,verification-token}` (for future OAuth/Events
use). **✅ PRODUCER LOCATED + WIRED 2026-06-21.** The 2026-06-20 search came up empty because the producer is NOT in any
slot clone or on the central VM — it is the **GCP Cloud Run job `paper-trading-engine`** (`central-element-323112` /
`asia-northeast1`), built from `e2e-testing/scripts/paper_trading/paper_engine.py` (`slack_alert()`, line ~246, header
`⚡ Paper-trading — trades to do now`) and deployed by `_engine_docker/deploy.sh`; it is triggered by the daily
`uts-prod-paper-engine-run-cron` (02:00 UTC) — the prior ~hourly observation was manual `gcloud run jobs execute` test
runs during setup. The live job's `SLACK_WEBHOOK` is bound to `agent-orchestrator-paper-trading-slack-webhook:latest`
(the deploy reroute is the live revision, gen 11), so the digest now posts to `#paper-trading-alerts`. Verified
end-to-end: secret value is a valid `hooks.slack.com` incoming-webhook; a labeled routing-test POST returned HTTP 200
(delivered). The sibling `paper-signal-engine` 15-min job carries only `DB_API_KEY` (no Slack) → not a second producer.
Security note: the client/signing secrets transited chat — rotate them in the Slack app **if** it's ever extended beyond
the incoming webhook (inert for webhook-only use); the webhook URL can be regenerated + re-stored if you want it
rotated.

## Why it matters

- Paper-trading "trades to do now" is an OPERATOR ACTION feed (orders to place) — burying it in the noisy
  agent-orchestrator-alerts (worker deaths every 10 min) means real trade actions get lost. Its own channel is correct.
- The idle-min bug + quarantine-no-autoheal make the alert stream cry-wolf + can starve dispatch — both erode trust in
  the alert system the operator is trying to act on.

## Composes with

- `alert_quality_overhaul_2026_06_18.md` (watchdog/alert quality — the home for the 2 orchestrator bugs)
- `issues/staging_to_main_promotion_starvation_2026_06_19.md` + `cicd_promotion_pipeline_2026_06_18.md` (promotion lag)
- `cicd_quality_gates_2026_06_18.md` + `org_migration_to_odumresearch_2026_06_07.md` (doc-drift / contradictions)

## 2026-06-20 PM — ci-failures channel sweep (round 2)

- [x] ✅ [CICD] **Build Smoke — 1st-order error (PROJECT_ID/GAR auth) FIXED** (PM@c59ea0b1c). The bare `docker build .`
      (no `--build-arg PROJECT_ID`, no AR auth) failed at parse with
      `pkg.dev//unified-trading-library@… invalid reference format` (empty `${PROJECT_ID}` → `//`) for every service
      Dockerfile. Added `google-github-actions/auth` (`GCP_SA_KEY`)
  - `gcloud auth configure-docker` + `--build-arg PROJECT_ID=central-element-323112`. **Verified (LDR quick smoke run
    27905420638): the `//` invalid-reference is GONE — base image resolves + the GAR pull works** (SA has AR-reader).
    Real progress, keep it.
- [x] ✅ [CICD] P2. **Build Smoke — 2nd-order DESIGN gap.** **DONE via operator option (ii)** — the matrix now scopes to
      a wheel build for libraries + a Dockerfile-lint (`buildx build --check`, ADVISORY: fail only on hard parse errors,
      not intentional-pattern warnings) for image repos, and SKIPS Dockerfile-less / non-library repos — no full image
      build, so the editable-dep `uv sync` / missing-Dockerfile failures are gone. Also authenticates to Artifact
      Registry + passes `PROJECT_ID` so the private digest-pinned base images resolve. The full multi-repo image build
      stays with Cloud Build (`cloud-build-router.yml`, the real gate with the correct context). Latest run (2026-06-21
      13:39 UTC) GREEN. — unified-trading-pm@6f8fc47fc + @70076d830 + @c59ea0b1c.
      `unified-trading-pm/.github/workflows/build-smoke-all-repos.yml`.
- **mtds#260 QG red** — self-resolved earlier (MERGED; green run superseded the failure). No action.
- **Paper-trading re-route** — ALREADY WIRED in code: `e2e-testing/scripts/paper_trading/_engine_docker/deploy.sh` sets
  `SLACK_WEBHOOK=agent-orchestrator-paper-trading-slack-webhook:latest` ("reroute 2026-06-20" — the SM secret from this
  session), and `paper_engine.py` posts via `SLACK_WEBHOOK`. The producer I couldn't find last session is the
  **e2e-testing paper-trading Cloud Run job** (`scripts/paper_trading/`, added with e2e-testing 0.8.0). Remaining:
  confirm the running Cloud Run job was re-deployed with the new secret (run `deploy.sh`) so the next digest lands in
  #paper-trading-alerts.
- **strategy-service `staging-to-main` FAILED (repeating) + market-tick-data-service `update-repo-version` FAILED
  (v0.21.0) + promotion-lag 22–30 pairs** — all symptoms of the **tracked staging→main promotion starvation**
  (`issues/staging_to_main_promotion_starvation_2026_06_19.md` + `cicd_promotion_pipeline_2026_06_18.md` Bug#11, P0).
  NOT new + NOT a quick patch — the P0 fix (promote non-bumping QG-green content + the manifest version-desync /
  squash-fallback label-loss modes) is the genuinely-completable big item; recommend tackling as a focused unit.

### 2026-06-21 PM — cloud-build-router prod-deploy warnings (downstream of the drain)

The staging→main backlog drain (pushing content to main) made `cloud-build-router` attempt prod deploys and emit two
WARNINGs (not failures) for strategy-service:

- **Cloud Build Trigger Not Configured | strategy-service | prod** — but strategy-service ALREADY has
  `strategy-service-build` + `strategy-service-feature-build` triggers in `central-element-323112`, and the alert's
  suggested remediation `scripts/create-cloud-build-feature-triggers.sh` **does not exist** in the repo. So this is a
  **router prod-deploy trigger-DETECTION** nuance (the router expects a prod-deploy-named trigger, e.g. a `-main-deploy`
  like deployment-ui/api have, that service repos lack), NOT a literally-missing build trigger. Stale remediation text.
- **Tier-Ordered Deploy Warning | strategy-service blocked by instruments-service(not-deployed)** — the dep-order gate
  working as DESIGNED (strategy-service must deploy after instruments-service).

- [ ] [INFRA] P3. **cloud-build-router prod-deploy readiness for service repos** — decide (deploy-readiness,
      pre-cutover): do core service repos (strategy-service, instruments-service, …) get a prod-deploy trigger +
      auto-deploy on main now, or stay build-only until live cutover? If yes, fix the router's trigger-detection / add
      the prod-deploy triggers + fix the stale `create-cloud-build-feature-triggers.sh` remediation pointer. NOT
      triggering prod deploys of trading services autonomously (consequential; outside the starvation scope). The
      semver/update-repo-version SUCCESSES in the same dump confirm the Mode-B fix is working (repos bumping again).
      Provenance: 2026-06-21 ci-failures dump.
