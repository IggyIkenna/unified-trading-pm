---
doc_type: plan
title: Board Presentations Suite — Odum Research
summary: Build a suite of 10 company-grade board presentations (Reveal.js HTML) covering all 9 business lines of the unified
  trading system. Presentations are semi-technical, targeting professional/institutional board-level audience. Includes
  smoke test suite (Playwright) to catch rendering and syntax errors.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
todos:
- {id: create-theme-css, content: 'Create assets/theme.css — premium dark theme (deep navy #0a0f1e, gold #d4af37, electric blue #00d4ff). Typography: Inter headings, JetBrains Mono labels.', status: completed}
- {id: create-00-master, content: 'Create 00-master.html — master board deck (~26 slides). Platform thesis, client lifecycle funnel, TAM across all 8 lines, revenue stack, shared infra moat, AI-native ops, system quality, ask/next steps.', status: completed}
- {id: create-01-data-provision, content: 'Create 01-data-provision.html — Data Provision Service. 33 venues, 5 asset classes, 18+ data types, ML signal layer. Pricing tiers £2k–£200k/month.', status: completed}
- {id: create-02-baas, content: Create 02-backtesting-as-a-service.html — BaaS. Sports + DeFi + options + futures + crypto in one engine. No-code + NL agent config. Pricing £500–£20k/month., status: completed}
- {id: create-03-strategy-wl, content: Create 03-strategy-white-labelling.html — Strategy White Labelling. 17+ strategy types across 5 asset classes. Managed alpha option. SHAP explainability., status: completed}
- {id: create-04-eaas, content: Create 04-execution-as-a-service.html — EaaS. 9 algo types including Almgren-Chriss. Native DEX + CEX + TradFi execution. Alpha-fee charging vs VWAP benchmark., status: completed}
- {id: create-05-im, content: Create 05-investment-management.html — IM + Prop Trading + DeFi LP. FCA-authorised. 2/20 structure. Cross-asset portfolio (TradFi + Crypto + Sports)., status: completed}
- {id: create-06-regulatory, content: Create 06-regulatory-umbrella.html — FCA Umbrella + Sports Predictions. FCA ref 975797. AR umbrella for institutional algo firms. Sports ML probability API., status: completed}
- {id: create-07-ai-ops, content: 'Create 07-autonomous-ai-operations.html — Autonomous AI Operations. PR review agents, P&L monitor agents, trade quality agents, AI-driven onboarding pipeline (client/venue/instrument/strategy/AR onboarding).', status: completed}
- {id: create-08-quality, content: 'Create 08-system-quality.html — System Quality & Robustness. T0→T3 invariant, 246–1056 tests per service, two-pass quality gates, SIT repo, performance regression, agent-driven auditing.', status: completed}
- {id: create-09-portal, content: 'Create 09-platform-portal.html — Platform Portal & Client Experience. Authenticated portal, AI NL querying, automated monthly reporting, accounting/invoicing automation.', status: completed}
- {id: fix-mermaid-rendering, content: 'Fix all blank/broken Mermaid diagrams across all decks. Root causes: ready-event registered after initialize(), data-processed flag on hidden slides, emoji/Unicode in diagram code, subgraph IDs used as edge targets, cyclic graphs in LR layout, ~ asymmetric shape syntax. Resolution: replace ALL Mermaid diagrams with pure HTML/CSS equivalents — zero remaining Mermaid dependencies.', status: completed}
- {id: smoke-tests, content: 'Write Playwright smoke test suite (tests/smoke.spec.js + playwright.config.js). 86 tests across 10 decks: JS errors, logo visible, slide count, no broken Mermaid, cover title, no empty sections, footer FCA number, FCA badge. Static checks: no raw Mermaid blocks, logo refs, ready-event pattern, logo file exists, theme.css exists, no emoji in Mermaid context.', status: completed}
- {id: self-contained-html, content: 'Make all 10 HTML files fully self-contained: inline theme.css into <style> block, base64-encode odum-logo.png into img src data URI. Copy logo into presentations/assets/ so the presentations folder is self-contained. Single HTML file can be opened by anyone with no additional files or folders needed (internet required for Reveal.js CDN).', status: completed}
isProject: false
---

## Summary

10 Reveal.js HTML presentations built and hardened for board delivery. All 86 smoke tests pass. Each HTML file is fully
standalone — send any single file or the whole folder.

### Files delivered

```
presentations/
├── assets/
│   ├── theme.css
│   └── odum-logo.png
├── 00-master.html
├── 01-data-provision.html
├── 02-backtesting-as-a-service.html
├── 03-strategy-white-labelling.html
├── 04-execution-as-a-service.html
├── 05-investment-management.html
├── 06-regulatory-umbrella.html
├── 07-autonomous-ai-operations.html
├── 08-system-quality.html
├── 09-platform-portal.html
├── playwright.config.js
├── package.json
└── tests/
    └── smoke.spec.js
```

### Key technical decisions

- All Mermaid diagrams replaced with pure HTML/CSS — eliminates rendering dependency entirely
- Reveal.js 5 via jsDelivr CDN (no build step)
- FCA ref 975797 present in every deck; Professional/ECP-only restriction clearly stated in deck 06
- IP protection framework applied: algorithm names shown, parameters/weights/features not shown
- Cross-sell "super-cycle" slide in master and each deep-dive deck
