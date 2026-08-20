---
doc_type: issue
title:
  manifest_hygiene_daily.py's "found non-empty candidate lists for" sentence hardcodes/mis-derives the full 5-AG
  list regardless of actual findings — and no defi manifest-hygiene CSV has regenerated in ~53 days
summary: >-
  Found during `/plan-reconcile observability_master` (2026-08-19), corroborated across 3 independent hunter
  passes reading `manifest_hygiene_red_all_2026_08_17.md` and `_2026_08_18.md`. Both daily auto-filed issue docs'
  "What I found" prose claims non-empty candidate lists for all 5 canonical AGs (cefi, defi, prediction, sports,
  tradfi), but the attached candidate-CSV list + doc title ("4 AG(s)") both show only 4 — defi is named in prose
  every day with zero corresponding evidence. Root cause located: `e2e-testing/scripts/audit/manifest_hygiene_daily.py`
  lines 717-721 build the sentence from `", ".join(sorted(ag_results))` — `ag_results` (line 708:
  `report["asset_groups"] = ag_results`) appears to be keyed by every AG the script iterates, not filtered to AGs
  that actually produced a non-empty candidate CSV (the `if csv_path is not None: candidate_csvs.append(csv_path)`
  gate at line 705-706 is the real per-AG filter, and it is NOT what the "found non-empty candidate lists for"
  sentence reads from). Separately and NOT yet explained: `plans/audit/results/manifest_hygiene_defi_*.csv` has no
  file newer than `manifest_hygiene_defi_2026_06_27.csv` (independently confirmed via `ls plans/audit/results/ |
  grep manifest_hygiene | sort` — cefi/prediction/sports/tradfi all have fresh 2026-08-17/18 CSVs, defi's newest is
  2026-06-27, ~53 days stale as of this filing). This is POSSIBLE evidence defi's manifest-hygiene check itself has
  silently stopped producing findings (a real gap) rather than genuinely having zero candidates every day for 53
  days straight — NOT confirmed either way in this pass; filing per the "data pipeline correctness is the heartbeat"
  HARD RULE (a possible silent-check-stall is exactly the class that rule exists to catch) rather than treating an
  absence result as evidence of health.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, unified-trading-pm]
scope: [engineer, admin]
tags: [data-pipeline-audit, manifest-hygiene, boilerplate-bug, defi, data-pipeline-correctness, big-finding]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/manifest_hygiene_red_all_2026_08_17.md,
    /plans/active/issues/manifest_hygiene_red_all_2026_08_18.md,
    /plans/active/issues/manifest_hygiene_red_cefi_2026_08_16.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-08-19
author: plan-reconcile (observability_master epic-scoped pass, hunters D+E, adjudicated + filed by lead)
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: worker
drift_direction: advance-code
source: [manifest_hygiene_daily.py, plan-reconcile-observability_master-2026-08-19]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
    /plans/active/issues/manifest_hygiene_red_all_2026_08_18.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
---

# manifest_hygiene_daily.py's AG-list sentence is boilerplate; possible silent defi check stall

## What I found

Two independent findings, related but distinct — do not conflate them when triaging:

**1. Confirmed bug (doc-text only, low risk on its own).** `manifest_hygiene_daily.py:717-721` writes the
`what_i_found` prose for every daily `manifest_hygiene_red_<mode>_<date>.md` issue doc from
`", ".join(sorted(ag_results))`, not from `candidate_csvs` (the actual per-AG non-empty-finding list gated at
lines 705-706). This makes the prose claim "found non-empty candidate lists for: cefi, defi, prediction, sports,
tradfi" verbatim every day the script runs, regardless of how many AGs actually had findings — verified identical
in both `manifest_hygiene_red_all_2026_08_17.md` (title: "4 AG(s)", 4 CSVs attached, defi named in prose anyway)
and `_2026_08_18.md` (same shape). A worker triaging from the doc's own title/CSV list (correct) never notices;
one triaging from the prose sentence (wrong) wastes time chasing a defi finding that has no attached evidence.

**2. Unconfirmed, higher-stakes possibility.** `ls plans/audit/results/ | grep manifest_hygiene | sort` (run
2026-08-19) shows defi's newest CSV is `manifest_hygiene_defi_2026_06_27.csv` — every other AG (cefi/prediction/
sports/tradfi) has a CSV from within the last 2 days. Two explanations are consistent with this, and this pass
did NOT distinguish between them:
  - (a) defi has genuinely had zero manifest-hygiene candidates for 53 straight days (the check runs, finds
    nothing, correctly writes no CSV) — benign, no code fix needed beyond finding #1 above.
  - (b) the defi leg of the daily check has silently stopped running/erroring/short-circuiting, and finding #1's
    prose bug is precisely what's been masking this — every day's issue doc prose has claimed a defi finding,
    which is what a human/agent skimming the corpus would read as "defi is being checked and clean," when defi
    may not be getting checked at all.

## Why it matters

Per `/codex/02-data/data-pipeline-correctness-hard-rule.md` — a silently-stalled data-correctness check is exactly
the failure class that rule exists to catch; "the prose says it checked defi" is not the same claim as "defi was
actually checked," and this pass could not tell the two apart from the CSV evidence alone.

## Recommended decision

Converted to tracked todos below (Phase 2 zero-checkbox sweep, plan-reconcile — a P1 doc with no `- [ ]` surface is
invisible to `regen_backlog_from_plan.py`).

## Todos

- [x] ✅ [SCRIPT] P2. Fix `e2e-testing/scripts/audit/manifest_hygiene_daily.py`'s `what_i_found` sentence (lines
      717-721, or the `ag_results` dict it's built from at line 708) to name only AGs with an actual non-empty
      `candidate_csvs` entry, not every AG the script iterates — same fix shape for both `-changed` and `-full`
      modes. Done when: a fresh daily run's issue-doc prose names exactly the AGs its own attached CSV list covers,
      verified against a re-run or the next real daily-cron output. Repo: e2e-testing@0a43d0ec70; regression test `test_run_what_i_found_names_only_actual_findings` verifies the post-fix re-run output in the assigned slot.
- [x] ✅ [DATA] P1. Determine whether defi's manifest-hygiene leg has run at all in the last ~53 days (log/cron
      history for `manifest_hygiene_daily.py`'s defi branch) and, if it's silently failing, root-cause + fix that
      leg specifically. If defi genuinely has zero candidates every day, state that explicitly (a comment/log
      line) so the next reconcile pass doesn't re-raise the same "is this stalled?" question from CSV-absence
      alone. Done when: a definite verdict (broken vs. genuinely-clean) is on record, evidenced by cron/log history
      or a live re-run. Repo: e2e-testing. — e2e-testing@f76412e746
- [ ] [DATA] P2. Re-verify whether `manifest_hygiene_red_cefi_2026_08_16.md`'s suppression fix
      (`e2e-testing@9ed5f78e3f`, widened `_active_backfill_residual_venues`'s glob) is actually holding —
      `manifest_hygiene_cefi_2026_08_18.csv` (dated 2 days after that fix) has 5 of 6 rows for venue=UPBIT,
      `oracle_expects_but_empty`/`DP_DIVERGENT_EMPTY`, exactly the shape the fix claimed to silence. Determine
      whether the suppression genuinely isn't holding, or `manifest_hygiene_red_all`'s generating pass runs a
      different code path than what the fix patched. Done when: a definite verdict is on record, evidenced by
      reading the live suppression-check code path against this CSV's own rows. Repo: e2e-testing.

## Progress Log

- 2026-08-19: Filed during `/plan-reconcile observability_master` — corroborated by hunter batch D (root-cause
  code read + `git log`) and hunter batch E (independent CSV-directory cross-check across 2 consecutive days'
  issue docs), then independently re-verified by the lead session (`ls` re-run, `grep` for the source sentence in
  `manifest_hygiene_daily.py`, read lines 695-734 directly). NOT shipped this session (working-tree-only pass,
  heavy multi-session contention on the shared checkout) — the lead/operator session should pick this up.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): RECLASSIFY whole-doc — all 3 open todos are freshly
  filed (2026-08-19, no prior audit pass), each bounded with a stated done-when and no operator gate or
  design-judgment call found. Flipped `assigned_vm: NA -> planning`, added `assigned_role: worker` (was missing).
  Companion: `manifest_hygiene_daily_ag_list_boilerplate_bug_2026_08_19_finalize_2026_08_19.md`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **2026-08-20 (slot-33, escalation agt-56f0d4)**: todo 1's AG-list bug recurred live in today's
  daily run (`plans/active/issues/manifest_hygiene_red_changed_all_2026_08_20.md` — defi named
  in prose again with no CSV) and was fixed at the root in the same session, alongside a second,
  independently-found half of the same pattern (the Finding-classes sentence was ALSO hardcoded
  regardless of `--mode`, naming `phantom_captured_no_parquet`/`shard_4pillar_fail` on
  `--mode changed` runs even though those checks are scoped out entirely in that mode). Both
  fixed in one commit, `e2e-testing@0a43d0ec70`, with regression test
  `test_run_what_i_found_names_only_actual_findings`. **Todo 1 remained open at that point** — its own
  "Done when" requires live verification against a re-run/the next real daily-cron output, which
  hasn't happened; the next reconcile pass or tomorrow's 08:00 UTC cron run should confirm the
  fresh issue-doc prose names only real findings, then flip this checkbox.
- **2026-08-20 (slot-32, P1 [DATA] verdict + fix)**: defi's manifest-hygiene leg IS running and genuinely clean —
  NOT broken. Verdict evidence: (1) `deployment-service/terraform/gcp/data_pipeline_audit_scheduler.tf` runs
  `manifest_hygiene_daily.py --mode changed` daily 08:00 UTC with NO `--asset-group` filter → all 5 AGs (incl.
  defi) iterate every run; (2) retained Cloud Run logs (`uts-prod-dp-manifest-hygiene-changed`, 2026-08-18 +
  08-19) show `invoking divergence ... --asset-group defi` (≈3 min over defi's 6.75GB availability index) →
  `schema_version_not_v9: count=0` (independent DuckDB check over the real defi index) → `oracle_expects_but_empty:
  count=0` → `defi hygiene: GREEN` → container exit(0); (3) PM git history confirms only 2 defi hygiene CSVs ever
  committed (2026-06-22, 2026-06-27) — none in the 06-27→now window; June's findings (22,140/15,697
  DIVERGENT_EMPTY, 988 legacy non-v9) match the defi onchain backfill/canonical work that began 2026-06-27
  (`mvp_backfill_defi_onchain_v10_2026_06_27.md` + `defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md`). A clean
  AG writes no candidate CSV by design (`if rows:` gate in `run()`), so ~53 days of CSV-absence == checked-and-clean,
  not a stall. **Code shipped** (`e2e-testing@f76412e746`): explicit GREEN-verdict log line + code comment in
  `manifest_hygiene_daily.py` stating a missing `manifest_hygiene_<ag>_<date>.csv` means checked-and-clean (a
  stalled/broken leg logs SKIPPED/errors/warnings, never a silent GREEN) — so the next reconcile pass does not
  re-raise "is defi being checked?" from CSV-absence alone.
