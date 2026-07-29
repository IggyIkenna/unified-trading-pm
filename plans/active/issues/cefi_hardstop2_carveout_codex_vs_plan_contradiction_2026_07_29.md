---
doc_type: issue
title:
  "delete-safety-protocol hard-stop #2's §3a-carveout status contradicts itself same-day -- codex says qualifiable, the
  CeFi orphan-sweep plan says categorically not, both dated 2026-07-28"
summary:
  "Found while recording the operator's 2026-07-29 authorization for the CeFi ~1.2M-object orphan-sweep delete
  (cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md Phase B). /codex/02-data/gcs-and-manifest-delete-
  safety-protocol.md §3 item 2 states hard-stop #2 (legacy-object-delete-after-copy) became §3a-reversibility-
  qualifiable (agent-executable, no human-execution requirement) as of a 2026-07-28 15:51:20 UTC operator ruling
  (unified-trading-pm@5cf3c2be0), once Part 5's twin-coverage proof independently confirms 100% canonical-twin coverage.
  The CeFi orphan-sweep plan's own 'Hard-stop review, 2026-07-28 (operator gated-decision closeout pass)' banner was
  written ~4h LATER the same day (19:36:00 UTC, unified-trading-pm@4b50207e5) and explicitly reaffirms 'Confirmed to
  remain permanent, human-only hard-stops -- delete-safety-protocol hard-stop #2 ... has no §3a reversibility carve-out
  ... neither qualifies for autonomous execution regardless of how thoroughly the pre-checks are verified' for this
  exact delete, reviewed alongside 3 other deletes (Track-7's 149-object delete, the already- executed Phase F
  legacy-bucket delete, and the Artifact Registry cleanup flip). Both statements are dated the same day; the plan's is
  later-timestamped and frames itself as a deliberate operator-reviewed review, not a stale leftover -- yet it
  contradicts the codex SSOT it should be deferring to. Treated conservatively pending resolution: Phase B's actual
  delete apply is being kept human-execution-only in the plan (see the 2026-07-29 ruling note added there), given the
  stakes (~1.2M objects, the same scale as the 70,570-object accidental-deletion incident earlier this cycle) and that
  overriding a hard-stop requires naming it explicitly in the same turn -- the operator's 2026-07-29 authorization named
  the protocol/conditions but not 'hard-stop #2' as an override target."
status: open
nature: issue
asset_group: [cefi, meta]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [delete-safety-protocol, hard-stop, ssot-contradiction, gcs-delete, cefi, codex-drift]
related:
  [
    /plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md,
    /plans/active/cefi_track7_candle_namespace_residual_2026_07_25.md,
    /plans/archive/2026_07/docker_artifact_registry_cleanup_policy_2026_07_24.md,
  ]
created: 2026-07-29
priority: P1
parent_epic: infrastructure_master
source: "Found while recording the operator's 2026-07-29 CeFi orphan-sweep authorization (interactive decision session)"
resolved_by:
locked_by:
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
---

# Hard-stop #2's §3a-carveout status contradicts itself: codex says qualifiable, the CeFi plan says categorically not

## Evidence

**Codex SSOT** (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, commit `5cf3c2be0`, 2026-07-28 15:51:20
UTC, "docs(plans): unblock whole-bucket-destroy + legacy-delete-after-copy under §3a reversibility"), § "3. Human-only
hard stops", item 2:

> Once Part 5 independently confirms 100% canonical-twin coverage (content-verified, not path-assumed), this class is
> ALSO reversibility-qualifiable per §3a (2026-07-28 operator ruling) — the fresh soft-delete check clears the
> human-EXECUTION requirement; it is never a substitute for Part 5's proof.

**The CeFi orphan-sweep plan** (`plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md`, commit
`4b50207e5`, 2026-07-28 19:36:00 UTC — ~4h LATER the same day — "docs(plans): apply operator theme + 10 direct answers
across the 73-decision digest"):

> **Hard-stop review, 2026-07-28 (operator gated-decision closeout pass).** Phase B (the ~1.2M-object orphan-sweep
> delete) and Phase F ... were reviewed together with the companion
> `cefi_track7_candle_namespace_residual_2026_07_25.md` delete (149 objects) and the
> `docker_artifact_registry_cleanup_policy_2026_07_24.md` Artifact Registry flip. **Confirmed to remain permanent,
> human-only hard-stops** — delete-safety-protocol hard-stop #2 (legacy-copied-not- moved) has no §3a reversibility
> carve-out ... neither qualifies for autonomous execution regardless of how thoroughly the pre-checks are verified.

Same day, same hard-stop, opposite conclusions. The plan's statement is the later of the two and explicitly frames
itself as a reviewed, operator-level ruling (not an agent's own read) covering 4 named deletes at once — which reads as
authoritative for those 4 specifically — but it directly contradicts the general codex text it should defer to (or the
codex text needs a caveat this plan's authors didn't know to check for).

## Why this matters now

This is not academic: the operator gave a 2026-07-29 go-ahead for this exact CeFi delete (~1.2M objects) in an
interactive session, following the standard protocol (dry-run, canonical VM script, soft-delete-retention check, apply,
verify). Whether an agent may execute that apply once the pre-checks clear, or whether a human must be the one to run
it, depends entirely on which of these two same-day statements is authoritative. Given the scale (comparable to the
70,570-object accidental-deletion incident already recovered once this cycle) and that the workspace's own hard-stop
rule requires naming the specific stop explicitly in the same turn to override it, this issue is being resolved
conservatively in the plan itself (human-execution-only kept) pending an explicit operator ruling here.

## Two plausible root causes (not yet distinguished)

1. **Precondition not met, not a categorical ban.** The general codex carve-out is conditional on Part 5's
   100%-twin-coverage proof. If that proof was never actually run for this specific ~1.2M-object corpus-wide sweep (vs.
   assumed), "no carve-out" would be correct FOR NOW, just imprecisely worded as if it were categorical/permanent rather
   than "not yet qualified."
2. **Deliberate exception for this delete's scale/risk class.** The operator may have wanted this specific corpus-wide
   sweep (and the 3 other deletes reviewed alongside it) held to a stricter bar than the general policy, regardless of
   Part 5 proof — i.e. a real, intentional carve-out-of-the-carve-out for large/high-blast-radius deletes.

## Open question for the operator

- [ ] [OPERATOR] P1. **Resolve which reading is correct** — (a) has Part 5's 100% twin-coverage proof actually been run
      for the CeFi ~1.2M-object corpus yet (if not, run it — that alone may resolve this without a policy change), or
      (b) is this genuinely a deliberate stricter carve-out for corpus-wide/large-scale deletes that the general codex
      text should be amended to state explicitly? Once ruled, update whichever doc is wrong (codex needs a scale/
      precondition caveat, or the plan's banner needs correcting) so the next similar delete doesn't hit the same
      ambiguity.

## Progress Log

- 2026-07-29: Filed while recording the operator's CeFi orphan-sweep authorization. Treated conservatively — Phase B
  kept human-execution-only in the plan pending this ruling. Phase A (unaffected, no delete) proceeds as already
  `[DATA]` P0 dispatchable.
