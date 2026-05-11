---
title: "Phase 3.D cross-asset rescan VM fails at startup — CLI dispatcher gap"
created: 2026-05-11
resolved: 2026-05-11
status: ✅ RESOLVED
author: ikenna-available-at-tab (slot 3)
resolver: ikenna-available-at-tab (slot 3) — operator authorized 2026-05-11 PM
resolution_commits:
  - deployment-service@03ce073 (route launcher via VM_BACKFILL_CMD direct script invocation)
source:
  - market-data-processing-service VM run log at gs://deployment-scripts-central-element-323112/vm-logs/cross-asset-rescan-20260511-153940/run.log
  - instruments-service@a264f21 (Phase 3.D rescan script ship)
  - deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh (launcher)
  - instruments-service/scripts/cross_asset_rescan.py:25-32 (invocation contract in docstring)
locked_by: live-defi-rollout
locked_since: 2026-05-11
---

> ✅ **RESOLVED 2026-05-11 PM** via Option B (route launcher through `VM_BACKFILL_CMD`
> direct-script-invocation, bypass CLI dispatch). Fix shipped at
> `deployment-service@03ce073`. Same shape as `launch-defi-phantom-recon-vm.sh` +
> `launch-expected-universe-enumerator-vm.sh` — the rescan is a one-shot
> orchestrator on top of the existing phantom-audit reconciler, not a payload-
> processor in the `UnifiedServiceHandler` shape, so direct script invocation
> is the right abstraction. (Option A — register CLI dispatcher entry — would
> have forced the rescan into a payload-processor shape it doesn't fit.)
> Relaunched as `cross-asset-rescan-20260511-171623`; Phase 8 triage review
> unblocked.

> **Severity**: P0 — blocks `manifest_schema_final_gate_2026_05_09.md` Phase 8 triage review on the May-23 critical
> path. Phase 8 consumes `gs://central-element-323112-rescan-triage/{run_id}/triage.jsonl` produced by the rescan VM;
> currently no rescan run can succeed.
>
> **Blast radius**: Phase 3 (cross-asset rescan launcher + dispatcher + watchdog dict + deployment-api registry) ships
> are individually green per slot 6's earlier ping, but the end-to-end runtime path is broken at the CLI boundary.
> The first operational kickoff (slot 3's `cross-asset-rescan-20260511-153940` VM at 14:39:40Z 2026-05-11) failed at
> argparse with `error: argument --operation: invalid choice: 'cross_asset_rescan' (choose from instruments)` and
> auto-shutdown without producing a `triage.jsonl`.
>
> **Suggested owner**: slot 6 (manifest_schema_final_gate Phase 3.D owner — they shipped the rescan script at
> `instruments-service@a264f21`).

# Phase 3.D cross-asset rescan VM fails at startup — CLI dispatcher gap

## What I found

The `cross-asset-rescan-20260511-153940` VM (launched 2026-05-11 14:39:40Z per the slot 3 VM-wrap cycle) ran:

```
/home/ikennaigboaka/venv/bin/python -m instruments_service \
  --operation cross_asset_rescan --mode batch --asset-group cross_asset_all
```

(per the metadata fields `VM_OPERATION=cross_asset_rescan` + `VM_ASSET_GROUP=cross_asset_all` set by
`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh:159` and translated to argv by
`gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh`).

The instruments-service CLI's `--operation` choice set is:

```
--operation {instruments}
```

i.e. only `instruments` is registered as a valid operation. `cross_asset_rescan` is NOT registered, so argparse
rejects the launch with `error: argument --operation: invalid choice: 'cross_asset_rescan' (choose from instruments)`
and `[vm-exec] command exited rc=2`. The VM emits `DEPLOYMENT_FAILED` and auto-deletes per
`VM_SHUTDOWN_ON_COMPLETION=true`.

Full failure log preserved at:
- `gs://deployment-scripts-central-element-323112/vm-logs/cross-asset-rescan-20260511-153940/run.log`

The rescan script itself exists at `instruments-service/scripts/cross_asset_rescan.py` (shipped at
`instruments-service@a264f21`) with its own `argparse` + `main()` + `if __name__ == "__main__":` (line 252-332). The
script's docstring at lines 25-32 declares the canonical invocation as:

```
python -m instruments_service \
    --operation cross_asset_rescan \
    --mode batch \
    --asset-group <cefi|defi|tradfi|sports|prediction|cross_asset_all> \
    [--apply]
```

But there is no `cross_asset_rescan` operation dispatcher registered in `instruments_service.cli` to translate this
invocation into a call to `scripts/cross_asset_rescan.py:main()`. Grep across `instruments_service/cli/` returns no
hits for `cross_asset_rescan`.

## Why it matters

`manifest_schema_final_gate_2026_05_09.md` Phase 3 is supposed to be operationally complete after:
1. Launch cross-asset-rescan VM (deployment-service@`19fad8c`) ✅ launcher shipped
2. VM runs cross_asset_rescan dispatcher (instruments-service@`a264f21`) ❌ CLI dispatcher gap
3. Triage JSONL streams to `gs://{pid}-rescan-triage/{run_id}/triage.jsonl` ❌ never written
4. Phase 8 triage review consumes the JSONL ❌ blocked on (3)

The Phase 8 gate IS on the 2026-05-15 freeze gate + 2026-05-23 cutover critical path. Without a successful rescan run,
the workspace has no visibility into manifest↔disk drift across the 5 asset_groups — a known blast radius from the
2026-05-04 130,897 false-positive phantoms incident.

The cost of slot 3's failed kickoff is small (~$0.10 for the 3-min VM run before auto-shutdown), but every retry
without fixing the dispatcher will fail the same way.

## Recommended decision

Two valid fixes — slot 6 (or whoever picks up the routing) picks:

**Option A — register `cross_asset_rescan` as a CLI operation in `instruments_service.cli`**:

The cleaner path. Add `cross_asset_rescan` to the operation choices list + register a dispatcher that imports
`scripts/cross_asset_rescan` and calls its `main()`. Matches the docstring-stated invocation contract; no launcher
change needed.

```python
# instruments_service/cli/__init__.py or wherever the choices are defined
operation_choices = ["instruments", "cross_asset_rescan"]
```

```python
# instruments_service/cli/dispatcher.py
def dispatch(operation: str, args: argparse.Namespace) -> int:
    if operation == "instruments":
        return _dispatch_instruments(args)
    if operation == "cross_asset_rescan":
        from scripts.cross_asset_rescan import main as rescan_main
        return rescan_main()  # uses its own argparse over sys.argv
    raise ValueError(f"unknown operation: {operation}")
```

**Option B — change launcher to invoke the script directly**:

Update `deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh` (and/or
`gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh`) to translate
`VM_OPERATION=cross_asset_rescan` into:

```
python scripts/cross_asset_rescan.py --asset-group cross_asset_all [--apply]
```

instead of `python -m instruments_service --operation cross_asset_rescan ...`. Less clean (deviates from the
service-CLI convention codified in CLAUDE.md "Service CLIs: --operation (what) --mode (batch/live) --asset-group
(domain)") but lighter-touch fix.

**Suggested**: Option A. Matches the docstring-stated contract + workspace convention + minimal launcher churn. ~30
min of slot 6 time (1 dispatcher registration + 1 import + 2 unit tests asserting the dispatcher resolves correctly).

After the fix lands, slot 3 (or whoever picks up the operational follow-up) can relaunch the rescan VM via
`bash deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh cross_asset_all` and the run will complete
naturally, producing the `triage.jsonl` Phase 8 needs.

## Composes with

- `manifest_schema_final_gate_2026_05_09.md` Phase 3 (slot 6 — owner of Phase 3.D dispatcher fix)
- `manifest_schema_final_gate_2026_05_09.md` Phase 8 (triage review owner — blocked until dispatcher fix lands)
- `available_at_lookahead_bias_completion_2026_05_08.md` Re-task continuation 6 (slot 3 cross-side ping marked the
  rescan kickoff; this issue doc supersedes the ✅ status to ❌ blocked)
- CLAUDE.md "Service CLIs" convention (the dispatcher should be where new operations register)
- CLAUDE.md "No fire-and-forget VM launches" — the failure was caught immediately via the event-stream verification
  recipe (STARTED fired but no progress + no STOPPED → diagnosed via VM run log)
