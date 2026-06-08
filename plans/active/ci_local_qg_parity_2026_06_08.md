---
title: CI/local-QG parity — local LDR-checkout QG (dep order) is the staging oracle; divergence is a bug
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
created: 2026-06-08
orchestrated_by: plans/active/cicd_contract_hardening_2026_06_01.md
related_plans:
  - plans/active/quickmerge_dep_content_sync_and_strict_enforcement_2026_06_08.md
  - plans/active/staging_clean_start_and_stale_pr_hygiene_2026_06_08.md
  - plans/active/issues/full_cicd_sit_target_state_2026_05_24.md
source:
  - chat design session 2026-06-08 (operator + vm-planning)
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# CI/local-QG parity — local is the oracle

> **Orchestrated by** `cicd_contract_hardening_2026_06_01.md`. This is the **confidence model** that makes the whole
> reform safe: it's what lets us trust local-green and treat staging-red-after-local-green as a _bug to audit_, not a
> normal occurrence.

## Principle (operator, 2026-06-08)

> "Once QG has run everywhere in dep order on a local checkout of LDR, we can be confident staging will work too. When
> it doesn't, we audit **why CI has a different structure to local QG** — it is key they are in line."

LDR is the SSOT. A local checkout of LDR, with `quality-gates.sh` run in **dependency order** (T0 → dependents →
leaves), against **content-synced editable deps** (per `quickmerge_dep_content_sync_and_strict_enforcement`), is the
**oracle** for staging. If local is green and staging is red, **CI and local QG have diverged in structure** — that is a
defect in the parity, and it gets audited and closed, not normalized.

## Pre-audit — enumerate every place local QG and CI QG/SIT can differ

- [ ] [SCRIPT] P1. Build the parity matrix: for each gate step, does it run identically in (a) local `quality-gates.sh`,
      (b) `quality-gates-v2.yml` on staging, (c) SIT `full-workspace-sit` cross-repo invariants? Columns: which deps are
      present (editable-local vs cloned-pinned), Python/tool versions, env (`CLOUD_MOCK_MODE`), test selection
      (`PYTEST_UNIT_DIR`), `--ignore-vuln` set, the `<300s`/`MAX_DURATION` budget, and which checks are SKIPPED in each.
      This matrix IS the divergence surface.

## Phase 1 — Close the known structural divergences (depends: Pre-audit)

- [ ] [SCRIPT] P1. **The SIT delta is intentional and must stay visible**: per-repo QG has a PARTIAL dep set so
      cross-repo invariants SKIP (feature-DAG SSOT, cassette↔consumer linkage, data_type canonicalization); SIT
      assembles the FULL workspace and runs them. Make this delta **explicit + asserted** — local QG must print
      "cross-repo invariants: DEFERRED-TO-SIT (N checks)" so local-green is never mistaken for SIT-green; and a local
      `--with-sit` mode can run the assembled invariants on demand.
- [ ] [SCRIPT] P1. Any divergence found in the Pre-audit matrix that is NOT the intentional SIT-assembly delta → fix so
      the step is byte-identical local vs CI (same selection, env, tool versions, ignore-sets). Drive to: "local QG
      green in dep order ⇒ staging-v2 green" with the only residual being the assembled-SIT layer.

## Phase 2 — Make divergence self-auditing (depends: Phase 1)

- [ ] [SCRIPT] P1. Add a **parity watchdog**: when a repo is local-QG-green (LDR checkout) but its staging
      `quality-gates-v2` is red, auto-file/append an issue doc
      `plans/active/issues/ci_local_qg_divergence_<repo>_<date>.md` with the diff of which step diverged (from the
      matrix) + the run logs. Divergence becomes a tracked defect, per principle.
- [ ] [SCRIPT] P2. Wire the watchdog signal into the orchestrator alert path (every alert → orchestrator).

## Phase 3 — Dependency-order local sweep as a first-class command (depends: Phase 1)

- [ ] [SCRIPT] P1. Ship `scripts/cicd/local_qg_sweep.py` — runs `quality-gates.sh` across the workspace in topological
      dep order on the current LDR checkout, ≤2 concurrent (host governor), content-sync-gated, emitting per-repo
      green/red + the aggregate "staging-confidence" verdict. This is the operator's pre-promotion oracle.

## Success criteria

- The parity matrix exists and every non-SIT-assembly divergence is closed (proven on ≥1 consumer repo + across
  promotion branches — rule 11).
- Local-QG-green-in-dep-order on an LDR checkout reliably predicts staging-v2-green; the only documented gap is the
  assembled-SIT cross-repo layer, which local QG explicitly DEFERS rather than silently skips.
- A local-green/staging-red event auto-files a divergence issue doc.

## Codex SSOT updates

`codex/06-coding-standards/quality-gates.md` § local↔CI parity matrix; `codex/08-workflows/ci-cd-flow.md` § "local QG is
the staging oracle"; `full_cicd_sit_target_state_2026_05_24.md` cross-link (SIT = the assembled-invariant layer).
