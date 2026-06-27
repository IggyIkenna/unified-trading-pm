---
doc_type: issue
title:
  admin force-sync landed RED + divergent content on main → deadlocked LDR→staging drain + conflicted staging→main
  promotion (deployment-service, 2026-06-24)
summary:
status: open
nature: notes
stage: [meta]
repos: [deployment-api, deployment-service, ibkr-gateway-infra, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-24
parent_epic: infrastructure_master
priority: P1
source:
  [
    "2026-06-24 incident — deployment-service main RED CRITICAL (ci-status-update refiring every ~12 min);
    operator-directed live remediation (slot-3, laptop, owner creds)",
    "deployment-service@32facd6 (chore: admin force-sync, the trigger) · fix 040d27d (noqa TID251) · PR #265 (manual
    LDR→staging unblock) · PR #266 (staging→main conflict resolved via -s ours) · main green @636a456",
  ]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
asset_group: cross-asset
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

An `admin force-sync` (commit `chore: admin force-sync`, deployment-service@`32facd6`) pushed **RED + divergent content
onto `main`**, which cascaded into a self-sustaining, multi-repo promotion deadlock:

1. **main went RED.** The force-synced content failed the STEP 5.95 ruff ratchet (`tid251: 14 > baseline 13`) — a new
   `import boto3` in `scripts/vm/vm_zombie_watchdog_aws.py` whose `# noqa: TID251` fix had been written locally but
   **never shipped**. `quality-gates-v2` on `32facd6` recorded `ci_status=FAILING`.

2. **The LDR→staging drain deadlocked.** `ldr-to-staging-promote`'s Tier-A gate reads the repo's cached
   `ci_status=FAILING`. Because LDR never re-runs v2 on its own (LDR-trunk decoupling), the status could never refresh →
   the fix sitting on LDR could never promote to staging → main could never go green → `ci_status` stayed FAILING.
   Self-sustaining: `BLOCK: Tier A — deployment-service LDR CI is FAILING`.

3. **The staging→main promotion conflicted.** Once the fix was force-promoted to staging, the staging→main PR (#266) was
   `CONFLICTING`: main's lone divergent commit (`32facd6`) clashed with staging on 7 files; `git` reported main
   `ahead_by:1, behind_by:26` (diverged).

4. **Blast radius — 4 repos.** The FAILING `deployment-service` dep-order-blocked **deployment-api (+316)**,
   **instruments-service**, and **ibkr-gateway-infra** from promoting (they require
   `deployment-service ≥ STAGING_GREEN`). One stuck repo jammed its whole dependent tier.

**Manual remediation (operator-directed, slot-3):** shipped the noqa fix to LDR via quickmerge (`040d27d`); opened a
manual **LDR→staging PR #265** (v2-gated) to bypass the stale-FAILING Tier-A gate → merged; resolved **PR #266**'s
staging→main conflict with a content-preserving `git merge -s ours origin/main` (kept staging's SSOT tree byte-for-byte,
**no force-push to `main`**; allowed because `staging` has `enforce_admins:false`) → #266 merged; main v2 green at
`636a456` → CRITICAL cleared, dependents unblocked.

## Why it matters

A **single bad force-sync deadlocked the entire promotion tier (4 repos) with no automatic escape** — it took manual
owner intervention across two promotion hops to recover. Two distinct systemic gaps enabled it:

1. **Force-sync has no green pre-check.** `admin-force-sync-all-to-main.sh` (and any force-sync path) can land RED
   content directly on `main`, which both reds the branch and — via the Tier-A gate — deadlocks all promotion behind it.

2. **The Tier-A gate trusts a cached `ci_status` that LDR can never refresh.** Once a (now-superseded) main commit sets
   `ci_status=FAILING`, and LDR never re-runs v2, the FAILING verdict is **permanent** — there is no escape for a
   "stale-FAILING whose commit is no longer the branch tip." This is the core of the deadlock. Composes with CLAUDE.md §
   "LDR is the SSOT" and § "Force-push vs let-CI/CD".

## Recommended decision

- [ ] [INFRA] P1. **Force-sync green pre-check** — `admin-force-sync-all-to-main.sh` (+ any force-sync path) MUST verify
      the synced content is QG-green (a v2 / `.qg_content_sentinel` check on the target SHA) **before** landing on
      `main`; refuse to force-sync RED content. Target repo: `unified-trading-pm` (`scripts/`) + the force-sync
      workflow.
- [ ] [INFRA] P1. **Drain escape for stale-FAILING** — the `ldr-to-staging-promote` Tier-A gate must not be permanently
      blockable by a cached FAILING whose commit is no longer the branch tip. Either (a) auto-trigger a v2-on-LDR to
      refresh `ci_status` when the FAILING commit ≠ current main tip, or (b) treat a FAILING status as **stale** when
      LDR content differs from the FAILING SHA and re-evaluate from LDR. Target: `unified-trading-pm`
      `ldr-to-staging-promote` + the ci_status / Tier-A logic.
- [ ] [INFRA] P2. **Document the divergence runbook** — when `main` diverges from a force-sync, the canonical resolution
      is the operator-gated clean-start force-sync to the LDR SSOT, **not** leaving a conflicting staging→main PR.
      Record the non-force-push alternative used in this incident (a content-preserving `git merge -s ours origin/main`
      on the head branch when `enforce_admins:false`) as the in-bounds manual escape. Target:
      `codex/08-workflows/ci-cd-flow.md` § "LDR is the SSOT" / § "Force-push vs let-CI/CD".
