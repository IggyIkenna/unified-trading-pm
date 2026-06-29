---
doc_type: plan
title: Fleet LDR→main promote was dead ~7h — a YAML break silently killed the */15 schedule (+ UTL flaky stale-status)
created: 2026-06-29
source:
  - .github/workflows/ldr-to-main-promote-fleet.yml (the broken workflow — fixed LDR@7ecd7aa9c + main@3c82b6ad5)
  - scripts/cicd/ci_status_store.py (UTL ci_status clear)
  - plans/active/cicd_retire_staging_branch_2026_06_27.md (2026-06-29 Progress Log)
  - plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md (unknown-delta / coverage)
priority: P1
status: active
cadence: on-incident
verifier:
  gh run list --repo IggyIkenna/unified-trading-pm --workflow ldr-to-main-promote-fleet.yml (event=schedule fires +
  succeeds)
last_executed: 2026-06-29
summary:
  "Fleet-wide LDR→main promotion-lag >60m alert (8 service repos: instruments-service, market-tick-data-service,
  market-data-processing-service, deployment-api, deployment-service, +3) — NOT a display bug. Root cause: the fleet
  promoter ldr-to-main-promote-fleet.yml had a YAML parse error (an embedded python3 -c heredoc at column-0 inside a
  10-space `run: |` block → 'could not find expected :' at line 307). GitHub does NOT schedule a workflow whose file is
  unparseable on the default branch, so the */15 cron silently STOPPED at 2026-06-28 22:58 UTC → the fleet auto-drain
  was dead ~7h. CORRECTION to an earlier analysis: the promoter IS scheduled (cron 8,23,38,53) — it was not '0 scheduled
  runs ever'; the schedule was YAML-killed. Compounded by UTL's stale ci_status=FAILING (a flaky QG dep-clone failure)
  dep-order-holding deployment-api. Both fixed."
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

## Symptom

- `branch-health` Slack: `PROMOTION LAG > 60m — 8 branch-pair(s) across 7 repo(s)` (service repos; PM not listed).
- `/repos`: LDR→main delta + multi-day lag on instruments-service / market-tick-data-service /
  market-data-processing-service / deployment-api / deployment-service / agent-orchestrator / deployment-ui.
- `Overnight Dead Man Switch CRITICAL` (the overnight orchestrator's Tier-0 hit UTL's transient flaky QG).
- Last content-to-main was 1.5–2.5 days old for several repos; deployment-api drained only on a manual dispatch.

## Root cause (verified)

1. **`ldr-to-main-promote-fleet.yml` failed to PARSE.** The `CURRENT_WORKSPACE_DIGEST=$(python3 -c "..."`
   workspace-digest heredoc sat at **column 0** inside a 10-space `run: |` block → YAML ended the block early →
   `could not find expected ':'` (line 307). GitHub **will not schedule an unparseable default-branch workflow**, so the
   `*/15` cron (`8,23,38,53 * * * *`) **silently stopped firing at 2026-06-28 22:58 UTC** (last schedule-event run). The
   workflow stayed `state: active` — there is no "disabled" signal; it just stops scheduling. Push-triggered runs still
   appeared (as parse failures); scheduled runs were simply never created.
2. **UTL stale ci_status=FAILING (flaky).** `unified-trading-library`'s QG failure was the **dep-clone phantom-version /
   stale-deps** class (a fresh QG-v2 on main came back SUCCESS). The stale FAILING dep-order-held deployment-api.

## Fix (shipped)

- Re-indented the python to the block base (verified: file parses + the python compiles at col-0). **LDR@7ecd7aa9c +
  main@3c82b6ad5** — `.github` carve-out **direct-to-main** because a broken promote cannot self-promote its own fix.
- Cleared UTL `ci_status` FAILING→MAIN_GREEN via the `ci_status_store.py` producer (Firestore SSOT) after verifying
  green.
- Manual `workflow_dispatch` runs (28350383721 SUCCESS, +) drained deployment-api#249 / market-tick-data-service#467 /
  deployment-service#318; the gate auto-dispatched SIT-on-LDR for the `unknown-delta` repos.

## Open follow-ups

- [x] **P1 — the `*/15` schedule self-healed (RESOLVED 2026-06-29).** GitHub's scheduler stayed dormant ~3.5h after the
      YAML fix (consistent with its known post-invalid dormancy; neither the fix commit nor a disable→enable toggle
      forced it), then revived on its own: first `event=schedule` run fired **2026-06-29T08:47:15Z and SUCCEEDED**, with
      native cron ticks continuing on cadence after (verify:
      `gh run list --workflow ldr-to-main-promote-fleet.yml     --json event,conclusion` shows `schedule`/`success`).
      **Stopgap (15-min `workflow_dispatch` loop) ran 08:15–09:00, auto-detected the heal, and stopped** — no longer
      needed; fleet auto-drain is self-sustaining.
- [ ] **P1 — harden the QG dep-clone (the recurring root).** The phantom-version → stale-deps fallback is what made UTL
      flake; it will re-trip the overnight Dead-Man-Switch and can re-stale a tier-0 ci_status → re-block the fleet.
      Durable fix = make the cross-repo dep-clone resolution deterministic (don't fall through to stale deps; fail
      loud).
- [x] **P2 — workflow-YAML gate on PM `.github/` workflows (DONE — PM@94391e2e7).**
      `scripts/quality_gates/     check_workflow_yaml_valid.py` (wired into `scripts/quality-gates.sh` after the
      workflow-template-parity check) FAILS QG on any unparseable `.github/workflows/*.yml` (`yaml.safe_load`) — the
      exact incident class is now caught pre-merge; actionlint runs as an informational deeper lint (non-blocking, to
      avoid pre-existing style noise). Tested: passes on the fixed file, exits 1 on the re-injected col-0 break.
- [ ] **P2 — deployment-ui + agent-orchestrator `unknown-delta`.** TS / differ-source-dir → they promote only via the
      auto-dispatched SIT (coverage flipped 21/21, `7e0177e1e`) or need genuine SIT invariants (no forged manifest
      edits). Cross-ref `sit_rehome_safety_gate_gaps_2026_06_27.md`.
