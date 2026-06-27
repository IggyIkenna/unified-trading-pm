---
doc_type: plan
title: instruments-service build_instrument_catalogue defi-pool dual-form tests FAIL on origin/LDR (pre-existing)
created: 2026-06-24
source:
  - tradfi_datasource_closeout_krx_yahoo_parity_2026_06_24.md
locked_by: live-defi-rollout
priority: P2
status: active
summary: "`instruments-service/tests/unit/scripts/test_build_instrument_catalogue.py` has **4 FAILING tests on the clean `origin/live-defi-rollout` tip** (verified by running them in a worktree off origin/LD..."
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

## What I found

`instruments-service/tests/unit/scripts/test_build_instrument_catalogue.py` has **4 FAILING tests on the clean
`origin/live-defi-rollout` tip** (verified by running them in a worktree off origin/LDR with NO local changes):

- `test_rollup_defi_pool_emits_dual_form_ids`
- `test_rollup_defi_pool_dual_form_round_trips_via_converter`
- `test_rollup_defi_pool_spelling_variants_collapse_to_one_open_lifecycle`
- `test_rollup_non_pool_row_has_blank_dual_form`

They are about the DeFi pool **dual-form instrument-id** rollup in `build_instrument_catalogue.py`. The main IS clone
currently has a CONCURRENT agent's WIP touching exactly this area (dirty `catalogue.py` + a DELETED
`scripts/reconcile_defi_pool_manifest_dual_form_2026_06_23.py` + its test) — so this is almost certainly a
mid-flight refactor of the dual-form rollup whose fix has not yet landed on LDR.

## Why it matters

The instruments-service QG (`--no-fix`) fails on these 4 tests, which **blocks the green sentinel for ANY
instruments-service change** (it blocked the KRX venue close-out ship — the KRX work itself is QG-clean: basedpyright +
ruff + all 54 databento-tardis tests + 52 venue/adapter tests pass). This is a data-pipeline-correctness concern for the
DeFi catalogue (the dual-form id is the canonical/legacy pool-id round-trip).

## Recommended decision

The CONCURRENT agent working the `reconcile_defi_pool_manifest_dual_form` / `catalogue.py` dual-form refactor should
land their fix (it owns this surface — do NOT have a second agent stomp it). Once their fix lands, these 4 tests go
green and the IS QG unblocks for everyone. The KRX venue close-out (`venue_core.py` + databento adapter
`_create_krx_equity_records` + the databento-tardis KRX mock) was committed/pushed to LDR via the dirty-deps carve-out
(IS clone was dirty with the foreign defi-pool WIP, so quickmerge was not usable) — KRX commit is clean + tested and
does NOT touch the defi-pool surface.
