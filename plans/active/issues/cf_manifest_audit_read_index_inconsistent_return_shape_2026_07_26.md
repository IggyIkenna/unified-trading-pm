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
status: open
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
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
locked_since:
---

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

- [ ] [SCRIPT] P2. Reproduce `_read_index('market-data-tick-tradfi-prd-central-element-323112', ...)` in a clean `.venv`
      (fresh `uv sync`, not a possibly-stale long-lived one) and confirm whether the tuple-return repros. If it does,
      read `unified_trading_library/cf_manifest_audit.py`'s actual installed/imported source
      (`python -c "import     unified_trading_library.cf_manifest_audit as m; print(m.__file__)"`) to rule out a
      stale-package-vs-live-source mismatch (this workspace uses live-source dev installs; a `.venv` that lagged a
      mid-session `unified-trading-library` quickmerge could explain it). If NOT reproducible cleanly, close as a
      session-local artifact (unrelated to the Cloud Run Job's own venv). Repo: unified-trading-library. **Done when**:
      the tuple-return either reproduces with a root cause identified (and a fix follow-up filed), or is confirmed
      non-reproducible in a clean venv, recorded here either way.
