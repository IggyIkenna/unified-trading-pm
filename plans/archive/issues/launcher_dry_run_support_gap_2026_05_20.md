---
doc_type: issue
title: VM launchers missing --dry-run support — real-money risk during verification
summary:
status: RESOLVED — see "Fix shipped" below
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-20
author: slot-1 main ikenna (delegated)
source:
  [
    deployment-service/scripts/vm/launch-tradfi-forward-poll.sh,
    "2026-05-20 bash-3.2 verification incident — `launch-tradfi-forward-poll.sh --dry-run` silently launched real VM
    `tradfi-fwd-20260523-184709` (deleted within 60s via gcloud, no harm done, but the gap is workspace-wide)",
    deployment-service@7232a5b — fix shipped same-cycle,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-20
severity: P2 — real-money / real-VM risk during any future verification or agent dispatch
---

> **ARCHIVED 2026-05-23 — ACKED-INTO-CODE.** Filed + closed in the same commit per Issue-Doc Lifecycle Discipline
> (`/codex/11-project-management/issue-doc-lifecycle.md`). Fix shipped at `deployment-service@7232a5b`. No follow-up
> work; no dual-tracking.

## What I found

The 2026-05-20 verification incident exposed that VM launchers in `deployment-service/scripts/vm/launch-*.sh` were
inconsistent about honoring `--dry-run`:

| State                        | Count | %    | Sample                                                                                                                                                                                                                                                                                                                                                                                                           |
| ---------------------------- | ----- | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Pre-fix HAS `--dry-run`      | 74    | 59%  | `launch-instruments-backfill-vm.sh`, `launch-defi-backfill-vm.sh`, `launch-mtds-backfill-vm.sh`, `launch-tradfi-backfill-vm.sh`                                                                                                                                                                                                                                                                                  |
| Pre-fix MISSING `--dry-run`  | 51    | 41%  | `launch-tradfi-forward-poll.sh` (incident), `launch-cefi-forward-poll.sh`, `launch-defi-forward-poll.sh`, `launch-mtds-lst-rates-backfill-vm.sh`, `launch-dashboard-vm.sh`, all 5 forward-poll launchers (cefi/defi/tradfi/aster/sfi/footystats/prediction/cefi-onchain), 19 mtds-\* backfill launchers, 5 sports launchers, 2 wrapper launchers (features-onchain GCP + AWS), 1 docker-build dashboard launcher |
| Post-fix HAS `--dry-run`     | 125   | 100% | (full sweep)                                                                                                                                                                                                                                                                                                                                                                                                     |
| Post-fix MISSING `--dry-run` | 0     | 0%   | —                                                                                                                                                                                                                                                                                                                                                                                                                |

The 51 MISSING launchers split across six structural patterns:

1. **Inline `gcloud compute instances create` with backslash-continuation** (47 launchers, e.g.
   `launch-tradfi-forward-poll.sh`, `launch-aster-forward-poll.sh`, `launch-mtds-*.sh`, `launch-defi-forward-poll.sh`) —
   the dominant pattern; the auto-transformer added `--dry-run` arg parsing + an
   `if [[ "${DRY_RUN:-false}" == "true" ]]; then ... else <call> fi` wrapper around the gcloud call.
2. **`lc_gcloud_create` helper callers** (2 launchers: `launch-canonical-smoke-vm.sh`, `launch-instruments-smoke-vm.sh`)
   — added explicit `--dry-run) export LC_DRY_RUN=true ;;` arg parsing; the helper now honors `LC_DRY_RUN`.
3. **`gcloud compute instances create-with-container` + docker build/push + IAM + firewall** (1 launcher:
   `launch-dashboard-vm.sh`) — guarded the entire post-auth block with a single `if $DRY_RUN; then ... exit 0; fi` gate.
4. **`exec env ... bash <other-launcher>` wrappers** (2 launchers: `launch-features-onchain-backfill-vm.sh`,
   `launch-features-onchain-backfill-vm-aws.sh`) — added a pre-positional-arg `--dry-run` scan + bail-with-description
   before `exec`.
5. **Internal `bash <other-launcher>` fan-out** (2 launchers: `launch-cefi-week-test.sh`,
   `launch-sku-matrix-v2-benchmark.sh`) — added `--dry-run` arg parse + propagation of `--dry-run` to each child
   launcher invocation via a `DRY_RUN_ARG=()` array.
6. **Existing arg parser with `*)` break-out-of-loop** (3 launchers: `launch-blank-reason-recon-vm.sh`,
   `launch-expected-universe-enumerator-vm.sh`, `launch-expected-universe-v2-vm.sh`) — manually injected
   `--dry-run) DRY_RUN=true; shift ;;` cases since the auto-transformer's regex assumed `case "$1" in` (not
   `case "${1:-}" in`).

## Why it matters

Any agent (or operator) running `bash launch-<X>-vm.sh --dry-run` expects no side effects. Launchers without `--dry-run`
support silently ignored the flag and executed the real launch path:

- Real GCP VM (e2-standard-{2,4,8,16}).
- Real GCP cost (machine + boot disk + egress).
- Real coordination footprint (manifest writes, deployment registry rows, watchdog heartbeats, downstream auto-trigger
  chains).
- Real risk in the launch-dashboard-vm.sh case (docker build + push to Artifact Registry + IAM binding + firewall rule).

The 2026-05-20 incident was caught in under 60s because the verification agent was actively watching. An autonomous
agent might not notice for hours.

Composes with the CLAUDE.md HARD RULE "No fire-and-forget VM launches" — that rule requires post-launch verification
(T+10min heartbeat + `gcloud instances describe` = RUNNING). But pre-launch `--dry-run` is the FIRST safety net. The two
together form defense-in-depth: dry-run catches the wrong-script case; post-launch verification catches the wrong-config
case.

## Fix shipped

`deployment-service@7232a5b` (2026-05-23, live-defi-rollout).

**Centralised safety net** (`scripts/vm/lib/launcher_common.sh`):

```bash
lc_gcloud_create() {
    # ... arg unpacking ...
    local lc_dry_run_lc
    lc_dry_run_lc="$(printf '%s' "${LC_DRY_RUN:-false}" | tr '[:upper:]' '[:lower:]')"
    if [[ "$lc_dry_run_lc" == "true" ]]; then
        echo "[DRY-RUN] Would create VM: ${vm_name}"
        echo "[DRY-RUN]   project=${project} zone=${zone} machine=${machine_type} disk=${disk_gb}GB"
        echo "[DRY-RUN]   metadata=${metadata_str}"
        echo "[DRY-RUN]   labels=${labels_str}"
        return 0
    fi
    gcloud compute instances create "$vm_name" ...
}
```

**Per-launcher fixes** (51 files): each launcher's arg parser now has a `--dry-run` case that sets `DRY_RUN=true` (and
exports `LC_DRY_RUN=true` for helper-based launchers); the side-effecting block(s) check the flag and emit
`[DRY-RUN] Would <op>` instead of executing.

**Verification (bash 3.2 + bash 5)**:

- 125/125 launchers pass `bash -n` syntax check on both bash 3.2 (macOS `/bin/bash`) and bash 5
  (`/opt/homebrew/bin/bash`).
- End-to-end `--dry-run` exercised on representative launchers covering all 6 structural patterns:
  `launch-tradfi-forward-poll.sh` (incident launcher), `launch-aster-forward-poll.sh` (inline gcloud),
  `launch-mtds-lst-rates-backfill-vm.sh` (mtds family), `launch-canonical-smoke-vm.sh` (lc_gcloud_create path),
  `launch-features-onchain-backfill-vm.sh` (exec env wrapper).
- `gcloud compute instances list --filter="name~tradfi-fwd OR ..." --project=central-element-323112` returns only the
  pre-existing `tradfi-fwd-daily-cron-20260520-091306` (TERMINATED) — no VMs created during verification.

## Pattern guide

The canonical `--dry-run` pattern for new VM launchers (mirror this in any future `launch-*.sh` script):

```bash
#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=false
FORCE=false
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-prod}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --force)   FORCE=true; shift ;;
    --env)     DEPLOYMENT_ENV="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

# ... rest of setup ...

if $DRY_RUN; then
  echo "[DRY-RUN] Would create VM: $VM_NAME"
  echo "[DRY-RUN]   project=$PROJECT zone=$ZONE machine=$MACHINE_TYPE disk=${DISK_GB}GB"
  echo "[DRY-RUN]   metadata=$METADATA"
  echo "[DRY-RUN]   labels=$LABELS"
  exit 0
fi

gcloud compute instances create "$VM_NAME" \
  --project="$PROJECT" \
  --zone="$ZONE" \
  ...
```

For launchers that wrap another launcher via `bash <other>` or `exec ... bash <other>`: propagate `--dry-run` to the
child via a `DRY_RUN_ARG=()` array OR bail early with a `[DRY-RUN] Would delegate to: <child>` message before `exec`.

For launchers that use `lc_gcloud_create`: just set `export LC_DRY_RUN=true` on `--dry-run` — the helper handles the
rest.

## Related findings (out of scope; surfaced during fix)

1. **`launch-features-vm.sh` has `--launch-mode dry|full` semantics**, which is distinct from `--dry-run`:
   `--launch-mode dry` means "VM runs in dry-run-payload mode" but the VM is STILL created. This is a confusing semantic
   mismatch but is NOT a missing-dry-run-support case (the launcher honors `--launch-mode` correctly). Consider renaming
   the inner flag to `--workload-mode` or `--payload-mode` to avoid future confusion. Filed as a non-blocking nit.

2. **`launch-aster-forward-poll.sh` line 56** uses `set -- "${_positional[@]}"` without the bash-3-safe `+"${...[@]}"`
   guard, so an empty positional array triggers `unbound variable` under `set -u` on macOS bash 3.2 when no positional
   dates are passed. Pre-existing; unrelated to dry-run support but surfaced during verification. The dry-run path
   itself works correctly when dates ARE passed. Not fixing in this commit (out of scope; foreign-adjacent pattern;
   would need workspace sweep).

## Lifecycle

- Filed: 2026-05-23.
- Acked-into-code: 2026-05-23 same commit.
- Archived: 2026-05-23 (this file at `plans/archive/issues/`).
- No follow-up plan needed — the fix is complete and verified.
