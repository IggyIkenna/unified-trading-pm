---
title: Content-based breaking-detection — SIT triggers on real schema/API-contract change, not 0.x-minor
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: local-only
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
created: 2026-06-08
orchestrated_by: plans/active/cicd_contract_hardening_2026_06_01.md
related_plans:
  - plans/active/ci_local_qg_parity_2026_06_08.md
  - plans/active/staging_clean_start_and_stale_pr_hygiene_2026_06_08.md
source:
  - chat design session 2026-06-08 (operator + vm-planning)
---

# Content-based breaking-detection — SIT only on real breaking changes

> **Orchestrated by** `cicd_contract_hardening_2026_06_01.md`. **BUILD-TRACK PREREQUISITE that GATES the drain**
> (operator 2026-06-08: "Full now, then drain"). Ship this BEFORE the LDR→staging→main drain so the cascade runs on the
> correct gate from the first repo.

## Problem (what we found)

The "breaking" decision that locks staging + triggers SIT is **version-phase based, not content based**.
`update-repo-version.yml:131-139` locks on `bump_type == "major" OR is_breaking`, and `is_breaking` is set upstream by
`semver-agent` from the commit's semver class — a `feat!` marker **or any 0.x MINOR bump**. So **every `feat`-level
change to a 0.x lib (utl, uac) is "breaking"** → full cascade lock + SIT, even when nothing in the public contract
changed. A **docstring edit, an internal refactor, an added optional kwarg** all trip the heaviest gate. This is the
root of the slow cascade: SIT (the 30-min assembled cross-repo run) + the serialized lock fire on changes that cannot
break any consumer.

## Decision (operator, 2026-06-08)

**SIT triggers ONLY on a real breaking change** = an actual change to the **public API surface / schema / contract**
that affects how consumers import or use the symbol. **QG (`quality-gates-v2`) still runs on EVERY staging PR.** A
docstring / internal-only change is **not** breaking. Removed/renamed public symbol, changed signature, changed
Pydantic/dataclass/schema field, changed serialization/contract → breaking.

## Approach — reuse the API-diff that already exists

`semver-agent` already computes an **API diff for label validation** (it validates the declared bump label vs the actual
API change). The fix is to make the **SIT-trigger + cascade-lock key off that API-diff verdict**, not the `0.x-minor`
heuristic.

## Pre-audit

- [ ] [SCRIPT] P1. Read `system-integration-tests/.github/workflows/semver-agent.yml` + `update-repo-version.yml` +
      `sit-gate.yml`: find exactly where `is_breaking` is computed and where SIT is dispatched. Confirm whether
      semver-agent's API-diff is already a usable signal (griffe / public-symbol diff / UAC schema-cassette diff) or
      must be built. Document the real current source of `is_breaking`.

## Phase 1 — Content-based `is_breaking` (depends: Pre-audit)

- [ ] [SCRIPT] P1. Define the public-surface differ per repo type:
  - **Python libs (utl, services):** diff exported public symbols + signatures (e.g. `griffe`) between the promoted ref
    and the new ref; backward-incompatible removal/rename/signature-change → breaking; added-optional / internal /
    docstring → NOT breaking.
  - **UAC (contracts):** diff the schema/contract surface (cassette-schema-parity already exists) — field
    removal/rename/type-change/serialization-change → breaking.
- [ ] [SCRIPT] P1. Set `is_breaking` from the differ verdict (not version phase). `feat!` stays an explicit
      human-declared breaking override. A 0.x MINOR with no public-surface change → `is_breaking=false` → **no SIT, no
      cascade lock** → fast drain.

## Phase 2 — Gate SIT + lock on the new verdict (depends: Phase 1)

- [ ] [SCRIPT] P1. `update-repo-version.yml` / `sit-gate.yml`: lock staging + dispatch SIT **only** when
      `is_breaking == true` (real surface change) OR an explicit `feat!`/major. Non-breaking promotions go
      LDR→staging→main on QG-only (no SIT, no lock). **QG-v2 still required on every staging PR** (do not weaken that).
- [ ] [SCRIPT] P1. **Rule-11 fleet proof**: before flipping the gate, replay the new `is_breaking` against the last N
      fleet promotions and confirm it classifies the known-breaking ones as breaking and the docstring/internal ones as
      non-breaking — in the SAME change. Never "flip it and see what skips SIT."

## Success criteria

- A docstring-only / internal-refactor promotion to a 0.x lib → `is_breaking=false` → drains LDR→staging→main on QG
  alone, no SIT, no cascade lock (proven on a real consumer).
- A removed/renamed public symbol or changed schema field → `is_breaking=true` → SIT + lock fire (proven).
- QG-v2 still gates every staging PR.
- The fleet drain after this lands is QG-paced, not SIT-paced, for the non-breaking majority.

## Codex SSOT updates

`codex/08-workflows/ci-cd-flow.md` § "breaking = public-surface change, not version phase; SIT scope"; cross-link
`ci_local_qg_parity` (SIT = the assembled-invariant layer, now breaking-gated).
