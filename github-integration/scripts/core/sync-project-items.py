#!/usr/bin/env python3
"""
Create/fetch a GitHub Project and add issues from artifact plans.

Primary inputs:
  - feature-cards-plan.json
  - delta-audit-plan.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _run_gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=check,
    )


def _assert_project_scope(owner: str) -> None:
    proc = _run_gh(["project", "list", "--owner", owner], check=False)
    if proc.returncode == 0:
        return
    stderr = (proc.stderr or "") + "\n" + (proc.stdout or "")
    if "read:project" in stderr or "project" in stderr.lower():
        raise RuntimeError(
            "Missing GitHub project scopes. Run:\n"
            "  gh auth refresh --hostname github.com -s read:project -s project\n"
            "Then re-run this script."
        )
    raise RuntimeError(stderr.strip() or "Unable to query GitHub Projects.")


def _get_project_number(owner: str, title: str) -> int | None:
    r = _run_gh(["project", "list", "--owner", owner, "--format", "json"])
    parsed = json.loads(r.stdout or "{}")
    if isinstance(parsed, dict):
        data = parsed.get("projects", [])
    elif isinstance(parsed, list):
        data = parsed
    else:
        data = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if str(item.get("title", "")).strip().lower() == title.strip().lower():
            return int(item["number"])
    return None


def _ensure_project(owner: str, title: str, dry_run: bool) -> int:
    existing = _get_project_number(owner, title)
    if existing is not None:
        print(f"Using existing project: {owner}/{title} (#{existing})")
        return existing

    if dry_run:
        print(f"[DRY-RUN] Would create project: {owner}/{title}")
        return -1

    _run_gh(["project", "create", "--owner", owner, "--title", title])
    created = _get_project_number(owner, title)
    if created is None:
        raise RuntimeError(f"Project was created but not found by title: {title}")
    print(f"Created project: {owner}/{title} (#{created})")
    return created


def _load_titles(plan_path: Path) -> list[str]:
    raw = json.loads(plan_path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return [str(x.get("title", "")).strip() for x in raw if isinstance(x, dict) and x.get("title")]
    if isinstance(raw, dict):
        titles: list[str] = []
        for key in ("epics", "discovery"):
            vals = raw.get(key, [])
            if isinstance(vals, list):
                for x in vals:
                    if isinstance(x, dict) and x.get("title"):
                        titles.append(str(x["title"]).strip())
        return titles
    return []


def _find_issue_url(repo: str, title: str) -> str | None:
    r = _run_gh(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--search",
            f'in:title "{title}"',
            "--json",
            "title,url",
            "--limit",
            "100",
        ]
    )
    data = json.loads(r.stdout or "[]")
    for item in data:
        if str(item.get("title", "")).strip() == title:
            return str(item.get("url", "")).strip()
    return None


def _add_issue_to_project(owner: str, project_number: int, issue_url: str, dry_run: bool) -> bool:
    if dry_run:
        print(f"  [DRY-RUN] add to project #{project_number}: {issue_url}")
        return True
    cmd = [
        "project",
        "item-add",
        str(project_number),
        "--owner",
        owner,
        "--url",
        issue_url,
    ]
    proc = _run_gh(cmd, check=False)
    if proc.returncode == 0:
        return True
    err = (proc.stderr or "") + (proc.stdout or "")
    if "already exists" in err.lower():
        return True
    print(f"  WARN project add failed for {issue_url}: {err.strip()}", file=sys.stderr)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Create/fetch project and add issue items from plan JSON.")
    parser.add_argument("--owner", required=True, help="Project owner (user or org).")
    parser.add_argument("--repo", required=True, help="Issue repo (owner/name).")
    parser.add_argument("--project-title", required=True, help="GitHub Project title.")
    parser.add_argument(
        "--plan-json",
        action="append",
        required=True,
        help="Plan JSON file path (can pass multiple times).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview only.")
    args = parser.parse_args()

    _assert_project_scope(args.owner)

    project_number = _ensure_project(args.owner, args.project_title, args.dry_run)

    titles: list[str] = []
    for path_str in args.plan_json:
        path = Path(path_str)
        if not path.exists():
            print(f"WARN missing plan json: {path}", file=sys.stderr)
            continue
        titles.extend(_load_titles(path))

    # deterministic de-dup while preserving order
    deduped: list[str] = []
    seen = set()
    for t in titles:
        if not t or t in seen:
            continue
        deduped.append(t)
        seen.add(t)

    if not deduped:
        print("No issue titles found in plan files.")
        return 0

    added = 0
    missing = 0
    for title in deduped:
        url = _find_issue_url(args.repo, title)
        if not url:
            print(f"  MISSING ISSUE: {title}")
            missing += 1
            continue
        if _add_issue_to_project(args.owner, project_number, url, args.dry_run):
            added += 1

    print(f"\nDone: {added} added, {missing} missing-issue-titles, total-target={len(deduped)}")
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
