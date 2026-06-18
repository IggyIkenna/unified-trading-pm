---
title: "Scripts lifecycle-marker rollout — stamp every script's frontmatter (orchestrator-dispatched, per-repo)"
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P2
status: active
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
created: 2026-06-18
locked_by: live-defi-rollout
source:
  - operator decision 2026-06-18 — roll out the lifecycle frontmatter to track usage + prune later (no deletes now)
  - convention SSOT codex/06-coding-standards/script-homes.md § "Lifecycle marker"
  - fleet characterization plans/audit/results/repo_scripts_characterization_2026_06_18.md
---

# Scripts lifecycle-marker rollout — stamp every script (per-repo, orchestrator-dispatched)

> **What:** stamp the 3-line lifecycle marker (`Epic:` / `Lifecycle:` / `Delete-when:`) onto **every** script under each
> repo's `scripts/`, so we can later see which are used and prune the unused. **No deletions** — pure additive
> frontmatter (Decision 6 of `repo_scripts_governance_audit_2026_06_18.md`). Each per-repo todo below is **sonnet-level,
> cold-start, mechanical** — designed for the orchestrator to dispatch to a worker per repo (also a live orchestrator
> test).

## Cold-start context for the worker (read before stamping a repo)

1. **The convention SSOT** — `codex/06-coding-standards/script-homes.md` § "Lifecycle marker". The marker:
   ```
   # Epic: <epic-slug>                            # owning epic (validated vs the orchestrator_vm_registry)
   # Lifecycle: permanent | campaign | oneoff
   # Delete-when: <concrete completion condition>  # required for campaign + oneoff; permanent OMITS it
   ```
2. **Placement** — **immediately after the shebang** (`#!/…`), for BOTH `.sh` and `.py` (in `.py` it precedes the module
   docstring — comments don't affect `__doc__`). **Idempotent: SKIP any file already carrying a `# Lifecycle:` line.** A
   script with no shebang → put the 3 lines at the very top. Pilot examples already stamped in PM:
   `scripts/cicd/{promote_provenance_range,slot_drift_check,parity_watchdog}.py`,
   `scripts/quality-gates-base/qg-host-governor.sh`.
3. **Classification source** — for the SERVICE repos, the per-script disposition is already in
   `plans/audit/results/repo_scripts_characterization_2026_06_18.md`: `KEEP-PERMANENT`→`permanent`;
   `KEEP-ONEOFF`→`campaign:<name>` + a `Delete-when` (the campaign milestone); `DELETE`/`DEPRECATE`→`oneoff` (or
   `campaign`) + a `Delete-when` (e.g. "after prod-run + orphan-sweep=0", or "after `<plan>` archives"). When the doc is
   silent on a file, classify by sonnet judgment per the convention. `Epic:` = the repo's owning epic (from
   `plans/epics/`; data repos → `mtds_mdps_master`/`instruments_master`/etc.; tooling → `infrastructure_master`).
4. **Ship** — stamp all of one repo's `scripts/` in one pass, commit per-repo
   (`ci(scripts): stamp lifecycle markers — <repo>`), push to that repo's `live-defi-rollout` (the marker is a comment;
   `scripts/` is outside the main gate, so no QG run needed — prek/ruff on a comment-only change is clean). Collision is
   a non-issue: a top-of-file marker doesn't conflict with body edits.
5. **Do NOT delete or deprecate-fix anything** — this is the marker rollout ONLY. Deletes/CLI-promotions stay PARKED in
   `repo_scripts_governance_audit_2026_06_18.md` until the observation window.

## Per-repo stamping todos (one worker each)

- [ ] [SCRIPT] P2. Stamp `unified-trading-pm/scripts/` (~248; 4 pilots already done — skip them). Mostly `permanent`
      tooling (cicd / quality-gates-base / propagation / plan-hygiene / agents / dev / workflow-templates); flag the few
      genuine one-offs (`migrate_*`/`backfill_*`/`gen_*_<date>`) as `oneoff`+`Delete-when`.
      `Epic: infrastructure_master` (or the owning epic for a domain script). Target: **unified-trading-pm**.
- [ ] [SCRIPT] P2. Stamp `instruments-service/scripts/` (~117) — use the characterization (64 DELETE/`oneoff`, 16
      KEEP-ONEOFF/`campaign:*-canonicalisation`, 17 permanent, etc.). `Epic: instruments_master`. Target:
      **instruments-service**.
- [ ] [SCRIPT] P2. Stamp `market-tick-data-service/scripts/` (~69) — characterization-driven (the `defi_*_2026_06_01.py`
      set = `campaign:defi_manifest_canonicalisation`, NOT oneoff). `Epic: mtds_mdps_master`. Target:
      **market-tick-data-service**.
- [ ] [SCRIPT] P2. Stamp `deployment-service/scripts/` (~270; ~217 `.sh` VM launchers = `permanent`).
      `Epic: infrastructure_master`. Target: **deployment-service**.
- [ ] [SCRIPT] P2. Stamp `e2e-testing/scripts/` (~107; the `<domain>/` harness bulk = `permanent`). `Epic:` per domain
      (defi→strategy, sports→sports, etc.) or `infrastructure_master`. Target: **e2e-testing**.
- [ ] [SCRIPT] P2. Stamp `features-service/scripts/` (~62; per-family quintet = `permanent`).
      `Epic: features_and_ml_master`. Target: **features-service**.
- [ ] [SCRIPT] P2. Stamp `unified-api-contracts/scripts/` (~33; codegen/QG checkers = `permanent`).
      `Epic: infrastructure_master` (or the contracts epic). Target: **unified-api-contracts**.
- [ ] [SCRIPT] P2. Stamp `strategy-service/scripts/` (~28; DeFi tracers = `campaign:master_to_live_defi`).
      `Epic: strategy_master`. Target: **strategy-service**.
- [ ] [SCRIPT] P2. Stamp `agent-orchestrator/scripts/` (~24; self-fleet tooling = `permanent`).
      `Epic: orchestrator_master`. Target: **agent-orchestrator**.
- [ ] [SCRIPT] P2. Stamp `unified-trading-system-ui/scripts/` (~17; 7 are 2026-03 run-once splitters = `oneoff`).
      `Epic:` the UI epic. Target: **unified-trading-system-ui**.
- [ ] [SCRIPT] P2. Stamp `execution-service/scripts/` (~12; validation runbooks = `campaign`/`permanent`).
      `Epic: execution_master`. Target: **execution-service**.
- [ ] [SCRIPT] P2. Stamp `ml-service/scripts/` (~12; per-family boilerplate = `permanent`).
      `Epic: features_and_ml_master`. Target: **ml-service**.
- [ ] [SCRIPT] P2. Stamp `ibkr-gateway-infra/scripts/` (~11; all clean `permanent` gateway/VM lifecycle).
      `Epic: infrastructure_master`. Target: **ibkr-gateway-infra**.
- [ ] [SCRIPT] P2. Stamp `market-data-processing-service/scripts/` (~10; 3 dated reconcilers = `oneoff`).
      `Epic: mtds_mdps_master`. Target: **market-data-processing-service**.
- [ ] [SCRIPT] P2. Stamp `client-reporting-api/scripts/` (~9; `daily_update.py` recurring). `Epic:` the client-reporting
      epic. Target: **client-reporting-api**.
- [ ] [SCRIPT] P2. Stamp `unified-trading-library/scripts/` (~9; codegen/checkers = `permanent`;
      `migrate_manifest_v8.py` = `oneoff`). `Epic: infrastructure_master`. Target: **unified-trading-library**.
- [ ] [SCRIPT] P2. Stamp `system-integration-tests/scripts/` (~7; SIT runners = `permanent`).
      `Epic: infrastructure_master`. Target: **system-integration-tests**.
- [ ] [SCRIPT] P2. Stamp `unified-trading-api/scripts/` (~5; openapi/persona codegen = `permanent`). `Epic:` the api
      epic. Target: **unified-trading-api**.
- [ ] [SCRIPT] P2. Stamp `deployment-api/scripts/` (~5; 1 ghost-venue one-shot). `Epic: deployment_and_user_management`.
      Target: **deployment-api**.
- [ ] [SCRIPT] P2. Stamp `alerting-service/scripts/` (~5; clean `permanent`). `Epic: observability_master`. Target:
      **alerting-service**.
- [ ] [SCRIPT] P2. Stamp `trading-agent-service/scripts/` (~4; clean boilerplate `permanent`).
      `Epic: trading_agent_master`. Target: **trading-agent-service**.
- [ ] [SCRIPT] P2. Stamp `batch-live-reconciliation-service/scripts/` (~4; clean boilerplate `permanent`). `Epic:` the
      recon epic. Target: **batch-live-reconciliation-service**.

## Success criteria

- `grep -rl '^# Lifecycle:' <repo>/scripts/` covers every script in every repo (idempotent — re-running stamps nothing
  new).
- Each `campaign`/`oneoff` carries a `Delete-when`; each `Epic:` is a valid registry id.
- No deletions / no body edits — frontmatter-only.
- Then (separate, deferred): prune by `Delete-when` per `repo_scripts_governance_audit_2026_06_18.md` — **NO run-ledger
  / no runtime last-run tracking** (operator 2026-06-18: the `Delete-when` condition is the trigger; an auto usage
  timestamp is commit-noise for ~zero decision value).
