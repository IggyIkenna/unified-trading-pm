"""Unit tests for ci_failure_watcher billing-block detection.

The GitHub Actions billing/spending-limit outage (incident 2026-06-08) freezes ALL CI
fleet-wide — every job fails at "Set up job" with 0 steps + a check-run annotation
carrying the spending-limit text. These tests cover the pure annotation matcher and the
build_report wiring (network-free; the live scan `detect_billing_block` is integration,
not unit). SSOT: cicd_contract_hardening_2026_06_01.md § "Auto-remediation pipeline gaps".
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    watcher_path = repo_root / "scripts" / "repo-management" / "ci_failure_watcher.py"
    stub = types.ModuleType("pin_branch_protection_rulesets")
    stub.ORG = "IggyIkenna"  # type: ignore[attr-defined]
    stub.REPOS = []  # type: ignore[attr-defined]
    sys.modules.setdefault("pin_branch_protection_rulesets", stub)
    spec = importlib.util.spec_from_file_location("ci_failure_watcher", watcher_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()
_annotation_is_billing = MOD._annotation_is_billing  # type: ignore[attr-defined]
build_report = MOD.build_report  # type: ignore[attr-defined]


class TestAnnotationIsBilling:
    def test_real_github_spending_limit_message(self) -> None:
        msg = (
            "The job was not started because recent account payments have failed or your "
            "spending limit needs to be increased. Please check the 'Billing & plans' "
            "section in your settings"
        )
        assert _annotation_is_billing([msg]) is True

    def test_spending_limit_phrase(self) -> None:
        assert _annotation_is_billing(["your spending limit needs to be increased"]) is True

    def test_case_insensitive(self) -> None:
        assert _annotation_is_billing(["RECENT ACCOUNT PAYMENTS have failed"]) is True

    def test_unrelated_failure_is_not_billing(self) -> None:
        assert _annotation_is_billing(["Process completed with exit code 1"]) is False

    def test_empty_and_none(self) -> None:
        assert _annotation_is_billing([]) is False
        assert _annotation_is_billing(["", ""]) is False


class TestBuildReportBilling:
    def test_billing_forces_critical_alert(self) -> None:
        billing = {"repo": "unified-trading-pm", "workflow": "tab-mirror-to-ldr", "url": "https://x/run/1"}
        alert, severity, report = build_report([], [], [], billing)
        assert alert is True
        assert severity == "CRITICAL"
        assert "BILLING BLOCK" in report
        assert "Billing & plans" in report

    def test_no_billing_when_none(self) -> None:
        alert, severity, report = build_report([], [], [], None)
        assert alert is False
        assert severity == "INFO"
        assert "BILLING BLOCK" not in report
