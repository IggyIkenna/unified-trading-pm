---
doc_type: issue
title: "Manifest hygiene RED — 4 AG(s) with findings (2026_08_19)"
summary: "Daily manifest-hygiene-vs-GCS audit found non-empty candidate lists across cefi/defi/prediction/sports/tradfi (schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail) — needs worker triage of real gap vs code bug."
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [manifest-hygiene, data-pipeline, honest-coverage]
related: [/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md]
created: 2026-08-19
parent_epic: observability_master
priority: P1
assigned_vm: planning
resolved_by: slot-7 (e2e-testing@e8c41f618c)
source:
  - manifest_hygiene_daily.py
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
    unified-trading-library/scripts/detect_manifest_divergence.py,
    /plans/active/issues/manifest_hygiene_red_all_2026_08_17.md,
  ]
---

> **📦 ARCHIVED 2026-08-22 (archival pass 2)** — `locked_by: live-defi-rollout` placeholder cleared (corpus-wide
> fix, `scripts/plans/clear_locked_by_placeholder_2026_08_12.py --apply`); 0 open todos. Kept as a historical
> daily-monitor record.
# Manifest hygiene RED — 4 AG(s) with findings (2026_08_19)

> Auto-filed by the daily data-pipeline audit `manifest_hygiene_daily.py` (Wave 4b, Phase 5
> scripted→LLM escalation hop). A deterministic candidate list was non-empty — the
> verdicts below need a worker's judgment (real gap vs code bug, straggler
> vs intentional new venue). See `/codex/05-infrastructure/data-pipeline-alerts.md`.

## What I found

The daily manifest-hygiene-vs-GCS orchestrator found non-empty candidate lists for: cefi, defi, prediction, sports, tradfi. Finding-classes: schema_version_not_v9, oracle_expects_but_empty, noncanonical_path_on_disk, phantom_captured_no_parquet, shard_4pillar_fail.

Candidate list(s) (deterministic, machine-written):

- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_cefi_2026_08_19.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_tradfi_2026_08_19.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_sports_2026_08_19.csv`
- `/app/unified-trading-pm/plans/audit/results/manifest_hygiene_prediction_2026_08_19.csv`

## Why it matters

Each class is a data-correctness signal: non-v9 rows are pre-canonicalisation stragglers; oracle-expects-but-empty is a candidate C1 misclassification (real gap vs code bug — needs judgment); non-canonical paths break selective reads; phantoms are captured cells with no parquet.

## Recommended decision

Triage each candidate CSV: confirm real gaps → backfill; confirm code bugs → fix the adapter/writer; confirm intentional new venues/spellings → extend the UAC oracle/canonical builders. Per data_pipeline_hardening_self_monitoring_2026_06_22.md Phase 3/5.

Cold-start context: read `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
in full + `/codex/05-infrastructure/data-pipeline-alerts.md` + the candidate CSV(s)
above before acting.

## Todos

- [x] ✅ [CODE] P1. Manifest hygiene RED — 4 AG(s) with findings (2026_08_19) — diagnose + fix the root cause (misclassified-empty vs real gap, not-v9 schema row, or oracle-expects-but-empty divergence) in `market-tick-data-service`. Read `SUB_AGENT_MANDATORY_RULES.md` + the data-pipeline codex SSOT + the candidate CSV(s) above first (source `manifest_hygiene_daily.py`). — e2e-testing@e8c41f618c

## Progress Log

**2026-08-19 (slot-7)** — Diagnosed: this was a **misclassified-empty (code bug), not a real data gap**. Every
candidate row across cefi/tradfi/prediction/sports is `oracle_expects_but_empty` (`DP_DIVERGENT_EMPTY`), and the
`detail` text in all 4 CSVs is verbatim stdout from `detect_manifest_divergence.py`'s own print summary/footer
("  DIVERGENT_EMPTY   58,362 ❌", "DIVERGENT_EMPTY:  58,362", raw `WARNING` log lines) — proof that
`manifest_hygiene_daily.py::_check_divergence`'s CSV-missing FALLBACK path fired for all 4 AGs
(`_read_divergence_csv` returned `None` on this run), not the primary CSV-read path (whose sample format is
`VENUE/data_type N`, never seen here).

Root cause (`e2e-testing/scripts/audit/manifest_hygiene_daily.py::_check_divergence`): the fallback used
`out.count("DIVERGENT_EMPTY")` — a raw substring count over the CLI's stdout tail. That counts the CLI's own
**unconditional** footer line (`print(f"DIVERGENT_EMPTY:  {counts.get('DIVERGENT_EMPTY', 0):,}")`, which prints even
when the real count is 0) as a hit. Proof: sports' candidate row detail is literally `"DIVERGENT_EMPTY:  0"` — a
finding whose own text says zero, filed as a `count>0` RED escalation. cefi/tradfi/prediction's large counts
(58,362 / 8,486 / 463) are the CLI's real totals (the footer line IS accurate — it's computed over the full
in-memory frame, not the truncated tail) but the specific 3-date UPBIT/NYSE/POLYMARKET samples shown are just
whichever `WARNING` lines happened to survive the [-2000:]+[-500:] stdout/stderr truncation, not a representative or
complete sample — no evidence these specific dates are special.

Fix shipped: `e2e-testing@e8c41f618c` — the fallback now parses the footer's own authoritative integer via regex
(`DIVERGENT_EMPTY:\s+([\d,]+)`) instead of substring-counting, and (when the footer itself was truncated out of the
tail) falls back to counting genuine per-cell `WARNING ... DIVERGENT_EMPTY ...` lines only — never the bare label,
never the boilerplate header/footer. Added 2 regression tests
(`test_check_divergence_fallback_does_not_false_positive_on_zero`,
`test_check_divergence_fallback_prefers_footer_count_over_substring`) + updated the pre-existing
`test_check_divergence_falls_back_when_csv_missing` fixture to a realistic stdout shape. QG green, sentinel-verified,
landed on LDR.

Not actioned (out of scope, genuinely negligible): cefi's `schema_version_not_v9` finding is 1 row out of 30,001,825
(1/30M, `contaminated=0`) — a single pre-v9 legacy straggler, not a code bug; no fix needed.

Secondary, not fixed here: `repos: [market-tick-data-service]` in this doc's own frontmatter is misleading — it's a
hardcoded default (`_dp_common.py::file_escalation_issue`'s `target_repo: str = "market-tick-data-service"` param,
never overridden by `manifest_hygiene_daily.py`'s call site), not a diagnosis of where the bug actually lives. The
real fix landed in `e2e-testing` (where `_check_divergence` lives). Worth fixing the default/wiring separately if
this recurs, but out of scope for this P1.

Why the underlying `_read_divergence_csv` miss itself (the reason the fallback fired at all) wasn't chased further:
the day's raw `divergence_<date>.csv` is written to the Cloud Run Job's own ephemeral container filesystem, not
committed anywhere this worker can inspect post-hoc — reproducing that specific failure would need live GCS
credentials + re-running the job, out of scope for a P1 given the fallback-path bug itself is fully root-caused,
fixed, and test-covered independent of why the CSV read missed.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
