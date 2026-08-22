#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG ratchet — chain-set inclusion invariant on UAC chain registries.

Enforces:

    set(MAINNET_CHAIN_IDS keys) ⊇ set(CHAIN_GENESIS_DATES keys)
    set(MAINNET_CHAIN_IDS keys) ⊇ chain-name resolution of GAS_FEE_CHAIN_START_DATES keys

SSOT: ``unified_api_contracts.registry.chain_env``. The three dicts MUST be
kept inclusive-aligned so that any chain that ships gas-fee or genesis data
is also recognised as a mainnet EVM chain by callers that iterate
``MAINNET_CHAIN_IDS``. Drift surfaces as silent zero-shard coverage in the
honest-coverage panel (DF-7 reference incident).

Closes cross_asset_group_catalogue_audit_2026_05_10.md Phase 1F-extend
``check_chain_set_inclusion.py QG ratchet`` carry-forward (Phase 6A).

Non-EVM chains (``SOLANA``/``BITCOIN``) carry ``chain_id=0`` in
``MAINNET_CHAIN_IDS``; they are excluded from gas-fee reverse-lookup since
``GAS_FEE_CHAIN_START_DATES`` is EVM-only (Solana gas-fee uses
``GAS_FEE_SOLANA_START_DATE`` separately).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_chain_env() -> object:
    """Load chain_env.py directly, bypassing the UAC package ``__init__``.

    Importing via ``unified_api_contracts.registry.chain_env`` triggers the
    UAC package ``__init__`` which may carry unrelated foreign-plan import
    failures (e.g. WIP normalize_utils changes); chain_env.py itself only
    declares plain ``dict`` constants and has no in-package imports, so
    loading the file directly is safe.

    Direct-file load is tried FIRST (not as an ImportError fallback) — a bare
    package-path import of the registry module almost never raises
    ImportError (the package usually imports fine), so gating the fast path
    behind "on failure" meant it never actually ran: every invocation paid
    the full ``unified_api_contracts`` package ``__init__`` cost (pandas +
    every ``external``/``canonical`` submodule, ~13s wall) just to read three
    plain dict constants — measured as the dominant contributor to a
    quality-gates-v2 timeout on system-integration-tests#311 (2026-07-28).
    """
    workspace_root = Path(__file__).resolve().parents[3]
    chain_env_path = workspace_root / "unified-api-contracts" / "unified_api_contracts" / "registry" / "chain_env.py"
    if chain_env_path.exists():
        spec = importlib.util.spec_from_file_location("_chain_env_direct", chain_env_path)
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    from unified_api_contracts.registry.chain_env import (  # type: ignore[no-redef]  # noqa: qg-deep-import
        CHAIN_GENESIS_DATES,
        GAS_FEE_CHAIN_START_DATES,
        MAINNET_CHAIN_IDS,
    )

    class _Module:
        pass

    module = _Module()
    module.CHAIN_GENESIS_DATES = CHAIN_GENESIS_DATES  # type: ignore[attr-defined]
    module.GAS_FEE_CHAIN_START_DATES = GAS_FEE_CHAIN_START_DATES  # type: ignore[attr-defined]
    module.MAINNET_CHAIN_IDS = MAINNET_CHAIN_IDS  # type: ignore[attr-defined]
    return module


def check_chain_set_inclusion() -> list[str]:
    """Return a list of human-readable invariant violations (empty = clean)."""
    try:
        module = _load_chain_env()
    except (ImportError, FileNotFoundError) as exc:
        return [f"FATAL: cannot load unified_api_contracts.registry.chain_env: {exc}"]

    MAINNET_CHAIN_IDS: dict[str, int] = module.MAINNET_CHAIN_IDS  # type: ignore[attr-defined]  # noqa: N806
    CHAIN_GENESIS_DATES: dict[str, str] = module.CHAIN_GENESIS_DATES  # type: ignore[attr-defined]  # noqa: N806
    GAS_FEE_CHAIN_START_DATES: dict[int, str] = module.GAS_FEE_CHAIN_START_DATES  # type: ignore[attr-defined]  # noqa: N806

    violations: list[str] = []

    mainnet_names = set(MAINNET_CHAIN_IDS)
    genesis_names = set(CHAIN_GENESIS_DATES)

    # MAINNET ⊇ GENESIS
    genesis_orphans = sorted(genesis_names - mainnet_names)
    if genesis_orphans:
        violations.append(
            f"CHAIN_GENESIS_DATES has {len(genesis_orphans)} chain(s) missing from MAINNET_CHAIN_IDS: {genesis_orphans}"
        )

    # MAINNET ⊇ GAS_FEE (via chain_id reverse-lookup).
    chain_id_to_name = {cid: name for name, cid in MAINNET_CHAIN_IDS.items() if cid != 0}
    gas_fee_orphans_int: list[int] = []
    for chain_id in GAS_FEE_CHAIN_START_DATES:
        if chain_id not in chain_id_to_name:
            gas_fee_orphans_int.append(chain_id)
    if gas_fee_orphans_int:
        violations.append(
            f"GAS_FEE_CHAIN_START_DATES has {len(gas_fee_orphans_int)} chain_id(s) "
            f"not in MAINNET_CHAIN_IDS values: {sorted(gas_fee_orphans_int)}"
        )

    # Bonus invariant: every GAS_FEE chain must also be in CHAIN_GENESIS_DATES
    # so the data-status panel knows the earliest possible data date for that
    # chain. (DF-7: GAS_FEE archival can lag chain genesis, but never lead it.)
    gas_fee_names_missing_genesis = sorted(
        chain_id_to_name[cid]
        for cid in GAS_FEE_CHAIN_START_DATES
        if cid in chain_id_to_name and chain_id_to_name[cid] not in genesis_names
    )
    if gas_fee_names_missing_genesis:
        violations.append(
            f"{len(gas_fee_names_missing_genesis)} chain(s) in GAS_FEE_CHAIN_START_DATES "
            f"missing from CHAIN_GENESIS_DATES: {gas_fee_names_missing_genesis}"
        )

    return violations


def main() -> int:
    # SKIP when UAC repo not present as a workspace sibling — this check is a
    # regression guard on UAC's own registries and is only meaningful when UAC
    # is checked out alongside the calling repo. PM (and any other repo without
    # UAC as a sibling) treats this as SKIP, not FAIL.
    workspace_root = Path(__file__).resolve().parents[3]
    chain_env_path = workspace_root / "unified-api-contracts" / "unified_api_contracts" / "registry" / "chain_env.py"
    if not chain_env_path.exists():
        spec = None
        try:
            spec = importlib.util.find_spec("unified_api_contracts.registry.chain_env")
        except (ImportError, ModuleNotFoundError, ValueError):
            spec = None
        if spec is None:
            print(
                "[check_chain_set_inclusion] SKIP — UAC repo not present in workspace "
                f"(chain_env.py not found at {chain_env_path}); inclusion invariant guard skipped."
            )
            return 0

    violations = check_chain_set_inclusion()
    if not violations:
        print(
            "[check_chain_set_inclusion] OK — MAINNET_CHAIN_IDS ⊇ "
            "CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES (via chain_id)."
        )
        return 0
    print("[check_chain_set_inclusion] FAIL — chain-set inclusion invariant violated:", file=sys.stderr)
    for v in violations:
        print(f"  - {v}", file=sys.stderr)
    print(
        "\nFix: in unified_api_contracts/registry/chain_env.py, add the missing "
        "chain entries to MAINNET_CHAIN_IDS and/or CHAIN_GENESIS_DATES so the "
        "inclusion holds. SSOT: cross_asset_group_catalogue_audit_2026_05_10.md "
        "Phase 1F-extend (DF-7).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
