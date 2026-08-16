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
status: resolved
nature: issue
asset_group: [cefi, cross-cutting, tradfi]
stage: [data]
repos: [deployment-service]
scope: [engineer, admin]
tags: [tardis, vm-launcher, concurrency, name-pattern, guard, tradfi, databento]
related:
  [
    /plans/archive/issues/tardis_concurrency_gate_hardening_2026_08_09.md,
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
resolved_by: slot-33, 2026-08-16
source: >-
  Re-check of cefi_deribit_futures_chain_canonical_write_path_exposure_2026_08_09.md todo 1's precondition via the
  canonical tardis-concurrency-guard.sh (slot 19, 2026-08-10).
context_scope:
  [
    /plans/archive/issues/tardis_concurrency_gate_hardening_2026_08_09.md,
    /plans/active/issues/cefi_deribit_futures_chain_canonical_write_path_exposure_2026_08_09.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/tardis-concurrency-guard.sh,
    deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh,
  ]
---

> **🟢 ARCHIVED 2026-08-16 — RESOLVED.** Both action items done: the fix itself (option 3, negative-stamp exclusion)
> already shipped 2026-08-10 (`tardis-concurrency-guard.sh@98ec8ddb85` + `launch-tradfi-backfill-vm.sh@f8d3312d21`,
> under an unrelated-sounding commit message — confirmed via direct code read, not the message alone); the missing
> regression test shipped 2026-08-16 (`deployment-service@374b1dcd`). Live over-count table in this doc (1 genuine +
> 3 Databento → 4) now reproducibly returns 1 against the real script. No open todos remain.

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

- [x] ✅ [DATA] P3. **DONE — already shipped 2026-08-10 (option 3: negative-stamp), confirmed 2026-08-16 (slot-33,
      data_engineering).** `tardis-concurrency-guard.sh@98ec8ddb85` ("fix(vm): honor explicit VM_TARDIS_CONSUMER
      opt-out so Databento tradfi backfill VMs aren't killed as tardis_cap_violation", 2026-08-10T16:23:04Z) already
      made `tardis_running_vm_count` read an explicit `VM_TARDIS_CONSUMER` metadata declaration (`1`=consumer,
      `0`=explicit opt-out) BEFORE falling back to `TARDIS_VM_NAME_PATTERN` (`compose_instrument_ids`-style union
      logic, `tardis-concurrency-guard.sh:204-217`); `launch-tradfi-backfill-vm.sh:269` stamps
      `VM_TARDIS_CONSUMER=0` on every VM it creates (`es-opt-backfill-watcher.sh` shells out to that same launcher,
      so it inherits the stamp with no separate fix needed). Verified live against the real script (mocked
      `gcloud compute instances list`, not a re-implementation): a `tradfi-bf-vix-light-2020-...` name-match with
      `VM_TARDIS_CONSUMER=0` now returns count=0; the exact live over-count scenario from this doc's own table (1
      genuine `cefi-queue-heavy` Tardis VM + 3 `tradfi-bf-*-light-*` Databento VMs) now returns 1, not 4. No further
      code change needed — this todo's own scope (fix the guard) was already complete; only the regression test
      below was still missing.
- [x] ✅ [DATA] P3. **DONE 2026-08-16 (slot-33, data_engineering) — `deployment-service@374b1dcd`.** Added
      `TestTardisConcurrencyGuardConsumerStamp` (`tests/unit/test_vm_launcher_scripts.py`) — 4 regression tests
      against the REAL `tardis-concurrency-guard.sh` (mocked `gcloud compute instances list`, same pattern as the
      file's existing `TestSetupScriptFreshnessGuard`/`TestCanonicalisationGateGuard` classes): (1) a
      `tradfi-bf-*-light-*` name-match stamped `VM_TARDIS_CONSUMER=0` is excluded; (2) a
      `VM_TARDIS_CONSUMER=1` stamp is counted even without a name match; (3) an UNSTAMPED name-match still counts
      (pre-rollout fallback preserved); (4) the mixed fleet from this doc's own live evidence table (1 genuine +
      3 Databento) counts as 1. All 4 manually verified against the live script before wiring into pytest (see
      Progress Log) — full `quality-gates.sh` run before ship.

## Progress Log

- **2026-08-10T12:31Z (slot 19, data_engineering)** — found during the DERIBIT todo-1 precondition re-check (see parent
  issue's progress log). No code shipped (read-only observation + issue-doc filing). The N=1 slot decision in the parent
  issue was unaffected: even excluding the 3 over-counted VMs, the genuine stamped `cefi-queue-heavy` VM still holds the
  sole slot.

- **context-scout 2026-08-14**: populated context_scope (5 entries).

- **2026-08-16 (slot-33, data_engineering)** — on pickup, found the fix itself already shipped 2026-08-10
  (`tardis-concurrency-guard.sh@98ec8ddb85` + `launch-tradfi-backfill-vm.sh@f8d3312d21`'s `VM_TARDIS_CONSUMER=0`
  stamp) under a differently-worded commit message (framed as fixing a `tardis_cap_violation` false-kill, not
  explicitly citing this issue doc) — confirmed via `git log` + direct code read, not assumed from the commit
  message alone. Verified the fix's actual behavior against the real script with mocked `gcloud` output
  reproducing this doc's own live over-count table exactly (1 genuine + 3 Databento → 1, not 4). Wrote the
  still-missing regression test (todo 2) covering both the exclusion and the backward-compat fallback path.
