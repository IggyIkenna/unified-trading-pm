---
doc_type: plan
title: Sports book scrapers — post-cutover successor (14 UK/EU + 2 US adapters)
summary:
status: complete
nature: record
asset_group: [sports]
stage: [meta]
repos: [alerting-service, deployment-service]
scope: [engineer, admin]
tags: []
related: [/plans/active/master_to_live_defi_2026_05_23.md]
created: "2026-05-21"
parent_epic: sports_master
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 20.0
estimate_calibrated_ai_days: 20.0
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

> **ARCHIVED 2026-05-21** — Operator BLOCKED-OPERATOR-DECISION (2026-05-12): scraper path not in May-23 scope. All
> phases DEFERRED-POST-CUTOVER. Activates when operator provisions accounts + credentials at 14 UK/EU + 2 US books.
> status: paused → archived.

# Sports Book Scrapers — Post-Cutover Successor

**BLOCKED-OPERATOR-DECISION** — operator explicitly chose 2026-05-12 not to pursue scraper-path book adapters for the
May-23 cutover. Sports track ships odds-aggregator-API path only (api-football, the-odds-api, OddsJam, SFI Footystats).
This plan formalises the deferral per the HARD RULE "External Data Is Always Available — Never Silently Defer Adapters."
14 UK/EU + 2 US bookmaker scrapers deferred pending operator decision + account provisioning.

Codex SSOTs: `codex/14-customer-journeys/sports/` (per-book credential rotation runbook — created at Phase 4)

---

## Phase 1 — Account provisioning (operator-side)

- [x] ✅ **[BLOCKED-OPERATOR-DECISION — account provisioning gate; this plan re-activates when operator acks]** [HUMAN]
      P0. Operator opens accounts at 14 UK/EU books + 2 US books; deposits £50-100/book minimum; provisions
      GeoComply/XPoint subscription + API credentials; vaults in Secret Manager under
      `sports-scrapers-{book}-{credential_type}`. (trivial-sweep 2026-05-21)

## Phase 2 — Per-book scraper hardening (~8 cal AI-days)

- [x] ✅ **[DEFERRED-POST-CUTOVER-2026-06-01+ — gated on Phase 1 operator decision]** [AGENT] P1. For each of 16 books:
      wire credential flow (login → session cookie/token); update HTML/XHR parsing; add residential-proxy rotation +
      retry/backoff; anti-bot bypass (TLS fingerprint masking, behavioural delays); unit tests against captured HTML
      fixtures; integration tests `@pytest.mark.requires_credentials`; manifest emission per writegate Phase 6.x
      pattern. (trivial-sweep 2026-05-21)

## Phase 3 — Production rollout + monitoring (~4 cal AI-days)

- [x] ✅ **[DEFERRED-POST-CUTOVER-2026-06-01+ — gated on Phase 2]** [AGENT] P1. Singleton-locked VM launcher
      `deployment-service/scripts/vm/launch-sports-book-scraper-vm.sh`; per-book health watchdog
      (ban/rate-limit/session-expiry → alerting-service); manifest reconciliation (scraper vs aggregator-API
      cross-check; ≥1bps dispersion threshold → alert); `categorical_dispersion_across_books` archetype eligibility
      flip. (trivial-sweep 2026-05-21)

## Phase 4 — Post-launch operational ramp (~4 cal AI-days)

- [x] ✅ **[DEFERRED-POST-CUTOVER-2026-06-01+ — gated on Phase 3]** [AGENT] P2. Per-book account-balance monitor (refill
      alerts); anti-detection rule iteration as books update bot-detection; codex doc updates per
      `interface-credential-convention.md` § Sports books. (trivial-sweep 2026-05-21)

## Deferred work — migrated to:

| Deferred item                                               | Successor                                                         |
| ----------------------------------------------------------- | ----------------------------------------------------------------- |
| Phase 1 — account provisioning (14 UK/EU + 2 US bookmakers) | BLOCKED-OPERATOR-DECISION; this plan activates when operator acks |
| Phase 2 — per-book scraper hardening (~8 cal AI-days)       | This plan post-Phase-1                                            |
| Phase 3 — production rollout + monitoring (~4 cal)          | This plan post-Phase-2                                            |
| Phase 4 — post-launch operational ramp (~4 cal)             | This plan post-Phase-3                                            |

## Temporary states + canonical follow-up plans

- Activation gated on operator decision + account provisioning (Phase 1). No auto-fire.
- Sports MVP path that ships May-23 (without scrapers): api-football + the-odds-api + OddsJam + SFI Footystats.
- Credential approval request shape (pre-filled per HARD RULE): 14 UK/EU books + GeoComply/XPoint
  ~$2-5k/mo enterprise
  tier + optional residential-proxy provider ~$500-1500/mo.
