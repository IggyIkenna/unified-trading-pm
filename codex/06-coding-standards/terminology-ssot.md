---
doc_type: codex-ssot
title: Terminology SSOT
summary: >-
  UI terminology SSOT — every user-facing strategy-system label MUST come from the TERMS.* constants in
  lib/architecture-v2/terminology.ts, never inline literals; locks "asset group" (not "asset class"), CeFi/DeFi casing,
  catalogue-level names, and access-badge labels; includes the rename/add-term procedures.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [terminology, ui, strategy, defi, cefi]
related:
  [/codex/06-coding-standards/strategy-display-conventions.md, /codex/04-architecture/commercial-service-families.md]
created: 2026-04-25
authoritative_for: [UI terminology constants SSOT (TERMS.* user-facing labels)]
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Terminology SSOT

> **Status:** canonical (2026-04-25) **Owner:** UI + Architecture **SSOT for:**
> `unified-trading-system-ui/lib/architecture-v2/terminology.ts`.

Every user-facing label that names a strategy-system concept MUST come from the `TERMS.*` constants in
[`lib/architecture-v2/terminology.ts`](../../../unified-trading-system-ui/lib/architecture-v2/terminology.ts), not be
inlined as a string literal.

This prevents drift like:

- "DeFi/DeFi" mis-label on strategy-family chips (caught + fixed 2026-04-25 via the strategy-family glossary entry).
- "asset class" / "asset group" inconsistency (renamed find/replace 2026-04-25; constant added to lock the canonical
  form).

---

## §1 — Canonical terms

| Constant key                                                                 | Canonical user-facing label                      | Where it appears                                             |
| ---------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------ |
| `PRIMARY_CATEGORY`                                                           | "primary execution category"                     | Top-level catalogue filter, questionnaire                    |
| `ASSET_GROUP`                                                                | "asset group"                                    | Trading scope filters, mandates, reports — NOT "asset class" |
| `STRATEGY_FAMILY`                                                            | "strategy family"                                | Catalogue level 2, IM reporting filter                       |
| `STRATEGY_ARCHETYPE`                                                         | "strategy archetype"                             | Catalogue level 3, terminal entry                            |
| `STRATEGY_INSTANCE`                                                          | "strategy instance"                              | Catalogue level 4, slot label rendering                      |
| `CATALOGUE` / `ENVELOPE`                                                     | "strategy catalogue" / "strategy envelope"       | Page titles, navigation                                      |
| `BESPOKE` / `CUSTOM_BUILD`                                                   | "bespoke" / "custom build"                       | Bespoke row CTAs                                             |
| `FILTER_CATEGORY` / `FILTER_FAMILY` / `FILTER_ARCHETYPE` / `FILTER_INSTANCE` | "Category" / "Family" / "Archetype" / "Strategy" | Filter dropdown labels                                       |
| `FILTER_ALL`                                                                 | "All"                                            | "Show All" option                                            |
| `ACCESS_TERMINAL_AND_REPORTS`                                                | "Available for terminal & reports"               | Access badge                                                 |
| `ACCESS_REPORTS_ONLY`                                                        | "Reports only"                                   | Access badge — locked-but-reportable                         |
| `ACCESS_LOCKED_VISIBLE`                                                      | "Locked — upgrade to access"                     | Access badge                                                 |
| `ACCESS_HIDDEN`                                                              | "Not available"                                  | Access badge                                                 |
| `TENOR_0DTE` / `WEEKLY` / `MONTHLY` / `QUARTERLY` / `LEAPS` / `MULTI`        | Tenor labels                                     | Vol archetype tenor selector                                 |

Plus helper functions:

- `formatCategory(category: string): string` — normalise CEFI/DEFI/etc. to CeFi/DeFi/etc.
- `formatTenor(tenor: string): string` — normalise `0dte` → `0DTE`, `multi-tenor` → `Multi-tenor`.

---

## §2 — Renaming a term

1. Update the value in [`terminology.ts`](../../../unified-trading-system-ui/lib/architecture-v2/terminology.ts).
2. Run `npm test` — visual snapshot tests catch any pages still using the old literal.
3. Update this doc with the new canonical label.
4. If the term appears in codex prose, ripgrep + replace.

---

## §3 — Adding a new term

1. Add to `TERMS` constant in `terminology.ts`. Use SCREAMING_SNAKE_CASE for the key, kebab-case-or-prose for the value.
2. Add to the table above.
3. Wire into consumers via `import { TERMS } from "@/lib/architecture-v2/terminology"`.

---

## §4 — Anti-patterns

- ❌ `<h1>Strategy Family</h1>` — should be `<h1>{TERMS.STRATEGY_FAMILY}</h1>`.
- ❌ `aria-label="Filter by asset class"` — should be `aria-label={`Filter by ${TERMS.ASSET_GROUP}`}` (or the constant
  directly).
- ❌ Hardcoded "DeFi" / "CeFi" — should be `formatCategory("DEFI")`.

The lint rule `no-hardcoded-terminology` (planned, P11.7 follow-up) will flag these.

---

## §5 — Cross-references

- DART UI plan:
  [`../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md`](../../plans/archive/dart_ui_strategy_filtering_and_onboarding_2026_04_24.plan.md)
  §Phase 11
- Glossary: [`../../../unified-trading-system-ui/lib/glossary.ts`](../../../unified-trading-system-ui/lib/glossary.ts)
  (in-app hover definitions, complementary to TERMS)
- Categories enum: `unified_api_contracts/internal/architecture_v2/enums.py::VenueCategoryV2`
