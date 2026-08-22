#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: temporary — delete once pipeline_e2e_check.py itself gains native
#   multi-cell-per-invocation report accumulation (the skill's own "under
#   /autonomous, append to the same day's report" design intent).
# Delete-when: pipeline_e2e_check.py accumulates across --asset-group/--family-scoped
#   invocations natively, or the data_pipeline_check_mdps_features_2026_07_20.md
#   full-matrix todo is closed (whichever comes first).
"""Merge a freshly-overwritten pipeline_e2e_check JSON report against its
previously-committed git version, by (shard_label, leg) key.

WHY THIS EXISTS: ``features-service/scripts/pipeline_e2e_check.py`` OVERWRITES
its ``plans/audit/results/data_pipeline_e2e_check_features_<day>.json`` (+ the
paired ``.md``) on every invocation — it does not append when invoked as
SEPARATE processes with different ``--asset-group``/``--family`` filters
(the documented "append to the same day's report" behaviour only applies
WITHIN one long-running ``/autonomous`` process). Running the 29-cell matrix
in `data_pipeline_check_mdps_features_2026_07_20.md`'s
"Run /data-pipeline-check-features across ALL shards" todo one cell at a time
(the only viable pattern given the driver's own multi-minute per-shard VM
launch+wait, and the documented WorkerLivenessWatchdog risk on a single
long-lived multi-cell process — see that plan's 2026-07-27 slot-7 Progress
Log entries) means EVERY cell's driver invocation wipes the prior cells'
rows unless something re-merges them. This script is that something.

USAGE (run AFTER pipeline_e2e_check.py writes its fresh report, BEFORE
committing)::

    git show HEAD:plans/audit/results/data_pipeline_e2e_check_features_<day>.json \\
        > /tmp/prior.json
    python3 scripts/plan-hygiene/merge_pipeline_e2e_report.py \\
        --prior /tmp/prior.json \\
        --fresh plans/audit/results/data_pipeline_e2e_check_features_<day>.json \\
        --out plans/audit/results/data_pipeline_e2e_check_features_<day>.json

Regenerates the paired ``.md`` from the merged JSON's ``results`` list (a
plain Results + Bucket-paths table — any hand-written prose ``## Note``
sections in the prior ``.md`` are NOT preserved by this script; re-append
them manually after running, same as before). Dedup key is
``(shard_label, leg)`` — the FRESH row wins on a collision (re-running the
same cell is expected to supersede its own prior result, not be treated as
a duplicate).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def merge_reports(prior: dict[str, object], fresh: dict[str, object]) -> dict[str, object]:
    prior_results = list(prior["results"])
    fresh_results = list(fresh["results"])

    fresh_keys = {(r["shard_label"], r["leg"]) for r in fresh_results}
    kept_prior = [r for r in prior_results if (r["shard_label"], r["leg"]) not in fresh_keys]
    merged_results = kept_prior + fresh_results
    merged_results.sort(key=lambda r: (str(r["shard_label"]), str(r["leg"])))

    merged = dict(fresh)
    merged["results"] = merged_results
    merged["total"] = len(merged_results)
    for status in ("passed", "failed", "ambiguous", "skipped"):
        merged[status] = sum(1 for r in merged_results if r.get("status") == status)
    merged["started_at"] = prior.get("started_at", fresh.get("started_at"))
    return merged


def _shard_prefix(row: dict[str, object]) -> str:
    return str(row["shard_label"]).split(":")[0].lower()


def render_md(merged: dict[str, object], *, prior_md_text: str | None) -> str:
    results = merged["results"]
    lines: list[str] = []
    lines.append("---")
    lines.append("doc_type: audit-result")
    lines.append(f'title: "Pipeline E2E Check — {merged["service"]} ({merged["run_date"]})"')
    lines.append(
        f'summary: "{merged["service"]} pipeline-e2e-check {merged["run_date"]} (merged across multiple '
        f"driver invocations — see merge_pipeline_e2e_report.py): total={merged['total']} passed={merged['passed']} "
        f'failed={merged["failed"]} ambiguous={merged["ambiguous"]} skipped={merged["skipped"]}"'
    )
    lines.append("status: pass" if merged["failed"] == 0 else "status: fail")
    lines.append("nature: record")
    # frontmatter schema's asset_group enum has no "global" — GLOBAL-family shards
    # (e.g. calendar) are cross-asset-group and map to "cross-cutting" instead.
    ag_map = {"global": "cross-cutting"}
    ags = sorted({ag_map.get(_shard_prefix(r), _shard_prefix(r)) for r in results})
    lines.append(f"asset_group: [{', '.join(ags)}]")
    lines.append("stage: [data]")
    lines.append("repos: [features-service, deployment-service]")
    lines.append("scope: [engineer, admin]")
    lines.append(f"tags: [pipeline-e2e-check, {merged['service']}]")
    lines.append("related: []")
    lines.append("created: 2026-07-27")
    lines.append(
        f'audited_scope: "{merged["service"]} real-VM force/skip/live pipeline check for '
        f'day={merged["run_date"]}, legs={",".join(merged["legs"])}"'
    )
    lines.append("date: 2026-07-27")
    lines.append(f"auditor: {merged['service']} (real-VM automated run, merged)")
    lines.append("parent_epic: infrastructure_master")
    lines.append("severity: P3")
    lines.append("resulting_plan:")
    lines.append("lib_version:")
    lines.append("doc_versions_checked:")
    lines.append(f"service: {merged['service']}")
    lines.append(f"run_date: {merged['run_date']}")
    lines.append(f'generated_at: "{merged["finished_at"]}"')
    lines.append("---")
    lines.append("")
    lines.append(f"# Pipeline E2E Check — {merged['service']} ({merged['run_date']})")
    lines.append("")
    lines.append(f"**Legs:** {', '.join(merged['legs'])}")
    lines.append("")
    lines.append(
        "**Note — merged across multiple driver invocations** via `merge_pipeline_e2e_report.py` "
        "(the driver overwrites its report per-invocation, does not append across separate "
        "`--asset-group`/`--family`-scoped processes)."
    )
    lines.append("")
    lines.append(
        f"**Summary:** total={merged['total']} passed={merged['passed']} failed={merged['failed']} "
        f"ambiguous={merged['ambiguous']} skipped={merged['skipped']}"
    )
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Reason |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in results:
        lines.append(
            f"| {r['shard_label']} | {r['leg']} | {r['status']} | {r.get('skip_proof', '-')} | "
            f"{r.get('exit_status', '-')} | {r.get('parquet_count', '-')} | "
            f"{'ok' if r.get('manifest_ok') else '-'} | {r.get('reason', '-')} |"
        )
    lines.append("")
    lines.append("## Bucket paths (where each write/read actually landed)")
    lines.append("")
    lines.append("| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        pb = r.get("parquet_bucket") or "-"
        mb = r.get("manifest_bucket") or "-"
        same = "yes" if pb != "-" and pb == mb else "-"
        lines.append(f"| {r['shard_label']} | {r['leg']} | `{pb}` | `{mb}` | {same} |")
    lines.append("")
    if prior_md_text and "## Note" in prior_md_text:
        note_start = prior_md_text.index("## Note")
        lines.append(prior_md_text[note_start:].rstrip())
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prior", required=True, type=Path, help="prior (previously-committed) JSON report")
    ap.add_argument("--fresh", required=True, type=Path, help="freshly-overwritten JSON report")
    ap.add_argument("--out", required=True, type=Path, help="output JSON path (usually same as --fresh)")
    ap.add_argument("--prior-md", type=Path, default=None, help="prior .md (to preserve any ## Note sections)")
    args = ap.parse_args(argv)

    prior = _load(args.prior)
    fresh = _load(args.fresh)
    merged = merge_reports(prior, fresh)

    args.out.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")

    prior_md_text = args.prior_md.read_text(encoding="utf-8") if args.prior_md and args.prior_md.exists() else None
    md_out = args.out.with_suffix(".md")
    md_out.write_text(render_md(merged, prior_md_text=prior_md_text), encoding="utf-8")

    print(
        f"merged: total={merged['total']} passed={merged['passed']} failed={merged['failed']} "
        f"ambiguous={merged['ambiguous']} skipped={merged['skipped']}"
    )
    print(f"wrote {args.out}")
    print(f"wrote {md_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
