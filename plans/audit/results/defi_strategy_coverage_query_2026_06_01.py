"""DeFi strategy data-coverage audit query (item v — honest coverage per data_type x venue/chain).

Reads the prd availability_index for defi + cefi + tradfi and produces, for the three
in-scope DeFi MVP strategies, the honest-coverage totality breakdown:
  - per (asset_group, data_type, venue): 4-state capture_status counts + schema_version v9% + date window
  - per (data_type, chain): same, for chain-scoped data_types

Run: .venv-workspace/bin/python <this>
"""

from __future__ import annotations

import sys
from collections import defaultdict

import gcsfs
import pandas as pd

PROJECT_ID = "central-element-323112"
ENV = "prd"
BUCKETS = {
    "defi": f"market-data-tick-defi-{ENV}-{PROJECT_ID}",
    "cefi": f"market-data-tick-cefi-{ENV}-{PROJECT_ID}",
    "tradfi": f"market-data-tick-tradfi-{ENV}-{PROJECT_ID}",
}

# Strategy → data_types it consumes (canonical names).
STRATEGY_DATA_TYPES = {
    "staked_basis_carry": {
        "defi": ["lst_rates", "staking_yields", "oracle_prices", "lending_indices"],
        "cefi": ["perp_funding", "derivative_ticker"],
    },
    "funding_rate_arb": {
        "defi": ["perp_funding"],
        "cefi": ["perp_funding", "derivative_ticker", "book_snapshot_5", "trades"],
    },
    "basis_carry": {
        "cefi": ["trades", "derivative_ticker", "futures_chain", "options_chain"],
        "tradfi": ["trades", "ohlcv_1m"],
    },
}

ALL_DT_BY_AG = defaultdict(set)
for _strat, by_ag in STRATEGY_DATA_TYPES.items():
    for ag, dts in by_ag.items():
        ALL_DT_BY_AG[ag].update(dts)

CHAIN_SCOPED = {
    "lst_rates",
    "staking_yields",
    "oracle_prices",
    "lending_indices",
    "dex_swaps",
    "dex_pools",
    "perp_funding",
}


def load(ag: str, fs: gcsfs.GCSFileSystem) -> pd.DataFrame:
    import pyarrow.parquet as pq

    path = f"{BUCKETS[ag]}/_index/availability_index.parquet"
    want = ["date", "venue", "data_type", "chain", "schema_version", "capture_status", "error_reason"]
    print(f"reading gs://{path} ...", flush=True)
    with fs.open(path) as fh:
        present = {f.name for f in pq.read_metadata(fh).schema}
    cols = [c for c in want if c in present]
    df = pd.read_parquet(fs.open(path), columns=cols)
    for c in want:
        if c not in df.columns:
            df[c] = None
    df = df[df["data_type"].isin(ALL_DT_BY_AG[ag])].copy()
    df["ag"] = ag
    return df


def main() -> int:
    fs = gcsfs.GCSFileSystem()
    frames = [load(ag, fs) for ag in BUCKETS]
    df = pd.concat(frames, ignore_index=True)
    print(f"\nTotal strategy-relevant manifest rows: {len(df):,}\n", flush=True)

    out = []
    out.append("# DeFi strategy data-coverage — honest breakdown per data_type x venue/chain\n")
    out.append(f"_prd indexes; total strategy-relevant rows: {len(df):,}_\n")

    # ---- Per (asset_group, data_type, venue) ----
    out.append("\n## A. Per data_type x venue (in totality)\n")
    out.append(
        "| ag | data_type | venue | rows | captured | empty_conf | attempted_failed | exp_unatt | other | v9% | date_min | date_max |"
    )
    out.append("|---|---|---|--:|--:|--:|--:|--:|--:|--:|---|---|")
    g = df.groupby(["ag", "data_type", "venue"], dropna=False)
    for (ag, dt, venue), sub in sorted(g, key=lambda kv: (kv[0][0], kv[0][1], str(kv[0][2]))):
        cs = sub["capture_status"].value_counts()
        cap = int(cs.get("captured", 0))
        emp = int(cs.get("empty_confirmed", 0))
        af = int(cs.get("attempted_failed", 0))
        eu = int(cs.get("expected_unattempted", 0))
        other = len(sub) - cap - emp - af - eu
        v9 = 100.0 * (sub["schema_version"] == 9).sum() / len(sub) if len(sub) else 0.0
        dmin, dmax = sub["date"].min(), sub["date"].max()
        out.append(
            f"| {ag} | {dt} | {venue} | {len(sub):,} | {cap:,} | {emp:,} | {af:,} | {eu:,} | {other:,} | {v9:.0f}% | {dmin} | {dmax} |"
        )

    # ---- Per (data_type, chain) for chain-scoped types ----
    out.append("\n## B. Per data_type x chain (chain-scoped data_types)\n")
    out.append("| data_type | chain | rows | captured | empty_conf | attempted_failed | v9% | date_min | date_max |")
    out.append("|---|---|--:|--:|--:|--:|--:|---|---|")
    dch = df[df["data_type"].isin(CHAIN_SCOPED)]
    gc = dch.groupby(["data_type", "chain"], dropna=False)
    for (dt, chain), sub in sorted(gc, key=lambda kv: (kv[0][0], str(kv[0][1]))):
        cs = sub["capture_status"].value_counts()
        cap = int(cs.get("captured", 0))
        emp = int(cs.get("empty_confirmed", 0))
        af = int(cs.get("attempted_failed", 0))
        v9 = 100.0 * (sub["schema_version"] == 9).sum() / len(sub) if len(sub) else 0.0
        out.append(
            f"| {dt} | {chain} | {len(sub):,} | {cap:,} | {emp:,} | {af:,} | {v9:.0f}% | {sub['date'].min()} | {sub['date'].max()} |"
        )

    # ---- Schema version distribution per data_type ----
    out.append("\n## C. schema_version distribution per data_type (read from DATA)\n")
    out.append("| ag | data_type | rows | v-distribution |")
    out.append("|---|---|--:|---|")
    for (ag, dt), sub in sorted(df.groupby(["ag", "data_type"])):
        vd = sub["schema_version"].value_counts().sort_index()
        dist = " ".join(f"v{int(v)}:{c:,}" for v, c in vd.items())
        out.append(f"| {ag} | {dt} | {len(sub):,} | {dist} |")

    # ---- empty_confirmed reasons ----
    out.append("\n## D. empty_confirmed reasons (verify owed-data vs genuine absence)\n")
    out.append("| ag | data_type | error_reason | rows |")
    out.append("|---|---|---|--:|")
    ec = df[df["capture_status"] == "empty_confirmed"]
    for (ag, dt, reason), sub in sorted(
        ec.groupby(["ag", "data_type", "error_reason"], dropna=False), key=lambda kv: -len(kv[1])
    ):
        out.append(f"| {ag} | {dt} | {reason} | {len(sub):,} |")

    report = "\n".join(out)
    print(report)
    dest = __file__.replace("_query_", "_report_").replace(".py", ".md")
    with open(dest, "w") as fh:
        fh.write(report + "\n")
    print(f"\n\nWrote {dest}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
