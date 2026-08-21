---
doc_type: plan
title: TradFi legacy-twin bucket deletes — Ikenna sign-off gate
summary:
  Small follow-up forked out of tradfi_v9_stage1_finish_2026_07_06.md (now archived, all its other tasks closed) during
  the 2026-07-24 plan-hygiene line-cap remediation. Carries the single remaining legacy-twin bucket delete todo — after
  the tradfi v9 apply + orphan-sweep E=0 + a byte-verify, the legacy-path twin objects (defi / tradfi / pred; cefi
  previously reported done, **sports is NOT done** — 0 of 34,385 `B_legacy_duplicate` rows pass the 5-part delete-safety
  proof per `sports_legacy_duplicate_triage_2026_07_22.md`, corrected 2026-07-25) can be deleted in a quiet window.
  **UPDATED 2026-07-28** — this todo is no longer operator-sign-off-gated — the §3a reversibility carve-out was extended
  the same day to cover this exact delete class (legacy-object-delete-after-copy) once Part 5's twin-coverage proof
  independently confirms 100% canonical-twin coverage; the todo now dispatches as a normal AO todo with a fresh-check
  dispatch shape (see the todo itself). This plan does NOT re-run or duplicate the dry-run evidence; it references it.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service]
scope: [engineer, admin]
tags: [tradfi, legacy-twin, bucket-delete, operator-signoff, hard-stop, orphan-sweep]
related:
  [
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/migration_verification_orphan_safety_2026_06_10.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: 2026-08-09
parent_epic: instruments_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
effort: xhigh
context_scope:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    instruments-service/scripts/cleanup_legacy_twins.py,
    /plans/active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md,
    /plans/archive/issues/tradfi_legacy_twin_candidate_set_995_to_900_unexplained_shrink_2026_08_05.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/issues/sports_legacy_duplicate_triage_2026_07_22.md,
  ]
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Forked from tradfi_v9_stage1_finish_2026_07_06.md's task 11 (this was the only remaining open todo besides the
  Folded-in-scope Layer-1 certify item, which moved to tradfi_consolidated_closeout_2026_07_18.md in the same
  remediation pass) per the operator-approved plan-hygiene line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 30). Content moved verbatim, not rewritten.
---

# TradFi legacy-twin bucket deletes — Ikenna sign-off gate

> **UPDATED 2026-07-28 — no longer an operator sign-off gate.** The banner below ("do not run any delete without
> operator sign-off") described hard-stop #2 (legacy-object-delete-after-copy) as unconditionally human-only. Operator
> ruling 2026-07-28 (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, extended) makes hard-stop #2
> reversibility-qualifiable the same way hard-stop #1 (plain object/prefix deletes) already was, **once Part 5's
> twin-coverage proof independently confirms 100% canonical-twin coverage (content-verified)** — this only changes WHO
> executes (agent, not human), it never waives Part 5's proof requirement itself. See the todo below for the updated
> dispatch shape. Original banner, preserved for context:
>
> **Do not run any delete without operator sign-off** — this was a hard-stop per `/codex/11-project-management/`
> governance HARD RULES (bucket deletes are human-only) and per `migration_verification_orphan_safety_2026_06_10.md`
> §"HARD-STOP respected: everything up to `--apply` only; G4 `--apply` + G4.5 verified-delete `--apply` stay
> operator-gated" — `cleanup_legacy_twins.py --apply` is listed there alongside the migration `--apply` itself as a
> HARD-STOP. That governing text predates the 2026-07-28 §3a extension and is now superseded by it for this specific
> delete class, conditional on Part 5 clearing.

## Where the dry-run evidence already lives (referenced, not duplicated)

The prerequisite this todo needs (orphan-sweep `orphan_class_E=0` + a byte-verify) was met and evidenced in
`/plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md`'s own task 2 (🎯 GATE MET 2026-07-10 17:17:22 UTC —
`A_canonical_manifested=2,594,017 · B_legacy_duplicate=995 · C_manifest_infra=38 · C2_non_data=7,884,651 · D_junk=105,207 · E_orphan_real=0`
[note: the 2026-07-30 re-sweep updated B_legacy_duplicate from 995→900 — see
`/plans/archive/issues/tradfi_legacy_twin_candidate_set_995_to_900_unexplained_shrink_2026_08_05.md`], over 10,584,946
objects). The report itself lives at
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet` — 900 actionable rows
(0 orphan-E + 900 legacy-B), which is this plan's verified-delete candidate set. Read that task's full entry for the
complete diagnosis trail (taxonomy fixes, the 585-orphan backfill-and-close, the fresh full re-sweep) — it is not
restated here.

## Todo

- [x] ✅ [REVIEW] P1. **Verify (or correct) the "cefi + sports already done" claim in this plan's summary/banner —
      CORRECTED 2026-07-25.** Re-checked `sports_legacy_duplicate_triage_2026_07_22.md` — no evidence closes sports's
      34,385-row population; it independently measures **0 of 34,385 `B_legacy_duplicate` rows** pass the 5-part
      delete-safety proof (every sub-population fails per its own per-row triage). No newer doc supersedes that
      measurement. Corrected the frontmatter summary and body banner below to state sports is NOT yet done, citing that
      doc; left the cefi half of the claim unchanged (out of this todo's scope — no contradicting evidence found for
      cefi in this pass).
- [x] ✅ [DATA] P1. **DONE 2026-07-30 — flipped by na-eligibility-audit (tradfi tranche) against this doc's OWN Progress
      Log evidence; the definition-of-done below is met verbatim.** **Evidence (this doc's Progress Log, 2026-07-30
      doc-triage pass, dispatched from `/plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s
      REVIEW todo — the same batch1 todo the superseded 2026-07-27 note below said this was waiting on)**: the dry-run
      WAS run against the live prod report
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet` — **900 class-B
      legacy twins loaded → 0 deletable, 900 blocked**, every one with reason "canonical twin NOT captured in manifest -
      would delete the only copy". Report path + row count are both cited, so the DoD is satisfied. The RESULT is a
      negative one (Part 5 twin-coverage is 0%, not the 100% the gated delete below requires), which is recorded against
      the delete todo — not a reason to keep this dry-run todo open. Original text and its now-superseded note follow.
      **Run the dry-run (not the delete) as the safe next step**:
      `cleanup_legacy_twins.py --asset-group tradfi --report-uri _index/audit/orphan_sweep_tradfi.parquet --dry-run`
      against the 900 legacy-B candidate rows (see "Where the dry-run evidence already lives" above). This is NOT the
      operator-gated delete — `--apply` stays hard-stopped on Ikenna's sign-off per the banner above; this todo only
      produces the verified-delete candidate list + byte-verify evidence the BLOCKED todo below needs to post.
      Definition-of-done: dry-run output cited (report path + row count), ready for the sign-off ask. **NOTE
      (na-eligibility-audit 2026-07-27)**: this exact dry-run is already claimed as
      `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 2nd todo (`status: active`, `assigned_vm: planning`) — still
      open there too as of this audit. Not reclassified independently; this checkbox stays open until that batch's todo
      lands and its finalize twin flips it here.
- [ ] [DATA] P1. **legacy-twin bucket DELETES (defi / tradfi / pred) — CONDITIONALLY ungated: executes WITHOUT
      operator sign-off ONLY once both fresh checks below clear (Part 5 twin-coverage=100% AND soft-delete
      retention≥604800s on all 3 target buckets); if either fails, this stays operator-gated.** Retagged 2026-07-28
      per the operator ruling in the banner above
      (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a extended, 2026-07-28): hard-stop #2
      (legacy-object-delete-after-copy) is reversibility-qualifiable once Part 5's twin-coverage proof independently
      confirms 100% canonical-twin coverage (content-verified). After the tradfi apply + orphan-sweep E=0 + a
      byte-verify, the legacy-path twin objects can be deleted (cefi previously reported done; **sports is NOT done** —
      0 of 34,385 `B_legacy_duplicate` rows pass the 5-part proof, per `sports_legacy_duplicate_triage_2026_07_22.md` —
      sports deletes stay blocked on that separately, independent of this tradfi/defi/pred gate). **New dispatch shape
      (no operator sign-off needed once both checks below clear):** (1) re-run
      `cleanup_legacy_twins.py --asset-group tradfi --report-uri _index/audit/orphan_sweep_tradfi.parquet --dry-run` (or
      read its already-landed output if the todo above already ran it this session) and re-confirm Part 5's
      twin-coverage is still 100% (content-verified, not path-assumed) for the tradfi/defi/pred candidate rows; (2) run
      a FRESH, same-run `gcs_bucket_soft_delete_retention_seconds(bucket)` check against each of the three target
      buckets (`market-data-tick-tradfi-prd-central-element-323112`, `market-data-tick-defi-prd-central-element-323112`,
      `market-data-tick-pred-prd-central-element-323112`) and cite the actual returned values — do not reuse the
      2026-07-27 cited numbers below as the fresh check; (3) if BOTH clear (Part 5 = 100%, retention ≥604800s on all
      three), execute the delete via the sanctioned UTL helpers (`gcs_delete_object` / `gcs_conditional_delete` — never
      subprocess `gcloud`/`gsutil`), scoped to the 900 tradfi legacy-B candidate rows (+ the equivalent defi/pred
      candidate sets) only, never sports. If either check fails, this stays gated — fall back to §3a's approve-executes
      flow (stage the command, open a structured BLOCKED question, single-session execute on a FINAL operator answer)
      rather than assuming clearance. Cite both fresh check results + the extended §3a section in this plan when done.
      **STATUS 2026-07-10 (historical, preserved): still correctly BLOCKED at that time, NOT run — two real reasons, not
      one.** (1) The task's own literal prerequisite — orphan-sweep E=0 + byte-verify — was not yet available at that
      time; task 2's full sweep was genuinely still in progress that session (see task 2 above, now met — see "Where the
      dry-run evidence already lives" above). (2) That session's dispatch briefing characterized tradfi/defi/pred
      legacy-bucket deletes as "pre-approved per this workspace's standing migration-mechanics decision — proceed," but
      the then-governing SSOT (`migration_verification_orphan_safety_2026_06_10.md` §"HARD-STOP respected: everything up
      to `--apply` only; G4 `--apply` + G4.5 verified-delete `--apply` stay operator-gated") explicitly listed
      `cleanup_legacy_twins.py --apply` alongside the migration `--apply` itself as a HARD-STOP at that time — correctly
      not run then. That governing HARD-STOP is now superseded for this delete class by the 2026-07-28 §3a extension,
      conditional on the two fresh checks above.

  **Note (2026-07-24, forked from `tradfi_v9_stage1_finish_2026_07_06.md`, now archived)**: the task's own literal
  prerequisite (task 2's orphan-sweep) IS now met — see "Where the dry-run evidence already lives" above. The
  `--dry-run` re-run against the fresh report (900 legacy-B candidate rows) is the safe next step for whoever picks this
  up; `--apply` stays gated on Ikenna's sign-off regardless.

  **Note (2026-07-27, sub-agent operator-gate review — left GATED, NOT downgraded, genuinely uncertain which category
  applies).** Checked this todo against the §3a reversibility carve-out
  (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, 2026-07-26): a fresh check today confirms ALL THREE
  target buckets clear the bucket-level precondition (object/prefix-scoped, not a whole-bucket destroy) —
  `market-data-tick-tradfi-prd-central-element-323112`, `market-data-tick-defi-prd-central-element-323112`, and
  `market-data-tick-pred-prd-central-element-323112` each report `soft_delete_policy.retentionDurationSeconds = 604800`.
  **Did NOT downgrade anyway**, because this delete class is specifically legacy-object-delete-**after-copy**
  (v9-migration COPY-not-MOVE, Part 5 of that same doc), which is governed by a SEPARATE, unconditional hard stop (§3
  item 2: "Any legacy-object delete after copy... gated by Part 5") plus the closed disposition vocabulary's own "Who
  may act" column for exactly this disposition class (`yes-twin-confirmed`/`yes-after-verify`: "Human executes; agent
  suggests") — and §3a's own text scopes its carve-out explicitly to **"Hard-stop #1"** only ("Hard-stop #1 above is not
  absolute..."), with no stated amendment to hard-stop #2 or the disposition table. It is genuinely ambiguous from the
  doc alone whether §3a's general bucket-reversibility carve-out was meant to also reach legacy-twin dispositions, or
  whether the disposition table's stricter "Human executes" column is a deliberate, still-binding, separate constraint
  for this delete class specifically (the exact ORPHAN-risk trap Part 5 exists to guard against — a false-positive twin
  match here is a real, unrecoverable-per-cell data loss, not merely an undo-within-7-days mistake). Recommend the plan
  owner/operator resolve this ambiguity once, in `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` itself
  (state explicitly whether §3a extends to legacy-twin/Part-5 deletes or not) rather than re-litigating it per-plan.

  **RESOLVED 2026-07-28 (operator ruling)** — the exact ambiguity flagged above is now closed: §3a was extended the same
  day to explicitly cover hard-stop #2 (legacy-object-delete-after-copy), conditional on Part 5 independently confirming
  100% canonical-twin coverage first — see `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a item 1 and §3
  item 2 (both updated 2026-07-28). This doc's own disposition-table "Who may act" column (§2) was updated in lockstep:
  `yes-twin-confirmed`/`yes-after-verify` now read "Agent executes once §3a's fresh reversibility check clears
  (2026-07-28); else human executes, agent suggests" — the stricter "Human executes" reading this note worried about is
  no longer current. The todo above has been retagged and re-dispatched accordingly; the fresh per-run checks it
  requires are NOT satisfied by this note or by the 2026-07-27 bucket-retention numbers cited above — the executing
  worker must re-query fresh.

- [x] ✅ [CODE] P2. **RULED + EXTRACTED 2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling) →
      `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` (`assigned_vm: planning`).** Checkbox flip
      was missed when the Progress Log entry below was written (na-eligibility-audit 2026-08-16, dispatch agt-45ad7b,
      caught this citing-not-flipped gap) — fixed here. Fix `cleanup_legacy_twins.py::canonical_twin_path()` — it cannot reconstruct the canonical GCS path
      for PRE-HIVE legacy shapes, which is why Part 5's twin-coverage measures 0% for all 900 tradfi class-B candidates
      (root-caused 2026-08-09, see Progress Log entry below — a lookup-logic bug, NOT a manifest registration gap).**
      All 900 tradfi legacy-B candidates share the pre-hive shape
      `raw_tick_data/by_date/day=<date>/data_type=<dt>/<instrument_type_plural>/<VENUE>/<file>` (no
      `asset_group=`/`venue=`/`instrument_type=` hive keys — venue/instrument_type are bare non-hive path segments).
      `canonical_twin_path()` only renames `category=`→`asset_group=` (never present here) and inserts
      `pipeline_mode=batch_<source>` after `day=`, producing a path missing
      `asset_group=tradfi/venue=<V>/ instrument_type=<IT>/` entirely (confirmed via `gcs_describe_object` — the derived
      path does not exist) instead of the real canonical shape from
      `unified_api_contracts.canonical_path_templates("tradfi")`
      (`raw_tick_data/by_date/day={date}/pipeline_mode=batch_{source}/asset_group=tradfi/venue={venue}/ instrument_type={instrument_type}/data_type={data_type}/<file>`).
      Fix: reuse the SAME non-hive-tail venue/instrument_type derivation `migration_orphan_sweep.py::classify_object()`
      step 3.5 already has (the shared `_backfill_parser()` from `backfill_orphan_class_e.py`) to derive
      `(venue, instrument_type)` for a pre-hive legacy path, then build the canonical path by formatting the matched
      `canonical_path_templates("tradfi")` entry (not a partial string splice) — so the two scripts derive the canonical
      shape from the same SSOT instead of two independent (and now provably divergent) implementations. Also handle the
      already-hive-shaped legacy case (the `category=`/`asset_group=` rename path `canonical_twin_path()` currently
      targets) without regressing it — add a unit test covering both shapes. Once shipped, re-run this doc's dry-run
      todo above fresh; a correct twin-coverage measurement is the real gate input, not assumed to hit 100% by this fix
      alone (some candidates may still legitimately be registration gaps — this fix only removes the lookup-logic
      false-negative). **Secondary (optional, same PR if convenient, not blocking)**: `_source_by_cell_from_manifest`
      reads the manifest via a full-width `pd.read_parquet` + `to_dict("records")` over ~7M rows — slow; column-project
      to the same 6 fields `migration_orphan_sweep.py::_load_manifested_cells` already uses. Repo: instruments-service.
      **Done when**: `canonical_twin_path()` (or its replacement) correctly derives the canonical path for a
      pre-hive-shape sample (regression test asserting the derived path matches a real captured canonical object), the
      existing hive-shaped-legacy case still passes, and `quality-gates.sh` is green.

## Progress Log

- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **KEEP-NA, stale citation — reaffirms
  today's own slot-23 finding directly below, no new content.** The sole open item's 2026-07-28-vintage dispatch-shape
  text (re-run dry-run + fresh retention check + execute) is superseded by the fresh finding already recorded here
  today: all 900 legacy-B candidates now read "legacy object no longer exists" rather than a coverage-percentage
  failure, so the real next step is the fresh `migration_orphan_sweep.py --asset-group tradfi` walk tracked in
  `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` (`assigned_vm: planning`), not a re-run of
  this doc's own literal dispatch shape. Not reclassifying — the walk itself hasn't run yet, and this remains a real
  prod-bucket delete gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. `assigned_vm` unchanged.
- **2026-08-17 (slot-23, `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`'s P1 todo)**: the
  `canonical_twin_path()` lookup-logic bug root-caused below (2026-08-09) was fixed prior to this pass
  (instruments-service@271b3d33, 2026-08-14) — verified correct via regression tests + a live-GCS cross-check. **Twin
  coverage re-measured against the existing 900-row `orphan_sweep_tradfi.parquet` report: still 0/900 deletable, but
  the reason changed** — no longer "canonical twin NOT captured" (0% Part-5 coverage); now **all 900 rows report
  "legacy object no longer exists"** — the legacy objects themselves have been deleted from GCS since the report was
  generated (2026-07-30), independently confirmed for one sampled row (legacy URI → `gcs_describe_object` returns
  `None`; its now-correctly-derived canonical twin → resolves to a real object, `last_modified=2026-08-10`). **The
  delete gate below still does NOT clear** — the report this doc's measurement depends on is now itself stale (0
  live candidates, not a coverage percentage), so no coverage number can be trusted until a fresh
  `migration_orphan_sweep.py --asset-group tradfi` walk rebuilds the candidate list — tracked as the new follow-up
  todo in the sibling plan above. Full detail + independent verification evidence in that plan's own Progress Log.
- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA-STALE (already-duplicated) —
  citation gap fixed.** 2 open todos re-read end-to-end. The CODE P2 canonical_twin_path() fix was already ruled +
  extracted per the entry directly below, but its checkbox was never flipped to match — fixed above (checkbox now
  cites `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`). The DATA P1 legacy-twin-delete todo
  stays genuinely gated (twin-coverage last measured 0%, pending the fix above landing + a fresh re-measurement).
  Doc stays NA, now 1 open todo.
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling)**: given the 2026-08-09 finding below
  suggests the 0% twin-coverage measurement may itself be a `canonical_twin_path()` lookup-logic bug — **fix the
  lookup bug first, then let the existing auto-execute-on-100%-coverage rule apply** (not downgraded to
  permanently-human-only, not left as-is on a possibly-broken measurement) — extracted to
  `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` (`assigned_vm: planning`). The delete itself
  stays gated on a fresh, trustworthy 100% coverage measurement.
- **2026-08-09 (tradfi_satellite_ao_dispatch_batch7-003, root-cause investigation, diagnostic-only, no delete/apply
  run)**: **ROOT CAUSE FOUND — this is a lookup-logic bug in `cleanup_legacy_twins.py`'s `canonical_twin_path()`, NOT a
  manifest registration gap.** Read-only investigation against the live prod report
  (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet`, 900 class-B
  rows) + the live tradfi manifest (`_index/availability_index.parquet`, column-projected read — never the whole 40-col
  frame):
  1. **All 900 candidate rows share the identical PRE-HIVE legacy path shape** — e.g.
     `raw_tick_data/by_date/day=2025-01-02/data_type=ohlcv_1m/equities/NYSE/NYSE:EQUITY:ABBV-USD.parquet` — verified by
     grep across the full 900-row report: 0/900 carry an `asset_group=`/`category=` hive key, 0/900 carry a `venue=`
     key, 0/900 carry an `instrument_type=` key (venue/instrument_type are bare non-hive path segments, e.g.
     `equities/NYSE/`). This is the exact shape `migration_orphan_sweep.py::classify_object()` step 3.5 already has
     special-cased handling for (derives venue/instrument_type from the non-hive tail via the shared
     `_backfill_parser()`), which is HOW these 900 objects got correctly classified `B_legacy_duplicate` in the first
     place — `migration_orphan_sweep.py`'s classifier proves the manifest DOES cover these cells.
  2. **Reproduced the manifest cell lookup independently** (both the exact-match shape `cleanup_legacy_twins.py`'s own
     `_source_by_cell_from_manifest`/`_canonical_source_for_cell` use, and the grain-aware `is_covered()` shape
     `migration_orphan_sweep.py` uses) against all 900 rows: **both report 900/900 hits** — the manifest cell lookup
     itself is NOT the defect (no venue-spelling / grain-wildcard mismatch found; ruled out as a hypothesis).
     `_canonical_source_for_cell` correctly resolves `source="databento"` for every sampled cell.
  3. **The actual defect is downstream, in `canonical_twin_path()`'s string-splice.** For the resolved `source`, it only
     (a) renames `category=`→`asset_group=` if present (never present here) and (b) inserts
     `pipeline_mode=batch_<source>` immediately after the `day=` segment — producing, for the ABBV example above:
     `raw_tick_data/by_date/day=2025-01-02/pipeline_mode=batch_databento/data_type=ohlcv_1m/equities/NYSE/NYSE:EQUITY:ABBV-USD.parquet`.
     Confirmed via `gcs_describe_object` this derived path **does not exist** in GCS. Confirmed via
     `unified_api_contracts.canonical_path_templates("tradfi")` the REAL canonical v9 shape is
     `raw_tick_data/by_date/day={date}/pipeline_mode=batch_databento/asset_group=tradfi/venue={venue}/instrument_type={instrument_type}/data_type={data_type}/<file>`
     — `canonical_twin_path()`'s output is missing `asset_group=tradfi/venue=NYSE/instrument_type=equity/` entirely
     (never derives them for the pre-hive shape) and additionally mis-orders `data_type=` (template has it LAST before
     the venue/instrument_type keys, the splice leaves it where the legacy path had it). Every one of the 900 rows hits
     this same defect (same pre-hive shape confirmed for all 900 in step 1), which is sufficient to explain the full 0%
     Part-5 twin-coverage measurement without needing to invoke a registration gap. **Conclusion**: the manifest is NOT
     missing these 900 canonical twins — `cleanup_legacy_twins.py`'s `canonical_twin_path()` cannot reconstruct the
     canonical path for pre-hive legacy shapes (it silently assumes the legacy path is already hive-shaped with
     `asset_group=`/`venue=`/`instrument_type=` keys present, which is false for this candidate set) and needs the same
     non-hive-tail venue/instrument_type derivation `migration_orphan_sweep.py::classify_object()` already has
     (`_backfill_parser()`), then to build the FULL canonical path from `unified_api_contracts.canonical_path_templates`
     rather than a partial insert-only string splice. Filed as a properly-scoped follow-up todo below (fix stays
     separate from this diagnostic-only todo — no delete/apply run, per the plan's own scope). **Secondary, non-blocking
     observation**: `_source_by_cell_from_manifest` itself reads the manifest via `pd.read_parquet(io.BytesIO(raw))`
     (all ~40 columns) then `.to_dict("records")` over ~7M rows — slow (a column-projected equivalent completed in ~40s
     CPU vs. this pattern not finishing within a 2-minute bound in this session's own timing) but NOT the root cause of
     the 0% measurement (the cell lookup itself, once it completes, correctly resolves 900/900 as shown in step 2) —
     worth a P3 efficiency cleanup riding the same fix, not filed as its own todo to avoid a bundled/unscoped change.
- **na-eligibility-audit 2026-08-02** (tradfi tranche, dispatch agt-6397c9): **KEEP-NA, valid — re-verified,
  unchanged.** Sole open checkbox (the legacy-twin bucket DELETE todo) re-read end-to-end via an independent sub-agent
  classification; count reconciled (1/1). The delete gate still correctly does not clear — twin-coverage remains
  last-measured at 0% (2026-07-31), not the 100% the §3a reversibility carve-out requires. Independently, this audit is
  NOT unilaterally reclassifying this todo even though it is technically letter-compliant with the
  safe-idempotent-justification bar (§3a path (c)): it bundles a re-verify step with an irreversible-if-wrong
  multi-bucket (tradfi/defi/pred) prod GCS delete in one todo, which the bounded-outcome bar's "stay skeptical of
  bundled, high-consequence actions" guidance flags for plan-owner confirmation before AO dispatch — recommend the plan
  owner explicitly rule on dispatch-eligibility once/if twin-coverage reaches 100%, distinct from today's "does the gate
  clear" question. Doc stays NA.
- **na-eligibility-audit 2026-07-31** (tradfi tranche, dispatch agt-6d6eaf): **KEEP-NA, valid.** Sole open checkbox (the
  legacy-twin bucket DELETE todo) read end-to-end; count matches tranche-inventory tool (1). The delete gate still
  correctly does not clear — no new dry-run has been re-run since 2026-07-30 (twin-coverage still last-measured at 0%,
  not the 100% §3a reversibility carve-out requires). Nothing changed since the prior verdict; doc stays NA.
- **na-eligibility-audit 2026-07-30** (tradfi tranche): **KEEP-NA, valid — 1 stale item CLOSED.** Both open todos read
  end-to-end. Todo 1 (the `cleanup_legacy_twins.py` dry-run) was flipped `[x]` this pass: its stated definition-of- done
  ("dry-run output cited — report path + row count") is met verbatim by this doc's OWN 2026-07-30 Progress Log entry
  (900 class-B twins loaded → 0 deletable, 900 blocked), and the 2026-07-27 note saying it was waiting on
  `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 2nd todo is superseded — that batch1 todo is what executed it.
  The remaining delete todo correctly stays open and gated: the same fresh dry-run measured Part 5 twin-coverage at
  **0%**, not the 100% the 2026-07-28 §3a reversibility carve-out requires, so the delete gate does NOT clear today. Doc
  stays NA.

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-30 (doc-triage pass, `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`'s REVIEW todo)** — Ran the dry-run
  (default no-`--apply` mode; the `--dry-run` flag named in the todo text does not actually exist on this script's CLI —
  `parser.add_argument`s are `--asset-group`/`--report-uri`/`--cloud`/`--apply`/`--i-understand` only; omitting
  `--apply` IS the dry-run, confirmed via the script's own docstring "Default `--dry-run`"):
  `GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prod .venv/bin/python instruments-service/scripts/cleanup_legacy_twins.py --asset-group tradfi --report-uri _index/audit/orphan_sweep_tradfi.parquet`
  against the live prod report
  (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet`, confirmed present
  before running). **Result: 900 class-B legacy twins loaded from the report (not the 995 cited in this doc's own text
  as of 2026-07-24 — the report has evidently shrunk by 95 rows in the interim, not re-investigated here) → 0 deletable,
  900 blocked.** Every one of the 900 was blocked with reason "canonical twin NOT captured in manifest - would delete
  the only copy" — i.e. Part 5's twin-coverage proof is **0% for this candidate set right now**, not the 100% the gated
  delete todo (below) requires. This is a FRESH, same-session negative result: the delete gate does NOT clear today —
  deletes correctly stay blocked, no `--apply` was run. Full stdout (900 BLOCKED lines) captured in the executing
  session's log; not reproduced here in full — the summary counts above are the load-bearing evidence. Part (1) of the
  combined REVIEW todo ("verify/correct the cefi+sports claim") was already resolved by this doc's own todo 1 (✅ done
  2026-07-25, cites `sports_legacy_duplicate_triage_2026_07_22.md`) — re-confirmed current, no further correction
  needed.

- **2026-07-28 (gate-cleanup pass)** — retagged the legacy-twin bucket delete todo: the 2026-07-27 note's flagged
  ambiguity (whether §3a's reversibility carve-out reaches hard-stop #2) was resolved by operator ruling 2026-07-28
  (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a, extended) — hard-stop #2 is now
  reversibility-qualifiable once Part 5's twin-coverage proof independently confirms 100% coverage. Updated the top
  banner, the todo itself, and the 2026-07-27 note with the resolution + the new fresh-check dispatch shape. No delete
  executed as part of this pass (retag/dispatch-shape only) — the dry-run todo above is still open.
- **2026-07-25** — `/plan-reconcile` fix pass: corrected the "cefi + sports already done" claim (frontmatter summary,
  body banner, BLOCKED-OPERATOR-DECISION todo) to state sports is NOT done — 0/34,385 `B_legacy_duplicate` rows pass the
  5-part delete-safety proof per `sports_legacy_duplicate_triage_2026_07_22.md` — and flipped todo 1 to done with that
  evidence cited. Also fixed `last_updated` (was 2026-06-27, predating this doc's own `created: 2026-07-24`) to
  2026-07-25.
- **2026-07-24** — Forked out of `tradfi_v9_stage1_finish_2026_07_06.md` (task 11) via the operator-approved
  plan-hygiene line-cap remediation (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 30). Content
  moved verbatim; no new work performed. The parent plan's remaining task (Folded-in-scope Layer-1 certify) moved to
  `tradfi_consolidated_closeout_2026_07_18.md` in the same pass, leaving the parent with 0 open todos — it was archived
  to `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md`.
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — still accurate, no changes needed.
- **context-scout 2026-08-06**: re-scouted; fixed a wrong repo-relative path (script lives in instruments-service, not
  unified-trading-pm) and added the new `tradfi_legacy_twin_candidate_set_995_to_900_unexplained_shrink_2026_08_05.md`
  issue doc the body now cites; now 5 entries.
- **na-eligibility-audit 2026-08-07** (tradfi tranche): **KEEP-NA, valid -- re-verified, unchanged.** Sole open todo
  (the legacy-twin bucket DELETE) re-read end-to-end; count reconciled (1/1). The delete gate still correctly does not
  clear -- twin-coverage was last measured at 0% (2026-07-30/31), not the 100% the 2026-07-28 §3a reversibility
  carve-out requires, and no fresher re-run was found. Established ruling not re-litigated (4th consecutive
  KEEP-NA-valid pass). Doc stays NA.
- **na-eligibility-audit 2026-08-08** (tradfi tranche, dispatch agt-29c933): **KEEP-NA, valid -- confirmed via git log
  that this doc's most recent commit IS the 2026-08-07 marker above (provably unchanged since, not just claimed).** Sole
  open todo re-read; count reconciled (1/1). 5th consecutive KEEP-NA-valid pass -- same standing reasons hold: the
  delete gate remains unmet (twin-coverage 0% vs required 100%), and bundling a re-verify step with an
  irreversible-if-wrong multi-bucket prod GCS delete in one todo still flags for plan-owner confirmation before AO
  dispatch even once the gate clears (2026-08-02 reasoning, not re-litigated). Doc stays NA.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-09** (tradfi tranche, dispatch agt-3df41f) [body-hash:2279a6513fd11994]: **KEEP-NA,
  valid -- confirmed unchanged.** Phase-0 flagged this doc as "changed since the 08-08 marker" (git-date fallback), but
  `git diff <08-08-marker-sha>..HEAD` shows the intervening changes are an unrelated `effort: xhigh` frontmatter bump
  (already hash-excluded by `strip_frontmatter()`) plus the context-scout line directly above -- zero todo/verdict
  content changed. Reaffirming the 08-08 verdict without a fresh full re-read; see
  `na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md` for the underlying false-positive class
  this run found and filed.
- **na-eligibility-audit 2026-08-10** (tradfi tranche, dispatch agt-a70469) [body-hash:1edcd67dbf5276f3]: **KEEP-NA,
  valid -- fresh full read found a NEW item the hash-check timing gap hid from every prior pass.** The 08-09 marker
  above reaffirmed via hash-diff only, computed BEFORE a same-day root-cause investigation
  (`tradfi_satellite_ao_dispatch_batch7-003`) added a brand-new second todo
  (`cleanup_legacy_twins.py:: canonical_twin_path()` pre-hive shape lookup bug) that no audit pass had yet assessed --
  this pass is the first fresh full read since. Todo 1 (the destructive 3-bucket delete) stays DEPENDENCY_BLOCKED,
  established reasoning unchanged (twin-coverage last measured 0% vs required 100%). Todo 2 is tagged
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE, high confidence (root cause fully diagnosed with before/after path evidence via
  `gcs_describe_object`, fix reuses an existing derivation helper + an existing UAC SSOT, crisp done-when) -- but per
  the whole-doc RECLASSIFY rule, 1-of-2 bounded keeps the doc KEEP-NA; flagging for a future `/ag-closeout-audit`
  satellite-extraction pass (not this skill's mechanism) rather than promoting unilaterally. `assigned_vm` unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **KEEP-NA, stale-items reaffirmed —
  no new change.** Sole open todo (the 3-bucket legacy-twin DELETE) re-read end-to-end; its embedded dispatch-shape
  text (re-run the dry-run against the existing 900-row `orphan_sweep_tradfi.parquet` report) is still stale per the
  2026-08-17 marker's finding — the walk that would produce a fresh, trustworthy twin-coverage number
  (`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`, `assigned_vm: planning`) has not run in
  the intervening 2 days. Not reclassifying, per the same reasoning: this remains a real prod-bucket delete gated
  per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, and the real next step lives in the already-
  AO-dispatched doc above, not a re-run of this doc's own literal dispatch shape. `assigned_vm` unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Sole open todo (the 3-bucket legacy-twin DELETE)
  remains a real prod-bucket delete gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`; the real
  next step (a fresh twin-coverage walk) lives in `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`
  (`assigned_vm: planning`), not a re-run of this doc's own stale dispatch-shape text. `assigned_vm` unchanged.
