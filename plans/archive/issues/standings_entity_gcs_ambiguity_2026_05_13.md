---
title: "Sports `entity=standings/` GCS directory — SFI vs api_football provenance ambiguity"
created: 2026-05-13
resolved: 2026-05-13
author: slot-4-ikenna
source:
  - expected_unattempted_propagation_chain_2026_05_12
  - manifest_migration_master_2026_05_07
severity: P2
status: RESOLVED — entity=standings/ is api_football, NOT SFI; no GCS action needed
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## ✅ RESOLUTION 2026-05-13 (slot 4 — same session)

Investigated by reading
`gs://instruments-store-sports-central-element-323112/sports_reference/by_date/day=2024-01-01/entity=standings/standings.parquet`.

**Result: `entity=standings/` is `api_football` STANDINGS, NOT `SFI_STANDINGS`.**

Evidence:

- **Logo URLs**: `https://media.api-sports.io/football/teams/...` (api-sports.io is api_football's CDN).
- **Schema columns**: `rank` / `team` / `points` / `goalsDiff` / `group` / `form` / `status` / `description` / `all` /
  `home` / `away` / `update` / `league_id` / `data_available_at` — classic api_football `/leagues/standings` response.
- **League IDs**: `league_id=39` (Premier League per api_football's mapping).
- **Team objects**: `{'id': 42, 'name': 'Arsenal', 'logo': '...'}` — api_football team-ID universe.

**Conclusion: NO GCS DELETION NEEDED.**

The 42 SFI_STANDINGS manifest rows that the migration script flipped on 2026-05-13 were rows that WRITE-TIME logic
created (probably during the pre-2026-04-24 era when SFI_STANDINGS was a thing) but the **on-disk parquets at
`entity=standings/` are populated by api_football's standings endpoint** — a legitimate, currently-active data source.
Deleting these would have lost real data.

The manifest is now honest (`empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` for the 42 SFI_STANDINGS rows). The
api_football standings parquets remain intact and continue serving downstream consumers.

**Cross-side ping (Harsh sports plane)**: not needed — the resolution is self-contained. Just noting the finding here.

---

## ORIGINAL FINDING (preserved for audit)

## What I found

During slot 4 retired-sports-data-type cleanup 2026-05-13 (migrate_sports_retired_types VM
`migrate-sports-retired-20260513-160205` flipped 88,779 manifest rows to
`empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE`), I needed to delete the on-disk parquets backing the retired manifest
rows. Per manifest_migration_master § C.1, this is a separate operator-confirmed step preserving rollback path.

**Two of the three retired data_types map unambiguously to GCS entity directories**:

| Manifest `data_type`    | GCS entity directory                                                                               | Status             |
| ----------------------- | -------------------------------------------------------------------------------------------------- | ------------------ |
| `TRANSFERMARKT_LEAGUES` | `gs://instruments-store-sports-{pid}/sports_reference/by_date/day=*/entity=transfermarkt_leagues/` | ✅ safe to delete  |
| `SFI_LEAGUES`           | `gs://instruments-store-sports-{pid}/sports_reference/by_date/day=*/entity=sfi_leagues/`           | ✅ safe to delete  |
| `SFI_STANDINGS`         | `entity=standings/` (ambiguous — see below)                                                        | 🟡 **investigate** |

The third — `SFI_STANDINGS` — has an **ambiguous GCS provenance**. The on-disk directory is named `entity=standings/`,
not `entity=sfi_standings/`. There is ALSO a top-level `gs://instruments-store-sports-{pid}/sports_reference/standings/`
directory (alongside `fixtures/`, `mappings/`, `venues/`, etc.) which may be a separate api_football-sourced standings
collection, NOT SFI-sourced.

I did NOT delete the `entity=standings/` parquets to avoid the risk of clobbering api_football standings data (or any
other source that may write into `entity=standings/`). Only ~42 manifest rows were flipped for SFI_STANDINGS, so the
cost of deferring is low; the cost of an erroneous delete (losing api_football historical standings) is high.

## Why it matters

- **Per CLAUDE.md SSOT** the venue/source axis MUST be unambiguous (`entity=` directory should encode the source).
  Today's `entity=standings/` ambiguity is a write-side foot-gun: two different sources writing to the same on-disk path
  makes downstream readers unable to distinguish them.
- **Manifest reconciliation is now blocked from going fully clean for SFI_STANDINGS** — the 42 manifest rows are flipped
  to `empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE` (✅) but the on-disk parquets remain (and may or may not have
  legitimate api_football content alongside).
- **The 2026-05-05 retirement of SFI_LEAGUES/TRANSFERMARKT_LEAGUES was clean** because each had its own entity
  directory. SFI_STANDINGS (retired 2026-04-24) was NOT clean — entity naming drift was introduced earlier and never
  reconciled. This is the source of the ambiguity.

## Recommended decision

Investigation is the gating step before any GCS rm. Suggested investigation steps for the next slot to pick this up:

1. **Schema sniff**: read a sample of
   `gs://...sports_reference/by_date/day=2024-01-01/entity=standings/standings.parquet` and check for a `source` column
   (or columns that strongly indicate SFI vs api_football provenance, e.g. `competition_id` shape, `league_id`
   namespace, `season` formatting).
2. **Cross-reference manifest**: query the manifest for ALL rows with `data_type` matching STANDINGS or standings-like,
   and check what `venue` / `source` field is set to. (The 42 SFI_STANDINGS rows already flipped; check if there are
   other captured rows that point at the same `entity=standings/` path.)
3. **Cross-reference write-path**: grep `instruments-service` orchestrator + adapters for `entity=standings` /
   `entity_path` / `standings/` writes. Identify every code path that produces parquets at this path.
4. **Decision tree**:
   - If `entity=standings/` is **exclusively** SFI data → safe to `gcloud storage rm -r` it after follow-up cross-side
     ping to Harsh (sports data owner).
   - If `entity=standings/` is **mixed** SFI + api_football → write a per-row filter script (read parquet → drop SFI
     rows → write back) OR migrate api_football STANDINGS to `entity=api_football_standings/` first, then delete
     `entity=standings/`.
   - If `entity=standings/` is **api_football only** (SFI_STANDINGS rows wrote elsewhere) → the entity directory is
     legitimate; leave it alone. The 42 manifest rows are already honest
     (`empty_confirmed/EXPECTED_DEPRECATED_DATA_TYPE`); no GCS action needed.

**Severity P2** because:

- 42 manifest rows is a tiny tail; not blocking Gate 3 phantom-count target
- Manifest is already in honest state (flipped 2026-05-13 by slot 4)
- Risk of acting without investigation > value of acting now

**Suggested owner**: sports data plane owner (Harsh slot 2 or 5) — they have the most context on SFI vs api_football
collection patterns.

## Related context

- Migration VM that uncovered the ambiguity: `migrate-sports-retired-20260513-160205`
  (`gs://deployment-scripts-central-element-323112/vm-logs/migrate-sports-retired-20260513-160205/run.log`)
- Migration script: `instruments-service/scripts/migrate_sports_retired_types_2026_05_13.py`
- Plan reference: `expected_unattempted_propagation_chain_2026_05_12.md` § "BIG FINDING 2026-05-13 slot 4"
- Parent plan: `manifest_migration_master_2026_05_07.md` § C.1 LEAGUES kill (pattern this followed)
