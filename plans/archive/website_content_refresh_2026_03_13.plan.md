---
doc_type: plan
title: website-content-refresh-2026-03-13
summary: 'Refresh odum-research-website content: About page with 6 team member stubs (photos TBD), services copy from presentations
  (regulatory umbrella, investment management, multi-asset), updated traction data. Odum tagline preserved.'
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
type: mixed
epic: epic-website
superseded_by: website_master_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: D1, business: B1}
repo_gates:
- {repo: odum-research-website, code: C0, deployment: none, business: none, readiness_note: 'DR N/A: staging deploy only (domain migration plan owns production cutover). BR: user sign-off on content.'}
depends_on: [website-repo-integration-2026-03-13]
todos:
- {id: asset-audit, content: 'Identify all existing photos/images in repo. Document which are outdated. Create odum-research-website/docs/website-photo-requirements.md listing each required photo: dimensions, format, who it''s for (team member name or hero banner).', status: todo, note: ''}
- {id: stub-team-bios, content: 'Create About/Team page with 6 member slots. Members: Shaun Lim, Julian John, Femi Amoo, Harsh, Robert Osborne, Ikenna Igboaka. Each slot: name, title (TBD), photo placeholder (grey box with initials), bio stub. Derive brief expertise blurbs from presentation slides (use 01-09 HTML presentations as source).', status: todo, note: Photos blocked on team supply — stub slots only. Titles TBD by user.}
- {id: update-services-copy, content: 'Refresh services section. Focus: regulatory umbrella + investment management. Multi-asset coverage: TradFi, prediction markets, DeFi, CeFi (crypto). Services (light touch): consultancy, strategy-as-a-service, backtesting-as-a-service, execution-as-a-service. Source: unified-trading-pm/presentations/06-regulatory-umbrella.html + 05-investment-management.html.', status: todo, note: ''}
- {id: update-tagline, content: 'Preserve Odum dual meaning tagline: "Odum carries two meanings: the lion for strength and the tree for rooted innovation." Update hero copy to reflect current platform: multi-asset quantitative research and execution platform.', status: todo, note: 'Old about us text: ''Odum Research builds highly tuned pricing, risk and execution strategies at low latency to capture financial market inefficiencies across derivatives and spot markets.'''}
- {id: update-traction-content, content: 'Update traction/about section to reflect 2026 state: 8 active strategy clients, Edge Capital fund-to-fund (BTC strategy), Indian options mandate (incoming), live trading March 20 2026, 33 venues (9 CeFi + 9 TradFi + 14 DeFi + 1 onchain perps), 60+ repos.', status: todo, note: ''}
- {id: update-hero-images, content: 'Replace hero/banner images with placeholder brand imagery until real photos supplied. Use Odum brand colours (derive from existing site or define: dark background, gold/amber accent). Document colour tokens in odum-research-website/docs/brand-tokens.md.', status: todo, note: ''}
- {id: photo-handoff-slots, content: 'Finalize odum-research-website/docs/website-photo-requirements.md with exact specs (e.g. "Team: 400x400px JPEG, square crop, professional headshot"). Share doc with team members to collect photos.', status: todo, note: Blocking on team — cannot complete until photos supplied.}
- {id: quality-gate-pass, content: Run bash scripts/quality-gates.sh. Deploy preview to odum-research.co.uk staging. User sign-off on content before merge., status: todo, note: ''}
isProject: false
---

# Plan: Odum Research Website — Content Refresh

## Context

The current `odum-research.co.uk` website has outdated content and photos. Before migrating to `odum-research.com` (Plan
3), the content needs to accurately represent Odum Research: the team, the platform capabilities, and current traction.

**Implementer: Femi Amoo**

Photos are not yet available — stubs will be created and filled when team supplies images. Copy is sourced from the
existing PM presentation slides (01-09) which represent the current narrative.

---

## About / Team Page Structure

```
Team section (6 members):
┌────────────────────────────────────────────────────────────────┐
│ [Photo]  Shaun Lim        | Title: TBD | Bio: <from slides>   │
│ [Photo]  Julian John      | Title: TBD | Bio: <from slides>   │
│ [Photo]  Femi Amoo        | Title: TBD | Bio: <from slides>   │
│ [Photo]  Harsh            | Title: TBD | Bio: <from slides>   │
│ [Photo]  Robert Osborne   | Title: TBD | Bio: <from slides>   │
│ [Photo]  Ikenna Igboaka   | Title: TBD | Bio: <from slides>   │
└────────────────────────────────────────────────────────────────┘
Photo placeholder: grey box with initials (CSS only, no image required)
```

---

## Services Copy (Light Touch)

Focus areas:

1. **Regulatory Umbrella** — FCA compliance, regulatory framework
2. **Investment Management** — fund-to-fund structure, client mandates
3. **Multi-Asset** — TradFi, prediction markets, DeFi, CeFi

Supporting services (brief mention):

- Consultancy
- Strategy-as-a-service
- Backtesting-as-a-service
- Execution-as-a-service

Source presentations: `unified-trading-pm/presentations/05-investment-management.html`,
`unified-trading-pm/presentations/06-regulatory-umbrella.html`

---

## Traction Bar (cross-page)

> 8 active strategy clients · Edge Capital fund-to-fund · Indian options mandate (incoming) · Live March 2026

---

## Verification Gates

- [ ] About/Team page renders with 6 member placeholders
- [ ] Services section updated — regulatory umbrella + investment management prominent
- [ ] Tagline preserved on hero
- [ ] Traction bar visible on homepage
- [ ] `bash scripts/quality-gates.sh` exits 0
- [ ] Preview deployed to odum-research.co.uk staging; user signs off

## Files Created / Modified

- `odum-research-website/src/pages/About.tsx` (or equivalent)
- `odum-research-website/public/assets/team/` (placeholder images)
- `odum-research-website/docs/website-photo-requirements.md` (new)
- `odum-research-website/docs/brand-tokens.md` (new)
