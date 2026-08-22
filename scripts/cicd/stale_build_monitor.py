#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Stale-build watcher — Gap 2 of
plans/active/issues/cloud_build_router_concurrency_drops_dispatch_2026_07_27.md.

The 2026-07-27 incident showed a `cloud-build-router.yml` dispatch can be silently CANCELLED
(a shared `change-freeze-check.yml` concurrency group, since fixed) — a repo's `main` merge goes
green on every CI signal (PR merged, quality-gates-v2 passed) while its deployed Cloud Run image
silently stays on the PREVIOUS build, indefinitely, with no error anywhere. That specific
concurrency bug is fixed, but there was (and is) no independent check that the dispatch actually
RESULTED in a fresh image — this is that check, a defence-in-depth safety net for THIS class of
silent drop and any future one like it.

For each `ldr_main` repo (`workspace-manifest.json`, `promotion_model == "ldr_main"`):
  1. Fetch the repo's `cloudbuild.yaml` at `main` and resolve every `:latest` entry in its
     `images:` list against the file's own `substitutions:` block (+ the Cloud Build builtin
     `$PROJECT_ID`). A repo whose `cloudbuild.yaml` is unreadable, or resolves NO `:latest` image
     (a library/test-harness repo with no continuously-deployed service image), is SKIPPED —
     never a false page for a repo that legitimately doesn't ship one.
  2. Read `main` HEAD's commit timestamp (`gh api repos/{OWNER}/{repo}/commits/main`).
  3. Read each resolved image's last-push timestamp in Artifact Registry
     (`gcloud artifacts docker images list <repo_path> --include-tags`, filtered locally to the
     `:latest`-tagged entry — mirrors `assert_deps_published_to_ar.py::_ar_versions`'s
     list-then-filter-locally style rather than assuming an exact JSON key/format).
  4. Flag STALE when `main_head_time - image_push_time > threshold` (default 45 min — a margin
     over the ~30 min max cloudbuild.yaml timeout plus dispatch/queue latency). An image whose
     push time could not be read (AR query error, no matching tagged entry) is SKIPPED, not
     flagged — ambiguity must never page (fail-open, mirrors every other cicd/ script here).

Stdlib + `gh` + `gcloud` only. Prints a human report; `--slack` prints a Slack-formatted block
(the workflow posts it verbatim). Exit 1 if any repo is stale (so an alert can gate on it).

Usage:
    stale_build_monitor.py [--threshold-min 45] [--repo NAME ...] [--slack] [--json]
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
from pathlib import Path
from typing import cast

OWNER = "IggyIkenna"

# GCP project id — env-only (no hardcoded prod project id in production code; the check for this
# lives in scripts/quality-gates-base/base-service.sh). Mirrors assert_deps_published_to_ar.py.
AR_PROJECT = os.environ.get("GCP_PROJECT_ID") or ""  # noqa: qg-gcp-project-id (cicd gate: project for the gcloud AR query)

# Matches the "substitutions:" YAML block (a flat, indented `_KEY: value` mapping — the observed
# convention across every cloudbuild.yaml in the fleet) up to the next top-level (column-0) key.
_SUBST_BLOCK_RE = re.compile(r"(?m)^substitutions:\s*\n((?:[ \t]+.*\n?)*)")
_SUBST_KV_RE = re.compile(r'(?m)^[ \t]+(_[A-Za-z0-9_]+):\s*"?([^"\n#]*?)"?\s*(?:#.*)?$')
_IMAGES_BLOCK_RE = re.compile(r"(?m)^images:\s*\n((?:[ \t]+.*\n?)*)")
_IMAGE_LINE_RE = re.compile(r'(?m)^[ \t]*-\s*"?([^"\n]+?)"?\s*$')
_VAR_TOKEN_RE = re.compile(r"\$\{?(_?[A-Za-z0-9_]+)\}?")


def _repos_json(manifest_path: Path) -> dict[str, object]:
    try:
        with manifest_path.open() as f:
            m = cast("dict[str, object]", json.load(f))
    except (OSError, ValueError):
        return {}
    repos = m.get("repositories")
    return repos if isinstance(repos, dict) else {}


def ldr_main_repos(manifest_path: Path) -> list[str]:
    """Every repo flagged `promotion_model == "ldr_main"` — the population this todo names."""
    repos = _repos_json(manifest_path)
    out: list[str] = []
    for name, cfg in repos.items():
        if str(name).startswith("_"):
            continue
        if isinstance(cfg, dict) and cast("dict[str, object]", cfg).get("promotion_model") == "ldr_main":
            out.append(str(name))
    return sorted(out)


def _extract_substitutions(text: str) -> dict[str, str]:
    m = _SUBST_BLOCK_RE.search(text)
    if not m:
        return {}
    return {km.group(1): km.group(2).strip() for km in _SUBST_KV_RE.finditer(m.group(1))}


def _resolve_vars(template: str, lookup: dict[str, str]) -> str | None:
    """Substitute every `$VAR`/`${VAR}` token; None (unresolved) if any token has no mapping."""
    missing = False

    def repl(m: re.Match[str]) -> str:
        nonlocal missing
        val = lookup.get(m.group(1))
        if val is None:
            missing = True
            return m.group(0)
        return val

    resolved = _VAR_TOKEN_RE.sub(repl, template)
    return None if missing else resolved


def extract_latest_images(cloudbuild_text: str, project_id: str) -> list[str]:
    """Every fully-resolved `:latest`-tagged image URL in the file's `images:` list."""
    m = _IMAGES_BLOCK_RE.search(cloudbuild_text)
    if not m:
        return []
    lookup = _extract_substitutions(cloudbuild_text)
    lookup["PROJECT_ID"] = project_id
    out: list[str] = []
    for line in _IMAGE_LINE_RE.finditer(m.group(1)):
        raw = line.group(1).strip()
        if not raw.endswith(":latest"):
            continue
        resolved = _resolve_vars(raw, lookup)
        if resolved is not None:
            out.append(resolved)
    return out


def split_image_ref(resolved: str) -> tuple[str, str] | None:
    """'HOST/PROJECT/AR_REPO[/...]/NAME:latest' -> (repo_path 'HOST/PROJECT/AR_REPO[/...]', NAME).

    None if the ref is too short to contain a repo path + image name, or isn't `:latest`.
    """
    if ":" not in resolved:
        return None
    path, _, tag = resolved.rpartition(":")
    if tag != "latest":
        return None
    parts = [p for p in path.split("/") if p]
    if len(parts) < 4:
        return None
    return "/".join(parts[:3]), "/".join(parts[3:])


def _fetch_text(repo: str, path: str, ref: str) -> str | None:
    """Fetch a text file from GitHub at `ref` via the contents API (base64-decoded)."""
    proc = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{repo}/contents/{path}?ref={ref}", "--jq", ".content"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        return base64.b64decode(proc.stdout.strip()).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


def main_head(repo: str, ref: str = "main") -> tuple[str, dt.datetime] | None:
    """(short_sha, committer_when) of `ref` HEAD; None on any error."""
    proc = subprocess.run(
        ["gh", "api", f"repos/{OWNER}/{repo}/commits/{ref}", "--jq", "{sha: .sha, date: .commit.committer.date}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        d = cast("dict[str, object]", json.loads(proc.stdout))
    except json.JSONDecodeError:
        return None
    sha = d.get("sha")
    date_s = d.get("date")
    if not sha or not date_s:
        return None
    try:
        when = dt.datetime.fromisoformat(str(date_s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return str(sha)[:7], when


def active_trigger_repos(project_id: str) -> set[str] | None:
    """Repo names with at least one non-disabled Cloud Build trigger; None if the query failed.

    A repo whose `cloudbuild.yaml` resolves a `:latest` image but has NO active trigger wired up
    (e.g. `unified-trading-system-ui`, confirmed 2026-07-29 via `gcloud builds triggers list`) has
    no continuous-build mechanism for this check to verify in the first place — its AR `:latest`
    entry is whatever was last pushed manually/one-off, and will read as stale forever regardless
    of how recently `main` committed. That is a monitor-config artifact, not a live incident
    (cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md). None (not an empty
    set) on a query error — fail-open, never silently exempt every repo because the call broke.
    """
    proc = subprocess.run(
        ["gcloud", "builds", "triggers", "list", "--project", project_id, "--format=json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        triggers = cast("list[object]", json.loads(proc.stdout))
    except json.JSONDecodeError:
        return None
    out: set[str] = set()
    for t in triggers:
        if not isinstance(t, dict):
            continue
        td = cast("dict[str, object]", t)
        if td.get("disabled") is True:
            continue
        rec = cast("dict[str, object]", td.get("repositoryEventConfig") or {})
        repo_path = str(rec.get("repository") or "")
        if repo_path:
            out.add(repo_path.rsplit("/", 1)[-1])
        gh = cast("dict[str, object]", td.get("github") or {})
        gh_name = str(gh.get("name") or "")
        if gh_name:
            out.add(gh_name)
    return out


def list_ar_images(repo_path: str) -> list[dict[str, object]]:
    """Raw `gcloud artifacts docker images list <repo_path> --include-tags` JSON; [] on any error."""
    proc = subprocess.run(
        ["gcloud", "artifacts", "docker", "images", "list", repo_path, "--include-tags", "--format=json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    try:
        d = cast("object", json.loads(proc.stdout))
    except json.JSONDecodeError:
        return []
    return cast("list[dict[str, object]]", d) if isinstance(d, list) else []


def _parse_ar_timestamp(raw: str) -> dt.datetime | None:
    try:
        return dt.datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.UTC)
    except ValueError:
        return None


def latest_push_time(images: list[dict[str, object]], image_name: str) -> dt.datetime | None:
    """Newest push time among AR entries tagged `latest` whose package tail matches `image_name`.

    Matches on the LAST path segment (mirrors `assert_deps_published_to_ar.py::_ar_versions`'s
    `rsplit("/", 1)[-1]` style) rather than an exact field-name/prefix assumption, since AR's
    `package` resource-path format is not something this repo has previously had to parse exactly.
    """
    best: dt.datetime | None = None
    for img in images:
        pkg = str(img.get("package") or img.get("IMAGE") or "")
        if pkg.rsplit("/", 1)[-1] != image_name:
            continue
        tags = img.get("tags")
        tag_list = tags if isinstance(tags, list) else ([tags] if isinstance(tags, str) else [])
        if "latest" not in tag_list:
            continue
        raw_ts = str(img.get("updateTime") or img.get("createTime") or img.get("uploadTime") or "")
        if not raw_ts:
            continue
        when = _parse_ar_timestamp(raw_ts)
        if when is not None and (best is None or when > best):
            best = when
    return best


def check_repo(
    repo: str,
    project_id: str,
    thresh_s: float,
    now: dt.datetime,
    ar_cache: dict[str, list[object]],
    trigger_repos: set[str] | None,
) -> str | None:
    """One finding line if `repo` is stale; None if not-stale OR the repo/query is ambiguous
    (fail-open — never page on a repo we could not affirmatively measure)."""
    if trigger_repos is not None and repo not in trigger_repos:
        return None  # no active Cloud Build trigger — nothing continuous to verify (fail-open scope)
    cloudbuild_text = _fetch_text(repo, "cloudbuild.yaml", "main")
    if cloudbuild_text is None:
        return None  # no cloudbuild.yaml on main (or transient gh error) — not this check's scope
    images = extract_latest_images(cloudbuild_text, project_id)
    if not images:
        return None  # no `:latest` image resolved — library/test-harness repo, not a deployed service

    head = main_head(repo, "main")
    if head is None:
        return None
    sha, head_when = head

    worst_gap_s = 0.0
    worst_image = ""
    for image_ref in images:
        split = split_image_ref(image_ref)
        if split is None:
            continue
        repo_path, image_name = split
        cached = ar_cache.get(repo_path)
        if cached is None:
            cached = cast("list[object]", list_ar_images(repo_path))
            ar_cache[repo_path] = cached
        push_when = latest_push_time(cast("list[dict[str, object]]", cached), image_name)
        if push_when is None:
            continue  # AR query error / no matching tagged entry — ambiguous, skip this image
        gap_s = (head_when - push_when).total_seconds()
        if gap_s > worst_gap_s:
            worst_gap_s = gap_s
            worst_image = image_name

    if worst_gap_s <= thresh_s:
        return None
    gap_m = int(worst_gap_s // 60)
    return (
        f":warning: {repo}@{sha} — `:latest` image `{worst_image}` is {gap_m}m older than `main` HEAD "
        f"(committed {int((now - head_when).total_seconds() // 60)}m ago) — image build/dispatch likely dropped"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--threshold-min",
        type=int,
        default=45,
        help="Staleness threshold in minutes — a margin over the ~30min max cloudbuild.yaml "
        "timeout plus dispatch/queue latency.",
    )
    ap.add_argument(
        "--repo", action="append", default=None, help="limit to these repo(s) (repeatable); default: all ldr_main repos"
    )
    ap.add_argument("--manifest", default=None, help="workspace-manifest.json path override")
    ap.add_argument("--project", default=AR_PROJECT, help="GCP project id (default: $GCP_PROJECT_ID)")
    ap.add_argument(
        "--now-iso", default="", help="UTC now override (no wallclock in CI sandbox); else uses gh server time"
    )
    ap.add_argument("--slack", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    thresh_s = cast(int, args.threshold_min) * 60.0
    project_id = cast(str, args.project)
    manifest_path = (
        Path(cast(str, args.manifest))
        if args.manifest
        else Path(__file__).resolve().parent.parent.parent / "workspace-manifest.json"
    )

    now_iso = cast(str, args.now_iso)
    if now_iso:
        now = dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    else:
        r = subprocess.run(["gh", "api", "-i", "rate_limit"], capture_output=True, text=True, check=False)
        now = None
        for line in r.stdout.splitlines():
            if line.lower().startswith("date:"):
                try:
                    now = dt.datetime.strptime(line[5:].strip(), "%a, %d %b %Y %H:%M:%S GMT").replace(tzinfo=dt.UTC)
                except ValueError:
                    now = None
                break
        if now is None:
            now = dt.datetime.now(dt.UTC)

    repos = cast("list[str] | None", args.repo) or ldr_main_repos(manifest_path)
    if not project_id:
        print("stale-build-monitor: no GCP project id ($GCP_PROJECT_ID/--project unset) — fail-open, skipping")
        return 0

    trigger_repos = active_trigger_repos(project_id)

    findings: list[str] = []
    ar_cache: dict[str, list[object]] = {}
    for repo in repos:
        line = check_repo(repo, project_id, thresh_s, now, ar_cache, trigger_repos)
        if line:
            findings.append(line)

    if cast("bool", args.as_json):
        print(json.dumps({"stale": findings}))
        return 1 if findings else 0

    if not findings:
        print(
            f"✅ stale-build-monitor: all {len(repos)} ldr_main repo(s) with a `:latest` image are "
            f"within {int(thresh_s // 60)}m of main HEAD"
        )
        return 0

    if cast("bool", args.slack):
        header = (
            f":building_construction: *stale-build-monitor: {len(findings)} repo(s) with a stale `:latest` image* "
            f"(> {int(thresh_s // 60)}m behind `main` HEAD)"
        )
        print(header + "\n" + "\n".join(sorted(findings)))
    else:
        print(f"⚠️  {len(findings)} repo(s) with a stale `:latest` image:")
        for f in sorted(findings):
            print(f"  - {f}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
