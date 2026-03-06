"""Lib package for check-codex-violations."""

from .codex_violations import (
    DriftGap,
    check_for_existing_issue,
    create_github_issue,
    ensure_labels_exist,
    fetch_all_existing_issues,
    find_architecture_gaps,
    find_coding_standards_violations,
    find_domain_event_gaps,
    find_event_logging_gaps,
    gap_to_dict,
)

__all__ = [
    "DriftGap",
    "check_for_existing_issue",
    "create_github_issue",
    "ensure_labels_exist",
    "fetch_all_existing_issues",
    "find_architecture_gaps",
    "find_coding_standards_violations",
    "find_domain_event_gaps",
    "find_event_logging_gaps",
    "gap_to_dict",
]
