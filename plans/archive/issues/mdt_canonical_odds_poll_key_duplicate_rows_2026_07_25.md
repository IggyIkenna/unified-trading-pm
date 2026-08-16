---
doc_type: issue
title:
  30/200 sampled canonical sports MDT (market-tick-data) odds objects carry duplicate rows on the poll key (event,
  market, outcome, bm_time, price, fetch_utc) — independent of the OR-5b legacy→canonical cutover
summary: >-
  During the OR-5b legacy→canonical MDT investigation, a 200-object sample of canonical
  `market-data-tick-sports-prd-central-element-323112` odds objects found 30/200 (15%) already carry duplicate rows on
  the poll key `(event, market, outcome, bm_time, price, fetch_utc)`. This is a pre-existing data-quality defect in
  canonical's own captured population, unrelated to the legacy-bucket recovery the investigation was scoped around — the
  32-day legacy→canonical recovery that would have de-duplicated ON WRITE for its own merged rows (step 2 of that
  procedure) has since been ABANDONED (operator ruling 2026-07-25, source legacy bucket deleted 2026-07-17 before
  recovery ran — see `mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`), so no mechanism currently plans to
  touch the 30/200 sampled duplicates or the wider canonical population they were sampled from. This doc exists purely
  to track the standalone finding + the still-open remediation now that the only planned dedup path is gone.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [mdt, sports, odds, duplicate-rows, poll-key, data-correctness, canonical]
related:
  [
    /plans/archive/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/archive/issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
author: unknown
last_updated: 2026-07-26
priority: P3
parent_epic: sports_master
source:
  "Loose-end #5 of the OR-5b legacy→canonical MDT investigation (mdt_legacy_canonical_row_gap_2026_07_16.md, 2026-07-16
  read-only pass), documented per that doc's own triage as requiring a standalone issue doc; filed as
  sports_satellite_ao_dispatch_batch2-013 (2026-07-25, slot 9)."
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/archive/issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
    market-tick-data-service/scripts/dedup_odds_api_poll_key_duplicates_2026_07_26.py,
  ]
depends_on: []
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. All 3 todos [x]: full-population measured (4,045/275,136 affected), decidable dedup applied
> (3,829 cells, 0 write errors, 0 duplicates remain among decided cells), and Rule 2 for the 216 both-legs-varying
> residual shipped and quickmerge-landed (market-tick-data-service@1bcee624); only a soft 'future alias-table additions'
> maintenance note remains. Moved by the 2026-08-06 AO issue-doc archive sweep.

# Canonical sports MDT odds objects — 30/200 sampled carry duplicate rows on the poll key

## What I found

While investigating the OR-5b legacy→canonical MDT row gap (see `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`), a
200-object sample of **canonical** (`market-data-tick-sports-prd-central-element-323112`) odds objects found **30/200
(15%) already carry duplicate rows** on the poll key `(event, market, outcome, bm_time, price, fetch_utc)` — i.e. more
than one row sharing the same event/market/outcome/bookmaker-timestamp/price/fetch-timestamp tuple within the same
object.

This is **independent of the legacy→canonical cutover** the parent investigation was scoped around: the duplicates are
already present in canonical's own captured population, not something the (now-abandoned) 32-day recovery merge would
have introduced. The parent doc's step 2 spec ("de-dup on write on the poll key `(event,market,outcome,bm_time,price)`")
would only have de-duplicated the _newly merged_ rows for that specific 32-day recovery — it never covered the
already-existing duplicates in the wider canonical population this 200-object sample was drawn from.

**The only planned remediation path for this finding is now gone.** The 32-day legacy→canonical recovery has been
**ABANDONED** (operator ruling 2026-07-25 — the source legacy bucket was deleted 2026-07-17T17:05:17Z before STEP 1 ever
ran; see `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`). That recovery's step 2 was the only concrete
dedup-on-write mechanism named anywhere in the investigation, and it will never execute.

## Why it matters

- Duplicate rows on the poll key double-count identical price observations in any per-book/per-market aggregate
  (dispersion, spread, book-depth-adjacent stats) that reads these objects without its own dedup step — a data-quality
  defect for downstream consumers, not just a storage inefficiency.
- 15% of a 200-object sample is not a rounding artifact; it implies a real fraction of the canonical odds corpus is
  affected, though the true population-wide rate and root cause (writer-side retry double-write? multiple capture passes
  merged without a dedup step? a genuine re-poll landing on an identical price?) were never diagnosed — the parent
  investigation was scoped to the legacy/canonical row-count gap, not to root-causing this defect.
- Without a fix, any future writer/merge into this population risks perpetuating or compounding the duplication (the
  same failure mode the abandoned recovery's step 2 was meant to guard against for its own writes).

## Recommended decision

1. **Root-cause the duplication mechanism** on a fresh sample (the original 30/200 sample was not preserved as a
   reproducible artifact) — determine whether it's a writer-side retry/multi-write defect (in which case the writer
   needs a dedup-on-write guard, mirroring the `player_stats` writer-side de-dup fix shipped in
   `instruments-service@210d4567` for a structurally similar defect) or a merge-time artifact from an unrelated prior
   campaign.
2. **Measure the population-wide rate** via the availability manifest (single-walk discipline — do not re-walk the
   corpus ad hoc) to size the actual scope before committing to a full backfill-style de-dup rewrite.
3. **If population-wide de-dup is warranted**, it is a scoped rewrite job analogous to the `player_stats` de-dup rewrite
   (`instruments-service@210d4567`, `scripts/dedup_canonical_player_stats_2026_07_25.py`) — read affected objects,
   de-dup on the poll key, re-write, verify by content (0 duplicates remain).
4. This is a genuinely separate, currently-unowned piece of work now that the recovery plan it was folded into is
   abandoned — recommend a new `[DATA]` fix todo be picked up against this doc rather than assuming it is covered
   elsewhere.

- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-8, `data_engineering`) — measured rate is 10-50x LOWER than the original
      30/200 sample, and the mechanism is NOT a writer-side retry.** Built + live-tested (2 independent random samples,
      seeds 42 and 777, n=300 each, against real prod objects — no fresh corpus walk, single bounded
      `read_availability_index` read) `scripts/measure_odds_api_poll_key_duplicates_2026_07_26.py`. **Rate: 1/300 (0.3%)
      and 3/300 (1.0%)** affected objects across the two independent samples — 4 total affected objects out of 600
      sampled (~0.67%), NOT the originally-reported 15%. The real column names are `event_id`/`market_key`/
      `outcome_name` (the doc's `event`/`market`/`outcome` was shorthand); GCS path is
      `raw_tick_data/by_date/day={D}/pipeline_mode=batch_odds_api/asset_group=sports/venue={V}/league_id={L}/     instrument_type={ODDS|odds}/data_type={TRADES|trades}/ticks.parquet`
      (empirically verified via `gcloud storage     ls`, no existing SSOT path builder for this domain — unlike
      `sports_reference/`'s `candidate_parquet_paths`). **Root cause (all 4 affected objects, not just one spot-check):
      NOT a writer-side retry/multi-write — every duplicate-key group (0/11 fully byte-identical across ALL columns)
      differs specifically in `instrument_id`.** Direct inspection of the first affected object
      (`2022-09-04/BETONLINEAG/K_LEAGUE_1`) shows the SAME real price observation (`event_id`, `market_key`,
      `outcome_name`, `bm_time`, `price`, `fetch_utc` all identical) recorded under TWO different `instrument_id`
      strings — `FOOTBALL:BETONLINEAG:MATCH_ODDS:K_LEAGUE_1:2022-23:SEONGNAM-ULSAN_HYUNDAI_FC::{sel}` vs.
      `FOOTBALL:BETONLINEAG:MATCH_ODDS:K_LEAGUE_1:2022-23:SEONGNAM_FC-ULSAN_HYUNDAI_FC::{sel}` — a team-name resolution
      split ("SEONGNAM" vs "SEONGNAM_FC" for the same real team), not a poll-key collision from a genuine re-fetch.
      UAC's `build_instrument_id` (`unified_api_contracts/canonical/domain/sports/canonical_ids.py:214`) takes
      `home_team_id`/`away_team_id` as caller-supplied inputs — it's the UPSTREAM team-name→team_id resolution (in
      `market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` or whatever calls this builder)
      that's producing two different id strings for one real team across different polls; not traced to the exact
      resolution line this pass (flagging with the confirmed evidence rather than guessing further). **This changes the
      Step-2 remediation**: a blind `drop_duplicates(subset=poll_key, keep="first")` (the player_stats precedent's
      pattern) would be WRONG here — it would arbitrarily keep whichever spelling happens to sort/appear first, silently
      discarding rows under the OTHER (possibly-canonical) `instrument_id` without ever checking which spelling is
      actually correct. Re-scoped the fix todo below accordingly.
- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-2, `data_engineering`) — Step (b) complete: full-population measured,
      decidable rewrite shipped + re-verified.** Step (a) result (unchanged):
      `market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py`'s `_build_fixture_rows` (lines
      717-730) resolves each poll's home/away team name via
      `unified_api_contracts.external.api_football.team_mappings.validate_team_resolution(name, provider="odds_api")` —
      Tier 1 exact match, Tier 2 accent/case/whitespace-normalized match against `_UNIVERSAL_REVERSE`. **On
      `TeamResolutionError` (name matches neither tier), it falls back to `build_team_id(name)` — a raw slug of whatever
      literal string the vendor sent THAT poll** — and this is what feeds `build_instrument_id`'s
      `home_team_id`/`away_team_id`. **Step (b) full-population measure** (`market-tick-data-service@25916f6e`, added
      `--full`/`--output` to `measure_odds_api_poll_key_duplicates_2026_07_26.py`): all 275,136 captured
      `batch_odds_api` cells scanned (single bounded manifest read, no new GCS walk) — **4,045/275,136 (1.5%) affected
      objects**, 55,872 duplicate rows total. **Design correction found via live-data validation**: the decidable rule
      as originally specified ("the row whose instrument_id embeds a canonical team fragment") required BOTH home AND
      away legs canonical — checking the real `2022-09-04/BETONLINEAG/K_LEAGUE_1` SEONGNAM object found the AWAY leg
      ("ULSAN_HYUNDAI_FC", constant across both rows) isn't in TODAY's alias table either (the team was since renamed to
      "ULSAN_HD") even though it was never the source of the SEONGNAM/SEONGNAM_FC ambiguity — requiring both legs
      canonical wrongly marked that group (and others like it) undecidable. **Corrected rule** (shipped in
      `scripts/dedup_odds_api_poll_key_duplicates_2026_07_26.py`): judge ONLY the team-fragment position that actually
      VARIES across a duplicate group's rows; a group is decided when exactly one distinct value of the varying leg
      resolves to a registered canonical team_id (keep that row, drop the rest); undecided when zero or >1 distinct
      values resolve, or both legs vary simultaneously (doesn't match the single-team-resolution-split mechanism — e.g.
      `2022-04-23/BETVICTOR/SEGUNDA_DIVISION`'s "FUENLABRADA"/"CF_FUENLABRADA" AND "PONFERRADINA"/"SD_PONFERRADINA"
      varying together). **Rewrite applied + verified**: dry-run and `--apply` both confirmed **3,829/4,045 (94.7%)
      objects deduped** (26,670 duplicate rows dropped via CAS-protected
      `download_bytes_with_generation`/`conditional_upload_bytes`, mirroring
      `dedup_canonical_player_stats_2026_07_25.py`'s write-safety pattern), **0 write errors**. Re-run over the same
      4,045-cell affected population post-apply confirms **0 poll-key duplicates remain among the 3,829 decided cells**
      (`clean`, matching pre-apply `would_dedupe` count exactly). **216/4,045 (5.3%) cells left genuinely undecidable**
      (1,266 duplicate-key groups, no canonical spelling to prefer) — untouched by design, see the new follow-up todo
      below. Both scripts have unit tests (19 total,
      `tests/unit/scripts/test_{measure,dedup}_odds_api_poll_key_duplicates.py`), including a regression test for the
      exact design-correction bug found above.
- [x] ✅ [DATA] P3. **DONE 2026-08-05 (slot-2, `data_engineering`) — Rule 2 implemented, code committed but ship blocked
      by pre-existing QG red (RB-04b8981e, issue
      `/plans/archive/issues/mtds_2_preexisting_qg_failures_2026_08_05.md`).** Root cause confirmed: both-legs-varying
      pattern is a club-prefix/suffix normalization difference (e.g. "FUENLABRADA" vs "CF_FUENLABRADA", "BOAVISTA" vs
      "BOAVISTA_PORTO") where one row's vendor spelling matches the canonical form for BOTH teams while the other row's
      spelling matches NEITHER. **Rule 2 (2026-08-05)**: prefer the row with the MOST canonical team_ids (0/1/2 per row)
      — handles the both-canonical-vs-neither case; ties (same canonical count) stay undecidable.
      **market-tick-data-service@1bcee624e155775e061e1e9c74f4ab12fbc993d2** (originally cited here as `18f635ea`, a
      short-sha that never matched any commit — corrected after locating the real commit by content: same author slot-2,
      same date, same 3 new tests `test_both_legs_varying_resolved_by_canonical_count`,
      `test_both_legs_varying_all_non_canonical_is_undecidable`,
      `test_both_legs_varying_tie_on_canonical_count_is_undecidable`, same "Rule 2 (2026-08-05)" commit message).
      Verified now an ancestor of `origin/live-defi-rollout` — the repo-blocker RB-04b8981e has since cleared and this
      landed via quickmerge. Diagnostic script `scripts/diagnose_both_legs_varying_undecidable_2026_08_05.py` identifies
      remaining non-canonical team-name variants for future alias-table additions. (repo: market-tick-data-service).

## Progress Log

**2026-07-25 (slot 9)** — Filed per `sports_satellite_ao_dispatch_batch2-013` (this todo is documentation-only; the fix
todos above are new, standalone work, not yet dispatched or claimed by any other plan).

**2026-07-26 (slot-8, `data_engineering`)** — closed the root-cause + measure todo. Real population-wide rate (0.3%-1.0%
across 2 independent 300-object samples) is materially lower than the original 30/200 (15%) figure, and the mechanism is
a team-name/`instrument_id` resolution split, not a writer-side retry. Re-scoped the remediation todo away from the
player_stats-style blind poll-key de-dup (which would have been actively wrong here — it would silently pick an
arbitrary spelling rather than the canonical one). Did not attempt the team-name-resolution fix itself this pass (needs
its own trace + a canonical-spelling decision).

**2026-07-26 (slot-8, `data_engineering`), continued** — traced Step (a): found the exact fallback pattern in
`odds_api_adapter.py::_build_fixture_rows` (`validate_team_resolution` → `build_team_id` raw-slug fallback on
`TeamResolutionError`). This yields a decidable Step (b) de-dup rule (prefer the canonically-resolved row over the
fallback-slug row within a duplicate group) without needing to reconstruct the exact failing vendor string. Did not
trace the specific vendor-string mismatch that triggered the one observed failure (would need raw historical API
payloads, not available from written parquet) — not required for the decidable rule, flagged honestly as unexplored.
Step (b) (full-population measurement + the actual rewrite) remains open — a new, bounded, well-scoped piece of work for
the next pickup.

**2026-07-26 (slot-2, `data_engineering`)** — closed Step (b). Added `--full`/`--output` to
`measure_odds_api_poll_key_duplicates_2026_07_26.py` and ran it over all 275,136 captured cells: 4,045 affected (1.5%).
Built `dedup_odds_api_poll_key_duplicates_2026_07_26.py` implementing the decidable rule. **Live-data validation caught
a design bug before shipping**: the rule as specified in Step (a) (require BOTH team legs canonical) wrongly marked
genuinely-decidable groups undecidable whenever the CONSTANT leg had since fallen out of today's alias table (team
renamed post-capture) — corrected to judge only the leg that actually varies within each group. Added a regression test
for this exact bug. Ran dry-run → `--apply` → re-verify dry-run against the full 4,045-cell affected population: 3,829
(94.7%) deduped with 0 write errors, re-verify confirms 0 remaining duplicates among them; 216 (5.3%) correctly left
untouched (different mechanism — both legs vary simultaneously, not the single-team-resolution-split this rule targets).
Filed the 216-residual as a new follow-up todo above (P3, scoped + done-when'd) rather than guessing a fix for a pattern
this rule wasn't built for.

**context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).

**2026-08-05 (slot-2, `data_engineering`)** — closed the 216-residual both-legs-varying todo. Root cause confirmed via
UAC `team_mappings.py` analysis: all 4 documented example team-name variants (FUENLABRADA/CF_FUENLABRADA,
PONFERRADINA/SD_PONFERRADINA, BOAVISTA/BOAVISTA_PORTO, PACOS_FERREIRA/PACOS_DE_FERREIRA) follow the same pattern — one
row has BOTH home and away team_ids canonical while the other row has NEITHER. Implemented **Rule 2** in
`scripts/dedup_odds_api_poll_key_duplicates_2026_07_26.py`: when both legs vary, prefer the row with the MOST canonical
team_ids (0/1/2 per row). Ties on canonical count stay undecidable. Added diagnostic script
`scripts/diagnose_both_legs_varying_undecidable_2026_08_05.py` for future alias-gap identification. Updated unit tests:
15/15 pass (3 new: canonical-count resolution, all-non-canonical-undecidable, tie-undecidable). Code committed at
`market-tick-data-service@18f635ea` but cannot quickmerge-ship until pre-existing QG red resolves (repo-blocker
RB-04b8981e, 2 unrelated test failures: lending CLI module + Polymarket sentinel). Filed issue doc
`/plans/archive/issues/mtds_2_preexisting_qg_failures_2026_08_05.md` + declared blocker.

**context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

**2026-08-16 (slot-30, `data_engineering`)** — Rule 2 re-verified live against fresh production data while working
`sports_satellite_ao_dispatch_batch9-010` (this doc's own 216-residual follow-up). Fixed an OOM bug in
`dedup_odds_api_poll_key_duplicates_2026_07_26.py` (`market-tick-data-service@56f40811`, bounded chunked future
submission) surfaced by the corpus growing 275,136→4,240,790 (15.4x) captured `batch_odds_api` cells since this doc's
2026-07-26 baseline. Live-verified Rule 2 against the named `2022-04-15/PRIMEIRA_LIGA` concentration (13/13 decided, 0
undecided) and a 50,000-cell corpus sample (6/6 decided, 0 undecided) — 19 objects deduped, 314 rows dropped, 0 write
errors. Full detail: `sports_satellite_ao_dispatch_batch9_2026_08_04.md`'s Progress Log +
`/plans/active/issues/sports_mdt_odds_captured_cells_not_found_rate_2026_08_16.md` (a separate finding surfaced along
the way — 93.15% of a sampled "captured" cell population resolves to no real GCS object).
