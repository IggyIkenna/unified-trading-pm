"""Validate G1.7 restriction-profile YAML files.

Reads every `*.yaml` in `codex/14-customer-journeys/demo-ops/profiles/`, asserts:

* Required top-level keys present (`persona_id`, `base_audience`, `tiles`,
  `flavour_overrides`).
* Every ``tile_id`` key in ``tiles`` is in the closed tile-id enum mirrored
  from ``unified-trading-system-ui/lib/config/services.ts`` SERVICE_REGISTRY.
* Every state value is in ``{"unlocked", "padlocked", "hidden"}``.
* Every flavour override keys a known ``DemoFlavour`` value.
* No tile from the closed enum is silently omitted (prevents stealth drift).

Exits 0 on success; non-zero on any violation with a human-readable message.
Invoked by PM quality-gates; paired with the UAC unit-test suite at
``unified-api-contracts/tests/internal/unit/test_restriction_profiles.py``.

Usage:
    python codex/14-customer-journeys/demo-ops/_tools/validate_profiles.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

import yaml

_PROFILES_DIR: Final = Path(__file__).resolve().parent.parent / "profiles"

# Mirror of ``SERVICE_REGISTRY[].key`` in
# unified-trading-system-ui/lib/config/services.ts. Keep in sync.
_VALID_TILE_IDS: Final[frozenset[str]] = frozenset(
    {
        "data",
        "research",
        "promote",
        "trading",
        "observe",
        "reports",
        "investor-relations",
        "admin",
    }
)

# Closed enum for tile lock state.
_VALID_STATES: Final[frozenset[str]] = frozenset({"unlocked", "padlocked", "hidden"})

# Closed enum for DemoFlavour — mirror of
# ``unified_api_contracts/internal/architecture_v2/derivation.py`` DemoFlavour.
_VALID_FLAVOURS: Final[frozenset[str]] = frozenset({"broader_platform", "turbo", "deep_dive", "sales_pitch"})

# Closed enum for the subset of ClientAudience that maps to personas.
_VALID_AUDIENCES: Final[frozenset[str]] = frozenset(
    {
        "admin",
        "im_client",
        "im_desk",
        "reg_umbrella_client",
        "trading_platform_subscriber",
    }
)


def _validate_file(path: Path) -> list[str]:
    """Return a list of validation errors for one YAML file. Empty list = OK."""

    errors: list[str] = []
    with path.open("r", encoding="utf-8") as handle:
        try:
            data = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            return [f"{path.name}: YAML parse error — {exc}"]

    if not isinstance(data, dict):
        return [f"{path.name}: top-level must be a mapping"]

    for required_key in ("persona_id", "base_audience", "tiles"):
        if required_key not in data:
            errors.append(f"{path.name}: missing required key '{required_key}'")

    persona_id = data.get("persona_id")
    if persona_id is not None and f"{persona_id}.yaml" != path.name:
        errors.append(f"{path.name}: persona_id '{persona_id}' must match filename '{path.stem}'")

    audience = data.get("base_audience")
    if audience is not None and audience not in _VALID_AUDIENCES:
        errors.append(f"{path.name}: base_audience '{audience}' not in enum {sorted(_VALID_AUDIENCES)}")

    tiles = data.get("tiles", {})
    if not isinstance(tiles, dict):
        errors.append(f"{path.name}: 'tiles' must be a mapping")
    else:
        for tile_id, state in tiles.items():
            if tile_id not in _VALID_TILE_IDS:
                errors.append(f"{path.name}: unknown tile_id '{tile_id}' (valid: {sorted(_VALID_TILE_IDS)})")
            if state not in _VALID_STATES:
                errors.append(
                    f"{path.name}: tile '{tile_id}' has invalid state '{state}' (valid: {sorted(_VALID_STATES)})"
                )

        missing_tiles = _VALID_TILE_IDS - set(tiles.keys())
        if missing_tiles:
            errors.append(f"{path.name}: profile must declare state for every tile; missing: {sorted(missing_tiles)}")

    overrides = data.get("flavour_overrides", {})
    if not isinstance(overrides, dict):
        errors.append(f"{path.name}: 'flavour_overrides' must be a mapping")
    else:
        for flavour, tile_map in overrides.items():
            if flavour not in _VALID_FLAVOURS:
                errors.append(f"{path.name}: unknown flavour '{flavour}' (valid: {sorted(_VALID_FLAVOURS)})")
            if not isinstance(tile_map, dict):
                errors.append(f"{path.name}: flavour_overrides['{flavour}'] must be a mapping")
                continue
            for tile_id, state in tile_map.items():
                if tile_id not in _VALID_TILE_IDS:
                    errors.append(f"{path.name}: override tile_id '{tile_id}' unknown under flavour '{flavour}'")
                if state not in _VALID_STATES:
                    errors.append(
                        f"{path.name}: override '{tile_id}' state '{state}' invalid under flavour '{flavour}'"
                    )

    return errors


def main() -> int:
    """Validate every profile YAML. Return 0 on success, 1 on any error."""

    if not _PROFILES_DIR.is_dir():
        print(f"ERROR: profiles directory not found at {_PROFILES_DIR}", file=sys.stderr)
        return 2

    yaml_files = sorted(_PROFILES_DIR.glob("*.yaml"))
    if not yaml_files:
        print(f"ERROR: no YAML files in {_PROFILES_DIR}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    for yaml_file in yaml_files:
        all_errors.extend(_validate_file(yaml_file))

    if all_errors:
        print(f"FAIL: {len(all_errors)} validation error(s) across {len(yaml_files)} profile(s):", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(yaml_files)} restriction-profile YAML(s) valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
