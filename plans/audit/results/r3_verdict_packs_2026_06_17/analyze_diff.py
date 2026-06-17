#!/usr/bin/env python3
"""Adjudicate a manifest_diff JSON into a verdict: separate respelling churn from real regression."""
import json
import re
import sys
from collections import defaultdict


def norm_venue(v):
    # canonicalise for pairing: strip chain suffix, remove underscores, upper
    v = (v or "").upper()
    v = re.sub(r'-[A-Z0-9]+$', '', v)   # drop trailing -CHAIN
    v = v.replace("_", "")
    return v

def main(path):
    with open(path) as _fh:
        d = json.load(_fh)
    ag = d["asset_group"]
    cells = d["cells"]
    reg = d["regressions"]
    st = d.get("status_transitions", {})
    # downgrades = any captured->X
    downgrades = {k:v for k,v in st.items() if k.startswith("captured->")}
    # net delta per data_type (respelling churn nets to ~0 within a data_type)
    net_dt = defaultdict(int)
    net_dt_abs = defaultdict(int)
    for g in d.get("group_row_deltas", []):
        net_dt[g["data_type"]] += g["delta"]
        net_dt_abs[g["data_type"]] += abs(g["delta"])
    nonzero_net = {k:v for k,v in net_dt.items() if v != 0}
    total_net = sum(net_dt.values())
    # pair removed venues to added venues by (data_type, norm_venue)
    added_keys = defaultdict(int)
    removed_keys = defaultdict(int)
    for g in d.get("group_row_deltas", []):
        if g["delta"] > 0:
            added_keys[(g["data_type"], norm_venue(g["venue"]))] += g["delta"]
        elif g["delta"] < 0:
            removed_keys[(g["data_type"], norm_venue(g["venue"]))] += -g["delta"]
    unmatched_removed = 0
    unmatched_detail = []
    for k, n in removed_keys.items():
        a = added_keys.get(k, 0)
        if a < n:
            unmatched_removed += (n - a)
            unmatched_detail.append((k, n-a))
    print(f"=== AG={ag} ===")
    print(f"current_rows={d['current']['rows']}  projected_rows={d['projected']['rows']}")
    print(f"cells: added={cells['added']} removed={cells['removed']} changed={cells['changed']} unchanged={cells['unchanged']}")
    print(f"captured_regressions={reg['captured_regressions']}  is_regression(gate)={reg['is_regression']}")
    print(f"status_transitions(upgrades shown, downgrades flagged): {dict(st)}")
    print(f"CAPTURED DOWNGRADES (captured->*): {downgrades if downgrades else 'NONE'}")
    print(f"total_net_row_delta(all data_types)={total_net}")
    print(f"data_types with NONZERO net delta ({len(nonzero_net)}): top10 by |net|:")
    for k,v in sorted(nonzero_net.items(), key=lambda x:-abs(x[1]))[:10]:
        print(f"    {k}: net={v}")
    print(f"RESPELLING-RECONCILED unmatched-removed rows (genuine-loss candidates)={unmatched_removed}")
    for k,v in sorted(unmatched_detail, key=lambda x:-x[1])[:10]:
        print(f"    UNMATCHED {k}: {v}")
    verdict = "GREEN" if (reg['captured_regressions']==0 and not downgrades and unmatched_removed==0) else "RED"
    print(f"ADJUDICATED VERDICT: {verdict}")

if __name__=="__main__":
    main(sys.argv[1])
