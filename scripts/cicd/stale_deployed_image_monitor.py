#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Stale-deployed-image monitor — a loud failure signal for a cancelled/dropped cloud-build-router
dispatch.

Ref: plans/active/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md todo -002.

`cloud-build-router.yml`'s per-repo Cloud Build dispatch can be silently CANCELLED under merge-pileup
load (see the issue doc — a shared `change-freeze-check.yml` concurrency group cancelled a caller's
whole run before it reached `route-build`, root-caused + fixed there 2026-07-27). A cancelled GHA run
is invisible in GitHub's UI unless someone is watching that specific repo's Actions tab, so a dropped
dispatch can leave a repo's deployed image silently stale FOREVER with every other CI signal green (PR
merged, quality-gates-v2 passed). This is the missing "did the thing I expect to have happened, actually
happen" check for the LAST mile of the promote→build→deploy chain — mirrors the promotion-lag +
AR-dep-publish-lag monitors already wired into `branch-health.yml` for the earlier links in that chain.

For every `ldr_main` repo (direct LDR→main promotion) whose `cloudbuild.yaml` declares a `:latest`-tagged
Docker image, this compares:

  * the repo's `main` branch HEAD commit timestamp (GitHub API)
  * the `:latest` tag's most recent push (`updateTime`) in Artifact Registry (`gcloud artifacts docker
    images list --include-tags`)

and flags the repo if the image is older than the commit by more than `--threshold-min` (default 90 —
the Cloud Build build step alone has a 1800s/30m timeout; add the caller repo's own quality-gates-v2 run
plus the router's regional-fallback retry path and 90m is a conservative floor past which "still
building" stops being a plausible explanation). A commit younger than the threshold is never flagged —
the build may simply still be in flight.

Image-path resolution is TEMPLATE-DRIVEN, not hand-mapped per repo: it fetches each repo's own
`cloudbuild.yaml` (`gh api .../contents/cloudbuild.yaml`), parses its `substitutions:` block, and
resolves the `images:` list's `:latest` entries by substituting `$PROJECT_ID` + `${_KEY}` tokens. This
handles both the canonical `_REGISTRY_REPO`/`_SERVICE_NAME` template (most services) and repos with
different substitution names or already-literal image paths (e.g. unified-trading-library's base-image
build, deployment-service's `_ARTIFACT_REPO`/`_REGION`), with zero repo-specific hardcoding. A repo
whose `images:` entries can't be fully resolved (an unresolved `${_TOKEN}` left over) is SKIPPED, not
flagged — fail-open by design (mirrors `assert_deps_published_to_ar.py`): any uncertainty must never
manufacture a false page. Library-only repos with no Docker image (pure wheel publishers) and repos with
no `cloudbuild.yaml` at all are silently skipped — they have no `:latest` image staleness to measure.

Stdlib + `gh` + `gcloud` only. Prints a human report; with `--slack` prints a Slack-formatted block (the
workflow posts it). Exit 1 if any repo is stale past the threshold (so a required-check/alert can gate);
exit 0 otherwise, including every fail-open path.

Usage:
    stale_deployed_image_monitor.py [--threshold-min 90] [--project-id central-element-323112] [--slack] [--json]
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
from typing import cast

OWNER = "IggyIkenna"
DEFAULT_PROJECT_ID = "central-element-323112"


def _repos_manifest(manifest_path: str | None = None) -> dict[str, object]:
    if manifest_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        manifest_path = os.path.join(here, "..", "..", "workspace-manifest.json")
    with open(manifest_path) as f:
        m = cast("dict[str, object]", json.load(f))
    repos = m.get("repositories")
    return cast("dict[str, object]", repos) if isinstance(repos, dict) else {}


def _ldr_main_repos(manifest_path: str | None = None) -> list[str]:
    """Repos that promote LDR→main directly (`promotion_model: ldr_main` in the workspace manifest).

    Conceptually the same "main-direct" set `promotion_lag_monitor._main_direct_repos` tracks; kept
    self-contained here rather than cross-imported — this is a standalone, read-only classification of
    ~25 static manifest rows, not worth coupling two otherwise-unrelated monitors over.
    """
    repos = _repos_manifest(manifest_path)
    out: list[str] = []
    for name, cfg in repos.items():
        if isinstance(cfg, dict) and cast("dict[str, object]", cfg).get("promotion_model") == "ldr_main":
            out.append(str(name))
    return sorted(out)


def _fetch_file(repo: str, path: str, ref: str = "main") -> str | None:
    """Fetch a file's text content from GitHub at `ref` via `gh api`; None on any error."""
    proc = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}?ref={ref}", "--jq", ".content"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return base64.b64decode(proc.stdout.strip()).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


_SUB_LINE_RE = re.compile(r'^\s+(_[A-Za-z0-9_]+):\s*"?([^"#\n]*?)"?\s*(?:#.*)?$')
_IMAGE_LINE_RE = re.compile(r'^\s*-\s*"([^"]+)"\s*$')
_TOKEN_RE = re.compile(r"\$\{(_[A-Za-z0-9_]+)\}")


def _parse_substitutions(text: str) -> dict[str, str]:
    """Parse the `substitutions:` top-level block into a {_KEY: value} dict.

    Line-based, not a YAML parser — these files carry Cloud Build's `$$`-escaped bash inside
    multi-line `|` blocks that a strict YAML load chokes on inconsistently across the fleet's
    cloudbuild.yaml variants. Good enough here: we only need the top-of-file substitutions block.
    """
    out: dict[str, str] = {}
    in_block = False
    for line in text.splitlines():
        if line.strip() == "substitutions:":
            in_block = True
            continue
        if in_block:
            if line and not line[0].isspace():
                break  # dedented to a new top-level key — block over
            m = _SUB_LINE_RE.match(line)
            if m:
                out[m.group(1)] = m.group(2).strip()
    return out


def _parse_latest_image_refs(text: str) -> list[str]:
    """Parse the `images:` top-level block's `:latest`-tagged entries (raw, unsubstituted)."""
    out: list[str] = []
    in_block = False
    for line in text.splitlines():
        if line.strip() == "images:":
            in_block = True
            continue
        if in_block:
            if line and not line[0].isspace():
                break
            m = _IMAGE_LINE_RE.match(line)
            if m and m.group(1).endswith(":latest"):
                out.append(m.group(1))
    return out


def _resolve_image_ref(ref: str, substitutions: dict[str, str], project_id: str) -> str | None:
    """Substitute `$PROJECT_ID`/`${PROJECT_ID}` + `${_KEY}` tokens; None if any `${_KEY}` is left
    unresolved. Cloud Build accepts the builtin project-id token in either bare or braced form
    (deployment-service's cloudbuild.yaml uses `${PROJECT_ID}`; most others use bare `$PROJECT_ID`)."""
    resolved = ref.replace("${PROJECT_ID}", project_id).replace("$PROJECT_ID", project_id)

    def _sub(m: re.Match[str]) -> str:
        return substitutions.get(m.group(1), m.group(0))

    resolved = _TOKEN_RE.sub(_sub, resolved)
    if _TOKEN_RE.search(resolved):
        return None  # a token had no matching substitution — unresolved, skip (fail-open)
    return resolved


def _latest_image_paths_for_repo(repo: str, project_id: str) -> list[str] | None:
    """The repo's fully-resolved `:latest` AR image path(s); None if cloudbuild.yaml absent/unreadable."""
    text = _fetch_file(repo, "cloudbuild.yaml")
    if text is None:
        return None
    subs = _parse_substitutions(text)
    raw_refs = _parse_latest_image_refs(text)
    out: list[str] = []
    for ref in raw_refs:
        resolved = _resolve_image_ref(ref, subs, project_id)
        if resolved:
            out.append(resolved)
    return out


def _main_head_commit(repo: str) -> tuple[str, dt.datetime] | None:
    """(short_sha, committer_datetime) of the repo's `main` HEAD; None on any error."""
    proc = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{repo}/commits/main"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        d = cast("dict[str, object]", json.loads(proc.stdout))
    except json.JSONDecodeError:
        return None
    sha = d.get("sha")
    commit = cast("dict[str, object]", d.get("commit") or {})
    committer = cast("dict[str, object]", commit.get("committer") or {})
    date_s = committer.get("date")
    if not isinstance(sha, str) or not isinstance(date_s, str):
        return None
    try:
        when = dt.datetime.fromisoformat(date_s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return sha[:7], when


def _ar_latest_tag_update_time(image_path: str) -> dt.datetime | None:
    """Most recent push (`updateTime`, falling back to `createTime`) of `image_path`'s `:latest` tag.

    None if the image/tag doesn't exist in AR at all (never built) OR on any gcloud error — both fail
    toward "can't measure staleness" rather than a false page; `scan()` treats that None as its own
    (still-actionable — "never built") finding rather than silently dropping it.
    """
    base, _, tag = image_path.rpartition(":")
    if tag != "latest" or not base:
        return None
    proc = subprocess.run(
        ["gcloud", "artifacts", "docker", "images", "list", base, "--include-tags", "--format=json"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        entries = cast("list[object]", json.loads(proc.stdout))
    except json.JSONDecodeError:
        return None
    best: dt.datetime | None = None
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        e = cast("dict[str, object]", entry)
        tags = e.get("tags")
        tag_list = tags if isinstance(tags, list) else ([tags] if isinstance(tags, str) else [])
        if "latest" not in [str(t) for t in cast("list[object]", tag_list)]:
            continue
        ts = e.get("updateTime") or e.get("createTime")
        if not isinstance(ts, str):
            continue
        try:
            when = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            continue
        if best is None or when > best:
            best = when
    return best


def scan(threshold_min: int, project_id: str) -> list[dict[str, object]]:
    """Per-repo staleness findings.

    A repo is flagged when its `main` HEAD commit is itself already older than `threshold_min` (a
    fresh merge gets the benefit of the doubt — the build may still be running) AND its `:latest`
    image is either absent from AR entirely or older than that commit by more than `threshold_min`.
    """
    findings: list[dict[str, object]] = []
    now = dt.datetime.now(dt.UTC)
    for repo in _ldr_main_repos():
        image_paths = _latest_image_paths_for_repo(repo, project_id)
        if not image_paths:
            continue  # no cloudbuild.yaml / unreadable / no resolvable :latest ref — nothing to measure
        head = _main_head_commit(repo)
        if head is None:
            continue
        sha, commit_time = head
        commit_age_min = (now - commit_time).total_seconds() / 60
        if commit_age_min < threshold_min:
            continue  # too soon to expect a finished build — never a false page on a fresh merge
        for image_path in image_paths:
            image_time = _ar_latest_tag_update_time(image_path)
            if image_time is None:
                findings.append(
                    {
                        "repo": repo,
                        "image": image_path,
                        "sha": sha,
                        "commit_age_min": round(commit_age_min),
                        "staleness_min": None,
                        "reason": (
                            "no :latest tag found in Artifact Registry — image never built, or the AR query failed"
                        ),
                    }
                )
                continue
            staleness_min = (commit_time - image_time).total_seconds() / 60
            if staleness_min > threshold_min:
                findings.append(
                    {
                        "repo": repo,
                        "image": image_path,
                        "sha": sha,
                        "commit_age_min": round(commit_age_min),
                        "staleness_min": round(staleness_min),
                        "reason": f":latest is {round(staleness_min)}m older than main HEAD {sha}",
                    }
                )
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold-min", type=int, default=90)
    ap.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    ap.add_argument("--slack", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    threshold_min = cast("int", args.threshold_min)
    project_id = cast("str", args.project_id)

    findings = scan(threshold_min, project_id)

    if cast("bool", args.json):
        print(json.dumps({"findings": findings}, indent=2))
        return 1 if findings else 0

    if not findings:
        print(f"✅ stale-deployed-image: all ldr_main repos' :latest images within {threshold_min}m of main HEAD")
        return 0

    if cast("bool", args.slack):
        _max_lines = 6
        repos_affected = sorted({str(f["repo"]) for f in findings})
        header = (
            f":rotating_light: *STALE DEPLOYED IMAGE* — {len(findings)} `:latest` image(s) across "
            f"{len(repos_affected)} repo(s) behind their `main` HEAD by >{threshold_min}m"
        )
        body_lines = [f"  • {f['repo']}: {f['reason']}" for f in findings[:_max_lines]]
        if len(findings) > _max_lines:
            body_lines.append(f"  • … +{len(findings) - _max_lines} more (full list in the workflow log)")
        pointer = "→ re-trigger via `gcloud builds triggers run <repo>-prod --branch=main --substitutions=_SHA=<sha>`"
        cli_hint = "  (the same manual unblock used for instruments-service PR #983 — see the issue doc)"
        print(header + "\\n" + "\\n".join(body_lines) + "\\n" + pointer + "\\n" + cli_hint)
    else:
        print(f"⚠️  stale-deployed-image ({len(findings)}):")
        for f in findings:
            print(f"  - {f['repo']}: {f['reason']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
