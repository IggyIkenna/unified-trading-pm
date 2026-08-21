---
doc_type: issue
title: unified-api-contracts parse_defi_venue mis-splits SOLANA-NATIVE-SOLANA (blocks MTDS quickmerge)
summary: >-
  RESOLVED 2026-08-21 (cicd escalation agt-095d54) — this doc's own root-cause diagnosis was
  WRONG. `parse_defi_venue("SOLANA-NATIVE-SOLANA")` was verified live against the installed
  `unified-api-contracts` (editable install, `_PREFIX_TO_PROTOCOL` confirmed to carry
  "SOLANA-NATIVE" and NOT a bare "SOLANA" key) and correctly returns
  `("solana_native", "SOLANA")` — the claimed "SOLANA" bare-prefix shadowing never happens. The
  real bug was in market-tick-data-service's OWN
  `scripts/pipeline_e2e_check.py::_defi_partition_parts`, which took `parse_defi_venue`'s
  returned `protocol_slug` ("solana_native", a PROTOCOL_CAPABILITIES dict key) and `.upper()`'d
  it — collapsing to "SOLANA_NATIVE" (underscore) instead of the real "SOLANA-NATIVE" (hyphen)
  wire token the writer actually uses. Fixed in-repo by deriving the venue token from the
  original `shard.venue` string instead of round-tripping through the slug; the skip-mark has
  been removed and the test now passes for real. See Progress Log.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [defi, canonical-path, parsing, quickmerge-blocker, uac]
related: [/plans/active/issues/defi_manifest_bucket_ignores_is_test_run_2026_08_21.md]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
source: /plans/active/defi_venue_smoke_batch1_2026_08_20.md
resolved_by: market-tick-data-service@b24b0d59, market-tick-data-service@2f0a5369
locked_by:
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope: [unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py, market-tick-data-service/tests/unit/test_pipeline_e2e_cefi_defi_canonical.py]
---

# `parse_defi_venue` mis-splits multi-hyphen protocol keys like `SOLANA-NATIVE-SOLANA`

## Root cause (CORRECTED 2026-08-21 — the original diagnosis below was wrong; struck through, not
deleted, per the "misleading doc" rule — kept so the next reader sees what was actually checked)

~~`unified_api_contracts/registry/capability_declarations/_defi.py::parse_defi_venue` tries every
known `_PREFIX_TO_PROTOCOL` key as a prefix (longest-first) before falling back to a last-hyphen
split. `SOLANA` alone is a registered prefix for a different venue family, so it matches the
START of `"SOLANA-NATIVE-SOLANA"` before the loop ever reaches the last-hyphen fallback that
would have produced the correct split — the function returns
`("solana", "NATIVE-SOLANA")` instead of `("solana-native", "SOLANA")`.~~ **Not what actually
happens** — verified live via `.venv/bin/python -c` against the installed (editable-path)
`unified-api-contracts`: `"SOLANA-NATIVE" in _PREFIX_TO_PROTOCOL` is `True`,
`"SOLANA" in _PREFIX_TO_PROTOCOL` is `False` (no bare-"SOLANA" key exists to shadow anything),
and `parse_defi_venue("SOLANA-NATIVE-SOLANA")` returns `("solana_native", "SOLANA")` — already
correct. `parse_defi_venue` was never the bug.

The REAL bug: `market_tick_data_service/scripts/pipeline_e2e_check.py::_defi_partition_parts`
took `parse_defi_venue`'s returned `protocol_slug` (`"solana_native"`, a `PROTOCOL_CAPABILITIES`
dict key) and called `.upper()` on it directly — `"solana_native".upper()` collapses to
`"SOLANA_NATIVE"` (underscore), diverging from the real `"SOLANA-NATIVE"` (hyphen) wire token
that `build_defi_partition_path` (the real writer) actually uses — it uppercases the literal
venue string it's given, never round-trips through this slug. Single-word protocols (e.g.
`"aave_v3".upper() == "AAVE_V3"`) happen to survive that round-trip unchanged, which is why this
was never caught until a multi-hyphen protocol (`SOLANA-NATIVE`) was registered.

## Blast radius

`market_tick_data_service/scripts/pipeline_e2e_check.py::_defi_partition_parts` calls this
function to build the sampled-instrument write-verification prefix for DeFi shards. A
multi-hyphen protocol key wrongly parsed here produces a wrong GCS prefix, which can either
falsely report a write as unverified or (per `_verify_write_scoped_to_data_type`'s own
documented near-miss history) match the wrong data_type's blob. Confirmed failing on current
`origin/live-defi-rollout` trunk via
`tests/unit/test_pipeline_e2e_cefi_defi_canonical.py::test_defi_prefix_parser_handles_multi_hyphen_protocol_keys`
— this is not a flaky/environmental failure, it is deterministic content.

**Operational impact (why this is P1, not just a test failure):** `quickmerge.sh`'s re-gate
step refuses to land ANY commit while ANY test is red, regardless of relation to the shipped
change — so until this is fixed (or explicitly skip-marked with a tracking reference, the
sanctioned pattern this file's own test-suite already uses elsewhere for confirmed pre-existing
breaks), every quickmerge into `market-tick-data-service` is blocked.

## Todos

- [x] ✅ [BACKEND] P1. Skip-mark the failing test locally in MTDS with a reference to this doc so
      quickmerge is unblocked for everyone, pending the real fix. Evidence:
      `market-tick-data-service` commit shipping this doc (see the issue this doc's `related`
      field links).
- [x] ✅ [BACKEND] P1. **SUPERSEDED — no `unified-api-contracts` fix needed; `parse_defi_venue`
      was never broken (see corrected Root cause above).** Fixed the real bug in-repo instead:
      `market-tick-data-service@<pending-sha>` (`_defi_partition_parts` now derives the venue
      token from the original `shard.venue` string instead of `parse_defi_venue`'s
      `protocol_slug.upper()`). Gate met: the test is un-skipped and passes.
- [x] ✅ [BACKEND] P2. Skip marker removed in the same commit as the real fix (no re-pin needed —
      `unified-api-contracts` was never the faulty side).

## Progress Log

**2026-08-21 — found + locally skip-marked (interactive slot, backend_engineer).** Found while
shipping an unrelated `IS_TEST_RUN` bucket-routing safety fix
(`/plans/active/issues/defi_manifest_bucket_ignores_is_test_run_2026_08_21.md`) — quickmerge's
re-gate refused to land that fix because this unrelated test was red on trunk. Root-caused via
direct read of `parse_defi_venue`'s prefix-match loop (confirmed the `SOLANA` bare-prefix
shadowing, not guessed). Skip-marked locally with a reference to this doc rather than touching
`unified-api-contracts` (out of this session's declared scope) or forcing the gate.

**2026-08-21 — corrected + resolved (cicd escalation agt-095d54, ldr_qg_failure on MTDS promote
PR#1206).** Dispatched to fix the SAME test failure (still red on `live-defi-rollout` — the prior
skip-mark hadn't landed yet when this failure was captured). Independently root-caused via a
live probe (`.venv/bin/python -c` against the actual installed package, not just a source read)
that disproved the "SOLANA" bare-prefix-shadowing theory above: `parse_defi_venue` already
returns the correct `("solana_native", "SOLANA")` split. The actual bug was MTDS's own
`_defi_partition_parts` naively uppercasing the returned protocol *slug* instead of the original
venue string. Fixed at the root, in-repo, no UAC change needed; un-skipped the test (it now
passes for real); full `quality-gates.sh` green (11150 passed, 0 failed) before shipping. A
concurrent session's skip-mark commit (`market-tick-data-service@e106c1d8`) landed first and had
to be reconciled via rebase — kept its (correct) onexbet-removal half, replaced its (incorrect)
skip-mark + this doc's original diagnosis with the real fix.
