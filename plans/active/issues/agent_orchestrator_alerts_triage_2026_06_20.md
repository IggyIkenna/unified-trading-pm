---
title: "Slack/orchestrator alert triage (2026-06-20) — alerts vs open PM plans; paper-trading channel split; 2 net-new gaps"
created: 2026-06-20
status: active
priority: P2
locked_by: live-defi-rollout
source:
  - 2026-06-20 operator paste — ci-failures + agent-orchestrator-alerts Slack dump
  - 3 Explore sub-agents (slot-3) — alert↔plan cross-reference + Slack-routing map
---

# Slack / agent-orchestrator alert triage (2026-06-20)

## What I found — every live alert theme mapped to its tracking plan (open vs done)

| Alert (channel) | Tracking plan / issue | Status | Action |
| --- | --- | --- | --- |
| Worker heartbeat loop dead — slots 1/4/5/6, every ~10–15 min | `alert_quality_overhaul_2026_06_18.md` (dedup→disk SHIPPED) | TRACKED; **the absurd idle-minute values (5711, 1515) are a NET-NEW UNTRACKED BUG** | NEW todo ↓ |
| Spawn failure — branch-state quarantine (slot 6, unified-trading-pm diverged, FM5/FM7) | `alert_quality_overhaul_2026_06_18.md` Phase 3 (alert SHIPPED) | TRACKED alert; **no auto-recovery (quarantine never auto-clears) = gap** | NEW todo ↓ |
| Context-burn suspected (slot 1, flag-only) | `alert_quality_overhaul_2026_06_18.md` Phase 3 | TRACKED; flag-only BY DESIGN (kill gated off) | none — expected |
| Orphan ping(s) detected (2) | `issue_docs_remediation_sweep_2026_06_02.md` + `codex/11-project-management/plan-hygiene.md` | TRACKED; process discipline | slot-1/harsh clear within cycle |
| Slot N unpushed plan(s) (citadel…, master…) | `fleet_git_health_orchestrator_2026_06_10.md` | TRACKED; transient (Commit+Push+Flip) | slot owner pushes |
| QG slice FAILED — market-tick-data-service PR#260 LDR→staging | (live code failure, not a plan gap) | OPEN — genuine red | fix the failing test/code now (like execution-service 2026-06-17) |
| promotion-lag-monitor — 24 branch-pairs un-propagated (ages to 7305m) | `issues/staging_to_main_promotion_starvation_2026_06_19.md` + `cicd_promotion_pipeline_2026_06_18.md` Bug#11 (P0) + `promotion_queue_conflict_wall_pileup_2026_06_17.md` (squash-noise P1s) | TRACKED — but the **P0 root-cause fixes are OPEN** | drive the open P0/P1 promote-flow todos; large age = commit-count noise + the 2 unfixed structural causes |
| plan-health doc-drift (5) + contradictions (6) — stale `tab/<op>/N` refs, IggyIkenna→OdumResearch | `cicd_quality_gates_2026_06_18.md` (AO worker.md/boot-prompt rewrite, P2) + `org_migration_to_odumresearch_2026_06_07.md` (Phase 5 sweep) + `issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md` | TRACKED; OPEN P2–P3 | unblock the Path-B AO doc rewrites |
| **Paper-trading — "trades to do now"** (mis-routed to agent-orchestrator-alerts) | — none — | NET-NEW | route to `#paper-trading-alerts` ↓ |

**Headline:** almost every alert is ALREADY tracked. The promotion-lag (P0 Bug#11 + the squash-noise/staging-merge-base
structural P1s) is the biggest open theme and is the same un-done work from 2026-06-17/19 — not new. Three things are
genuinely net-new and captured below.

## Net-new todos (the gaps the alerts surfaced)

- [ ] [BUG] P2. **WorkerLivenessWatchdog bogus idle-minute calc** — alerts show "idle for 5711min" (slot 4) / "1515min"
      (slot 5) — physically impossible (≈4 days / 1 day). Root cause (per code read): the silence anchor in
      `agent-orchestrator/server/health.py` (~L182, `max(last, last_spawned_at, assigned_at)`) inherits a PREDECESSOR
      session's `last_spawned_at` after a silent respawn, so `silence` balloons backwards → `stale_min` (L273) reports
      days. Fix: anchor silence to the CURRENT session's spawn/heartbeat only (reset on respawn), clamp to session age.
      **Target repo:** agent-orchestrator. Composes with `alert_quality_overhaul_2026_06_18.md` (add as its Phase-4 item
      if that plan owns watchdog-alert quality).
- [ ] [INFRA] P2. **Quarantined-slot auto-recovery** — a slot stuck in "branch-state quarantine" (worktree not on
      `live-defi-rollout`) is only ALERTED, never auto-cleaned; one quarantined slot starved escalation dispatch for
      hours (2026-06-18 incident, escalation.py). Add a bounded auto-heal: on quarantine, attempt
      `git -C .tabs/<N>/<repo> merge --abort || true; git checkout live-defi-rollout; git reset --hard origin/live-defi-rollout`
      ONLY when the worktree is provably a dead session (no live `.agent-claim`, no tmux) per the liveness-gated
      inherited-dirty-WIP rule — never stomp a live peer. **Target repo:** agent-orchestrator. Composes with
      `alert_quality_overhaul_2026_06_18.md` Phase 3 + the respawn-hygiene rule.
- [ ] [INFRA] P2. **Split paper-trading "trades to do now" alerts into `#paper-trading-alerts`** (operator created the
      channel 2026-06-20). The `:zap: Paper-trading — trades to do now` digest currently posts to
      `#agent-orchestrator-alerts`; it should go to the dedicated channel. **Operator Slack-setup required FIRST** (see
      below). **Emitter NOT in any slot clone** (grep for `trades to do now` / `book ROE` / `paper vs backtest
      divergence` = 0 code hits fleet-wide) → the paper-trading scan/notifier runs on the orchestrator VM (vm-planning)
      or an un-cloned path; locate it there (`ssh human-planning-vm` / central VM) before wiring. **Target repo:**
      agent-orchestrator (or wherever the paper-trading scan emitter lives) + the alerting webhook config.

## Paper-trading channel split — operator Slack setup (the answer to "what do I need to do")

**Slack reality:** a Slack-app **incoming webhook is bound to ONE channel at creation** — the `channel` field in the
payload is IGNORED for modern app webhooks. So you **cannot** "reuse the same webhook URL but a different channel." You
reuse the same Slack **app + the same backend notify code**, but you need a **separate webhook URL** for the new channel
(the current alerts post via a webhook URL env `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` / SM `alerting-uts-live-alerts-slack-webhook`).

**Operator steps:**
1. Slack → the app that already posts to `#agent-orchestrator-alerts` → **Incoming Webhooks** → **Add New Webhook to
   Workspace** → pick **`#paper-trading-alerts`** → copy the new URL (`https://hooks.slack.com/services/T…/B…/…`).
2. Hand me the URL (or store it yourself) → I put it in Secret Manager as **`agent-orchestrator-paper-trading-slack-webhook`**.
3. I point ONLY the paper-trading "trades to do now" emitter at that webhook (the other agent-orchestrator alerts stay
   on the existing webhook/channel). One-line routing change once the emitter is located.

**Alternative (no new webhook):** if the backend is switched to a Slack **bot token** (`chat.postMessage` with a
`channel` param) the bot can post to any channel it's invited to — then you'd just `/invite` the bot to
`#paper-trading-alerts`. But today it's webhook-based, so the new-webhook path above is the route.

**✅ DONE 2026-06-20 — `papertrading-alerts` Slack app created + all creds stored in GCP Secret Manager**
(`central-element-323112`, values never in repo/chat-persisted): `agent-orchestrator-paper-trading-slack-webhook` (the
incoming webhook — the only one the emitter needs) + `slack-papertrading-alerts-{app-id,client-id,client-secret,signing-secret,verification-token}`
(for future OAuth/Events use). **Remaining = wire the emitter — BLOCKED on locating the producer (2026-06-20 search exhausted).**
Searched + came up empty: (a) all local slot clones — by message text AND structural fragments (`trades to do now`,
`book ROE`, `paper vs backtest`, `identical by construction`, `est cost`, `taker-IOC`, `Sharpe`) = 0 code hits; (b) the
central orchestrator VM `i-0c9b283b31d6b5ca7` (registry `planning`) — source tree, venv site-packages, crontab (ubuntu +
root), `journalctl -u orchestrator -n 3000`, `server/notifications/{slack,telegram}.py`, `.env.local` (no `*WEBHOOK*`/
`*SLACK*`/`*PAPER*` var) — all 0. The digest **lacks the `Dashboard | from: vm-planning` footer that every AO notifier
alert carries**, so it does NOT go through `server/notifications/slack.py` — it is an **external producer posting
directly to the agent-orchestrator-alerts webhook**, ~hourly (10:39 → 12:25 UTC observed). **UNBLOCK (operator input
needed):** where does the paper-trading "trades to do now" scan run / who set it up? (a strategy paper VM? a Cloud Run /
scheduled scan? a colocated_engine cron on another host?) Once the producer host+config is named, the wiring is a
one-liner: point its webhook env/secret at `agent-orchestrator-paper-trading-slack-webhook` + restart. The destination
(channel + webhook + all app creds in SM) is 100% ready. Security note: the client/signing secrets transited chat — rotate them in the Slack app **if** the app is ever
extended beyond the incoming webhook (inert for webhook-only use); the webhook URL can be regenerated in Slack + re-stored
if you want it rotated.

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
  (no `--build-arg PROJECT_ID`, no AR auth) failed at parse with `pkg.dev//unified-trading-library@… invalid reference
  format` (empty `${PROJECT_ID}` → `//`) for every service Dockerfile. Added `google-github-actions/auth` (`GCP_SA_KEY`)
  + `gcloud auth configure-docker` + `--build-arg PROJECT_ID=central-element-323112`. **Verified (LDR quick smoke run
  27905420638): the `//` invalid-reference is GONE — base image resolves + the GAR pull works** (SA has AR-reader). Real
  progress, keep it.
- [ ] [CICD] P2. **Build Smoke — 2nd-order DESIGN gap (the smoke is still RED; this is the real blocker, needs a
  decision).** With the base image resolving, the smoke now hits the actual problem: a standalone single-repo
  `docker build .` **cannot build the fleet's images** because (a) **service images need sibling editable path-deps in
  the build context** — `uv sync --frozen` → `Distribution not found at: file:///app/unified-api-contracts` (ml-service
  + every service that `[tool.uv.sources]`-path-deps UAC/UTL/…); Cloud Build supplies the multi-repo context, a lone
  `docker build .` does not; and (b) **Dockerfile-less repo types are still `docker build`ed** — `system-integration-tests`
  + `unified-trading-api` → `open Dockerfile: no such file or directory`. **Decision (operator):** (i) give the smoke the
  same multi-repo context as Cloud Build (checkout/COPY sibling deps, or reuse `create-code-tarballs`) — heaviest, truest;
  (ii) scope the matrix to only repos with a self-contained root Dockerfile + skip the editable-dep `uv sync` (Dockerfile
  lint/parse smoke only); or (iii) RETIRE the build-smoke and rely on Cloud Build (the real image gate with the correct
  context) — the live pipeline already builds via `cloud-build-router.yml`, so a red weekly smoke is not blocking
  deploys. **Recommend (iii) or (ii)** — (i) re-implements Cloud Build's context in GHA for marginal value. **Target:**
  `unified-trading-pm/.github/workflows/build-smoke-all-repos.yml`. Provenance: run 27905420638.
- **mtds#260 QG red** — self-resolved earlier (MERGED; green run superseded the failure). No action.
- **Paper-trading re-route** — ALREADY WIRED in code: `e2e-testing/scripts/paper_trading/_engine_docker/deploy.sh`
  sets `SLACK_WEBHOOK=agent-orchestrator-paper-trading-slack-webhook:latest` ("reroute 2026-06-20" — the SM secret from
  this session), and `paper_engine.py` posts via `SLACK_WEBHOOK`. The producer I couldn't find last session is the
  **e2e-testing paper-trading Cloud Run job** (`scripts/paper_trading/`, added with e2e-testing 0.8.0). Remaining: confirm
  the running Cloud Run job was re-deployed with the new secret (run `deploy.sh`) so the next digest lands in
  #paper-trading-alerts.
- **strategy-service `staging-to-main` FAILED (repeating) + market-tick-data-service `update-repo-version` FAILED
  (v0.21.0) + promotion-lag 22–30 pairs** — all symptoms of the **tracked staging→main promotion starvation**
  (`issues/staging_to_main_promotion_starvation_2026_06_19.md` + `cicd_promotion_pipeline_2026_06_18.md` Bug#11, P0).
  NOT new + NOT a quick patch — the P0 fix (promote non-bumping QG-green content + the manifest version-desync /
  squash-fallback label-loss modes) is the genuinely-completable big item; recommend tackling as a focused unit.
