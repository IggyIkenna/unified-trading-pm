#!/usr/bin/env python3
"""
Generate GitHub Issues from Epic Classifications

Reads classification data and generates GitHub issues with proper labels,
dependencies, and metadata for project automation.

Usage:
    python generate-issues-from-classifications.py --epic data-io-production-readiness
    python generate-issues-from-classifications.py --all --dry-run
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import cast

if importlib.util.find_spec("yaml") is None:
    print("ERROR: PyYAML not installed. Run: uv pip install pyyaml")
    sys.exit(1)

import yaml

# Type alias
JsonDict = dict[str, object]


class GitHubIssueGenerator:
    """Generate GitHub issues from classification data."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root: Path = workspace_root
        self.codex_root: Path = workspace_root / "unified-trading-codex"
        self.classifications_dir: Path = self.codex_root / "11-project-management" / "task-classifications"

        # Load mappings
        self.blocker_mapping: JsonDict = self._load_json(
            self.codex_root / "10-audit" / "blocker-dependency-spec.json",
        )
        self.validator_mapping: JsonDict = self._load_yaml(
            self.codex_root / "10-audit" / "validator-epic-mapping.yaml",
        )

    def _load_json(self, path: Path) -> JsonDict:
        """Load JSON file."""
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return cast(JsonDict, json.load(f))

    def _load_yaml(self, path: Path) -> JsonDict:
        """Load YAML file."""
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return cast(JsonDict, yaml.safe_load(f) or {})

    def generate_issues_for_epic(self, epic_name: str, dry_run: bool = False) -> list[JsonDict]:
        """Generate issues for a single epic."""
        classification_file: Path = self.classifications_dir / f"{epic_name}-classification.json"

        if not classification_file.exists():
            print(f"  Classification not found: {classification_file}")
            return []

        with open(classification_file, "r") as f:
            data: JsonDict = cast(JsonDict, json.load(f))

        raw_tasks: object = data.get("tasks") or []
        tasks: list[JsonDict] = (
            [cast(JsonDict, t) for t in cast(list[object], raw_tasks) if isinstance(t, dict)]
            if isinstance(raw_tasks, list)
            else []
        )

        issues: list[JsonDict] = []
        for task in tasks:
            issue: JsonDict = self._create_issue(task, epic_name)
            issues.append(issue)

            if not dry_run:
                print(f"   {issue.get('title', '')}")

        return issues

    def _create_issue(self, task: JsonDict, epic_name: str) -> JsonDict:
        """Create GitHub issue structure from task."""
        task_title: str = str(task.get("title", ""))
        task_id: str = str(task.get("task_id", ""))
        task_owner: str = str(task.get("owner", "Unknown"))
        task_classification: str = str(task.get("classification", ""))
        task_estimated: str = str(task.get("estimated_hours", ""))
        body: str = self._build_issue_body(task, epic_name)
        labels: list[str] = self._build_issue_labels(task, epic_name)
        title: str = f"[{epic_name.upper()}] {task_title}"
        return {
            "title": title,
            "body": body,
            "labels": labels,
            "assignee": task_owner.lower() if task_owner != "Unknown" else None,
            "metadata": {
                "epic": epic_name,
                "task_id": task_id,
                "classification": task_classification,
                "estimated_hours": task_estimated,
            },
        }

    def _build_issue_body(self, task: JsonDict, epic_name: str) -> str:
        """Build body markdown for issue."""
        task_title: str = str(task.get("title", ""))
        task_id: str = str(task.get("task_id", ""))
        task_owner: str = str(task.get("owner", "Unknown"))
        task_classification: str = str(task.get("classification", ""))
        task_priority: str = str(task.get("priority", ""))
        task_estimated: str = str(task.get("estimated_hours", ""))
        task_complexity: str = str(task.get("complexity", ""))
        body_parts: list[str] = [
            f"## Task: {task_title}",
            "",
            f"**Epic:** {epic_name}",
            f"**Task ID:** {task_id}",
            f"**Owner:** {task_owner}",
            f"**Classification:** {task_classification}",
            f"**Priority:** {task_priority}",
            f"**Estimated:** {task_estimated}",
            f"**Complexity:** {task_complexity}",
            "",
        ]
        raw_checklist: object = task.get("checklist_items")
        if raw_checklist and isinstance(raw_checklist, list):
            checklist_items: list[str] = [str(c) for c in cast(list[object], raw_checklist)]
            body_parts.extend(["## Related Checklist Items", ""])
            for item in checklist_items:
                body_parts.append(f"- [ ] {item}")
            body_parts.append("")
        raw_validators: object = task.get("validators")
        if raw_validators and isinstance(raw_validators, list):
            validators: list[str] = [str(v) for v in cast(list[object], raw_validators)]
            body_parts.extend(["## Automated Validators", ""])
            for validator in validators:
                body_parts.append(f"- `{validator}`")
            body_parts.append("")
        body_parts.extend(
            [
                "## Acceptance Criteria",
                "",
                "- [ ] Code implemented and tested",
                "- [ ] Quality gates pass",
                "- [ ] Documentation updated",
                "- [ ] Validators pass (if applicable)",
                "",
                "---",
                f"*Auto-generated from epic classification: {task_classification}*",
            ]
        )
        return "\n".join(body_parts)

    def _build_issue_labels(self, task: JsonDict, epic_name: str) -> list[str]:
        """Build labels list for issue."""
        task_owner: str = str(task.get("owner", "Unknown"))
        task_classification: str = str(task.get("classification", ""))
        task_priority: str = str(task.get("priority", ""))
        labels: list[str] = [
            f"epic:{epic_name}",
            f"classification:{task_classification.lower()}",
            f"priority:{task_priority.lower()}",
            f"owner:{task_owner.lower()}",
        ]
        blockers: list[str] = self._determine_blockers(task, epic_name)
        for blocker in blockers:
            labels.append(f"blocker:{blocker}")
        return labels

    def _determine_blockers(self, task: JsonDict, epic_name: str) -> list[str]:
        """Determine blocker types for task."""
        _ = self.blocker_mapping, epic_name  # Used for context
        blockers: list[str] = []

        task_classification: str = str(task.get("classification", ""))
        task_title: str = str(task.get("title", "")).lower()

        # Check classification
        if task_classification == "IMPLEMENT":
            blockers.extend(["D4-code-structure", "D5-implementation"])
        elif task_classification == "VALIDATE":
            blockers.extend(["D3-quality-gates", "D6-testing"])

        # Check if data-dependent
        if "data" in task_title or "catalogue" in task_title:
            blockers.append("D1-data")

        # Check if requires auth/packages
        if "auth" in task_title or "package" in task_title:
            blockers.append("D2-auth-package")

        return blockers

    def generate_all_issues(self, dry_run: bool = False) -> dict[str, list[JsonDict]]:
        """Generate issues for all epics."""
        all_issues: dict[str, list[JsonDict]] = {}

        classification_files: list[Path] = list(self.classifications_dir.glob("*-classification.json"))

        print(f"\n  Generating issues for {len(classification_files)} epics...\n")

        for classification_file in sorted(classification_files):
            if classification_file.stem == "all-epics-classification-summary":
                continue

            epic_name: str = classification_file.stem.replace("-classification", "")
            print(f"  {epic_name}:")

            issues: list[JsonDict] = self.generate_issues_for_epic(epic_name, dry_run)
            all_issues[epic_name] = issues

            print(f"   Generated {len(issues)} issues\n")

        return all_issues

    def save_issues(self, all_issues: dict[str, list[JsonDict]], output_dir: Path) -> None:
        """Save generated issues to JSON files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        for epic_name, issues in all_issues.items():
            output_file: Path = output_dir / f"{epic_name}-github-issues.json"

            with open(output_file, "w") as f:
                json.dump(
                    {"epic": epic_name, "total_issues": len(issues), "issues": issues},
                    f,
                    indent=2,
                )

            print(f"   Saved: {output_file.name}")

        # Save aggregate
        aggregate_file: Path = output_dir / "all-github-issues.json"
        with open(aggregate_file, "w") as f:
            json.dump(
                {
                    "total_epics": len(all_issues),
                    "total_issues": sum(len(issues) for issues in all_issues.values()),
                    "by_epic": {name: len(issues) for name, issues in all_issues.items()},
                    "issues": all_issues,
                },
                f,
                indent=2,
            )

        print(f"\n  Aggregate: {aggregate_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate GitHub issues from classifications")
    parser.add_argument("--epic", help="Specific epic to process")
    parser.add_argument("--all", action="store_true", help="Process all epics")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't save)")
    parser.add_argument(
        "--output-dir",
        default="unified-trading-codex/11-project-management/github-integration/generated-issues",
        help="Output directory",
    )
    parsed = parser.parse_args()

    epic_arg: str = str(getattr(parsed, "epic", "") or "")
    all_flag: bool = bool(getattr(parsed, "all", False))
    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    output_dir_str: str = str(getattr(parsed, "output_dir", ""))

    workspace_root: Path = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    generator = GitHubIssueGenerator(workspace_root)

    if all_flag:
        all_issues: dict[str, list[JsonDict]] = generator.generate_all_issues(dry_run)

        if not dry_run:
            output_dir: Path = workspace_root / output_dir_str
            generator.save_issues(all_issues, output_dir)

        print("\n" + "=" * 80)
        print("ISSUE GENERATION COMPLETE")
        print("=" * 80)
        total: int = sum(len(issues) for issues in all_issues.values())
        print(f"Total Issues Generated: {total}")

    elif epic_arg:
        issues: list[JsonDict] = generator.generate_issues_for_epic(epic_arg, dry_run)
        print(f"\n  Generated {len(issues)} issues for {epic_arg}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
