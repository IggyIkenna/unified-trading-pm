---
title:
  QG commit-quality-boundary + slot FF-push to LDR (aggregation of uv-determinism + governor-macOS-fix + commit-gate
  design)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
created: 2026-06-03
locked_by: live-defi-rollout
related_plans:
  - plans/active/uv_lockfile_determinism_2026_06_02.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/active/agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md
source:
  - operator design discussion 2026-06-02/03 (slot tab/ikennaigboaka/4)
  - plans/active/uv_lockfile_determinism_2026_06_02.md (parent effort, shipped)
---

# QG commit-quality-boundary + slot FF-push to LDR

> Aggregates the 2026-06-02/03 session: the shipped uv.lock-determinism + QG-host-governor-macOS-fix work, the discovery
> it produced, and the design decisions that follow — then aligns the canonical rule/flow docs. **doc → plan → code**:
> this plan enumerates the doc/rule/codex edits so they're reviewable before they ship.

## Shipped this session (on LDR — evidence)

All on `origin/live-defi-rollout`; full detail in
[uv_lockfile_determinism_2026_06_02.md](uv_lockfile_determinism_2026_06_02.md).

- [x] [INFRA] uv.lock determinism Phases 1–5 — read-only QG verifier (`uv lock --check`, not mutating `uv lock`), pin
      `uv==0.10.8` at all install sites (setup.sh, base-service/library bootstraps, CI workflow, UTL Dockerfile),
      ratchet verifier to blocking-on-pinned-uv, codex 3-role model (writer=quickmerge / verifier=QG / determinism=pin).
- [x] [INFRA] **QG host-governor macOS fix** — `qg-host-governor.sh` used bash≥4.1 `exec {fd}>`; macOS bash 3.2 parsed
      it as a command and CRASHED `quality-gates.sh` at stage [2] (no sentinel → quickmerge blocked from any Mac slot).
      Fixed: degrade to ungoverned on bash <4.1 (acquire + `--status`). **This unblocks local QG on every Mac slot.**
- [x] [INFRA] PM codex empty-fallback excludes + `.code-workspace`/manifest drift fix (greeks/fund-admin
      `future`→`scaffolded`). PM QG fully green (exit 0, all 6 stages + drift guard).
- [x] [DEPS] Re-lock-all sweep: **13/14** stale repos re-locked to LDR (uv 0.10.8, 0 resolved-version moves); UTL
      pinned. (`unified-trading-api` re-lock = 1 straggler, see below.)
- [x] [INFRA] Slot-branch reconciliation: 16 touched slot branches brought current with LDR (14 → 0↑/0↓; PM + uta →
      1↑/0↓).

## Key discovery (cross-cuts cicd_contract_hardening Phase 6)

- [ ] [INFRA] P1. **The governor bash-3.2 crash had been MASKING pre-existing per-repo QG debt workspace-wide** — every
      macOS `quality-gates.sh` died at stage [2], so no repo's stage-5+ failures (codex baselines, cloudbuild-schema,
      size/import) were visible locally. Fixing the governor makes local QG run fully and **surfaces** that debt
      (observed: PM 3 issues cleared; UTL within-baseline; trading-agent-service STEP-5.17 cloudbuild-schema FAILS).
      **This is the same per-repo-debt that
      [cicd_contract_hardening_2026_06_01.md](cicd_contract_hardening_2026_06_01.md) Phase 6 greens** — that plan
      attributed surfacing to the v2 rollout; the governor crash was a second masking layer on the _local_ gate
      specifically. Cross-link, don't duplicate: the debt-greening lives in cicd Phase 6; this plan owns the
      governor-fix that exposed it. **DEFERRED to the cicd Phase-6 per-repo sweep.**

- [ ] [SCRIPT] P2. **QG sentinels not gitignored fleet-wide → per-QG-run drift (TWO failure modes)** —
      `.qg_last_passed_sha` (and `.qg_content_sentinel`) are local caches written by `quality-gates.sh`. (a)
      **untracked** in most repos → reappear as `??` after every QG run; (b) **already committed/tracked** in some repos
      (found: `agent-orchestrator`, `unified-api-contracts` — a machine-specific HEAD SHA was committed) → **gitignore
      alone does NOTHING, needs `git rm --cached`**. Both re-dirty slot trees + jam `slot-cron-ff-pull.sh` (observed:
      alerting-service, 2026-06-03). Fix: add both patterns to the **canonical `.gitignore` template**
      (`scripts/templates/`, the workspace SSOT) + roll out to all repos; AND for each repo run
      `git ls-files | grep -E 'qg_last_passed_sha|qg_content_sentinel'` → `git rm --cached` any tracked instance. **Done
      this session (slot branches)**: `alerting-service` (gitignore — was untracked), `agent-orchestrator` +
      `unified-api-contracts` (`rm --cached` + gitignore — were tracked); **`unified-trading-pm` `.qg_content_sentinel`
      gitignored (local, PM@7b6a46b48, 2026-06-03)** — alongside the already-present `/.qg_last_passed_sha`. **STILL
      PENDING**: the canonical `.gitignore` template (`scripts/propagation/templates/gitignore-python.txt` — verified
      2026-06-03 it carries NEITHER sentinel) + roll-out to the remaining ~22 service repos. Repo: unified-trading-pm
      (template) + remaining ~22 service repos. Provenance: alerting drift triage + slot-4 PM dirty-tree audit this
      session.

## Design decisions (this session)

1. **Commit = the per-repo quality boundary.** A commit may only be made from a `quality-gates.sh`-green tree (lint +
   codex + unit + types), so any committed work is already per-repo-validated. Today this holds for the quickmerge path
   (Pass-1 QG → Pass-2 quickmerge commits) but NOT for direct `git commit` (Commit+Push+Flip), which only gets the light
   prek hook (ruff/format/gitleaks/conventional-commit). Decision: unify — **all** commits require full-QG-green first,
   leaning on the existing **QG-sweep batching** rule so it isn't per-commit-expensive.
2. **Staging/SIT stays the cross-repo integration gate** (unchanged). The commit-gate covers per-repo correctness only;
   a locally-green commit can still break a downstream repo — that's what staging/SIT catches. Layering preserved.
3. **FF-push to LDR = NARROW LAST-RESORT, not a routine path (operator framing 2026-06-03).** Primary stays: agents
   **quickmerge** finished units → staging PR (gated); for substantial work, always a PR. The **alert→auto-PR /
   auto-merge / promotion automation is already substantially built** in PM `.github/workflows/`:
   `ldr-to-staging-promote.yml` (Tier C — drains committed-LDR → staging), `ci-failure-watcher.yml` (stuck-PR poller +
   alerts, cron `*/15`), `escalate-to-orchestrator.yml` + `conflict-resolution-agent.yml` (auto-triage/resolve),
   `auto-merge-minor-fixes.yml`, `main-backmerge-to-ldr.yml`. The cron FF-push fills only the remaining gap — a
   **QG-green** commit an agent made but didn't quickmerge, sat clean >1h → FF-push to LDR, where the **existing Tier C
   bot then promotes it to staging** (still gated). So the HARD-RULE carve-out is NARROW (last-resort drain of QG-green
   stranded commits), **not** a routine direct-push loosening — only ahead-only/clean/aged, FF-only (lossless). Still
   NEEDS-RATIFICATION for the carve-out wording, but small blast radius. The auto-PR automation's remaining wiring is
   owned by cicd_contract_hardening (escalate @127/929, auto-merge @1138) — cross-link, don't duplicate.

## Action items — doc/rule/codex alignment (precise edits)

### Reconcile the QG-timing inconsistency (commit-prereq) — SAFE (tightening; fixes existing drift)

- [ ] [DOC] P1. **CLAUDE.md** (canonical `cursor-configs/CLAUDE.md`) "Quality gates BEFORE quickmerge" → reframe as
      "Quality gates BEFORE **commit**" (no commit to the workspace branch until `quality-gates.sh` exit 0 on HEAD; then
      quickmerge commits+PRs). Reconciles with SUB_AGENT_MANDATORY_RULES which already says commit-prereq.
- [ ] [DOC] P1. **codex/08-workflows/ci-cd-flow.md** § "Two-Pass Workflow Model" — same reframe (QG before commit, not
      just before quickmerge); state the commit is the per-repo quality boundary.
- [ ] [DOC] P2. **SUB_AGENT_MANDATORY_RULES.md** — already commit-prereq; add the explicit "commit only from a QG-green
      tree (full `quality-gates.sh`, not just the prek hook); use QG-sweep batching" sentence.
- [ ] [DOC] P2. **codex/06-coding-standards/quality-gates.md** — note the commit-as-quality-boundary framing + that the
      prek hook is the LIGHT gate, full QG is the commit-prereq.

### FF-push slot→LDR — PROPOSED, ratify before shipping (loosens a HARD RULE)

- [ ] [INFRA] P2. **[NEEDS-RATIFICATION]** Extend `scripts/dev/slot-cron-ff-pull.sh` to FF-push clean / >1h-old /
      ahead-only (0-behind) slot commits to LDR (generalize the ping-flush block; FF-only; retry-on-race). Makes the
      uta-style straggler self-resolve. **Placement = the symmetric slot-host cron stack** (per the "Local slot host =
      VM slot host" HARD RULE): one SSOT script in PM, run every 5 min on EVERY slot host — the agent-orchestrator's VM
      worker slots, the operator laptop, Harsh's laptop — so each host drains its OWN slots' stranded QG-green commits
      (no central pusher; symmetric, verified by `verify-slot-host-symmetry.sh`). Composes with agent_orchestrator_e2e
      (worker-slot model) + the per-tab-worktrees SSOT. **Makes the slot-host cron bidirectional**: today it is
      pull-only (`slot-cron-ff-pull.sh` FF-pulls incoming); background/spawned worker agents need the PUSH side too —
      FF-pull to stay current AND FF-push the QG-green work they commit, else their commits strand on the worker's tab
      branch exactly like the uta re-lock did. A background worker that finishes + moves on (no interactive operator to
      quickmerge) is the canonical strander this closes.
- [ ] [DOC] P2. **[NEEDS-RATIFICATION]** Reconcile the "Never raw `git push` for CODE" HARD RULE in CLAUDE.md +
      SUB_AGENT_MANDATORY_RULES.md + ci-cd-flow.md to carve out the cron FF-push of QG-green committed work (exact
      wording drafted; gap-analysis line anchors in the session notes). **Do NOT edit the HARD RULE until operator
      ratifies decision 3.**

### Residual

- [ ] [DEPS] P3. **unified-trading-api** re-lock commit (1 trivial metadata-sync, 0 version moves) — race-blocked by the
      ci_status bot on uta's LDR; lands via the FF-push cron (once shipped) or a quiet-window FF push.

## Cross-links (do NOT duplicate — these items live in the named plans)

- **cicd_contract_hardening_2026_06_01.md**: per-repo QG-debt greening (Phase 6) ← amplified by the governor fix here;
  `pyjwt`→2.13.0 fleet bump (its line ~350) composes with the uv re-lock sweep; manifest/DAG worktree-dirty churn (its
  lines ~678 / ~1109 / ~1201) is the same prettier/regen churn this session worked around — its structural fix (untrack
  generated SVG + ci_status sidecar) would remove the churn that complicated reconciliation here.
- **agent_orchestrator_e2e_workflow_and_execution_scope_2026_06_02.md**: G6 (AO staging branch + standard
  tab→LDR→staging→main flow) shares the commit/push model; the commit-as-quality-boundary rule applies to AO too once G6
  lands its quickmerge path.

## LDR-protection resolution (2026-06-03) — docs reconciled

- [x] [DOC] **RESOLVED + reconciled across docs**: LDR is the **unprotected integration axis** (no required-check
      ruleset) — best practice. The enforced `quality-gates-v2` check fires at the **staging/main PR** (promotion
      boundary); **local QG + sentinel is the agent + quickmerge pre-flight** (fail-fast), not a server gate.
      Reconciled: `cicd_contract_hardening` goal-line ("runs+green across branches; required ruleset on main, LDR
      unprotected") + its reconcile-todo marked RESOLVED; canonical `CLAUDE.md` "Merge Prerequisite" rule clarified
      (local pre-flight vs staging/main server gate; default-branch must be `main`); `ci-cd-flow.md` reinforced.
      **Root-cause code fix shipped**: `verify_branch_protection_check_names.py` now asserts `default_branch == main`
      fleet-wide (uta+greeks were `live-defi-rollout` → fixed to `main`; `~DEFAULT_BRANCH` ruleset no longer lands on
      LDR). ⇒ **the FF-push design (decision 3) holds** — raw/FF-push to the unprotected LDR is viable.

## Success criteria

- Canonical docs agree: commit is the per-repo quality boundary (no more merge-vs-commit-prereq drift).
- (If ratified) slot FF-push cron drains clean/aged/ahead-only commits to LDR; no more uta-style stranding.
- The governor-unmasked per-repo QG debt is tracked + greened via cicd Phase 6 (cross-linked, not duplicated).

## Conflict-resolution + convergence model — Option-B follow-on (design locked 2026-06-03)

> **Convergence model (confirmed — mostly already built).** LDR = fast live integration (agents work here, allowed
> temporarily inconsistent); the gated **main PR is the reconciliation point** (under Option B, PM's main does for plans
> what staging does for service repos); `main-backmerge-to-ldr.yml` feeds reconciled main→LDR on every main push
> (additive merge, never force/drop) → FF-pull cron (≤5 min) converges every host (other VMs + laptops). **Three
> conflict layers, no race:** TEXTUAL merge = conflict-resolution-agent; SEMANTIC = per-VM `review.md` + the new
> cross-plan detector; HYGIENE = plan-health-agent (scripted + Haiku, report-only).

- [ ] [SCRIPT] **P0 PREREQUISITE (blocks the whole escalation pipeline — discovered 2026-06-03).** The GHA→orchestrator
      bridge is **auth-dead**: `ORCHESTRATOR_INTERNAL_SECRET` is **NOT in PM's Actions secrets** (PM has GH_PAT /
      ANTHROPIC / SLACK / GCP_SA but not it), and `escalate-to-orchestrator.yml`'s only run (2026-06-03T09:57,
      repository_dispatch) **FAILED**. So **no** alert can reach the orchestrator today — this is the real root of the
      operator-blindness, not the wiring. Fix: read the canonical `ORCHESTRATOR_INTERNAL_SECRET` off the central
      orchestrator VM (`i-007e8d99d12831578`, via SSM — it lives in the server env, not GCP/AWS SM) and set it as a PM
      Actions secret so it MATCHES what the server validates. Until this lands, the two P1 wirings below escalate into a
      void. repo: unified-trading-pm (+ orchestrator VM read).
- [ ] [SCRIPT] P1. **conflict-resolution-agent → Max-plan worker (drop API credits).** _(blocked on the P0 above)_ Today
      it runs `claude-code` in-GHA via `ANTHROPIC_API_KEY_CICD` (`conflict-resolution-agent.yml:296/305`). Conflict
      resolution is the HARD judgment task + must not be pay-per-call API. Route via `escalate-to-orchestrator.yml`
      (`POST /api/escalate`, type=merge_conflict) → orchestrator spawns a setup-token Max worker → resolves on LDR;
      remove the in-GHA API path. repo: unified-trading-pm.
- [ ] [SCRIPT] P1. **Every Slack-alert event ALSO pings the orchestrator → it delegates (operator-blindness fix,
      operator 2026-06-03).** Operator doesn't always watch #ci-failures, so every alert must reach the orchestrator,
      which delegates to the owning slot / review-agent / epic-VM. Gaps: (a) `main-backmerge-to-ldr.yml` conflict →
      opens a HUMAN PR only (`:95` "no auto-resolve") → ADD orchestrator escalation (autonomous main↔LDR reconcile); (b)
      `ci_failure_watcher.py` escalates only CONFLICT stuck-PRs (`conflict_prs_to_escalate`) → extend to ALL failure
      classes (test/lint/coverage RED). repo: unified-trading-pm.
- [ ] [SCRIPT] P2. **Semantic cross-plan/cross-slot conflict DETECTOR (scripted-first + epic-VM decides).** Catches "two
      individually-valid plans whose WORK conflicts, no textual overlap" — which no existing layer does. (1) scripted
      overlap-detector: parse active-plan todos for declared **target surface** (repo/file/symbol), flag cross-slot
      overlaps, feed to plan-health-agent like the hygiene scripts. (2) on flag → ping the OWNING epic-VM orchestrator →
      auto-reconcile (worker) or post proposed solution + operator-block (VM chat / laptop). Reuses
      escalate-to-orchestrator + reviewer→worker→main — no new escalation path. repo: unified-trading-pm +
      agent-orchestrator.
- [x] ✅ [DOC] P1. **Lock the convergence + 3-layer-conflict + Option-B model in canonical docs** —
      unified-trading-pm@706fe8170: ci-cd-flow.md (new "PM/codex main-direct (Option B)" + "Convergence +
      conflict-resolution model" sections), CLAUDE.md (PM/codex→main directive + pointer), SUB_AGENT_MANDATORY_RULES
      (target-surface declaration + 3-layer model + check overlapping open claims). setup-workspace codex-clone removed
      in same commit.
- [ ] [SCRIPT] P2. **Finish codex-not-a-separate-repo cleanup.** Live SSOT (`workflow-templates/`) + deployed fleet
      already correct. Fixed: `scripts/templates/semver-agent.yml` (c10463f69),
      `scripts/propagation/templates/semver-agent.yml` (0ca9dc657). Remaining:
      `propagation/templates/major-bump-approval.yml` (checkout + 3 consumers + a write-back
      `cd ../unified-trading-codex` that commits BR8 → redirect to PM/codex + commit-to-PM),
      `setup-workspace-from-manifest.sh` (optional clone of the ARCHIVED codex repo → remove), + a few doc mentions
      (readiness-verifier.yml, setup.sh, \_workspace-lib.sh, compute-epic-readiness.py, check-repo-readiness.py,
      workspace-bootstrap.sh, auto-populate-tags.py — verify benign-vs-broken). repo: unified-trading-pm.
