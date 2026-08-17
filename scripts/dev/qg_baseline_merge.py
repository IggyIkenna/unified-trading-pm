#!/usr/bin/env python3
"""qg_baseline_merge.py — anomaly-guarded JSON merge for measure-qg-baseline.sh.

Extracted from measure-qg-baseline.sh's former inline python heredoc so the anomaly-guard
decision (PROMOTED vs ANOMALY) is independently testable — see
test-qg-baseline-anomaly-guard.sh. Internal helper for that caller only; argv is positional
by design, not a standalone CLI contract.

Usage: qg_baseline_merge.py <out_json> <repo> <env> <wall_s> <rss_mb> <cpu_s> <exit_code>
                             <quick:true|false> <jobs> <measured_at_utc> <force:true|false>
                             <anomaly_pct>

Prints "PROMOTED <rss_mb>" and writes <out_json> on promotion, or "ANOMALY <prior_mb>
<rss_mb>" and leaves <out_json> untouched when the freshly measured peak is >= anomaly_pct
percent above the existing committed value for (repo, env) and force != "true". A (repo,
env) with no existing committed value always promotes (nothing to compare against).
"""

import json
import os
import sys


def main(argv: list[str]) -> None:
    out, repo, env, wall, rss, cpu, ec, quick, jobs, ts, force, anomaly_pct = argv[1:13]
    data: dict[str, dict[str, dict[str, object]]] = {}
    if os.path.exists(out):
        try:
            with open(out) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {}
    rss_i = int(rss)
    prior_entry = (data.get(repo) or {}).get(env) or {}
    prior = prior_entry.get("peak_rss_mb")
    if isinstance(prior, (int, float)) and force != "true" and rss_i >= prior * (1 + float(anomaly_pct) / 100.0):
        print(f"ANOMALY {int(prior)} {rss_i}")
        return
    data.setdefault(repo, {})[env] = {
        "wall_s": float(wall),
        "peak_rss_mb": rss_i,
        "cpu_s": float(cpu),
        "exit_code": int(ec),
        "quick": quick == "true",
        "measured_concurrency": int(jobs),
        "measured_at_utc": ts,
    }
    with open(out, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"PROMOTED {rss_i}")


if __name__ == "__main__":
    main(sys.argv)
