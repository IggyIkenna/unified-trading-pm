---
doc_type: plan
title: SIT-rehome cross-repo breaking-gate has 2 verified safety/liveness gaps + 3 design issues (adversarial-caught pre-merge)
created: 2026-06-27
source:
  - plans/active/cicd_retire_staging_branch_2026_06_27.md (the SIT-rehome 6-step spec, lines 118-209)
  - scripts/cicd/ci_status_store.py (rank table + resolve_status)
  - system-integration-tests/scripts/run_cross_repo_invariants.sh (REQUIRED_SIBLINGS)
  - .github/workflows/ldr-to-main-promote-fleet.yml (the consumer/frozen-head — REVERTED, not shipped)
locked_by: live-defi-rollout
priority: P1
status: active
summary: "Adversarial verification (3 sub-agents) of the SIT-rehome STEPS 1+4+5 BEFORE landing caught two CRITICAL gaps that make the change unsafe to ship as specced: (1) liveness — once a repo is MAIN_GREEN (rank 4) the no-downgrade resolve_status REJECTS every later SIT_VALIDATED (rank 3) write, so sit_validated_tree is never re-written → the gate would jam every ldr_main repo on its 2nd breaking change FOREVER; (2) safety — the cross-repo SIT suite validates only 5 REQUIRED_SIBLINGS but the producer stamps SIT_VALIDATED on all 21 ldr_main repos, so a breaking change in any of the other 16 would get a valid SIT_VALIDATED+tree and promote UNGATED. The consumer + frozen-head were REVERTED (backed up); the inert building blocks (producer/store/get-doc/token-swap) stay shipped. Needs an operator design decision on SIT coverage before the corrected gate lands."
nature: process
asset_group: cross-asset
stage: [meta]
repos: [unified-trading-pm, system-integration-tests]
scope: [engineer, admin]
tags: [cicd, WS-L, SIT-rehome, safety-gate, breaking-detection, ldr_main]
related:
  - plans/active/cicd_retire_staging_branch_2026_06_27.md
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

# SIT-rehome cross-repo breaking-gate — verified gaps (adversarial-caught pre-merge)

## How this was found

The SIT-rehome STEPS 1+4+5 (frozen-head promote + Firestore-live consumer gate + on-block SIT dispatch) were
implemented in `ldr-to-main-promote-fleet.yml` and then **adversarially verified by 3 read-only sub-agents (safety /
liveness / mechanics) BEFORE landing** — the spec's own "adversarial-verify before landing" rule for this fleet
breaking-change gate. The review surfaced two CRITICAL gaps (both since **directly verified by reading the actual
code**) plus three real design issues. The consumer + frozen-head changes were **REVERTED** (diff backed up at
`scratchpad/fleet_promoter_step145.diff`); they were never shipped. The fleet promoter is back at its prior state.

## What stays shipped (verified INERT — nothing gates on it yet)

- **App-token jam fix** (PM@860f64d0c) — unrelated to these gaps; fixes a real live `action_required` deadlock. KEEP.
- **STEP 2 producer** (system-integration-tests@1e92c0a) — `full-workspace-sit` stamps SIT_VALIDATED+tree. INERT: the
  live consumer reads the manifest ci_status + staging tree, NOT Firestore `sit_validated_tree`, so these writes gate
  nothing today.
- **STEP 3 store** (PM@375b967) + **get-doc read primitive** (PM@f548a1b39) — INERT (only the reverted consumer reads
  them).

These are safe to leave shipped and are building blocks for the corrected design.

## CRITICAL-1 (liveness, VERIFIED) — MAIN_GREEN permanently blocks SIT_VALIDATED re-entry → 2nd-breaking-change jam

`ci_status_store.py` rank table: `STAGING_GREEN:2, SIT_VALIDATED:3, MAIN_GREEN:4`. `resolve_status` is no-downgrade:
`if rank(new) < rank(prev): return prev` (and a non-`main` branch is not authoritative). STEP 3 only persists
`sit_validated_tree` when `written == "SIT_VALIDATED"`.

Sequence: repo R promotes its 1st breaking change → v2-on-main writes `MAIN_GREEN` (rank 4), `sit_validated_tree`
cleared. R's 2nd breaking change lands on LDR. SIT validates it and dispatches `SIT_VALIDATED` (branch=live-defi-rollout)
→ `resolve_status(MAIN_GREEN, SIT_VALIDATED, ldr)` → `rank(3) < rank(4)` → stays `MAIN_GREEN` → `sit_validated_tree`
NOT written. The consumer gate (`status==SIT_VALIDATED && sit_validated_tree==LDR_TREE`) can never pass → BLOCK →
re-dispatch SIT → SIT passes → write rejected again → **infinite block.** Hits all 21 ldr_main repos after their first
promote. No natural recovery (only a FAILING or a main-branch write dislodges MAIN_GREEN).

**Fix direction (self-contained, but part of the corrected consumer):** decouple the SIT-validation fact from the
status rank — store/read `sit_validated_tree` as an INDEPENDENT field set whenever a SIT_VALIDATED dispatch arrives
(regardless of resolve_status's rank outcome), with explicit clear-on-tree-change; the gate checks
`sit_validated_tree == LDR_TREE` and `status != FAILING`, NOT `status == SIT_VALIDATED`. (Alternative: a SIT_VALIDATED
carve-out in resolve_status — narrower but conflates "main is green" with "LDR tree is SIT-validated"; the decouple is
cleaner. The rank table is also consumed by the dep-order gate + staging-to-main, so re-ranking is higher blast radius.)

## CRITICAL-2 (safety, VERIFIED) — SIT validates 5 repos but the gate would trust SIT_VALIDATED for 21

`run_cross_repo_invariants.sh` `REQUIRED_SIBLINGS = {unified-api-contracts, market-tick-data-service, features-service,
instruments-service, strategy-service}` (5) and runs ~4 cross-repo invariants (feature-DAG SSOT, cassette↔consumer
linkage, data_type canonicalization). The STEP 2 producer stamps `SIT_VALIDATED` + `sit_validated_tree` on **every**
cloned sibling (all 21 ldr_main repos). So a breaking change in any of the **16 uncovered repos** (execution-service,
ml-service, deployment-api, greeks-service, trading-agent-service, alerting-service, deployment-service,
fund-administration-service, batch-live-reconciliation-service, client-reporting-api, market-data-processing-service,
unified-trading-api, unified-trading-library, agent-orchestrator, deployment-ui, unified-trading-system-ui) gets a
genuine `SIT_VALIDATED` + matching tree and the consumer would PASS it ungated. The cross-repo gate's guarantee is a
forged certificate for 16/21 repos. **This needs an operator/design decision (see below) — it is not a quick fix.**

## HIGH (real, design-level)

- **H-ref:** I implemented a MUTABLE per-repo `promote/<repo>` ref force-updated each tick; the spec calls for an
  IMMUTABLE per-SHA `promote/<repo>/<shortsha>` ref deleted on merge. The mutable ref re-opens a (narrower) head-drift
  window if a newer non-breaking SHA force-updates the ref under an armed auto-merge PR. The corrected design must use
  per-SHA immutable refs + delete-on-merge. (No ref-deletion existed in my impl at all.)
- **H-combo:** the per-repo tree fingerprint cannot express the validated cross-repo COMBINATION — repo R validated
  against UAC v1 can promote even after UAC v2 (breaking) lands on main. The honest fix is to gate on a workspace digest
  (all sibling LDR trees) or to require the whole assembled ldr_main set to be jointly SIT-validated before promoting any
  member.
- **H-differ:** `--source-dir "${REPO//-/_}"` is a blind hyphen→underscore guess; for any repo whose package dir differs
  the differ scans nothing → `is_breaking=false` → SIT skipped entirely (a silent false-negative, output `2>/dev/null`).
  The corrected consumer must resolve source-dir from the manifest and FAIL-CLOSED (treat as unknown→require SIT) when
  the dir is absent or zero files were scanned; do not swallow the differ's stderr.

## MEDIUM / LOW (carry into the corrected impl)

- Deploy-ordering: STEP 3 store + `ci-status-update.yml` threading must be on **main** (ci-status-update runs from the
  default branch) before any consumer trusts the fingerprint, else fingerprints are silently dropped (fail-closed jam).
- Producer `-b main` clone fallback can stamp a `main` tree for a repo whose LDR clone failed; drop the fallback (SIT
  must validate LDR or fail loud).
- Firestore-unavailable → get-doc `{}` → fail-CLOSED blocks ALL breaking promotes until Firestore returns (acceptable
  degradation but needs alerting; nightly SIT is the backstop only if Firestore is up at 03:00).
- SIT monolithic (`if: success()`): one unrelated repo's broken invariant blocks SIT_VALIDATED for everyone → add
  per-invariant isolation / an operator manual-stamp escape hatch.
- Pre-existing (not mine): `gh api POST <path>` at the label-check status post is wrong syntax (`-X POST`), so the
  commit-status badge is never posted (guarded by `|| true`; no promotion risk).
- Frozen-head mechanics for the corrected impl: explicit empty-`LDR_SHA` guard; per-SHA ref delete-on-merge; stale-check
  re-dispatch should return BLOCKED/RECOVERING not PROMOTED; Slack alert when blocked_count stays high (PAT-expiry
  blindspot); de-dupe the per-repo SIT dispatch into one batch event.

## Decision required from the operator (the architectural fork)

The cross-repo breaking gate is only as strong as what SIT actually validates. CRITICAL-2 means we must choose the
guarantee:

- **Option A — Expand SIT coverage to all 21 ldr_main repos** (add per-repo cross-repo/consumer-contract invariants so
  SIT_VALIDATED is honest fleet-wide). Aligns with "every repo through the new pipeline"; substantial effort
  (per-repo contract tests). [RECOMMENDED long-term]
- **Option B — Scope the gate's trust to the 5 covered repos**; the other 16 keep the per-repo v2 gate only (a breaking
  change in them promotes on v2 alone, no cross-repo SIT). Lower effort; weaker guarantee for 16 repos; document it.
- **Option C — Workspace-digest / joint validation**: gate on the whole assembled ldr_main set being jointly
  SIT-validated (one digest), not per-repo. Strongest cross-repo guarantee; couples all promotes to one green SIT.

The liveness fix (CRITICAL-1 decouple) + H-ref (per-SHA immutable) + H-differ (source-dir fail-closed) are bundled into
whichever option, and are implementable once the coverage guarantee is chosen.

## Current state (safe)

Breaking ldr_main changes today BLOCK on the prior consumer's never-written-SIT_VALIDATED + staging-tree check (a
conservative stuck, not a leak — except the narrow pre-existing differ-error fail-open). NOT shipping the consumer keeps
this conservative state. The token-swap (shipped) independently fixes the live `action_required` deadlock.
