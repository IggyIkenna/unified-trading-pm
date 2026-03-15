#!/usr/bin/env python3
# SCHEMA_PROVENANCE_EXEMPT — PM-internal tooling model, not a domain schema
"""
Track workflow success metrics.

Metrics tracked:
- Drift detection rate
- Duplication rate
- Automation rate
- Cycle time
- Quality gate pass rate
- Regeneration frequency

Usage:
  python track-metrics.py --repo OWNER/REPO --output metrics-report.json
  python track-metrics.py --repo OWNER/REPO --report-format markdown
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)

# Type alias
JsonDict = dict[str, object]


@dataclass
class WorkflowMetrics:
    """Workflow success metrics."""

    timestamp: str
    repo: str
    period_days: int

    # Drift detection
    drift_gaps_found: int
    drift_gaps_caught_before_review: int
    drift_detection_rate: float  # % caught before review

    # Duplication
    total_issues_created: int
    duplicate_issues_created: int
    duplication_rate: float  # %

    # Automation
    total_tasks_completed: int
    total_automation_tasks: int  # Auto-pickup + Auto-close
    semi_auto_front_tasks: int  # Human pickup + Auto-close
    semi_auto_back_tasks: int  # Auto-pickup + Human UAT
    full_human_loop_tasks: int  # Human pickup + Human UAT
    automation_rate: float  # % total automation

    # Cycle time (days)
    avg_cycle_time_total_auto: float
    avg_cycle_time_semi_auto: float
    avg_cycle_time_full_human: float
    avg_cycle_time_overall: float

    # Quality gates
    total_quickmerge_attempts: int
    first_time_pass: int
    quality_gate_pass_rate: float  # %

    # Regeneration
    total_regenerations: int
    avg_regenerations_per_epic: float
    max_regeneration_hit_count: int  # Issues hitting 3-regen limit


def _run_gh(args: list[str]) -> str:
    """Run gh CLI command and return stdout."""
    result: subprocess.CompletedProcess[str] = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _parse_issues(raw: str) -> list[JsonDict]:
    """Parse JSON string into a list of issue dicts."""
    if not raw:
        return []
    raw_parsed: object = cast(object, json.loads(raw))
    if isinstance(raw_parsed, list):
        return [cast(JsonDict, item) for item in cast(list[object], raw_parsed) if isinstance(item, dict)]
    return []


def _get_issues_created_in_period(repo: str, days: int) -> list[JsonDict]:
    """Get all issues created in the last N days."""
    since_date: datetime = datetime.now(timezone.utc) - timedelta(days=days)
    since_str: str = since_date.strftime("%Y-%m-%d")

    result: str = _run_gh(
        [
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--search",
            f"created:>={since_str}",
            "--limit",
            "1000",
            "--json",
            "number,title,body,labels,createdAt,closedAt,state",
        ]
    )

    return _parse_issues(result)


def _get_pr_checks_in_period(repo: str, days: int) -> list[JsonDict]:
    """Get all PR check runs in the last N days."""
    since_date: datetime = datetime.now(timezone.utc) - timedelta(days=days)
    since_str: str = since_date.strftime("%Y-%m-%d")

    result: str = _run_gh(
        [
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--search",
            f"created:>={since_str}",
            "--limit",
            "1000",
            "--json",
            "number,createdAt,mergedAt,mergeable,statusCheckRollup",
        ]
    )

    return _parse_issues(result)


def _get_body(issue: JsonDict) -> str:
    """Safely get issue body as string."""
    return str(issue.get("body", ""))


def _get_labels(issue: JsonDict) -> list[str]:
    """Safely get label names from issue."""
    raw_labels: object = issue.get("labels") or []
    if isinstance(raw_labels, list):
        labels_list: list[JsonDict] = [
            cast(JsonDict, lb) for lb in cast(list[object], raw_labels) if isinstance(lb, dict)
        ]
        return [str(lb.get("name", "")) for lb in labels_list]
    return []


def calculate_drift_metrics(issues: list[JsonDict]) -> tuple[int, int, float]:
    """Calculate drift detection metrics."""
    drift_issues: list[JsonDict] = [i for i in issues if "gap-id:" in _get_body(i)]
    gaps_found: int = len(drift_issues)

    # Check how many were caught by diff checker vs human report
    caught_before_review: int = sum(1 for i in drift_issues if "detected by: diff-checker" in _get_body(i).lower())

    detection_rate: float = (caught_before_review / gaps_found * 100) if gaps_found > 0 else 0.0

    return gaps_found, caught_before_review, detection_rate


def calculate_duplication_metrics(issues: list[JsonDict]) -> tuple[int, int, float]:
    """Calculate duplication metrics."""
    total_created: int = len(issues)

    # Check for regeneration markers
    duplicates: int = 0
    for i in issues:
        body: str = _get_body(i)
        if "regeneration-count:" in body:
            try:
                count_str: str = body.split("regeneration-count:")[1].split()[0].strip()
                if int(count_str) > 0:
                    duplicates += 1
            except (ValueError, IndexError):
                pass

    duplication_rate: float = (duplicates / total_created * 100) if total_created > 0 else 0.0

    return total_created, duplicates, duplication_rate


def calculate_automation_metrics(issues: list[JsonDict]) -> tuple[int, int, int, int, int, float]:
    """Calculate automation rate by quadrant."""
    closed_issues: list[JsonDict] = [i for i in issues if str(i.get("state", "")) == "closed"]
    total_completed: int = len(closed_issues)

    # Classify by automation quadrant
    # Use labels and body content to determine quadrant
    total_auto: int = 0
    semi_auto_front: int = 0
    semi_auto_back: int = 0
    full_human: int = 0

    for issue in closed_issues:
        body: str = _get_body(issue).lower()
        labels: list[str] = _get_labels(issue)

        # Determine quadrant based on markers
        auto_close: bool = "auto-closed" in body
        review_required: bool = "review required: yes" in body or "uat-required" in labels

        if auto_close and not review_required:
            # Check if it was auto-pickup
            if "auto-fixable: yes" in body or "refactor" in labels:
                total_auto += 1
            else:
                semi_auto_front += 1
        elif not auto_close and review_required:
            # Check if it was auto-pickup
            if "auto-fixable: no" in body and "feature" not in labels:
                semi_auto_back += 1
            else:
                full_human += 1

    automation_rate: float = (total_auto / total_completed * 100) if total_completed > 0 else 0.0

    return (
        total_completed,
        total_auto,
        semi_auto_front,
        semi_auto_back,
        full_human,
        automation_rate,
    )


def calculate_cycle_time_metrics(issues: list[JsonDict]) -> tuple[float, float, float, float]:
    """Calculate average cycle time by automation type."""
    closed_issues: list[JsonDict] = [i for i in issues if str(i.get("state", "")) == "closed" and i.get("closedAt")]

    total_auto_times: list[float] = []
    semi_auto_times: list[float] = []
    full_human_times: list[float] = []

    for issue in closed_issues:
        created_str: str = str(issue.get("createdAt", "")).replace("Z", "+00:00")
        closed_str: str = str(issue.get("closedAt", "")).replace("Z", "+00:00")
        created: datetime = datetime.fromisoformat(created_str)
        closed: datetime = datetime.fromisoformat(closed_str)
        cycle_time: float = (closed - created).total_seconds() / 86400  # days

        body: str = _get_body(issue).lower()
        labels: list[str] = _get_labels(issue)

        # Classify by automation type
        if "auto-closed" in body and "auto-fixable: yes" in body:
            total_auto_times.append(cycle_time)
        elif "review required: yes" in body or "uat-required" in labels:
            full_human_times.append(cycle_time)
        else:
            semi_auto_times.append(cycle_time)

    avg_total_auto: float = sum(total_auto_times) / len(total_auto_times) if total_auto_times else 0.0
    avg_semi_auto: float = sum(semi_auto_times) / len(semi_auto_times) if semi_auto_times else 0.0
    avg_full_human: float = sum(full_human_times) / len(full_human_times) if full_human_times else 0.0
    all_times: list[float] = total_auto_times + semi_auto_times + full_human_times
    avg_overall: float = sum(all_times) / len(all_times) if all_times else 0.0

    return avg_total_auto, avg_semi_auto, avg_full_human, avg_overall


def calculate_quality_gate_metrics(prs: list[JsonDict]) -> tuple[int, int, float]:
    """Calculate quality gate pass rate."""
    total_attempts: int = len(prs)

    first_time_pass: int = 0
    for pr in prs:
        raw_rollup: object = pr.get("statusCheckRollup")
        if not raw_rollup or not isinstance(raw_rollup, list):
            continue
        checks: list[JsonDict] = [cast(JsonDict, c) for c in cast(list[object], raw_rollup) if isinstance(c, dict)]
        if all(
            str(check.get("conclusion", "")) == "success"
            for check in checks
            if str(check.get("__typename", "")) == "CheckRun"
        ):
            first_time_pass += 1

    pass_rate: float = (first_time_pass / total_attempts * 100) if total_attempts > 0 else 0.0

    return total_attempts, first_time_pass, pass_rate


def calculate_regeneration_metrics(issues: list[JsonDict]) -> tuple[int, float, int]:
    """Calculate regeneration frequency."""
    # Count total regenerations
    total_regenerations: int = 0
    epic_regen_counts: dict[str, int] = {}
    max_regen_hits: int = 0

    for issue in issues:
        body: str = _get_body(issue)

        # Extract regeneration count
        if "regeneration-count:" in body:
            try:
                count_str: str = body.split("regeneration-count:")[1].split()[0].strip()
                count: int = int(count_str)
                total_regenerations += count

                # Track by epic
                if "epic-ref:" in body:
                    epic_ref: str = body.split("epic-ref:")[1].split()[0].strip()
                    epic_regen_counts[epic_ref] = epic_regen_counts.get(epic_ref, 0) + count

                # Track issues hitting max (3)
                if count >= 3:
                    max_regen_hits += 1

            except (ValueError, IndexError) as e:
                logger.debug(
                    "Suppressed %s during calculate regeneration metrics: %s",
                    type(e).__name__,
                    e,
                )

    num_epics: int = len(epic_regen_counts)
    avg_per_epic: float = sum(epic_regen_counts.values()) / num_epics if num_epics > 0 else 0.0

    return total_regenerations, avg_per_epic, max_regen_hits


def collect_metrics(repo: str, period_days: int) -> WorkflowMetrics:
    """Collect all workflow metrics."""
    print(f"Collecting metrics for {repo} over last {period_days} days...")

    # Fetch data
    issues: list[JsonDict] = _get_issues_created_in_period(repo, period_days)
    prs: list[JsonDict] = _get_pr_checks_in_period(repo, period_days)

    print(f"  Found {len(issues)} issues and {len(prs)} PRs")

    # Calculate metrics
    drift_found, drift_caught, drift_rate = calculate_drift_metrics(issues)
    total_created, duplicates, dup_rate = calculate_duplication_metrics(issues)
    (
        completed,
        total_auto,
        semi_front,
        semi_back,
        full_human,
        auto_rate,
    ) = calculate_automation_metrics(issues)
    (
        cycle_total_auto,
        cycle_semi,
        cycle_full,
        cycle_overall,
    ) = calculate_cycle_time_metrics(issues)
    qg_attempts, qg_pass, qg_rate = calculate_quality_gate_metrics(prs)
    total_regen, avg_regen, max_regen = calculate_regeneration_metrics(issues)

    return WorkflowMetrics(
        timestamp=datetime.now(timezone.utc).isoformat(),
        repo=repo,
        period_days=period_days,
        drift_gaps_found=drift_found,
        drift_gaps_caught_before_review=drift_caught,
        drift_detection_rate=drift_rate,
        total_issues_created=total_created,
        duplicate_issues_created=duplicates,
        duplication_rate=dup_rate,
        total_tasks_completed=completed,
        total_automation_tasks=total_auto,
        semi_auto_front_tasks=semi_front,
        semi_auto_back_tasks=semi_back,
        full_human_loop_tasks=full_human,
        automation_rate=auto_rate,
        avg_cycle_time_total_auto=cycle_total_auto,
        avg_cycle_time_semi_auto=cycle_semi,
        avg_cycle_time_full_human=cycle_full,
        avg_cycle_time_overall=cycle_overall,
        total_quickmerge_attempts=qg_attempts,
        first_time_pass=qg_pass,
        quality_gate_pass_rate=qg_rate,
        total_regenerations=total_regen,
        avg_regenerations_per_epic=avg_regen,
        max_regeneration_hit_count=max_regen,
    )


def _format_markdown_header(metrics: WorkflowMetrics) -> str:
    """Format report header with metadata."""
    return f"""# Workflow Metrics Report

**Generated:** {metrics.timestamp}
**Repository:** {metrics.repo}
**Period:** Last {metrics.period_days} days

---

"""


def _format_markdown_drift_section(metrics: WorkflowMetrics) -> str:
    """Format drift detection section."""
    det_status: str = "PASS" if metrics.drift_detection_rate >= 90 else "WARN"
    det_analysis: str = (
        "Strong drift prevention"
        if metrics.drift_detection_rate >= 90
        else "Needs improvement - increase diff checker coverage"
    )
    return f"""## 1. Drift Detection

- **Gaps found:** {metrics.drift_gaps_found}
- **Caught before human review:** {metrics.drift_gaps_caught_before_review}
- **Detection rate:** {metrics.drift_detection_rate:.1f}% [{det_status}] (target: 90%+)

**Analysis:** {det_analysis}

---

"""


def _format_markdown_duplication_section(metrics: WorkflowMetrics) -> str:
    """Format duplication prevention section."""
    dup_status: str = "PASS" if metrics.duplication_rate < 2 else "WARN"
    dup_analysis: str = (
        "Excellent duplication prevention"
        if metrics.duplication_rate < 2
        else "Review marker system - duplicates detected"
    )
    return f"""## 2. Duplication Prevention

- **Total issues created:** {metrics.total_issues_created}
- **Duplicate issues:** {metrics.duplicate_issues_created}
- **Duplication rate:** {metrics.duplication_rate:.1f}% [{dup_status}] (target: <2%)

**Analysis:** {dup_analysis}

---

"""


def _format_markdown_automation_section(metrics: WorkflowMetrics) -> str:
    """Format automation effectiveness section."""
    auto_status: str = "PASS" if metrics.automation_rate >= 60 else "WARN"
    max_completed: int = max(metrics.total_tasks_completed, 1)
    bar_auto: str = "X" * int(metrics.total_automation_tasks / max_completed * 20)
    bar_front: str = "X" * int(metrics.semi_auto_front_tasks / max_completed * 20)
    bar_back: str = "X" * int(metrics.semi_auto_back_tasks / max_completed * 20)
    bar_human: str = "X" * int(metrics.full_human_loop_tasks / max_completed * 20)
    return f"""## 3. Automation Effectiveness

- **Total tasks completed:** {metrics.total_tasks_completed}
- **Total automation (auto-pickup + auto-close):** {metrics.total_automation_tasks}
- **Semi-auto front (human pickup + auto-close):** {metrics.semi_auto_front_tasks}
- **Semi-auto back (auto-pickup + human UAT):** {metrics.semi_auto_back_tasks}
- **Full human loop:** {metrics.full_human_loop_tasks}
- **Automation rate:** {metrics.automation_rate:.1f}% [{auto_status}] (target: 60%+)

**Distribution:**
```
Total Auto:    {bar_auto} {metrics.total_automation_tasks}
Semi Front:    {bar_front} {metrics.semi_auto_front_tasks}
Semi Back:     {bar_back} {metrics.semi_auto_back_tasks}
Full Human:    {bar_human} {metrics.full_human_loop_tasks}
```

---

"""


def _format_markdown_cycle_time_section(metrics: WorkflowMetrics) -> str:
    """Format cycle time section."""
    return f"""## 4. Cycle Time

- **Total automation:** {metrics.avg_cycle_time_total_auto:.1f} days
- **Semi-automation:** {metrics.avg_cycle_time_semi_auto:.1f} days
- **Full human loop:** {metrics.avg_cycle_time_full_human:.1f} days
- **Overall average:** {metrics.avg_cycle_time_overall:.1f} days

**Analysis:** Total automation should be <2 days. Semi-auto <5 days. Full human <10 days.

---

"""


def _format_markdown_quality_gate_section(metrics: WorkflowMetrics) -> str:
    """Format quality gate performance section."""
    qg_status: str = "PASS" if metrics.quality_gate_pass_rate >= 90 else "WARN"
    qg_analysis: str = (
        "Excellent quality - agents understanding standards well"
        if metrics.quality_gate_pass_rate >= 90
        else "Review common failures - may need better agent guidance"
    )
    return f"""## 5. Quality Gate Performance

- **Total quickmerge attempts:** {metrics.total_quickmerge_attempts}
- **First-time pass:** {metrics.first_time_pass}
- **Pass rate:** {metrics.quality_gate_pass_rate:.1f}% [{qg_status}] (target: 90%+)

**Analysis:** {qg_analysis}

---

"""


def _format_markdown_regeneration_section(metrics: WorkflowMetrics) -> str:
    """Format regeneration frequency section."""
    regen_status: str = "PASS" if metrics.avg_regenerations_per_epic < 1.5 else "WARN"
    regen_analysis: str = (
        "Stable epic generation"
        if metrics.avg_regenerations_per_epic < 1.5
        else "Review epic generator - too much churn"
    )
    return f"""## 6. Regeneration Frequency

- **Total regenerations:** {metrics.total_regenerations}
- **Average per epic:** {metrics.avg_regenerations_per_epic:.2f} [{regen_status}] (target: <1.5)
- **Issues hitting 3-regen limit:** {metrics.max_regeneration_hit_count}

**Analysis:** {regen_analysis}

---

"""


def _format_markdown_footer(metrics: WorkflowMetrics) -> str:
    """Format overall health score and recommendations header."""
    passing: int = sum(
        [
            metrics.drift_detection_rate >= 90,
            metrics.duplication_rate < 2,
            metrics.automation_rate >= 60,
            metrics.quality_gate_pass_rate >= 90,
            metrics.avg_regenerations_per_epic < 1.5,
        ]
    )
    overall_status: str = "HEALTHY" if passing == 5 else "NEEDS ATTENTION"
    return f"""## Overall Health Score

{overall_status}

**Passing targets:** {passing}/5

---

## Recommendations

"""


def format_markdown_report(metrics: WorkflowMetrics) -> str:
    """Format metrics as markdown report."""
    return (
        _format_markdown_header(metrics)
        + _format_markdown_drift_section(metrics)
        + _format_markdown_duplication_section(metrics)
        + _format_markdown_automation_section(metrics)
        + _format_markdown_cycle_time_section(metrics)
        + _format_markdown_quality_gate_section(metrics)
        + _format_markdown_regeneration_section(metrics)
        + _format_markdown_footer(metrics)
    )


def calculate_recommendations(metrics: WorkflowMetrics) -> list[str]:
    """Generate recommendations based on metrics."""
    recommendations: list[str] = []

    if metrics.drift_detection_rate < 90:
        recommendations.append("- Expand diff checker coverage to catch more violations")

    if metrics.duplication_rate >= 2:
        recommendations.append("- Review marker system - ensure all scripts use consistent markers")

    if metrics.automation_rate < 60:
        recommendations.append("- Review auto-pickup criteria - may be too conservative")

    if metrics.quality_gate_pass_rate < 90:
        recommendations.append("- Analyze common quality gate failures and improve agent guidance")

    if metrics.avg_regenerations_per_epic >= 1.5:
        recommendations.append("- Review epic generator stability - reduce unnecessary regenerations")

    if not recommendations:
        recommendations.append("- All metrics healthy - continue current practices")

    return recommendations


def main() -> int:
    parser = argparse.ArgumentParser(description="Track workflow success metrics")
    parser.add_argument("--repo", required=True, help="Target repo (OWNER/REPO)")
    parser.add_argument("--period-days", type=int, default=7, help="Period to analyze (days)")
    parser.add_argument("--output", type=Path, help="Output JSON file")
    parser.add_argument("--report-format", choices=["json", "markdown"], default="json", help="Output format")

    parsed = parser.parse_args()

    repo: str = str(getattr(parsed, "repo", ""))
    period_days: int = int(getattr(parsed, "period_days", 7))
    raw_output: object = getattr(parsed, "output", None)
    output: Path | None = cast(Path, raw_output) if isinstance(raw_output, Path) else None
    report_format: str = str(getattr(parsed, "report_format", "json"))

    try:
        # Collect metrics
        metrics: WorkflowMetrics = collect_metrics(repo, period_days)

        # Output based on format
        if report_format == "markdown":
            report: str = format_markdown_report(metrics)
            recommendations: list[str] = calculate_recommendations(metrics)
            full_report: str = report + "\n".join(recommendations) + "\n"

            if output is not None:
                output.write_text(full_report)
                print(f"\nMarkdown report written to {output}")
            else:
                print(full_report)

        else:  # json
            metrics_dict: dict[str, object] = cast(dict[str, object], asdict(metrics))

            if output is not None:
                output.write_text(json.dumps(metrics_dict, indent=2))
                print(f"\nJSON metrics written to {output}")
            else:
                print(json.dumps(metrics_dict, indent=2))

        # Print summary to console
        print("\n=== Metrics Summary ===")
        print(f"Drift detection rate: {metrics.drift_detection_rate:.1f}%")
        print(f"Duplication rate: {metrics.duplication_rate:.1f}%")
        print(f"Automation rate: {metrics.automation_rate:.1f}%")
        print(f"Quality gate pass rate: {metrics.quality_gate_pass_rate:.1f}%")
        print(f"Avg regenerations per epic: {metrics.avg_regenerations_per_epic:.2f}")

        return 0

    except (OSError, PermissionError, ValueError) as e:
        print(f"Error collecting metrics: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
