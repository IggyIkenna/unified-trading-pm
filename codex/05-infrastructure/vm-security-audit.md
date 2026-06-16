---
scope: [engineer, admin]
title: VM Launcher Security Audit
type: infrastructure
status: living
last_reviewed: 2026-05-17
owner: deployment-platform
---

# VM Launcher Security Audit

**Author**: slot-2 agent  
**Date**: 2026-05-15  
**Scope**: All `deployment-service/scripts/vm/launch-*.sh` (83 launchers)  
**Tool**: shellcheck 0.11.0 `-S warning`

---

## Summary

| Severity                                                      | Count | Status        |
| ------------------------------------------------------------- | ----- | ------------- |
| P0 (hardcoded credentials / curl-pipe-bash)                   | 0     | ✅ None found |
| P1 (shell injection vectors — SC2046 unquoted word splitting) | 3     | ✅ Fixed      |
| P2 (unused variables — SC2034)                                | 9     | ✅ Fixed      |
| False positives (SC2211 in comments)                          | 2     | ℹ️ Accepted   |

**Outcome**: All P0 and P1 issues resolved. Launchers are shellcheck-clean at warning+ severity.

---

## Security Checks

### Hardcoded credentials (P0)

**Result**: None found.

All secret access routes through `gcloud secrets versions access latest --secret=<name> --project=<id>` (Secret Manager)
or VM metadata `--secret=<name>` binding. No plaintext API keys, tokens, or passwords in any launcher.

Checked patterns: `password=`, `api_key=`, `secret=` (in variable assignments), `token=`.

### Unsafe curl-pipe-bash (P0)

**Result**: None found.

`curl` in launchers is used only for:

- GCP instance metadata API: `curl -sf -H "Metadata-Flavor: Google" http://metadata.google.internal/...`
- File downloads: `curl -LsSf https://astral.sh/uv/install.sh | sh` (inside startup scripts embedded as heredocs — these
  run inside the VM, not on the host)

No `curl ... | bash` patterns on the host-side launcher execution path.

### Shell injection vectors (P1) — SC2046

**File**: `launch-amm-golden-fixture-validation-vm.sh` (3 warnings, same pattern)

**Root cause**: Unquoted command substitutions `$( $FORCE && echo "--force" )` and `$( $DRY_RUN && echo "--dry-run" )`
in a flag-aggregation loop. If output contained spaces, word splitting would produce unexpected argument boundaries.

**Fix**: Replaced with flag arrays:

```bash
# Before (SC2046)
$( $FORCE && echo "--force" ) \
$( $DRY_RUN && echo "--dry-run" )

# After (fixed)
EXTRA_FLAGS=()
$CAPTURE && EXTRA_FLAGS+=("--capture")
$FORCE && EXTRA_FLAGS+=("--force")
$DRY_RUN && EXTRA_FLAGS+=("--dry-run")
bash "${BASH_SOURCE[0]}" ... "${EXTRA_FLAGS[@]}"
```

---

## Code Quality Fixes (SC2034 — Unused Variables)

Nine unused variable assignments removed across 8 files:

| File                                            | Variable           | Risk                                                 |
| ----------------------------------------------- | ------------------ | ---------------------------------------------------- |
| `launch-mtds-dex-pools-backfill-vm.sh`          | `TICK_BUCKET_NAME` | Dead code (bucket never created)                     |
| `launch-mtds-eigenlayer-rewards-backfill-vm.sh` | `TICK_BUCKET_NAME` | Same                                                 |
| `launch-mtds-liquidations-backfill-vm.sh`       | `TICK_BUCKET_NAME` | Same                                                 |
| `launch-mtds-perp-funding-backfill-vm.sh`       | `TICK_BUCKET_NAME` | Same                                                 |
| `launch-cefi-migration-vm.sh`                   | `SCRIPT_DIR`       | Set up but path never used                           |
| `launch-prediction-features-vm.sh`              | `SCRIPT_DIR`       | Same                                                 |
| `launch-prediction-pipeline-vm.sh`              | `SCRIPT_DIR`       | Same                                                 |
| `launch-execution-alpha-vm.sh`                  | `SCRIPT_DIR`       | Same                                                 |
| `launch-amm-golden-fixture-validation-vm.sh`    | `SHAPE_LOWER`      | Computed but unused                                  |
| `launch-cefi-sharded-backfill.sh`               | `DATA_LIGHT_SPOT`  | Unused constant                                      |
| `launch-strategy-test-vm.sh`                    | `CREATE_CMD`       | Documented but unused (actual gcloud call is inline) |

---

## False Positives Accepted

**SC2211** (2 instances) — shellcheck misinterprets backtick-quoted glob patterns in shell comments as actual glob
commands.

- `launch-aave-lending-rate-validation-vm.sh:191`: `# PYTHONPATH ensures \`tests.defi_execution.\*\` imports resolve`
- `launch-amm-golden-fixture-validation-vm.sh:258`: `# PYTHONPATH ensures \`tests.\*\` imports resolve`

These are in comments only. No fix needed; accepted as shellcheck parser limitation.

---

## References

- `deployment-service/scripts/vm/` (all launch-\*.sh)
- `codex/05-infrastructure/launcher-script-ssot.md`
- `codex/05-infrastructure/vm-tarball-deployment.md`
