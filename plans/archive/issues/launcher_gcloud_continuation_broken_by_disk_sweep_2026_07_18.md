---
doc_type: issue
title: "P0: disk-policy sweep broke the gcloud line-continuation across 88 VM launchers"
summary:
  The 2026-07-18 pd-balanced disk-policy sweep inserted the rationale comment block BETWEEN
  `--image-project=...ubuntu-os-cloud \` and `--boot-disk-size` inside the `\`-continued `gcloud compute instances
  create` command in ~88 launchers. A comment inside a backslash-continued command silently truncates it — bash -n and
  shellcheck do NOT flag it — so gcloud ran with no --metadata/--boot-disk/--labels (a metadata-less VM with no
  startup-script = no backfill) and then errored on the stray --boot-disk-size flag.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [vm-launcher, gcloud, disk-provisioning, p0, quality-gate-gap]
related: [check_backfill_vm_disk_provisioning.py]
created: 2026-07-18
parent_epic: infrastructure_master
priority: P0
source:
  ["discovered during the A3.1 Databento throughput measurement — 3 metadata-less VMs booted idle and were deleted"]
assigned_vm:
resolved_by: >-
  deployment-service@ac5d166 (peer: removed the in-continuation comments) + this slot's sweep (moved the rationale ABOVE
  each command in 11 further launchers, verified per file that --boot-disk-size and --metadata are back inside ONE
  command) + the gate that closes the gap: scripts/quality_gates/check_no_comment_in_line_continuation.py, wired into
  quality-gates.sh, verified green on the fixed tree AND red on the re-injected shape that bash -n calls valid.
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# P0 — disk-policy sweep broke the `gcloud` line-continuation across 88 VM launchers

## Symptom (measured 2026-07-18)

Launching any affected VM (first hit: `launch-mtds-backfill-vm.sh` during the A3.1 Databento throughput measurement)
prints:

```
scripts/vm/launch-mtds-backfill-vm.sh: line 247: --boot-disk-size=50GB: command not found
```

and creates a **metadata-less VM** (no `startup-script-url`, no `--boot-disk`, no `--labels`) that boots idle and never
runs the backfill. Three such VMs were created + immediately deleted during the measurement.

## Root cause

The pd-balanced disk sweep added a multi-line rationale comment **inside** the `\`-continued
`gcloud compute instances create` block, e.g.:

```bash
gcloud compute instances create "${VM_NAME}" \
  ...
  --image-project=ubuntu-os-cloud \
  # Tardis-consumer boot disk (measured 2026-07-18): pd-standard 50GB sustains only   <-- BREAKS HERE
  # ~6 MB/s ...
  --boot-disk-size="${BOOT_DISK_SIZE:-250GB}" --boot-disk-type="${BOOT_DISK_TYPE:-pd-balanced}" \
```

In bash, `--image-project=... \` continues onto the next line, which is a `#comment` — the `#` comments out the rest of
the _logical_ line, so the `gcloud` command **ends at `--image-project`** (no metadata/disk/labels), and the
`--boot-disk-size=...` line below becomes a new (nonexistent) command.

## Why it passed QG (gate gap)

`bash -n` (syntax-only) and `shellcheck -S error` do **not** flag a comment inside a `\`-continuation — it is a runtime
_semantic_ truncation, not a parse error. So the sweep's QG went green while shipping a broken fleet.

## Scope

**88 launchers** matched `--image-project=ubuntu-os-cloud \` immediately followed by a `#comment` (ripgrep PCRE2,
verified). Includes every `launch-tradfi-*`, `launch-defi-*`, `launch-mdps-*`, `launch-mtds-*`, `launch-sports-*`,
`launch-features-*`, most `launch-cefi-*`, and all `launch-*-forward-poll.sh`. Launchers with a _second_ clean create
block (e.g. `launch-cefi-sharded-backfill.sh` line 790, the SINGLE_VM_QUEUE path) still worked through that path — which
is why the peer's cefi throughput measurement succeeded and the bug went unnoticed. Launchers whose only create is the
broken one (`launch-tradfi-backfill-vm.sh`, `launch-defi-backfill-vm.sh`, `launch-mdps-backfill-vm.sh`,
`launch-mtds-backfill-vm.sh`, …) were **fully broken** — including the forward-poll launchers, so live coverage was
eroding.

## Fix (applied 2026-07-18)

Uniform: remove the comment lines the sweep inserted between `--image-project=...ubuntu-os-cloud \` and the next flag,
restoring the continuation. The disk rationale is preserved in
`deployment-service/scripts/quality_gates/check_backfill_vm_disk_provisioning.py` (the enforcing gate). `bash -n` clean
on all 88; 0 remaining matches of the broken pattern. Shipped with the A3.1 Databento concurrency plumbing.

## Follow-ups (P1)

- [ ] [SCRIPT] P1. **Add a QG check that catches a comment inside a `\`-continued command** (the gate gap that let this
      ship) — a small AST/line-scan in the deployment-service QG (`scripts/quality_gates/`). Without it, the next sweep
      can re-break the fleet silently.
- [ ] [DOCS] P2. Prefer moving rationale comments **above** the `gcloud compute instances create` line as a convention
      (documented in the launcher-runbook), so a future sweep can't reintroduce the break.
