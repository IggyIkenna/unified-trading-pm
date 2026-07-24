---
doc_type: plan
title: Marketing site — Phase 1 pre-audit manifest (tone / glossary / depth)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-20"
companion_to: marketing_site_restructure_2026_04_20.plan.md
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. Companion manifest to
> marketing_site_restructure_2026_04_20 (parent already unlocked d2aa8c42). Ready for archive. See
> `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors.

# Pre-audit manifest — marketing site tone + glossary + briefing depth

Companion to [marketing_site_restructure_2026_04_20.plan.md](marketing_site_restructure_2026_04_20.plan.md) Phase 1.
Built from a three-agent scan of `unified-trading-system-ui` public routes, briefings, and the codex `14-playbooks/`
SSOT on 2026-04-20. Consume in Phase 1; do not re-scan.

**Decisions still open:** M1-M10 from the parent plan Phase 0 remain unresolved. This manifest feeds the audit even
while decisions are pending — items below are independent of M1-M10 direction.

## 0. Auth state — clarification

User ask on 2026-04-20: "briefings should be user authentication."

**Current state: already gated.**
[components/briefings/briefing-access-gate.tsx:1-61](../../unified-trading-system-ui/components/briefings/briefing-access-gate.tsx#L1)
implements a light-auth code check against `NEXT_PUBLIC_BRIEFING_ACCESS_CODE`, with localStorage session persistence
under `odum-briefing-session`.
[app/(public)/briefings/layout.tsx:1-5](<../../unified-trading-system-ui/app/(public)/briefings/layout.tsx#L1>) wraps
every `/briefings/*` route. This matches
[authentication/light-auth-briefings.md](/codex/14-playbooks/authentication/light-auth-briefings.md) spec exactly — it
is deliberately NOT Firebase auth (too heavy for post-first-call prospects).

The "Sign-in required" badge on
[app/(public)/briefings/page.tsx:20-22](<../../unified-trading-system-ui/app/(public)/briefings/page.tsx#L20>) is
cosmetic and misleading — says "Sign-in required" but the gate is a single access code, not a user account.
**Recommended copy fix:** change badge to "Access code required."

If the user wants stronger auth (Firebase staging), that supersedes the codex spec and should be captured as decision M4
variant — per `light-auth-briefings.md` the intentional design is low-friction for warm prospects. Flag it as a
M4-adjacent decision before execution.

## 1. Route inventory (public shell)

24 public routes split across (a) React pages with inline copy, (b) pages rendering `public/*.html` via
`MarketingStaticFromFile`. Inventory at [/tmp/public-pages-audit.md](/tmp/public-pages-audit.md#L7) (persisted this
session, lines 7-42).

**Static HTML surfaces:** `homepage.html` / `platform.html` / `strategies.html` / `regulatory.html` / `signals.html` /
`firm.html` — copy changes here don't show in TSX grep; both surfaces need audit.

**Shared copy modules:**

- [lib/briefings/content.ts](../../unified-trading-system-ui/lib/briefings/content.ts) — `BRIEFING_PILLARS` array
- [components/shell/nav-copy.ts](../../unified-trading-system-ui/components/shell/nav-copy.ts) —
  `PLATFORM_MARKETING_NAV_LABEL` ("DART")
- [lib/marketing/load-marketing-static.ts](../../unified-trading-system-ui/lib/marketing/load-marketing-static.ts) —
  HTML loader

## 2. Tone flags — fix list with file:line

Ordered by severity. Every item cites the codex rule it violates (`_ssot-rules/02-tone-and-posture.md`,
`04-dart-commercial-axes.md`, `06-show-dont-show-discipline.md`, `09-rule-expansion-pattern.md`).

### Meta-commentary / internal-instruction voice (rule 02 violation)

| #   | File:line                                                                                                            | Current copy                                                                                                                | Fix                                                                                                                     |
| --- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| T1  | [briefings/[slug]/page.tsx:57](<../../unified-trading-system-ui/app/(public)/briefings/[slug]/page.tsx#L57>)         | "Book directly from the hero above or open the other briefings if two paths apply."                                         | Drop "from the hero above" — reader can see the page. Rephrase to state-of-offering, not navigation instruction.        |
| T2  | [briefings/[slug]/page.tsx:65](<../../unified-trading-system-ui/app/(public)/briefings/[slug]/page.tsx#L65>)         | "For the public marketing surface see odumresearch.com. For signed-in strategy catalogue and terminal access, use Sign in." | Drop the cross-site meta. Briefings prospect already knows how they got here.                                           |
| T3  | [lib/briefings/content.ts:55](../../unified-trading-system-ui/lib/briefings/content.ts#L55) (Platform pillar bullet) | "Signed-in Platform reuses the same identity as Investment management; navigation separates job-to-be-done."                | Pure internal-IA language. Replace with content about what DART offers, not how the nav is organised.                   |
| T4  | [homepage.html](../../unified-trading-system-ui/public/homepage.html) ("What each service looks like in practice")   | "Choose a category from the list."                                                                                          | Delete — the list is below, reader doesn't need told.                                                                   |
| T5  | [briefings/page.tsx:33](<../../unified-trading-system-ui/app/(public)/briefings/page.tsx#L33>)                       | "The three paths" (section heading)                                                                                         | Refers to page structure, not offering. Use "Investment Management, DART, Regulatory" or "Pick the briefing that fits." |

### Wordiness / convoluted phrasing (rule 02 "specific over evocative")

| #   | File:line                                                                                                                               | Current copy                                                                                                                                                                                                              | Fix direction                                                                                                                                     |
| --- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| T6  | [lib/briefings/content.ts:49-50](../../unified-trading-system-ui/lib/briefings/content.ts#L49) (Regulatory TLDR)                        | "Odum operates regulated activity for clients under its own FCA permissions — the umbrella is a specific scope, not a blanket cover."                                                                                     | Double-negative at the end. Try: "Odum covers specific regulated activities for clients under its FCA permissions — scope is named, not assumed." |
| T7  | [investment-management/page.tsx:5](<../../unified-trading-system-ui/app/(public)/investment-management/page.tsx#L5>) (meta description) | "FCA-regulated investment management: sleeves, domain breadth, allocator workflow, and how to get started with Odum."                                                                                                     | "sleeves, domain breadth, allocator workflow" is jargon cluster. Drop "sleeves" (undefined), rewrite as plain statement of what the page covers.  |
| T8  | [services/regulatory/page.tsx:266-279](<../../unified-trading-system-ui/app/(public)/services/regulatory/page.tsx#L266>)                | "If you're managing capital, executing trades, or advising on investments — however you describe it internally — those are regulated activities. The line between software and advice is thinner than most people think…" | Editorial / op-ed voice. "find out the hard way" is colloquial + faintly patronising. Rule 02 anti-pattern. Compress to one factual paragraph.    |

### Pricing leakage / tier opacity (rule 08)

| #   | File:line                                                                                                                  | Current copy                                                                                                     | Fix direction                                                                                                                                                                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T9  | [services/backtesting/page.tsx:120-189](<../../unified-trading-system-ui/app/(public)/services/backtesting/page.tsx#L120>) | Three tiers (Starter / Professional / Enterprise), each labelled "Get in Touch" for price                        | Rule 08: no tier pricing on public pages. Either drop the tier cards entirely (likely correct — tiering belongs post-briefing per rule 04 axis resolution) or rewrite as capability lists without the tier scaffolding. |
| T10 | [services/investment/page.tsx:174-180](<../../unified-trading-system-ui/app/(public)/services/investment/page.tsx#L174>)   | "Management Fee: 0% / Performance Fee: 20-40% (HWM) / Minimum Investment: $100,000 / Redemption Notice: 30 days" | Rule 08 breach — IM perf-fee range is codex-private until second call per `path_to_100m_finalization`. Either remove the table or keep only "FCA-regulated; fees disclosed at second call."                             |
| T11 | [services/regulatory/page.tsx:163-173](<../../unified-trading-system-ui/app/(public)/services/regulatory/page.tsx#L163>)   | "AR Setup — From £4,000/mo" / "Advisory Engagement — From £3,000/mo"                                             | Check against `commercial-model/` codex — these numbers may or may not be sanctioned for public display. Flag for commercial review in Phase 1.                                                                         |

### Placeholder-feeling / vague CTAs

| #   | File:line                                                                                                                      | Current copy  | Fix direction                                                                                         |
| --- | ------------------------------------------------------------------------------------------------------------------------------ | ------------- | ----------------------------------------------------------------------------------------------------- |
| T12 | [services/investment/page.tsx:343](<../../unified-trading-system-ui/app/(public)/services/investment/page.tsx#L343>)           | "Apply Now"   | Vague. Either "Request an intro call" or remove — no public signup path exists for IM clients anyway. |
| T13 | Nav unauth ([components/shell/site-header.tsx:162-167](../../unified-trading-system-ui/components/shell/site-header.tsx#L162)) | "Get Started" | Points where? Align with briefing flow: "Book a call" or "Briefings" depending on funnel stage.       |
| T14 | [services/data/page.tsx:149](<../../unified-trading-system-ui/app/(public)/services/data/page.tsx#L149>)                       | "Get Access"  | Same issue — destination unclear.                                                                     |

### Voice drift across pages (rule 02)

| #   | Symptom                                                                                                                                        | Fix                                                                                                                                                                                                   |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T15 | Homepage is benefit-punchy, briefings are procedural, regulatory is protective/heavy, services/\* pages are ad-brochure. Four distinct voices. | Rule 02 pass per page against the `dart-briefing.md` / `im-decision-journey.md` / `regulatory-umbrella-briefing.md` templates — those three are the canonical voice. Bring service/\* into alignment. |

## 3. Term drift — cross-checked against codex glossary

Codex SSOT: [/codex/14-playbooks/glossary.md](/codex/14-playbooks/glossary.md),
[codex/14-playbooks/\_ssot-rules/02-tone-and-posture.md](/codex/14-playbooks/_ssot-rules/02-tone-and-posture.md).

### Forbidden / deprecated (codex rule)

| Canonical                                                                  | Found drift                                                                                                                                                                                                                                                                                                                  | File refs                                                                        |
| -------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| **DART** (first mention expand: "Data Analytics, Research & Trading")      | Never expanded on public pages — first exposure is nav label only ([nav-copy.ts:7](../../unified-trading-system-ui/components/shell/nav-copy.ts#L7)). Briefing copy at [content.ts:62-63](../../unified-trading-system-ui/lib/briefings/content.ts#L62) uses "data, analytics, research and trading" (lowercase, unbranded). | Expansion must appear at first use on homepage + /platform + briefings-hub tile. |
| **Catalogue** (UK spelling)                                                | "Data Catalogue" + "Feature Catalogue" + "Instrument Catalogue" consistent. ✓                                                                                                                                                                                                                                                | No drift found — but watch `docs/*` and any new pages.                           |
| **on-chain** / **real-time** (hyphenated)                                  | [services/data/page.tsx](<../../unified-trading-system-ui/app/(public)/services/data/page.tsx>) uses "real-time" ✓                                                                                                                                                                                                           | Spot-check remaining pages in Phase 2.                                           |
| **IM** / **Investment Management** (capitalised)                           | [content.ts:35](../../unified-trading-system-ui/lib/briefings/content.ts#L35) uses "Investment management" (lowercase m).                                                                                                                                                                                                    | Normalise to "Investment Management" per glossary §2.                            |
| No "DRT"                                                                   | ✓ Not found.                                                                                                                                                                                                                                                                                                                 | —                                                                                |
| No "Elysium" / "Arkham" / "Bloxroute" / "Pyth" / "Infura" as product names | ✓ Not found in public copy.                                                                                                                                                                                                                                                                                                  | —                                                                                |

### Unexpanded acronyms (institutional audience OK, but first-mention expand per rule 02)

All of the following appear without first-mention expansion: **DART**, **MiFID II**, **HWM**, **AR** (Appointed
Representative), **SMA**, **OMS**, **P&L**, **VaR**, **FCA** (usually OK but inconsistent). List at
[/tmp/public-pages-audit.md:964-986](/tmp/public-pages-audit.md#L964).

Fix: add first-mention-expand pass on each page during Phase 2 rewrite.

### Naming inconsistencies

| Concept                                       | Page 1                                                                                             | Page 2                                                                                                                             | Resolution per codex                                                                                                            |
| --------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `/services/backtesting` route vs page heading | URL: "backtesting"                                                                                 | H1: "Research"                                                                                                                     | Per plan M3 + glossary — page should be "Research"; URL redirect to `/services/research` in Phase 2.                            |
| Asset-class label                             | [docs/page.tsx:57](<../../unified-trading-system-ui/app/(public)/docs/page.tsx#L57>) "Crypto CeFi" | [services/regulatory/page.tsx:110](<../../unified-trading-system-ui/app/(public)/services/regulatory/page.tsx#L110>) "Crypto spot" | Glossary §2: "CeFi" is the canonical asset-class name; "Crypto spot" is an instrument type within CeFi. Normalise per glossary. |
| Signals page                                  | "Signals" (nav + page)                                                                             | "Signal Leasing" (codex + commercial model)                                                                                        | Decision M3 recommends "Signals Service (Signals-Out)" — confirm, then normalise everywhere including briefing content.         |
| "Platform" vs "DART"                          | Nav short = "DART", URL = `/platform`, page title = "Platform"                                     | Briefing slug = "platform"                                                                                                         | Per plan M2 — `/platform` is the DART umbrella. Add DART expansion to page copy.                                                |

## 4. Briefing depth — current vs codex spec

**Current shipped:** 3 pillars × 1 page each × ~2-3 bullets of body copy. Template =
[briefings/[slug]/page.tsx:36-62](<../../unified-trading-system-ui/app/(public)/briefings/[slug]/page.tsx#L36>)
(Situation / Position / Call, one paragraph each). Not nearly enough to bridge first-call → second-call.

**Codex spec** requires 4-5 sections per pillar. Full table follows. Cross-ref to parent plan Phase 3 (per-path briefing
routes).

### Investment Management briefing — gap vs [im-decision-journey.md](/codex/14-playbooks/experience/im-decision-journey.md)

| Codex required section                                                     | Shipped                                    | Gap type                                                                    |
| -------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------- |
| Strategy surface (one screen: maturity + capacity per slot, role-filtered) | —                                          | Missing page                                                                |
| SMA vs Pooled structure walkthrough                                        | Mentioned once in bullet                   | Shallow                                                                     |
| Reporting surface (positions, P&L, reconciliation, audit trail)            | —                                          | Missing page                                                                |
| FCA / MLRO / compliance detail                                             | "under Odum's FCA permissions" (TLDR only) | Shallow                                                                     |
| Platform-fee client-choice mechanic (+5% perf OR $500/mo)                  | —                                          | Missing — per rule 08, keep codex-private unless plan M5 resolves otherwise |

### DART briefing — gap vs [dart-briefing.md](/codex/14-playbooks/experience/dart-briefing.md)

| Codex required section                                                                   | Shipped               | Gap type                                                |
| ---------------------------------------------------------------------------------------- | --------------------- | ------------------------------------------------------- |
| Fit-check: 4 sub-sections (schema / what-we-need / what-we-don't / signals-only-vs-full) | —                     | Missing entire section                                  |
| Instruction schema — 8 required fields                                                   | —                     | Missing (per plan Phase 3 `/briefings/dart-signals-in`) |
| Signals-only vs full DART comparison table (13 dimensions)                               | —                     | Missing                                                 |
| Strategy catalogue preview (one row per slot, maturity + phase + venue)                  | —                     | Missing (per plan M7 — behind light-auth gate)          |
| Research/promote/execute loop                                                            | One phrase in summary | Shallow                                                 |
| Venue / chain / instrument-type packs + 12-month commitment floor                        | —                     | Missing                                                 |

### Regulatory briefing — gap vs [regulatory-umbrella-briefing.md](/codex/14-playbooks/experience/regulatory-umbrella-briefing.md)

| Codex required section                                                                                | Shipped                                  | Gap type       |
| ----------------------------------------------------------------------------------------------------- | ---------------------------------------- | -------------- |
| FCA permissions enumeration (in/out of scope)                                                         | "FCA authorisation scope" phrase only    | Missing detail |
| Five-workstream onboarding (legal / compliance / MLRO / venue / reporting) with owners + dependencies | "Engagement paths are explicit" sentence | Shallow        |
| Operating model post-signing (designated rep mechanics, compliance monitoring, best-ex evidence)      | —                                        | Missing        |
| 12-month commitment rationale                                                                         | —                                        | Missing        |

Fifth pillar (**Signals-out**) and direction-split DART briefings referenced in parent plan Phase 3 do not yet have any
content — ship from scratch.

## 5. Canonical glossary — reference pointer

Full canonical glossary extracted this session. Primary SSOT docs that Phase 2/3 writers must align to:

- **Audience terms** — [audiences-and-journeys.md](/codex/14-playbooks/audiences-and-journeys.md)
- **Product terms** — [glossary.md](/codex/14-playbooks/glossary.md) +
  [\_ssot-rules/04-dart-commercial-axes.md](/codex/14-playbooks/_ssot-rules/04-dart-commercial-axes.md)
- **Environments** — [environments/README.md](/codex/14-playbooks/environments/README.md)
- **Catalogues** — [cross-cutting/catalogues.md](/codex/14-customer-journeys/playbook-concepts/catalogues.md)
- **Lock state + maturity** —
  [09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md](/codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
- **Tone & posture (anti-patterns)** —
  [\_ssot-rules/02-tone-and-posture.md](/codex/14-playbooks/_ssot-rules/02-tone-and-posture.md) lines 56-77
- **Playbook grammar (9-section structure)** —
  [\_ssot-rules/01-grammar.md](/codex/14-playbooks/_ssot-rules/01-grammar.md)
- **Building-block dimensions (for pricing-adjacent copy)** —
  [\_ssot-rules/05-building-block-dimensions.md](/codex/14-playbooks/_ssot-rules/05-building-block-dimensions.md)

## 6. Delta summary — what this manifest adds beyond the parent plan

Parent plan already scopes:

- 5-path restructure (Phase 2)
- Light-auth briefing expansion (Phase 3)
- Visual assets (Phase 4)
- Docs alignment (Phase 5)
- QG + commit (Phase 6)

This manifest adds, specifically:

1. **15 concrete tone fixes** (T1-T15) with file:line + fix direction — consume in Phase 1/2
2. **Term drift table** — consume in Phase 2 rewrite pass
3. **Per-briefing gap matrix** — consume in Phase 3 content build
4. **Auth-state clarification** — briefings are already gated; flag "Sign-in required" badge copy (T-aux1) + raise
   M4-variant if Firebase is genuinely wanted
5. **Pricing-leakage items** (T9-T11) — rule 08 audit that should block Phase 2 sign-off until commercial review
6. **Voice drift across services/\*** (T15) — scope to remediate beyond just the briefings surface

## 7. Execution hand-off note

Parent plan Phase 1 item "Build per-page issue list + remediation spec" is **closed by this document**. Phase 1
remaining: commit this manifest + advance to Phase 0 decisions gate (M1-M10).

Phase 2 + Phase 3 agents should read this manifest first, not re-scan the site.
