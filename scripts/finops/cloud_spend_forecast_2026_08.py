#!/usr/bin/env python3
# Epic: cloud cost + credits negotiation
# Lifecycle: POINT-IN-TIME — the 2026-08-09 forecast presented to Google Cloud
# Delete-when: superseded by the next forecast round, or after the contract signs
#
# WHY THIS EXISTS: bottom-up 12-month GCP consumption forecast (Sep-2026..Aug-2027)
# built for the credits/committed-use conversation. Anchored on the MEASURED Aug-2026
# exit run-rate, not on wishful growth curves.
#
# KEY MODELLING DECISIONS (all operator-corrected during the 2026-08-09 session):
#  1. agent-LLM is DERIVED, not list-priced: standard Anthropic rate limits cost ~2.0x
#     Max-tier economics, less a 10% discount = 1.8x current spend. Metered list for the
#     same measured volume is $0.9M-$1.5M/yr against ~$36k/yr actually paid; putting
#     THAT in a forecast line would be a fiction. The gap IS the credit ask.
#  2. batch_pipeline is EPHEMERAL backfill, not a recurring monthly cost. It decays hard
#     to incremental steady state once history lands. An early draft ran it flat for 12
#     months and materially overstated every scenario.
#  3. ml_train_infer is GPU-based from the point accelerators land — CPU today is a cost
#     workaround, not a design choice.
#  4. AWS $1,700/mo decomposes: CI VM $550 + AO orchestrator $1,000 + ~$200 misc. The AO
#     component sits with agent_llm (scales with fleet), not with CI (scales with repos).
"""Odum Research — Google Cloud 12-month consumption forecast (v2).

Adds the two lines the v1 model missed:
  * agent_llm      — Vertex AI / Model Garden inference for the autonomous
                     engineering fleet, MEASURED from Claude Code transcripts
                     (2026-08-02..08, 7 complete days) and priced at Vertex rates.
  * research_backtest — strategy research at the operator's stated cadence
                     (10 backtests/archetype/day, ~1,000 backtests to take one
                     live, 1 T+1 batch=live reconciliation per live archetype/day).

Window 2026-09 .. 2027-08. USD, gross of credits, monthly.
"""

import csv
import json
from pathlib import Path

OUT = Path(__file__).parent
GBP_PER_USD = 0.7522

MONTHS = [
    "2026-09",
    "2026-10",
    "2026-11",
    "2026-12",
    "2027-01",
    "2027-02",
    "2027-03",
    "2027-04",
    "2027-05",
    "2027-06",
    "2027-07",
    "2027-08",
]

# ---------------------------------------------------------------- ACTUALS ----
ACTUALS = [
    ("2026-01", None, None, 153.18, "GCP billing export not yet enabled"),
    ("2026-02", None, None, 15.59, "GCP billing export not yet enabled"),
    ("2026-03", None, None, 170.40, "GCP billing export not yet enabled"),
    ("2026-04", 84.89, 84.55, 18.00, "Export enabled 2026-04-30 (30th only)"),
    ("2026-05", 14466.26, 13280.26, 4.74, "Platform build-out begins"),
    ("2026-06", 19017.18, 16059.69, 35.62, "Multi-asset-group backfill"),
    ("2026-07", 20146.50, 16246.29, 1020.06, "AWS CI runner fleet stands up"),
    ("2026-08", 7706.52, 4098.02, 1035.66, "1-9 Aug only (partial month)"),
]

# --------------------------------------------------- MEASURED TOKEN USAGE ----
# tok.py over ~/.claude/projects, 7 complete days. Operator confirms this is
# the orchestrator fleet; the two operator laptops add ~25% on top.
TOKENS_7D_M = {"input": 0.844, "cache_write": 800.328, "cache_read": 53_586.783, "output": 101.527}
FLEET_UPLIFT = 1.25
TOKENS_PER_DAY_B = sum(TOKENS_7D_M.values()) / 7 / 1000
FLEET_TOKENS_PER_MONTH_B = TOKENS_PER_DAY_B * 30.44 * FLEET_UPLIFT
FLEET_TOKENS_PER_YEAR_T = FLEET_TOKENS_PER_MONTH_B * 12 / 1000

# Vertex-priced monthly cost of that volume under three routing policies
# (from llm_and_research.py; asia-northeast1 regional endpoints, +10%):
LLM_POLICY = {
    "claude_only": 94_478,  # all Claude on Vertex, prompt caching on
    "half_openweight": 62_835,  # 50% routed to Model Garden OW + 25% batch
    "mostly_openweight": 49_479,  # 80% routed OW + 30% batch
    "no_cache_tier": 604_165,  # risk case: caching unavailable/ineffective
}

# ---------------------------------------------- BASELINE (Aug-2026 exit) ----
# Sums to the measured ~$26,000/mo GCP+AWS. AWS $1,700 decomposes as: self-hosted CI VM
# $550 + AO orchestrator $1,000 + ~$200 misc — ALL migrating to GCP. agent_llm holds the
# $1,000 AO orchestrator today; Vertex token spend (~$5,400/mo at the derived 1.8x) lands
# on migration. GitHub Actions ~$60/mo excluded — not GCP spend, unchanged by migration.
# batch_pipeline is EPHEMERAL BACKFILL, not a recurring monthly cost — it decays hard to
# incremental steady state once history lands; new data sources cause fresh bursts.
BASELINE = {
    "data_capture": 5000,
    "batch_pipeline": 13000,
    "research_backtest": 2000,
    "ml_train_infer": 1500,
    "live_trading": 1400,
    "agent_llm": 1000,
    "ci_agents_infra": 1830,
    "analytics_client": 300,
}

BUCKET_LABELS = {
    "agent_llm": "Agent LLM inference (Vertex AI / Model Garden)",
    "research_backtest": "Strategy research & backtesting",
    "batch_pipeline": "Batch pipeline — backfill, candles, features",
    "data_capture": "Data capture & storage",
    "live_trading": "Paper, live trading & T+1 reconciliation",
    "ml_train_infer": "ML training & inference",
    "ci_agents_infra": "CI/CD & orchestrator infrastructure",
    "analytics_client": "Analytics, client platform & data products",
}

BUCKET_DRIVERS = {
    "agent_llm": "TWO COMPONENTS. (1) AO orchestrator + worker-slot compute: $1,000/mo on AWS "
    "today, migrating to GCP, scaling with fleet size. (2) Model inference — MEASURED "
    "at 7.8B tokens/day on the orchestrator over 7 days (98.3% prompt-cache reads), "
    "+25% from two operator laptops = ~296B tokens/month, ~3.55 trillion/year. We pay "
    "$1,500/mo TODAY across 6 Claude accounts + 1 DeepSeek account. Max-tier accounts "
    "roughly HALVE the effective rate, so the same work under standard GCP/Vertex "
    "terms is ~$3,000/mo — that is the forecast figure (a 10% discount would put it "
    "nearer $2,700, so $3,000 is the conservative side). Combined bucket = ~$4,000/mo "
    "at current fleet. NOT the $55k-126k/mo metered-list cost of that volume — the "
    "37x-84x gap between $1,500 actual and metered list IS the credit ask.",
    "research_backtest": "10 backtests per strategy archetype per day across the full data "
    "history, ~1,000 backtests to take one strategy live, plus one T+1 "
    "batch-versus-live reconciliation run per live archetype per day. A "
    "backtest costs ~$0.60 at the current narrow research universe and "
    "~$8.50 at the full captured universe — so the archetype count and the "
    "universe width multiply together.",
    "batch_pipeline": "EPHEMERAL, NOT RECURRING — and the steady state is TINY. Each month processes "
    "30 days of new data, ~2% of the historical corpus; live streaming through IS, "
    "MTDS and the rest of the pipeline adds a similar volume again. So ongoing "
    "monthly cost is roughly 6% of the ONE-TIME backfill cost — operator estimate "
    "~$400/mo for incremental backfill plus ~$400/mo for live streaming, i.e. ~$800/mo "
    "steady state. Of the ~$151k spent on GCP to date (~$90k Feb-Apr pre-export + $61.4k "
    "measured May-Aug) roughly 90% is ONE-OFF build-out — initial backfill, pipeline "
    "migrations and re-processing as the schema settled — not recurring operating cost. "
    "Frame it as non-recurring, not as waste. The Sep-Nov peak is the "
    "real TradFi x4 expansion (CME futures + options) plus CeFi x1.5 landing together; "
    "after that the line only spikes when a NEW data source is onboarded.",
    "data_capture": "112 TB across 79 buckets today. Cost is ~48% object operations, ~30% "
    "stored bytes, ~22% retrieval — it tracks pipeline throughput, not just "
    "corpus size, so it rises with research reads as well as ingest.",
    "live_trading": "Always-on execution spine — event transport, execution, strategy, risk, "
    "live market data — plus continuous paper trading alongside every live "
    "strategy. Capital isolation means one process tree per client, so this "
    "scales with mandates as well as strategies.",
    "ml_train_infer": "GPU from the point accelerators land — CPU training today is a cost workaround, "
    "not a design choice. A five-model crypto directional ensemble, sports outcome "
    "models and a traditional-markets index signal, with continuous retraining. "
    "~11.7M training rows at current scope; universe width and retrain cadence are "
    "the multipliers. Conservative stays CPU-bound (~$4k/mo exit); base assumes "
    "L4-class capacity in asia-northeast1 (~$12k/mo exit); ambitious assumes "
    "A100-class with continuous retraining (~$35k/mo exit). GATED ON GPU QUOTA AND "
    "PRICING IN TOKYO — there is no GPU spend on this account today.",
    "ci_agents_infra": "Self-hosted CI runner VM ($550/mo, on AWS today, migrating to GCP) running "
    "ALONGSIDE Cloud Build ($878/mo measured Aug) and Artifact Registry ($199/mo) "
    "rather than replacing them, plus ~$200/mo misc AWS that also migrates. GitHub "
    "Actions (~$60/mo) is EXCLUDED — not Google Cloud spend, unchanged by migration. "
    "Grows slowly with repo count and CI matrix width, not with fleet size.",
    "analytics_client": "BigQuery for live-trading analytics and client reporting (the lake "
    "stays Hive-partitioned Parquet on Cloud Storage), plus externally-facing "
    "surfaces — research workspace, signal delivery, data catalogue, and "
    "natural-language query over the corpus.",
}

# ------------------------------------------------------------- SCENARIOS ----
# Monthly values in $k, Sep-2026 .. Aug-2027.
SCENARIOS = {
    "conservative": {
        "label": "Conservative (budget-capped)",
        "premise": "NO CREDIT SUPPORT. Without renewed credits the affordable ceiling is ~$13,000/month, "
        "so this is not a slower version of the roadmap — it is the roadmap rationed to fit a "
        "budget. The agent fleet stays on flat-fee subscriptions rather than migrating to "
        "Vertex. No accelerators, so ML stays CPU-bound. Storage is tiered hard to Coldline to "
        "hold the line. Research is squeezed to whatever is left after fixed costs: the narrow "
        "universe only, a handful of archetypes. Two carry strategies go live because they are "
        "already committed. The captured universe keeps growing; the universe we can afford to "
        "RESEARCH does not.",
        "agent_llm": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        "research_backtest": [1.5, 1.5, 1.6, 1.7, 1.8, 1.9, 1.9, 2.0, 2.0, 2.1, 2.1, 2.2],
        "batch_pipeline": [4.0, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
        "data_capture": [5.0, 5.0, 4.9, 4.9, 4.8, 4.8, 4.8, 4.7, 4.7, 4.7, 4.6, 4.6],
        "live_trading": [1.6, 2.0, 2.2, 2.3, 2.4, 2.4, 2.5, 2.5, 2.6, 2.6, 2.7, 2.7],
        "ml_train_infer": [0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3],
        "ci_agents_infra": [1.83, 1.83, 1.83, 1.83, 1.83, 1.83, 1.83, 1.83, 1.83, 1.83, 1.83, 1.83],
        "analytics_client": [0.3, 0.3, 0.3, 0.3, 0.35, 0.35, 0.35, 0.35, 0.4, 0.4, 0.4, 0.4],
    },
    "base": {
        "label": "Base",
        "premise": "The roadmap runs on a realistically slipped schedule. The fleet "
        "migrates to Vertex with roughly half of turns routed to open-weight "
        "Model Garden models and the batch tier on autonomous runs, and grows "
        "~1.6x as more work is delegated to agents. Data expansion lands "
        "across Q4. Live trading starts in October and reaches eight to twelve "
        "strategy instances across four to six mandates. Research widens to "
        "~20 archetypes, with crypto and traditional markets moving to the "
        "full captured universe.",
        "agent_llm": [1.0, 4.0, 4.2, 4.5, 4.7, 5.0, 5.2, 5.5, 5.7, 6.0, 6.2, 6.4],
        "research_backtest": [3.3, 5.5, 9.0, 13.0, 17.0, 21.0, 25.0, 28.5, 31.5, 34.5, 37.0, 39.3],
        "batch_pipeline": [14.0, 16.0, 15.0, 8.0, 3.5, 2.0, 1.6, 1.6, 1.7, 1.8, 1.8, 1.9],
        "data_capture": [5.6, 6.6, 8.0, 9.2, 10.2, 11.0, 11.8, 12.6, 13.4, 14.3, 15.2, 16.2],
        "live_trading": [1.8, 3.4, 4.5, 5.4, 6.3, 7.2, 8.0, 8.8, 9.6, 10.4, 11.2, 12.0],
        "ml_train_infer": [1.8, 2.3, 3.2, 4.5, 5.8, 7.0, 8.0, 8.9, 9.7, 10.5, 11.3, 12.0],
        "ci_agents_infra": [1.9, 2.05, 2.2, 2.35, 2.5, 2.65, 2.8, 2.95, 3.1, 3.2, 3.3, 3.4],
        "analytics_client": [0.55, 0.85, 1.35, 1.9, 2.6, 3.3, 4.15, 5.0, 5.85, 6.7, 7.55, 8.5],
    },
    "ambitious": {
        "label": "Ambitious",
        "premise": "The engineering fleet is the product's velocity, so it stays on "
        "Claude for the hard majority of turns and grows ~2.5x as more of the "
        "build is delegated. The full captured universe feeds research across "
        "all five asset classes at ~40 archetypes. The live book scales toward "
        "the architecture's design ceiling with ten or more mandates and "
        "colocated execution in three regions. Continuous retraining on "
        "accelerators. External users — signal subscribers, research clients, "
        "catalogue access — become a material share of consumption.",
        "agent_llm": [1.0, 4.0, 4.5, 5.1, 5.6, 6.2, 6.7, 7.3, 7.8, 8.4, 8.9, 10.0],
        "research_backtest": [3.3, 8.0, 16.0, 27.0, 40.0, 53.0, 66.0, 78.0, 90.0, 101.0, 111.0, 120.0],
        "batch_pipeline": [15.0, 19.0, 20.0, 14.0, 8.0, 5.5, 4.5, 4.5, 4.5, 4.8, 4.8, 5.0],
        "data_capture": [6.0, 7.8, 10.0, 12.4, 14.6, 16.8, 18.9, 21.0, 23.2, 25.4, 27.7, 30.0],
        "live_trading": [2.2, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0, 22.5, 24.5, 26.5, 28.0],
        "ml_train_infer": [2.2, 3.5, 6.0, 9.5, 13.5, 17.5, 21.0, 24.5, 27.5, 30.0, 32.5, 35.0],
        "ci_agents_infra": [2.1, 2.4, 2.8, 3.1, 3.5, 3.8, 4.2, 4.5, 4.8, 5.1, 5.3, 5.5],
        "analytics_client": [0.8, 1.8, 3.4, 5.6, 8.3, 11.3, 14.5, 18.0, 21.5, 24.5, 27.5, 30.0],
    },
}

BUCKETS = [
    "agent_llm",
    "research_backtest",
    "batch_pipeline",
    "data_capture",
    "live_trading",
    "ml_train_infer",
    "ci_agents_infra",
    "analytics_client",
]


def build() -> dict:
    out = {
        "meta": {
            "window": f"{MONTHS[0]} .. {MONTHS[-1]}",
            "currency": "USD gross (pre-credit)",
            "gbp_per_usd": GBP_PER_USD,
            "baseline_month": "2026-08",
            "baseline_total_usd_per_month": sum(BASELINE.values()),
            "fleet_tokens_per_day_B": round(TOKENS_PER_DAY_B * FLEET_UPLIFT, 2),
            "fleet_tokens_per_month_B": round(FLEET_TOKENS_PER_MONTH_B),
            "fleet_tokens_per_year_T": round(FLEET_TOKENS_PER_YEAR_T, 2),
            "llm_policy_usd_per_month": LLM_POLICY,
            "llm_subscription_today_usd_per_month": 3000,
            "llm_list_value_usd_per_year": {"routed": 920280, "vertex_card": 1133736, "api_standard": 1513752},
        },
        "actuals": [
            {"month": m, "gcp_gross_usd": g, "gcp_net_usd": n, "aws_usd": a, "note": note}
            for m, g, n, a, note in ACTUALS
        ],
        "baseline": BASELINE,
        "bucket_labels": BUCKET_LABELS,
        "bucket_drivers": BUCKET_DRIVERS,
        "months": MONTHS,
        "scenarios": {},
    }
    for key, sc in SCENARIOS.items():
        totals = [round(sum(sc[b][i] for b in BUCKETS) * 1000) for i in range(12)]
        year = sum(totals)
        out["scenarios"][key] = {
            "label": sc["label"],
            "premise": sc["premise"],
            "buckets": {b: [round(v * 1000) for v in sc[b]] for b in BUCKETS},
            "bucket_totals": {b: round(sum(sc[b]) * 1000) for b in BUCKETS},
            "monthly_totals": totals,
            "year_total_usd": year,
            "year_total_gbp": round(year * GBP_PER_USD),
            "exit_run_rate_usd": totals[-1],
            "exit_multiple_vs_baseline": round(totals[-1] / sum(BASELINE.values()), 2),
        }
    return out


def main() -> None:
    d = build()
    (OUT / "forecast.json").write_text(json.dumps(d, indent=2))

    compact = {
        "months": d["months"],
        "labels": d["bucket_labels"],
        "baseline": d["baseline"],
        "meta": d["meta"],
        "scen": {
            k: {
                "label": v["label"],
                "buckets": v["buckets"],
                "totals": v["monthly_totals"],
                "year": v["year_total_usd"],
                "yearGbp": v["year_total_gbp"],
                "exit": v["exit_run_rate_usd"],
                "mult": v["exit_multiple_vs_baseline"],
                "bucketTotals": v["bucket_totals"],
            }
            for k, v in d["scenarios"].items()
        },
    }
    (OUT / "embed.json").write_text(json.dumps(compact, separators=(",", ":")))

    with (OUT / "forecast_monthly.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "cost_line", *MONTHS, "12mo_total_usd"])
        for _k, sc in d["scenarios"].items():
            for b in BUCKETS:
                v = sc["buckets"][b]
                w.writerow([sc["label"], BUCKET_LABELS[b], *v, sum(v)])
            w.writerow([sc["label"], "TOTAL", *sc["monthly_totals"], sc["year_total_usd"]])

    m = d["meta"]
    print(
        f"Baseline (Aug-2026 measured, GCP+AWS): ${m['baseline_total_usd_per_month']:,}/mo"
        f"  = ${m['baseline_total_usd_per_month'] * 12:,}/yr if flat"
    )
    print(
        f"Agent fleet: {m['fleet_tokens_per_day_B']}B tokens/day · "
        f"{m['fleet_tokens_per_month_B']:,}B/month · "
        f"{m['fleet_tokens_per_year_T']}T/year"
    )
    print()
    print(f"{'Scenario':<14}{'12-mo USD':>14}{'12-mo GBP':>14}{'Exit $/mo':>12}{'x today':>10}")
    print("-" * 64)
    for _k, sc in d["scenarios"].items():
        print(
            f"{sc['label']:<14}{sc['year_total_usd']:>14,}{sc['year_total_gbp']:>14,}"
            f"{sc['exit_run_rate_usd']:>12,}{sc['exit_multiple_vs_baseline']:>9.1f}x"
        )
    print()
    for _k, sc in d["scenarios"].items():
        print(f"--- {sc['label']}: bucket share of the 12-month total")
        tot = sc["year_total_usd"]
        for b, v in sorted(sc["bucket_totals"].items(), key=lambda x: -x[1]):
            print(f"    {BUCKET_LABELS[b]:<48} ${v:>10,}  {v / tot * 100:5.1f}%")
        print()


if __name__ == "__main__":
    main()
