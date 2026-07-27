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
status: open
assigned_vm:
resolved_by:
locked_by:
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [evidence-backed-completion, cloud-build, citation-format, review-gate, quality-gates, evidence-integrity]
related:
  [
    /plans/active/issues/deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md,
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
