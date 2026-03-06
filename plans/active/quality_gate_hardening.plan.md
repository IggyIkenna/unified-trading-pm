# Plan: Quality Gate Hardening — Cloud Agnostic + Protocol Enforcement

**ID:** quality_gate_hardening
**Status:** active
**Day:** 2–3 (runs alongside #2a and #2b)
**Scope:** All 59 repos per workspace manifest (`unified-trading-system-repos.code-workspace`) — quality gate scripts, codex, violations audit. Note: recount before each sweep; repo count may grow.
**Prerequisite:** None — can run in parallel with #2a and #2b

---

## Problem

STEP 5.10 and 5.11 were added to the quality gate TEMPLATES as soft-warning checks.
But:

1. Not all repos have a quality-gate script that runs these templates
2. The checks currently log violations but may not hard-fail the build (needs verification)
3. No baseline audit exists — existing violations haven't been catalogued and fixed
4. The gates aren't wired into `quickmerge.sh` D-level hardening flags
5. No repo-level `QUALITY_GATE_BYPASS_AUDIT.md` tracks approved exceptions

Without this hardening, the architecture rules from plans #2a + #2b are guidelines-only.
After this hardening, any PR that introduces a direct `google.cloud` import in a service
will fail CI immediately.

---

## What to Block (Hard-Fail)

### Category A — Direct cloud SDK imports (STEP 5.10)

Pattern: `^from google\.cloud|^import boto3|^import botocore`
Allowed ONLY in:

- `unified_cloud_interface/providers/` (UCI provider implementations)
- `unified_cloud_interface/cache.py` (AsyncRedisProvider)
- Terraform files (by definition not Python)
- `# noqa: UCI-direct-sdk` comment for approved exceptions tracked in QUALITY_GATE_BYPASS_AUDIT.md

### Category B — Protocol-leaking symbols in service code (STEP 5.11)

Pattern: `CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService`
Allowed NOWHERE in service code (no exceptions).
Library code in UTL may have these during transition — tracked with TODO comments.

### Category C — Direct redis imports outside UCI (STEP 5.10 extension)

Pattern: `^import redis` (not `from unified_cloud_interface`)
Allowed ONLY in `unified_cloud_interface/cache.py`

### Category D — os.environ violations (existing STEP 5.9)

Pattern: `os\.getenv|os\.environ`
Allowed ONLY in files with `# config-bootstrap` comment or UCI factory.py

---

## Todos

### P0 — Audit existing violations (run scanners, produce report)

- [ ] `p0-scan-category-a` — Scan all 52 repos for Category A violations; produce `CLOUD_SDK_VIOLATIONS.md`
- [ ] `p0-scan-category-b` — Scan all 52 repos for Category B violations; produce list in same file
- [ ] `p0-scan-category-c` — Scan for direct redis imports outside UCI
- [ ] `p0-scan-category-d` — Re-run os.environ scan (baseline from phase0); confirm current state

### P1 — Fix all violations found in P0

- [ ] `p1-fix-category-a` — Remove/replace all direct cloud SDK imports found (per #2a guidance)
- [ ] `p1-fix-category-b` — Remove/replace all protocol-leaking symbols found (per #2b guidance)
- [ ] `p1-fix-category-c` — Replace direct redis imports with UCI AsyncRedisProvider or RedisProvider
- [ ] `p1-baseline-approved` — Any violations that CANNOT be fixed yet → add `# noqa: UCI-direct-sdk` with reference to tracking TODO in QUALITY_GATE_BYPASS_AUDIT.md

### P2 — Harden gate scripts (hard-fail on new violations)

- [ ] `p2-verify-exit-codes` — Verify all 4 gate scripts (`service-template`, `library-template`, `codex-compliance-snippet`, `template`) exit with code 1 when STEP 5.10/5.11 fail, not just set FAIL=1
- [ ] `p2-quickmerge-d3` — Ensure STEP 5.10+5.11 are included in quickmerge.sh D3+ hardening (i.e., fail quickmerge at D3 or above if cloud SDK imports detected)
- [ ] `p2-per-repo-scripts` — For repos that don't have a per-repo `scripts/quality-gate.sh`, ensure it sources the template (or add them)
- [ ] `p2-codex-readme` — Update `codex/06-coding-standards/README.md` TL;DR to document STEP 5.10 + 5.11 as hard gates

### P3 — QUALITY_GATE_BYPASS_AUDIT.md

- [ ] `p3-bypass-audit-file` — Create `QUALITY_GATE_BYPASS_AUDIT.md` in workspace root documenting:
  - Any approved `# noqa: UCI-direct-sdk` exceptions with expiry dates
  - Repos that currently fail gates with a fix deadline
  - Tracking TODOs for violations that need plan items before fix
- [ ] `p3-bypass-audit-update` — After P1 fixes, update the audit file to reflect zero unapproved violations

### P4 — CI enforcement

- [ ] `p4-cloudbuild-gate` — For repos with `cloudbuild.yaml`, add a quality-gate step that runs STEP 5.10+5.11 and blocks the build
- [ ] `p4-buildspec-gate` — For repos with `buildspec.aws.yaml`, add equivalent check in `pre_build` phase
- [ ] `p4-github-action` — Ensure any GitHub Action workflows that run tests also run the quality gate check

---

## Violation Tracker (populated after P0 scan)

To be filled after P0 scan completes. Format:

```
| Repo | File | Category | Violation | Fix | Status |
```

---

## Acceptance Criteria

1. `rg "^from google\.cloud|^import boto3|^import botocore" --type py --glob '!.venv*' --glob '!unified_cloud_interface/providers/**' --glob '!unified_cloud_interface/cache.py' .` → 0 results or all have `# noqa: UCI-direct-sdk`
2. `rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" --type py --glob '!.venv*' --glob '!tests' services/` → 0 results
3. All 52 repos have a working quality gate script that runs STEP 5.10+5.11
4. QUALITY_GATE_BYPASS_AUDIT.md exists with zero unapproved exceptions
5. CI (Cloud Build + CodeBuild) fails on Category A/B violations in any PR
