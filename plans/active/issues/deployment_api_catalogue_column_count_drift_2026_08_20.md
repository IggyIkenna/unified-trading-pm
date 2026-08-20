---
doc_type: issue
title: deployment-api catalogue-schema test drifted from live INSTRUMENT_CATALOGUE contract (60+ cols expected, 41 actual)
summary: Pre-existing qg_red on deployment-api — instrument_catalogue drilldown test's column-count threshold no longer matches the live UAC contract.
status: open
created: 2026-08-20
author: slot-4-worker
assigned_vm: planning
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api, unified-api-contracts]
scope: [engineer]
related: [security_and_cross_cutting_master, cross_cutting_consolidated_closeout_2026_07_25]
parent_epic: security_and_cross_cutting_master
priority: P2
source: [deployment-api]
tags: [qg-red, pre-existing, schema-drift]
resolved_by: null
locked_by: null
---

## What I found

`deployment-api/tests/unit/test_data_status_drilldown.py::TestGetSchemaForShard::
test_instruments_service_legacy_v4_resolves_catalogue_contract` fails on a clean
`live-defi-rollout` tree (confirmed pre-existing — unrelated to any commit made in
this session; my two shipped commits (`7cbb97c` project_id kwarg fix,
`180888d` symbol_column test fix) do not touch schema-registry code).

Two distinct drifts surfaced:

1. **FIXED (180888d)**: the test asserted `symbol_column == "instrument_key"`.
   UAC's own `unified_api_contracts/internal/schemas/_instrument_catalogue_contract.py`
   (and its own test `test_instrument_catalogue_contract.py:159`) both assert
   `symbol_column == "instrument_id"` — the deployment-api test was stale. Fixed.

2. **STILL RED**: after fix (1), the same test now fails on
   `assert len(cols) > 50` — the live `INSTRUMENT_CATALOGUE` contract (derived from
   `INSTRUMENTS_PARQUET_SCHEMA` in UAC) currently resolves to only 41 columns, not
   60+. Either the UAC contract genuinely shrank (schema consolidation) and the
   deployment-api test's `> 50` threshold is stale, OR something upstream is
   dropping columns it shouldn't. Root cause not yet determined — needs someone
   with UAC schema-history context to confirm which side is correct.

## Why it matters

Blocks a green `quality-gates.sh` on deployment-api, which blocks ANY future
quickmerge ship from this repo (the commit-only-from-green-tree hard rule) until
resolved.

## Recommended decision

- [ ] [BACKEND] P2. Diagnose whether `INSTRUMENT_CATALOGUE`'s live column count
      (41) is intentional (UAC schema consolidation) or a regression, then either
      update `test_instruments_service_legacy_v4_resolves_catalogue_contract`'s
      `> 50` threshold to match the current correct count, or fix the UAC contract
      to restore the missing columns. (repo: deployment-api + unified-api-contracts)
