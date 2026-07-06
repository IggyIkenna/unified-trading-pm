---
doc_type: issue
title: Fleet LDR→main promote was dead ~7h — a YAML break silently killed the */15 schedule (+ UTL flaky stale-status)
summary: 'Fleet-wide LDR→main promotion-lag >60m alert (8 service repos: instruments-service, market-tick-data-service, market-data-processing-service, deployment-api, deployment-service, +3) — NOT a display bug. Root cause: the fleet promoter ldr-to-main-promote-fleet.yml had a YAML parse error (an embedded python3 -c heredoc at column-0 inside a 10-space `run: |` block → ''could not find expected :'' at line 307). GitHub does NOT schedule a workflow whose file is unparseable on the default branch, so the */15 cron silently STOPPED at 2026-06-28 22:58 UTC → the fleet auto-drain was dead ~7h. CORRECTION to an earlier analysis: the promoter IS scheduled (cron 8,23,38,53) — it was not ''0 scheduled runs ever''; the schedule was YAML-killed. Compounded by UTL''s stale ci_status=FAILING (a flaky QG dep-clone failure) dep-order-holding deployment-api. Both fixed.'
status: resolved
nature: process
asset_group: cross-asset
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-service, deployment-ui, instruments-service, market-data-processing-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-29
source: [.github/workflows/ldr-to-main-promote-fleet.yml (the broken workflow — fixed LDR@7ecd7aa9c + main@3c82b6ad5), scripts/cicd/ci_status_store.py (UTL ci_status clear), plans/active/cicd_retire_staging_branch_2026_06_27.md (2026-06-29 Progress Log), plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md (unknown-delta / coverage)]
priority: P1
superseded_by: cicd_mvp_ldr_to_main_pipeline_2026_06_30.md
cadence: on-incident
verifier: gh run list --repo IggyIkenna/unified-trading-pm --workflow ldr-to-main-promote-fleet.yml (event=schedule fires + succeeds)
last_executed: 2026-06-29
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-30
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
- [x] [CICD] P1. "harden the QG dep-clone" — INVESTIGATED 2026-07-03; the stated premise does NOT hold (the
      "phantom-version → stale-deps" label was imprecise). Evidence: (a) the GHA `quality-gates-v2` dep-clone is NOT the
      flake — `clone_repo()` (python-quality-gates-v2.yml:359) shallow-clones each sibling at LDR HEAD tagless, but
      setuptools-scm does NOT `LookupError` on a tagless tree; it falls back to `0.1.devN+g<sha>` and the editable
      install SUCCEEDS every run (green UTL run 28349073534: `+ unified-api-contracts==0.1.dev1+ga10374f9f`,
      `+ unified-trading-library==0.1.dev2+gd98e65069`). The original UTL failure self-cleared on a same-commit rerun →
      a genuine transient, not a structural defect. (b) The real D13 `LookupError` surface (Cloud Build wheel + Docker
      image) is ALREADY FIXED fleet-wide and GREEN: 22 dynamic+`source="vcs"` repos carry either a `fetch-tags` step OR
      an inline authenticated `git fetch --unshallow --tags` in `extract-version` + a `0.0.0.dev0` PEP-440 sentinel
      (never `LookupError`); recent Cloud Builds for instruments/MTDS/execution = SUCCESS. → No structural dep-clone
      flake to harden; the recurring D13 root is mitigated. Recurrence-prevention shipped as P3.
- [x] [CICD] P3. D13 version-resolution regression gate SHIPPED — PM@f838b76c5 (PR #796). New per-repo QG
      `scripts/quality_gates/check_scm_version_resolution.py` (wired into `base-service.sh`; resolves the repo via
      git-toplevel since base-service.sh is sourced before quality-gates.sh sets REPO_ROOT) FAILS LOUD if a
      dynamic+`source="vcs"` repo has a `python -m build` cloudbuild step OR an editable `pip install -e .` Dockerfile
      WITHOUT tag/pretend-version resolution (`--tags` / `fetch-tags` / `SETUPTOOLS_SCM_PRETEND_VERSION` / `0.0.0.dev0`
      sentinel / `FROM unified-trading-library` base). Zero-FP verified across all 25 repos (both `python -m build`
      forms; Surface-2 base-image-inheritance-aware); `SCM_VERSION_GATE_WARN=1` escape valve. The surgical rollout
      appliers (`patch_cloudbuild_fetch_tags.py` + `patch_dockerfile_scm_version.py`) committed as tracked tooling. This
      is the only durable recurrence-prevention given there is no cloudbuild/Dockerfile template SSOT. Real-CI
      confirmation pending (watch a repo's quality-gates-v2 for the `scm-version-gate` line).
- [x] **P2 — workflow-YAML gate on PM `.github/` workflows (DONE — PM@94391e2e7).**
      `scripts/quality_gates/     check_workflow_yaml_valid.py` (wired into `scripts/quality-gates.sh` after the
      workflow-template-parity check) FAILS QG on any unparseable `.github/workflows/*.yml` (`yaml.safe_load`) — the
      exact incident class is now caught pre-merge; actionlint runs as an informational deeper lint (non-blocking, to
      avoid pre-existing style noise). Tested: passes on the fixed file, exits 1 on the re-injected col-0 break.
- [ ] [CICD] P2. deployment-ui + agent-orchestrator `unknown-delta`. TS / differ-source-dir → they promote only via the
      auto-dispatched SIT (coverage flipped 21/21, `7e0177e1e`) or need genuine SIT invariants (no forged manifest
      edits). Cross-ref `sit_rehome_safety_gate_gaps_2026_06_27.md`.
