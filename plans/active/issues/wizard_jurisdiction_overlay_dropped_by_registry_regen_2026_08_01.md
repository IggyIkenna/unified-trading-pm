---
doc_type: issue
title: wizard-jurisdiction-filter.spec.ts genuinely broken — registry regen silently drops jurisdiction_overlay
summary: >-
  `generate_ui_reference_data.py` has no `extract_jurisdiction_overlay()` extractor, so the 2026-07-31 "regenerate
  ui-reference-data.json from UAC/UTL main" commit silently dropped the `jurisdiction_overlay` key — the Stage-A
  jurisdiction-select dropdown now renders with zero jurisdiction options, making the whole jurisdiction-filter feature
  inert. Confirmed via wizard_smoke_suite_pre_existing_failures_2026_07_28.md's triage (todo 1): reproducible
  deterministically in isolation, not a shared-host contention flake.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, unified-api-contracts, unified-trading-system-ui]
scope: [engineer]
tags: [ui, wizard, jurisdiction, registry-regen, ci-regen, playwright, smoke]
related:
  [
    /plans/archive/issues/wizard_smoke_suite_pre_existing_failures_2026_07_28.md,
    /plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md,
    /plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md,
  ]
created: 2026-08-01
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
resolved_by:
locked_by:
source: [
    "wizard_smoke_suite_pre_existing_failures_2026_07_28.md todo 1 triage session, 2026-08-01: full tests/smoke/ run\
    (--workers=1) reproduced `wizard-jurisdiction-filter.spec.ts` › 'US_CFTC jurisdiction blocks the known CeFi-perp\
    venue picklist at Stage E' failing deterministically (confirmed 2x in isolation with a warm dev server)",
  ]
execution_scope: orchestrator-agent
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md,
    unified-trading-pm/scripts/openapi/generate_ui_reference_data.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/jurisdiction_overlay.py,
    unified-trading-system-ui/lib/registry/jurisdiction-overlay.ts,
  ]
---

# wizard-jurisdiction-filter.spec.ts genuinely broken — registry regen silently drops jurisdiction_overlay

## What I found

While triaging the ~65 untriaged `tests/smoke/` failures tracked in
`wizard_smoke_suite_pre_existing_failures_2026_07_28.md` (todo 1), a clean `--workers=1` full run of
`unified-trading-system-ui`'s `tests/smoke/` (108 tests, 2026-08-01) reproduced exactly 4 failures. Three re-verified as
shared-host-contention / Next.js dev-mode cold-route-compile flakes (pass once the dev server / route is warm — no
action needed). The fourth is a **genuine, deterministic regression**:

`tests/smoke/wizard-jurisdiction-filter.spec.ts:135` — "US_CFTC jurisdiction blocks the known CeFi-perp venue picklist
at Stage E" fails every time (confirmed 2x in isolation against an already-warm dev server), with:

```
Error: page.selectOption: Test timeout of 30000ms exceeded.
  - waiting for locator('[data-testid="jurisdiction-select"]')
    - did not find some options
```

**Root cause**: `lib/registry/jurisdiction-overlay.ts` reads `JURISDICTIONS` from the generated
`lib/registry/ui-reference-data.json`'s `jurisdiction_overlay` key, falling back to an **empty array** when that key is
absent (`EMPTY_OVERLAY` in the same file). The key IS present in the version committed alongside the feature
(`unified-trading-system-ui@49a6fc9f`, 2026-07-28, "feat(wizard): Stage-A jurisdiction filter") — confirmed via
`git show 49a6fc9f:lib/registry/ui-reference-data.json`. It is **absent** as of `unified-trading-system-ui@dfbfff68`
("fix(registry): regenerate ui-reference-data.json from UAC/UTL main (registry-drift green)") — the very next commit to
touch this file. Confirmed: `generate_ui_reference_data.py` (this repo, `scripts/openapi/`) has **no
`extract_jurisdiction_overlay()` function at all** — zero references to
`jurisdiction_overlay`/`extract_jurisdiction_overlay` anywhere in this repo's Python. So `49a6fc9f`'s json must have
carried the key from a hand-edit (or a since-reverted local extractor) rather than the real generator, and the very next
automated regen (`dfbfff68`) silently wiped it because the generator overwrites the whole file from a fixed field list
that never included this key.

The underlying UAC registry is real and intact — `unified_api_contracts.internal.architecture_v2.jurisdiction_ overlay`
(`Jurisdiction`, `KNOWN_VENUE_IDS`, `JURISDICTION_VENUE_POLICIES`, `allowed_venues_for_jurisdiction()`) — this is purely
an extraction gap in the UI-facing regen pipeline, not a data-loss issue upstream.

Effect on the product: the Stage-A "Investor entity jurisdiction" `<select>` on `/wizard` currently renders with only
the "Not specified — no filtering" option — a user can never actually pick a jurisdiction, so the whole
jurisdiction-based venue-filtering feature (`capability_wizard_gap_discovery_2026_06_11.md` P2 item) is silently inert
in the current build, even though the feature code (`applyJurisdictionFilter()`, `isVenueAllowed()`, the Stage-E
disabled/reason rendering) is all still present and correct.

## Why it matters

This regressed a shipped, tested feature (that plan doc's own evidence line records "2/2 passed" at ship time) without
any code change to the feature itself — purely a side effect of an unrelated registry-drift regen. It will silently
re-break again on every future `generate_ui_reference_data.py` run unless the extractor is added, since the script has
no notion this key should exist. `check_openapi_drift.py` / the registry-drift CI gate would not catch this either,
since a MISSING key that was never in the generator's schema doesn't drift from anything — it's simply never produced.

## Recommended decision

- [x] ✅ [BACKEND] P2. Add `extract_jurisdiction_overlay()` to
      `unified-trading-pm/scripts/openapi/generate_ui_reference_data.py`, mirroring the existing extractor pattern (e.g.
      `extract_sports_bookmaker_registry()` / `extract_venue_data_availability()`): pull `Jurisdiction`,
      `KNOWN_VENUE_IDS`, `JURISDICTION_VENUE_POLICIES`, and `allowed_venues_for_jurisdiction()` from
      `unified_api_contracts.internal.architecture_v2.jurisdiction_overlay`, and emit the same shape
      `lib/registry/jurisdiction-overlay.ts` already expects (`known_venue_ids`, `jurisdictions`, `policies`,
      `allowed_venues_by_jurisdiction`). Wire it into `main()` (numbered step ~22, alongside
      `archetype_capability_registry`) so it's produced on every regen going forward. Repo: unified-trading-pm. —
      unified-trading-pm@31b7cf457 (2026-08-02). Verified: `extract_jurisdiction_overlay()` exists (line 569), wired
      into `main()` step 22 (line 895), and imports/executes cleanly, producing 32 policies across 6 jurisdictions in
      the exact shape `jurisdiction-overlay.ts` expects (`known_venue_ids`/`jurisdictions`/`policies`/
      `allowed_venues_by_jurisdiction`) — confirmed `us_cftc` correctly resolves to an empty allowed-venue set.
- [x] ✅ [SCRIPT] P2. Re-run `generate_ui_reference_data.py`, commit the regenerated
      `unified-trading-system-ui/lib/registry/ui-reference-data.json` with the `jurisdiction_overlay` key restored, and
      verify `npx playwright test --project=chromium tests/smoke/wizard-jurisdiction-filter.spec.ts` passes 2/2 again.
      Repo: unified-trading-system-ui + unified-trading-pm. — unified-trading-system-ui@097e1d64 (2026-08-02). Verified:
      `jurisdiction_overlay` key present with the expected shape (`known_venue_ids`/`jurisdictions`/`policies`/
      `allowed_venues_by_jurisdiction`); `wizard-jurisdiction-filter.spec.ts` — 2/2 passed.

## Progress Log

- 2026-08-02 (slot 4): Todo 1 checkbox flip — the extractor was already shipped by another slot
  (`unified-trading-pm@31b7cf457`, slot-10) ahead of this task's dispatch, but its plan checkbox was never flipped.
  Verified the shipped code end-to-end (import + execute `extract_jurisdiction_overlay()` in isolation: 32 policies, 6
  jurisdictions, correct shape, `us_cftc` allowed-set empty as expected) and flipped the checkbox to reflect reality.
  Todo 2 (regen `ui-reference-data.json` + verify the playwright spec) is still open — the last regen
  (`unified-trading-system-ui@19e849c2`, 2026-08-02 16:33 UTC) predates the extractor commit (17:17 UTC), so the JSON
  still lacks the `jurisdiction_overlay` key. That is a separate backlog task
  (`wizard_jurisdiction_overlay_dropped_by_registry_regen-002`, still queued) — not done here.
- 2026-08-02 (slot 10): Todo 2 done. Regenerated `ui-reference-data.json` via `generate_ui_reference_data.py` (targeted
  merge — only `jurisdiction_overlay` added, every other key byte-identical to the committed baseline, so unrelated
  `service_port_registry` drift stayed out of scope); shipped `unified-trading-system-ui@097e1d64`. Verified
  `wizard-jurisdiction-filter.spec.ts` 2/2 passed against the regenerated registry. Both todos now done, doc unlocked —
  archival-eligible per the plan-completion-and-archival-discipline HARD RULE.
