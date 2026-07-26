---
doc_type: issue
title: cf_manifest_audit._read_index() returned an inconsistent return shape mid-session (tuple vs DataFrame)
summary: >-
  During the tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md P2 todo, a direct
  `unified_trading_library.cf_manifest_audit._read_index()` call against `market-data-tick-tradfi-prd-*` returned a
  `(9-column DataFrame, frozenset)` tuple instead of the full-column single DataFrame the SAME function returned
  successfully earlier in the same session against a different bucket (cefi's instruments-store). The function's own
  type signature declares `-> pd.DataFrame | None`, never a tuple. Not diagnosed further live (the local disk was
  independently failing with ENOSPC at the same time, so root-causing was not safe/possible in that window) — filed so
  the discrepancy is tracked rather than lost as chat-only prose.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library]
scope: [engineer]
tags: [cf-manifest-audit, utl, bug, data-audit-tooling]
related: [/plans/active/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md]
created: 2026-07-26
parent_epic: infrastructure_master
priority: P2
source: [tradfi_mdps_build_continuous_mismatches_2_and_4_still_open-010, slot 6, 2026-07-26]
assigned_vm: planning
resolved_by: slot-6, 2026-07-26 — confirmed intentional (unified-trading-library@6ce1ddb6), not a bug
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
locked_since:
---

> **🟢 RESOLVED 2026-07-26** — confirmed intentional (unified-trading-library@6ce1ddb6, column-prune + pyarrow-backed
> read fix), not a bug. Session observed a shared module's before/after state across a real intervening commit.

# cf_manifest_audit._read_index() inconsistent return shape

## What I found

Two calls to `unified_trading_library.cf_manifest_audit._read_index()` in the SAME session, same `.venv`, returned
different shapes:

- Against `instruments-store-cefi-prd-central-element-323112` (earlier in the session): a plain `pd.DataFrame`, 39
  columns, as the function's own type hint (`-> pd.DataFrame | None`) declares.
- Against `market-data-tick-tradfi-prd-central-element-323112` (later): a 2-tuple `(df, frozenset)`, where `df` had only
  9 columns (`available_at`, `capture_status`, `data_type`, `date`, `error_reason`, `pipeline_mode`, `schema_version`,
  `source`, `venue`) — missing `instrument_type`/`underlying`/`asset_group`/etc entirely.

The current source of `_read_index` (read live during this session) is a simple `return pd.read_parquet(dst)` — it does
not construct a tuple anywhere. This mismatch was NOT diagnosed further live because the local session's disk (`/home`)
was independently failing with ENOSPC (a separate, already-tracked fleet incident, `BLK-37401b23`-class) at the same
time, making further investigation unsafe/unreliable in that window.

## Why it matters

`cf_manifest_audit.py` is the daily CF-1…CF-14 cross-AG data-state audit (Cloud Run Job `cf-manifest-audit`, alert-on-
RED) — if this inconsistency is real (not just a local venv/bytecode artifact), it could mean the daily scheduled audit
itself is silently reading a truncated/wrong-shape manifest for at least the tradfi market-data-tick bucket, which would
make its CF-1/CF-3/CF-4/CF-8/etc verdicts wrong for that bucket without any visible failure.

## Recommended decision

- [x] ✅ [SCRIPT] P2. DONE 2026-07-26 (slot 6) — **NOT A BUG, confirmed intentional.**
      `python -c "import     unified_trading_library.cf_manifest_audit as m; print(m.__file__)"` confirmed the `.venv`
      is a live-source editable install (not a stale wheel — that hypothesis is ruled out). The live source's current
      signature IS `_read_index(...) -> tuple[pd.DataFrame, frozenset[str]] | None` (column-pruned df + full-columns
      frozenset), NOT the plain-`DataFrame` signature this doc's "What I found" observed earlier in the same session.
      `git log` pinpoints the exact change: `unified-trading-library@6ce1ddb6` ("fix(cf-manifest-audit): column-prune +
      pyarrow-backed read to stop the daily OOM", slot-10, `2026-07-26T21:07:41Z`) — a legitimate, intentional,
      well-justified fix (stopping a real daily-OOM bug in the scheduled Cloud Run Job) that quickmerge-landed to
      `live-defi-rollout` BETWEEN this doc's two `_read_index()` calls (cefi call was ~19:33Z, before the fix; tradfi
      call was ~22:34Z+, after). The "inconsistency" was this session observing a shared, continuously-shipping module's
      before/after state across a real intervening commit — not a defect. No fix needed; any caller written against the
      OLD single-DataFrame signature (as this doc's own diagnostic scripts were) should be updated to unpack the tuple,
      which the tradfi_mdps doc's own re-measurement code already did once this was discovered live. Repo:
      unified-trading-library (read-only diagnosis).
