---
doc_type: issue
title: tardis-concurrency-guard.sh name-pattern fallback over-counts non-Tardis tradfi-bf Databento OHLCV backfill VMs
summary: >-
  The guard's legacy name-pattern fallback `^(cefi|tradfi)-.*-(heavy|light)-` catches the `tradfi-bf-*-light-*`
  Databento OHLCV backfill VMs (launched by launch-tradfi-backfill-vm.sh, which serializes across the shared Databento
  account, NOT the Tardis IP), inflating the Tardis-concurrent-VM count from the true 1 to 4. Observed live
  2026-08-10T12:31Z while re-checking the N=1 slot for the DERIBIT futures_chain re-capture. The count is
  conservative-direction (over-blocks), so no cap breach risk, but it pollutes the fleet count every launcher's guard
  reads: a future legitimately-free Tardis slot could read as occupied while tradfi-bf VMs run, and it makes "how many
  Tardis VMs are running" questions unanswerable from the guard alone.
status: open
nature: issue
asset_group: [cefi, cross-cutting, tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tardis, vm-launcher, concurrency, name-pattern, guard, tradfi, databento]
related:
  [
    /plans/active/issues/tardis_concurrency_gate_hardening_2026_08_09.md,
    /plans/active/issues/cefi_deribit_futures_chain_canonical_write_path_exposure_2026_08_09.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
author: slot-19 (data_engineering)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  Re-check of cefi_deribit_futures_chain_canonical_write_path_exposure_2026_08_09.md todo 1's precondition via the
  canonical tardis-concurrency-guard.sh (slot 19, 2026-08-10).
---

# tardis-guard name-pattern fallback over-counts tradfi-bf Databento VMs

## What I found

While re-checking the N=1 Tardis slot for the DERIBIT futures_chain re-capture, the canonical guard
(`tardis_running_vm_count asia-northeast1-c central-element-323112`) returned **4** (rc=0), up from slot 8's 1 a day
earlier. Decomposing the union (name-pattern OR `VM_TARDIS_CONSUMER=1` metadata stamp):

| VM                                                 | name_match | stamped | real Tardis consumer?                         |
| -------------------------------------------------- | ---------- | ------- | --------------------------------------------- |
| `cefi-queue-heavy-binancefutu-x17-20260809-083733` | True       | True    | **Yes** — genuine Tardis (aggregate backfill) |
| `tradfi-bf-es-opt-light-2026-20260810-113302`      | True       | False   | **No** — Databento OHLCV backfill             |
| `tradfi-bf-vix-light-2020-20260810-131032`         | True       | False   | **No** — Databento OHLCV backfill             |
| `tradfi-bf-vix-light-2022-20260810-131116`         | True       | False   | **No** — Databento OHLCV backfill             |

The 3 `tradfi-bf-*-light-*` VMs are launched by `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh`, whose
header states it serializes the fleet "across the shared **Databento** account" (and the es-opt watcher
`scripts/vm/es-opt-backfill-watcher.sh` is likewise Databento-sourced). They carry no `VM_TARDIS_CONSUMER=1` stamp and
their launcher does NOT source `tardis-concurrency-guard.sh`. They are caught purely by the guard's legacy name-pattern
fallback `TARDIS_VM_NAME_PATTERN='^(cefi|tradfi)-.*-(heavy|light)-|^cefi-queue-|^mtds-backfill-cefi-'`.

## Why it matters

The guard is the fleet-wide SSOT for the Tardis N=1 cap (operator HARD RULE 2026-07-16 — N>1 storms the shared
academic-key IP with mutual 403s). Its count is read by every Tardis launcher's pre-flight. Two concrete harms:

1. **False "slot occupied"**: while any tradfi-bf-_-light-_ VM runs, the guard reads >1, so a genuinely-free Tardis slot
   would be refused — delaying legitimately gated work like the DERIBIT futures_chain re-capture (this issue's parent).
2. **Unanswerable fleet question**: "how many Tardis VMs are actually consuming the IP right now?" can no longer be
   answered from `tardis_running_vm_count` alone; the over-count must be manually decomposed every time.

Direction is safe (over-block, never over-launch) — no live cap breach. But the fleet-migration intent of the
name-pattern fallback (per the guard header, it exists to catch pre-rollout VMs not yet stamped) is defeated when
current-generation launchers produce name-colliding but non-Tardis VMs.

## Recommended decision

Fix at the root per the data-pipeline-correctness HARD RULE. Options, in order of preference:

1. **Narrow the fallback pattern** so it stops matching Databento OHLCV backfills, e.g. drop `tradfi-.*-(heavy|light)-`
   from the OR-alternation (TradFi Tardis consumers today are all stamped; confirm no legacy un-stamped tradfi Tardis VM
   is still possible) — or require a venue/data-type hint in the name that Tardis-tradfi sharded backfills carry and
   Databento ones don't.
2. **Make launch-tradfi-backfill-vm.sh / es-opt watcher stamp a negative** (e.g. `VM_TARDIS_CONSUMER=0`) so the union
   ignores them explicitly — lighter-touch than repainting the shared pattern.
3. Failing both, extend the guard to also read the `VM_TARDIS_CONSUMER=0` negative-stamp and treat name-match + negative
   stamp as non-consumer.

## Action items

- [ ] [DATA] P3. Fix the `tardis-concurrency-guard.sh` name-pattern over-count of `tradfi-bf-*-light-*` Databento VMs so
      `tardis_running_vm_count` reflects true Tardis consumers (repo: deployment-service). Prefer narrowing
      `TARDIS_VM_NAME_PATTERN` or a negative `VM_TARDIS_CONSUMER=0` stamp on the Databento launchers; verify by
      re-running `tardis_running_vm_count` while a tradfi-bf VM runs (should read the genuine Tardis count, not 4).
- [ ] [DATA] P3. Add a guard regression test asserting the union count excludes `tradfi-bf-*-light-*` Databento VMs
      (repo: deployment-service).

## Progress Log

- **2026-08-10T12:31Z (slot 19, data_engineering)** — found during the DERIBIT todo-1 precondition re-check (see parent
  issue's progress log). No code shipped (read-only observation + issue-doc filing). The N=1 slot decision in the parent
  issue was unaffected: even excluding the 3 over-counted VMs, the genuine stamped `cefi-queue-heavy` VM still holds the
  sole slot.
