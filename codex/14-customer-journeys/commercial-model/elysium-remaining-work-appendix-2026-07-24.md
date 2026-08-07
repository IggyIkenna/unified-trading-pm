---
doc_type: codex-ssot
title: Elysium — Phase 2 remaining-work appendix (2026-07-24)
summary:
  Companion appendix to the 2026-07-20 delay letter — plain-English breakdown of what's left before the staked-basis and
  perp-basis carry strategies go live for Elysium (OKX, Bybit, Binance, Deribit, Lido) — historical backfill,
  staking/funding-rate completeness, instrument-naming standardisation cutover, and live-collection resume, plus broader
  estate work that doesn't gate the client's strategies.
status: current
nature: record
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, elysium, remaining-work, appendix, client-communication]
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-delay-letter-2026-07-20.md,
    /codex/14-customer-journeys/commercial-model/ODUM_SLA_v4_2026-07-24.md,
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
  ]
created: 2026-07-24
authoritative_for: [exact wording of the Elysium Phase-2 remaining-work appendix sent 2026-07-24]
referenced_by: []
owner:
last_reviewed:
code_refs: []
---

# Appendix: Remaining work to production (high level)

_Companion to the Phase 2 update. This is the honest, plain-English view of what is left before the two strategies
(staked-basis carry and perp-basis carry, across OKX, Bybit, Binance, Deribit and Lido) are running live. Most of it is
completing and hardening the underlying market-data pipeline; the strategy logic and execution machinery are
substantially built._

**Critical path to your two strategies going live**

- **Historical market-data backfill.** Filling the complete trade, price and funding history for your venues. A
  bottleneck that had been capping our fetch throughput has been found and fixed; the remaining gap is now on the order
  of a day or two of compute rather than the much longer ceiling we'd feared. _In progress, tail remaining._

- **Staking- and funding-rate completeness.** Making sure the specific inputs these carry strategies live on (staking
  and exchange rates for assets like Lido stETH, and perpetual funding rates on each exchange) are complete and
  continuous rather than patchy. _In progress._

- **Instrument-naming standardisation.** A large, mostly mechanical migration that gives every instrument one consistent
  identity across storage, records and indexes, so the same contract is never mislabelled or double-counted. The
  migration code is written and validated in dry-runs; the production cutover is staged and waiting on a maintenance
  window. _Substantially built, cutover pending. Gates your venues specifically; the rest is estate-wide._

- **Live-collection resume and execution wiring (final mile).** Restarting the live data collectors we paused during the
  migration, and completing the exchange-execution credentials for the trade venues. The very last step, moving onto a
  live wallet, is a deliberate human sign-off rather than anything automated. _Queued behind the backfill._

**Broader estate work (does not gate your strategies)**

- **Honest completeness accounting.** Making our data-completeness figures count genuine gaps honestly rather than
  flattering themselves, and restoring a clean internal view of exactly what data exists. _In progress._

- **Pipeline verification and quality gating.** End-to-end checks that derived data (candles, features) matches its
  source, plus tidying a few internal coverage registries. _In progress._

- **Estate cleanup.** Removing decommissioned venues, legacy storage and orphaned files. _In progress, cosmetic to you._

**Bottom line:** most of what's left is data-pipeline completion and hardening. The strategy models, the execution
engine, the risk controls and the monitoring are already built; the remaining effort is getting the full, clean data
behind them and completing the final live wiring. We'll walk through any of this in as much depth as you'd like on a
call.
