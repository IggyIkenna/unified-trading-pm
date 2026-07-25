---
doc_type: issue
title:
  Half-time odds — SFI's derived half-time DOES carry half-time ODDS (not just match state), and it is the DENSER
  source; the 746,928 legacy in-play rows are per-bookmaker FULL-TIME-market prices on a coarse grid, of which only
  ~3.1% are PIT-usable half-time-break quotes — and the HT-RESULT market exists in NEITHER source
summary:
  'Read-only investigation answering the operator''s 2026-07-16 question ("we want half time odds — is there knowledge
  of this from SFI derived half time?"), commissioned to settle OR-5b(c) before the `market-data-tick-sports` delete.
  **The premise that SFI is match-STATE-only is FALSE.** The captured SFI contract `sfi_progressive_stats` (entity
  `progressive_stats`) declares **12 odds/PRICE columns** (`odds_1x2_home/draw/away`, `odds_ou_over/under/line`,
  `odds_ah_home/away/line`, `odds_asian_corner_over/under/line`) plus `ht_start_timer`/`ht_end_timer`, and they are
  **live and populated**: measured on real parquets, `odds_1x2_home` is 90% non-null overall and **100% non-null inside
  the half-time break** (2550-2999s), with **31/31 sampled fixtures (100%) across 2021→2026 and 5 leagues carrying 1X2
  odds quoted DURING the HT break**. They are genuine repriced in-play quotes, not a frozen pre-match price (28-41
  distinct values per match; one fixture drifts 3.3 at kickoff → 36.0 at HT → 301 late). SFI covers 2020→2026 over a
  **superset** of the 10 leagues that have legacy in-play rows. **What SFI does NOT give**: bookmaker identity (one
  anonymous consensus series — no `bookmaker` column), no exchange lay side, no cross-book dispersion. **The 746,928
  in-play rows** (69-object sample, 2020-2026, 300,194 rows / 14,876 in-play = 4.96%) are **per-bookmaker** (23 books:
  pinnacle, matchbook, betfair_ex_uk/eu, …) but carry **only full-time markets** — `h2h`/`totals`/`spreads`/`h2h_lay`,
  **zero HT-specific markets, in-play OR pre-match** — on a **coarse grid** (+5/+15/+30/+45/+60/+75/+90/+120), not
  continuous. Against the features-service HT odds PIT gate (`_apply_ht_odds_pit_gate`, default cutoff `bm_mtk >= -55`):
  **only 3.1% (+45..55) is PIT-usable HT-break data**; 20.3% (+56..62) and 25.7% (2nd half) and 17.0% (post-match) are
  **actively REJECTED as 2nd-half leakage**. **The horizon ladder has NO HT bucket** — `TIER1_HORIZONS` is 8 pre-match
  buckets T-24h…T-0 (the "T-0/HT" framing in circulation is wrong). **BIG FINDING**: `assign_horizon_buckets_vectorised`
  applies `nearest_idx[vals < 0] = N_BUCKETS - 1` **AFTER** the staleness rejection, resurrecting dropped post-kickoff
  rows into T-0 — measured **184/282 (65%) of sampled canonical T-0 rows are post-kickoff, bm down to −71.1 min**
  (lookahead leakage; adjacent to `sports_odds_stale_fixture_reinjection_2026_07_14`). **The HT-RESULT market
  (first-half 1X2) is captured NOWHERE** — `ht_odds_home_implied` reads `first_half_*_odds` from the **dormant,
  never-captured** `CanonicalProgressiveOdds`; SFI''s provider API serves it (`h1_*` in `SFMatchProgressiveOddsRaw`) but
  the adapter''s `_extract_odds` never reads it → **re-fetchable from SFI, NOT recoverable from the legacy bucket**.
  Recommendation: **OR-5b(c) → B-REFINED** — recover the in-play rows as a ~zero-marginal-cost rider on the already-
  recommended OR-5b(b) option-D G1 read-split-merge, into a DISTINCT population quarantined from the pre-match bucketing
  path (never merged into the T-0 lineage, which is already 65% contaminated).'
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    market-tick-data-service,
    unified-api-contracts,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags:
  [
    sports,
    odds,
    halftime,
    soccer-football-info,
    in-play,
    bucket-canonicalisation,
    data-correctness,
    lookahead-bias,
    investigation,
    read-only,
  ]
related:
  [
    ./mdt_legacy_canonical_row_gap_2026_07_16.md,
    ../sports_legacy_bucket_cutover_2026_07_16.md,
    ./sports_odds_stale_fixture_reinjection_2026_07_14.md,
    ./sports_odds_horizon_bucket_malformed_tick_field_2026_07_15.md,
    ../../epics/sports_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-25
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  [
    "market-data-processing-service@3bf56ff (T-0 ordering fix)",
    "features-service@c57cc753 (HT honest absence)",
    "features-service@bf6fc2f4 + ml-service@c0603cb (closing-line leak fix)",
    "uac@96cdfc4f + instruments-service@1f7c51cf + features-service@5a8684ed (SFI h1_* capture)",
    "market-data-processing-service@9f2560b7 (fixture-identity collapse)",
  ]
source:
  [
    'operator question 2026-07-16 — "we want helf time odds is there knowledge of this from sfi derived half time?"',
    "OR-5b(c) — disposition of the 746,928 post-kickoff / in-play rows",
    "./mdt_legacy_canonical_row_gap_2026_07_16.md",
  ]
---

# Half-time odds: does SFI's derived half-time already give us them?

> **⚠️ STATUS CORRECTION 2026-07-25 — `status:` flipped back to `open`. Read this first.**
>
> This doc's frontmatter previously read `status: resolved`. That was WRONG. The
> `## RE-TRIAGE (2026-07-23, count corrected 2026-07-24)` section below is this doc's own live self-correction: it
> verdicts the ORIGINAL core investigation "RESOLVED BY LATER WORK" (all spun-off P0/CODE items shipped and
> independently re-verified — T-0 ordering fix, HT honest absence, the closing-line/CLV leak fix, the SFI `h1_*`
> capture-gap fix, and the fixture-identity-collapse fix), but a direct `grep -n '^- \[ \]'` against the live file shows
> this doc still carries **5 genuinely open checkboxes**: (1) [CODE] P1 `_apply_ht_odds_pit_gate`'s default-cutoff
> branch still unreachable in prod; (2) [DATA] P1 blank-`fixture_id` raw generation still open, no upstream-writer fix
> found; (3) [DATA] P1 `verify_ml_readiness.py`'s 95% non-NULL threshold still a flat un-rebased constant; (4) [DATA] P1
> market-data-sports manifest reconciliation for the 2,436 deleted T-0 shards still blocked on its stated dependency
> (T6.1 merge not yet done); (5) [ML] P2 retrain the CLV models after the ODDS_FEATURES recompute — prerequisite now
> done but retrain not yet run. **Re-verified independently 2026-07-25** (this pass, not inherited from the
> 2026-07-23/07-24 passes): the count is still exactly **5**, same 5 items, content unchanged. `status:` stays `open`
> until all 5 close — see "Open Todos" below.
>
> **This doc was also split 2026-07-25** (was 1,513 lines, over the `plans/active/issues/*.md` 1000-line hard cap —
> `scripts/plan-hygiene/check_line_caps.sh`). The original read-only investigation narrative (SFI column inventory, the
> 746,928 in-play rows anatomy, the T-0/HT horizon analysis, the features-consumption audit, the OR-5b(c) B-REFINED
> verdict, cross-checks, loose ends) plus every shipped-fix Progress Log entry moved verbatim to
> `/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_history_part1_2026_07_25.md` +
> `/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md` (2 chunks — the history itself
> was over the active-tier 1000L cap as one file). This parent keeps the frontmatter, a one-paragraph answer, the 5 open
> todos, and the RE-TRIAGE section (per the `plan_line_cap_remediation_2026_07_23.md` § FINAL RESOLUTION
> extract-to-archive-bound-history-child pattern).

> **READ-ONLY investigation. Zero mutations** — no writes, no copies, no manifest changes, no bucket changes.

## THE ANSWER — one sentence

**Yes — SFI's derived half-time already carries half-time ODDS, not merely half-time state: the captured
`sfi_progressive_stats` contract has 12 populated price columns and 100% of sampled fixtures have 1X2 odds quoted
_during_ the half-time break at 30-second granularity — so the half-time market LEVEL survives the bucket delete; what
dies with the bucket is the _per-bookmaker_ half-time dispersion (~3.1% of the 746,928 rows, ~23k quotes), and the
HT-RESULT market (first-half 1X2) is in NEITHER source and must be re-fetched from SFI regardless.** Recommendation
(OR-5b(c) → B-REFINED) and every spun-off P0/CODE fix from this investigation shipped and is independently re-verified
in the RE-TRIAGE section below. Full original investigation, evidence, and shipped-fix Progress Log:
`/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_history_part1_2026_07_25.md` (investigation + lookahead-leak

- SFI `h1_*` + closing-line-leak legs) and
  `/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md` (T-0 recompute + collapse
  recompute + ODDS_FEATURES recompute + fixture-identity-collapse + phantom-block/pivot legs).

---

## Open Todos (re-verified 2026-07-25 — 5 open, re-derived from a live grep, not inherited)

> Moved here from their original positions in the two "Todos" lists (the "lookahead-leak fix leg" list in history part
> 1, and the "T-0 recompute leg" list in history part 2 — see those docs for the DONE/PARTIAL items around them) during
> the 2026-07-25 line-cap split. Text unchanged from the original.

- [ ] [CODE] P1. **`_apply_ht_odds_pit_gate`'s default-cutoff branch is unreachable in production.** The only caller
      guards with `if ht_break_minutes:` (`odds_features_exporter.py:232`), so the `if not ht_break_minutes:` default
      `-55` branch (lines 65–83) can never run outside tests → **when HT break times are unknown, NO PIT gate is applied
      at all** and post-kickoff odds flow into HT features ungated (measured: 12,463 T-0 rows at `bm < -55`, 1,406 at
      `bm < -110`, worst −374.6 = 6.2h after kickoff / well after full time). Either call the gate unconditionally
      (letting it apply its documented default) or delete the dead branch.
- [ ] [DATA] P1. **The blank-`fixture_id` raw generation is STILL BEING WRITTEN — fix the upstream writer.** The
      collapse signature reaches the **corpus edge** (last collapsed date **2026-06-20**; 2026-04: 28 dates · 2026-05:
      28 · 2026-06: 8 — only **9** healthy dates in all of 2026), so the current ODDS_API capture path emits
      `fixture_id=""` alongside a populated `event_id`. MDPS@9f2560b7 makes the DERIVE immune (identity is coalesced),
      so this is no longer data-destroying — but the raw is still carrying a blank column that means "absent", which is
      the exact trap that cost this corpus ~1.1M observations. Either populate `fixture_id` at write time or drop the
      column rather than writing it blank (a blank-but-present column is a placeholder that looks populated —
      `/codex/02-data/honest-absence-downstream-handling.md`). Owner: MTDS (the ODDS_API writer). Measured by the
      2026-07-17 blast-radius census (2,221 dates, 0 gaps).
- [ ] [DATA] P1. **Re-calibrate the `verify_ml_readiness.py` 95% non-NULL threshold against the HONEST matrix.** The
      gate now fails 1,683/1,860 dates at ~69-80% non-NULL — **not a regression**: the threshold was calibrated when the
      closing line was broadcast into every T-24h row, i.e. against a leaking matrix, so 95% was only ever reachable
      _because_ of the leak. Post-purge, a T-24h row legitimately carries NULL for every closing-derived column
      (`clv_*`/`odds_movement_*`/`velocity_*_1h_to_0`/`steam_*`, ~27+ columns), so the gate is now structurally
      unmeetable at 95% and measures the wrong thing. Re-base it per-horizon on the columns each horizon can honestly
      know (`FEATURE_HORIZONS[h]` / the `min_horizon` registry) rather than on a flat cell-count. **Deliberately NOT
      tuned in this leg** — lowering a number to make a gate green is the anti-pattern.
- [ ] [DATA] P1. **Reconcile the market-data-sports manifest for the 2,436 deleted T-0 shards.** They still read as
      `captured` in the availability index; they should be `empty_confirmed` (honest absence). NOT done here: the
      operator scoped this session's manifest work to the FEATURES surface only, and the market-data-sports consolidator
      is owned by the in-flight bucket cutover (its unmerged shard `_index/per_vm/cutover-move-20260716.parquet` must
      not be merged by anyone else).
- [ ] [ML] P2. **Retrain the CLV models after the ODDS_FEATURES recompute.** The 3 quarantined artifacts stay in place
      as the reference for what the leak produced. Do not promote or cite them.

---

## RE-TRIAGE (2026-07-23, count corrected 2026-07-24)

**Verdict: RESOLVED BY LATER WORK** (core investigation + all spun-off P0/CODE items), **but the 2026-07-23 pass
undercounted this doc's own remaining Todos** — it named "one residual P1" (the PIT-gate item only). A direct
`grep -n '- \[ \]'` of this file shows **5 open checkboxes** (lines 547, 1006, 1015, 1023, 1028 — the finding
`sports_plan_and_docs_reconcile_findings_2026_07_24.md` flagged this). All 5 are re-verified below against current
code/plans on 2026-07-24, not inherited from the 2026-07-23 pass or from each other; **none turned out to be
already-fixed-but-unflipped** — every one is genuinely still open.

- The doc's own central question ("does SFI substitute for half-time odds?") is answered and the OR-5b(c) → B-REFINED
  recommendation stands unchallenged in the umbrella closeout (`sports_master_closeout_2026_07_21.md` §D, `ad#4`, 2 days
  old). Every major sub-finding this doc raised was shipped and each is independently re-verified in its own Progress
  Log with runtime evidence, not just claimed: T-0 ordering fix (MDPS@3bf56ff), HT honest-absence
  (features-service@c57cc753), the closing-line/CLV leak fix + 3 quarantined models (features-service@bf6fc2f4 +
  ml-service@c0603cb), the SFI `1h_*` capture-gap fix (uac@96cdfc4f + instruments-service@1f7c51cf +
  features-service@5a8684ed), and the fixture-identity-collapse fix (market-data-processing-service@9f2560b7).
- **All 5 of this doc's own remaining Todos are still genuinely open** — each re-checked directly against current
  code/plans on 2026-07-24:
  1. **(line 547, [CODE] P1)** `_apply_ht_odds_pit_gate`'s `if not ht_break_minutes:` default-cutoff branch is still
     unreachable in production. `features_service/sports/exporters/odds_features_exporter.py` (current
     `live-defi-rollout` checkout, line 287) still guards the only call site with
     `if ht_break_minutes: bucketed = _apply_ht_odds_pit_gate(...)` — the gate is never invoked at all when HT break
     times are unknown, matching this doc's original P1 exactly. Also matches the master closeout's own framing:
     `"_apply_ht_odds_pit_gate default-cutoff unreachable in prod (1 open P1; leaks already fixed)"`. This is the item
     the 2026-07-23 pass already named — still correct, just no longer the ONLY one.
  2. **(line 1006, [DATA] P1)** The blank-`fixture_id` raw generation — still open, no upstream-writer fix found.
     Checked MTDS's ODDS_API adapter (`market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py`,
     which writes `event_id` but never a populated `fixture_id`) and its git log since 2026-07-17: no commit populates
     `fixture_id` at write time or drops the blank column. MDPS@9f2560b7 (already shipped) makes the DOWNSTREAM derive
     immune to this, but the raw writer itself is unchanged. Owner MTDS, per the todo.
  3. **(line 1015, [DATA] P1)** `verify_ml_readiness.py`'s 95% non-NULL threshold — still open, still a flat un-rebased
     constant. `features_service/sports/compute/ml_readiness_check.py:29` reads `NON_NULL_THRESHOLD: float = 0.95`
     verbatim, with no per-horizon logic added. The recalibration against the post-purge honest matrix has not been
     done.
  4. **(line 1023, [DATA] P1)** Reconcile the market-data-sports manifest for the 2,436 deleted T-0 shards — still open,
     still blocked on its stated dependency. Per
     `plans/archive/2026_07/sports_legacy_bucket_cutover_history_2026_07_24.md` (dated the same day as this re-triage),
     the cutover's T6.1 merge of `_index/per_vm/cutover-move-20260716.parquet` is still confirmed **NOT merged** — the
     blocker this todo names is unchanged.
  5. **(line 1028, [ML] P2)** Retrain the CLV models after the `ODDS_FEATURES` recompute — still open. The stated
     prerequisite (the recompute) IS now done (see "ODDS_FEATURES recompute EXECUTED" in the history doc part 2 —
     `/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md` — 1,524/1,861 dates purged,
     2026-07-17), but no retrain followed it: `ml-service` git log since 2026-07-17 has no CLV/retrain commit, and the 3
     quarantined artifacts (`ml-service@c0603cb`) remain the only reference models. The prerequisite clearing does not
     by itself close this todo — retraining is a separate, not-yet-run action.
- The other open P0 item this doc's history references (the 423-date odds-features recompute from the
  fixture-identity-collapse fix) belongs to `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`'s
  scope, not this doc's own remaining Todos — not duplicated here.
- The cutover runbook (`sports_legacy_bucket_cutover_2026_07_16.md`) already carries this doc's B-REFINED verdict inline
  (dated 2026-07-16), so no doc-drift found there either.
- No conflicting doc found.
