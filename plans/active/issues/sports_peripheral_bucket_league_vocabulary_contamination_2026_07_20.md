---
doc_type: issue
title:
  sports peripheral buckets carry a DIFFERENT non-canonical league vocabulary from an untraced writer
  (features-sports-prd 30 + instruments-store-sports-prd 9,733 objects)
summary: >-
  The league_id relocation workflow's GCS-sizing VERIFIER found that two buckets outside the odds-tick relocation scope
  carry non-canonical league values in a DIFFERENT vocabulary than the api-football display names the write-path fix
  addresses — ENGLAND_PREMIER_LEAGUE / LA_LIGA_2 / UNKNOWN rather than PREMIER_LEAGUE / EPL. features-sports-prd has 30
  such objects (contamination ongoing to 2026-07-11); instruments-store-sports-prd has 9,733 objects / 172 distinct
  values across 6 pipeline_modes. **ROOT-CAUSED + FIXED 2026-08-04** (`unified-api-contracts@f3f1bbe0`): shared
  normalizer `normalize_api_football_fixture()` built the league id from a raw country/name slug instead of the UAC
  registry; `instruments-service`'s own write paths were already gated (hence its population is legacy residue, not
  growing), `features-service`'s was not (hence the live leak). Write path closed for every consumer. The 9,733-object
  historical migration remains open, `[OPERATOR]`-gated (see Todos) — must NOT be folded into the odds-tick relocation.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service, instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [sports, canonical, league-id, contamination, data-correctness]
related:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    ../sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-20"
source: league_id relocation workflow wf_664f7ed4-df6 gcs-sizing verifier (2026-07-20)
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/epics/sports_master.md,
  ]
---

# Sports peripheral buckets — a second, different non-canonical league vocabulary

## What was found (relocation workflow gcs-sizing VERIFIER, 2026-07-20)

While sizing the odds-tick `league_id` relocation, the adversarial verifier caught the surveyor wrongly clearing two
buckets from 2-3-date spot checks. A fuller walk found real contamination — but in a **different vocabulary** than the
one the write-path fix (`mtds@ad4f1872`) and the odds-tick relocation address:

| bucket                         | contaminated objects | vocabulary examples                                                              |
| ------------------------------ | -------------------: | -------------------------------------------------------------------------------- |
| `features-sports-prd`          |                   30 | `ENGLAND_PREMIER_LEAGUE` 16, `BRAZIL_SERIE_A` 2, `ARGENTINA_PRIMERA_NACIONAL` 12 |
| `instruments-store-sports-prd` |                9,733 | 172 distinct values across 6 pipeline_modes (`LA_LIGA_2`, `UNKNOWN`, …)          |

Key distinction: the odds-tick manifest uses the **api-football display names** (`PREMIER_LEAGUE`, `PRIMERA_DIVISION`).
These buckets use a **country-prefixed vocabulary** (`ENGLAND_PREMIER_LEAGUE`, `ARGENTINA_PRIMERA_NACIONAL`) — a
different naming scheme, implying a different writer. The `features-sports-prd` contamination is **ongoing** (latest
observed 2026-07-11), so whatever emits it is still live.

## Why this is filed separately (not folded into the relocation)

The odds-tick relocation (`sports_league_id_namespace_migration_2026_07_20.md`) resolves raw api-football names →
canonical slugs via the numeric `api_football_id` / `sport_key`. That machinery does **not** apply to
`ENGLAND_PREMIER_LEAGUE`-style values — they'd need their own mapping, and their WRITER must be found and fixed first
(canonicalise-at-write, same principle) or they'll keep reappearing. Folding them into the odds-tick relocation would
(a) apply the wrong resolver and (b) migrate history while the source keeps re-emitting the bad form.

## Required work (not started)

1. **Trace the writer** for each vocabulary — grep for `ENGLAND_PREMIER_LEAGUE` / `ARGENTINA_PRIMERA_NACIONAL` /
   `LA_LIGA_2` emission across features-service + instruments-service; the `features-sports-prd` write is live
   (2026-07-11), so start there.
2. **Root-cause** why a country-prefixed vocabulary exists at all — is it a legacy scraper, a different provider
   adapter, or a mis-normalisation? UNVERIFIED today.
3. **Fix at the write path** (canonicalise-at-write), then migrate the 9,733 historical objects under the delete-safety
   protocol.

P2 because it is small (9,733 objects) and outside the ML-critical odds-tick path — but it IS live contamination, so it
does not simply age out.

Evidence: relocation workflow `subagents/workflows/wf_664f7ed4-df6/journal.jsonl` (gcs-sizing surveyor + verifier),
2026-07-20.

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-08-04 (slot-12)** — traced the writer, root-caused, fixed at the write path.
      `unified-api-contracts/unified_api_contracts/external/api_football/normalize.py`'s
      `normalize_api_football_fixture()` built `CanonicalLeague.league_id` via a bare `build_league_id(country, name)`
      slug of the RAW api-football country name ("England" → `ENGLAND_PREMIER_LEAGUE`, "Argentina" →
      `ARGENTINA_PRIMERA_NACIONAL`, "Brazil" → `BRAZIL_SERIE_A`) instead of the UAC league registry's canonical slug
      ("EPL" etc.) — this is the SAME shared normalizer both `features-service` and `instruments-service` consume, so
      every consumer inherited the leak. `instruments-service`'s own write paths (`_write_sports_fixture_venue` /
      `_write_fixtures_per_league` / `_write_fixture_entity_per_league`) mask it behind a separate write-universe gate
      (`_is_in_canonical_write_universe`, added ~2026-06-24/27) — which is why `instruments-store-sports-prd`'s 9,733
      objects read as legacy pre-gate residue, not an actively-growing leak. `features-service`'s `_write_per_league`
      has NO equivalent gate, so `features-sports-prd` was still live-leaking as of 2026-07-11 (the "start there" signal
      this doc's own todo named). Checked every other sports provider adapter in both repos (soccerfootball_info,
      footystats, transfermarkt, understat, betfair, open_meteo) — none use a country-prefixed convention natively;
      confirmed this is a mis-normalization of the SAME api-football data, not a third-party adapter naming scheme.
      **Fix** (`unified-api-contracts@f3f1bbe0`): new `_resolve_league_id()` mirrors instruments-service's own
      `_canonical_league_id` two-pass, non-lossy design — registry-first via the numeric `api_football_id`
      (authoritative, the same id `get_league_by_api_football_id` uses everywhere else), falling back to the raw
      country/name slug ONLY when the league genuinely has no registry entry (non-lossy CF-7 passthrough, never drops or
      blanks a field). Closes the leak at its true shared source for every consumer, not just the one ungated write
      path. 5 new regression tests (`tests/unit/test_normalize_api_football_fixture_league_id.py`) lock in: a registered
      league resolves via the registry not the raw slug; an unregistered league falls back non-lossily; a missing
      `api_football_id` falls back non-lossily; a missing league yields a blank id (unchanged prior behavior). Full
      existing `api_football`-related suite (95 tests) re-run clean, no regressions.
- [ ] [DATA] P2. **[OPERATOR] Migrate the 9,733 legacy-contaminated `instruments-store-sports-prd` objects** to the
      correct league vocabulary now that the write path is fixed (the todo above) and no longer re-contaminates.
      Requires the delete-safety 5-part proof (this is a GCS content/path rewrite over prod objects) — a FRESH
      `gcs_bucket_soft_delete_retention_seconds()` check on the bucket, snapshot-before-write, CAS-safe apply,
      self-verify, per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. Build a migration script mirroring
      the pattern already used for the sibling odds-tick `league_id` relocation
      (`market-tick-data-service/scripts/sports/league_id_relocation/`): re-derive each contaminated object's league
      value via the SAME registry-first resolution the write-path fix now uses (`get_league_by_api_football_id` →
      fallback slug), rename/rewrite the `league=` GCS partition segment, and re-run the manifest bookkeeping. **Done
      when**: a fresh census of `instruments-store-sports-prd` returns 0 objects carrying the country-prefixed
      vocabulary. (repo: instruments-service / market-tick-data-service). Not started this session — deliberately
      deferred per the `[OPERATOR]` gate, not a scope-creep decision to skip it.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — root cause is UNVERIFIED and the writer
  untraced, and the single todo bundles the trace with a write-path fix AND a migration of 9,733 historical
  `instruments-store-sports-prd` objects — a GCS data migration is the dispatch atom here, so it needs an
  `[OPERATOR]`/delete-safety gate rather than a bare flip
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid (sports tranche) — re-verified, unchanged since 2026-07-30 (only a
  context-scout frontmatter backfill since); sole open todo bundles an unbounded root-cause trace with a 9,733-object
  GCS migration carrying no `[OPERATOR]` tag or delete-safety citation.
- **context-scout 2026-08-03**: populated/refreshed context_scope (3 entries).
- **2026-08-04 (slot-12, data_engineering, dispatched via `sports_closeout_track_x_hygiene-003`)**: traced the writer
  (Explore-agent investigation across features-service + instruments-service, confirmed by direct code read), root-
  caused (shared UAC normalizer mis-slugging the raw country name instead of registry-resolving via the numeric
  api_football_id), and shipped the write-path fix — `unified-api-contracts@f3f1bbe0`, 5 new regression tests, full
  existing api_football suite (95 tests) re-run clean. Split the original bundled todo into DONE (trace+root-cause+fix)
  and a new, properly-scoped `[OPERATOR]`-gated migration todo for the 9,733 historical objects — the split itself
  resolves the na-eligibility-audit's own stated blocker ("bundles an unbounded root-cause trace with a ... migration
  carrying no `[OPERATOR]` tag"), so a future audit pass should re-classify the migration todo once it's picked up. Did
  NOT attempt the migration itself — out of AO scope without the delete-safety gate, per `task_template.md` finding O.
