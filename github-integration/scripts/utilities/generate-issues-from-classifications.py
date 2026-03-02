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
from typing import Dict, List

if importlib.util.find_spec("yaml") is None:
    print("ERROR: PyYAML not installed. Run: uv pip install pyyaml")
    sys.exit(1)

import yaml


class GitHubIssueGenerator:
    """Generate GitHub issues from classification data."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.codex_root = workspace_root / "unified-trading-codex"
        self.classifications_dir = self.codex_root / "11-project-management" / "task-classifications"

        # Load mappings
        self.blocker_mapping = self._load_json(self.codex_root / "10-audit" / "blocker-dependency-spec.json")
        self.validator_mapping = self._load_yaml(self.codex_root / "10-audit" / "validator-epic-mapping.yaml")

    def _load_json(self, path: Path) -> Dict:
        """Load JSON file."""
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def _load_yaml(self, path: Path) -> Dict:
        """Load YAML file."""
        if not path.exists():
            return {}
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def generate_issues_for_epic(self, epic_name: str, dry_run: bool = False) -> List[Dict]:
        """Generate issues for a single epic."""
        classification_file = self.classifications_dir / f"{epic_name}-classification.json"

        if not classification_file.exists():
            print(f"❌ Classification not found: {classification_file}")
            return []

        with open(classification_file, "r") as f:
            data = json.load(f)

        issues = []
        for task in data.get("tasks", []):
            issue = self._create_issue(task, epic_name)
            issues.append(issue)

            if not dry_run:
                print(f"   📝 {issue['title']}")

        return issues

    def _create_issue(self, task: Dict, epic_name: str) -> Dict:
        """Create GitHub issue structure from task."""
        # Build title
        title = f"[{epic_name.upper()}] {task['title']}"

        # Build body
        body_parts = [
            f"## Task: {task['title']}",
            "",
            f"**Epic:** {epic_name}",
            f"**Task ID:** {task['task_id']}",
            f"**Owner:** {task['owner']}",
            f"**Classification:** {task['classification']}",
            f"**Priority:** {task['priority']}",
            f"**Estimated:** {task['estimated_hours']}",
            f"**Complexity:** {task['complexity']}",
            "",
        ]

        # Add checklist items if available
        if task.get("checklist_items"):
            body_parts.extend(["## Related Checklist Items", ""])
            for item in task["checklist_items"]:
                body_parts.append(f"- [ ] {item}")
            body_parts.append("")

        # Add validators if available
        if task.get("validators"):
            body_parts.extend(["## Automated Validators", ""])
            for validator in task["validators"]:
                body_parts.append(f"- `{validator}`")
            body_parts.append("")

        # Add acceptance criteria
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
                f"*Auto-generated from epic classification: {task['classification']}*",
            ]
        )

        body = "\n".join(body_parts)

        # Determine labels
        labels = [
            f"epic:{epic_name}",
            f"classification:{task['classification'].lower()}",
            f"priority:{task['priority'].lower()}",
            f"owner:{task['owner'].lower()}",
        ]

        # Add blocker labels
        blockers = self._determine_blockers(task, epic_name)
        for blocker in blockers:
            labels.append(f"blocker:{blocker}")

        return {
            "title": title,
            "body": body,
            "labels": labels,
            "assignee": task["owner"].lower() if task["owner"] != "Unknown" else None,
            "metadata": {
                "epic": epic_name,
                "task_id": task["task_id"],
                "classification": task["classification"],
                "estimated_hours": task["estimated_hours"],
            },
        }

    def _determine_blockers(self, task: Dict, epic_name: str) -> List[str]:
        """Determine blocker types for task."""
        blockers = []

        # Check classification
        if task["classification"] == "IMPLEMENT":
            blockers.extend(["D4-code-structure", "D5-implementation"])
        elif task["classification"] == "VALIDATE":
            blockers.extend(["D3-quality-gates", "D6-testing"])

        # Check if data-dependent
        if "data" in task["title"].lower() or "catalogue" in task["title"].lower():
            blockers.append("D1-data")

        # Check if requires auth/packages
        if "auth" in task["title"].lower() or "package" in task["title"].lower():
            blockers.append("D2-auth-package")

        return blockers

    def generate_all_issues(self, dry_run: bool = False) -> Dict[str, List[Dict]]:
        """Generate issues for all epics."""
        all_issues = {}

        classification_files = list(self.classifications_dir.glob("*-classification.json"))

        print(f"\n🚀 Generating issues for {len(classification_files)} epics...\n")

        for classification_file in sorted(classification_files):
            if classification_file.stem == "all-epics-classification-summary":
                continue

            epic_name = classification_file.stem.replace("-classification", "")
            print(f"📊 {epic_name}:")

            issues = self.generate_issues_for_epic(epic_name, dry_run)
            all_issues[epic_name] = issues

            print(f"   ✅ Generated {len(issues)} issues\n")

        return all_issues

    def save_issues(self, all_issues: Dict[str, List[Dict]], output_dir: Path):
        """Save generated issues to JSON files."""
        output_dir.mkdir(parents=True, exist_ok=True)

        for epic_name, issues in all_issues.items():
            output_file = output_dir / f"{epic_name}-github-issues.json"

            with open(output_file, "w") as f:
                json.dump({"epic": epic_name, "total_issues": len(issues), "issues": issues}, f, indent=2)

            print(f"   💾 Saved: {output_file.name}")

        # Save aggregate
        aggregate_file = output_dir / "all-github-issues.json"
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

        print(f"\n✅ Aggregate: {aggregate_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate GitHub issues from classifications")
    parser.add_argument("--epic", help="Specific epic to process")
    parser.add_argument("--all", action="store_true", help="Process all epics")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (don't save)")
    parser.add_argument(
        "--output-dir",
        default="unified-trading-codex/11-project-management/github-integration/generated-issues",
        help="Output directory",
    )
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    generator = GitHubIssueGenerator(workspace_root)

    if args.all:
        all_issues = generator.generate_all_issues(args.dry_run)

        if not args.dry_run:
            output_dir = workspace_root / args.output_dir
            generator.save_issues(all_issues, output_dir)

        print("\n" + "=" * 80)
        print("ISSUE GENERATION COMPLETE")
        print("=" * 80)
        total = sum(len(issues) for issues in all_issues.values())
        print(f"Total Issues Generated: {total}")

    elif args.epic:
        issues = generator.generate_issues_for_epic(args.epic, args.dry_run)
        print(f"\n✅ Generated {len(issues)} issues for {args.epic}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
