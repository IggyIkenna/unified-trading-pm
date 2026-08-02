---
doc_type: issue
title:
  CF-8 (`available_at` non-null coverage) checks the FULL manifest denominator, not `capture_status=captured` rows —
  likely produces false/misleading REDs fleet-wide, contradicting how every backfill session has measured "fill rate"
summary: >-
  While working the tradfi CF-8 finding (`cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`'s first todo,
  folded into `mtds_available_at_cross_asset_backfill_2026_07_13.md`), re-ran
  `unified_trading_library.cf_manifest_audit.audit()` directly against the tradfi bucket after a real backfill + fix
  landed real progress (captured-row `available_at` fill 69.97% -> ~77-82%). CF-8 still read RED:
  `non-null=3,233,717/6,577,303` — but `6,577,303` is the FULL manifest row count (all 4 `capture_status` states:
  `captured`, `empty_confirmed`, `attempted_failed`, `expected_unattempted`), not just the 1,697,765 `captured` rows.
  `_check_cf8_available_at()` (`unified_trading_library/cf_manifest_audit.py:374-382`) computes `nn =
  df["available_at"].notna().sum()` and `n = len(df)` against the RAW, unfiltered dataframe — no
  `capture_status=='captured'` filter is applied, even though a `capture_status`-filtering pattern already exists
  elsewhere in the same file (`_cells()`, line 284: `cap = df[df["capture_status"] == "captured"]`).

  This directly contradicts the canonical CF-8 definition
  (`plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` line 99: "`available_at` per-row,
  preserve-or-honest-derive; never lookahead / migration-time / read-time") — "preserve-or-honest-derive" only makes
  sense for a row that was actually captured; a non-captured row (empty/failed/expected-unattempted) has no availability
  event to timestamp, so it is structurally impossible for the current full-denominator check to ever reach GREEN unless
  non-captured rows also get some `available_at`-equivalent stamp (no evidence any writer does this intentionally). It
  ALSO contradicts every session in `mtds_available_at_cross_asset_backfill_2026_07_13.md` (the whole multi-week,
  multi-asset-group backfill effort this checker is meant to validate), which has consistently measured and reported
  "available_at fill rate" against `capture_status=='captured'` rows specifically — including the ORIGINAL 2026-07-13
  audit that started that plan (`manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`'s table is
  explicitly labeled "captured rows").
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [cf-manifest-audit, cf-8, available-at, data-correctness, denominator-bug, cross-cutting, manifest-master]
related:
  [
    /plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md,
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/audit/instructions/canonical_form_cross_service_audit_checklist.md,
  ]
created: 2026-08-02
parent_epic: manifest_master
priority: P1
source:
  [
    "unified_trading_library/cf_manifest_audit.py:374-382 (_check_cf8_available_at)",
    "Live re-run: unified_trading_library.cf_manifest_audit.audit('market-data-tick-tradfi-prd-central-element-323112',
    None) — CF-8 RED, non-null=3,233,717/6,577,303 (full manifest), vs captured-only fill of ~77-82% measured
    independently across two sessions",
    "plans/audit/instructions/canonical_form_cross_service_audit_checklist.md line 99 (CF-8 canonical definition)",
    "/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md (every session's captured-row framing)",
  ]
assigned_vm: planning
locked_by:
resolved_by:
  "unified-trading-library@6af7c4b7 (denominator fix, captured-status filter mirroring _cells()) + 2026-08-02T19:15Z
  slot-4 10-bucket re-verification confirming zero net CF-8 verdict change vs the 2026-07-26 rollup"
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    unified-trading-library/unified_trading_library/cf_manifest_audit.py,
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/audit/instructions/canonical_form_cross_service_audit_checklist.md,
  ]
---

# CF-8's denominator is the full manifest, not captured rows — likely mis-scoped, fleet-wide blast radius

> **✅ RESOLVED 2026-08-02.** Both todos shipped: the fix itself (`unified-trading-library@6af7c4b7`, scoping CF-8's
> denominator to `capture_status=='captured'` rows, mirroring the existing `_cells()` pattern) and the fleet-wide
> re-verification (slot 4, 2026-08-02T19:15Z — a fresh 10-bucket `cf_manifest_audit.py --all-ags` run diffed against the
> actual raw 2026-07-26 rollup JSON found ZERO verdict change: the same 5 RED / 5 GREEN split, bucket-for-bucket, both
> before and after the fix — every previously-RED bucket is genuinely RED under the corrected denominator too, full
> evidence in `cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`'s "Denominator-fix re-verification" note).
> Codex-alignment: no new codex SSOT needed — this is a narrow single-function correctness fix (the corrected
> denominator convention is now self-documented in `_check_cf8_available_at`'s own code comment, citing this doc), not a
> new cross-cutting architectural pattern. Moved to
> `/plans/archive/issues/cf8_available_at_denominator_scoped_to_full_manifest_not_captured_2026_08_02.md`; corpus
> referrer (`cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`) repointed to the archive path.

## What I found

See summary above. Concretely: `_check_cf8_available_at(df, cols, n, results)` is called from `audit()` at line 603 with
`df`/`n` = the RAW, unfiltered index dataframe/row-count (all `capture_status` values), not a captured-only subset.
Every OTHER piece of evidence in this codebase — the canonical checklist's own wording, and every session of the active
`mtds_available_at_cross_asset_backfill_2026_07_13.md` plan — treats "available_at fill rate" as a captured-rows-only
metric.

Live reproduction (tradfi, post-backfill): captured rows = 1,697,765, `available_at` non-null on captured ≈
1,307,774-1,389,705 (77.03%-81.85%, two independent measurements this session — see that plan's Progress Log #11/#12 for
the discrepancy note). The RAW `audit()` call instead computed `non-null=3,233,717/6,577,303` (49.2% against the FULL
manifest) — a completely different, much lower number that doesn't match either captured-only measurement, because the
~4.88M non-captured rows (which structurally have no `available_at`) are diluting the denominator.

## Why it matters

- **Blast radius is fleet-wide, not tradfi-specific.** `_check_cf8_available_at`'s signature takes a generic `df`/`n` —
  nothing tradfi-specific about the bug. The 2026-07-26 first-ever-complete rollup
  (`cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`) reported "CF-8 RED on 5 of 10 buckets across 4
  asset_groups" — some or all of those REDs may be this same denominator artifact rather than genuine data gaps, meaning
  the true picture of what's actually broken could be very different from what's currently tracked.
- **It may make CF-8 structurally unreachable-GREEN even after a fully-successful backfill.** If captured-row fill
  reaches 100% but non-captured rows (empty_confirmed/attempted_failed/expected_unattempted — the majority of most
  manifests) never carry `available_at` by design, CF-8 would stay RED forever under the current denominator, regardless
  of how much real backfill work lands — directly undermining the entire `mtds_available_at_cross_asset_backfill` plan's
  exit criterion.
- **Discovered mid-task**, not from a dedicated audit — this session was scoped to tradfi's CF-8 finding specifically
  and found this while re-verifying whether a real backfill had actually turned CF-8 GREEN. Did not attempt the code fix
  inline: this is a semantic change to a fleet-wide correctness gate, not a tradfi-scoped bug, and deserves its own
  scoped fix + verification pass across all 10 buckets (not smuggled into an unrelated tradfi diff).

## What I did NOT do

Did not patch `_check_cf8_available_at`, did not re-run the full 10-bucket rollup to see how many of the currently
tracked CF-8 REDs would flip GREEN under a captured-only denominator, and did not check whether any downstream consumer
of `audit()`'s CF-8 result depends on the current (arguably wrong) full-manifest semantics — worth confirming before
changing it, in case something already compensates for or intentionally relies on this behavior.

## Recommended decision

- [x] ✅ [BACKEND] P1. Fix `_check_cf8_available_at` (`unified_trading_library/cf_manifest_audit.py:374-382`) to filter
      to `capture_status=='captured'` rows before computing `n`/`nn`, mirroring the existing `_cells()` pattern (line
      284). Add a regression test with a mixed-capture-status dataframe (some captured+filled, some captured+blank, some
      non-captured+blank) asserting CF-8 keys only off the captured subset. Grep for any caller of `audit()`/`run_all()`
      that reads the CF-8 result and might depend on the current full-manifest semantics before shipping (data-status
      UI, alerting, gates) — update or confirm unaffected. Repo: unified-trading-library. —
      unified-trading-library@6af7c4b7. Grepped for `results["CF-8"]`/`audit()`/`run_all()` callers outside
      `cf_manifest_audit.py`: none found — `run_all()`'s only consumers are the JSON rollup file and the process exit
      code (any-RED -> exit 1); no UI/alerting/gate reads the per-key CF-8 result directly. Added 2 regression tests
      (`test_check_cf8_available_at_keys_off_captured_rows_only`,
      `test_check_cf8_available_at_green_when_all_captured_rows_filled`) proving the captured-only denominator and that
      the fix makes a previously-unreachable GREEN reachable. QG green, shipped via quickmerge.
- [x] ✅ [DATA] P2. **DONE 2026-08-02T19:15Z (slot 4).** Re-ran `cf_manifest_audit.py --all-ags` (all 10 prod buckets,
      read-only, memory-bounded via `run-bounded-analysis.sh` — `--mem-cap` needed raising to 40G on this host, since
      the fallback `ulimit -v`/RLIMIT_AS mechanism requires materially more headroom than the deployed job's own 32Gi
      RSS-based cgroup cap for the same workload, confirmed live on the 39.4M-row defi bucket) and diffed against the
      ACTUAL raw `gs://cf-manifest-audit-central-element-323112/cf_audit/2026-07-26.json` (pulled directly, not the
      prose table). **Result: zero verdict change** — identical 5 RED / 5 GREEN split, bucket-for-bucket, before and
      after the fix. None of the 5 previously-RED buckets flipped GREEN under the corrected denominator; the 5
      previously-GREEN buckets had already reached literal 100% `available_at` fill across ALL rows (captured +
      non-captured), a strictly stronger bar than the corrected check requires, so they were never denominator-diluted
      false REDs. Concretely: `market-data-tick-cefi-prd` 29.20% (1,223,809/4,191,160), `market-data-tick-tradfi-prd`
      81.92% (1,395,684/1,703,744), `market-data-tick-sports-prd` 82.17% (503,722/613,034),
      `instruments-store-sports-prd` 91.56% (5,856,820/6,396,870), `market-data-tick-pred-prd` 90.48% (318,065/351,535)
      — all confirmed GENUINE captured-row fill gaps, not checker artifacts. Updated
      `cf_manifest_audit_first_full_rollup_findings_2026_07_26.md` (new "Denominator-fix re-verification" note + the
      pred-tick todo) with the corrected picture. Repo: NA (audit + doc update only, as scoped).
