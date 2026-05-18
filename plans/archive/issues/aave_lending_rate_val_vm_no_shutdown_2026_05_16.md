---
title: "aave-lending-rate-val VM ran validation in 3 min but stayed alive 7+ hours (no STOPPED event; no shutdown)"
created: 2026-05-16
author: ikenna-main (orchestrator cycle audit during continuous /loop)
status: RESOLVED — root-cause fix shipped at deployment-service@472f9ca (2026-05-16 slot-8)
source:
  - "ikenna-main launched VM 2026-05-16 12:15:30 UTC per operator request"
  - "results.json written at 2026-05-16T11:18:49Z (~3 min after VM launch)"
  - "VM serial console shows only systemd housekeeping (cert refresh + sysstat) — no python process active"
  - "VM still RUNNING 7+ hours later (deleted manually 2026-05-16 18:42 UTC)"
severity: P1 (compute waste + no-fire-and-forget HARD RULE violation)
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## ✅ RESOLUTION 2026-05-16 (slot-8)

**Root cause confirmed**: `launch-aave-lending-rate-validation-vm.sh` startup-script has `set -euo pipefail` at
line 129. When validation exits non-zero (e.g., FAILED gate with pass_rate < threshold per
`run_lending_rate_validation.py` final `log_event("STOPPED" if passed_gate else "FAILED")` + `sys.exit(1)`), the
`set -e` halted the startup script BEFORE reaching the `shutdown -h now` step at line 214. VM stayed alive indefinitely.

**Fix shipped** at `deployment-service@472f9ca`: brackets the `python3 scripts/run_lending_rate_validation.py ...` call
with `set +e` / `set -e` so `EXIT_CODE` is captured and the final `shutdown -h now` runs regardless of validation
outcome. Final log upload (`gsutil cp || true`) was already non-blocking.

The validation script ALREADY emitted STOPPED — original issue-doc Recommended decision (A) was based on incomplete
reading. The script does `log_event("STOPPED" if passed_gate else "FAILED")` at end. Only the **VM shutdown** was
missing. Recommended decision (B) (watchdog re-pointing) is no longer needed since the launcher itself now self-deletes
deterministically.

Next phase_3c re-run will exercise the fix; expect STOPPED event + VM deletion within ~30s + 30s sleep + ~10s gcloud
shutdown round-trip.

## What I found

The `aave-lending-rate-val-` VM type (Phase 3C Aave V3 lending rate validation harness) runs the validation script,
writes `results.json` to `gs://central-element-323112-defi-validation/results/lending/<date>/<correlation_id>/`, then
**stays alive indefinitely** without:

- Emitting a `STOPPED` event to `gs://central-element-323112-events/events/lending-rate-validation/`
- Calling `gcloud compute instances delete <self>` to clean up

Observed today: VM `aave-lending-rate-val-20260516-121530` launched at 12:15:30 UTC by `ikenna-main`. Validation
completed at 11:18:49Z (the script's clock — ~3 min runtime). VM was still `RUNNING` 7 hours later when I noticed during
orchestrator cycle audit. Serial console showed only systemd housekeeping after 11:21 UTC (no python work).

Manually deleted at 18:42 UTC. Cost impact: ~7 hours of `n2-standard-4` idle compute = ~$0.50, but the pattern is the
bug, not the cost.

## Why it matters

Per CLAUDE.md HARD RULE "No fire-and-forget VM launches (CRITICAL)":

> STARTED within 60s + ≥1 progress event/hour + STOPPED/FAILED at exit

This VM emits STARTED (verified earlier today) but NEVER emits STOPPED. The
[`vm_zombie_watchdog.py`](../../deployment-service/vm_zombie_watchdog.py) per-prefix threshold for
`aave-lending-rate-val-` is probably set incorrectly OR the launcher's shutdown step is missing.

Compounding: if multiple phase_3c re-runs happen during DAI IRM iteration (which slot 6 may do soon when they fix DAI's
interest-rate-strategy), each re-run leaves an idle VM behind. With slot 6 likely doing 5-10 iterations, that's 5-10
idle n2-standard-4 instances accumulating $3-5/day each.

## Root cause hypothesis

Looking at
[`deployment-service/scripts/vm/launch-aave-lending-rate-validation-vm.sh`](../../deployment-service/scripts/vm/launch-aave-lending-rate-validation-vm.sh)
header comment:

> Watchdog registration: VM prefix "aave-lending-rate-val-" is registered in VM_PREFIX_TO_BUCKET in
> vm_zombie_watchdog.py (None = heartbeat-only since this VM does NOT write per-VM manifest shards).

The launcher relies on the zombie watchdog to clean up; the validation script itself doesn't shut down. But
heartbeat-only watchdog means it only kills VMs that stop emitting heartbeat — not VMs that emit nothing after the
workload completes.

## Recommended decision

Two-part fix:

**(A) Update validation script** to emit STOPPED + call self-delete on completion. Pattern from existing
event-stream-aware launchers:

```python
# At end of run_lending_rate_validation.py
log_event("STOPPED", details={"correlation_id": correlation_id})
# Optional: trigger self-delete via gcloud metadata API or systemd shutdown unit
```

**(B) Update `vm_zombie_watchdog.py` threshold for `aave-lending-rate-val-`** from heartbeat-only to "kill if no
STARTED→STOPPED within 1 hour" (the validation is bounded at ~10 min worst case).

**Owner**: Ikenna slot 6 (phase_3c lending model owner) — fold into the DAI IRM iteration work. Each iteration's VM
launch should use the fixed launcher.

**Interim**: any operator/slot launching `aave-lending-rate-val-` VMs should `gcloud compute instances delete <vm-name>`
after results.json lands. I'll add a post-launch reminder to my own slot 1 main launch pattern.

## Phase 3c result from today's idle VM (still valid; DAI IRM still wrong)

Just for reference, the result that the VM produced before going idle:

```
total_events: 60   passed: 10   pass_rate: 16.7%
USDC: 7/7 = 100% ✅
USDT: 3/3 = 100% ✅
DAI: 0/50 = 0% ❌ — sim ~1.1% vs realized 3.7-6.4% (360-526bps delta)
```

USDC + USDT IRM defaults from `unified-api-contracts@215ed3e` (slot 6 yesterday) are CORRECT. DAI defaults remain
fundamentally wrong; needs slot 6 follow-up per my 2026-05-16 12:15 UTC ping in `ikenna_orchestrator/pings/slot_6.md`.
