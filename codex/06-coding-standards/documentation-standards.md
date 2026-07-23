---
doc_type: codex-ssot
title: Documentation Standards
summary:
  Per-repo required-docs standard (S5) — service repos need 8 canonical docs, libraries 5, UIs 4 (WARN-only); a stub (≤3
  lines or only TODO) counts as missing; no hardcoded project-IDs/buckets in docs; and the S5.11 HARD RULE that repo
  docs link the codex SSOT rather than duplicating canonical content (stale repo-doc vs codex is review-blocking).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-ui, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [documentation-standards, ssot-audit, plan-hygiene, quality-gates, docspec]
related: [/codex/02-data/schema-governance.md, /codex/02-data/canonical-schema-groups.md]
created: 2026-03-27
authoritative_for: [per-repo required-docs set (S5), repo-docs-defer-to-codex rule]
referenced_by: [/codex/06-coding-standards/cursor-rules-system.md]
owner:
last_reviewed:
code_refs:
---

# Documentation Standards

Every repo in the unified trading system must maintain a canonical set of documentation files. Missing or stub docs (3
lines or fewer, or containing only "TODO") count as **missing** for audit purposes (S5.4) and block the documentation
gate in Phase 0.

---

## S5.1 — Service-Canonical Required Docs

All service repos (`*-service`, `*-api`, deployment-api, etc.) must contain:

| File                           | Purpose                                                               |
| ------------------------------ | --------------------------------------------------------------------- |
| `README.md`                    | Entry point: purpose, quickstart, links to other docs                 |
| `docs/ARCHITECTURE.md`         | Component diagram (text/ASCII), key classes/modules, data flows       |
| `docs/CONFIGURATION.md`        | Config class name, all fields with types and defaults, secrets list   |
| `docs/GCS_PATHS.md`            | Bucket name pattern, all path templates with variable descriptions    |
| `docs/DEPLOYMENT_GUIDE.md`     | Prerequisites, deployment steps, rollback procedure, health check URL |
| `docs/TESTING.md`              | How to run tests, coverage target, known exclusions                   |
| `docs/SCHEMA_VALIDATION.md`    | Schema location, validation approach, example pass/fail               |
| `QUALITY_GATE_BYPASS_AUDIT.md` | Every `# qg-bypass` exemption with owner, date, and rationale         |

**Note:** `docs/ARCHITECTURE.md` must live under `docs/` — not at the repo root. If a service has it at the root, move
it.

---

## S5.2 — Library-Canonical Required Docs

All library repos (`unified-*-interface`, `unified-trading-library`, `matching-engine-library`, etc.) must contain:

| File                           | Purpose                                                         |
| ------------------------------ | --------------------------------------------------------------- |
| `README.md`                    | Entry point: what the library provides, install, usage examples |
| `docs/ARCHITECTURE.md`         | Module structure, public API surface, extension points          |
| `docs/CONFIGURATION.md`        | Any config classes or env vars the library reads, with defaults |
| `docs/TESTING.md`              | How to run tests, coverage target, mock/fixture patterns        |
| `QUALITY_GATE_BYPASS_AUDIT.md` | Every `# qg-bypass` exemption with owner, date, and rationale   |

---

## S5.3 — UI-Canonical Required Docs (WARN only, not blocking)

All UI repos (`deployment-ui`, `*-dashboard`, etc.) should contain:

| File                       | Purpose                                                                   |
| -------------------------- | ------------------------------------------------------------------------- |
| `README.md`                | Entry point: purpose, local dev setup, env vars                           |
| `docs/ARCHITECTURE.md`     | Component structure, state management, API integration points             |
| `docs/DEPLOYMENT_GUIDE.md` | Build, deploy, CDN/hosting, rollback                                      |
| `docs/TESTING.md`          | How to run tests, coverage target, Playwright/Cypress setup if applicable |

---

## S5.4 — Stub Definition

A doc is a **stub** (counts as missing) if it:

- Has 3 lines or fewer, OR
- Contains only "TODO" or placeholder text, OR
- Has no real content (empty sections only)

### Minimum content per doc type

| Doc                    | Not a stub if it contains                                                   |
| ---------------------- | --------------------------------------------------------------------------- |
| `ARCHITECTURE.md`      | Purpose, component diagram (text or ASCII), key classes/modules, data flows |
| `CONFIGURATION.md`     | Config class name, all fields with types and defaults, secrets list         |
| `DEPLOYMENT_GUIDE.md`  | Prerequisites, deployment steps, rollback procedure, health check URL       |
| `GCS_PATHS.md`         | Bucket name pattern, all path templates with variable descriptions          |
| `SCHEMA_VALIDATION.md` | Schema location, validation approach, example pass/fail                     |
| `TESTING.md`           | How to run tests, coverage target, known exclusions                         |

---

## S5.5 — Placement Rules

- All docs except `README.md` and `QUALITY_GATE_BYPASS_AUDIT.md` live under `docs/`.
- `docs/` must be a directory, not a single file named `docs`.
- `QUALITY_GATE_BYPASS_AUDIT.md` lives at the repo root (not under `docs/`).

---

## S5.6 — No Hardcoded IDs in Docs

Docs must not contain hardcoded GCP project IDs, bucket names, or service account emails. Use placeholders:

| Forbidden pattern        | Replace with         |
| ------------------------ | -------------------- |
| `odum-trading-prod`      | `{project_id}`       |
| `gs://odum-trading-*`    | `gs://{bucket_name}` |
| `*@odum-trading-*.iam.*` | `{service_account}`  |

**Audit command:**

```bash
grep -rn "odum-\|trading-prod-\|trading-staging-" docs/ README.md 2>/dev/null
```

---

## S5.7 — Audit Script

```bash
#!/usr/bin/env bash
# Run from any service repo root
REQUIRED_SERVICE_DOCS=(
  "README.md"
  "docs/ARCHITECTURE.md"
  "docs/CONFIGURATION.md"
  "docs/GCS_PATHS.md"
  "docs/DEPLOYMENT_GUIDE.md"
  "docs/TESTING.md"
  "docs/SCHEMA_VALIDATION.md"
  "QUALITY_GATE_BYPASS_AUDIT.md"
)

for doc in "${REQUIRED_SERVICE_DOCS[@]}"; do
  if [ ! -f "$doc" ]; then
    echo "MISSING: $doc"
  elif [ "$(wc -l < "$doc")" -le 3 ]; then
    echo "STUB:    $doc"
  else
    echo "OK:      $doc"
  fi
done

# Hardcoded ID scan
grep -rn "odum-\|trading-prod-\|trading-staging-" docs/ README.md 2>/dev/null \
  && echo "WARNING: hardcoded project IDs found above" \
  || echo "OK: no hardcoded IDs"
```

---

## S5.8 — Priority Order for Gap Filling

When filling doc gaps, use this priority:

1. `docs/DEPLOYMENT_GUIDE.md` — highest audit risk; missing from core services
2. `docs/SCHEMA_VALIDATION.md` — required for data pipeline correctness
3. `docs/GCS_PATHS.md` — required before production data writes
4. `docs/TESTING.md` — required for onboarding and coverage audit
5. `docs/ARCHITECTURE.md` — required for any review or refactor
6. `docs/CONFIGURATION.md` — required for ops runbook

---

## S5.9 — Schema Contract Docs

Schema governance documentation lives in:

- **Canonical schema groups:** [02-data/canonical-schema-groups.md](/codex/02-data/canonical-schema-groups.md) — UAC
  (`unified_api_contracts.canonical`) = normalization outputs; UAC internal (`unified_api_contracts.internal`) =
  internal messaging contracts
- **Schema governance:** [02-data/schema-governance.md](/codex/02-data/schema-governance.md) — Validation integration
  point, DRY/SoC enforcement, STEP 5.12 quality gate
- **Schema contract audit:** `unified-trading-pm/plans/archive/schema_governance_full_audit.plan.md` — Full audit
  results for UAC normalization quality, UIC utilization, cross-contract deduplication

Service docs (`docs/SCHEMA_VALIDATION.md`) must reference the canonical schemas used, not redefine them.

---

## S5.11 — Repo docs defer to the codex SSOT (no duplication) — HARD RULE

> **Codified 2026-06-01.** Root cause of recurring stale-doc drift: the same canonical content is written **twice** —
> once in `unified-trading-pm/codex/` (the SSOT) and once in a repo's `docs/`. The two copies drift; the repo copy goes
> stale (e.g. the MTDS `GCS_PATHS.md` hyphen-partition + un-tiered-bucket drift, 2026-06-01). Generalises the S5.9
> schema principle ("reference, don't redefine") to **every** doc type.

**Contract.** `unified-trading-pm/codex/` is the single source of truth for all **canonical / cross-cutting** content
(architecture invariants, data/path/schema/bucket contracts, deployment flows, manifest semantics, coding standards). A
repo `docs/` file MUST carry **only repo-specific operational essentials** + a **link to the canonical codex SSOT** for
everything cross-cutting. **Never copy a codex table, contract, path template, or rule into a repo doc — link it.** When
canonical content changes, only the codex SSOT is edited; the repo link stays valid (zero repo-doc churn).

**Per-doc-type split** (what links to codex vs what stays repo-local):

| Repo doc                    | Link to codex SSOT (do NOT duplicate)                                                               | Keep in repo doc (repo-specific only)                            |
| --------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `README.md`                 | —                                                                                                   | purpose, quickstart, index of links (codex + repo docs)          |
| `docs/ARCHITECTURE.md`      | cross-cutting patterns → `codex/04-architecture/*`, `codex/03-services/*`                           | THIS repo's modules/classes/data-flows; engine/adapters/cli map  |
| `docs/CONFIGURATION.md`     | config patterns → `/codex/06-coding-standards/config-reloader-pattern.md`                           | THIS repo's config class + fields/defaults/secrets               |
| `docs/GCS_PATHS.md`         | bucket naming + hive layout → `/codex/02-data/per-asset-group-bucket-layouts.md`, `partitioning.md` | THIS repo's specific path templates + data_types                 |
| `docs/DEPLOYMENT_GUIDE.md`  | deploy flow → `/codex/08-workflows/deployment-flow.md`, `codex/05-infrastructure/*`                 | THIS repo's entrypoint, health URL, env vars, rollback specifics |
| `docs/TESTING.md`           | testing layers → `/codex/06-coding-standards/ui-testing-layers.md` + testing rules                  | THIS repo's test commands + fixtures                             |
| `docs/SCHEMA_VALIDATION.md` | schema governance → `/codex/02-data/schema-governance.md` (per S5.9)                                | which canonical schemas THIS repo uses                           |

**Redirect-doc template** (still substantive — clears the S5.4 stub bar):

```markdown
# <Doc Title> — <repo>

> **Canonical SSOT:** [<codex doc>](../../unified-trading-pm/codex/<path>). This file carries only <repo>-specific
> details. The cross-cutting rules/contracts/templates live in the codex SSOT above — **do not duplicate them here**; if
> this file disagrees with codex, codex wins.

## <repo>-specific <topic>

<the repo-local deltas only>
```

**Rules:**

- A required doc (S5.1/S5.2/S5.3) whose content is **entirely** canonical (no repo-specific delta) collapses to the
  redirect template pointing at its codex SSOT — it stays present (so the S5.1 audit passes) but stops duplicating.
- A **non-required** extra doc (onboarding dumps, person-named specs, `*_FEMI.md`, `SHAHRIYAR_*`, one-off strategy
  memos) that only duplicates codex is **deleted**; its unique repo-specific content (if any) migrates into the proper
  required doc or codex first, then the file is removed (git history is the rollback).
- **Stale repo doc vs codex = review-blocking.** Fix by deleting the duplicated repo content and linking codex — never
  by re-syncing two copies.
- Repo docs never hardcode canonical literals that have a resolver/SSOT (bucket names → `resolve_bucket_name()`, project
  IDs → `{project_id}`, per S5.6).

**Enforcement:** the consolidation rollout + per-repo registry is tracked in
`plans/active/issues/repo_docs_codex_ssot_consolidation_2026_06_01.md`.

---

## S5.10 — Enforcement

Phase 0 (`phase0_standards_enforcement.plan.md`) runs the audit script on all repos and produces a baseline gap table.
Phase 1 doc filling (`documentation_standards_enforcement.plan.md`) is blocked until Phase 0 baseline is established.

The documentation gate passes when:

- All service repos have all 8 required docs (no missing, no stub)
- All library repos have all 5 required docs (no missing, no stub)
- Zero docs contain hardcoded GCP project IDs or bucket names
- `docs/ARCHITECTURE.md` is under `docs/` (not root) in all repos
