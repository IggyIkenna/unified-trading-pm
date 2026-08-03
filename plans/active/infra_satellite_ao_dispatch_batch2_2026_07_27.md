---
doc_type: plan
title:
  Infra satellite docs — AO dispatch batch 2 (9 AO-eligible todos extracted from 3 NA-audited infra plans/issues via
  /na-eligibility-audit)
summary: >-
  First /na-eligibility-audit interactive dry-run (tradfi tranche, 2026-07-27) classified 21 assigned_vm:NA docs; 4
  verdicted RECLASSIFY carried mixed content (some items genuinely bounded, others still operator/judgment-gated) — per
  the shared conflict-check protocol's fresh-carve-out shape, only the conflict-cleared bounded items are extracted
  here, the source docs stay assigned_vm:NA for their remaining judgment-call items. 9 todos from 3 source docs, all
  parent_epic:infrastructure_master, all checked pairwise and against every active infrastructure_master planning doc
  for file-level collision — zero found.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos:
  [deployment-service, features-service, market-data-processing-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, na-eligibility-audit, satellite-docs, batch-2, plan-hygiene]
related:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/infra_satellite_ao_dispatch_batch2_finalize_2026_07_27.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md,
    /plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/infra_satellite_ao_dispatch_batch2_finalize_2026_07_27.md,
    /plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  /na-eligibility-audit interactive dry-run, tradfi tranche, 2026-07-27 (operator-supervised, sonnet-tier classification
  workers, requested to validate the skill's own Phase 0-5 procedure before its daily cron's first unsupervised fire).
  Phase 1 classified 21 assigned_vm:NA docs; Phase 2 conflict-checked the 5 RECLASSIFY candidates against every active
  parent_epic:infrastructure_master/instruments_master/tradfi_master planning doc — 4 cleared (this batch + its
  instruments_master sibling), 1 (`tradfi_backfill_throughput_followups_2026_07_24.md`) hit a genuine prior claim
  already queued in `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` and was held back, not re-drafted here.
---

# Infra satellite docs — AO dispatch batch 2 (na-eligibility-audit extraction)

## Why this plan exists

The first `/na-eligibility-audit` run (tradfi tranche, interactive dry-run, 2026-07-27) found 3 `assigned_vm: NA` docs
each carrying a mix of genuine judgment-call work (stays NA) and bounded, worker-determinable work that was simply never
assessed against the AO dispatch-scope bar (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` §
"Dispatch-scope eligibility"). Per the shared conflict-check protocol's naming convention
(`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1a), a doc with genuinely mixed content
gets a fresh carve-out — the bounded items land here as new dispatchable todos, the source docs are untouched and stay
NA for their remaining judgment-gated items. The paired finalize plan
(`infra_satellite_ao_dispatch_batch2_finalize_2026_07_27.md`) is responsible for reconciling each source doc's checkbox
once the corresponding todo below is actually done — not this plan.

## Rules this plan follows

- Every todo ends with `Source: <doc>.md #<original-item-number>` for traceability back to the NA doc it was extracted
  from, plus a **Done when** clause.
- Checked pairwise across all 9 todos and against every currently-active `parent_epic: infrastructure_master` planning
  doc (12 docs, incl. `infra_satellite_ao_dispatch_batch1_2026_07_26.md`,
  `candle_canonical_path_migration_execution_2026_07_24.md`, the 4 `cross_cutting_satellite_ao_dispatch_batch*` docs) —
  zero file-level collisions found.
- `sequential:` deliberately unset — these 9 touch disjoint files and are independently dispatchable.
- The source NA docs' own checkboxes are NOT touched by this plan — the finalize twin does that once each todo below is
  actually `[x]`.

## Todos

- [ ] [SCRIPT] P3. **Trim `launch-features-backfill-vm.sh` to its redirect stub.** Delete the unreachable dead body
      (lines ~170-309), the duplicate `lc_verify_tarball_freshness` definition (~274-278 vs ~280-284, keep one), and the
      pre-consolidation module names still referenced in `_python_module_for`. Repo: deployment-service. Source:
      `mdps_features_deadcode_consolidation_2026_07_20.md` #4. Done when: the script contains no unreachable code past
      the redirect stub, `lc_verify_tarball_freshness` is defined once, and `_python_module_for` only names
      post-consolidation module paths — `bash scripts/quality-gates.sh` green.
- [ ] [SCRIPT] P3. **Delete 8 stale `features_*_service` keys from `setup-data-pipeline-vm.sh`'s `SERVICE_TARBALLS`**
      (post-2026-05-08 consolidation; only `features_service` is built now) and adjacently fix the stale `ml_*_service`
      keys in the same map. Repo: deployment-service. Source: `mdps_features_deadcode_consolidation_2026_07_20.md` #5.
      Done when: `SERVICE_TARBALLS` contains no `features_*_service`/`ml_*_service` key that doesn't map to a real,
      currently-built tarball target — `bash scripts/quality-gates.sh` green.
- [ ] [SCRIPT] P3. **Delete 3 named MDPS one-off scripts past their `Delete-when` condition, after verifying each
      condition holds**: `reconcile_mdps_available_at_2026_05_13.py`,
      `reconcile_mdps_available_at_off_by_one_2026_05_10_2026_05_11.py`, `reconcile_1440_nan_placeholders.py`. KEEP
      `benchmark_fullmonth_binance.py` (still reused for MDPS steady-state benchmarking — do not delete). Repo:
      market-data-processing-service. Source: `mdps_features_deadcode_consolidation_2026_07_20.md` #6. Done when: each
      of the 3 named scripts' own `# Delete-when:` marker is re-verified true as of today (cite the check), the 3 files
      are deleted, and `benchmark_fullmonth_binance.py` is confirmed still present and referenced by its live consumer.
- [ ] [DOC] P3. **Repoint `features-service/scripts/sports/smoke_matrix.py`'s stale SSOT citations** (currently cite an
      archived plan + the dead `launch-features-backfill-vm.sh` header) to `launch-features-vm.sh` + the current codex
      smoke-matrix doc. **Citation-only scope** — do NOT physically relocate `smoke_matrix.py` (that relocation is
      separately tracked in `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s "features-service
      coverage/script-canon cleanup" todo, which explicitly carves this citation-only todo out of its own scope; verify
      that todo's status before starting in case its relocation already landed and moved the file). Repo:
      features-service. Source: `mdps_features_deadcode_consolidation_2026_07_20.md` #7. Done when: the script's header
      comment cites only current, live docs.
- [ ] [DOC] P3. **Update `build_canonical_candle_path()`'s docstring example** (unified-trading-library) — it still
      shows the SUPERSEDED "aggregated data_type" semantics (`data_type='deriv_ohlcv_15m'`) instead of the corrected
      SOURCE-keyed form. Not a functional bug (the function is value-agnostic), but could mislead a future maintainer.
      Repo: unified-trading-library. Source: `candle_feature_canonical_path_divergence_2026_07_20.md` #15. Done when:
      the docstring example matches the 2026-07-21 correction (per that doc's Progress Log).
- [ ] [SCRIPT] P3. **Investigate `CEFI:DERIBIT:trades:24h`'s force-leg `off_template=29` classification mismatch** —
      confirm whether the object path already writes `timeframe=1d` (making the docstring's "RAW token" claim stale the
      same way the `data_type` one was, todo above) or whether this is a genuine separate defect. Non-blocking audit.
      Repo: market-data-processing-service. Source: `candle_feature_canonical_path_divergence_2026_07_20.md` #16. Done
      when: a definitive root-cause is recorded (stale-docstring vs. genuine defect) with the checked object path cited;
      if genuine, file a follow-up todo/issue doc rather than fixing inline.
- [x] ✅ [SCRIPT] P2. **Fix `_copy_verify_delete()`'s retry-idempotency gap**
      (`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py:794-831`) — a destination that exists
      but FAILS verification (`SIZE_MISMATCH_KEPT_SRC`/`CRC32C_MISMATCH_KEPT_SRC`) is never re-copied on a subsequent
      run (gated on `dmeta is None`), so this straggler class cannot converge no matter how many re-runs. Fix: treat a
      verification-FAILED existing destination the same as an absent one (overwrite + re-verify), with tests against a
      synthetic bad-destination fixture before trusting it on prod. Source data was never at risk (`KEPT_SRC` never
      deletes source) — script gap, not a data-safety incident. Repo: market-data-processing-service. Source:
      `candle_feature_canonical_path_divergence_2026_07_20.md` #19 (full root-cause:
      `/plans/archive/issues/candle_feature_canonical_path_divergence_history_part2_2026_07_25.md`, "P7c: CEFI retry").
      — market-data-processing-service@beb9fed663a042322717046e0432e4aac1e9273e. `_copy_verify_delete()` now retries
      (overwrite + re-verify) once on any verification failure, whether the destination was freshly copied or already
      existed; 6 new fixture tests (mocked `unified_trading_library.cloud_interface`, no real GCS) cover: fresh-absent
      convergence, existing-good no-copy, existing-bad-SIZE retry-converges, existing-bad-CRC32C retry-converges,
      genuine-mismatch-after-retry keeps source, and SRC_ALREADY_GONE is unaffected. Full `quality-gates.sh` green
      (sentinel = this SHA). **The mop-up pass itself is split to the new todo directly below** — it's a real prod-GCS
      VM-scale operation (historically multi-hour with SPOT preemptions per the P7c progress log), a different-shaped
      unit of work than this code fix, not something to fold into the same dispatch cycle.
- [ ] [SCRIPT] P2. **Run the CEFI mop-up pass now that `_copy_verify_delete()`'s retry-idempotency gap is fixed** (todo
      above, market-data-processing-service@beb9fed663a042322717046e0432e4aac1e9273e). **TRADFI needs no mop-up** —
      confirmed via `candle_feature_canonical_path_divergence_history_part2_2026_07_25.md` lines 666-669 ("P7d: TRADFI
      DONE"): TRADFI's own migration converged to 0 outstanding legacy-path objects and never hit a single
      `KEPT_SRC`-class straggler across either of its two runs — this todo is CEFI-only. The original CEFI apply run
      never logged per-object URIs for `KEPT_SRC`-class outcomes (only
      `"non-success outcome '<TYPE>' at shard-local     index N"`, no path) and its `--out` mapping TSV never uploaded
      (runs exited rc=5, gated on `&&`), so the exact 149 objects are NOT independently known going in — a fresh
      `--dry-run` classify pass over a current CEFI enumeration is required first to relocate them (the P8 fresh-count
      re-verify after the original apply run found these same objects reclassify as `SPLIT_BRAIN_DUPLICATE` once a
      canonical twin already exists, per the same history doc's line ~699 — that disposition is the expected signature
      to search for). Then run `--apply` (MIGRATE/ SPLIT_BRAIN_DUPLICATE gate only, no `--quarantine`/`--content-repair`
      needed for this residual class) against just the reclassified stragglers. Per the infra craft's VM-launch
      discipline: NO fire-and-forget (STARTED <60s + ≥1 progress/hr + terminal STOPPED/FAILED, verified at T+10min),
      SPOT provisioning, idempotent/safe re-run (this todo's own prerequisite fix is what makes it safe — `KEPT_SRC`
      never deletes source on any residual failure, retried or not). Repo: market-data-processing-service. Source:
      `candle_feature_canonical_path_divergence_2026_07_20.md` #19. Done when: a fresh CEFI dry-run classify + `--apply`
      mop-up pass reports 0 remaining `SIZE_MISMATCH_KEPT_SRC`/`CRC32C_MISMATCH_KEPT_SRC` (149-object baseline).
- [x] ✅ [SCRIPT] P2. **Add a Phase-0 `-test-` bucket assertion on the resolved WRITE bucket** to
      `/data-pipeline-check-mdps` and `/data-pipeline-check-features`, closing their fail-open
      `--output-bucket`/`--sink-bucket` mechanism (a skill invocation with a bad bucket flag currently fails open rather
      than refusing before any write). Repo: unified-trading-pm. Source:
      `backfill_smoke_write_path_canonical_audit_2026_07_20.md` #4 (audit § 1). Done when: both skills assert the
      resolved bucket contains `-test-` before any write in non-prod invocations, and refuse loudly (not silently fall
      through) when it doesn't. — unified-trading-pm@0f13ea066. Added new "§2a Resolved-bucket assertion" subsections to
      both `SKILL.md`s: a `case`-statement guard run immediately before every Phase-1 launcher invocation, checking the
      EXACT resolved `--output-bucket`/`--sink-bucket` string for `-test-` and refusing loudly (exit 1) if absent —
      closes the gap where an omitted/mistyped flag silently fell through to PROD.
- [ ] [DOC] P3. **Add an explicit "never pass `--allow-live-prod-writes`" prohibition** to
      `cursor-configs/skills/data-pipeline-check-mtds/SKILL.md`. Repo: unified-trading-pm. Source:
      `backfill_smoke_write_path_canonical_audit_2026_07_20.md` #5 (audit § 1a). Done when: the skill doc states the
      prohibition explicitly, matching the pattern already used elsewhere in that skill for other prod-write guards.

## Deferred (conflict-checked, held back — not drafted here)

- **`tradfi_backfill_throughput_followups_2026_07_24.md`'s "Re-shard equity OHLCV by DATE-RANGE" + "Re-measure CME
  per-root-date cost" items** — both classifier-flagged RECLASSIFY, but Phase 2 found they are ALREADY claimed, combined
  into ONE todo, in `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` (line ~202-224, `status: active`), whose own
  "Done when" clause flips the corresponding checkboxes in the source doc once done. Drafting a competing todo here
  would duplicate live dispatched work — held back, not re-drafted. No operator ruling needed (unambiguous: batch2
  already owns this); reported informationally in the dry-run's chat summary instead of a parked escalation doc.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **2026-08-03 (slot 9, infra)**: shipped the `_copy_verify_delete()` retry-idempotency fix
  (market-data-processing-service@beb9fed663a042322717046e0432e4aac1e9273e, QG-green, 6 new fixture tests). Split the
  "Done when" clause's mop-up-pass requirement into its own todo (below the fix todo) — a real prod-GCS VM-scale
  operation, historically multi-hour with SPOT preemptions, not the same-shaped unit of work as the code fix. Confirmed
  via the linked history doc that TRADFI needs no mop-up (converged clean, 0 `KEPT_SRC` stragglers) — the new todo is
  CEFI-only.
- **2026-08-03 (slot 4, infra)**: shipped the Phase-0 resolved-bucket assertion for `/data-pipeline-check-mdps` and
  `/data-pipeline-check-features` (unified-trading-pm@0f13ea066, prek-green doc-only change). Added a §2a
  "Resolved-bucket assertion" subsection to each `SKILL.md`: a `case`-statement guard, run immediately before every
  Phase-1 launcher invocation, that checks the EXACT resolved `--output-bucket`/`--sink-bucket` string for `-test-` and
  refuses loudly (`exit 1`) if absent — closes the fail-open gap where an omitted/mistyped bucket flag previously fell
  through to a silent PROD write.
