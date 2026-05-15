---
title: "Sports book scrapers — post-cutover successor (14 UK/EU + 2 US adapters)"
created: 2026-05-14
type: plan
status: BLOCKED-OPERATOR-DECISION (May-23 out-of-scope; activation post-cutover at operator option)
predecessor: plans/epics/sports_master_2026_05_07.md § "Scrapers DEFERRED-INDEFINITELY 2026-05-12 per operator"
locked_by: live-defi-rollout
locked_since: 2026-05-14
deadline: post-cutover (target 2026-06-01)
estimate_class: brand-new
estimate_baseline_ai_days: 20
estimate_calibrated_ai_days: 20
parent_epic: plans/epics/sports_master_2026_05_07.md
priority: P2 (post-cutover; not blocking May-23)
---

# Sports book scrapers — post-cutover successor

## Status (2026-05-14, codified per CLAUDE.md "External Data Is Always Available — Never Silently Defer Adapters")

**BLOCKED-OPERATOR-DECISION** — operator explicitly chose 2026-05-12 not to pursue scraper-path book adapters for the
May-23 cutover. Sports track ships odds-aggregator-API path only (api-football, the-odds-api, OddsJam, SFI Footystats).
Scraper adapters are valuable but not critical for live trading.

This successor plan exists to satisfy the May-14 HARD RULE: every silently-deferred data adapter must either be
re-activated with credential ask OR have an explicit `BLOCKED-OPERATOR-DECISION` row + named successor plan. This is the
named successor.

## What's deferred

### 14 UK/EU bookmaker scrapers (`market-tick-data-service/.../sports/registry.py:14-21`)

`bet365` · `888sport` · `betfred` · `betvictor` · `betway` · `boylesports` · `bwin` · `coral` · `ladbrokes` ·
`paddypower` · `sbo` · `skybet` · `unibet` · `williamhill`

Source files retained as scaffolding (per `sports_master_2026_05_07.md:153-176`); production-forbidden via registry
gate.

### 2 US browser adapters

Specifics in `sports_master_2026_05_07.md` § "DEFERRED-INDEFINITELY". US books gated additionally by GeoComply / XPoint
state-level licensing checks.

## Activation prerequisites (operator-side; not blockers — operator decision needed first)

Pre-filled CREDENTIAL APPROVAL REQUEST shape per the HARD RULE, ready to dispatch if operator decides to activate:

```
CREDENTIAL APPROVAL REQUEST — sports_book_scrapers
Vendor: 14 UK/EU bookmaker accounts + 2 US books + GeoComply/XPoint behavioural-anti-bot service
What I need:
  - Account signup at each of the 14 UK/EU books (operator-provided KYC: name + DOB + address)
  - GeoComply or XPoint subscription (~$2-5k/mo enterprise tier per vendor pricing)
  - Optional: residential-proxy provider (Bright Data / Oxylabs ~$500-1500/mo) for anti-detection on UK books
Account: <new operator account per book; or shared service account if vendor permits>
Unblocks: sports MVP price-dispersion-across-books archetype; live odds-arb across retail books
Without it: sports track ships aggregator-only path (api-football, the-odds-api, OddsJam, SFI Footystats);
  scrapers stay dormant scaffolding
```

## Activation phases (post-operator-ack only)

### Phase 1 — Per-book account provisioning + credential vaulting (~4 cal AI-days, operator-blocking)

- Operator opens accounts at 14 UK/EU books + 2 US books (manual; ~30 min per book).
- Operator deposits ÂŁ50-100 / book minimum to satisfy account-active checks (~ÂŁ800 + GBP→USD conversion).
- Operator provisions GeoComply / XPoint subscription + obtains API credentials.
- Credentials vaulted in Secret Manager under `sports-scrapers-{book}-{credential_type}` per UAC
  `interface-credential-convention.md`.

### Phase 2 — Per-book scraper hardening (~8 cal AI-days; brand-new 1.0× class)

For each of 16 books:

- Wire credential flow (login → session cookie / token).
- Update HTML/XHR parsing to current site shape (most books rotate frontend every 3-6 mo).
- Add residential-proxy rotation logic + retry/backoff with exponential jitter.
- Anti-bot bypass: TLS fingerprint masking (CycleTLS / undetected-chromedriver), behavioural delays, mouse-movement
  simulation for browser-driven adapters.
- Unit tests against captured HTML fixtures; integration tests marked `@pytest.mark.requires_credentials`.
- Manifest emission per writegate Phase 6.x pattern.

### Phase 3 — Production rollout + monitoring (~4 cal AI-days)

- Singleton-locked VM launcher under `deployment-service/scripts/vm/launch-sports-book-scraper-vm.sh`.
- Per-book health watchdog: detect ban / rate-limit / session-expiry → alert operator via alerting-service.
- Manifest reconciliation: scraper output vs odds-aggregator-API output cross-check; ≥1bps dispersion threshold triggers
  alert.
- Sports `categorical_dispersion_across_books` archetype eligibility flip.

### Phase 4 — Post-launch operational ramp (~4 cal AI-days)

- Per-book account-balance monitor (refill alerts).
- Anti-detection rule iteration as books update their bot-detection.
- Codex doc updates per `interface-credential-convention.md` § Sports books.

## Estimate

20 cal AI-days post-operator-ack (Phase 2-4 only; Phase 1 is operator-side and ~0 AI-time).

## Success criteria

- All 14 UK/EU books emitting odds rows ≥99% uptime over a 7-day window.
- 2 US books emitting odds rows ≥99% uptime over a 7-day window in covered states.
- Manifest reconciliation passes ≤1bps dispersion threshold for shared markets.
- Per-book credential rotation runbook in `codex/14-customer-journeys/sports/` published.

## Cross-references

- **Predecessor (the silent-defer this plan formalises)**: `plans/epics/sports_master_2026_05_07.md:153-176`
- **HARD RULE this plan satisfies**: CLAUDE.md § "External Data Is Always Available — Never Silently Defer Adapters
  (HARD RULE codified 2026-05-14)"
- **Sports MVP path that ships May-23 (without scrapers)**: api-football + the-odds-api + OddsJam + SFI Footystats
- **Cross-link in master plan**: `master_to_live_defi_2026_05_23.md` § "Deferred / blocked-on-operator items"
  (BLOCKED-OPERATOR-DECISION row)

## Notes

The original 2026-05-12 deferral was operator's strategic call (sports scrapers are a multi-week build with ongoing
maintenance burden; the odds-aggregator-API path covers the MVP analytics use case). This plan does NOT contradict that
decision — it simply formalises the deferral under the post-2026-05-14 closed-set status taxonomy. Activation is at
operator's option post-cutover; nothing in this plan auto-fires.
