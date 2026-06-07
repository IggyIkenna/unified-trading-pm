---
title: major-bump-issue-handler.yml actionlint untrusted-input fails QG step 5.5 fleet-wide (blocks A11c-candle-enum)
created: 2026-06-07
author: ikennaigboaka [slot-7·laptop]
source:
  - plans/active/defi_manifest_canonicalisation_2026_06_01.md (A11c-candle-enum)
  - plans/active/cicd_contract_hardening_2026_06_01.md (live cicd track; successor of the archived
    cicd_hidden_fragility_audit_2026_06_05.md)
  - unified-trading-pm/scripts/quality-gates-base/base-service.sh (§ [5.5] WORKFLOW LINT)
locked_by:
---

## What I found

The PM-templated workflow `major-bump-issue-handler.yml` uses untrusted GitHub event context **directly inside `run:`
blocks**:

- `${{ github.event.comment.body }}` (template line ~46 / propagation copy ~39)
- `${{ github.event.issue.body }}` (template line ~103 / propagation copy ~96)

`quality-gates.sh` step **[5.5] WORKFLOW LINT** runs `actionlint` when it is installed and treats its
untrusted-`github.event.*`-in-`run:` rule as **STRICT / fatal** (`base-service.sh:1529` → `log_fail` + `exit 1`; the
surrounding comment explicitly keeps that rule strict by design). So on any host/CI image that has `actionlint`, the
gate exits non-zero for **every repo that carries this workflow** — the `.qg_last_passed_sha` / `.qg_content_sentinel`
are never written, and `quickmerge` then hard-refuses.

The defect lives in the **template SSOT** (`scripts/workflow-templates/major-bump-issue-handler.yml` AND
`scripts/propagation/templates/major-bump-issue-handler.yml`), so it is the same in every per-repo copy. Confirmed
pre-existing on clean `origin/live-defi-rollout` HEAD of market-data-processing-service (only `models.py` was dirty when
found).

Entanglement: these same `major-bump-issue-handler` / `request-major-bump` / `update-dependency-version` templates
already carry **63 un-rolled-out drift** from an in-flight Telegram→Slack migration (documented in the now-archived
`cicd_hidden_fragility_audit_2026_06_05.md` → migrated to `cicd_contract_hardening_2026_06_01.md`). A naive
`rollout-workflow-templates.sh` would also push that unrelated, un-reviewed migration fleet-wide, so the actionlint fix
must be coordinated with (or land as part of) that pending rollout — not bolted on by an unrelated task.

## Why it matters

It silently **blocks `quickmerge` for every affected repo** whose local pre-flight (or CI `quality-gates-v2`) runs
`actionlint`. Concretely it blocks **A11c-candle-enum** (`defi_manifest_canonicalisation_2026_06_01.md`): the UAC
`candle_schema.DataType` change removes `DEX_SWAPS`, so UAC + market-data-processing-service must promote in lockstep
(MDPS imports `DataType` and would `AttributeError` against the new UAC image otherwise) — and MDPS cannot get a green
sentinel until this actionlint failure is resolved. The A11c code itself is complete and otherwise-green (UAC
`quality-gates.sh` PASSED; MDPS passes every substantive step except this unrelated [5.5] workflow-lint).

## Recommended decision

1. In the PM template SSOT (both `workflow-templates/` and `propagation/templates/` copies), move the untrusted event
   context into a step `env:` and reference the env var inside the `run:` script, e.g.:
   ```yaml
   env:
     COMMENT_BODY: ${{ github.event.comment.body }}
   run: |
     BODY=$(cat << 'BODYEOF'
     $COMMENT_BODY
     BODYEOF
     )
   ```
   (and the same for `github.event.issue.body`). This is the actionlint-sanctioned script-injection mitigation.
2. Land it **with / as part of** the pending Telegram→Slack template rollout (so the `rollout-workflow-templates.sh` run
   carries both, with the migration reviewed) — owner = the cicd track (`cicd_contract_hardening_2026_06_01.md`).
3. On rollout completion, A11c-candle-enum unblocks: re-apply the A11c edits (recipe is in the plan's A11c-candle-enum
   steps; the verified diff is also parked in slot-7 stashes — UAC `stash@{0}` + MDPS `stash@{0}`, message
   `A11c-candle-enum WIP (BLOCKED-CICD 2026-06-07)`), re-run UAC + MDPS `quality-gates.sh`, quickmerge both in lockstep,
   flip A11c.

Operator-acked 2026-06-07 (decision: leave A11c BLOCKED-CICD; do not bundle the fleet template rollout into the enum
cleanup).
