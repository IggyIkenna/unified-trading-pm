---
doc_type: issue
title: "market-tick-data-service quality-gates.sh RED — migrate_sports_canonical_v9.py exceeds 900-line file-size gate"
summary:
  "Discovered while shipping the cryptography GHSA-537c-gmf6-5ccf floor bump (fleet_hygiene_crypto_ghsa_mtds_baseline
  plan, todo 1): market-tick-data-service's quality-gates.sh fails STEP 'File size OK' —
  market_tick_data_service/scripts/migrate_sports_canonical_v9.py is 934 lines (limit 900). Verified pre-existing
  (already 934 lines at HEAD~1, before the crypto-bump commit — introduced by 13c53dfa feat(mtds): add explicit
  legacy-vs-canonical reconciliation to MDPS raw_tick_data migration). No blank-line or comment trimming is available
  (already PEP8-clean, no runs >=3 blank lines) — the fix needs a genuine split (extract some of the pure
  canonicalization helpers, e.g. _canon_mdps_raw_prd/_canon_mdps_candle/
  _canon_instr_reference/_canon_instr_bare_day/_canon_instr_hyphen/_dispatch_canon_rel, into a sibling module), which is
  out of scope for a dependency-hygiene task and risks the migration script's correctness without deeper context."
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [quality-gates, file-size, repo-blocker, mtds]
related: [fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13.md]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P2
source: fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13 todo 1 (cryptography floor bump)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend-engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: advance-code
depends_on: []
---

## What I found

`market-tick-data-service`'s `quality-gates.sh` fails the file-size gate:

```
Files exceed 900 lines:
  ./market_tick_data_service/scripts/migrate_sports_canonical_v9.py: 934 L
```

Verified pre-existing via `git show HEAD~1:market_tick_data_service/scripts/migrate_sports_canonical_v9.py | wc -l` →
934 lines, i.e. already over the limit BEFORE my cryptography-bump commit (which only touches `pyproject.toml` +
`uv.lock`). Introduced by
`13c53dfa feat(mtds): add explicit legacy-vs-canonical reconciliation to MDPS raw_tick_data migration`. No mechanical
trim available: blank-line/comment ratio is normal (163 blank / 90 comment / 681 code lines; longest consecutive-blank
run is 2, already PEP8-clean).

## Why it matters

Blocks `market-tick-data-service`'s `quality-gates.sh`, and by extension any shipping through the mandatory
Pass-1(QG)→Pass-2(quickmerge) flow for that repo, until resolved. My cryptography-floor-bump commit
(`fix(deps): bump cryptography floor off GHSA-537c-gmf6-5ccf`) is sitting locally committed but unshipped in this repo,
waiting on this gate.

## Recommended decision

Extract a subset of the pure canonicalization helpers (`_canon_mdps_raw_prd`, `_canon_mdps_candle`,
`_canon_instr_reference`, `_canon_instr_bare_day`, `_canon_instr_hyphen`, `_dispatch_canon_rel` — lines ~220-462, no
external state, clear input/output contracts) into a sibling module (e.g.
`market_tick_data_service/scripts/_migrate_sports_canonical_v9_paths.py`), imported back into the main script. Pure
code-move, no logic changes; run the script's existing test coverage after the move to confirm behaviour-identical.
Declared as repo-blocker `RB-<see orchestrator>` so my cryptography-bump commit ships automatically once this clears.

## Todos

- [ ] [CODE] P2. Split `migrate_sports_canonical_v9.py` under 900 lines (extract pure canonicalization helpers to a
      sibling module, pure code-move, verify existing tests still pass), confirm `quality-gates.sh` green, ship via
      `quickmerge --agent --files '<paths>'`. (repo: market-tick-data-service)

## Progress Log

- **2026-07-13 (slot-6, sonnet/high)** — Found while shipping the fleet-wide cryptography GHSA floor bump. Verified
  pre-existing via a `HEAD~1` line-count check. Declared repo-blocker for `market-tick-data-service`.
