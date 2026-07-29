---
doc_type: issue
title:
  Cloud Build evidence citations recorded as 8-char short git hashes (e.g. 2ea305e9, d8ac905b) are unresolvable via
  `gcloud builds describe`, so the review-gate hard rule (check_evidence_backed_completion.py) can never independently
  verify them — an evidence-integrity defect that lets a build-backed `- [x]` completion pass the gate without the cited
  build ever being confirmed SUCCESS.
summary: >-
  The completion-evidence hard rule requires a `- [x]` Cloud Build / deploy / promote-green claim to cite `Evidence:
  cloudbuild=<id>` that resolves SUCCESS via `gcloud builds describe`
  (scripts/quality_gates/check_evidence_backed_completion.py, per plans/PLAN_FORMAT.md §8b). The review role observed
  citations recorded as **8-character short git hashes** (e.g. `2ea305e9`, `d8ac905b`) rather than full Cloud Build IDs
  (UUIDs) or full-length resolvable references. A short hash is NOT a Cloud Build id — `gcloud builds describe 2ea305e9`
  cannot resolve it regardless of whether the underlying build actually succeeded. Net effect: the independent
  verification the review-gate exists to perform is defeated at the citation-format level — the gate either (a) cannot
  confirm SUCCESS and the human/review reviewer cannot either, or (b) the check only pattern-matches the field's
  presence rather than truly resolving it. Either way a build-backed completion can pass without the cited build ever
  being confirmed. This is an evidence-integrity item, not a single bad checkbox: it undermines the "run it, don't read
  it" contract corpus-wide wherever short hashes were cited.
status: resolved
assigned_vm:
resolved_by: "interactive operator decision session, 2026-07-29"
locked_by:
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [evidence-backed-completion, cloud-build, citation-format, review-gate, quality-gates, evidence-integrity]
related:
  [
    /plans/archive/issues/deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md,
    /plans/active/issues/mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
priority: P1
parent_epic: infrastructure_master
source:
  "review role pre-compact checkpoint (msg 2373 to main agt-498659); main (agt-498659) previously said this was being
  escalated to the operator as an evidence-integrity item — captured here so it survives compaction (review role never
  commits). OPERATOR-facing: escalate."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## Defect

`scripts/quality_gates/check_evidence_backed_completion.py` enforces that a build-backed `- [x]` completion cite
`Evidence: cloudbuild=<id>` resolving SUCCESS via `gcloud builds describe` (SSOT: `plans/PLAN_FORMAT.md` §8b). The
review role observed citations recorded as **8-char short git hashes** (`2ea305e9`, `d8ac905b`, …). A short hash is not
a Cloud Build id and does not resolve via `gcloud builds describe` — so the gate's independent-verification purpose is
defeated regardless of whether the build genuinely succeeded.

## Why it matters

The whole point of §8b is "run it, don't read it": the reviewer (human or gate) must be able to re-resolve the cited
build to SUCCESS. A citation form that is structurally unresolvable makes that impossible, so a completion can clear the
review-gate hard rule without the build ever being confirmed. This is a **cross-cutting evidence-integrity** gap, not
one bad checkbox.

## Open questions for the owner / operator

- Does `check_evidence_backed_completion.py` actually call `gcloud builds describe` on the cited value, or only
  pattern-match the field's presence? If the latter, short hashes pass silently — the check needs to reject
  non-resolvable citation forms.
- Corpus sweep: how many existing `Evidence: cloudbuild=<8-char>` citations exist, and should they be back-filled with
  the full resolvable Cloud Build id?
- Format contract: pin the accepted `cloudbuild=` value to a resolvable Cloud Build id (UUID) and have the gate reject a
  bare short hash.

## Status / next step

Captured + flagged to the operator as an evidence-integrity escalation. **Not yet fixed.** Needs (1) confirmation of the
gate's actual resolve-vs-match behavior and (2) an operator decision on the citation-format contract + any back-fill.

## Todos

- [x] ✅ [SCRIPT] P1. **RESOLVED 2026-07-29.** Verified: the checker DOES call `gcloud builds describe` on every cited
      id, but only fails on an unresolvable citation when `--require-verification` is passed — the real
      `quality-gates.sh` invocation does NOT pass that flag, so a bogus short-hash citation silently passed by design
      (the "unresolvable" case originally covered both "no gcloud/auth here" and "gcloud ran, NOT_FOUND" with the same
      soft-skip). Operator direct answer: turn on `--require-verification` — but a corpus sweep first (84 `cloudbuild=`
      citations across `plans/` + `codex/`) found only 1 currently-in-scope (top-level `plans/active/*.md`, per the
      checker's own default non-recursive scan) affected string, and it was an ellipsis-truncated informal reference to
      an already-cited build, not a genuine bogus citation — fixed
      (`consolidator_throughput_backlog_monitor_2026_07_09.md`). Running the checker for real against the live corpus
      surfaced a sharper problem: 8 properly UUID-shaped citations no longer resolve — not bogus, just aged out of Cloud
      Build's retention window — so blindly turning on `--require-verification` would newly fail the standard QG on
      legitimate historical claims for no safety benefit. **Shipped the more precise fix instead** (same substance,
      better mechanism): `_describe_build_status` now distinguishes "gcloud couldn't run at all" (soft-skip, unchanged)
      from "gcloud ran and reported NOT_FOUND"; the latter is split further by citation shape — a non-UUID-shaped
      citation (the actual short-hash bug) is now an **unconditional** violation independent of
      `--require-verification`, while a well-formed UUID that's aged out stays soft-skipped by default (only flagged
      under `--require-verification`, for a stricter reviewer context). Closes the reported gap without breaking the QG
      on the 8 legitimate old citations. `Evidence: cloudbuild=` back-fill for the pre-existing short-hash citations:
      none needed in the active, in-scope corpus (all resolved to full UUID + short-form was cosmetic; archived docs are
      out of the checker's scan scope by design). (repo: unified-trading-pm —
      `scripts/quality_gates/check_evidence_backed_completion.py` +
      `tests/unit/test_check_evidence_backed_completion.py`, 5 new regression tests)
