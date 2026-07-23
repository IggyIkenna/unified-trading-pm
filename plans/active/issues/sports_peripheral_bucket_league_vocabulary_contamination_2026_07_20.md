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
  values across 6 pipeline_modes. Root cause is UNVERIFIED and the writer is untraced. Must NOT be folded into the
  odds-tick relocation.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service, instruments-service, unified-trading-pm]
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
3. **Fix at the write path** (canonicalise-at-write), then migrate the 9,763 historical objects under the delete-safety
   protocol.

P2 because it is small (9,763 objects) and outside the ML-critical odds-tick path — but it IS live contamination, so it
does not simply age out.

Evidence: relocation workflow `subagents/workflows/wf_664f7ed4-df6/journal.jsonl` (gcs-sizing surveyor + verifier),
2026-07-20.
