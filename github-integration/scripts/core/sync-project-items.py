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
from typing import cast

# Type alias
JsonDict = dict[str, object]


def _run_gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _assert_project_scope(owner: str) -> None:
    proc: subprocess.CompletedProcess[str] = _run_gh(
        ["project", "list", "--owner", owner],
        check=False,
    )
    if proc.returncode == 0:
        return
    stderr: str = (proc.stderr or "") + "\n" + (proc.stdout or "")
    if "read:project" in stderr or "project" in stderr.lower():
        raise RuntimeError(
            "Missing GitHub project scopes. Run:\n"
            "  gh auth refresh --hostname github.com -s read:project -s project\n"
            "Then re-run this script."
        )
    raise RuntimeError(stderr.strip() or "Unable to query GitHub Projects.")


def _get_project_number(owner: str, title: str) -> int | None:
    r: subprocess.CompletedProcess[str] = _run_gh(
        ["project", "list", "--owner", owner, "--format", "json"],
    )
    parsed: object = cast(object, json.loads(r.stdout or "{}"))
    data: list[object]
    if isinstance(parsed, dict):
        parsed_dict: JsonDict = cast(JsonDict, parsed)
        raw_projects: object = parsed_dict.get("projects", [])
        data = cast(list[object], raw_projects) if isinstance(raw_projects, list) else []
    elif isinstance(parsed, list):
        data = cast(list[object], parsed)
    else:
        data = []
    for item_raw in data:
        if not isinstance(item_raw, dict):
            continue
        item: JsonDict = cast(JsonDict, item_raw)
        if str(item.get("title", "")).strip().lower() == title.strip().lower():
            return int(str(item.get("number", 0)))
    return None


def _ensure_project(owner: str, title: str, dry_run: bool) -> int:
    existing: int | None = _get_project_number(owner, title)
    if existing is not None:
        print(f"Using existing project: {owner}/{title} (#{existing})")
        return existing

    if dry_run:
        print(f"[DRY-RUN] Would create project: {owner}/{title}")
        return -1

    _run_gh(["project", "create", "--owner", owner, "--title", title])
    created: int | None = _get_project_number(owner, title)
    if created is None:
        raise RuntimeError(f"Project was created but not found by title: {title}")
    print(f"Created project: {owner}/{title} (#{created})")
    return created


def _load_titles(plan_path: Path) -> list[str]:
    raw: object = cast(object, json.loads(plan_path.read_text(encoding="utf-8")))
    if isinstance(raw, list):
        raw_list: list[object] = cast(list[object], raw)
        return [
            str(cast(JsonDict, x).get("title", "")).strip()
            for x in raw_list
            if isinstance(x, dict) and cast(JsonDict, x).get("title")
        ]
    if isinstance(raw, dict):
        raw_dict: JsonDict = cast(JsonDict, raw)
        titles: list[str] = []
        for key in ("epics", "discovery"):
            vals_raw: object = raw_dict.get(key, [])
            if isinstance(vals_raw, list):
                vals: list[object] = cast(list[object], vals_raw)
                for x in vals:
                    if isinstance(x, dict):
                        xd: JsonDict = cast(JsonDict, x)
                        if xd.get("title"):
                            titles.append(str(xd["title"]).strip())
        return titles
    return []


def _find_issue_url(repo: str, title: str) -> str | None:
    r: subprocess.CompletedProcess[str] = _run_gh(
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
    data: list[object] = cast(list[object], json.loads(r.stdout or "[]"))
    for item_raw in data:
        if not isinstance(item_raw, dict):
            continue
        item: JsonDict = cast(JsonDict, item_raw)
        if str(item.get("title", "")).strip() == title:
            return str(item.get("url", "")).strip()
    return None


def _add_issue_to_project(
    owner: str,
    project_number: int,
    issue_url: str,
    dry_run: bool,
) -> bool:
    if dry_run:
        print(f"  [DRY-RUN] add to project #{project_number}: {issue_url}")
        return True
    cmd: list[str] = [
        "project",
        "item-add",
        str(project_number),
        "--owner",
        owner,
        "--url",
        issue_url,
    ]
    proc: subprocess.CompletedProcess[str] = _run_gh(cmd, check=False)
    if proc.returncode == 0:
        return True
    err: str = (proc.stderr or "") + (proc.stdout or "")
    if "already exists" in err.lower():
        return True
    print(f"  WARN project add failed for {issue_url}: {err.strip()}", file=sys.stderr)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create/fetch project and add issue items from plan JSON.",
    )
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
    parsed = parser.parse_args()

    owner: str = str(getattr(parsed, "owner", ""))
    repo: str = str(getattr(parsed, "repo", ""))
    project_title: str = str(getattr(parsed, "project_title", ""))
    plan_json_raw: object = getattr(parsed, "plan_json", [])
    plan_json_list: list[str] = cast(list[str], plan_json_raw) if isinstance(plan_json_raw, list) else []
    dry_run: bool = bool(getattr(parsed, "dry_run", False))

    _assert_project_scope(owner)

    project_number: int = _ensure_project(owner, project_title, dry_run)

    titles: list[str] = []
    for path_str in plan_json_list:
        path = Path(path_str)
        if not path.exists():
            print(f"WARN missing plan json: {path}", file=sys.stderr)
            continue
        titles.extend(_load_titles(path))

    # deterministic de-dup while preserving order
    deduped: list[str] = []
    seen: set[str] = set()
    for t in titles:
        if not t or t in seen:
            continue
        deduped.append(t)
        seen.add(t)

    if not deduped:
        print("No issue titles found in plan files.")
        return 0

    added: int = 0
    missing: int = 0
    for title in deduped:
        url: str | None = _find_issue_url(repo, title)
        if not url:
            print(f"  MISSING ISSUE: {title}")
            missing += 1
            continue
        if _add_issue_to_project(owner, project_number, url, dry_run):
            added += 1

    print(f"\nDone: {added} added, {missing} missing-issue-titles, total-target={len(deduped)}")
    if missing:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
