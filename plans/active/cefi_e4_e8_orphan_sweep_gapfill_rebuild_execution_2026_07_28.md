---
doc_type: plan
title: CeFi E4→E8 orphan-sweep + legacy gap-fill + manifest rebuild — VM execution chain
summary: >-
  Consolidates THREE overlapping, previously-separately-dispatched todos in data_completion_cefi_2026_07_15.md (the "E4
  remaining work = ORPHAN SWEEP + gap-fill" todo / data_completion_cefi-015, its "Orphan sweep + bucket-state evidence"
  sibling / data_completion_cefi-013, and the "NEXT SESSION — execute the migration" todo) into ONE properly-scoped,
  phased execution chain — main-agent ruling BLK-650261be, 2026-07-28. All steps are human-executed (LOCAL, not
  AO-dispatched) — this is ~1.2M-object prod-bucket delete + VM-scale work, squarely the delete-safety-protocol
  hard-stop class, never an autonomous-agent action.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [backfill, manifest, cefi, data-correctness, irreversible-delete, vm-scale, operator-gated]
related:
  [
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-28
last_updated: 2026-07-30 # (rulings-closeout re-confirm — Phase B still correctly gated, no change)
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: [data_completion_cefi_2026_07_15.md — consolidated 2026-07-28 per main-agent ruling BLK-650261be (slot-4)]
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/data_completion_cefi_2026_07_15.md,
    /plans/active/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md,
    /plans/active/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md,
  ]
---

# CeFi E4→E8 orphan-sweep + legacy gap-fill + manifest rebuild — VM execution chain

> **Why this plan exists.** `data_completion_cefi_2026_07_15.md` accumulated THREE separately-worded, separately-
> dispatched todos that all describe the SAME underlying E4→E8 chain (delete the pre-`pipeline_mode=` orphan objects,
> backfill the legacy-only cells, rebuild the manifest, verify, then retire the legacy bucket):
> `data_completion_cefi-015` ("E4 remaining work = ORPHAN SWEEP + gap-fill, NOT a path walk"),
> `data_completion_cefi-013` ("Orphan sweep + bucket-state evidence"), and the older "NEXT SESSION — execute the
> migration" todo (already flagged BLOCKED by a 2026-07-27 slot-14 session for the exact same reason this plan exists:
> bundling 5 irreversible/VM-scale steps into one ~1h dispatch is unsafe). Three different sessions independently
> arrived at "this needs to be its own phased plan" rather than executed as a single dispatched todo. This plan is that
> phased plan — authored 2026-07-28 (slot-4) per main-agent coordination ruling `BLK-650261be`.
>
> **Nothing irreversible in this plan auto-executes.** Phases B and F are `[OPERATOR]` or require an operator-supervised
> VM launch + monitoring — see `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § "3. Human-only hard stops"
> (#2, the LEGACY-COPIED-NOT-MOVED invariant, applies to the ENTIRE orphan-sweep-delete phase below — it is a
> categorical hard stop, not eligible for the §3a reversibility carve-out, because §3a only narrows hard-stop #1,
> general prod-object deletes; it does not touch hard-stop #2 at all). **Update (2026-07-28 gate-cleanup pass)**: Phase
> A (the pre-delete copy-only pass) carries none of that irreversibility — no delete occurs in it — so it is retagged
> `[DATA]` and dispatchable as a normal monitored VM launch per `/codex/05-infrastructure/vm-launcher-runbook.md`'s
> default-dispatchable posture for ordinary migration VM launches. Phase B (the actual delete) is unaffected and remains
> `[OPERATOR]`/hard-stop #2.
>
> **Hard-stop review, 2026-07-28 (operator gated-decision closeout pass).** Phase B (the ~1.2M-object orphan-sweep
> delete) and Phase F (the legacy-bucket delete, already executed 2026-07-14 per the finding above) were reviewed
> together with the companion `cefi_track7_candle_namespace_residual_2026_07_25.md` delete (149 objects) and the
> `docker_artifact_registry_cleanup_policy_2026_07_24.md` Artifact Registry flip. **Confirmed to remain permanent,
> human-only hard-stops** — delete-safety-protocol hard-stop #2 (legacy-copied-not-moved) has no §3a reversibility
> carve-out, and Artifact Registry has no soft-delete at all — neither qualifies for autonomous execution regardless of
> how thoroughly the pre-checks are verified. **Not retagged, not unlocked**: Phase B and Phase F stay `[OPERATOR]`; a
> human must still execute or explicitly sign off on each at dispatch time.
>
> **Operator ruling, 2026-07-29 (interactive decision session).** Authorized: Phase A now, then Phase B once Phase A
> confirms clean — conditional on the standard protocol (dry-run first, launched via the canonical
> `launch-canonical-migration-vm.sh` deployment-service script — never an ad hoc script, actual apply run + checked
> against expected post-delete counts, and a FRESH `gcs_bucket_soft_delete_retention_seconds()` check on
> `market-data-tick-cefi-prd` confirmed sufficient before the apply). **Flagging an unresolved contradiction found while
> recording this**: `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3 item 2 states hard-stop #2 became
> §3a-reversibility-qualifiable (agent-executable) as of a 2026-07-28 15:51 UTC operator ruling, once Part 5's
> twin-coverage proof clears 100%. THIS plan's own "Hard-stop review" banner above was written ~4h later (2026-07-28
> 19:36 UTC, `unified-trading-pm@4b50207e5`) and explicitly reaffirms "no §3a carve-out... regardless of how thoroughly
> the pre-checks are verified" for this exact delete — a same-day, later-timestamped, explicitly operator-reviewed
> statement that contradicts the codex's general text. Given the stakes (~1.2M objects, the same class of action that
> produced a real 70,570-object accidental-deletion incident earlier this cycle) and that this plan's own reaffirmation
> is more specific and more recent, **Phase B's actual apply is being treated as still requiring literal human hands**,
> not agent execution — the operator's 2026-07-29 answer authorized the protocol/steps but did not name "hard-stop #2"
> as an override target in the same turn (the bar this workspace's hard-stop rule requires), so it is not read as
> crossing it. Filed as `/plans/active/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` for an
> explicit resolution. Phase A is unaffected — already `[DATA]` P0, dispatchable now.

## Already-shipped tooling (credit, not a flip)

The delete MECHANISM this plan executes already exists and is QG-green, shipped 2026-07-28 (slot-3,
`market-tick-data-service@e663d72f`): `migrate_cefi_flat_to_v9_canonical.py --drop-stale` — twin-verified backup+delete
of the pre-canonicalisation cefi objects (day=/candle trees without `pipeline_mode=`, plus the 9 L-flat root orphans),
reusing the shared `_migrate_drop_stale.py` helper originally built for `migrate_sports_canonical_v9`'s already-proven
E8 sweep (snapshot-first → per-object twin-verify → backup-copy → parity-check → delete → verify-gone → HARD-ABORT on
any mismatch). Needs `--apply`; dry-run reports only.

A VM-launcher category wiring this tool was added this session (slot-4, `deployment-service@9dd27ff` —
`launch-canonical-migration-vm.sh cefi-drop-stale <start> <end> {dry|full}`, DRY-BY-DEFAULT, `--apply` for full,
`--also-legacy` available via `MIGRATION_EXTRA_ARGS`; quality-gates.sh green, 4 new regression tests). **Neither of
these ships a prod-touching run** — both are tooling only, proven in unit tests with mocked GCS, never invoked against
production. This plan is where that invocation actually happens, phase by phase, with an operator at each irreversible
step.

## Co-claim structure — RESOLVED 2026-07-31 (corpus-wide ownership-conflict sweep)

> Four other cefi docs point at this plan, which read as a co-claim. It is not — **this plan is the single EXECUTION
> SSOT** and the others are gates or citations. The `[OPERATOR]` hard-stop on **Phase B was deliberately left exactly as
> it is** (permanent human-only, delete-safety-protocol hard-stop #2); only the surrounding ownership was clarified.
>
> | Doc                                                                                      | Relationship to this plan                                                                                                                                                                                         |
> | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | `/plans/active/data_completion_cefi_2026_07_15.md`                                       | **CITES.** Its E4 + "NEXT SESSION — execute the migration" todos are already `SUPERSEDED-BY` this plan (verified 2026-07-31); they execute nothing themselves.                                                    |
> | `/plans/active/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`           | **GATES Phase C.** Owns the normalization-aware snapshot-vs-`-prd` comparison that decides whether Phase C is done-by-fait-accompli or needs a from-snapshot re-scope. Nothing here should pre-empt that verdict. |
> | `/plans/active/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` | **GATES Phase B's framing** (the hard-stop carve-out question) — not the execution.                                                                                                                               |
> | `/plans/active/cefi_track7_candle_namespace_residual_2026_07_25.md`                      | **CITES** for sequencing only.                                                                                                                                                                                    |
>
> Net: **only this plan's own todos execute.** Every other doc either gates a phase or cites it.

## Phase A — E4a(i): PRE-DELETE GUARANTEE copy pass (additive, reversible, VM-launched)

- [x] ✅ [DATA] P0. **DONE 2026-07-30 (autonomous session).** Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)
      — copy-only, additive, idempotent (no delete occurs in this phase), so none of the irreversibility that makes
      Phases B/F human-only applies here. Launched the full-corpus-range `--apply` COPY-ONLY pass (bare `cefi` category,
      **NOT** `--drop-stale`) on SPOT: `canonical-migration-cefi-20260730-012546`,
      `bash launch-canonical-migration-vm.sh cefi 2019-03-30 2026-07-30 full`. **STARTED<60s confirmed**
      (`gcloud compute instances describe` returned `RUNNING` within seconds). **Completed cleanly ~43 minutes later**
      (`insert` 2026-07-30T01:25:56 → `delete` 2026-07-30T02:08:36, confirmed via `gcloud compute operations list` — no
      `compute.instances.preempted` op, a genuine self-delete on completion, not a preemption). `run.log`:
      `TOTAL planned=5531182 written/moved=275363` (the rest already-copied from prior sessions' work, correctly
      idempotent-skipped), `command exited rc=0`, `DEPLOYMENT_COMPLETED ... exit_code=0`. Grepped the full log for
      error/exception/traceback/warning lines beyond the expected launch-time tarball-freshness warnings — zero hits.
      **Done-when met**: every orphan now provably has a migrated destination. **Phase B (the actual delete) stays
      `[OPERATOR]`, hard-stop #2 — unaffected by this completion**; still separately gated on the unresolved hard-stop-2
      contradiction (`issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md`).

## Phase B — E4a(ii): orphan-sweep DELETE (irreversible, `[OPERATOR]`, hard-stop #2)

- [ ] [OPERATOR] P0. **Operator-authorized 2026-07-29** (see ruling above), pending a human to execute the apply —
      **only after Phase A is confirmed clean.** Launch the delete sweep on a dedicated SPOT VM:
      `bash launch-canonical-migration-vm.sh cefi-drop-stale 2019-03-30 <today> full` — deletes the ~1.2M
      (`~474/day × ~2,613 days`) OLD `day=/asset_group=cefi/…` (no-`pipeline_mode=`) orphan objects corpus-wide + the 9
      L-flat root orphans, via the twin-verify/backup/delete/verify-gone contract in `_migrate_drop_stale.py`. Cite
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § Part 5 (LEGACY-COPIED-NOT-MOVED) — this is hard-stop
      #2, human-execute-only regardless of the §3a soft-delete carve-out (§3a narrows hard-stop #1 only). **Also
      covers**: the pre-existing legacy-FORM `-prd` objects measured 2026-06-02 (`market-data-tick-cefi-prd` was ~65% of
      legacy object count, ~17 days stale, INTERMEDIATE FORM — has `asset_group=cefi` in the path but no
      `pipeline_mode=` partition) — these become orphans the SAME way once their `pipeline_mode=` siblings exist, so
      this sweep must delete them too, not only a separate legacy SOURCE-bucket pass. **Done when**: post-sweep object
      count via Cloud Monitoring `storage/v2/total_count` (`type=live-object` — never a naive recursive `ls`, which
      double-counts noncurrent versions + soft-deleted objects) confirms the pre-`pipeline_mode=` shape is gone
      corpus-wide. Cite the before/after Monitoring counts as evidence. Absorbs the measured-evidence content of the
      former `data_completion_cefi_2026_07_15.md` "Orphan sweep + bucket-state evidence" todo
      (`data_completion_cefi-013`).

## Phase C — E4b: legacy→canonical gap-fill (additive, VM-scale) — 🔴 CANNOT-RUN-AS-WRITTEN

- [ ] [DATA] P1. **🔴 CANNOT-RUN-AS-WRITTEN (2026-07-28, slot-3, data_engineering)**: the source bucket
      `market-data-tick-cefi-central-element-323112` this phase's `--also-legacy` flag reads from **no longer exists** —
      `gcloud storage buckets describe` returns 404; Cloud Audit Logs confirm `storage.buckets.delete` by
      `ikenna@odum-research.com` at `2026-07-14T11:02:29Z`, well before this plan (or its L3 predecessor) was authored.
      Full evidence: `plans/active/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`. Do NOT dispatch this
      phase as written — `launch-canonical-migration-vm.sh cefi ... --also-legacy` will fail immediately against the
      now-nonexistent bucket. **Gated on the linked issue doc's migration-before-delete verification** (attempted
      read-only via the pre-migration snapshot's manifest index — INCONCLUSIVE, naive tuple-diff is unreliable per the
      same false-phantom normalization bug class already found in
      `cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`; a proper CF-11-style normalized comparison is
      still needed). Once that verification lands: if it confirms the legacy-only cells were already migrated before
      deletion, this phase is DONE-BY-FAIT-ACCOMPLI (nothing left to gap-fill) — flip with that citation. If it finds a
      genuine residual gap, this phase must be RE-SCOPED to a from-snapshot restore (there is no live bucket left to
      `--also-legacy` read from) rather than run as currently written. ~~The 5,233-cell legacy-only gap-fill:
      `MIGRATION_EXTRA_ARGS="--also-legacy" bash     launch-canonical-migration-vm.sh cefi <start> <end> full` (bare
      `cefi` category — additive-only, no `--drop-stale` in this phase; `--also-legacy` reads the legacy
      `market-data-tick-cefi` bucket as an additional source and copies any still-missing cell forward to canonical).
      Shard/bigger-mem: the 1.9M legacy-object listing previously stalled an `e2-standard-4` (use
      `MACHINE_TYPE=e2-standard-16` or shard the date range across multiple VMs). Done when: a fresh legacy-only-cells
      count reads 0 (was 5,233).~~ (original scope, kept for history — source bucket is gone, cannot execute verbatim)

## Phase D — E5: manifest `_index` rebuild — UNBLOCKED 2026-07-28 (slot-2), ready to dispatch

- [ ] [DATA] P0. **Depends on** `plans/archive/issues/cefi_rebuild_false_phantom_itype_underlying_drift_2026_07_28.md`
      landing — **✅ RESOLVED 2026-07-28 (slot-2), dependency SATISFIED.** 4 full-corpus dry-run iterations, 4
      confirmed + shipped fixes (market-tick-data-service@dcbed674, @42a2fd9f, @9a2927ad, @9c19c48b):
      `phantom_to_failed` 490,639 (8.6%) → **17,255 (0.3%)**, DERIBIT now the single largest venue (5,592, 32.4% — the
      originally-anticipated true-phantom class); every other significant contributor individually diagnosed
      (OKX-FUTURES = confirmed-ambiguous unfixable legacy ids, BYBIT residual = delisted-token true-phantoms, rest =
      long tail). Full evidence in the issue doc's final todo. **This phase's `--apply` execution is now dispatchable**
      — run `rebuild_cefi_manifest.py --apply` full range on a VM (now CF-11-canonical + false-phantom-safe,
      `mtds#fa2b02c7` + all 4 fixes above). **Done when**: the rebuild completes and a fresh `cf_manifest_audit` shows
      `phantom_to_failed` at the expected small residual, not the 8.6% figure. (NOT executed by slot-2 — this is a
      separate, VM-scale, real-production-write scoped todo outside the normalizer task that resolved the dependency
      above; dispatch this todo on its own.)

## Phase E — E7: verify

- [ ] [DATA] P0. Re-run `unified_trading_library.cf_manifest_audit.audit()` against `market-data-tick-cefi-prd-…` (the
      reusable tool already used by prior sessions this week) → confirm **CF-1…CF-12 GREEN on data-state**: v9=100% (was
      97.4-97.5%), `source` blank=0% (was 24.0%), `pipeline_mode` blank=0% (was 1.4-1.5%), Era-B legacy-form rows=0 (was
      ~490K). Flip the CF-coverage rows in `cefi_master_audit_instructions.md`. **Done when**: the audit's own printed
      verdict is GREEN on all four criteria — do not flip on a RED audit (data-pipeline-correctness HARD RULE). Once
      GREEN, flip the "E7 Verify" AND the "Post-walk" audit todos in `data_completion_cefi_2026_07_15.md` (both
      currently RED, most recently re-confirmed 2026-07-28 by slot-6/slot-8) citing this plan's evidence.

## Phase F — E8: legacy bucket delete — ✅ DONE-BY-OPERATOR-2026-07-14 (do not dispatch)

- [x] ✅ [OPERATOR] P0. **DONE-BY-OPERATOR-2026-07-14 (discovered 2026-07-28, slot-3, data_engineering)** — the legacy
      bucket `market-data-tick-cefi-central-element-323112` is already gone: `gcloud storage buckets describe` returns
      404, and Cloud Audit Logs confirm `storage.buckets.delete` by `ikenna@odum-research.com` at `2026-07-14T11:02:29Z`
      — ~2 weeks before this plan (or its predecessor todos) were even authored, and before gates (1)/(2) below were
      satisfied. Flipping so this phase never gets dispatched against a bucket that no longer exists; **this is NOT a
      claim that gates (1)/(2) were properly honored before the delete happened** — see
      `plans/active/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md` for the full finding (confirmed
      plan-vs-reality drift + an operator-confirmation todo on whether this was intentional). Original gating (kept for
      history, in case a future different-AG copy of this plan needs it): **Gated on ALL of**: (1) Phase E reads GREEN
      on all four criteria; (2) `plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md`:134 — "Do NOT delete
      an AG's legacy bucket while its L3 plan is open" — cefi's L3 plan (`data_completion_cefi_2026_07_15.md`) must
      itself be C-GREEN/closed, or this specific decommission item explicitly re-evaluated against its then-current open
      items; (3) delete-safety-protocol hard-stop #1 — a **whole-bucket** destroy is NEVER reversibility-qualified under
      §3a regardless of soft-delete config, so this step is human-execute-only unconditionally. Once all three clear:
      permanently delete the legacy `market-data-tick-cefi` bucket (both GCP live objects AND the 3.81M
      noncurrent/versioned objects it carries) — canonical `market-data-tick-cefi-prd` becomes the sole SSOT. Record the
      action in `_index/snapshots/decommission_2026_0X.md` per the decommission plan's own convention.

## Progress Log

### 2026-07-28 (slot-4, `data_engineering`) — plan authored, consolidating 3 overlapping todos per main ruling BLK-650261be

Main-agent coordination (via `/api/slots/4/progress` message) identified that `data_completion_cefi-015` (this session's
dispatched task) is the SAME underlying E4→E8 chain as its sibling `data_completion_cefi-013` (slot-3, "Orphan sweep +
bucket-state evidence") and the older "NEXT SESSION — execute the migration" todo (already declined by a 2026-07-27
slot-14 session for the identical reason). Ruling: do NOT execute the irreversible sweep now (human-only per
delete-safety §3a / hard-stop #2); author ONE consolidated, phased plan instead (this doc); mark all three source todos
`superseded_by` this plan in `data_completion_cefi_2026_07_15.md`, checkboxes left UNCHECKED (no sweep has run); credit
the already-shipped `--drop-stale` tooling (`mtds@e663d72f`) as a nested done-note, not a flip. Also shipped this
session, ahead of this plan: the `cefi-drop-stale` VM-launcher category in `deployment-service`
(`launch-canonical-migration-vm.sh` + regression tests, mocked-GCS only, no prod invocation) — Phases A-C above are how
that tooling actually gets run against production, one operator-supervised step at a time.

### 2026-07-28 (slot-3, `data_engineering`) — Phase C/F re-scope: legacy bucket already deleted 2026-07-14

Re-verifying `data_completion_cefi-013`'s "bucket-state evidence" (the todo this plan's Phase B already absorbed) found
the legacy bucket `market-data-tick-cefi-central-element-323112` was deleted 2026-07-14 (Cloud Audit Log confirmed),
predating this plan's own authoring by two weeks. Per main-agent coordination (slot-4 had already released ownership of
this plan after `/done`ing `data_completion_cefi-015` without incorporating the re-scope), applied it directly: **Phase
C** (`--also-legacy` gap-fill) marked CANNOT-RUN-AS-WRITTEN — its source bucket no longer exists; gated on a proper
normalization-aware migration-before-delete verification (attempted read-only via the pre-migration snapshot's manifest
index, but INCONCLUSIVE — a naive tuple diff isn't trustworthy for this corpus, same false-phantom bug class as the
CF-11 finding). **Phase F** (E8 legacy delete) flipped DONE-BY-OPERATOR-2026-07-14 — the bucket is already gone, so
dispatching this phase would just 404; explicitly NOT a claim that its gates were honored before the delete happened.
**Phase A/B/D/E unchanged** — Phase B's orphan-sweep targets the `-prd` bucket itself (still live), and D/E (manifest
rebuild + verify) don't touch the legacy bucket at all. Full evidence + the operator-intent question + the open
verification item: `plans/active/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`. No code shipped (plan
reconciliation only, per the finding's own recommended decision).

### 2026-07-30 (rulings-closeout pass, separate session) — re-confirmed, no change

Re-verified this doc's live-gate state per a workspace-wide sweep closing out recorded operator rulings implying
unshipped work. Phase A remains correctly flipped done (already verified complete this session by an earlier pass,
`canonical-migration-cefi-20260730-012546`). **Phase B remains correctly gated** — re-read
`plans/active/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` directly: `status: open`,
unchanged, no new resolution. Per this sweep's own explicit constraint (do not resolve an open operator-only policy
contradiction, do not execute a ~1.2M-object prod delete without an independently-verified §3a citation), Phase B was
NOT executed and the hard-stop-2 contradiction was NOT adjudicated. No action taken; no changes needed.

### 2026-07-31 (na-eligibility-audit, tranche=cefi, autonomous) — KEEP-NA, valid

All 4 open todos (Phases B/C/D/E) stay NA: the doc's own summary/banner declares "All steps are human-executed (LOCAL,
not AO-dispatched)... never an autonomous-agent action," Phase B is the categorical delete-safety hard-stop #2
(`[OPERATOR]`), Phase C is blocked on an unresolved migration-verification investigation, and Phase D/E — while reading
individually as "dispatchable" in their own todo text — are real-production-write, VM-scale steps tightly interleaved
with the still-open hard-stop-2 contradiction (`cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md`). Per
the skill's "stay skeptical of a todo's own self-framing" caveat, the doc-level banner governs over any individual
todo's isolated wording. No reclassification.

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, valid — re-confirmed. All 4 open todos
  (Phases B/C/D/E) still gated per the doc's own "all steps human-executed, never AO-dispatched" banner; Phase B still
  blocked on `cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` (status: open, unchanged); Phase C
  still blocked on the CF-11 investigation. No change since the 2026-07-31 marker above.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
