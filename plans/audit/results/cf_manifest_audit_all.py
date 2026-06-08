"""Cross-AG CF-1…CF-14 data-state audit — one invocation over all 5 asset_groups x
{market-data-tick, instruments-store} buckets (the 10 prod buckets), with a per-AG
GREEN/RED rollup + a machine-readable JSON summary, exiting NON-ZERO if any CF is RED.

This is the Tier-3 "Continuous Verification" wrapper (audit_criteria_automation_2026_06_08.md
Phase 2): the daily Cloud Run Job + Scheduler (deployment-service
`terraform/{gcp,aws}/cf_manifest_audit_scheduler.tf`) runs this and ALERTS ON ANY RED. It
composes the single-bucket `cf_manifest_audit_2026_06_01.audit()` over every AG bucket.

Entrypoint contract (referenced by the cron TF):
  cf-manifest-audit-all --all-ags --json-out gs://<audit-bucket>/cf_audit/<date>.json
exit 0 = every CF GREEN (SKIP is not RED); 1 = ≥1 RED; 2 = ≥1 bucket unreadable.

Run locally:
  .venv-workspace/bin/python cf_manifest_audit_all.py --all-ags
  .venv-workspace/bin/python cf_manifest_audit_all.py --all-ags --json-out /tmp/cf_audit.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from cf_manifest_audit_2026_06_01 import audit  # type: ignore[import-not-found]

#: AG → the bucket-name asset_group token. prediction's bucket token is `pred`.
AG_BUCKET_TOKENS: dict[str, str] = {
    "cefi": "cefi",
    "defi": "defi",
    "tradfi": "tradfi",
    "sports": "sports",
    "prediction": "pred",
}
#: The two manifest-bearing bucket kinds per AG.
BUCKET_KINDS: tuple[str, ...] = ("market-data-tick", "instruments-store")
DEFAULT_PROJECT = "central-element-323112"
DEFAULT_ENV = "prd"


def _bucket(kind: str, ag_token: str, env: str, project: str) -> str:
    return f"{kind}-{ag_token}-{env}-{project}"


def _write_json_out(uri_or_path: str, payload: dict[str, object]) -> None:
    """Write the JSON summary locally, then `gcloud storage cp` it up if a gs:// target."""
    text = json.dumps(payload, indent=2, sort_keys=True)
    if uri_or_path.startswith("gs://"):
        tmp = Path(tempfile.mkdtemp(prefix="cf_audit_json_")) / "cf_audit.json"
        _ = tmp.write_text(text, encoding="utf-8")
        res = subprocess.run(
            ["gcloud", "storage", "cp", str(tmp), uri_or_path],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            print(f"  WARN: could not upload JSON summary to {uri_or_path}: {res.stderr.strip()[-160:]}", flush=True)
    else:
        _ = Path(uri_or_path).write_text(text, encoding="utf-8")
    print(f"  JSON summary → {uri_or_path}", flush=True)


def run_all(env: str, project: str, json_out: str | None) -> int:
    per_bucket: dict[str, dict[str, str]] = {}
    any_red = False
    any_unreadable = False

    for ag, token in AG_BUCKET_TOKENS.items():
        for kind in BUCKET_KINDS:
            bucket = _bucket(kind, token, env, project)
            print(f"\n################ {ag} / {kind} :: {bucket} ################", flush=True)
            rc, results = audit(bucket, legacy=None)
            per_bucket[bucket] = results
            if rc == 2:
                any_unreadable = True
            if any(v == "RED" for v in results.values()):
                any_red = True

    # rollup
    print("\n================ CROSS-AG CF ROLLUP ================", flush=True)
    rollup: dict[str, dict[str, list[str]]] = {}
    for bucket, results in per_bucket.items():
        reds = sorted(k for k, v in results.items() if v == "RED")
        skips = sorted(k for k, v in results.items() if v.startswith("SKIP"))
        status = "RED" if reds else "GREEN"
        rollup[bucket] = {"status": [status], "reds": reds, "skips": skips}
        print(f"  {bucket:<55} {status}  reds={reds}  skips={len(skips)}")

    overall = "RED" if any_red else ("UNREADABLE" if any_unreadable else "GREEN")
    print(f"\nOVERALL: {overall}")

    if json_out:
        _write_json_out(
            json_out,
            {"overall": overall, "env": env, "project": project, "buckets": per_bucket, "rollup": rollup},
        )

    if any_red:
        return 1
    if any_unreadable:
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Cross-AG CF-1…CF-14 data-state audit (alert-on-RED).")
    _ = ap.add_argument("--all-ags", action="store_true", help="Run all 5 AGs x 2 bucket kinds (the default).")
    _ = ap.add_argument("--env", default=DEFAULT_ENV)
    _ = ap.add_argument("--project", default=DEFAULT_PROJECT)
    _ = ap.add_argument("--json-out", default=None, help="Local path or gs:// URI for the JSON summary.")
    a = ap.parse_args()
    env = str(a.env)
    project = str(a.project)
    json_out = a.json_out if a.json_out is None else str(a.json_out)
    return run_all(env, project, json_out)


if __name__ == "__main__":
    sys.exit(main())
