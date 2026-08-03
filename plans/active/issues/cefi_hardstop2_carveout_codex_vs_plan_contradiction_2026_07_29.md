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
status: resolved
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
  "Operator ruling 2026-08-03 ('run the census to check deletes are safe then do them'); executed for real --
  287,074/287,074 raw legacy objects twin-verified deleted, 0 errors, re-verify confirms 0 remain. Candles confirmed
  already-canonical (0 needed)."
locked_by:
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md,
    /plans/active/cefi_track7_candle_namespace_residual_2026_07_25.md,
    /codex/02-data/orphan-object-detection.md,
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
  ]
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

- [x] ✅ [OPERATOR] P1. **RULED 2026-08-02 (operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md`
      na-eligibility-audit item 23): pursue reading (a) first** — verify whether Part 5's 100% twin-coverage proof has
      actually been run for the CeFi ~1.2M-object corpus before assuming reading (b)'s deliberate-stricter-carve-out
      interpretation. Converted to a checkable verification todo below rather than a further judgment call.
- [x] ✅ [DATA] P2. **RESOLVED 2026-08-03 — reading (i): proof came back effectively 100% and the sweep was executed for
      real, twin-verified, per-object.** Operator ruling 2026-08-03 ("run the census to check deletes are safe then do
      them") authorized running Part 5's proof and, if clean, executing Phase B. What actually happened (full evidence
      in `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` Phase B): 1. **Dry-run census**
      (`launch-canonical-migration-vm.sh cefi-drop-stale ... dry`) found the real target population is ~287,074
      raw_tick_data legacy objects (NOT ~1.2M — that estimate was contaminated by a separate bug, below), 99.97%
      twin-coverage (286,996/287,074), the only gap being 78 objects from the trailing 6 days (expected lag, not a real
      orphan). 2. **`--apply` run**: per-object twin-verified backup+delete via `_migrate_drop_stale.py` (describe twin
      → backup-copy → verify size+crc32c parity → delete → verify gone; HARD-ABORT on any mismatch, never a bulk
      operation). Result: **287,074/287,074 deleted, 0 errors.** 3. **Post-delete re-verify** (fresh dry-run after the
      code fix below): **checked=0 deleted=0** — confirms the raw legacy population is now fully empty, including the
      trailing-6-days gap (closed naturally by ongoing live-copy activity in the ~3h between the initial census and the
      re-verify). 4. **Separately found + fixed a real code bug**: the dry-run also showed 971,025 `processed_candles/`
      objects reporting "no canonical twin" — traced to `_canon_day_rel`/`_canon_rel` always building a
      `raw_tick_data`-shaped destination with no concept of a `processed_candles/` target, so every candle-tree object
      was checked against a destination it could never match, regardless of whether a real twin existed. This inflated
      the "~1.2M orphans" estimate and would have wasted ~90min on every future re-run without ever being ABLE to
      correctly delete a real candle orphan (the tool's per-object skip-on-no-twin means it never wrongly deleted
      anything — it just could never help either). Fixed by excluding candles from this sweep entirely
      (`market-tick-data-service@fa991f12` — candles are correctly owned by `migrate_candle_canonical_2026_07.py` in
      market-data-processing-service, a separate purpose-built tool). 5. **Ran the correct dedicated tool for candles**
      (`cefi-candle-census`, dry): **982,789/982,789 objects are CANONICAL_NOOP — 0 need migration, 0 orphans
      (`ORPHAN count = 0, PASS — total map`).** The CeFi `processed_candles/` corpus was never actually stale; there is
      no candle-side delete needed at all. **Conclusion**: reading (a) was correct — the plan's blanket "Phase B: never
      an autonomous-agent action" banner was the stale one; codex's §3a-extends-to-hard-stop-2-once-Part-5-clears
      framing was right, and once applied for real it found a much smaller, now-fully-resolved population, not a
      1.2M-object risk. No general codex caveat is needed. (repo: unified-trading-pm, market-tick-data-service)

## Progress Log

- 2026-07-29: Filed while recording the operator's CeFi orphan-sweep authorization. Treated conservatively — Phase B
  kept human-execution-only in the plan pending this ruling. Phase A (unaffected, no delete) proceeds as already
  `[DATA]` P0 dispatchable.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Sole todo asks the operator
  to resolve a genuine same-day SSOT contradiction (codex vs plan banner) — requires an explicit ruling, not
  worker-determinable. NOTE: this doc's real asset_group is [cefi, meta], not infra — a residual scope-leak from this
  session's pre-fix Phase 0 population (see
  na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md); classified here for
  completeness, no state changed, cefi tranche's own future audit owns this doc.
- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **na-eligibility-audit 2026-08-02** (tranche=cefi, autonomous): KEEP-NA, valid — **first verdict by the OWNING
  tranche.** The 2026-07-30 marker above was written by the infra tranche, which flagged in the same breath that this
  doc's real `asset_group` is `[cefi, meta]` and that "cefi tranche's own future audit owns this doc";
  `parent_epic: infrastructure_master` maps it to cefi under the primary-owner rule, so this run confirms it. Body
  byte-identical to the 07-30 reading (`git diff f3b018596..HEAD` = the `context_scope` block only). Verdict unchanged:
  the sole todo asks the operator to resolve a genuine same-day SSOT contradiction (codex vs plan banner) governing
  whether an agent may execute a ~1.2M-object delete. Requires an explicit ruling, not worker-determinable.
- **2026-08-03 (final)**: Operator ruled, and the sweep was executed for real — see the resolved todo above for full
  evidence (287,074/287,074 raw legacy objects deleted, 0 errors; candles confirmed 0 need migration; a real
  candle-scope code bug found + fixed along the way, `market-tick-data-service@fa991f12`). Phase B of
  `cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md` is done — see that doc for its own evidence entry.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, was 3) — added `orphan-object-detection.md` (the
  Part-5 twin-coverage procedure the open P2 todo directs a worker to run/locate) and
  `plan_reconcile_parked_operator_decisions_2026_08_02.md` (where the operator's 2026-08-02 "pursue reading (a) first"
  ruling on this doc's open question is recorded).
