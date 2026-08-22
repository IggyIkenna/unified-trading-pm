# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_chain_set_inclusion.py — Phase 1F-extend QG ratchet.

Verifies the invariant assertion logic against the live UAC chain_env constants
(which MUST be inclusive-aligned post-Phase-1F-extend), and asserts the
violation-detection code paths via monkey-patching.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

import pytest

# Add the check script directory to sys.path so we can import it.
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from check_chain_set_inclusion import check_chain_set_inclusion  # type: ignore[import-not-found]


def test_invariant_holds_on_live_uac() -> None:
    """Live UAC chain_env constants must satisfy the inclusion invariant."""
    violations = check_chain_set_inclusion()
    assert not violations, (
        "Live UAC chain_env violates the chain-set inclusion invariant. "
        "Phase 1F-extend (DF-7) should have aligned these. Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_returns_violation_when_genesis_orphan(monkeypatch: pytest.MonkeyPatch) -> None:
    """Injecting a CHAIN_GENESIS_DATES key absent from MAINNET_CHAIN_IDS triggers a violation."""
    import check_chain_set_inclusion as mod  # type: ignore[import-not-found]

    real_load = mod._load_chain_env

    def fake_load() -> object:
        real = real_load()

        # Build a wrapper that overrides only CHAIN_GENESIS_DATES.
        class _Wrapped:
            MAINNET_CHAIN_IDS = real.MAINNET_CHAIN_IDS  # type: ignore[attr-defined]
            GAS_FEE_CHAIN_START_DATES = real.GAS_FEE_CHAIN_START_DATES  # type: ignore[attr-defined]
            CHAIN_GENESIS_DATES: ClassVar[dict[str, str]] = {**real.CHAIN_GENESIS_DATES, "GHOST_CHAIN": "2025-01-01"}  # type: ignore[attr-defined]

        return _Wrapped()

    monkeypatch.setattr(mod, "_load_chain_env", fake_load)

    violations = check_chain_set_inclusion()
    assert any("GHOST_CHAIN" in v for v in violations), f"Expected violation citing GHOST_CHAIN; got: {violations}"


def test_returns_violation_when_gas_fee_chain_id_orphan(monkeypatch: pytest.MonkeyPatch) -> None:
    """Injecting a GAS_FEE_CHAIN_START_DATES key not in MAINNET_CHAIN_IDS values triggers a violation."""
    import check_chain_set_inclusion as mod  # type: ignore[import-not-found]

    real_load = mod._load_chain_env

    def fake_load() -> object:
        real = real_load()

        class _Wrapped:
            MAINNET_CHAIN_IDS = real.MAINNET_CHAIN_IDS  # type: ignore[attr-defined]
            CHAIN_GENESIS_DATES = real.CHAIN_GENESIS_DATES  # type: ignore[attr-defined]
            GAS_FEE_CHAIN_START_DATES: ClassVar[dict[int, str]] = (  # type: ignore[attr-defined]
                {**real.GAS_FEE_CHAIN_START_DATES, 99999999: "2025-01-01"}
            )

        return _Wrapped()

    monkeypatch.setattr(mod, "_load_chain_env", fake_load)

    violations = check_chain_set_inclusion()
    assert any("99999999" in v for v in violations), f"Expected violation citing chain_id 99999999; got: {violations}"
