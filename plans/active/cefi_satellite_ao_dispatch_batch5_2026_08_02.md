---
doc_type: plan
title: CeFi satellite AO batch 5 — operator-authorized extraction from the 2026-07-30 ag-closeout-audit cefi residual
summary: >-
  Fifth AO-dispatch batch for cefi, drafted 2026-08-02 against the five source docs the `/ag-closeout-audit` cefi run
  named in the operator's 2026-07-30 interactive Q&A (dispatch explicitly AUTHORIZED in that session, so this plan ships
  `status: active` + `assigned_vm: planning` directly rather than draft-for-review). Every one of the five docs was
  re-read live before drafting because the corpus moved substantially between the audit and today: the intervening
  2026-07-31 corpus-wide ownership-conflict sweep, the 2026-07-31 autonomous `/ag-closeout-audit` run that produced
  `cefi_satellite_ao_dispatch_batch4_2026_07_31.md`, and three separate `/na-eligibility-audit` passes (07-30, 08-01)
  all landed rulings on this exact candidate set. Net result: 5 conflict-clear bounded todos extracted from 3 of the 5
  source docs; the other 2 docs' work is deliberately NOT re-drafted here because it is already claimed elsewhere (one
  verbatim by batch4, one already reclassified `assigned_vm: planning` in place) — re-drafting either would be the
  duplicate-claim the shared conflict-check protocol forbids. Two further todos are Deferred with their blocking ruling
  cited rather than guessed. This is fewer than the "~9" the original audit estimated, and the gap is accounted for
  item-by-item in "What was excluded and why" below rather than silently dropped.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm, deployment-service, market-tick-data-service, instruments-service, unified-trading-library]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-5, satellite-docs, iterative-drain]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md,
    /plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md,
    /plans/active/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md,
    /plans/active/issues/mdps_backfill_cefi_trades_gap_fill_completion_2026_07_28.md,
    /plans/active/issues/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md,
    /plans/active/issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator interactive Q&A 2026-07-30 — the `/ag-closeout-audit` cefi run's orphan residual was reviewed with the
  operator, who RULED that a batch be authored and dispatched directly (no draft-then-review cycle). Drafted 2026-08-02.
  Batch number 5 rather than the "batch4" the 2026-07-30 session anticipated, because the 2026-07-31 scheduled
  autonomous `/ag-closeout-audit` run claimed batch4 first with a different, non-overlapping candidate set;
  `cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize.md`'s own todo 2 already names "batch5" as the next extraction
  slot, so this follows the corpus's own established sequence rather than colliding on a duplicate batch number.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# CeFi satellite AO batch 5 — operator-authorized extraction

> **Status: active from the start.** Unlike the skill-drafted `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` (which
> correctly stayed `draft` because it was produced by an unattended scheduled run), this batch's dispatch was
> **explicitly authorized by the operator in the 2026-07-30 interactive session**. No further review gate applies.

> **Cross-todo file-collision check: PASS.** The 5 todos touch, respectively: (1) instruments-service reference-data
> catalogue adapters + a read-only MTDS manifest query; (2) `deployment-service/scripts/vm/launch-*live*.sh`; (3)
> `unified-trading-pm`'s `cursor-configs/skills/data-pipeline-check-mtds/SKILL.md`; (4) a VM-hosted invocation of
> `unified-trading-library`'s `merge_manifest_from_canonical_paths` (no source file edited; its manifest write is
> additive and scoped to the `processed_candles/by_date` prefix); (5) market-tick-data-service's
> `AsterLiquidationsWSConnector`. Todo 1 reads manifest rows under a DIFFERENT prefix (`raw_tick_data`) than todo 4
> writes, and reads only — so even concurrent execution is safe. Safe to dispatch concurrently; `sequential: false`.

> **Every claim below was re-verified against live code/state on 2026-08-02**, not carried over from the source docs'
> own prose. Where a source doc's stated detail had drifted, the todo says so and names the corrected fact.

> **Adjacent open work, checked and confirmed NON-colliding (2026-08-02).**
> `/plans/active/issues/mtds_live_smoke_vm_name_exceeds_gcp_limit_2026_08_01.md` (`assigned_vm: planning`) landed
> upstream after this batch's candidate set was assembled and concerns the same `mtds-live-smoke` launch path — but its
> single open todo claims `market-tick-data-service/scripts/pipeline_e2e_check.py` only (bounding the generated VM name
> to GCP's 63-char limit). It does **not** claim `launch-mtds-live.sh` (it only mentions it in prose) and does not touch
> the skill's `SKILL.md`, so it collides with neither todo 1 nor todo 2 here. Whoever picks up todo 1 should still read
> it first — a worker editing this launcher family benefits from knowing the name-length failure exists.

## Todos

- [ ] [INFRA] P1. **Wire the Tardis N=1 concurrency guard into `launch-mtds-live.sh` and every sibling live launcher.**
      Ordered sub-steps for ONE worker (same launcher family, deliberately not fanned out): (a) in
      `deployment-service/scripts/vm/launch-mtds-live.sh`, source `tardis-concurrency-guard.sh` and call
      `tardis_concurrency_guard` pre-flight plus `tardis_guard_reserve_slot` immediately before VM creation, gated on
      the shard's venue needing the guard. **REUSE, do not re-implement** — call the already-shipped
      `tardis_venue_list_needs_guard` helper (`deployment-service@2d6b01a`) rather than open-coding a venue list. (b)
      Then apply the same wiring to the sibling launchers that need it. **Verified live 2026-08-02**: the guard helper
      and `TARDIS_CAP_EXEMPT_VENUES` do exist in `deployment-service/scripts/vm/tardis-concurrency-guard.sh` (note:
      directly under `scripts/vm/`, not a `lib/` subdir as one might assume), and **all 8** `launch-*live*.sh` scripts
      under `scripts/vm/` currently have ZERO guard references — `launch-mtds-live.sh`,
      `launch-mtds-live-cefi-consolidated.sh`, `launch-mtds-live-prediction-consolidated.sh`,
      `launch-mdps-features-live.sh`, `launch-perp-clob-live.sh`, `launch-prediction-live.sh`,
      `launch-strategy-live-vm.sh`, `launch-batch-live-recon-cron-vm.sh`. That is a WIDER scope than the source doc's P2
      text (which named only 2 siblings); triage each of the 8 for whether it can actually create a Tardis-fetching VM
      and wire only those, recording the per-launcher verdict. **Do NOT "correct" the shipped exempt list from the
      source doc's prose** — the live list is `(HYPERLIQUID ASTER EXTENDED-STARKNET COINBASE-CDE)`, which differs from
      that doc's older text; if the divergence is real it is its own finding, confirm against `VENUE_TO_ADAPTER_KEY`
      first. **Scope note: this todo is a launcher-script code change only — it requires no new VM launch and performs
      no deletes.** It makes FUTURE live-leg launches respect the N=1 cap; the worker must not create a VM to test it
      (unit/shellcheck coverage plus a dry-run of the guard's refusal path is the intended verification). This todo
      covers the source doc's P1 and P2 together. Source:
      `/plans/active/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` (P1 + P2 of 3). **Done when**: every
      launcher that can create a Tardis-fetching VM sources the guard and reserves a slot before creation, each of the 8
      carries an explicit wired-or-exempt verdict, `quality-gates.sh` is green, and the source doc's P1 + P2 checkboxes
      are flipped citing the shipping commit. Repo: deployment-service.

- [ ] [DOC] P3. **Add the live-leg Tardis guard-gap note to the `data-pipeline-check-mtds` skill's Phase-2 section.**
      Document that a live-leg smoke check against a Tardis-sourced venue can contend with an active Tardis
      backfill/sharded VM for the single shared IP, and recommend deferring live-leg checks for Tardis-sourced venues
      while a real Tardis-consuming VM is confirmed running, until the launcher-guard todo above ships. **Scope-fenced:
      Phase 2 ONLY** — the same file's `§ 3 (Tardis cap)` section is owned by
      `/plans/active/issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`, whose
      equivalent todo is already DONE; read what it wrote and cross-link it rather than restating or editing it.
      **Corrected path (verified 2026-08-02)**: the skill lives at
      `unified-trading-pm/cursor-configs/skills/data-pipeline-check-mtds/`, NOT the `.claude/skills/...` path the source
      doc's todo text names — that directory does not exist. Source:
      `/plans/active/issues/mtds_live_smoke_vm_not_tardis_guarded_2026_07_28.md` (P3 of 3). **Done when**: the skill's
      Phase-2 section carries the guard-gap caveat with a cross-link to the § 3 work, prek is green, and the source
      doc's P3 checkbox is flipped. Repo: unified-trading-pm.

- [ ] [SCRIPT] P3. **Run the additive MDPS manifest reconciliation for the cefi trades gap-fill campaign, on a VM.**
      Invoke `merge_manifest_from_canonical_paths` (unified-trading-library, `manifest_writer/_maintenance.py`) with
      `bucket="market-data-tick-cefi-prd-central-element-323112"`, `service_name="market-data-processing-service"`,
      `prefix="processed_candles/by_date"`, to register the per-VM manifest shards that never flushed during the 15-VM
      campaign (notably `r20251225`'s final 7 rows — the underlying parquet data is confirmed present on GCS, only its
      manifest registration is missing). **Explicit safe-idempotent justification (this is the gating line the
      2026-07-30 na-eligibility-audit said was missing — it is why this todo needs no `[OPERATOR]` tag):** the function
      is ADDITIVE ONLY — it computes `discovered - existing` and uploads `existing + new_only`, so every row outside
      `prefix`, including the co-located MTDS `raw_tick_data` rows, survives untouched; re-running it is a no-op. Both
      properties are covered by live regression tests re-verified present 2026-08-02 —
      `test_merge_from_canonical_paths_preserves_rows_outside_prefix` and
      `test_merge_from_canonical_paths_is_idempotent_no_duplicate_rows` in
      `unified-trading-library/tests/unit/test_manifest_v4_migration.py`. **Do NOT call
      `rebuild_manifest_from_canonical_paths`** — that sibling wholesale-REPLACES the co-located bucket's entire
      manifest index and would delete essentially the whole CEFI `raw_tick_data` manifest to register 7 candle rows (P0
      data-correctness hazard,
      `/plans/active/issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md`). **Must run on an
      in-region VM, never locally** — it walks every parquet under the entire `processed_candles/by_date` prefix, which
      is exactly the full-corpus GCS walk the heavy-I/O HARD RULE forbids from a local session; the VM must be a
      registered launcher name per the runbook. Source:
      `/plans/active/issues/mdps_backfill_cefi_trades_gap_fill_completion_2026_07_28.md`. **Done when**: the merge runs
      to completion on a VM with a cited terminal `exit_code=0`, a before/after manifest row count for the
      `processed_candles/by_date` prefix is recorded, `r20251225`'s 7 rows are confirmed registered, and the source
      doc's open checkbox is flipped citing this run. Repos: unified-trading-library, deployment-service.

- [ ] [DIAG] P3. **Settle the ASTER `liquidations` 100%-`empty_confirmed` question with a multi-hour listen window.**
      The manifest shows 563/563 ASTER `liquidations` samples at `empty_confirmed`. A 2026-07-31 investigation was
      inconclusive and explicitly asked for a longer real-world check rather than another re-guess: it confirmed
      `AsterLiquidationsWSConnector` (market-tick-data-service, `live/connectors/aster_book_liq_ws.py`) connects
      cleanly, that `SUBSCRIBE !forceOrder@arr` gets a normal ack with no error, and that `_parse_aster_force_order`'s
      field mapping matches the real Binance-compatible `forceOrder` wire shape exactly — so this is NOT the
      already-fixed `bids`/`asks` vs `b`/`a` mismatch class. Two short windows (20s, then 90s) saw zero events, which is
      far too short to distinguish genuine liquidation rarity from a silent reconnect-drop bug. Run a listen window of
      several hours, OR equivalently audit the connector's own reconnect-flag/log activity across the live consolidated
      VM's actual uptime. **This todo's outcome is a VERDICT, either branch of which closes it**: zero events across a
      multi-hour window WITH clean reconnects throughout = data-source reality, close as not-a-bug; ANY silent
      multi-hour disconnect with no reconnect = the real bug, fix it and ship with a regression test. Source:
      `/plans/active/issues/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md` (its third `[DATA] P3` todo
      only — its other two todos are already claimed by batch4, see "What was excluded and why"). **Done when**: a
      listen window of several hours (or an equivalent uptime-log audit) is completed with its duration and event count
      cited, one of the two verdicts above is recorded, and the source doc's third P3 checkbox is flipped. Repo:
      market-tick-data-service.

- [ ] [DATA] P3. **Root-cause the KRAKEN-FUTURES / HYPERLIQUID PERPETUAL catalogue-completeness gap.** Both venues are
      already ~99-100% marker-format on BOTH the manifest and catalogue sides (KRAKEN-FUTURES PERPETUAL: catalogue
      501/501, manifest 562/568; HYPERLIQUID PERPETUAL: manifest 345/346), so this is explicitly NOT a marker-format
      migration-scope problem — the format explanation is already ruled out by the source doc's own traced evidence.
      Determine why real, captured, correctly-formatted instruments (~60 more distinct manifest ids than the catalogue
      carries for KRAKEN-FUTURES PERPETUAL) are missing from the reference-data catalogue builder's output for these 2
      venues. Candidate mechanisms named by the source doc, to confirm or eliminate: an adapter coverage gap, or an
      expiry/delisting filter (compare against the known `deribit_options_adapter` `expired=false` precedent, which is
      the same shape of filter). **Strictly read-only, with no new VM launch**: a catalogue read plus a
      `read_availability_index` manifest read — no corpus walk, no writes, no deletes. Source:
      `/plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md` (its
      `[DATA] P3` todo only — its `[DATA] P2` prod-`--apply` migration todo is Deferred below). **Done when**: the
      mechanism is named with cited evidence for each of the 2 venues (adapter gap vs filter vs something else), any
      resulting fix is either shipped or filed as its own properly-scoped follow-up todo, and the source doc's P3
      checkbox is flipped. Repos: instruments-service, market-tick-data-service.

## What was excluded and why

The 2026-07-30 audit estimated "~9" bounded todos across 5 source docs. Five survived the live re-check. Each item that
did not is accounted for here — none was silently dropped.

- **`/plans/active/issues/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md`'s first two todos (the
  `gcloud storage ls` ASTER landing re-check, and the 2-3 pre-existing-venue spot-check) — ALREADY CLAIMED VERBATIM by
  `cefi_satellite_ao_dispatch_batch4_2026_07_31.md`'s todo 2**, which cites this exact source doc and covers ASTER plus
  HYPERLIQUID plus BINANCE-FUTURES. Re-drafting them here would be the near-verbatim duplicate claim § 3 of the
  conflict-check protocol forbids. The 2026-08-01 na-eligibility-audit reached the same conclusion independently and
  recommended preferring batch4's path. Only this doc's THIRD todo (the ASTER `liquidations` listen window, added
  2026-07-31 and therefore not visible to batch4 when it was drafted) is extracted above.
- **`/plans/active/issues/execution_service_bitfinex_bitget_native_unreachable_2026_07_28.md` — ALREADY
  `assigned_vm: planning` IN PLACE.** The 2026-07-30 na-eligibility-audit reclassified this doc rather than parking it,
  per the naming SSOT's shape (b) "retroactive reclassification, name unchanged". Its single `[SCRIPT] P3` factory.py
  wiring todo is therefore already dispatchable on its own; extracting it into this batch would create a second dispatch
  path for the same change. Re-verified 2026-08-02 that the work is still genuinely open —
  `BitfinexCeFiAdapter`/`BitgetCeFiAdapter` still have zero references in `execution-service`'s
  `trade_execution/factory.py`. **One real gap noted, not fixed here**: that doc has no paired `_finalize` sibling,
  which shape (b) calls for and `task_template.md` § 4 requires of every AO-dispatched plan. It is tracked as a todo in
  this batch's finalize plan rather than invented as a fresh doc mid-batch.

## Deferred — BLOCKED-OPERATOR-DECISION (ruled KEEP-NA, not re-litigated here)

- **`/plans/active/issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`'s
  `[DATA] P2` marker-format migration** (BYBIT's raw-date dated-future shape, plus new coverage for COINBASE-FUTURES
  PERPETUAL and BITGET-FUTURES PERPETUAL — ~700 still-unmigrated manifest ids). The 2026-07-30 na-eligibility-audit
  ruled **KEEP-NA, valid**: it is a backup-first prod `--apply` content migration with no stated safe-idempotent
  justification, so it needs the delete/apply gate per CLAUDE.md's AO-todo gating rule. Not drafted here — clearing it
  requires either an `[OPERATOR]` tag with a delete-safety cite, or a fresh same-run reversibility verification
  (`gcs_bucket_soft_delete_retention_seconds()` ≥ 604800s) that this drafting pass could not perform. Note the contrast
  with this batch's own MDPS manifest todo, which WAS drafted precisely because its additive-idempotent property is
  provable from existing regression tests; this one has no equivalent proof.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated via the companion
`cefi_satellite_ao_dispatch_batch5_2026_08_02_finalize.md` (`depends_on` + `gate_on_depends: true`), mirroring the
batch1 through batch4 finalize pattern.

## Codex SSOTs

- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — § 1 (the two naming shapes, which is
  why the bitfinex/bitget doc is excluded rather than re-extracted) and § 3 (the conflict-check protocol every verdict
  above applied).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" — the
  bounded-outcome test each todo above must pass.
- `/codex/05-infrastructure/vm-launcher-runbook.md` § Tardis cap — the N=1 invariant todo 1 restores across the live
  launchers, and the heavy-I/O rule todo 3 obeys.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3a — the reversibility bar the Deferred marker-format
  migration has not cleared.
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step ritual this batch's finalize plan
  executes.
