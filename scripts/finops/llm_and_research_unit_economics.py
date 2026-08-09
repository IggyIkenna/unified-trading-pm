#!/usr/bin/env python3
# Epic: cloud cost + credits negotiation
# Lifecycle: DURABLE — the unit-economics layer under the forecast
# Delete-when: superseded by measured Vertex invoices or measured backtest timings
#
# WHY THIS EXISTS: two unit costs the forecast depends on and nobody had measured —
#   (1) fleet inference priced at Vertex/API rate cards under different routing
#       policies (open-weight share, batch tier, regional premium, cache tier);
#   (2) research backtest cost at the operator's stated cadence (10/archetype/day,
#       ~1,000 to take one strategy live, 1 T+1 batch=live recon per live archetype).
#
# LOAD-BEARING ASSUMPTION: prompt caching at the standard 0.1x read multiplier. At
# 98% cache reads, losing the cache tier moves the line 6x ($94k -> $604k/month).
# UNVERIFIED: per-backtest vCPU-hours are modelled bottom-up, never benchmarked.
"""Price the measured agent-fleet token usage at Vertex AI rates, and size the
research-backtest workload from the operator's stated cadence.

Token usage is MEASURED from Claude Code transcripts on one operator host,
2026-08-02 .. 2026-08-08 (7 complete days), via tok.py.
"""

import json
from pathlib import Path

OUT = Path(__file__).parent

# ----------------------------------------------------------- MEASURED ----
# 7 complete days (Aug 2-8), millions of tokens
DAYS = 7
MEASURED_7D = {  # millions of tokens
    "input": 0.844,  # uncached input
    "cache_write": 800.328,
    "cache_read": 53_586.783,
    "output": 101.527,
}
# Model mix over the window (share of total tokens)
MODEL_MIX = {"sonnet5": 0.964, "opus5": 0.036}

TOTAL_7D_M = sum(MEASURED_7D.values())
PER_DAY_M = TOTAL_7D_M / DAYS

# ------------------------------------------------------ VERTEX PRICING ----
# Claude on Vertex AI is partner-operated with its own rate card.
# Sonnet 5: $2.20 / $11.00 per 1M (global endpoint).
# Opus 5:   first-party parity assumed at $5.00 / $25.00 pending Vertex quote.
# Regional endpoints (asia-northeast1, where our data and venues are) carry a
# ~10% premium over global.
# Prompt caching: cache READ = 0.10x input rate, cache WRITE = 1.25x (5-min TTL).
# Batch API: 50% discount (applies to non-interactive agent work only).
REGIONAL_PREMIUM = 1.10
CACHE_READ_MULT = 0.10
CACHE_WRITE_MULT = 1.25

RATES = {  # USD per 1M tokens, global endpoint
    "sonnet5": {"in": 2.20, "out": 11.00},
    "opus5": {"in": 5.00, "out": 25.00},
    # Open-weight reference tier on Model Garden (DeepSeek-class MaaS).
    # NOTE: no Anthropic-style prompt caching -> cached tokens bill as full input.
    "openweight": {"in": 0.15, "out": 0.60},
}


def price_month(
    tokens_m: dict, model: str, regional: bool = True, caching: bool = True, batch_share: float = 0.0
) -> float:
    """Cost in USD for one month at the given per-month token mix."""
    r = RATES[model]
    prem = REGIONAL_PREMIUM if regional else 1.0
    rin, rout = r["in"] * prem, r["out"] * prem
    if caching:
        cost = (
            tokens_m["input"] * rin
            + tokens_m["cache_write"] * rin * CACHE_WRITE_MULT
            + tokens_m["cache_read"] * rin * CACHE_READ_MULT
            + tokens_m["output"] * rout
        )
    else:
        # no cache tier: every input token bills at full input rate
        cost = (tokens_m["input"] + tokens_m["cache_write"] + tokens_m["cache_read"]) * rin + tokens_m["output"] * rout
    # batch discount on the share of work that can run non-interactively
    return cost * (1 - 0.5 * batch_share)


def scale(tokens_7d: dict, factor: float, days: float = 30.44) -> dict:
    """Scale the 7-day measured mix to a month at `factor` x fleet size."""
    return {k: v / DAYS * days * factor for k, v in tokens_7d.items()}


def blended_month(fleet_factor: float, regional=True, caching=True, batch_share=0.0, openweight_share=0.0) -> dict:
    """Price a month of fleet inference, routing `openweight_share` of tokens
    to an open-weight Model Garden tier and the rest to Claude on Vertex."""
    m = scale(MEASURED_7D, fleet_factor)
    ow = {k: v * openweight_share for k, v in m.items()}
    cl = {k: v * (1 - openweight_share) for k, v in m.items()}
    cost = 0.0
    for model, share in MODEL_MIX.items():
        part = {k: v * share for k, v in cl.items()}
        cost += price_month(part, model, regional, caching, batch_share)
    if openweight_share > 0:
        # open-weight MaaS has no cache tier
        cost += price_month(ow, "openweight", regional, caching=False, batch_share=batch_share)
    return {
        "usd_per_month": round(cost),
        "tokens_per_month_B": round(sum(m.values()) / 1000, 2),
        "tokens_per_year_T": round(sum(m.values()) / 1000 * 12 / 1000, 2),
    }


# -------------------------------------------------- RESEARCH BACKTESTS ----
# Per-backtest compute, derived bottom-up:
#   MVP scope   (~30 CeFi bases x 6 venues, 2-5y of 1m bars) ~ 3 vCPU-hr + I/O
#   Full pool   (~490 bases x 14 venues)                     ~ 100 vCPU-hr + I/O
# Blended effective rate across spot VMs (~$0.012/vCPU-hr) and Cloud Run jobs
# (~$0.097/vCPU-hr) = ~$0.045/vCPU-hr, plus GCS read ops + retrieval.
BT_COST = {"mvp": 0.60, "full": 8.50}  # USD per backtest, all-in

RESEARCH_CADENCE = {  # operator-stated
    "backtests_per_archetype_per_day": 10,
    "backtests_to_take_one_live": 1000,
    "recon_backtests_per_live_archetype_per_day": 1,  # T+1 batch=live recon
}
DAYS_PER_MONTH = 30.44


def research_month(
    archetypes_in_research: int, full_pool_share: float, strategies_promoted: float, live_archetypes: int
) -> dict:
    avg = BT_COST["full"] * full_pool_share + BT_COST["mvp"] * (1 - full_pool_share)
    sweep = archetypes_in_research * RESEARCH_CADENCE["backtests_per_archetype_per_day"] * DAYS_PER_MONTH * avg
    promote = strategies_promoted * RESEARCH_CADENCE["backtests_to_take_one_live"] * avg
    recon = live_archetypes * RESEARCH_CADENCE["recon_backtests_per_live_archetype_per_day"] * DAYS_PER_MONTH * avg
    return {
        "sweep": round(sweep),
        "promote": round(promote),
        "recon": round(recon),
        "total": round(sweep + promote + recon),
        "backtests_per_month": round(
            archetypes_in_research * 10 * DAYS_PER_MONTH + strategies_promoted * 1000 + live_archetypes * DAYS_PER_MONTH
        ),
        "avg_cost_per_backtest": round(avg, 2),
    }


def main() -> None:
    print("=" * 78)
    print("MEASURED AGENT-FLEET TOKEN USAGE — one operator host, 7 days")
    print("=" * 78)
    print(f"  7-day total     {TOTAL_7D_M / 1000:>10.2f} B tokens")
    print(f"  per day         {PER_DAY_M / 1000:>10.2f} B tokens")
    print(f"  annualised      {PER_DAY_M * 365 / 1_000_000:>10.2f} T tokens  (this host alone)")
    for k, v in MEASURED_7D.items():
        print(f"    {k:<12} {v / 1000:>10.2f} B   ({v / TOTAL_7D_M * 100:5.2f}%)")
    print()

    print("=" * 78)
    print("PRICED AT VERTEX AI RATES (asia-northeast1 regional, +10%)")
    print("=" * 78)
    cases = [
        ("AO measured only, Claude, cache on", 1.00, True, 0.00, 0.00),
        ("AO measured, NO cache tier", 1.00, False, 0.00, 0.00),
        ("FLEET 1.25x, Claude only", 1.25, True, 0.00, 0.00),
        ("FLEET 1.25x, 30% batch", 1.25, True, 0.30, 0.00),
        ("FLEET 1.25x, 50% open-weight", 1.25, True, 0.00, 0.50),
        ("FLEET 1.25x, 80% OW + 30% batch", 1.25, True, 0.30, 0.80),
        ("FLEET 1.25x, 50% OW + 25% batch", 1.25, True, 0.25, 0.50),
        ("FLEET 2.0x growth, 50% OW", 2.00, True, 0.25, 0.50),
        ("FLEET 2.5x growth, Claude-heavy", 2.50, True, 0.15, 0.20),
        ("FLEET 3.0x growth, Claude-heavy", 3.00, True, 0.15, 0.20),
    ]
    print(f"{'Scenario':<38}{'tok/mo':>10}{'tok/yr':>10}{'$/month':>12}{'$/year':>13}")
    print("-" * 78)
    for label, f, cache, batch, ow in cases:
        r = blended_month(f, caching=cache, batch_share=batch, openweight_share=ow)
        print(
            f"{label:<38}{r['tokens_per_month_B']:>9.0f}B{r['tokens_per_year_T']:>9.1f}T"
            f"{r['usd_per_month']:>12,}{r['usd_per_month'] * 12:>13,}"
        )
    print()

    print("=" * 78)
    print("RESEARCH BACKTEST WORKLOAD (operator cadence)")
    print("  10 backtests/archetype/day  ·  ~1,000 backtests to take one live")
    print("  1 T+1 batch=live reconciliation backtest/live archetype/day")
    print("=" * 78)
    profiles = [
        ("Sep 2026  (6 in research, 0 live)", 6, 0.15, 0.0, 0),
        ("Conservative exit (10, 2 live)", 10, 0.30, 0.5, 2),
        ("Base exit (20 in research, 12 live)", 20, 0.55, 1.5, 12),
        ("Ambitious exit (40 in research, 40 live)", 40, 0.85, 3.0, 40),
    ]
    print(f"{'Profile':<44}{'backtests/mo':>14}{'$/backtest':>12}{'$/month':>12}")
    print("-" * 82)
    for label, arche, fps, promo, live in profiles:
        r = research_month(arche, fps, promo, live)
        print(f"{label:<44}{r['backtests_per_month']:>14,}{r['avg_cost_per_backtest']:>12.2f}{r['total']:>12,}")
        print(
            f"{'    sweep/promote/recon split':<44}{'':>14}{'':>12}{r['sweep']:>7,} / {r['promote']:,} / {r['recon']:,}"
        )
    print()

    with open(OUT / "llm_research.json", "w") as _out_fh:
        json.dump(
            {
                "measured_7d_M": MEASURED_7D,
                "per_day_B": PER_DAY_M / 1000,
                "annualised_T_one_host": PER_DAY_M * 365 / 1_000_000,
                "priced": {
                    label: blended_month(f, caching=c, batch_share=b, openweight_share=o) for label, f, c, b, o in cases
                },
                "research": {label: research_month(a, fps, p, live) for label, a, fps, p, live in profiles},
            },
            _out_fh,
            indent=1,
        )


if __name__ == "__main__":
    main()
