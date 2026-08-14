---
doc_type: issue
title: "immediately-safe ~40 DELETE cohort — 5 of 9 named items reclassified NOT-safe on live re-verification"
status: open
asset_group: [infrastructure]
created: "2026-08-14"
author: slot-15 [infra worker]
assigned_vm: planning
source:
  [
    /plans/active/infra_satellite_ao_dispatch_batch16_2026_08_13.md,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
    /plans/audit/results/repo_scripts_characterization_2026_06_18.md,
  ]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/bucket_estate_consolidation_closeout_2026_07_24.md,
  ]
summary:
  '`infra_satellite_ao_dispatch_batch16_2026_08_13.md`''s Delete-execution todo named 9 concrete items as the
  "unconditionally safe" sub-list (UI `.tsx.bak` splitters/codemods, done deployment-service ...'
nature: process
stage: [meta]
repos:
  [unified-trading-pm, unified-trading-system-ui, deployment-service, unified-trading-library, system-integration-tests]
scope: [engineer, admin]
tags: [script-lifecycle, stale-reclassification, script-homes]
execution_scope: orchestrator-agent
priority: P2
parent_epic: infrastructure_master
resolved_by:
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

# "immediately-safe ~40" DELETE cohort — 5 of 9 named items reclassified NOT-safe

## What I found

`infra_satellite_ao_dispatch_batch16_2026_08_13.md`'s Delete-execution todo named 9 concrete items as the
"unconditionally safe" sub-list (UI `.tsx.bak` splitters/codemods, done deployment-service bucket migrations, the 5 dead
checkers), quoting `repo_scripts_governance_audit_2026_06_18.md`'s parenthetical verbatim. Live re-verification (git
history, CI-workflow grep, cloudbuild.yaml, and each script's own `Delete-when:` lifecycle marker) found the
"unconditionally safe" framing is now WRONG for 5 of the 9 — the 2026-06-18 audit is ~2 months stale and several scripts
have since gained real callers or explicit lifecycle markers contradicting the DELETE classification.

**Executed as genuinely safe (this session):**

- unified-trading-system-ui: deleted `build-deployment-details-views.py`, `generate-deployment-split.py`,
  `split-deploy-form.py`, `split-deployment-components.py` — all four read a hardcoded, now-nonexistent
  `/home/hk/.../*.tsx.bak` path (confirmed zero `.tsx.bak` files anywhere in the repo); their split output
  (`components/ops/deployment/details/`, `components/ops/deployment/form/`) already exists and is stable.
  `unified-trading-system-ui@181ae65d8f`.
- market-tick-data-service: fixed (not deleted — it's a stale pointer inside a live QG script, not a standalone dead
  checker) the `quality-gates.sh:278` SSOT citation from the never-existent `_migrate_tradfi_hyphen_rewriter.py` to the
  real `migrate_tradfi_to_hive.py`. `market-tick-data-service@d6ca0a67`.
- unified-api-contracts `check_schema_organization.py`: already deleted upstream (commit `156c1eca`, "delete
  DELETE-class docs, fix residual mirror refs") — no action needed, checkbox-mirror only.

**NOT executed — reclassified, needs its own decision, NOT "unconditionally safe":**

1. **unified-trading-library `scripts/check-ruff-versions.sh`** — is CI Step 0 in `cloudbuild.yaml` ("Step 0:
   check-ruff-versions", confirmed in `docs/CLOUD_BUILD_TRIGGER_SETUP.md` + the script's own header) and self-declares
   `# Lifecycle: permanent` / `# Delete-when: NA`. The 2026-06-18 audit's "checks a retired v1 workflow path"
   observation is still true (degrades to `NOT_FOUND` for that one axis) but the script itself is live production CI
   tooling, not dead.
2. **system-integration-tests `scripts/check-sit-readiness.py`** — actively invoked from
   `.github/workflows/smoke-test-gate.yml:417` with an explicit
   `--codex-path ../unified-trading-pm/codex/10-audit/repos` override (the caller already worked around the script's
   stale hardcoded default). Self-declares `# Lifecycle: permanent` / `# Delete-when: NA`.
3. **deployment-service `scripts/aggregate_instruments.py`** — self-declares `# Lifecycle: oneoff` /
   `# Delete-when: after prod-run verified + GCS orphan-sweep=0`. No evidence found that the orphan-sweep ran; no
   confirmed live `--operation aggregate` on instruments-service's CLI to point to as the completed migration.
4. **deployment-service bucket-migration scripts** (`migrate-flat-to-env-tiered.sh`, `archive-flat-buckets.sh`,
   `aws/migrate-bucket-names-unified-to-canonical.sh`, `aws/migrate-defi-buckets-prod-to-prd.sh`) — all four
   self-declare the same `Delete-when: after prod-run verified + GCS orphan-sweep=0` marker.
   `bucket_estate_consolidation_closeout_2026_07_24.md` (2026-07-25 entry) explicitly confirms the sweep was **never
   run**: "left the actual delete-vs-keep decision against the Delete-when condition (orphan-sweep=0) for a dedicated
   sweep, since I didn't run one this session." Two of the four additionally carry a STATUS note marking them a
   "historical record," which is evidence of completion but not the orphan-sweep the marker itself requires.
5. **unified-trading-system-ui codemods** (general-purpose, NOT scoped to a single now-missing `.tsx.bak` the way the 4
   executed splitters were): `codemods/migrate_page_headers.py` — live grep found 20+ `app/**/page.tsx` files still
   carrying the raw legacy `<h1>`+`text-muted-foreground <p>` header block without a `PageHeader` import (its own
   `Delete-when: ...no legacy headers remain` is unmet); `codemods/replace-loader2-spinner.py` — `Loader2` is still
   directly used in 3 files under `app/(ops)/admin/` (its own `Delete-when: ...no Loader2 remain` is unmet);
   `dedupe-openapi-operation-ids.py` — `context/api-contracts/openapi/unified-trading-system.openapi.json` currently has
   7 duplicate `operationId` values (its own `Delete-when: ...no duplicate ids in schema` is unmet) — though it's
   unconfirmed whether that specific file is the "merged spec" the script's typegen pipeline actually consumes
   (`lib/registry/openapi.json` has zero duplicates).

## Why it matters

The source plan's own framing ("unconditionally safe, distinct from the campaign-gated cohort") is stale for targets
whose `Delete-when` conditions are objectively unmet right now, and two items that gained live CI callers since the June
audit. Deleting any of these 5 items on the strength of the June characterization alone would have been a real
regression (breaking Cloud Build / smoke-test-gate CI) or premature (data-migration scripts whose completion gate nobody
has actually verified).

## Recommended decision

- [ ] [SCRIPT] P3. Update `repo_scripts_governance_audit_2026_06_18.md`'s "Immediately-safe DELETE cohort" section to
      strike `unified-trading-library check-ruff-versions.sh` and `system-integration-tests check-sit-readiness.py` from
      the DELETE list — both are live CI tooling with `Lifecycle: permanent` markers, not dead checkers. Repo:
      unified-trading-pm.
- [ ] [AUDIT] P3. Run the dedicated GCS orphan-sweep the closeout plan deferred (per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) against the 4 deployment-service bucket-migration
      scripts' targets + `aggregate_instruments.py`'s targets; on orphan-sweep=0, git rm all 5 citing the sweep
      evidence. Repo: deployment-service. [OPERATOR] — GCS delete-adjacent verification.
- [ ] [CODE] P3. Re-run `codemods/migrate_page_headers.py` against the ~20 still-unmigrated `app/**/page.tsx` files (or
      confirm they're intentionally excluded, e.g. non-standard header shape) before re-evaluating its `Delete-when`
      gate. Repo: unified-trading-system-ui.
- [ ] [CODE] P3. Replace the 3 remaining direct `Loader2` + `animate-spin` usages under `app/(ops)/admin/` with
      `<Spinner />` before re-evaluating `codemods/replace-loader2-spinner.py`'s `Delete-when` gate. Repo:
      unified-trading-system-ui.
- [ ] [CODE] P3. Confirm which openapi json file actually feeds `openapi-typescript` (likely
      `lib/registry/openapi.json`, already duplicate-free) vs. the 7-duplicate
      `context/api-contracts/openapi/unified-trading-system.openapi.json`; if the latter is a genuine typegen input, run
      `dedupe-openapi-operation-ids.py` against it before deleting it. Repo: unified-trading-system-ui.

## Progress Log

- **2026-08-14 (slot 15)**: Filed during `infra_satellite_ao_dispatch_batch16_2026_08_13.md`'s Delete-execution todo.
  Executed the 4 genuinely-dead UI splitters + the MTDS pointer fix; deferred the 5 items above with evidence.
