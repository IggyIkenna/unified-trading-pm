---
doc_type: issue
title: market-tick-data-service quality-gates.sh RED on live-defi-rollout — 2 pre-existing test failures
summary:
  A full quality-gates.sh run on live-defi-rollout HEAD (b7677e04) found 2 test failures, confirmed pre-existing
  (byte-identical failures reproduced on HEAD~1, before this session's own unrelated commit) — not caused by this
  session's work. Blocks any quickmerge --agent ship from this repo until fixed.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [qg-red, market-tick-data-service, ldr_qg_failure, test-failure]
related: []
created: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
drift_direction: worsening-slowly
source: [/plans/active/issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md]
resolved_by:
locked_by:
depends_on: []
assigned_role: cicd
---

# market-tick-data-service quality-gates.sh RED on live-defi-rollout

## What I found

While shipping an unrelated one-off script (`scripts/one_offs/quantify_solana_dex_pools_catalogue_gap_2026_08_02.py`,
`market-tick-data-service@b7677e04` — closes
`plans/active/issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md`'s last open todo), a
full `bash scripts/quality-gates.sh` run on `live-defi-rollout` HEAD failed with 2 test failures. Verified pre-existing
per the repo-blocker protocol (RULES.md § 4b): stashed my diff (a single new file, touches no production code), reran
just the 2 failing tests against HEAD~1 (`b5e91e4d`), and got byte-identical failures — confirming this is NOT caused by
this session's work.

1. **`tests/unit/test_collect_handler_schema.py::TestCollectHandlerCoversProtocolClass::test_protocol_class_ops_have_modules[yield]`**

   ```
   AssertionError: CLI operation 'collect-vault-share-price' (ProtocolClass.YIELD) has no entry in _CLI_OP_TO_MODULE
   ```

   Some commit registered a new `collect-vault-share-price` CLI operation under `ProtocolClass.YIELD` without adding its
   corresponding entry to `_CLI_OP_TO_MODULE` in `market_tick_data_service/cli/handlers` (exact module TBD by whoever
   fixes this — grep `_CLI_OP_TO_MODULE` + `collect-vault-share-price`).

2. **`tests/unit/test_pipeline_e2e_prediction_canonical.py::test_rule11_per_ag_shard_counts_byte_unchanged`**
   ```
   AssertionError: DEFI shard count drifted: 3434 != 2727
   ```
   A golden/snapshot-style test with a hardcoded expected DEFI shard count (2727) that has drifted to 3434 — likely a
   legitimate side-effect of recent DeFi venue/data_type additions (e.g. the Solana DEX protocols, the 8 EVM "other"
   protocols work landed the same day per
   `plans/active/issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md`) rather than a bug —
   needs a human/cicd judgment call on whether 3434 is the new correct expected count (update the golden constant) or
   whether some shard-spec generation path is now double-counting (real bug). Did not investigate further — out of scope
   for the data_engineering task this was found under (dex_pools catalogue quantification), and the "read BOTH sides,
   never blindly bump a golden value" cicd-role discipline applies here.

## Why it matters

Blocks `quickmerge --agent` for ANY commit on this repo until fixed (the `quality-gates.sh` sentinel requires a clean
full run). This session's own ship (the Solana quantify script + the parent issue doc's plan-flip) is stalled on it.

## Recommended decision

A `cicd` role should triage both failures on their merits (read the yield CLI-op registration commit for #1; determine
whether 3434 is a legitimate new golden count or a real over-count bug for #2), fix the wrong side, and get
`quality-gates.sh` back to EXIT 0.

## Todos

- [ ] [CICD] P1. Fix `test_protocol_class_ops_have_modules[yield]` — add the missing `_CLI_OP_TO_MODULE` entry for
      `collect-vault-share-price` (or fix whatever commit introduced the CLI op without registering it). (repo:
      market-tick-data-service)
- [ ] [CICD] P1. Triage `test_rule11_per_ag_shard_counts_byte_unchanged`'s DEFI drift (3434 vs golden 2727) — determine
      if this is a legitimate shard-count increase (update the golden constant with a one-line note citing the commit(s)
      that legitimately added the new shards) or a real shard-spec-generation bug (fix the generator). (repo:
      market-tick-data-service)

## Progress Log

- **2026-08-03 (slot 2, data_engineering/cicd)**: filed after confirming pre-existing via the repo-blocker verification
  protocol; declaring a repo-blocker so `RepoHealthWatcher` pages a cicd worker and my own stalled
  `defi_dex_pools_catalogue_undercoverage_vs_historical_capture-003` ship resumes the moment this goes green.
