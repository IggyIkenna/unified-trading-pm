#!/usr/bin/env python3
"""
Mark completed Data I/O / Features & ML project tasks as Done in GitHub Project 10.

Reads from tasks/data-io-project-10-completed.yaml and updates project item status.
Issues may be in: instruments-service, features-delta-one-service, ml-training-service,
ml-inference-service, unified-trading-deployment-v2.

Prerequisites:
  gh auth refresh -s project   # Add project scope to gh token
"""

import json
import subprocess
import sys

# Completed issue numbers from data-io-project-10-completed.yaml
COMPLETED_ISSUES = [
    197,
    201,
    207,
    212,
    216,
    220,
    224,
    228,
    232,
    236,
    240,
    243,
    246,
    249,
    251,
    252,
    253,
    254,
    255,
    256,
    420,
    421,
    449,
    439,
    440,
    441,
    443,
    448,
    450,
    451,
    454,
]

PROJECT_NUMBER = 10
OWNER = "IggyIkenna"
STATUS_FIELD_ID = "PVTSSF_lAHOAn7P7c4BPohzzg9_H5M"
DONE_OPTION_ID = "98236657"
PROJECT_ID = "PVT_kwHOAn7P7c4BPohz"


def run_gh(args: list[str]) -> str:
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh failed: {result.stderr}")
    return result.stdout


def get_all_project_items() -> list[dict]:
    """Fetch all items from project 10 (paginated)."""
    items = []
    cursor = None
    while True:
        args = [
            "project",
            "item-list",
            str(PROJECT_NUMBER),
            "--owner",
            OWNER,
            "--format",
            "json",
            "--limit",
            "100",
        ]
        if cursor:
            args.extend(["--cursor", cursor])
        data = json.loads(run_gh(args))
        batch = data.get("items", [])
        items.extend(batch)
        if not batch or len(batch) < 100:
            break
        # Pagination - gh may not support cursor in item-list; if so we get all in one go
        if len(batch) < 100:
            break
        cursor = data.get("cursor")
        if not cursor:
            break
    return items


def main() -> int:
    print("Fetching project items...")
    items = get_all_project_items()
    print(f"Found {len(items)} total items")

    completed_set = set(COMPLETED_ISSUES)
    to_update = []
    for item in items:
        content = item.get("content", {})
        num = content.get("number")
        if num and num in completed_set:
            repo = content.get("repository", "?")
            title = content.get("title", "?")[:50]
            status = item.get("status", "?")
            to_update.append((item["id"], num, repo, title, status))

    print(f"\nTasks to mark Done: {len(to_update)}")
    for item_id, num, repo, title, status in to_update:
        print(f"  #{num} ({repo}) {title}... [current: {status}]")

    if not to_update:
        print("No matching items found. Check issue numbers and project.")
        return 1

    if "--yes" not in sys.argv and "-y" not in sys.argv:
        confirm = input("\nProceed? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return 0

    updated = 0
    for item_id, num, repo, title, status in to_update:
        if status == "Done":
            print(f"  #{num} already Done, skip")
            continue
        try:
            run_gh(
                [
                    "project",
                    "item-edit",
                    "--id",
                    item_id,
                    "--project-id",
                    PROJECT_ID,
                    "--field-id",
                    STATUS_FIELD_ID,
                    "--single-select-option-id",
                    DONE_OPTION_ID,
                ]
            )
            print(f"  #{num} -> Done")
            updated += 1
        except (OSError, PermissionError, ValueError) as e:
            print(f"  #{num} FAILED: {e}")

    print(f"\nUpdated {updated} items to Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
