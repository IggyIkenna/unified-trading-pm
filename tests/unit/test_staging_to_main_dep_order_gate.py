"""Unit tests for STAGE 1.8 dep-order gate (staging → main).

Tests the Python snippet embedded in staging-to-main.yml's STAGE 1.8 step
in isolation, using fixture manifests. The gate logic is inlined here so
tests are not fragile against YAML formatting changes.

HERMETIC: no network, no git ops, no file I/O beyond tmp fixtures.
Run via: cd unified-trading-pm && bash scripts/quality-gates.sh
"""

from __future__ import annotations

from typing import Any

# ── Inline the STAGE 1.8 gate logic (must mirror staging-to-main.yml) ────────

ON_MAIN_STATUSES = {"MAIN_GREEN", "SIT_VALIDATED"}


def _run_dep_order_gate(manifest: dict[str, Any], promoting: list[str]) -> tuple[bool, list[str]]:
    """Returns (passed, blocked_pairs).

    blocked_pairs: list of "dep_name:dep_status" strings (empty when passed=True).
    Replicates the STAGE 1.8 Python logic in staging-to-main.yml exactly.
    """
    repos_data: dict[str, Any] = manifest.get("repositories", {})
    blocked_pairs: list[str] = []

    for repo in promoting:
        repo_info = repos_data.get(repo)
        if repo_info is None:
            continue  # safe-default pass: repo not in manifest

        deps: list[Any] = repo_info.get("dependencies", [])
        for dep in deps:
            dep_name = dep.get("name", dep) if isinstance(dep, dict) else str(dep)
            if not dep_name or dep_name not in repos_data:
                continue  # safe-default pass: dep not tracked
            dep_status = repos_data[dep_name].get("ci_status") or ""
            if not dep_status:
                continue  # safe-default pass: unset/None ci_status
            if dep_status not in ON_MAIN_STATUSES:
                blocked_pairs.append(f"{dep_name}:{dep_status}")

    passed = len(blocked_pairs) == 0
    return passed, blocked_pairs


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_manifest(dep_name: str, dep_status: str) -> dict[str, Any]:
    """Single-dep manifest: my-service depends on dep_name at dep_status."""
    return {
        "repositories": {
            "my-service": {"dependencies": [{"name": dep_name, "version": ">=0.1.0", "required": True}]},
            dep_name: {"ci_status": dep_status},
        }
    }


def _make_multi_dep_manifest(uac_status: str, utl_status: str) -> dict[str, Any]:
    """Two-dep manifest: my-service depends on uac + utl."""
    return {
        "repositories": {
            "my-service": {
                "dependencies": [
                    {"name": "uac", "version": ">=0.1.0"},
                    {"name": "utl", "version": ">=0.1.0"},
                ]
            },
            "uac": {"ci_status": uac_status},
            "utl": {"ci_status": utl_status},
        }
    }


# ── Tests: PASS cases ─────────────────────────────────────────────────────────


def test_gate_passes_when_dep_is_main_green() -> None:
    manifest = _make_manifest("uac", "MAIN_GREEN")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is True
    assert blocked == []


def test_gate_passes_when_dep_is_sit_validated() -> None:
    """SIT_VALIDATED is the valid on-main signal during the promotion window."""
    manifest = _make_manifest("uac", "SIT_VALIDATED")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is True
    assert blocked == []


def test_gate_passes_when_repo_has_no_deps() -> None:
    manifest = {
        "repositories": {
            "my-service": {"dependencies": []},
        }
    }
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is True
    assert blocked == []


def test_gate_passes_when_repo_not_in_manifest() -> None:
    """Safe-default: repo absent from manifest → gate skipped (PASS)."""
    manifest = {"repositories": {}}
    passed, blocked = _run_dep_order_gate(manifest, ["unknown-service"])
    assert passed is True
    assert blocked == []


def test_gate_passes_when_dep_not_in_manifest() -> None:
    """Safe-default: dep absent from repositories → PASS."""
    manifest = {
        "repositories": {
            "my-service": {
                "dependencies": [{"name": "external-dep"}],
            }
            # "external-dep" not present → safe-default pass
        }
    }
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is True
    assert blocked == []


def test_gate_passes_when_dep_ci_status_is_unset() -> None:
    """Safe-default: dep ci_status None/'' → treat as external / not tracked → PASS."""
    manifest = {
        "repositories": {
            "my-service": {"dependencies": [{"name": "uac"}]},
            "uac": {},  # ci_status key absent
        }
    }
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is True
    assert blocked == []


def test_gate_passes_with_empty_promoting_list() -> None:
    """Nothing being promoted → gate trivially passes."""
    manifest = _make_manifest("uac", "FEATURE_GREEN")
    passed, blocked = _run_dep_order_gate(manifest, [])
    assert passed is True
    assert blocked == []


def test_gate_passes_all_deps_on_main_multi_dep() -> None:
    manifest = _make_multi_dep_manifest("MAIN_GREEN", "MAIN_GREEN")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is True
    assert blocked == []


# ── Tests: BLOCK cases ────────────────────────────────────────────────────────


def test_gate_blocks_when_dep_is_feature_green() -> None:
    """FEATURE_GREEN means dep is on LDR/feature but NOT on main → BLOCK."""
    manifest = _make_manifest("uac", "FEATURE_GREEN")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is False
    assert "uac:FEATURE_GREEN" in blocked


def test_gate_blocks_when_dep_is_staging_green() -> None:
    """STAGING_GREEN means dep is on staging but NOT yet on main → BLOCK."""
    manifest = _make_manifest("utl", "STAGING_GREEN")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is False
    assert "utl:STAGING_GREEN" in blocked


def test_gate_blocks_when_dep_is_failing() -> None:
    manifest = _make_manifest("uac", "FAILING")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is False
    assert "uac:FAILING" in blocked


def test_gate_blocks_when_dep_is_local_pass() -> None:
    manifest = _make_manifest("utl", "LOCAL_PASS")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is False
    assert "utl:LOCAL_PASS" in blocked


def test_gate_blocks_when_dep_is_not_configured() -> None:
    manifest = _make_manifest("uac", "NOT_CONFIGURED")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is False
    assert "uac:NOT_CONFIGURED" in blocked


def test_gate_blocks_only_below_main_dep_in_multi_dep() -> None:
    """With uac=MAIN_GREEN, utl=STAGING_GREEN: only utl is blocked."""
    manifest = _make_multi_dep_manifest("MAIN_GREEN", "STAGING_GREEN")
    passed, blocked = _run_dep_order_gate(manifest, ["my-service"])
    assert passed is False
    assert any("utl:STAGING_GREEN" in b for b in blocked)
    assert not any("uac:" in b for b in blocked)


# ── Tests: ci_status lifecycle constants ─────────────────────────────────────


def test_on_main_statuses_are_exactly_two() -> None:
    """MAIN_GREEN + SIT_VALIDATED — ensure no accidental additions."""
    assert {"MAIN_GREEN", "SIT_VALIDATED"} == ON_MAIN_STATUSES


def test_main_green_is_in_on_main_statuses() -> None:
    assert "MAIN_GREEN" in ON_MAIN_STATUSES


def test_sit_validated_is_in_on_main_statuses() -> None:
    assert "SIT_VALIDATED" in ON_MAIN_STATUSES


def test_below_main_statuses_are_rejected() -> None:
    """Verify that each status below main tier is NOT in ON_MAIN_STATUSES."""
    below_main = ["FEATURE_GREEN", "STAGING_GREEN", "LOCAL_PASS", "NOT_CONFIGURED", "FAILING"]
    for status in below_main:
        assert status not in ON_MAIN_STATUSES, f"{status} should not be in ON_MAIN_STATUSES"
