---
doc_type: issue
title:
  pipeline_e2e_check.py's batch-leg VM name collides across concurrent same-asset_group shard launches — corrupts
  results silently
summary:
  "Found 2026-07-12 while re-verifying 4 PREDICTION/TRADFI shards from the 2026-07-09 452-shard sweep's todo-25 triage.
  `market-tick-data-service/scripts/pipeline_e2e_check.py`'s `_vm_name(shard, run_ts)` builds the batch-leg VM name as
  `mtds-backfill-{asset_group}-pipelinecheck-{run_ts}`, where `run_ts` is second-granularity
  (`datetime.now(UTC).strftime('%Y%m%d-%H%M%S')`) and NEITHER venue NOR data_type is part of the name. Two shards of the
  SAME asset_group launched within the same UTC second collide on VM name — the second launcher call sees 'already
  exists', silently treats it as its own successful launch, and both checker processes then poll/verify against the SAME
  single VM. Reproduced twice independently within minutes (POLYMARKET book_snapshot_5 vs trades; KRX trades vs
  corporate_action_confirmed) while running 4 shards with only a few seconds' stagger. Confirmed via the KRX case's real
  run.log: the VM launched by the 'trades' request actually shows `data_type=ohlcv_24h` writes (unrelated to either
  colliding shard's OWN bug, a separate already-fixed issue) — proving BOTH checker processes were reading one VM's one
  real execution, not two independent ones. This is a genuine result-corruption risk for ANY concurrent same-asset_group
  sweep run (the actual 2026-07-09 452-shard sweep ran at concurrency=20, and multiple SIBLING agents were independently
  running concurrent `pipeline_e2e_check.py` invocations against this exact file/tool during this same session — cross-
  agent collisions are equally possible, not just within one process's own concurrency)."
status: open
nature: notes
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data, meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [pipeline_e2e_check, smoke-test, vm-launcher, vm-naming, concurrency, data-correctness, tooling-bug]
related: [../data_pipeline_e2e_check_2026_07_10.md, /codex/05-infrastructure/vm-launcher-runbook.md]
created: 2026-07-12
parent_epic: infrastructure_master
priority: P2
source: [pipeline_e2e_check todo-25 triage, real concurrent-launch reproduction, 2026-07-12]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# pipeline_e2e_check.py batch-leg VM name collision under concurrency

## Context

Investigating 4 shards flagged in `data_pipeline_e2e_check_2026_07_10.md` todo 25 (PREDICTION/KALSHI+POLYMARKET
book_snapshot_5/trades, TRADFI/FX+KRX). Launched several force-leg re-checks in parallel (a few seconds apart) to get
fresh, real VM evidence. Two independent pairs collided on VM name.

## Root cause

`scripts/pipeline_e2e_check.py`:

```python
def _run_ts() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _vm_name(shard: MtdsShardSpec, run_ts: str) -> str:
    return f"mtds-backfill-{shard.asset_group.lower()}-pipelinecheck-{run_ts}"
```

`run_ts` is generated fresh per `_run_batch_leg()` call, but at second granularity, and the name has NO venue or
data_type component — only `asset_group` + timestamp. Any two shards of the same asset_group whose `_run_batch_leg()`
calls land in the same UTC second produce byte-identical VM names.

## Evidence — 2 independent real collisions, same session

1. **POLYMARKET book_snapshot_5 vs POLYMARKET trades** (launched ~concurrently): both processes' `launch_vm_and_wait`
   log lines show the identical vm-name `mtds-backfill-prediction-pipelinecheck-20260712-095709`. One launcher call
   exits 0 (real create); the other exits 1 with
   `launcher exited 1 but the VM already exists — treating as launched (client-side report was stale/flaky, not retrying)`
   — a message designed for the transient-retry case (todo 23's fix), not a genuine cross-shard collision, so it
   silently mis-attributes.
2. **KRX trades vs KRX corporate_action_confirmed** (launched ~concurrently): same pattern, both collide on
   `mtds-backfill-tradfi-pipelinecheck-20260712-095739`. Confirmed via the real `run.log` for that VM: it wrote
   `data_type=ohlcv_24h` (a SEPARATE, already-fixed KRX adapter bug — see the sibling fix in this same commit) — the
   point here is that BOTH the `trades` and `corporate_action_confirmed` checker processes would have read this ONE VM's
   ONE execution and reported on it as if it were their own independent shard's result.

## Why this matters beyond this session

The actual 2026-07-09 452-shard sweep (`data_pipeline_e2e_check_2026_07_10.md`, `FINAL_REPORT.md`) ran the MTDS phase at
concurrency=20 per asset_group category. At that concurrency, multiple same-asset_group shards launching within the same
UTC second is a real, non-negligible probability (birthday-paradox effect), not a corner case only this session's
tighter-than-usual stagger produced. Additionally, **multiple sibling agents were independently running concurrent
`pipeline_e2e_check.py` invocations against different venues during this exact session** (observed via `ps aux`:
simultaneous processes for DERIBIT-COMBO, OKX-SPOT, BYBIT-SPOT, BITFINEX-SPOT, COINBASE-CDE, CBOE, NYSE, several DeFi
venues, all launched from separate agent sessions) — cross-AGENT collisions on the same VM-name scheme are equally
possible, not just within one process's own internal concurrency.

The practical effect: a shard whose launch collided silently reads and reports on a DIFFERENT shard's VM execution — its
own real capture attempt never happens, and its checker result (pass/fail/reason) reflects the colliding sibling's run
instead. This could silently corrupt an unknown fraction of the todo-25 residual "genuine, undocumented failures"
already logged as findings — any of them could actually be a collision artifact rather than the shard's own true result.

## Not fixed here

This session's own scope was the 4 named PREDICTION/TRADFI shards, not a general tooling audit — and
`scripts/pipeline_e2e_check.py` is under continuous, heavy concurrent editing by multiple sibling agents this same
session (observed via `git diff`/mtime — a different, unrelated in-flight fix, `_CHAIN_UNDERLYING_FALLBACK`, appeared
mid-session), so a further structural change here (adding venue/data_type into the VM name, which also needs to stay
under GCE's 63-char instance-name limit — several current names are already 50-54 chars, leaving little room) was
deliberately not attempted in this pass to avoid colliding with that live work.

## Suggested fix direction (not implemented)

Add a short collision-resistant component (e.g. an 8-hex slug of `hash(venue, data_type)`, or venue/data_type
truncated + a random 4-char suffix) to `_vm_name()`, keeping the total under 63 chars. Verify against
`vm_zombie_watchdog.py`'s `VM_PREFIX_TO_BUCKET` prefix-match (`name~"^mtds-backfill-{category}-"`) — a suffix change is
safe there since matching is prefix-only, not confirmed against any other exact-name assumption.

## Todos

- [ ] [CODE] P2. Add a collision-resistant component (e.g. an 8-hex slug of `hash(venue, data_type)`) to
      `pipeline_e2e_check.py::_vm_name()`, keeping the total name under GCE's 63-char instance-name limit. Verify the
      change against `vm_zombie_watchdog.py`'s `VM_PREFIX_TO_BUCKET` prefix-match (prefix-only, so a suffix addition is
      safe) and add a regression test asserting two same-asset_group, same-second shard launches produce distinct VM
      names. Definition-of-done: the test passes and a real concurrent re-launch of the two documented collision pairs
      (POLYMARKET book_snapshot_5/trades, KRX trades/corporate_action_confirmed) produces two distinct VMs.

## Progress log

- 2026-07-12: Filed after reproducing twice independently while re-verifying `data_pipeline_e2e_check_2026_07_10.md`
  todo-25 PREDICTION/TRADFI shards. No fix attempted — diagnosis handoff only, per the "file don't force" rule for a
  finding that touches actively-edited shared tooling.
