---
doc_type: issue
title: quickmerge.sh's own internal comment blocks describe 3 different, mutually contradictory routing models
summary: >-
  A /docs-reconcile doctrine-consistency sweep (2026-08-21) found scripts/quickmerge.sh — the single most
  load-bearing shipping script in the workspace — carries THREE different self-descriptions of its own
  routing model across its header comment, a mid-file code comment, and its own runtime echo message, and
  they disagree with each other and with CLAUDE.md's current statement. AGENTS.md + 2 .cursor/rules/*.mdc
  files were independently found stale in the same pass (already fixed, see Progress Log) — but this
  finding is about quickmerge.sh's OWN internal comments, which this session deliberately did NOT edit
  without a human/dedicated pass confirming the true current model, given how consequential a wrong edit
  to this specific script's documentation would be.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, quickmerge, shipping-pipeline, ldr, staging, doctrine-consistency, self-contradiction]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /AGENTS.md,
    /.cursor/rules/core/always-use-quickmerge.mdc,
    /.cursor/rules/dependencies/breaking-change-major-version-protocol.mdc,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: human
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: fix
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    scripts/quickmerge.sh,
    /codex/08-workflows/ci-cd-flow.md,
    /cursor-configs/CLAUDE.md,
  ]
source: >-
  /docs-reconcile Phase 1, doctrine-consistency hunter, 2026-08-21 — found while checking AGENTS.md /
  .cursor/rules against CLAUDE.md's current shipping-pipeline statement for the cross-agent-instruction
  gap this skill exists to catch.
---

# quickmerge.sh's own internal comments contradict each other on the LDR promotion model

## What was found

Three distinct self-descriptions of the routing model coexist inside `scripts/quickmerge.sh`:

1. **Header comment (lines 10-38)**: describes a "staging-first" model — "ALL human commits → staging →
   semver-agent validates → SIT → main". This predates the LDR migration and appears to be the OLDEST,
   most stale of the three.
2. **Mid-file code comment (~lines 3471-3480, `LDR-TRUNK MODEL` block, cites
   `ldr_trunk_promotion_decoupling_2026_06_10`)**: describes "a normal service-repo commit LANDS ON LDR
   AND STOPS. The Tier-C drain (`ldr-to-staging-promote`, every 15min) promotes LDR→staging in tier
   order..." — i.e. LDR promotes to STAGING, not main, every 15 minutes.
3. **The script's own runtime echo message (~line 3467, inside the `--hotfix`-on-`ldr_main`-repos guard)**:
   "This commit already landed on `$BRANCH` (LDR trunk) and will promote via `ldr-to-main-promote-fleet.yml`
   (~15min SLA)" — i.e. LDR promotes DIRECTLY to main, not staging.

**CLAUDE.md's current statement** (`cursor-configs/CLAUDE.md` § "Git discipline + shipping pipeline",
which this session treats as the authoritative live synthesis) matches description (3): "quickmerge lands
on LDR; default promote is LDR→`main` DIRECT — staging DORMANT... via `ldr-to-main-promote-fleet.yml` +
`ldr-to-main-promote.yml`, `*/30`, auto-merge... staging KEPT + REVERSIBLE (major/breaking bump or
operator decision routes THROUGH it; gates unchanged)."

So (1) and (2) both appear to be stale comments describing an earlier iteration of the promotion
mechanism, never updated when the script's actual behavior (and CLAUDE.md's documentation of it) moved to
the current LDR→main-direct model. But this session did NOT edit `quickmerge.sh` itself to fix them —
editing the comments in the single most load-bearing shipping script in the workspace on inference alone,
without confirming against a fresh read of the FULL surrounding code (which repo type dispatches through
which promotion path — `promotion_model: ldr_main` vs a legacy repo, per CLAUDE.md's own
`promotion_model` toggle), risked introducing a confidently-wrong description that would be worse than
the current honestly-ambiguous one.

## Why it matters

Any agent or human reading `quickmerge.sh`'s header comment for a quick "how does shipping work here"
answer gets an entirely retired model (staging-first). Anyone reading the mid-file LDR-TRUNK MODEL comment
gets a DIFFERENT wrong answer (LDR→staging every 15min) that contradicts the script's own live runtime
message a few lines later (LDR→main direct). This is exactly the failure class `/docs-reconcile` exists to
catch — but for the ground-truth script itself, not just its downstream doc mirrors.

## Recommended next step

A dedicated pass (not a docs-reconcile sub-agent working blind) should: (1) read the FULL current
promotion logic in `quickmerge.sh` end to end (not just the two comment blocks) to determine definitively
which of "staging-first" / "LDR→staging every 15min" / "LDR→main direct" is the TRUE current behavior for
each `promotion_model` value; (2) update the header comment (lines 10-38) and the LDR-TRUNK MODEL comment
block (~3471-3480) to match, deleting whichever description(s) are confirmed stale; (3) re-verify
AGENTS.md / the 2 `.cursor/rules/*.mdc` files this session already fixed (see Progress Log) still agree
once the ground truth is nailed down.

## Todos

- [ ] [DOCS] P2. Read `scripts/quickmerge.sh`'s full promotion-routing logic (not just the comment blocks)
      and determine definitively which promotion model is currently true for `promotion_model: ldr_main`
      repos vs any legacy/non-`ldr_main` repo. Update the header comment (lines ~10-38) and the
      `LDR-TRUNK MODEL` comment block (~lines 3471-3480) to a single, internally-consistent, currently-true
      description — delete the stale ones rather than layering a fourth. Cross-check against
      `cursor-configs/CLAUDE.md`'s current statement and `/codex/08-workflows/ci-cd-flow.md`; update either
      if the fresh code read reveals CLAUDE.md itself is stale. Done when: `scripts/quickmerge.sh` contains
      exactly one routing-model description, matches the script's actual live behavior, and matches
      CLAUDE.md (or CLAUDE.md is corrected to match, whichever is actually true). Repo: unified-trading-pm.

## Progress Log

- **2026-08-21 (docs-reconcile Phase 1/3)**: found via the doctrine-consistency hunter's sweep. In the
  same pass, fixed the downstream/lower-risk copies of this same stale doctrine in `AGENTS.md` (2 spots)
  and `.cursor/rules/core/always-use-quickmerge.mdc` + `.cursor/rules/dependencies/breaking-change-major-version-protocol.mdc`
  (3 spots) to match CLAUDE.md's current statement — but deliberately left `scripts/quickmerge.sh` itself
  untouched pending a dedicated read of its full routing logic, since its own three self-descriptions
  disagree with each other and a docs-reconcile pass editing on inference risked making it worse, not
  better.
