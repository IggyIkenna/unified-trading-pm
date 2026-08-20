---
doc_type: plan
title: CeFi E4→E8 orphan-sweep + legacy gap-fill + manifest rebuild — VM execution chain
summary: >-
  Consolidates THREE overlapping, previously-separately-dispatched todos in data_completion_cefi_2026_07_15.md (the "E4
  remaining work = ORPHAN SWEEP + gap-fill" todo / data_completion_cefi-015, its "Orphan sweep + bucket-state evidence"
  sibling / data_completion_cefi-013, and the "NEXT SESSION — execute the migration" todo) into ONE properly-scoped,
  phased execution chain — main-agent ruling BLK-650261be, 2026-07-28. All steps are human-executed (LOCAL, not
  AO-dispatched) — this is large-scale prod-bucket delete + VM-scale work (Phase B's dry-run census found the real
  population was 287,074 objects, not the ~1.2M this scope note originally estimated before the contaminating bug
  behind that figure was found and fixed — corrected 2026-08-19, `/plan-reconcile manifest_master`, see Phase B for the
  full trail), squarely the delete-safety-protocol hard-stop class, never an autonomous-agent action.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [backfill, manifest, cefi, data-correctness, irreversible-delete, vm-scale, operator-gated]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-28
last_updated: 2026-08-03 # Phase B executed for real, see its todo for evidence — the summary/banner above describes
# the ORIGINAL 2026-07-28 human-only ruling, since superseded by the 2026-08-03 operator ruling; kept as historical
# record rather than rewritten, per Phase B's own todo.
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
    /plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_cefi_manifest.py,
    unified-trading-library/unified_trading_library/cf_manifest_audit.py,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/archive/2026_08/data_completion_cefi_2026_07_15.md,
    /plans/audit/instructions/cefi_master_audit_instructions.md,
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
> crossing it. Filed as `/plans/archive/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` for an
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
> | Doc                                                                                       | Relationship to this plan                                                                                                                                                                                         |
> | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | `/plans/archive/2026_08/data_completion_cefi_2026_07_15.md`                               | **CITES.** Its E4 + "NEXT SESSION — execute the migration" todos are already `SUPERSEDED-BY` this plan (verified 2026-07-31); they execute nothing themselves.                                                    |
> | `/plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`           | **GATES Phase C.** Owns the normalization-aware snapshot-vs-`-prd` comparison that decides whether Phase C is done-by-fait-accompli or needs a from-snapshot re-scope. Nothing here should pre-empt that verdict. |
> | `/plans/archive/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` | **GATES Phase B's framing** (the hard-stop carve-out question) — not the execution.                                                                                                                               |
> | `/plans/archive/2026_07/cefi_track7_candle_namespace_residual_2026_07_25.md`              | **CITES** for sequencing only. (archived 2026-08-07)                                                                                                                                                              |
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

- [x] ✅ [DATA] P0. **DONE 2026-08-03.** Operator ruled 2026-08-03 ("run the census to check deletes are safe then do
      them") resolving `cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md` in favor of reading (a):
      codex's §3a-extends-to-hard-stop-2-once-Part-5-clears framing governs, not this plan's blanket "never an
      autonomous-agent action" banner (now superseded). - **Dry-run census** (`cefi-drop-stale ... dry`) found the real
      target population is ~287,074 raw legacy objects (NOT ~1.2M — that estimate was contaminated by a separate bug,
      below), 99.97% twin-coverage, the only gap being 78 objects from the trailing 6 days (expected copy-lag, not a
      real orphan). - **`--apply` run**: twin-verified backup+delete via `_migrate_drop_stale.py` (per-object
      describe→backup→ verify parity→delete→verify-gone, HARD-ABORT on any mismatch). **287,074/287,074 deleted, 0
      errors.** - **Post-delete re-verify** (fresh dry-run): **checked=0 deleted=0** — the raw legacy population,
      including the trailing-days gap, is now fully empty. - **Also found + fixed a real code bug**: candles were
      separately checked and ALL 971,025 showed "no canonical twin" — root cause was `_canon_day_rel` always building a
      `raw_tick_data`-shaped destination for `processed_candles/` sources too (no concept of the correct candle target
      shape), so every candle check was against an unreachable destination regardless of real twin status. This inflated
      the plan's own ~1.2M estimate. Fixed by excluding candles from this sweep (`market-tick-data-service@fa991f12`) —
      candles are correctly owned by `migrate_candle_canonical_2026_07.py` (market-data-processing-service), a separate
      tool. - **Ran that correct tool for candles** (`cefi-candle-census`, dry): **982,789/982,789 already
      CANONICAL_NOOP, 0 need migration, `ORPHAN count = 0` (total map)** — the candle corpus was never actually stale;
      nothing to delete there. **This sweep also covers** the pre-existing legacy-FORM `-prd` objects (the raw-shape
      delete above is the same no-`pipeline_mode=` population). No separate legacy SOURCE-bucket pass was needed —
      confirmed empty by the re-verify. Evidence: this session's VM run logs
      (`canonical-migration-cefi-drop-stale-20260803-102447` dry, `-120428` apply, `-144150` re-verify,
      `canonical-migration-cefi-candle-census-20260803-144337`), staged mapping/ reconcile reports at
      `gs://deployment-scripts-central-element-323112/vm-logs/` and
      `.../canonical-migration-candle-census/20260803-144337/`.

## Phase C — E4b: legacy→canonical gap-fill (additive, VM-scale) — ✅ DONE-BY-FAIT-ACCOMPLI (2026-08-08)

- [x] ✅ [DATA] P1. **DONE-BY-FAIT-ACCOMPLI 2026-08-08** (slot-8, `cefi_satellite_ao_dispatch_batch10`), citing the
      now-resolved gating investigation `plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`
      (`status: resolved` 2026-08-07, conclusion CF-11). That doc's final todo ran the proper normalization-aware CF-11
      covered-keys comparison between the pre-migration snapshot's manifest index (96,560 unique captured cells,
      2026-05-16) and the current `-prd` manifest: 36,850 covered (38.3%), 59,488 not covered (61.7%). The 59,488
      uncovered cells decompose entirely into (a) pre-canonical-era 2019+ data (DERIBIT/BYBIT/BINANCE-FUTURES/etc., out
      of the canonical-`-prd` migration's own scope), (b) 12,900 pre-CF-11 empty-`itype`/`dtype` ghost rows (not real
      cells), and (c) Era-B legacy chain-form rows in the `itype` column (already-tracked, separately-scoped class) —
      **no residual gap the `--also-legacy` gap-fill in this phase was meant to close.** Explicit conclusion from that
      investigation: "no unexpected data loss from the 2026-07-14 deletion beyond what was already scoped as
      out-of-canonical-scope legacy data." Since the source bucket `market-data-tick-cefi-central-element-323112` this
      phase's `--also-legacy` flag would read from no longer exists (deleted 2026-07-14, confirmed 404) and the
      investigation it was gated on found nothing left to gap-fill, this phase is closed by fait-accompli — the original
      `--also-legacy` VM launch below is superseded, not executed. ~~The 5,233-cell legacy-only gap-fill:
      `MIGRATION_EXTRA_ARGS="--also-legacy" bash launch-canonical-migration-vm.sh cefi <start> <end> full` (bare `cefi`
      category — additive-only, no `--drop-stale` in this phase; `--also-legacy` reads the legacy
      `market-data-tick-cefi` bucket as an additional source and copies any still-missing cell forward to canonical).
      Shard/bigger-mem: the 1.9M legacy-object listing previously stalled an `e2-standard-4` (use
      `MACHINE_TYPE=e2-standard-16` or shard the date range across multiple VMs). Done when: a fresh legacy-only-cells
      count reads 0 (was 5,233).~~ (original scope, kept for history — source bucket is gone, superseded by the CF-11
      finding above, not executed)

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
      `plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md` for the full finding (confirmed
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

- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
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
verification item: `plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`. No code shipped (plan
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
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — Phase B (the delete) is now DONE (2026-08-03) and
  its gate, `cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md`, is now `status: resolved`, so it was
  dropped; added the two source-code entry points the now-actionable remaining phases actually invoke (Phase D's
  `rebuild_cefi_manifest.py`, Phase E's `cf_manifest_audit.py`) plus the audit-instructions doc Phase E requires
  editing.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-01 verdict;
  Phase C stays blocked-investigation and Phases D/E remain real-production, VM-scale manifest rebuild+verify prod-write
  work despite Phase B's delete now completing. Not worker-determinable.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — Phase C is 🔴 CANNOT-RUN-AS-WRITTEN
  (gated on an unresolved normalization-verification investigation), Phases D/E are prod-scale manifest-rebuild/verify
  work on the data-correctness critical path with a track record of hidden production surprises; execution_scope:
  local-only by design. Reaffirms the 2026-08-04 pass.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries) — the only change since 2026-08-05 was a
  referrer-path fix (the hard-stop-2 contradiction issue doc's path updated to reflect its own archival), which isn't
  one of this doc's context_scope entries. All 6 (Phase C's gate doc, Phase D's `rebuild_cefi_manifest.py`, Phase E's
  `cf_manifest_audit.py` + audit-instructions doc, the vm-launcher runbook, and the parent L3 plan) re-verified
  resolving.
- **2026-08-08 (slot-8, `cefi_satellite_ao_dispatch_batch10` todo 1, data_engineering)** — Phase C's gate,
  `plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`, resolved 2026-08-07 with conclusion
  CF-11: the proper normalization-aware comparison found 59,488/96,338 eligible legacy cells not covered in current
  `-prd`, all decomposing into pre-canonical-era 2019+ data, pre-CF-11 empty-itype/dtype ghost rows, or already-tracked
  Era-B chain-form rows — "no unexpected data loss ... beyond what was already scoped as out-of-canonical-scope legacy
  data." Flipped Phase C to DONE-BY-FAIT-ACCOMPLI citing that conclusion — no residual gap-fill work remains, and the
  source bucket the original `--also-legacy` step would read from is gone anyway (confirmed 404, deleted 2026-07-14).
  Phases D/E remain open, unaffected by this change (they don't touch the legacy bucket).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-confirmed against today's 9
  cheat-sheet rulings (IAM self-service, D16 all-repos, S5.1 tiering, context_scope default, escalation-N default,
  reversibility-qualified deletes, Option B retirement, AWS lower-stakes, script-flag self-service precedent) — none
  apply here. Phases D (manifest `_index` rebuild `--apply`) and E (verify) remain real-production, VM-scale
  manifest-rewrite work on the data-correctness critical path; this doc's own banner ("all steps human-executed... never
  an autonomous-agent action") and 6 prior na-eligibility-audit passes (07-31 through 08-07) all reach the same verdict.
  Not a delete (ruling #6 doesn't apply), not IAM, not a scripted-flag gap — a genuine real-write VM-scale step this
  corpus has historically kept human-supervised given its track record of hidden production surprises on this exact
  migration.
- **round11 RECLASSIFY + satellite-extraction sweep 2026-08-09 (cefi tranche)**: KEEP-NA, valid — re-checked same-day
  against the round11 precedent set (identical core rulings to the round7 pass immediately above, plus
  plan-destination-default-to-AO for auto-filed findings and the specific GSM secret/webhook additions) — none newly
  bound Phases D/E. Phase D is a real-production `_index` rebuild `--apply`; Phase E is its verify gate; both remain
  VM-scale prod-writes this doc's own banner reserves for human execution. No reclassification.
- **context-scout 2026-08-15**: re-verified context_scope (6 entries), unchanged — Phase C's gate doc, Phase D/E's 2
  source-code scripts + the audit-instructions doc, the vm-launcher runbook, and the parent L3 plan all still resolve
  and remain the right minimal set for the still-open Phase D/E manifest-rebuild+verify work.
- **na-eligibility-audit 2026-08-16** [body-hash:e6d0725c3e72b6d4]: KEEP-NA, valid — Full end-to-end read confirms the doc's own checkbox state is accurate — no contradiction traps found.
- **context-scout 2026-08-19**: re-verified context_scope, no change needed (6 entries) — Phase D/E manifest-rebuild+verify remain the only open work; Phase C's gate doc, the 2 source-code scripts, the audit-instructions doc, the vm-launcher runbook, and the parent L3 plan all still resolve.
