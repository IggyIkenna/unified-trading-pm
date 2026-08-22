---
doc_type: issue
title: >-
  8 one-off launcher VMs use launcher_common.sh's lc_log_upload_trap_block (Class B), which has observability but ZERO
  in-VM stall-timeout/auto-kill logic — 6 of them also fail the fleet-wide backfill-naming heuristic, leaving no
  protective layer at any level
summary: >-
  Discovered as a byproduct of the Gap-3 naming-heuristic fix in
  /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md (todo 2/5). That doc's Gap 2 was
  re-verified this session and found narrower than originally stated: canonical-migration-family launchers DO route
  through `setup-data-pipeline-vm.sh`'s shared `_launch_with_tee()` → `vm-exec-with-gcs-tee.sh`, giving them the generic
  30-min byte-growth stall-kill by default (Class A). But a SECOND, separate launcher family —
  `deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_log_upload_trap_block()` (Class B) — is documented in its
  own docstring as "the SSOT lightweight equivalent" of `vm-exec-with-gcs-tee.sh`, but only provides log-tee-to-GCS + a
  heartbeat blob + a terminal EXIT_STATUS marker. It has NO `STALL_TIMEOUT_SEC`/kill logic anywhere — grep for
  STALL/kill/timeout in launcher_common.sh finds nothing resembling an auto-kill. 8 launchers use it. After the Gap-3
  naming fix (deployment-service@fde4f4f), 6 of those 8 STILL fail `_is_backfill_vm()` (their VM_NAME carries no
  backfill/migration-family substring), meaning they have no protective layer at ANY level: no in-VM stall-kill (Class
  B), and the fleet-wide heartbeat_stall_watcher.py routes them into the heartbeat-blob-only liveness path (which stays
  fresh even if the actual embedded workload hangs, since the blob is written by the wrapper's own background streamer
  loop, independent of the workload process). This is the single highest-priority remediation target of the whole
  one-off-launcher fleet audited by that issue doc's todo 5.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [vm-monitoring, hung-vm, stall-detection, launcher-common, class-b-launcher, deployment-observability]
related:
  [
    /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/05-infrastructure/deployment-observability.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-07-27
author: unknown
parent_epic: security_and_cross_cutting_master
priority: P2
estimate_class: infra
assigned_role: infrastructure
source: >-
  Surfaced during the Gap-3 launcher audit (todo 5) for
  /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md, 2026-07-27 — an interactive
  `/autonomous` session implementing todo 2's `_is_backfill_vm()` naming fix. All code-path claims in this doc were
  independently re-verified this session by direct file read (not trusted from any prior summary): `grep -n
  "STALL\|kill\|timeout" deployment-service/scripts/vm/lib/launcher_common.sh` and `grep -l "lc_log_upload_trap_block"
  deployment-service/scripts/vm/launch-*-vm.sh`, plus a direct `VM_NAME=`/`VM_PREFIX=` read of all 8 matching launchers
  against the shipped `_is_backfill_vm()`.
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /plans/archive/issues/migration_vm_hung_detection_monitoring_gap_2026_07_27.md,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
---

# 8 Class-B launcher VMs have zero in-VM stall-kill; 6 of them also fail the fleet naming heuristic

> Investigation-only record (this doc). No launcher script was changed, no `launcher_common.sh` behavior was modified
> while authoring this doc. `assigned_vm: NA`, `execution_scope: local-only` — a human decides when to pick up the fix
> todos below.

## What I found

`deployment-service/scripts/vm/lib/launcher_common.sh`'s `lc_log_upload_trap_block()` (function starts at line 1028) is
documented in its own docstring (lines 951-1007) as "the SSOT lightweight equivalent" of `vm-exec-with-gcs-tee.sh` for
launchers that build their own bespoke inline startup script instead of routing through the shared
`setup-data-pipeline-vm.sh`. It gives three things: (1) tee the workload's log to GCS, (2) a periodic heartbeat blob,
(3) a terminal `EXIT_STATUS` marker on process exit. Direct re-grep this session
(`grep -n "STALL\|kill\|timeout" deployment-service/scripts/vm/lib/launcher_common.sh`) confirms it has **no
`STALL_TIMEOUT_SEC`, no stall-detection, no auto-kill logic anywhere** — the only `kill` in the file (line ~1074,
`kill "$_LC_STREAM_PID" 2>/dev/null || true`) just tears down its own background log-streamer process on the wrapper's
EXIT trap, not the monitored workload.

`grep -l "lc_log_upload_trap_block" deployment-service/scripts/vm/launch-*-vm.sh` finds exactly 8 launchers on this
path:

- `launch-aave-lending-rate-validation-vm.sh` — `VM_PREFIX="aave-lending-rate-val-"`
- `launch-amm-golden-fixture-validation-vm.sh` — `VM_PREFIX="amm-golden-${SHAPE_SLUG}-"`
- `launch-cefi-fwd-daily-cron-vm.sh` — `VM_PREFIX="cefi-fwd-daily-cron-"`
- `launch-features-sports-parallel-backfill-vm.sh` — `VM_NAME="fss-backfill-vm-${VM_NUM}"`
- `launch-gcs-migration-bundle-vm.sh` — `VM_NAME="gcs-migration-bundle-${ASSET_GROUP}-${YEAR}-${RUN_TS}"`
- `launch-prediction-features-vm.sh` — `VM_NAME="${VM_NAME_OVERRIDE:-prediction-features-1}"`
- `launch-prediction-pipeline-vm.sh` — `VM_NAME="${VM_NAME_OVERRIDE:-prediction-pipeline-1}"`
- `launch-tradfi-fwd-daily-cron-vm.sh` — `VM_PREFIX="tradfi-fwd-daily-cron-"`

None of these 8 gets any in-VM stall-timeout protection — Class B is strictly weaker than even the canonical-migration
family's Class-A weak byte-growth default.

## The naming heuristic compounds this for 6 of the 8

After the Gap-3 fix shipped this session (`deployment-service@fde4f4f3b557f9dcef8cb355a57d63122ab087bd`,
`heartbeat_stall_watcher._is_backfill_vm()` now also matches the `canonical-migration`/`mtds-migrate-cefi-*`/
`mtds-prediction-kalshibulk`/`sports-v9-migration`/`mdps-sports-bucket`/`sports-manifest-rescan` prefixes), I re-checked
all 8 Class-B VM_NAME values against the shipped function directly:

| Launcher                                       | VM_NAME                               | `_is_backfill_vm()` after Gap-3 fix                                                                          |
| ---------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| launch-aave-lending-rate-validation-vm.sh      | `aave-lending-rate-val-*`             | **False** — no protective layer                                                                              |
| launch-amm-golden-fixture-validation-vm.sh     | `amm-golden-*-*`                      | **False** — no protective layer                                                                              |
| launch-cefi-fwd-daily-cron-vm.sh               | `cefi-fwd-daily-cron-*`               | **False** — no protective layer (lower priority: short cron poll, small exposure window)                     |
| launch-gcs-migration-bundle-vm.sh              | `gcs-migration-bundle-*-*-*`          | **False** — no protective layer (contains "migration" but not any of the specific matched prefixes)          |
| launch-prediction-features-vm.sh               | `prediction-features-1` (or override) | **False** — no protective layer                                                                              |
| launch-prediction-pipeline-vm.sh               | `prediction-pipeline-1` (or override) | **False** — no protective layer                                                                              |
| launch-tradfi-fwd-daily-cron-vm.sh             | `tradfi-fwd-daily-cron-*`             | **False** — no protective layer (lower priority: short cron poll)                                            |
| launch-features-sports-parallel-backfill-vm.sh | `fss-backfill-vm-*`                   | **True** (matches `"backfill"` substring, pre-existing) — carries only the Class-B risk, not the naming-miss |

6 of the 8 (all but `launch-features-sports-parallel-backfill-vm.sh`) have **no protective layer at any level**: no
in-VM stall-kill (Class B), and the fleet-wide `heartbeat_stall_watcher.py` routes them into the heartbeat-blob-only
liveness path — which per the watcher's own docstring stays fresh even if the monitored workload process hangs, because
the blob is written by the wrapper's OWN background streamer loop, independent of whether the embedded workload is
actually making progress. A wedged `launch-aave-lending-rate-validation-vm.sh` run, for example, would show `RUNNING` +
a fresh heartbeat blob indefinitely, identical in shape to the 10/42 hung canonical-migration VMs that motivated the
parent issue doc.

## Why this is a SEPARATE gap, not covered by the Gap-3 naming fix

The Gap-3 fix (`migration_vm_hung_detection_monitoring_gap_2026_07_27.md` todo 2) deliberately stayed narrow — it added
the specific, individually-verified `VM_TASK=canonical-migration`-dispatch family prefixes (Class A, confirmed live
stall-kill via the shared tee-wrapper), per that issue doc's own blast-radius requirement (a gate change must be proven
safe against the whole fleet before shipping, not broadened speculatively). Widening the naming heuristic with generic
substrings like `"validation"`/`"cron"`/`"migration"` to also catch these 6 was explicitly rejected as out-of-scope for
that fix — it would touch the SAME shared function used by the entire fleet, and none of these 6 launcher's broader
naming implications were individually verified against every other in-fleet VM name the way the Class-A migration family
was. Even if the naming gap were closed for these 6, they would STILL have zero in-VM stall-kill (Class B) — the naming
heuristic only decides which EXTERNAL liveness signal `heartbeat_stall_watcher.py` applies; it does not add an in-VM
watchdog. The real fix here is either (a) migrating these 8 launchers off `lc_log_upload_trap_block()` onto the shared
`setup-data-pipeline-vm.sh` / `vm-exec-with-gcs-tee.sh` route (Class A), or (b) adding an equivalent
`STALL_TIMEOUT_SEC`-style kill to `lc_log_upload_trap_block()` itself.

## What's NOT done / follow-up needed

- [ ] [HUMAN] P2. **Add stall-timeout/auto-kill logic to `lc_log_upload_trap_block()`** (or migrate the 8 launchers
      above onto the shared `setup-data-pipeline-vm.sh` route so they inherit `vm-exec-with-gcs-tee.sh`'s existing
      byte-growth watchdog). Done when: a deliberately-wedged workload under one of the 8 launchers is killed within a
      configured timeout instead of running indefinitely.
- [ ] [INFRA] P2. **Add an explicit allowlist (not a heuristic widening)** so the 6 doubly-unprotected launcher
      VM_NAMEs (`aave-lending-rate-val-*`, `amm-golden-*`, `cefi-fwd-daily-cron-*`, `prediction-features-*`,
      `prediction-pipeline-*`, `tradfi-fwd-daily-cron-*`) route through `heartbeat_stall_watcher.py`'s
      run-log-freshness liveness path. Per D140 ruling (2026-08-22): allowlist — gets protection without re-opening
      the heuristic to every fleet VM name. Done when: `_is_backfill_vm()` returns `True` for all 6 without any
      newly-introduced false positive against a legitimately-continuous live/paper VM name. **NOTE 2026-08-03 (slot-7,
      `bucket_iam_write_protection_per_tier_2026_06_09.md` P2.2i)**: `gcs-migration-bundle-*` removed from this list —
      `launch-gcs-migration-bundle-vm.sh` was confirmed-dead code and deleted, so it no longer needs a stall-kill fix.
- [ ] [HUMAN] P3. **Re-prioritize `cefi-fwd-daily-cron-*` / `tradfi-fwd-daily-cron-*`** — lower priority than the other
      4 since they're short daily cron polls with a much smaller wedge-exposure window, but still genuinely unprotected.

## Evidence / how to reproduce

```bash
# Class B has no stall-kill logic at all
grep -n "STALL\|kill\|timeout" deployment-service/scripts/vm/lib/launcher_common.sh

# The 8 launchers on the Class-B path
grep -l "lc_log_upload_trap_block" deployment-service/scripts/vm/launch-*-vm.sh

# Each launcher's actual VM_NAME/VM_PREFIX construction
grep -n "VM_NAME=\|VM_PREFIX=" deployment-service/scripts/vm/launch-aave-lending-rate-validation-vm.sh \
  deployment-service/scripts/vm/launch-amm-golden-fixture-validation-vm.sh \
  deployment-service/scripts/vm/launch-cefi-fwd-daily-cron-vm.sh \
  deployment-service/scripts/vm/launch-gcs-migration-bundle-vm.sh \
  deployment-service/scripts/vm/launch-prediction-features-vm.sh \
  deployment-service/scripts/vm/launch-prediction-pipeline-vm.sh \
  deployment-service/scripts/vm/launch-tradfi-fwd-daily-cron-vm.sh \
  deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh

# Confirm each VM_NAME against the shipped naming heuristic (deployment-service@fde4f4f3b557f9dcef8cb355a57d63122ab087bd)
python3 -c "
from deployment_service.data_pipeline_monitors.heartbeat_stall_watcher import _is_backfill_vm
for n in ['aave-lending-rate-val-20260727', 'amm-golden-shape-20260727', 'cefi-fwd-daily-cron-20260727',
          'gcs-migration-bundle-cefi-2026-20260727', 'prediction-features-1', 'prediction-pipeline-1',
          'tradfi-fwd-daily-cron-20260727', 'fss-backfill-vm-1']:
    print(n, _is_backfill_vm(n))
"
```

## Progress Log

- **na-eligibility-audit 2026-08-09 (round11 RECLASSIFY+satellite-extraction sweep, infra tranche)**: KEEP-NA, valid —
  unchanged. All 3 `[HUMAN]` P2/P3 items still require the same whole-fleet naming-collision blast-radius review this
  doc's own text says was explicitly rejected as out-of-scope for the narrower Gap-3 fix (a false positive here means
  wrongly matching a legitimately-continuous live/paper VM name); none is independently separable from that review.
  Checked against this round's accumulated-precedent list (IAM self-service, D16 all-repos, S5.1 tiering,
  plan-destination-AO-default, escalation-N=3-days, reversibility-qualified deletes, Option B retired, GSM secret + 5
  Slack webhooks) — none apply to a fleet-wide naming-heuristic blast-radius judgment call.
- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — 3 [HUMAN] P2 items (stall-timeout/auto-kill
  design, naming-heuristic allowlist, cron reprioritization); design/operator decisions, not bounded outcomes.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — All 3 todos require a
  fleet-wide blast-radius verification/judgment call (avoiding false positives against legitimately-continuous
  live/paper VM names) that the doc itself says was explicitly rejected as out-of-scope for a prior, narrower fix.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid — unchanged from the 2026-07-30
  verdict.** In scope only because a context-scout backfill touched the file; no content change since. Read end-to-end;
  `grep -cE '^- \[ \]'` = **3**, matching this verdict's item count. All 3 are `[HUMAN]`-tagged and each needs the
  whole-fleet naming-collision review the parent issue doc's own blast-radius rule mandates before touching the shared
  `_is_backfill_vm()` — a widening explicitly rejected as out-of-scope for the narrower Gap-3 fix, whose failure mode is
  a false positive against a legitimately-continuous live/paper VM name. Independently corroborated:
  `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s own non-batchable table classifies this doc
  **blast-radius-judgment-gated**. Not a bounded worker-determinable outcome.
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-17**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-20**: refreshed context_scope (4 entries)
- **2026-08-22 — ruling D140 (Class-B stall-watch coverage)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Allowlist — gets protection without re-opening the heuristic to every fleet VM name.
  Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
