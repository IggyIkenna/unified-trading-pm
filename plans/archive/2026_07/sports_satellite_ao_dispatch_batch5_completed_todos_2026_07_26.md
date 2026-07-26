---
doc_type: issue
title: Extracted history — 2 fully-closed DONE todos from sports_satellite_ao_dispatch_batch5_2026_07_26.md
summary: >-
  Extracted 2 fully-closed (`- [x]`) todos from sports_satellite_ao_dispatch_batch5_2026_07_26.md (2026-07-26, slot-2)
  to bring that actively multi-slot-edited plan back under the 1000-line hard cap (task_template.md finding J). Both
  items are complete historical records (a real prod fold-and-delete execution, and a capture-outage root-cause
  resolution) — no open work, nothing here needs picking up.
status: complete
nature: record
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [sports, history, extracted, archive]
related: [sports_satellite_ao_dispatch_batch5_2026_07_26]
created: 2026-07-26
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
locked_by:
---

# Extracted history: 2 completed todos from sports_satellite_ao_dispatch_batch5_2026_07_26.md

> Extracted verbatim (2026-07-26, slot-2) — both fully done, no open work.

- [x] ✅ [DATA] P1. Determine whether the canonical `batch_odds_api` sports capture pipeline is STILL susceptible to the
      confirmed 2022-09-07…2022-10-01 capture-outage pattern (the doc's own re-measurement superseded the original "92%
      under-capture over 2022-03-07…2023-04-30" headline — the real, re-measured gap is 550,062 legacy-only keys on 32
      of 1,837 days, dominated by that contiguous outage). The legacy `market-data-tick-sports` bucket that held the
      missing rows was permanently deleted 2026-07-17 (operator-confirmed deliberate abandonment 2026-07-25) — recovery
      of the lost rows is NOT possible and NOT in scope; this todo is forward-looking only: (a) inspect the current
      odds-capture adapter/scheduler logic (`odds_api_adapter.py` + whatever orchestrates the `batch_odds_api`
      June-campaign-successor capture) for a mechanism that could silently skip/under-fetch the pre-match horizon grid
      for a contiguous multi-day window the way the 2022-09 outage did; (b) measure recent (last 90 days) canonical
      pre-match key density per day against the same whole-day KEY-LEVEL containment method this doc used
      (`or5b_wholeday_check.py`-style: legacy... N/A now, so instead check day-over-day density/count anomalies in the
      canonical `batch_odds_api` capture itself) to see if any day drops to near-zero density the way the outage days
      did; (c) write a short disposition (root cause found + fixed / root cause found + still live + operator flagged /
      no reproducible mechanism found, campaign healthy) into a new issue doc
      `sports_batch_odds_api_capture_outage_recurrence_check_<date>.md`, citing this doc's SUPERSEDED-banner numbers (32
      days / 550,062 keys) as ground truth, not the original 92%/14-month headline. Source:
      `mdt_legacy_canonical_row_gap_2026_07_16.md` (Loose ends #1, "BIG FINDING → operator + own issue doc"). Done when:
      the new issue doc exists with a stated verdict on whether the outage mechanism is still live, and — if it is — the
      operator has been notified per the data-pipeline-correctness-hard-rule big-finding trigger. **Resolution
      (2026-07-26, slot 8)**: NOT the same 2022 mechanism (that one — the swallowed per-timestamp fetch error in
      `odds_api_adapter.py` — was traced and found largely mitigated by an independent sentinel safeguard) — a
      DIFFERENT, currently-live, more severe bug was found and fixed: `TickDataHandler._check_early_exit`'s future-date
      guard blocked 100% of same-day sports odds capture, unconditionally, since ≥2026-06-11 (live-verified via GCP
      logs: every dispatch today logged `DATA_NOT_AVAILABLE: date=2026-07-26 is in the future`). 90-day manifest density
      confirmed a ~94% collapse vs the same calendar window in 2024/2025. Fixed + tested + shipped
      `market-tick-data-service@410d7569`. Full writeup + operator-decision items (deploy confirmation + historical-gap
      backfill call) in `plans/active/issues/sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md` —
      `unified-trading-pm@7c94a8d14`.

- [x] [OPERATOR] P2. Fold the sibling `entity=fixtures` and `entity=fixtures_outcomes` non-canonical
      `league=169`/`league=235` GCS objects (21 rows: 12 `FIXTURES` + 9 `FIXTURES_OUTCOMES`, same 12-date/2-league
      cohort already folded for `entity=fixtures_schedule` in `instruments-service@4412e576`) into their canonical
      `league=CHINA_SUPER_LEAGUE`/`league=RUSSIA_PREMIER_LEAGUE` counterparts (repo: instruments-service). The fold
      script is already written and dry-run verified against live prod GCS (21/21 sources found, 21/21 canonical targets
      absent — pure move, zero overwrite risk): `instruments-service@1511b672`,
      `scripts/fold_china_russia_league_raw_id_folders_fixtures_siblings_2026_07_24.py`. **`[OPERATOR]` justification
      (stated safe-idempotent basis, no separate design decision needed)**: the prior escalation (`BLK-4c0c944b`) asked
      whether a manifest-consolidator cron pause was needed before `--apply`; follow-up research already answered this —
      the sibling precedent (`instruments-service@4412e576`, `entity=fixtures_schedule`) used the same
      per-VM-shard-writer pattern with NO cron pause, this fold's write pattern is structurally disjoint from the
      canonical index (cannot race the consolidator), and the general TOCTOU race class is separately fixed fleet-wide
      (`unified-trading-library@14301571`) — so `--apply` runs directly using the identical backup-copy →
      `record_captured()` → verify → delete recipe as the already-completed `fixtures_schedule` fold, with an explicit
      backup snapshot under `sports_reference/_purge_backups/` as the safety net (this bucket has no soft-delete).
      **Done when**: all 21 canonical objects exist and verify (size+crc32c parity vs. backup), all 21 raw-id
      (`league=169`/`league=235`) originals for `entity IN (fixtures, fixtures_outcomes)` are gone, 21 backup snapshots
      exist under `_purge_backups/`, and the manifest carries 21 `captured` rows for the canonical
      `(date, entity, league)` keys — independently verified via a fresh GCS listing, not just the script's own internal
      checks. Source: `sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24`. **DONE 2026-07-26T01:54Z
      — `--apply` executed (operator-authorized in-session; the plan's own `[OPERATOR]` justification only covered
      skipping a consolidator-cron pause, not the delete-safety codex's independent prod-bucket-delete hard stop —
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1 — so this required an explicit same-turn
      operator authorization naming that specific stop, obtained before `--apply` ran).** Fresh dry-run re-verify
      immediately prior to `--apply` reconfirmed 21/21 sources present, 21/21 canonical targets absent, 0 aborts.
      `--apply` output: `FOLD COMPLETE — 21/21 shard(s) copied+recorded+deleted, 0 remaining raw-id     objects.`
      **Independent fresh-listing verification (not the script's own internal checks)**: 21/21 canonical objects
      present; 21/21 raw-id (`league=169`/`league=235`) originals confirmed gone; 21/21 backup snapshots under
      `sports_reference/_purge_backups/2026_07_24_league_fold_fixtures_siblings/` present with size+crc32c parity vs.
      the canonical objects; the per-VM manifest shard (`_index/per_vm/league-fold-fixtures-siblings-20260724.parquet`)
      carries exactly 21 rows, all `capture_status=captured`, keyed to the canonical `(date, data_type, league_id)`
      triples.
