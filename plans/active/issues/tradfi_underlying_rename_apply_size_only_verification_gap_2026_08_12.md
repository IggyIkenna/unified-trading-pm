---
doc_type: issue
title: "Short-code underlying rename --apply withheld — _apply_one compares destination SIZE only, not content"
summary: >-
  The `tradfi-underlying-rename` canonical-migration VM launcher (deployment-service@b7a79165c3) and its underlying
  script (`migrate_tradfi_underlying_display_names_2026_08.py`) are shipped and dry-run-verified (166,995 objects
  streamed, 32,417 in-scope renames — exact match across two independent runs). `--apply`/`full` mode was deliberately
  NOT run: reading `_apply_one` in full found that when the display-name destination object already exists (a real,
  common case in this corpus per tradfi_canonical_path_migration_design_2026_07_19.md — short-code and display-name
  forms already coexist for many futures_chain/combo cells), the function decides whether to delete the short-code
  source by comparing file SIZE ONLY, never content. Two same-size, different-content files would pass this check and
  the source would be deleted, a real (if narrow) data-loss risk.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, data-correctness, delete-safety, underlying-rename]
related:
  [
    /plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
parent_epic: tradfi_master
source: "/backfill-monitor VM-launch + apply attempt, 2026-08-12 interactive session"
assigned_vm: NA
created: 2026-08-12
resolved_by:
locked_by:
locked_since:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# Short-code underlying rename --apply withheld — size-only verification gap

## What's ready

- `deployment-service@b7a79165c3` — `tradfi-underlying-rename` canonical-migration launcher category, shipped.
- Dry-run VM `canonical-migration-tradfi-underlying-rename-20260812-104822` completed, exit_code=0: **166,995 objects
  streamed, 32,417 in-scope short-code→display-name renames** — exact match to a prior independent local dry-run this
  same session, confirming the enumeration is stable and correct.

## What's blocked and why

`_apply_one` in `migrate_tradfi_underlying_display_names_2026_08.py`, on finding the display-name destination object
ALREADY exists (a real, documented, common case in this corpus), currently compares only the source and destination
object SIZES before deleting the source. This is the exact class of check the delete-safety protocol's Part 2 (content
verification) exists to prevent skipping — two objects of identical size but different content would pass and the source
would be destroyed with no real content-equivalence proof.

## Todos

- [ ] [SCRIPT] P1. Harden `_apply_one`'s destination-exists branch to do a real content/byte comparison (not size only)
      before deleting the source — mirror the compound-key content-comparison pattern already proven earlier this
      session for a similar duplicate-verification task (sort/compare on a stable row key, not just a coarse proxy like
      size or row count). Repo: market-tick-data-service.
- [ ] [OPERATOR] P2. Once hardened, re-run the dry-run for a fresh count (the corpus may have drifted slightly since
      2026-08-12), then decide whether to launch `full` mode — this remains a real prod-bucket delete, gated per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`.
