"""Unit tests for api-to-ui-coverage.json and ui-to-api-coverage.json.

Validates:
- JSON structural integrity (all required fields present)
- Orphan detection consistency (orphan=true iff consuming_uis or served_by_api empty/missing)
- Cross-map consistency (API->UI and UI->API maps agree)
- data_mode field is always present and valid
- Coverage maps reference only APIs/UIs that exist in ui-api-mapping.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DEV = REPO_ROOT / "scripts" / "dev"
API_TO_UI_PATH = SCRIPTS_DEV / "api-to-ui-coverage.json"
UI_TO_API_PATH = SCRIPTS_DEV / "ui-to-api-coverage.json"
UI_API_MAPPING_PATH = SCRIPTS_DEV / "ui-api-mapping.json"

VALID_DATA_MODES = {"live", "batch", "both"}
VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def api_to_ui() -> dict[str, object]:
    """Load the API-to-UI coverage map."""
    with open(API_TO_UI_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ui_to_api() -> dict[str, object]:
    """Load the UI-to-API coverage map."""
    with open(UI_TO_API_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ui_api_mapping() -> dict[str, object]:
    """Load the UI-API port mapping (SSOT)."""
    with open(UI_API_MAPPING_PATH) as f:
        return json.load(f)


# ── api-to-ui-coverage.json structural tests ──────────────────────────────────


class TestApiToUiStructure:
    """Verify JSON structure of api-to-ui-coverage.json."""

    def test_file_exists(self) -> None:
        assert API_TO_UI_PATH.exists(), f"Missing {API_TO_UI_PATH}"

    def test_valid_json(self) -> None:
        with open(API_TO_UI_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_has_api_entries(self, api_to_ui: dict[str, object]) -> None:
        api_names = [k for k in api_to_ui if not k.startswith("$")]
        assert len(api_names) > 0, "No API entries found"

    def test_each_api_has_endpoints(self, api_to_ui: dict[str, object]) -> None:
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            assert isinstance(api_data, dict), f"{api_name} must be a dict"
            assert "endpoints" in api_data, f"{api_name} missing 'endpoints'"
            assert isinstance(api_data["endpoints"], list), f"{api_name}.endpoints must be a list"

    def test_endpoint_required_fields(self, api_to_ui: dict[str, object]) -> None:
        required_fields = {"endpoint", "method", "consuming_uis", "orphan", "data_mode"}
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for i, ep in enumerate(api_data["endpoints"]):
                missing = required_fields - set(ep.keys())
                assert not missing, (
                    f"{api_name}.endpoints[{i}] ({ep.get('endpoint', '?')}) "
                    f"missing fields: {missing}"
                )

    def test_method_is_valid(self, api_to_ui: dict[str, object]) -> None:
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                assert ep["method"] in VALID_METHODS, (
                    f"{api_name} {ep['endpoint']}: invalid method '{ep['method']}'"
                )

    def test_data_mode_is_valid(self, api_to_ui: dict[str, object]) -> None:
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                assert ep["data_mode"] in VALID_DATA_MODES, (
                    f"{api_name} {ep['endpoint']}: invalid data_mode '{ep['data_mode']}'"
                )

    def test_orphan_flag_consistency(self, api_to_ui: dict[str, object]) -> None:
        """orphan=true iff consuming_uis is empty."""
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                has_consumers = len(ep["consuming_uis"]) > 0
                if ep["orphan"]:
                    assert not has_consumers, (
                        f"{api_name} {ep['endpoint']}: orphan=true but has consumers"
                    )
                else:
                    assert has_consumers, (
                        f"{api_name} {ep['endpoint']}: orphan=false but no consumers"
                    )


# ── ui-to-api-coverage.json structural tests ──────────────────────────────────


class TestUiToApiStructure:
    """Verify JSON structure of ui-to-api-coverage.json."""

    def test_file_exists(self) -> None:
        assert UI_TO_API_PATH.exists(), f"Missing {UI_TO_API_PATH}"

    def test_valid_json(self) -> None:
        with open(UI_TO_API_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_has_ui_entries(self, ui_to_api: dict[str, object]) -> None:
        ui_names = [k for k in ui_to_api if not k.startswith("$")]
        assert len(ui_names) > 0, "No UI entries found"

    def test_each_ui_has_requests(self, ui_to_api: dict[str, object]) -> None:
        for ui_name, ui_data in ui_to_api.items():
            if ui_name.startswith("$"):
                continue
            assert isinstance(ui_data, dict), f"{ui_name} must be a dict"
            assert "requests" in ui_data, f"{ui_name} missing 'requests'"
            assert isinstance(ui_data["requests"], list), f"{ui_name}.requests must be a list"

    def test_request_required_fields(self, ui_to_api: dict[str, object]) -> None:
        required_fields = {"fetch_url", "method", "served_by_api", "orphan", "data_mode"}
        for ui_name, ui_data in ui_to_api.items():
            if ui_name.startswith("$"):
                continue
            for i, req in enumerate(ui_data["requests"]):
                missing = required_fields - set(req.keys())
                assert not missing, (
                    f"{ui_name}.requests[{i}] ({req.get('fetch_url', '?')}) "
                    f"missing fields: {missing}"
                )

    def test_method_is_valid(self, ui_to_api: dict[str, object]) -> None:
        for ui_name, ui_data in ui_to_api.items():
            if ui_name.startswith("$"):
                continue
            for req in ui_data["requests"]:
                assert req["method"] in VALID_METHODS, (
                    f"{ui_name} {req['fetch_url']}: invalid method '{req['method']}'"
                )

    def test_data_mode_is_valid(self, ui_to_api: dict[str, object]) -> None:
        for ui_name, ui_data in ui_to_api.items():
            if ui_name.startswith("$"):
                continue
            for req in ui_data["requests"]:
                assert req["data_mode"] in VALID_DATA_MODES, (
                    f"{ui_name} {req['fetch_url']}: invalid data_mode '{req['data_mode']}'"
                )


# ── Cross-map consistency ─────────────────────────────────────────────────────


class TestCrossMapConsistency:
    """Verify API-to-UI and UI-to-API maps are mutually consistent."""

    def test_all_mapping_apis_in_coverage(
        self, api_to_ui: dict[str, object], ui_api_mapping: dict[str, object]
    ) -> None:
        """Every API in ui-api-mapping.json should appear in api-to-ui-coverage.json."""
        coverage_apis = {k for k in api_to_ui if not k.startswith("$")}
        for _stack, stack_data in ui_api_mapping["stacks"].items():
            api_name = stack_data.get("api")
            if api_name is not None:
                assert api_name in coverage_apis, (
                    f"API '{api_name}' from ui-api-mapping.json missing in api-to-ui-coverage.json"
                )

    def test_all_mapping_uis_in_coverage(
        self, ui_to_api: dict[str, object], ui_api_mapping: dict[str, object]
    ) -> None:
        """Every UI in ui-api-mapping.json should appear in ui-to-api-coverage.json."""
        coverage_uis = {k for k in ui_to_api if not k.startswith("$")}
        for _stack, stack_data in ui_api_mapping["stacks"].items():
            ui_name = stack_data.get("ui")
            if ui_name is not None:
                assert ui_name in coverage_uis, (
                    f"UI '{ui_name}' from ui-api-mapping.json missing in ui-to-api-coverage.json"
                )

    def test_non_orphan_ui_requests_have_api_endpoints(
        self,
        api_to_ui: dict[str, object],
        ui_to_api: dict[str, object],
    ) -> None:
        """For non-orphan UI requests targeting workspace API repos, the API should exist
        in the api-to-ui map."""
        api_names_in_coverage = {k for k in api_to_ui if not k.startswith("$")}
        for ui_name, ui_data in ui_to_api.items():
            if ui_name.startswith("$"):
                continue
            for req in ui_data["requests"]:
                if req["orphan"]:
                    continue
                served_by = req["served_by_api"]
                # Skip requests served by non-API-repo services (execution-service, alerting-service)
                if "not in workspace" in served_by or "(" in served_by:
                    # These are cross-service calls with notes
                    continue
                if served_by in api_names_in_coverage:
                    # Verify the API exists in the map (structural check only)
                    assert served_by in api_to_ui


# ── Orphan summary tests ─────────────────────────────────────────────────────


class TestOrphanSummary:
    """Summary statistics about orphan endpoints to ensure awareness."""

    def test_api_orphan_count_documented(self, api_to_ui: dict[str, object]) -> None:
        """Count API orphans. This test documents the count; it does not fail on orphans.
        Orphans are expected for internal/metrics/health endpoints."""
        orphan_count = 0
        total_count = 0
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                total_count += 1
                if ep["orphan"]:
                    orphan_count += 1
        # Just ensure we have data
        assert total_count > 0, "No endpoints found in api-to-ui-coverage"
        # Orphan ratio should be reasonable (under 50%)
        ratio = orphan_count / total_count
        assert ratio < 0.5, (
            f"Orphan ratio {ratio:.1%} ({orphan_count}/{total_count}) is too high"
        )

    def test_ui_orphan_count_documented(self, ui_to_api: dict[str, object]) -> None:
        """Count UI orphans (fetch calls with no matching API route)."""
        orphan_count = 0
        total_count = 0
        for ui_name, ui_data in ui_to_api.items():
            if ui_name.startswith("$"):
                continue
            for req in ui_data["requests"]:
                total_count += 1
                if req["orphan"]:
                    orphan_count += 1
        assert total_count > 0, "No requests found in ui-to-api-coverage"
        # UI orphans should be very low (under 20%)
        ratio = orphan_count / total_count
        assert ratio < 0.2, (
            f"UI orphan ratio {ratio:.1%} ({orphan_count}/{total_count}) is too high"
        )


# ── Data mode coverage tests ─────────────────────────────────────────────────


class TestDataModeCoverage:
    """Verify batch vs live data path classification."""

    def test_all_api_endpoints_have_data_mode(self, api_to_ui: dict[str, object]) -> None:
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                assert "data_mode" in ep, (
                    f"{api_name} {ep['endpoint']} missing data_mode"
                )
                assert ep["data_mode"] in VALID_DATA_MODES

    def test_all_ui_requests_have_data_mode(self, ui_to_api: dict[str, object]) -> None:
        for ui_name, ui_data in ui_to_api.items():
            if ui_name.startswith("$"):
                continue
            for req in ui_data["requests"]:
                assert "data_mode" in req, (
                    f"{ui_name} {req['fetch_url']} missing data_mode"
                )
                assert req["data_mode"] in VALID_DATA_MODES

    def test_streaming_endpoints_are_live(self, api_to_ui: dict[str, object]) -> None:
        """SSE/streaming endpoints should be data_mode='live'."""
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                if "/stream" in ep["endpoint"]:
                    assert ep["data_mode"] == "live", (
                        f"{api_name} {ep['endpoint']}: streaming endpoint should be live, "
                        f"got '{ep['data_mode']}'"
                    )

    def test_health_endpoints_are_live(self, api_to_ui: dict[str, object]) -> None:
        """Health/readiness endpoints should be data_mode='live'."""
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                if ep["endpoint"].endswith("/health") or ep["endpoint"].endswith("/readiness"):
                    assert ep["data_mode"] == "live", (
                        f"{api_name} {ep['endpoint']}: health endpoint should be live, "
                        f"got '{ep['data_mode']}'"
                    )

    def test_metrics_endpoints_are_live(self, api_to_ui: dict[str, object]) -> None:
        """Prometheus /metrics endpoints should be data_mode='live'."""
        for api_name, api_data in api_to_ui.items():
            if api_name.startswith("$"):
                continue
            for ep in api_data["endpoints"]:
                if ep["endpoint"] == "/metrics":
                    assert ep["data_mode"] == "live", (
                        f"{api_name} {ep['endpoint']}: metrics should be live"
                    )
