---
title: Service registry drift audit — VM prefix vs cloud-providers.yaml
created: 2026-05-15
author: slot-2 agent (harsh)
source:
  - deployment-service/scripts/vm/vm_zombie_watchdog.py
  - deployment-service/configs/cloud-providers.yaml
locked_by: none
---

# Service Registry Drift Audit — 2026-05-15

## What I found

### Audit scope

Item 14 from slot_2 queue: "verify every VM_PREFIX in vm_zombie_watchdog.py has a corresponding entry in any
service-registry / cloud-providers.yaml; file drift."

### cloud-providers.yaml is bucket-naming SSOT only

`deployment-service/configs/cloud-providers.yaml` maps logical bucket names to GCS paths using `${GCP_PROJECT_ID}`
template variables. It does NOT track VM name prefixes. It is the SSOT for `resolve_bucket_name()` (QG STEP 5.69), not
for VM launch governance.

**No separate "service registry" file exists** for VM prefix governance. `VM_PREFIX_TO_BUCKET` in
`vm_zombie_watchdog.py` **is** the VM prefix registry — it is the sole authoritative list.

### VM prefix coverage result: 0 orphans

Cross-checked all 94 launcher scripts against 145 registered prefixes in `VM_PREFIX_TO_BUCKET`. Method: extract
`VM_NAME=` definitions from each launcher and verify the name starts with at least one registered prefix.

**Result: 0 genuine orphan VM names.** Every launcher that emits a VM_NAME value matches a registered prefix.

Two edge cases reviewed:

- `launch-cefi-week-test.sh` — delegating wrapper; delegates to `launch-cefi-forward-poll.sh` which has `cefi-fwd-`
  registered. No direct `VM_NAME=` definition. False positive from regex (comment text only).
- `launch-vm-zombie-watchdog.sh` — uses `vm-zombie-watchdog-{ts}`. This prefix is intentionally absent from
  `VM_PREFIX_TO_BUCKET`. The watchdog exempts its own VM via `purpose=vm-zombie-watchdog` GCE label check
  (vm_zombie_watchdog.py line 856). This is documented design, not drift.

### What IS the registry relationship?

| Registry                         | SSOT for                                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------ |
| `VM_PREFIX_TO_BUCKET` (watchdog) | VM zombie governance — which prefixes are watched, which bucket holds their shard manifest |
| `cloud-providers.yaml`           | Bucket name resolution — `resolve_bucket_name()` lookups                                   |
| `VmPrefixSpec` in UAC            | Per-prefix metadata schema (bucket, manifest key, etc.)                                    |

These three are complementary; they do not overlap. No drift exists between them.

## Why it matters

The CLAUDE.md rule "VM naming: first segment must be in `VM_PREFIX_TO_BUCKET`" is being followed across all 94
launchers. Compliance is confirmed. The watchdog catch-all sweep covers any unlisted prefixes via
`has_known_prefix=False` path, so unregistered VMs are still detected (just without the richer shard-progress signal).

## Recommended decision

**No action required.** Audit passed clean.

Optional improvement (P3): add `vm-zombie-watchdog-` as an explicit `None` entry in `VM_PREFIX_TO_BUCKET` with a comment
documenting the self-exemption pattern. Currently the exemption is via label rather than dict entry, which is correct
but makes the registry less self-documenting. Not review-blocking.
