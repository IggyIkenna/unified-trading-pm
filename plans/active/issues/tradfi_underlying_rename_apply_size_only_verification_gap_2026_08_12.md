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
context_scope: [market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_underlying_display_names_2026_08.py, /codex/02-data/gcs-and-manifest-delete-safety-protocol.md]
---

# Short-code underlying rename --apply withheld — size-only verification gap

## What's ready

- `deployment-service@b7a79165c3` — `tradfi-underlying-rename` canonical-migration launcher category, shipped.
- Dry-run VM `canonical-migration-tradfi-underlying-rename-20260812-104822` completed, exit_code=0: **166,995 objects
  streamed, 32,417 in-scope short-code→display-name renames** — exact match to a prior independent local dry-run this
  same session, confirming the enumeration is stable and correct.

## What's blocked and why

> **RESOLVED 2026-08-15 — see Progress Log.** The size-only check described below was replaced with a real
> crc32c content compare in `market-tick-data-service@05062013`. Retained as historical context for the "Todos"
> section's provenance; do not read the paragraph below as the current code state.

`_apply_one` in `migrate_tradfi_underlying_display_names_2026_08.py`, on finding the display-name destination object
ALREADY exists (a real, documented, common case in this corpus), currently compares only the source and destination
object SIZES before deleting the source. This is the exact class of check the delete-safety protocol's Part 2 (content
verification) exists to prevent skipping — two objects of identical size but different content would pass and the source
would be destroyed with no real content-equivalence proof.

## Todos

- [x] ✅ [SCRIPT] P1. **EXTRACTED 2026-08-16 (na-eligibility-audit, tradfi tranche, dispatch agt-45ad7b) →
      `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch14_2026_08_16.md` todo 1.** Harden `_apply_one`'s
      destination-exists branch to do a real content/byte comparison (not size only) before deleting the source —
      mirror the compound-key content-comparison pattern already proven earlier this session for a similar
      duplicate-verification task (sort/compare on a stable row key, not just a coarse proxy like size or row count).
      Repo: market-tick-data-service. Bounded/deterministic, conflict-checked clean; dispatches through the batch, not
      this doc (stays NA for todo 2 below).
- [ ] [OPERATOR] P2. Once hardened, re-run the dry-run for a fresh count (the corpus may have drifted slightly since
      2026-08-12), then decide whether to launch `full` mode — this remains a real prod-bucket delete, gated per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`.

## Progress Log

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **RECLASSIFY, per-todo split.** Todo 1
  (bounded code fix) extracted to `tradfi_satellite_ao_dispatch_batch14_2026_08_16.md`; todo 2 (real prod-bucket-delete
  launch decision) stays genuinely operator-gated. Doc stays `assigned_vm: NA`.
- **2026-08-16 — batch14 dispatch found todo 1 already shipped a day before the audit extraction.**
  `market-tick-data-service@05062013` (2026-08-15 01:30 UTC, slot-14) already replaced the size-only check with a
  `crc32c` content compare (kept size-check only for the freshly-copied-by-us branch) + 2 unit tests, citing this same
  doc as its source. Flipped done in the batch plan citing that SHA; no new code shipped. The "What's blocked" section
  above is now stale-marked rather than deleted, since it's still useful provenance for why the check existed.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-17** (tradfi tranche, dispatch agt-d99b5c): **KEEP-NA, valid.** Sole open item
  (todo 2, the `full`-mode launch decision) is an explicit, self-cited real prod-bucket delete gated per
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — textbook human-only. `assigned_vm` unchanged.
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed. Sole open item (todo 2, the `full`-mode
  prod-bucket-delete launch decision) is an explicit, self-cited real delete gated per
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — human-only. `assigned_vm` unchanged.
