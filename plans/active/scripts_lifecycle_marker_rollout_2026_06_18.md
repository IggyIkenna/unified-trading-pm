---
title:
  "Scripts lifecycle-marker rollout — stamp every script's frontmatter (orchestrator-dispatched, per-repo) — AO
  fleet-test plan"
parent_epic: infrastructure_master
assigned_vm: harsh_pc
priority: P2
status: active
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
created: 2026-06-18
locked_by: live-defi-rollout
source:
  - operator decision 2026-06-18 — roll out the lifecycle frontmatter to track usage + prune later (no deletes now)
  - operator decision 2026-06-22 — Delete-when is MANDATORY-PRESENT (NA for permanent) so every script is greppable;
    marker becomes QG-ENFORCED (last item, after all repos stamped); reassigned to harsh_pc as the live AO fleet-test
    plan
  - convention SSOT codex/06-coding-standards/script-homes.md § "Lifecycle marker"
  - fleet characterization plans/audit/results/repo_scripts_characterization_2026_06_18.md
---

# Scripts lifecycle-marker rollout — stamp every script (per-repo, orchestrator-dispatched) — AO fleet-test plan

> **What:** stamp the 3-line lifecycle marker (`Epic:` / `Lifecycle:` / `Delete-when:`) onto **every** script under each
> repo's `scripts/`, so we can later see which are used and prune the unused. **No deletions** — pure additive
> frontmatter (Decision 6 of `repo_scripts_governance_audit_2026_06_18.md`). Each per-repo todo below is **sonnet-level,
> cold-start, mechanical** — designed for the orchestrator to dispatch to a worker per repo.
>
> **Dual purpose — this is also the live AO fleet-test plan (operator 2026-06-22):** `assigned_vm: harsh_pc` so the
> local orchestrator backend (running as `harsh_pc`, STANDALONE) ingests it via the reconciler and dispatches a worker
> per repo. The per-repo todos are independent (different repos, never the same file) → safe to parallelize, and the
> work is low-risk (additive comments, no QG run) — an ideal exercise of the worker-spawn loop.
>
> **⚠️ CONVENTION CORRECTION (operator 2026-06-22) — read before stamping:** all **3 fields are MANDATORY and PRESENT**
> on every script. `Epic:` and `Lifecycle:` always carry a value. `Delete-when:` is the only field whose _value_ is
> optional — but it must still be **present**, carrying **`NA`** when not needed (i.e. for `permanent`). This makes
> every script greppable for `Delete-when` (`grep -rL '^# Delete-when:' */scripts/` must return nothing). The marker
> becomes **QG-ENFORCED** like other frontmatter'd filetypes — but enforcement is the **LAST** item, blocked until every
> repo is stamped (else it would red the fleet). Todo #1 updates the SSOT to this corrected rule **first**, so every
> stamping worker reads the right spec.

## Cold-start context for the worker (read before stamping a repo)

1. **The convention SSOT** — `codex/06-coding-standards/script-homes.md` § "Lifecycle marker". The marker:
   ```
   # Epic: <epic-slug>                            # owning epic (validated vs the orchestrator_vm_registry) — REQUIRED
   # Lifecycle: permanent | campaign | oneoff     # REQUIRED
   # Delete-when: <condition> | NA                 # REQUIRED + PRESENT; `NA` for permanent, a real condition otherwise
   ```
   **All 3 lines on EVERY script** (operator 2026-06-22). `Delete-when` is never omitted — a `permanent` script carries
   `# Delete-when: NA` so the whole fleet is greppable: `grep -rL '^# Delete-when:' <repo>/scripts/` must be empty.
2. **Placement** — **immediately after the shebang** (`#!/…`), for BOTH `.sh` and `.py` (in `.py` it precedes the module
   docstring — comments don't affect `__doc__`). **Idempotent: SKIP any file already carrying a `# Lifecycle:` line.** A
   script with no shebang → put the 3 lines at the very top. Pilot examples already stamped in PM:
   `scripts/cicd/{promote_provenance_range,slot_drift_check,parity_watchdog}.py`,
   `scripts/quality-gates-base/qg-host-governor.sh`.
3. **Classification source** — for the SERVICE repos, the per-script disposition is already in
   `plans/audit/results/repo_scripts_characterization_2026_06_18.md`: `KEEP-PERMANENT`→`permanent` + `Delete-when: NA`;
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

## Phase 0 — fix the convention SSOT FIRST (one worker, do before any stamping)

- [x] ✅ [SCRIPT] P0. Update `codex/06-coding-standards/script-homes.md` § "Lifecycle marker" to the corrected rule
      (operator 2026-06-22): all 3 fields MANDATORY + PRESENT; `Delete-when` carries **`NA`** for `permanent` (never
      omitted) so `grep -rL '^# Delete-when:' */scripts/` is empty fleet-wide; and state the marker is **QG-ENFORCED**
      (ratchet) once the rollout completes. Replace the old "permanent omits it" wording + the "No `Delete-when`"
      bullet. This is the spec every stamping worker reads — it MUST land before Phase 1. Target:
      **unified-trading-pm**. — unified-trading-pm@0e3e2a130

## Per-repo stamping todos (one worker each — Phase 1; every script gets all 3 fields incl. `Delete-when` = `NA`-or-condition)

- [x] ✅ [SCRIPT] P2. Stamp `unified-trading-pm/scripts/` (~248; 4 pilots already done — skip them). Mostly `permanent`
      tooling (cicd / quality-gates-base / propagation / plan-hygiene / agents / dev / workflow-templates); flag the few
      genuine one-offs (`migrate_*`/`backfill_*`/`gen_*_<date>`) as `oneoff`+`Delete-when`.
      `Epic: infrastructure_master` (or the owning epic for a domain script). Target: **unified-trading-pm**. —
      unified-trading-pm@2dc131639 | 493 files stamped (484 new + 9 Delete-when: NA added to pre-existing) |
      grep -rL '^# Lifecycle:' scripts/ → empty ✓ | grep -rL '^# Delete-when:' scripts/ → empty ✓
- [x] ✅ [SCRIPT] P2. Stamp `instruments-service/scripts/` (~117) — use the characterization (64 DELETE/`oneoff`, 16
      KEEP-ONEOFF/`campaign:*-canonicalisation`, 17 permanent, etc.). `Epic: instruments_master`. Target:
      **instruments-service**. — instruments-service@6a64236 (123 stamped, 12 already done)
- [x] ✅ [SCRIPT] P2. Stamp `market-tick-data-service/scripts/` (~69) — characterization-driven (the `defi_*_2026_06_01.py`
      set = `campaign:defi_manifest_canonicalisation`, NOT oneoff). `Epic: mtds_mdps_master`. Target:
      **market-tick-data-service**. — market-tick-data-service@4c8ea5bf | 70 files stamped; grep -rL '^# Delete-when:' returns only __init__.py
- [x] ✅ [SCRIPT] P2. Stamp `deployment-service/scripts/` (~270; ~217 `.sh` VM launchers = `permanent`).
      `Epic: infrastructure_master`. Target: **deployment-service**. — deployment-service@51a2f4d | 275 files stamped | grep -rL '^# Lifecycle:' → empty ✓ | grep -rL '^# Delete-when:' → empty ✓ | grep -rL '^# Epic:' → empty ✓
- [ ] [SCRIPT] P2. Stamp `e2e-testing/scripts/` (~107; the `<domain>/` harness bulk = `permanent`). `Epic:` per domain
      (defi→strategy, sports→sports, etc.) or `infrastructure_master`. Target: **e2e-testing**.
- [ ] [SCRIPT] P2. Stamp `features-service/scripts/` (~62; per-family quintet = `permanent`).
      `Epic: features_and_ml_master`. Target: **features-service**.
- [ ] [SCRIPT] P2. Stamp `unified-api-contracts/scripts/` (~33; codegen/QG checkers = `permanent`).
      `Epic: infrastructure_master` (or the contracts epic). Target: **unified-api-contracts**.
- [ ] [SCRIPT] P2. Stamp `strategy-service/scripts/` (~28; DeFi tracers = `campaign:master_to_live_defi`).
      `Epic: strategy_master`. Target: **strategy-service**.
- [ ] [SCRIPT] P2. Stamp `agent-orchestrator/scripts/` (~24; self-fleet tooling = `permanent`).
      `Epic: orchestrator_master`. Target: **agent-orchestrator**. **PARTIAL — RE-STAMP NEEDED (2026-06-22 rule):** the
      first pass (`agent-orchestrator@ebb0c6f`) stamped `Epic:` + `Lifecycle: permanent` on all 23 non-symlink scripts
      but **OMITTED `Delete-when`** (the old "permanent omits it" convention). Under the corrected rule every script
      needs `# Delete-when: NA` — add it after the `# Lifecycle: permanent` line on all 23 (idempotent; skip any already
      carrying `# Delete-when:`; `quickmerge.sh` symlink → PM SSOT skipped). Done when
      `grep -rL '^# Delete-when:' scripts/` is empty.
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

## Phase 2 — QG enforcement (THE LAST ITEM — blocked until ALL of Phase 0 + Phase 1 above are ✅)

- [ ] [SCRIPT] P1. **BLOCKED — `[OPERATOR]`-gated; do NOT start until every Phase-0 + Phase-1 repo above is ✅** (else
      it reds the whole fleet on still-unstamped repos). Build + wire the lifecycle-marker QG checker so the 3-field
      marker is enforced like other frontmatter'd filetypes: a checker
      (`scripts/quality_gates/check_script_lifecycle_markers.py`) that FAILS when a `scripts/` file is missing any of
      `# Epic:` / `# Lifecycle:` / `# Delete-when:`, or has an invalid `Lifecycle` value, or an `Epic:` not in
      `orchestrator_vm_registry.yaml`'s epic set, or a non-`permanent` carrying `Delete-when: NA`. Wire it into the
      PM-sourced `base-service.sh` + `base-library.sh` so it rides fleet-wide with NO per-repo rollout (mirror STEP
      5.94/5.95). The operator unblocks this ONLY after confirming `grep -rL '^# Delete-when:' */scripts/` is empty
      fleet-wide. Update `codex/06-coding-standards/quality-gates.md` + `script-homes.md` § "What gates a scripts/ file"
      in the same unit. Target: **unified-trading-pm** (checker + base wiring) → fleet.

## Success criteria

- **All 3 fields on every script, fleet-wide:** `grep -rL '^# Lifecycle:' */scripts/` AND
  `grep -rL '^# Delete-when:' */scripts/` AND `grep -rL '^# Epic:' */scripts/` all return **nothing** (idempotent —
  re-running stamps nothing new).
- `permanent` carries `# Delete-when: NA`; each `campaign`/`oneoff` carries a real `Delete-when`; each `Epic:` is a
  valid registry id.
- No deletions / no body edits — frontmatter-only.
- **QG enforcement (Phase 2) green fleet-wide** — the marker checker passes in `base-*.sh`; a script missing any field
  fails CI like any other frontmatter violation.
- **Fleet-test outcome (this plan's dual purpose):** the `harsh_pc` backend ingested this plan via the reconciler and
  dispatched a worker per repo that shipped its per-repo `ci(scripts): stamp lifecycle markers — <repo>` commit — i.e.
  the orchestrator worker-spawn loop is verified end-to-end.
- Then (separate, deferred): prune by `Delete-when` per `repo_scripts_governance_audit_2026_06_18.md` — **NO run-ledger
  / no runtime last-run tracking** (operator 2026-06-18: the `Delete-when` condition is the trigger; an auto usage
  timestamp is commit-noise for ~zero decision value).
