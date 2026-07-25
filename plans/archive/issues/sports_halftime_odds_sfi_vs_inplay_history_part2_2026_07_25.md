---
doc_type: issue
title:
  Half-time odds — SFI vs in-play — resolved history PART 2 of 2 (T-0 recompute execution + second Todos list + collapse
  recompute + ODDS_FEATURES recompute + fixture-identity-collapse fix + phantom-block/pivot fixes), extracted 2026-07-25
  for the line-cap split
summary:
  'Archive-bound extraction (2026-07-25, plan line-cap remediation pass, precedent
  `/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md` § FINAL RESOLUTION) of the fully-historical body of
  `/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`. **PART 2 of 2** — continues directly from
  `sports_halftime_odds_sfi_vs_inplay_history_part1_2026_07_25.md` (part 1 carries the original investigation, the first
  Todos list, and the lookahead-leak / SFI h1_* / closing-line-leak Progress Logs). Part 2 carries: the T-0 recompute
  execution ("T-0 recompute EXECUTED" section), the second "Todos" list (opened by the T-0 recompute leg — DONE items
  only; the 4 genuinely-open `[ ]` items originally interleaved in this list were moved to the parent''s "Open Todos"
  section, not duplicated here), the "Collapse recompute EXECUTED" section, the "ODDS_FEATURES recompute EXECUTED"
  section, the "Fixture-identity collapse — FIXED" section, and the "Phantom-block + pivot fixes EXECUTED" section.
  Verbatim, byte-for-byte, in original order. 9 of the parent doc''s original 14 checkboxes live across parts 1+2 (8
  `[x]` done + 1 `[~]` partial, all superseded/completed by later work per the parent''s own RE-TRIAGE section) — the 5
  genuinely still-open `[ ]` checkboxes stay in the parent, not duplicated here. Record-only; not intended for further
  action. The parent''s live open work + RE-TRIAGE section is at
  /plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md.'
status: resolved
nature: record
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
    history,
    archive,
    plan-hygiene,
  ]
related:
  [
    /plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md,
    /plans/archive/issues/sports_halftime_odds_sfi_vs_inplay_history_part1_2026_07_25.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: "see parent doc's resolved_by list — this is an archive-bound extraction, not an independent resolution"
source:
  [
    "Plan line-cap hygiene remediation, /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md § FINAL RESOLUTION
    — extract-to-archive-bound-history-child pattern",
  ]
---

> **Archive-bound history child, part 2 of 2.** Continues directly from
> `/plans/archive/issues/sports_halftime_odds_sfi_vs_inplay_history_part1_2026_07_25.md`. For current status, the 5 open
> todos, and the RE-TRIAGE section, see the parent:
> `/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`. Everything below is extracted verbatim,
> byte-for-byte, from that doc's original body (the 2026-07-16/07-17 fix-execution legs).

---

## T-0 recompute EXECUTED — the leak is gone; the features leg is BLOCKED (2026-07-16)

> **Shipped**: features-service@c57cc753 (HT honest absence) · market-data-processing-service@e2ec8ce (stale-shard
> reconcile). **Sports stayed FROZEN** — all three sports consolidators (`features-sports`, `market-data-sports`,
> `instruments-sports`) and every sports scheduler verified PAUSED before and after; **nothing was resumed**.

### 1. Scope RE-VERIFIED independently (the standing 4-audits lesson) — every number confirmed

Full census, zero read failures, single walk (`gcloud storage ls -r` cached locally, reused for every check):

| claim                                          | doc     | measured    | verdict         |
| ---------------------------------------------- | ------- | ----------- | --------------- |
| canonical T-0 shards                           | 11,373  | **11,373**  | ✅              |
| T-0 rows                                       | 368,366 | **368,366** | ✅              |
| T-0 post-kickoff rows                          | 146,738 | **146,738** | ✅ (39.83%)     |
| T-0 shards carrying ≥1                         | 7,101   | **7,101**   | ✅              |
| worst `bm_minutes_to_kickoff`                  | −374.6  | **−374.6**  | ✅              |
| other 7 timeframes post-kickoff                | 0       | **0**       | ✅ of 4,151,352 |
| `ODDS_FEATURES` shards (FULL scope, not 1,275) | 1,812   | **1,812**   | ✅ 1,812 days   |
| affected days                                  | 1,316   | **1,316**   | ✅              |

**Two corrections to the doc's own numbers** (immaterial to scope, but the record should be right):

- The "97,631 shards" for the other 7 timeframes is a transcription slip — the real count is **101,631**. The ROW census
  (4,151,352) matches exactly, so the original census did cover all of them; only the shard tally was mistyped.
- `DERIVED_FEATURES` exclusion **verified before acting on it**, at BOTH levels: `derived_features_exporter` imports no
  odds calculator and never calls `read_bucketed_odds` (code), and 0/40 sampled shards carry any odds-family column
  (data). Correctly excluded.

### 2. 🔴 BIG FINDING — the prescribed `--force` re-derive is DESTRUCTIVE. Each layer is RICHER than its own upstream.

**The recompute mechanism in the todo above cannot be run as written.** Discovered by piloting one day, measured, then
fully reverted from GCS soft-delete (verified byte-exact).

`reprocess_sports_odds.py --force` re-derives a day from **today's canonical raw**. That raw no longer contains what the
existing corpus was built from:

| day        | canonical raw rows | legacy raw rows | ratio     |
| ---------- | ------------------ | --------------- | --------- |
| 2022-04-16 | **5,626**          | **79,773**      | **14.2×** |
| 2025-04-12 | 168,653            | —               | intact    |
| 2024-11-09 | 147,110            | —               | intact    |

A pre-flight harness (read-only: runs the real adapter, compares to the corpus per horizon) gives the verdict per day:

- **2022-04-16 → UNSAFE**: re-derive yields T-24h only; would destroy **4,741 legitimate pre-match rows**
  (T-10m/T-12h/T-1h/T-2h/T-4h/T-6h all → 0).
- **2025-04-12 / 2024-11-09 → SAFE**: every non-T-0 horizon reproduces **delta 0** (exact), T-0 drops precisely the
  post-kickoff rows (+18/+12 extra valid rows the richer raw supports).

**The old corpus is NOT itself mis-bucketed** — falsified rather than assumed: every non-T-0 shard on 2022-04-16 is
**100% inside its own staleness cap** (T-10m bm 5.6–14.9, T-12h 706.7–744.1, T-6h 343.4–380.4, …). Only T-0 was bad (21%
valid). So the multi-horizon data is real, and a blind re-derive really would have destroyed it.

**Same pathology one layer down**: `odds_features` is richer than the MDPS bucketed layer it derives from.
day=2024-01-01 holds **13 fixtures** in `odds_features` while MDPS bucketed holds **1**. Blast radius measured on a
31-date evenly-spaced sample: **4/31 dates (13%)** would LOSE fixtures on recompute (18 fixtures total) — bounded, not
universal, but non-zero. **This is why the features recompute was NOT run.**

> **Consequence for the cutover lane**: the sports lineage cannot currently rebuild itself at ANY layer. Until the
> legacy→canonical raw recovery (OR-5b(b) option-D G1 read-split-merge) lands, every `--force` re-derive is a data-loss
> event. Filed: `./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`.

### 3. What was actually done — a surgical filter, not a re-derive

MDPS@3bf56ff changes **only** the `bm<0` branch (post-kickoff → reject); rows with `bm>=0` are byte-identical
(test-enforced). So removing `bm<0` rows from the existing T-0 shards **is exactly what the fixed code emits from the
same inputs** — with zero dependency on raw completeness. This is the least-bad path: it fulfils the intent (remove the
leak) without the mechanism's destructiveness.

**Result — verified by a FRESH full census, not by re-reading my own output:**

| metric                    | before  | after       |
| ------------------------- | ------- | ----------- |
| canonical T-0 shards      | 11,373  | **8,937**   |
| canonical T-0 rows        | 368,366 | **221,628** |
| **T-0 post-kickoff rows** | 146,738 | **0** ✅    |
| worst `bm`                | −374.6  | **0.0**     |

Both deltas are exact: 11,373 − 2,436 = 8,937; 368,366 − 146,738 = 221,628. 4,665 shards rewritten in place, 2,436
emptied shards deleted (honest absence — the fixed writer emits no group for them).

**Blast radius contained, measured:** total bucketed objects 222,316 → 219,880 (delta **2,436** = exactly the emptied
T-0 shards). Non-T-0 canonical **unchanged at 101,631**. The legacy (no-`pipeline_mode=`) layout **untouched at
109,312** — it is fully shadowed (all 1,813 legacy days have a canonical counterpart, and the features reader probes
canonical first and only falls back when canonical is empty for that day).

### 4. Writer gap found + fixed — MDPS@e2ec8ce

`_write_bucketed_output` was **overwrite-only**: it uploads the (league, horizon) groups present in the NEW frame and
never removes shards the derive no longer produces. So a shard whose rows all become invalid keeps its **stale parquet
on disk**, and readers (which list the date prefix and concatenate) keep consuming it. Measured: **2,436 of the 11,373**
T-0 shards go fully empty under the fix — a naive `--force` recompute would have left **43,119 leaked rows (29.4%)**
live, and the "146,738 → 0" assertion would silently have failed at 43,119. Now reconciled via `_delete_stale_shards`
(canonical prefix only; never the legacy layout; never on a degenerate/empty derive), + 5 regression tests.

### 5. Model quarantine — DONE (nothing deleted)

All 3 CLV models flagged unusable, **artifacts retained**, verified read-back (manifest still parses, 15 other models
untouched). Leak re-confirmed independently before acting: `target_type='clv'` **and** `clv_home` present in
`feature_names` — it predicts CLV from CLV. Metrics re-measured: **0.9936** (V20260417164033), **1.0** (…154715,
degenerate), **0.6411** (…201036).

Flags written (additive keys — `quarantined` / `usable:false` / `promotion_blocked:true` / `quarantine_reason`) to
`model_registry/manifest.json` (entry + every version), each `model_registry/metadata/<id>/…/metadata.json`, and a
`QUARANTINED.json` marker beside each `model.joblib`.

### 6. ML-readiness — BEFORE captured; AFTER not meaningful yet

`verify_ml_readiness.py --start-date 2020-06-07 --end-date 2026-06-20` (full corpus), BEFORE: **2,205 dates checked ·
1,021 passed · 791 failed · 393 missing · avg non-NULL 94.0% · gate NO**. (1,021+791 = 1,812 = the odds_features census
— consistent.) **AFTER is deliberately not reported**: the gate measures `odds_features`, which was NOT recomputed, so
it would be unchanged by construction. Reporting it as an "after" would be a false signal.

## Todos (opened 2026-07-16 by the T-0 recompute leg)

- [x] [DATA] P0. ✅ **Recompute `ODDS_FEATURES` behind a PER-DATE loss guard — DONE 2026-07-17.** Guard shipped
      **features-service@3c15f3ff** (`data/loss_guard.py` pure core + `cli/handlers/_loss_guard_gate.py` wiring, 15 unit
      tests); recompute EXECUTED over the **full re-verified census of 1,861 dates** (not 1,812 — see § below), 4-way
      parallel through the production CLI: **1,524 written · 337 guard-ABORTED (18.1%) · 0 failures (rc=0 on
      1,861/1,861)**. Two-sided verification on the 1,524 written dates, full census (not sampled): `clv_home` **21,922
      → 0** · `odds_movement_home` 21,922 → 0 · `sharp_clv_home` 18,508 → 0 · `clv_direction_home` 21,922 → 0 ·
      `velocity_home_1h_to_0` 19,969 → 0; **`opening_home_odds` SURVIVED 31,539 → 31,545** (not over-gated) ·
      **`steam_detected_home`@T-1h SURVIVED 26,904 → 26,904 unchanged**, gated out at T-24h 26,359 → 0 (its
      `min_horizon` is T-1h) · `bookmaker_count_total`@T-24h pooled-signature dates **1,364 → 0**, median-of-max **145 →
      19** (the predicted ~21 genuine count) · HT rows **1,467 → 0** dates (honest absence). **Zero non-HT fixture
      losses** on written dates; the 134 net fixture-slot drop is entirely HT-only fixtures vanishing with HT. Residual
      leak is a **strict subset of the 337 aborted dates** (`clv_home` dirty-after = 329, `subset_of_blocked=True`, **0
      on written dates**) and all 337 aborted shards are **byte-intact** (row counts unchanged). ML-readiness re-run:
      see § "ODDS_FEATURES recompute EXECUTED" below — **1,021 → 177 passed / 94.0% → 80.0%, a CORRECT drop** (removing
      fabricated signal), gate NO both sides. The `MANIFEST_CONSOLIDATED_STALENESS_SEC` concern did not materialise —
      sports was RESTORED live 2026-07-17 (consolidators `*/1`), so the startup gate passed unmodified.
- [x] [DATA] P0. ✅ **MECHANISM DIAGNOSED + FIXED 2026-07-17 — `market-data-processing-service@9f2560b7`; the SPLIT-OUT
      RECOMPUTE is now DONE 2026-07-17 (447/449 MDPS + 192/192 features phantom-unblocked; see § "Phantom-block + pivot
      fixes").** The blank-`fixture_id` collapse is fixed at the adapter: identity is now COALESCED (blank == absent)
      into an authoritative `fixture_id` before anything keys on it, an unresolvable identity fails LOUD
      (`MalformedTickFieldError` → `attempted_failed`, never a silent collapse or a false `empty_confirmed`), and
      `odds_loss_guard` now **sources** `resolve_fixture_ids` from the adapter instead of carrying a second copy — so
      guard and derive cannot drift on what a fixture IS. **11 new regression tests** (`TestFixtureIdentityResolution`,
      incl. the pinned `2024-01-15` 1→5-fixture case); QG green (**2040 passed**, 1 skipped; sentinel == HEAD).
      Evidence + the two inherited numbers this leg **falsified**: see § "Fixture-identity collapse — FIXED" below.
      Headline: **448** dates carry the signature (**not** the 337 — that was the features-side symptom), **423** change
      on re-derive, **94.8%** of the derive was being destroyed on them (60,517 → 1,173,798 rows), **adds-only PROVEN**
      (0/1,934 dates lose an observation), and the (b) guard now **passes** the exact date it blocked pre-fix
      (`2023-01-08`, 514 → 514, was 514 → 61). Original scope text retained: They are the ONLY dates still carrying the
      closing-line leak. They are **not scattered — 49 contiguous windows with a hard WINTER signature**:
      `2021-01-01..2021-02-20` (49d) · `2022-01-01..2022-03-05` (60d) · `2022-12-23..2023-02-27` (61d) ·
      `2024-01-01..2024-02-02` (31d) · `2024-02-09..2024-02-23` (14d) · `2025-02-02..2025-02-15` (14d), by year 2021:49
      · 2022:147 · 2023:78 · 2024:45 · 2025:17 · 2026:1. On those dates the corpus holds **10,642 fixtures** and the
      re-derive reaches only **9,842** → the guard protected **800 fixtures** from deletion. Note the era overlaps the
      199-day `batch_footystats` merge window (`market-tick-data-service@75f226e8`, 2022:112 · 2023:48 · 2024:34) — so
      that merge fixed a _neighbouring_ slice but NOT these; a second, distinct starvation mechanism is live and
      unidentified. This is exactly the "nothing yet proves they cannot starve by another [mechanism]" caveat in
      `./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`. Do NOT lower the guard to force these
      through — fix the upstream, then re-run `drive.sh`-equivalent on the 337. > **🟢 MECHANISM IDENTIFIED 2026-07-17
      (by the fix-(b) leg) — FIXED 2026-07-17 `market-data-processing-service@9f2560b7`.** > **An empty-but-present
      `fixture_id` column silently collapses the MDPS adapter's dedup key.** > `pivot_mtds_to_wide` renames
      `event_id`→`fixture_id` ONLY when `fixture_id` is absent. On the affected dates the > raw carries BOTH —
      `event_id` populated and `fixture_id` present but **blank on 100% of rows** — so no rename > fires, and
      `_get_dedup_columns` then returns `['fixture_id', 'bookmaker_key']`. Dedup therefore runs on >
      `('', bookmaker_key, horizon_idx)` and **keeps ONE row per (bookmaker, horizon) for the whole league-day**, >
      destroying every other fixture. > **Measured live** (`market-data-processing-service/.venv`, real reads + real
      adapter, zero inherited numbers): > `day=2024-01-15` raw holds **5 distinct `event_id`** across 3,759 rows with
      `fixture_id` non-empty on **0/3,759**; > the adapter derives **166 rows / ~21 per horizon** = ~21 bookmakers ×
      **1** collapsed fixture (vs ~5×21×8 ≈ 840 > expected — **~80% destroyed**). Every probed shard on such a date has
      `event_id` nunique == **1**. Contrast > `day=2022-04-16`, where raw has `event_id` only → rename fires → **68
      fixtures** preserved / 5,635 rows / grid > `T-12h=896 · T-6h=898 · T-4h=896 · T-2h=884 · T-10m=870 · T-24h=894`
      (matches the corpus EXACTLY). > **Corpus generation split** (the diagnostic signature — grep it to enumerate the
      affected dates): > `fixture_id` populated + no `event_id` column = HEALTHY; `event_id` populated + blank
      `fixture_id` = COLLAPSED. > Probed collapsed: `2024-01-15`, `2025-02-05` — **both inside the 337 winter windows**.
      Probed healthy: > `2022-04-16`, `2023-05-10`, `2024-11-09`, `2025-04-12` — all outside. > **Why the features guard
      fired**: the MDPS corpus on these dates is ALREADY collapsed (the bug bit at original > derive time), so
      `odds_features` (13 fixtures) is richer than the MDPS upstream it reads (1) — exactly the > "richer than its own
      upstream" reading, but caused HERE, not by raw truncation. > **Fix direction**: make the fixture identity
      resolution explicit rather than rename-dependent — coalesce > `event_id`/`fixture_id` treating blank as absent
      (fix-(b)'s `_resolve_fixture_ids` in > `app/adapters/sports/odds_loss_guard.py` is a working reference), and make
      `_get_dedup_columns` refuse a dedup > key whose every value is blank rather than silently collapsing. ~~**NOT
      fixed here**~~ — **FIXED 2026-07-17, MDPS@9f2560b7** (both prescribed changes landed; the resolver is now SHARED
      with the guard rather than duplicated). > The fix-(b) guard > does NOT protect these dates: old and new both
      collapse identically, so the derive looks faithful — **still true, and still the reason the fix had to come from
      the derive side.** > _Provenance: fix-(b) leg 2026-07-17, `market-data-processing-service@6d20fb18`; fix + blast
      radius 2026-07-17, `market-data-processing-service@9f2560b7`._
- [x] [DATA] P0. ✅ **DONE 2026-07-17 — all 449 dates in their correct terminal state.** MDPS leg 447/449 adds-only
      (+710,850 rows, 0 lost); 2026-02-09 later re-derived after the pivot fix (2,697 rows). Features leg: 255 purged
      earlier + **192 phantom-blocked now 192/192 PASS** (features-service@16fdd141) + 2026-02-09/2025-02-16 features
      clean. **2025-02-16** is the one date whose MDPS re-derive stays (b)-guard-BLOCKED — genuine raw truncation
      (parent-issue class), intact corpus preserved, NOT forced. ML-readiness FLAT 53 pass / 78.1% (leak-purged honest
      matrix vs the miscalibrated 95% — P1 recalibration todo). See § "Phantom-block + pivot fixes EXECUTED
      (2026-07-17)". Original scope retained: **RECOMPUTE the collapse-affected dates through MDPS, then re-run
      `ODDS_FEATURES`. MDPS LEG DONE 2026-07-17 (447/449 recomputed, all `LOSS_GUARD_PASS`, 0 blocked, adds-only PROVEN
      463,092 → 1,173,942 rows / 0 lost); FEATURES LEG PARTIAL (255 purged + updated, 192 BLOCKED by the (c) guard
      protecting a blank `''` phantom — recorded + reported, NOT forced per the guard directive). See § "Collapse
      recompute EXECUTED (2026-07-17)" below + the two new findings.** Split out of the todo above (the fix —
      MDPS@9f2560b7 — is that todo's deliverable; this is the DATA leg it unblocks). **It now runs GUARDED**: the (b)
      loss guard (`market-data-processing-service@6d20fb18`) is unmodified and demonstrably passes the post-fix derive
      (`2023-01-08` 514 → 514; census `2023-01-05..20` **16/16 pass, 0 blocked**, where pre-fix it blocked **15/16**),
      so a `--force` over these dates can only add. Do NOT lower the guard; a block on any date = STOP-and-diagnose (a
      THIRD starvation mechanism), not a nuisance. **Scope (measured, full census — `~/tmp-collapse/blast_radius.jsonl`
      methodology, real reader + real adapter):** - **MDPS `odds_horizon_bucket`**: **423 dates** whose derive changes
      (of 448 signature dates; the other 25 are single-fixture days where the collapse is a no-op). Range **2020-06-06 …
      2026-06-20**; by year 2020:78 · 2021:50 · 2022:60 · 2023:52 · 2024:51 · 2025:47 · 2026:110. Expected write:
      **60,517 → 1,173,798 rows** (+1,113,281 observations; ~2,800 rows/date avg). **Cost**: measured 27.0s for 16 dates
      at `--workers 4` dry-run (≈1.7s/date derive+guard); with real per-shard uploads (~71 shards/date) budget **~1-2
      h** for all 423 at `--workers 4`. Command:
      `reprocess_sports_odds.py --start-date <D> --end-date <D> --force --workers 4` (resumable per date; verify each
      date logs `LOSS_GUARD_PASS`). - **features-service**: re-run `ODDS_FEATURES` (+ `DERIVED_FEATURES`) on the **423
      dates** AFTER the MDPS leg lands — they read the bucketed layer, so they must not be recomputed against the
      collapsed upstream. This also clears the **337 guard-aborted dates**' residual closing-line leak (the 337 ⊂ the
      collapse-affected era), which is the last 18.1% of the leak purge. Feature-side guard =
      `features-service@3c15f3ff` (fixture-SET containment). - **Sequencing**: MDPS first → verify → features. **Sports
      must not be mid-freeze/cutover when this runs**; confirm the bucket cutover's state before starting (this issue's
      own banner + the cutover runbook).

> _(Four items originally at this position in this list — all still genuinely open `[ ]` todos as of 2026-07-25: [DATA]
> P1 the blank-`fixture_id` raw-generation writer fix, [DATA] P1 the `verify_ml_readiness.py` 95% threshold
> recalibration, [DATA] P1 the market-data-sports manifest reconciliation for the 2,436 deleted T-0 shards, and [ML] P2
> retrain the CLV models after the ODDS_FEATURES recompute — were moved to the parent doc's "Open Todos" section on the
> 2026-07-25 line-cap split, not duplicated here. See
> `/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`.)_

- [x] [CODE] P0. ✅ **FIXED + VERIFIED 2026-07-17 — features-service@16fdd141** (rec A). The (c) guard now resolves
      identity with **blank == ABSENT on BOTH sides** (`_resolve_fixture_id_set` in `loss_guard.py`, mirroring the MDPS
      `resolve_fixture_ids` semantics — a literal shared import is barred by the T4 service→service dep ban, so the
      semantics are duplicated locally and pinned to parity by the shared 192-class test vector). Re-ran all **192**
      blocked dates via the real `odds_features --force` CLI → **192/192 PASS · 0 blocked · 0 error** (2020:78 · 2024:6
      · 2026:108); **4,532 real fixtures written, 0/192 dates lose a real fixture**, leak purged (`CLV features: 0`);
      `2026-05-17` 0→104, `2024-01-01` 13→13. **Real protection PRESERVED** (test-pinned): old {A,B,'',C} vs
      {A,B,C}→PASS, all-phantom {''}×3 vs real→PASS, but old {A,B,'',D} vs {A,B,C}→**BLOCK on D**. QG green (17,679
      passed; sentinel==HEAD); 8 new tests. See § "Phantom-block + pivot fixes EXECUTED (2026-07-17)". Original finding
      retained: **NEW FINDING (2026-07-17 collapse-recompute leg) — the (c) features loss guard BLOCKS the phantom→real
      transition on 192 collapse dates because it protects a blank `''` fixture id.** After the MDPS leg un-collapsed
      the corpus, `odds_features --force` on the 447 recomputed dates gave **255 PASS / 192 BLOCKED**. Every blocked
      date's EXISTING shard (written in the collapsed-MDPS era) carries a blank `''` fixture cell — exactly ONE per
      model horizon (measured: 3 blank cells / date across T-10m·T-1h·T-24h). The un-collapsed re-derive emits only REAL
      fixture ids, so the blank `''` disappears → `fixture_loss` containment fails → block. **PROVEN zero real-data
      loss**: across all 192 blocks, `max lost = 1 per (date,horizon)` and **0 dates lose >1** (aggregated from every
      block log), i.e. the lost cell is ALWAYS the single blank — no genuine fixture is ever dropped. This is **NOT the
      "third starvation mechanism"** the P0 todo warned about (MDPS is now RICH, e.g. 2026-05-17 = 104 fixtures); it is
      the id-set guard refusing to drop a stale collapse-artifact placeholder (a blank-but-present id — itself an
      honest-absence violation, `/codex/02-data/honest-absence-downstream-handling.md`). **Per the guard directive I did
      NOT bypass/delete/lower it — reported for an operator decision.** Fix options (operator to pick): (A) make the (c)
      guard treat a blank/empty `fixture_id` as ABSENT on BOTH the existing-shard and new-derive sides — mirrors the
      already-shipped MDPS `resolve_fixture_ids` (blank == absent) at `bucket_assignment_adapter.py`; then re-run the
      192 → they clear with real fixtures still protected [WORKER REC]; (B) delete the 192 phantom `''` shards then
      re-derive (GCS soft-delete recovers) — band-aid, doesn't fix the guard for next time; (C) fix the FEATURES
      exporter so it never emits a blank `''` fixture cell in the first place (root cause on the write side).
      Blocked-date list + per-year split: 2020:78 · 2024:6 · 2026:108.
- [x] [CODE] P1. ✅ **FIXED + VERIFIED 2026-07-17 — market-data-processing-service@4172156.** The pivot now (i)
      COALESCES `venue`/`bookmaker_key` into one authoritative bookmaker identity (blank == absent,
      `_materialise_bookmaker_identity`) — needed because `2025-02-16` SPLITS the bookmaker id across generations (65
      fixtures only via `venue`, 6 only via `bookmaker_key`, ZERO overlap), so merely dropping `venue` would lose 65
      fixtures; and (ii) keeps vendor metadata / PIT-stamp columns
      (`instrument_type`/`data_source`/`source`/`data_type`/**`available_at`**) OUT of the pivot index
      (`_PIVOT_INDEX_EXCLUDE`). `available_at` was the extra culprit the doc under-specified: it is NaN on the
      `2025-02-16` trades generation and alone would drop those 65 fixtures. Before/after harness (real pre- & post-fix
      adapters, same cached raw): both problem dates EMPTY→**2025-02-16 71 fixtures / 2026-02-09 18 fixtures**; two
      HEALTHY controls (`2024-11-09`, `2023-05-10`) **odds-data byte-identical** (only non-consumed metadata passengers
      dropped — `read_bucketed_odds` uses only fixture/bookmaker/horizon/odds; features stamp their own `available_at`
      from `kickoff_utc`). Re-derives: **2026-02-09 MDPS re-derived (2,697 rows, LOSS_GUARD_PASS, 0 blocked)** +
      features re-run (18→18, 54 rows, CLV=0). **2025-02-16 MDPS re-derive correctly BLOCKED by the (b) guard** — NOT
      the pivot (which now yields 71 fixtures) but genuine **raw truncation**: fixture `058da690…` has its earliest raw
      snapshot at 164.8 min pre-kickoff, so the current raw carries 0 rows in the T-10m/T-1h/T-2h windows while the
      intact corpus holds them (bm 6.0–14.8 / 64.6–68.8 / 124.5–132.0) from a fuller past raw — the parent-issue "richer
      than its own upstream" class (`sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`).
      **Reported, NOT forced** (per the guard directive); intact corpus preserved; its features re-derived clean against
      that corpus (71→71, 213 rows, CLV=0). QG green (sentinel==HEAD); 6 new tests. Original finding retained: **NEW
      FINDING (2026-07-17) — MDPS `pivot_mtds_to_wide` empties the whole derive when the raw carries stray mostly-NaN
      metadata columns.** 2 of the 449 dates (`2025-02-16`, `2026-02-09`) recorded `ADAPTER_RETURNED_EMPTY_OUTPUT` →
      `attempted_failed` (NON-destructive: 0 shards written, corpus byte-identical before/after — 10,602/71 and 2,696/18
      unchanged). Root cause (measured, real reader+adapter): the raw for these dates carries extra columns
      `venue`/`instrument_type`/`data_source` that are NaN on **12,693/12,702 (99.9%)** of rows; `pivot_mtds_to_wide`
      builds `group_cols` from EVERY non-excluded column, and `pivot_table(index=group_cols)` **drops every row with NaN
      in any index level** → the h2h pivot returns empty → "No h2h data found" even though the raw HAS 12,702
      well-formed h2h rows (HOME/DRAW/AWAY, price non-null). Fixture identity resolves fine (18/71 fixtures) — this is
      orthogonal to the collapse fix. Fix: exclude stray/redundant GCS-partition metadata columns
      (`venue`/`instrument_type`/`data_source` — they duplicate `bookmaker_key`/`data_type`/`source`) from the pivot
      index, or drop all-/mostly-NaN columns before pivoting. Owner: MDPS
      (`bucket_assignment_adapter.pivot_mtds_to_wide`).

---

## Collapse recompute EXECUTED (2026-07-17) — MDPS 447/449 adds-only; features 255 purged / 192 phantom-blocked

> **Ran, did not inherit.** Regenerated the scope from a fresh signature census (raw walk 2026-07-17), re-verified QG
> green at MDPS@9f2560b7 (`.qg_last_passed_sha == HEAD`, not exit code), piloted before scaling. Zero code shipped (both
> repos clean); all drivers were scratch in `~/tmp-rerun`. No date forced past a guard.

### 1. Scope re-verified independently

Fresh signature census over all **1,935** raw dates (sample 3 objects/date, disagreements flagged AMBIGUOUS): **448
COLLAPSED + 1 AMBIGUOUS (`2025-02-16`, genuinely mixed-generation — some objects blank `fixture_id`, some absent) +
1,486 HEALTHY** — reproduces the doc's 448/1,486 exactly. **New vs the doc**: the signature now reaches `2026-07-16`
(the doc's stated last collapsed date was 2026-06-20; the resumed live edge is already collapsed), so target list =
**449** (448 + the mixed date), today (`2026-07-17`, no raw) excluded.

### 2. MDPS recompute — 447/449, adds-only PROVEN on the real run

Ran the real `reprocess_sports_odds.py --force --workers 1` once per date (per-VM manifest shards, `VM_NAME` per lane,
to avoid the live-consolidator CAS contention that made a naive single-date manifest flush take ~9 min). **447
recomputed, all `LOSS_GUARD_PASS`, 0 blocked.** Full before/after corpus census (real reads):

| metric                                         | BEFORE (corpus) | AFTER     | delta        |
| ---------------------------------------------- | --------------- | --------- | ------------ |
| rows (447 recomputed dates)                    | 463,092         | 1,173,942 | **+710,850** |
| dates that grew                                | —               | 424       |              |
| dates flat (single-fixture)                    | —               | 23        |              |
| **dates that LOST rows/fixtures/observations** | —               | **0**     | ✅ adds-only |

AFTER total (1,173,942) matches the doc's predicted 1,173,798 (+144 = the new `2026-07-16` date). **Spot-checks match
the doc's predictions exactly**: `2024-01-15` 240→**746** rows / 3→**5** fixtures (doc: "1 phantom → 5"); `2026-05-17`
184→**16,938** rows / 0→104 fixtures (doc: "raw supports 16,938" — derive produced EXACTLY 16,938); `2023-01-08`
2,242→3,734 (T-12h=514, matches the (b)-guard census); `2026-07-16` live edge 0→144, clean.

**2 dates empty-derived** (`2025-02-16`, `2026-02-09`) — NOT a guard block; `ADAPTER_RETURNED_EMPTY_OUTPUT` from the
stray-NaN-column pivot bug (new P1 finding above). Non-destructive: corpus byte-identical before/after. Recorded
`attempted_failed`, never forced.

### 3. Features recompute — 255 purged, 192 phantom-blocked

`odds_features --force` on the 447 recomputed dates (per-VM shards): **255 PASS (leak purged + features updated to the
un-collapsed MDPS; `clv_*` = 0 at pre-match horizons, `CLV features: 0 fixture rows`), 192 BLOCKED**. The 192 blocks are
the blank-`''` phantom mechanism (new P0 finding above) — proven zero real-fixture loss, reported not forced.
`2024-01-01` (the doc's canonical 52→3 date) now PASSES 13→13.

### 4. Manifest — absorbed by the live consolidators

Per-VM shards (`mdps-collapse-recompute-20260717-l{0,1,2}` on instruments-store-sports; `feat-collapse-recompute-*` on
features-sports) were written and are **already GONE from `_index/per_vm/`** — the live `*/1` consolidators
(instruments-sports / market-data-sports / features-sports all ENABLED) merged them. Content-verified: the 5.35M-row
`availability_index.parquet` carries the recomputed dates (`2026-05-17` 242 odds_horizon_bucket entries, `2024-01-15`
140).

### 5. ML-readiness — 80.0% → ~79% (gate NO), tuned nothing

`verify_ml_readiness.py 2020-06-07→2026-06-20`: **passed 177 → 53 · avg non-NULL 80.0% → ~79% · gate NO both sides**.
The number moved slightly DOWN and passed dropped because un-collapsing replaced thin phantom dates with many real
pre-match fixtures whose T-24h cells honestly carry NULL for the ~27 closing-derived columns (the leak-purged honest
matrix). The 95% threshold is miscalibrated against the old leaking matrix (already the P1 re-calibration todo) —
**nothing was tuned**.

---

## ODDS_FEATURES recompute EXECUTED — the leak is purged on 1,524/1,861 dates (2026-07-17)

> **Shipped**: features-service@3c15f3ff (the per-date loss guard). **No code change to the exporter** — the leak fixes
> (@bf6fc2f4 / @c57cc753) were already live and correct; this leg is the DATA purge they were waiting on.

### 1. Scope RE-VERIFIED — the doc's own number was stale by +49

Single cached walk of `gs://features-sports-prd-central-element-323112/sports_features/by_date/**` (248,813 objects):

| claim                            | doc (2026-07-16)      | measured 2026-07-17                       | verdict                  |
| -------------------------------- | --------------------- | ----------------------------------------- | ------------------------ |
| `ODDS_FEATURES` shards           | 1,812                 | **1,861**                                 | ⚠️ +49 — explained below |
| date range                       | 2020-06-07→2026-06-20 | **2020-06-06→2026-06-20**                 | ⚠️ +1 day earlier        |
| layout                           | day-level             | **day-level (1,861/1,861; 0 per-league)** | ✅                       |
| `DERIVED_FEATURES` odds-derived? | no                    | **no** — re-confirmed                     | ✅ correctly excluded    |

**The +49 is real and benign.** A **10-VM parallel gap-fill campaign** (`fss-backfill-vm-1..10`, launched 02:18Z
2026-07-17 by another lane, `--skip-existing`, ranges spanning 2015-01-01→2026-07-17) filled **49 previously-MISSING
odds_features dates** while this leg was starting. Independently cross-checked: `verify_ml_readiness` missing went **393
→ 345 = 48**, +1 for `2020-06-06` (outside the doc's start) = **49** ✅. Those 49 were written by the FIXED code and are
already clean (probed `day=2020-10-02` / `2020-09-30`: `clv_*` 0 at every horizon, no HT, `opening_*` present, `steam_*`
at T-1h only). **`--skip-existing` means that campaign never touched the 1,812 leaked shards — the `--force` purge below
is exactly the piece it could not do.** No collision: the only two VMs still alive (vm-3 `2017-04-22.. 2018-06-16`, vm-4
`2018-06-17..2019-08-11`) sit entirely **before** odds_features exists (2020-06-06).

`DERIVED_FEATURES` / `FIXTURE_FEATURES` full-corpus counts are **42,965 / 72,347** — the doc's 15,415 / 26,942 were the
_affected-dates subset_, not the corpus; not a contradiction.

### 2. The guard (fix (c)) — features-service@3c15f3ff

Pure decision core `features_service/sports/data/loss_guard.py` (`evaluate_loss_guard`, no I/O) + wiring
`cli/handlers/_loss_guard_gate.py`, called in `_run_feature_group` **after** the emission policy and **before** any
write reaches GCS. **Fixture-SET containment per horizon**, not row-count: the grain is one row per (fixture × horizon),
so the HT honest-absence drop legitimately removes rows on every date — a row-count guard would abort 100% of dates on a
correct fix. Horizons in `EXACT_SNAPSHOT_HORIZONS` (today: `HT`) are exempt, **sourced from the exporter** so the
exemption dissolves by itself when a genuine in-play population lands. Fails **CLOSED**: an unreadable existing shard
blocks the write. Also guards the **empty-derive → `record_empty`** path, which would otherwise stamp `empty_confirmed`
on a date whose shard still holds fixtures (a manifest that contradicts the data).

15 unit tests (`tests/sports/unit/test_loss_guard.py`) pin both sides — including the measured `day=2024-01-01`
52-rows→3 regression, the HT-only-fixture justified drop, a same-count fixture SWAP (which a count-based guard would
wave through), and an int-vs-str id dtype mismatch (which would otherwise fabricate total loss and abort every date). QG
green: **17,632 passed, 209 skipped**.

**Proven in the real production path before the run**: `--date 2024-01-01 --tables odds_features --force` →
`LOSS_GUARD_BLOCKED ... fixtures 13 -> 1 ... Date SKIPPED; existing shard left intact`, and the shard's GCS update time
stayed `2026-07-16T19:10:29Z` (untouched).

### 3. The run — 1,861 dates, 4-way parallel, resumable

`1,524 written · 337 guard-ABORTED (18.1%) · 0 failed`; **rc=0 on 1,861/1,861**. Every date appends one JSON verdict
line, so the run resumes losslessly from any kill.

### 4. Two-sided verification — FULL census, not sampled

Measured over all 1,861 shards before and after (`census_before/after.jsonl`), restricted to the 1,524 **written**
dates:

| column                          | T-24h before                               | T-24h after                               | verdict                             |
| ------------------------------- | ------------------------------------------ | ----------------------------------------- | ----------------------------------- |
| `clv_home`                      | 21,922                                     | **0**                                     | ✅ purged                           |
| `odds_movement_home`            | 21,922                                     | **0**                                     | ✅ purged (identical count = alias) |
| `sharp_clv_home`                | 18,508                                     | **0**                                     | ✅ purged                           |
| `clv_direction_home`            | 21,922                                     | **0**                                     | ✅ purged                           |
| `velocity_home_1h_to_0`         | 19,969                                     | **0**                                     | ✅ purged                           |
| **`opening_home_odds`**         | 31,539                                     | **31,545**                                | ✅ **SURVIVED** — not over-gated    |
| **`steam_detected_home` @T-1h** | 26,904                                     | **26,904**                                | ✅ **SURVIVED** — unchanged         |
| `steam_detected_home` @T-24h    | 26,359                                     | **0**                                     | ✅ gated (`min_horizon` = T-1h)     |
| `bookmaker_count_total` @T-24h  | pooled 1,364 dates / median-of-max **145** | **0 dates** pooled / median-of-max **19** | ✅ genuine count (predicted ~21)    |
| HT rows                         | 1,467 dates                                | **0**                                     | ✅ honest absence                   |

- **Residual leak lives ONLY on the aborted dates**: `clv_home` dirty-after = 329 dates, `subset_of_blocked = True`, **0
  leaked cells on any written date** (all five markers).
- **Zero non-HT fixture losses** across 1,524 written dates. Net fixture-slot delta −134 = HT-only fixtures vanishing
  with the HT horizon (the justified class the guard's own test pins).
- **All 337 aborted shards intact** — row counts identical before/after.

### 5. ML-readiness — the number DROPPED, and that is the correct result

`verify_ml_readiness.py --start-date 2020-06-07 --end-date 2026-06-20`:

| metric        | BEFORE (doc, 2026-07-16) | AFTER (measured 2026-07-17) |
| ------------- | ------------------------ | --------------------------- |
| dates checked | 2,205                    | 2,205                       |
| passed        | **1,021**                | **177**                     |
| failed        | 791                      | 1,683                       |
| missing       | 393                      | 345                         |
| avg non-NULL  | **94.0%**                | **80.0%**                   |
| gate met      | NO                       | NO                          |

**This is the leak leaving, not a regression.** Failures read `non-NULL at target horizons 77.0% < 95%` — i.e. the T-24h
rows now honestly carry NULL where the closing line used to be broadcast in. Internally consistent: before 1,021+791 =
**1,812** = the doc's census; after 177+1,683 = **1,860** = my 1,861 minus `2020-06-06` (outside the range); missing
393→345 = the 48 in-range gap-fill dates. **Nothing was tuned to improve this number** — the 95% threshold was
calibrated against a leaking matrix and is now structurally unmeetable; re-basing it is filed as a P1 todo above.

### 6. Honest limits of this leg

- **337 dates (18.1%) still carry the leak** — the guard refused to purge them because doing so would delete 800
  fixtures. They are 49 contiguous winter-clustered windows: a second, distinct upstream starvation mechanism that the
  `batch_footystats` merge did not address. P0 todo above.
- ~~**Fix (b) — the `reprocess_sports_odds.py` (MDPS) guard — remains OPEN**~~ → **CLOSED 2026-07-17,
  `market-data-processing-service@6d20fb18`** (tracked in
  `./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`). This leg shipped fix **(c)** (the features
  guard); the MDPS side is now guarded too — observation-SET containment per horizon at the (fixture × bookmaker) grain,
  T-0 exemption sourced from `POST_KICKOFF_CONTAMINATED_HORIZONS`, fails closed. Proven live: a real `--force` on
  `day=2023-01-08` blocked (514 → 61 observations), shards byte-identical; 15/16 dates blocked across 2023-01-05..20.
  **Anyone running the MDPS tool historically is now protected.** That leg also IDENTIFIED the second starvation
  mechanism behind this doc's 337 aborted dates — see the P0 todo above (empty `fixture_id` collapses the dedup key).
- **`fss-backfill-vm-3` died without its EXIT trap firing** (SPOT preemption): its `EXIT_STATUS` still reads `RUNNING`
  while the instance is gone, so its chunk `2017-04-22..2018-06-16` is silently incomplete. Not this leg's lane —
  flagged for the campaign owner.

---

## Fixture-identity collapse — FIXED (2026-07-17)

> **Shipped**: `market-data-processing-service@9f2560b7` (verified `merge-base --is-ancestor origin/live-defi-rollout`).
> QG `--no-fix` green — **2040 passed / 1 skipped**, sentinel `.qg_last_passed_sha` == HEAD (verified by CONTENT, not
> exit code). **Zero mutations to the corpus**: every measurement below is a read or a `--dry-run`; the recompute is
> deliberately NOT run (scoped as its own P0 todo above).

### 1. REPRODUCED first — the report was not taken on trust

Real reader (`reprocess_sports_odds._read_raw_odds`) + real adapter
(`SportsBucketAssignmentAdapter.process_to_bucketed_df`), never a re-implementation. The signature is exactly as
diagnosed, on 2/2 collapsed and 4/4 healthy dates:

| day            | raw rows | `event_id`        | `fixture_id`         | signature | derive (pre-fix)          |
| -------------- | -------- | ----------------- | -------------------- | --------- | ------------------------- |
| **2024-01-15** | 3,759    | 5 distinct, 100%  | present, **0/3,759** | COLLAPSED | **166 rows / 1 phantom**  |
| **2025-02-05** | 3,246    | 4 distinct, 100%  | present, **0/3,246** | COLLAPSED | **181 rows / 1 phantom**  |
| 2022-04-16     | 83,916   | 68 distinct, 100% | **ABSENT**           | HEALTHY   | 5,635 rows / 68 fixtures  |
| 2023-05-10     | 10,199   | 11 distinct, 100% | **ABSENT**           | HEALTHY   | 1,515 rows / 11 fixtures  |
| 2024-11-09     | 147,110  | 91 distinct, 100% | **ABSENT**           | HEALTHY   | 14,077 rows / 91 fixtures |
| 2025-04-12     | 168,653  | 97 distinct, 100% | **ABSENT**           | HEALTHY   | 14,255 rows / 97 fixtures |

`fixture_id` on the collapsed generation is **literally the empty string** (`object` dtype, `nunique=1`, value `''`) —
not NaN, not whitespace. That is why `"fixture_id" not in df.columns` never fired.

### 2. Two inherited numbers CORRECTED (re-measured, per the standing never-inherit rule)

1. **"~840 expected / ~80% destroyed" on `2024-01-15` was an ESTIMATE** (`5 × 21 × 8`). Measured post-fix: the derive
   yields **746 rows**, not ~840 — not every (fixture × bookmaker × horizon) cell exists (staleness caps + missing
   snapshots). The real destruction on that date is **166/746 = 77.7% destroyed**. Corpus-wide the figure is **worse**
   than the doc's ~80%: **94.8%**.
2. **"337 dates" is the FEATURES-side symptom, not the MDPS blast radius.** Measured directly on MDPS: **448 dates**
   carry the collapsed signature and **423** change on re-derive. The two sets overlap but are not the same population
   (the 337 were winter-clustered; the 448 span **every year 2020→2026** and are heaviest in **2026: 110**).

### 3. THE FIX

`bucket_assignment_adapter.py` — identity is resolved EXPLICITLY, never inferred from a column's presence:

- `FIXTURE_ID_COL_CANDIDATES = ("event_id", "fixture_id")` + `resolve_fixture_ids()` — coalesce, **blank == ABSENT**,
  values normalised to `str`. This is the (b) guard's `_resolve_fixture_ids`, **moved to the adapter** (the authority on
  its own dedup grain) rather than copied — `odds_loss_guard` now imports it, so the two **cannot** disagree about what
  an entity is. Same sourcing pattern as `POST_KICKOFF_CONTAMINATED_HORIZONS`. A regression test pins the identity
  (`odds_loss_guard.resolve_fixture_ids is resolve_fixture_ids`).
- `_materialise_fixture_identity()` runs in `pivot_mtds_to_wide` **and** `_prepare_tick_data` (the already-wide path
  skips the pivot and previously reached dedup with a blank key). Idempotent; drops the redundant `event_id` so both raw
  generations converge on ONE output shape. Column POSITION is preserved (rename-then-overwrite when `fixture_id` is
  absent), so healthy dates keep a byte-identical shape.
- **Fails LOUD, never collapses**: identity unresolvable on every row → `MalformedTickFieldError` (→ `attempted_failed`,
  a diagnosable source-format problem — never a false `empty_confirmed`). Partial → the unkeyable rows are dropped with
  a loud `logger.warning` (they would otherwise merge into one phantom fixture). **Measured: 0/1,934 dates hit either
  path** — the real corpus always resolves.
- `_get_dedup_columns` **refuses** an all-blank `fixture_id` (raises) rather than dropping the column — dropping it
  would silently fall back to `(bookmaker, horizon)`, i.e. the identical collapse by another route.

### 4. BLAST RADIUS — full corpus, both adapters run for real

The **real pre-fix adapter** (loaded from `git show HEAD:…`) and the **real post-fix adapter** were run over **every
date 2020-06-01 … 2026-06-30 — 2,221 dates, zero gaps**, comparing observation SETS per horizon on the shared resolver.
(283 dates have no raw; 4 dates — `2026-06-21..24` — raise the reader's own pre-existing `RawOddsShapeUnrecognizedError`
(meta-snapshot-only blobs), unrelated to this fix.)

| measure                           | value                                                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------------------- |
| dates with raw data               | **1,934**                                                                                         |
| COLLAPSED signature               | **448** (23.2%)                                                                                   |
| derive CHANGES                    | **423** (all 423 are collapsed-signature)                                                         |
| collapsed-signature but NO change | 25 — **all single-fixture days** (collapse is a no-op there: exactly what the mechanism predicts) |
| HEALTHY (`event_id` only)         | 1,486 — **0 changed**                                                                             |
| rows on collapsed dates           | **60,517 → 1,173,798** (**94.8% was destroyed**)                                                  |
| observations gained               | **+1,113,281**                                                                                    |

**ADDS-ONLY — PROVEN, not argued:**

| assertion                         | measured      |
| --------------------------------- | ------------- |
| dates losing ≥1 observation       | **0** / 1,934 |
| dates where `new_rows < old_rows` | **0** / 1,934 |
| dates losing ≥1 fixture           | **0** / 1,934 |
| healthy dates changed at all      | **0** / 1,486 |

### 5. The (b) guard PASSES the post-fix re-derive — on the date it blocked

The strongest available proof: the (b) leg recorded `LOSS_GUARD_BLOCKED day=2023-01-08 … observations 514 -> 61` (2,019
lost). Post-fix, through the **real production CLI** (`--force --dry-run`, guard runs identically in dry-run):

```
LOSS_GUARD_PASS 2023-01-08 [no_loss] — Every retained horizon reproduces its observations (514 -> 514); justified drops: none.
  2023-01-08: 48915 rows → 3734 bucketed (8 horizons, 18 bookmakers)
```

And the (b) leg's own 16-date census `2023-01-05..20`, which blocked **15/16** pre-fix, is now **16/16 PASS, 0 blocked**
— observations only ever rise or hold:
`72→83 · 141→160 · 84→179 · 102→117 · 514→514 · 86→168 · 18→18 · 440→440 · 111→119 · 46→48 · 149→282 · 568→621 · 45→48 · 118→148 · 986→991 · 196→217`.
The two dates the (b) leg cited to justify set-vs-count containment (`2023-01-17` 46→47 losing 40; `2023-01-19` 45→45
losing 4) now read `no_loss`.

### 6. 🔴 NOTIFY-OPERATOR — the collapse is LIVE, not historical

The signature reaches the **corpus edge**: **2026-04: 28 dates · 2026-05: 28 · 2026-06: 8**, last collapsed date
**2026-06-20**, against only **9** healthy dates in all of 2026. `2026-05-17` derived **184 rows where the raw supports
16,938** (98.9% destroyed). So the ODDS_API writer is **still emitting a blank `fixture_id`**, and every recent derive —
including anything the rolling `mdps_odds_horizon_scheduler` recon window touched while sports was live — collapsed the
day to ~one fixture per bookmaker. MDPS@9f2560b7 makes the derive immune from now on; the **writer** is a separate P1
todo above. **This also means the recompute is not purely historical clean-up — it is repairing live data.**

---

## Phantom-block + pivot fixes EXECUTED (2026-07-17) — the last 194 dates closed

> **Shipped**: features-service@16fdd141 (fix (c) blank == absent) · market-data-processing-service@4172156 (pivot
> bookmaker-coalesce + metadata-exclusion). Both QG-green by `.qg_last_passed_sha == HEAD`; scoped
> `quickmerge --agent --files`; the 4 live `codex/09-strategy` foreign WIP files were PROTECTED (never staged). Sports
> consolidators live; per-VM manifest shards (`feat-rerun-*`, `mdps-f2-rederive-*`, `feat-f2-*`) absorbed by the `*/1`
> consolidators.

### 1. FINDING 1 — (c) features guard blank-`''` phantom (rec A) — features-service@16fdd141

`loss_guard.py` `_fixtures_by_horizon` now builds identity sets through `_resolve_fixture_id_set` (blank/whitespace ==
ABSENT, str-normalised), so the collapsed-era blank `''` fixture cell is dropped on BOTH old and new sides before the
per-horizon containment check. The `derive_empty` branch's `lost_by_horizon` filters phantom-only horizons. **Cross-repo
constraint**: features-service (T4) may not import the MDPS `resolve_fixture_ids` (service→service dep ban), so the
`blank == absent` semantics are duplicated locally and pinned to parity by the shared 192-class test vector — the two
guards agree by contract, not by a shared symbol.

**Verified on real data first** (grep-then-READ): the blank lives in `event_id` (the column the guard measures) as a
literal empty string. `2020-06-06` shard = 1 real fixture + 2 blank cells; `2026-06-20` shard = ONLY blank (3 rows);
`2024-01-01` = 13 real, 0 blank.

**Re-ran all 192 blocked dates** (`odds_features --force`, real production CLI, 4-way, resumable ledger): **192/192 PASS
· 0 blocked · 0 error** (rc=0 on 192/192). By year 2020:78 · 2024:6 · 2026:108. **4,532 real fixtures written (was
phantom), 0/192 dates lose a real fixture** (`fx_after < fx_before` on 0/192), 13,385 odds_features rows,
`CLV features: 0` at pre-match horizons (leak purged). Spot: `2026-05-17` 0→104 fixtures (311 rows), `2024-01-01` 13→13.

**Real protection PRESERVED** (8 new tests, all pass in QG): old {A,B,'',C} vs new {A,B,C}→PASS; all-phantom {''}×3 vs
real→PASS; blank-both-sides→PASS; whitespace-only→absent; **old {A,B,'',D} vs new {A,B,C}→BLOCK on D** (a genuine vanish
still aborts even with a blank present — the fix does not weaken the guard). QG green (17,679 passed, 209 skipped;
`.qg_last_passed_sha == HEAD`).

### 2. FINDING 2 — MDPS pivot empties on stray metadata — market-data-processing-service@4172156

Reproduced on real data (never inherited): the doc named `venue`/`instrument_type`/`data_source` as the stray columns
(true for `2026-02-09`, NaN on 99.95%), but `2025-02-16` is a **split bookmaker identity** — `venue` populated 90.64%,
`bookmaker_key` 9.36%, covering **DISJOINT fixtures** (65 via venue, 6 via bookmaker_key, ZERO overlap) — and
**`available_at`** is the additional NaN culprit there (NaN on the 77,442 venue/`trades` rows).
`pivot_table(index=group_cols)` drops any NaN-index row, emptying the whole derive.

**Fix** (two parts): (i) `_materialise_bookmaker_identity` coalesces `venue`/`bookmaker_key` (blank == absent) into one
authoritative `bookmaker_key` — a strict generalisation of the old `rename(venue→bookmaker_key) only-if-absent`; (ii)
`_PIVOT_INDEX_EXCLUDE` keeps `instrument_type`/`data_source`/`source`/`data_type`/`available_at` out of the pivot index
(vendor metadata / PIT stamps, not grain). Safe: `read_bucketed_odds` (the sole features consumer) uses only
fixture/bookmaker/horizon/odds; features stamp their own `available_at` from `kickoff_utc`; the current shards already
carry these columns inconsistently across generations.

**Before/after harness** (real pre-fix adapter from `git stash` + real post-fix adapter, same cached raw): both problem
dates **EMPTY → 2025-02-16 71 fixtures (28,507 pivot rows) / 2026-02-09 18 fixtures (4,234)**; two HEALTHY controls
`2024-11-09` (91 fx) and `2023-05-10` (11 fx) **odds-data byte-identical** (sha match), only the non-consumed metadata
passenger columns dropped. QG green (`.qg_last_passed_sha == HEAD`); 6 new tests.

### 3. The 2 empty-derives re-derived

- **2026-02-09**: MDPS `--force` → **LOSS_GUARD_PASS [no_loss] (378→378), 2,697 rows / 79 shards, 0 blocked**; features
  `--force` → **PASS (18→18), 54 rows, CLV=0**. Fully repaired.
- **2025-02-16** (the AMBIGUOUS mixed-generation date): the pivot fix makes the derive yield 71 fixtures / 10,516
  bucketed rows, but the **(b) loss guard correctly BLOCKS the write** — `observation_loss`, 62 (fixture,bookmaker) obs
  at T-10m(20)/T-1h(21)/T-2h(21), justified T-0 drop 40. **Diagnosed (STOP, do not force)**: the block is ONE fixture
  `058da690…` whose earliest CURRENT-raw snapshot is 164.8 min pre-kickoff (0 rows in the T-10m/T-1h/T-2h windows),
  while the intact corpus holds it there (bm 6.0–14.8 / 64.6–68.8 / 124.5–132.0) from a **fuller past raw** — the
  parent-issue "richer than its own upstream" raw-truncation class, NOT the phantom and NOT the pivot fix. Corpus
  preserved intact; features re-derived clean against it (**PASS 71→71, 213 rows, CLV=0**). This belongs to
  `./sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md` (legacy→canonical raw recovery), not to this
  leg.

### 4. ML-readiness — FLAT, tuned nothing

`verify_ml_readiness.py --start-date 2020-06-07 --end-date 2026-06-20`:

| metric       | BEFORE this leg | AFTER (2026-07-17) |
| ------------ | --------------- | ------------------ |
| passed       | 53              | **53**             |
| failed       | 1,683           | **1,839**          |
| missing      | 345             | **313**            |
| avg non-NULL | ~79%            | **78.1%**          |
| gate met     | NO              | NO                 |

Passed **FLAT at 53**; avg drifted 79%→78.1% because the 192 dates now hold many real fixtures whose T-24h rows honestly
carry NULL for the ~27 closing-derived columns (the leak leaving, not a regression). **Nothing tuned** — the 95%
threshold is calibrated against the old leaking matrix and is structurally unmeetable on the honest matrix (the P1
recalibration todo above). The 313 missing are pre-existing coverage holes owned by the gap-fill campaign.

### 5. All 449 collapse dates — terminal state

447 MDPS adds-only + 2026-02-09 re-derived = **448 recomputed with real data**; **2025-02-16** intact corpus preserved
(re-derive correctly refused on raw truncation). Features: 255 + **192/192 phantom-unblocked** + 2 finding-dates clean.
The instruction ("just fix the leakage in the odds and any associated features") is closed: the (c) guard no longer
over-blocks a phantom, the pivot no longer empties a real date, and every date is in its correct, honest state.
