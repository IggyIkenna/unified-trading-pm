---
doc_type: issue
title: "LDR→main promotion machinery — consolidated findings + doc contradictions (2026-06-29, for Ikenna escalation)"
created: 2026-06-29
source:
  - .github/workflows/ldr-to-main-promote-fleet.yml
  - system-integration-tests/.github/workflows/full-workspace-sit.yml
  - scripts/cicd/detect_breaking_change.py
  - plans/active/issues/ldr_main_label_check_false_block_promotion_stall_2026_06_29.md
  - plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md
  - plans/active/issues/fleet_promote_schedule_yaml_break_2026_06_29.md
  - plans/active/cicd_sit_full_coverage_handoff_2026_06_27.md
assigned_vm: NA
status: active
priority: P1
summary:
  "Single consolidated record of every finding from the 2026-06-29 LDR→main promotion-stall investigation, classified by
  whether it is already tracked (and where) or NEW/untracked, with evidence and current status — plus the contradictions
  these findings create with current docs. The systemic root cause of the broad delay was a legacy `promote/<repo>` ref
  D/F-conflict freezing per-SHA ref creation on 15/21 repos (NEW, now fixed). Several related issues were already known
  from the 2026-06-27 SIT-rehome adversarial review, but that doc is now STALE (says the gate is 'reverted/inert' when it
  is in fact live + gating). For Ikenna to review when free."
nature: process
asset_group: cross-asset
stage: [meta]
repos:
  - unified-trading-pm
  - system-integration-tests
  - instruments-service
  - features-service
  - market-tick-data-service
  - unified-api-contracts
  - agent-orchestrator
  - deployment-ui
  - execution-service
  - deployment-service
  - unified-trading-library
scope: [engineer, admin]
tags: [cicd, promotion, ldr-main, sit-rehome, breaking-detection, promote-ref, label-check, escalation, doc-contradiction]
related:
  - plans/active/issues/ldr_main_label_check_false_block_promotion_stall_2026_06_29.md
  - plans/active/issues/sit_rehome_safety_gate_gaps_2026_06_27.md
  - plans/active/issues/fleet_promote_schedule_yaml_break_2026_06_29.md
  - plans/active/cicd_sit_full_coverage_handoff_2026_06_27.md
  - plans/active/cicd_retire_staging_branch_2026_06_27.md
  - plans/active/cicd_consolidated_remaining_2026_06_24.md
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-29
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# LDR→main promotion machinery — consolidated findings + contradictions (for Ikenna)

> **Purpose.** During a 2026-06-29 investigation of "9 repos with real un-promoted content," a chain of stacked bugs in
> the LDR→main promotion machinery was found and mostly fixed. This doc consolidates **every** finding in one place,
> marks which are **already tracked** (and where) vs **NEW/untracked**, and lists the **contradictions** these create
> with current docs. Escalated for Ikenna (CI/CD owner) to review and decide the durable code fixes.
>
> **One-line root cause of the broad delay:** 15/21 `ldr_main` repos carried a leftover legacy `promote/<repo>` git ref;
> the per-SHA promote-ref scheme (`promote/<repo>/<sha>`) can't create its ref while that exists (git D/F conflict → HTTP
> 422), so the fleet promoter opened **0 PRs**. NEW + now fixed (15 refs deleted). The rest are secondary/per-repo.

## ROOT CAUSE I AM FLAGGING (read this first)

Two levels — an immediate systemic cause and a deeper meta-cause:

1. **Immediate (mechanical) root cause of the broad delay — finding B-5.** 15/21 `ldr_main` repos carried a leftover
   legacy `promote/<repo>` ref. The per-SHA promote-ref scheme (`promote/<repo>/<sha>`, live since 2026-06-28) cannot
   create its ref while that legacy ref exists (git directory/file conflict → HTTP 422), and the bot's cleanup never
   deletes it. So the fleet promoter passed every gate and then **failed at ref creation on every repo** → opened **0
   PRs** (verified: the 13:51 scheduled run logged `Promoted (0)`). Every promote today happened only because it was
   manually driven. **This is THE reason the fleet wasn't draining.** Now fixed (15 refs deleted); the code follow-up to
   harden the cleanup is open.

2. **Deeper (process) root cause — why so many latent bugs surfaced at once.** The WS-L LDR→main gate (per-SHA refs, SIT
   producer/stamp, breaking-differ, label-check, combination digest) was **shipped to production live and gating**, but
   the tracking docs still describe it as **"reverted / inert / intentionally inactive"** (contradictions C-1 and C-5).
   Because everyone believed it was off, a fragile, live, multi-component pipeline had **no owner watching it and was
   never exercised end-to-end** — so each component went live carrying a latent bug that only fires on the real path:
   the SIT producer never ran (so its invalid YAML, B-3, was invisible); the per-SHA refs never created against repos
   with legacy refs (B-5); the label-check never saw a real mixed-bump range (B-8); the combination digest never met
   live churn (B-9); and a stale armed PR could delete a branch (B-7). **The doc-vs-reality drift ("inactive" when live)
   is the meta-root-cause** — it is why these weren't caught and why they accumulated. Fixing the docs (C-1/C-3) and
   adding end-to-end exercise of the promote path is as important as the individual code fixes.

## A. Findings index (tracked vs NEW; status)

| # | Finding | Tracked? | Where | Status |
|---|---------|----------|-------|--------|
| 1 | SIT gate fail-closed on missing `sit_validated_tree` | ✅ tracked | sit_rehome_safety_gate_gaps (CRITICAL-1 liveness) | FIXED (decouple shipped) |
| 2 | SIT-stamp producer stranded off SIT default branch | ◑ partial | sit_rehome (STEP 2 + MEDIUM deploy-order) | FIXED (PR #288/#289) |
| 3 | **YAML col-0 break in `full-workspace-sit.yml` (SIT producer)** | ❌ NEW | — (the *class* is tracked for the PROMOTER only) | FIXED (PR #289) |
| 4 | **Differ counts private `__all__` names as public API** | ❌ NEW | — (H-differ tracks source-dir, not this) | FIXED (PM@`da4dc099`) |
| 5 | **Legacy `promote/<repo>` ref D/F-conflict → 422 (FLEET ROOT CAUSE, 15/21 repos)** | ❌ NEW | — | FIXED (15 refs deleted); code follow-up OPEN |
| 6 | Squash-divergence backmerge can stick → blocks next promote | ◑ partial | provenance_gate_squash (archive) + ldr_main doc | per-repo reconciled; code fix OPEN |
| 7 | **`--delete-branch` on `head=live-defi-rollout` PR deletes the SSOT branch** | ❌ NEW | — | FIXED (deployment-ui recovered); guard OPEN |
| 8 | **Label-check range-asymmetry (EXPECTED=latest-commit vs COMPUTED=range-max) → false block** | ◑ was tracked, now lost | original ldr_main forward note (deleted in my rewrite) | OPEN — blocks IS, mtds |
| 9 | **SIT-combination workspace-digest thrashes under fleet churn** | ◑ partial | sit_rehome (H-combo proposed it as a *fix*) | OPEN — blocks agent-orchestrator, features-service |
| 10 | Scheduled `*/15` cron fires ~1/1.5–2h | ◑ partial | fleet_promote_schedule_yaml_break (claims resolved) | OPEN (see contradiction C-2) |
| 11 | Differ source-dir guess + UI/TS `unknown-delta` permanent block | ✅ tracked | sit_rehome (H-differ + ADDENDUM) | mitigated (21/21 coverage) |
| 12 | UAC provenance gate block (non-quickmerge code on LDR) | ✅ tracked | provenance_gate_squash (archive) | OPEN — re-ship via quickmerge |
| 13 | label-check status-post 403 (App token lacks statuses:write) | ✅ tracked | sit_rehome (MEDIUM) | benign (`|| true`) |
| 14 | UTL flaky QG dep-clone staled tier-0 ci_status (Cause A) | ✅ tracked | fleet_promote_schedule_yaml_break | OPEN P1 (Ikenna's agent) |

## B. NEW / untracked findings (detail)

### B-5 (PRIMARY) Legacy `promote/<repo>` ref D/F-conflict — froze the whole fleet
The per-SHA immutable-ref scheme (`promote/<repo>/<sha>` heads, live 2026-06-28) cannot create its ref when a legacy
no-slash `promote/<repo>` ref exists — git rejects it (`promote/<repo>` can't be both a ref and a directory) with HTTP
**422 "Reference update failed."** The bot's superseded-ref cleanup only matches `promote/<repo>/` (trailing slash), so
it never deletes the legacy ref. **15 of 21 `ldr_main` repos carried one.** Evidence: the 13:51 scheduled run logged
`Promoted (0)` with `could not create immutable promote ref … skipping (retry next tick)` on every divergent repo.
**Fixed:** deleted all 15 orphaned legacy refs (none had an open PR); the next run created PRs (execution-service #429,
deployment-service #320 merged; UAC #542 opened). **Code follow-up OPEN:** harden the cleanup to also delete the
legacy no-slash ref so this can't recur.

### B-7 (CRITICAL) `--delete-branch` deleted a repo's `live-defi-rollout`
A stale pre-frozen-ref promote PR (deployment-ui #345, head = `live-defi-rollout`, armed `--delete-branch` auto-merge)
merged at 2026-06-29 13:33:38Z and **deleted `live-defi-rollout` itself** (`DeleteEvent ref=live-defi-rollout`). No
commits lost (last tip `955140892a11`/tree `80e886b4` preserved in the frozen ref + main); branch restored + `-s ours`
reconciled. Fleet audit: all 21 repos have LDR; no other armed `head=live-defi-rollout` PR exists. **Guard OPEN:** the
promoter must never arm `--delete-branch` on a protected/long-lived head; add a recurring sweep for legacy armed PRs.

### B-3 SIT-producer YAML break + QG-gate coverage gap
`full-workspace-sit.yml`'s stamp step had two embedded `python3 -c` heredocs at column 0 (below the `run: |` base) →
YAML-invalid → GitHub rejected the workflow on SIT's `main` ("workflow file issue"), so the producer never ran. **This
is the same class** as the promoter YAML break in `fleet_promote_schedule_yaml_break_2026_06_29.md`, but the QG gate
added there (`check_workflow_yaml_valid.py`) is **PM-scoped** and does NOT validate `system-integration-tests`'
workflows — so it never guarded this file. Fixed (PR #289). **Follow-up OPEN:** extend the YAML-valid QG to the SIT repo
(and any repo carrying `.github/workflows`).

### B-4 Differ counts private `__all__` names as public API
`detect_breaking_change.py` set `surf.exports = declared __all__` verbatim, so `_CEFI_VENUES`/`_TRADFI_VENUES`
(underscore-prefixed, listed in `__all__`) counted as public exports; removing them read as `breaking`. Fixed: filter
`_`-prefixed names out of `declared_all` (PM@`da4dc099`) + regression test. (Distinct from H-differ, which is about the
source-dir guess.)

### B-8 Label-check range-asymmetry (the IS/mtds block — NOT a mislabel)
The promoter's label-check derives `EXPECTED` from **only the latest commit subject** but `COMPUTED` from the
**whole-range max bump**. When the range has an earlier `feat:` (minor) and the latest commit is a `fix:` (patch), it
false-blocks as "mislabeled." Verified: IS range latest = `fix(understat):` but contains `feat:` (venue consolidation,
NYSE enum); mtds latest = `fix(defi)/fix(tradfi)` but contains `feat(scripts)/feat(tradfi)`. **The commits are correctly
labeled — there is nothing to relabel; the check is buggy.** Fix = compute `EXPECTED` as the range-max (same as
`COMPUTED`). This asymmetry WAS noted in the original forward note of `ldr_main_label_check_…` but that note was deleted
in this session's rewrite (see C-3). The fix also belongs in `semver-agent.yml.tmpl` Step-4 (the promoter's check is a
"faithful copy" of it — keep them in sync).

### B-9 SIT-combination workspace-digest thrashes under churn
The combination gate blocks when any covered repo's LDR tree changed since SIT stamped the digest. In an actively
churning fleet the stored digest is almost always stale → block + re-dispatch SIT → re-stamp → next tick stale again. It
only converges in a quiet window. Currently blocking agent-orchestrator + features-service. `H-combo` proposed the digest
as a *fix* for the per-repo-fingerprint weakness; nobody documented that it can chronically block. Needs a
churn-tolerant design (e.g. validate against the digest at PR-open time, or a staleness tolerance).

## C. Contradictions to current docs

- **C-1 (biggest).** `issues/sit_rehome_safety_gate_gaps_2026_06_27.md` states the gate consumer + frozen-head were
  **"REVERTED, never shipped, INERT… current state safe (conservative stuck)."** This is **false now**: the corrected
  consumer (per-SHA refs, live SIT gate, combination digest, **21/21 coverage**) WAS shipped and is **live + gating
  today** — confirmed by `cicd_sit_full_coverage_handoff_2026_06_27.md:307-319` and
  `cicd_retire_staging_branch_2026_06_27.md:179` ("coverage flipped 21/21, `7e0177e1e`"). The gaps doc was never updated
  post-ship. **Recommend:** add a "SUPERSEDED — gate shipped via handoff plan" banner; its open gaps either landed
  (CRITICAL-1/2, H-ref, H-combo, H-differ) or are superseded by the NEW findings here.

- **C-2.** `issues/fleet_promote_schedule_yaml_break_2026_06_29.md` says the `*/15` schedule **"self-healed… native cron
  ticks continuing on cadence (RESOLVED)."** Contradicted by 2026-06-29 evidence: scheduled runs fired **08:47 → 10:24
  → 12:15 → 13:51** (~1 per 1.5–2h), not every 15 min. Either it re-degraded or "on cadence" was optimistic.
  **Recommend:** reopen the schedule-reliability item; consider an event-driven (push-to-LDR) trigger.

- **C-3 (self-inflicted, this session).** `issues/ldr_main_label_check_false_block_promotion_stall_2026_06_29.md`
  (Correction #2) currently says the IS/mtds label-check is *"Real label mismatch, not a bug — relabel `feat:`."* That is
  **wrong** (see B-8 — it's the range-asymmetry bug). The same rewrite **deleted** the original forward note that
  documented this asymmetry. **Recommend:** correct that doc and restore the asymmetry note (or point it here).

- **C-4.** The two 2026-06-29 docs (`ldr_main_label_check_…` and `fleet_promote_schedule_yaml_break_…`) overlap (same
  fleet stall + same UTL flaky-QG Cause A) but cite **different** YAML breaks (SIT producer vs promoter) and **disagree**
  on schedule health, and don't cross-reference each other. **Recommend:** cross-link them and this consolidated doc.

- **C-5 (already corrected).** `ldr_main_label_check_…` originally claimed the fleet promoter was "intentionally inactive
  / not in production." Corrected in-session (Correction #2): it is live + scheduled and was the active blocker. Noted
  here only because it is the **same stale-"machinery-inactive" framing** as C-1 — two docs carried it.

## D. Recommended actions (for Ikenna)

Durable code fixes (all P1 unless noted):
- [ ] [CICD] P1. B-5: harden the promoter's superseded-ref cleanup to delete the legacy no-slash `promote/<repo>` ref.
- [ ] [CICD] P0. B-7: never arm `--delete-branch` on a protected/long-lived head; recurring sweep for legacy armed
      `head=live-defi-rollout` PRs.
- [ ] [CICD] P1. B-8: fix label-check `EXPECTED` to use the range-max bump (promoter **and** `semver-agent.yml.tmpl` Step-4).
- [ ] [CICD] P1. B-3: extend `check_workflow_yaml_valid.py` (or equivalent) to cover `system-integration-tests` (+ all repos
      carrying `.github/workflows`), not just PM.
- [ ] [CICD] P1. B-9: make the SIT-combination digest churn-tolerant (validate at PR-open, or tolerance window).
- [ ] [CICD] P1. B-6: auto-resolve squash-divergence backmerge (`-s ours`) in `main-backmerge-to-ldr`.
- [ ] [CICD] P1. C-2: make LDR→main promotion not depend on GitHub's unreliable scheduled cron (event-driven trigger).
- [ ] [CICD] P1. Cause A: harden the flaky QG dep-clone (already tracked; the recurring tier-0-stale root).

Doc corrections:
- [ ] [DOCS] P2. C-1: SUPERSEDED banner on `sit_rehome_safety_gate_gaps_2026_06_27.md`.
- [ ] [DOCS] P2. C-3: fix the label-check mischaracterization in `ldr_main_label_check_…` + restore the asymmetry note.
- [ ] [DOCS] P2. C-2/C-4: correct the schedule-health claim + cross-link the 2026-06-29 docs.

Operator decisions pending:
- [ ] [OPS] P1. features-service: promote (consumer-less, version-neutral on 0.x) vs relabel `feat!:` vs defer (real public-API
      removal `extract_book_microstructure_feature_dict`, 0 cross-repo consumers).
- [ ] [OPS] P1. UAC #542: re-ship the non-quickmerge LDR commits via quickmerge to clear the provenance gate.

## E. What was already fixed this session (for context)

instruments-service PROMOTED (PR #697, tree-equal, `behind_by=0`); agent-orchestrator (#530) + deployment-ui (#346,
recovered) + execution-service (#429) + deployment-service (#320) promoted; SIT producer on SIT `main` (PR #288/#289);
differ private-`__all__` fix (PM@`da4dc099`); 15 legacy refs deleted. Detail in
`ldr_main_label_check_false_block_promotion_stall_2026_06_29.md`.

## Progress Log

- 2026-06-29: Created as the consolidated escalation record. Indexes all 14 findings (which are tracked vs NEW), details
  the 5 NEW/untracked ones (B-3,4,5,7,8,9), and lists 5 doc contradictions (C-1..C-5). For Ikenna to review + decide the
  durable code fixes; no other docs edited yet (recommendations only).
