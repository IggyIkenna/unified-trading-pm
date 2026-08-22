# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Render or verify ``unified-trading-system-ui/lib/architecture-v2/restriction-profiles.ts``
from the 6 YAML files under ``codex/14-playbooks/demo-ops/profiles/``.

Downstream arm of G1.7: PM YAML owns the tile-lock-state SSOT, UI renders
a TS mirror, this script enforces parity. Invoked from:

  * ``unified-trading-pm/scripts/propagation/sync-restriction-profiles-to-ui.sh``
  * ``unified-trading-system-ui/scripts/quality-gates.sh`` (``--check`` mode).

Pattern mirrors
``unified-trading-pm/scripts/propagation/sync_archetype_capability_to_ui.py``
(G1.8). Kept deliberately parallel so the two drift-detectors behave the
same way and fail with the same shape of message.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml  # pyright: ignore[reportMissingTypeStubs]

PROFILES_REL = Path("unified-trading-pm/codex/14-playbooks/demo-ops/profiles")
UI_MIRROR_REL = Path("unified-trading-system-ui/lib/architecture-v2/restriction-profiles.ts")


_HEADER_PREFIX = """\
// AUTO-GENERATED from PM demo-ops/profiles/*.yaml.
// Do not edit by hand. Re-run:
//   bash unified-trading-pm/scripts/propagation/sync-restriction-profiles-to-ui.sh --write
// SSOT: unified-trading-pm/codex/14-playbooks/demo-ops/profiles/*.yaml
// Validator: unified-trading-pm/codex/14-playbooks/demo-ops/_tools/validate_profiles.py
// UAC engine: unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py

import type { TileLockState } from "../visibility/tile-lock-state";

"""

_HEADER_SUFFIX = """\
export type DemoFlavour = "broader_platform" | "turbo" | "deep_dive" | "sales_pitch";

export type TileId =
  | "data"
  | "research"
  | "promote"
  | "trading"
  | "observe"
  | "reports"
  | "investor-relations"
  | "admin";

export interface RestrictionProfileYaml {
  readonly persona_id: PersonaId;
  readonly base_audience: string;
  readonly description: string;
  readonly tiles: Readonly<Record<TileId, TileLockState>>;
  readonly flavour_overrides: Readonly<
    Partial<Record<DemoFlavour, Readonly<Partial<Record<TileId, TileLockState>>>>>
  >;
}

"""


_FOOTER = """
/**
 * Resolve the effective tile lock-state for a persona + optional flavour.
 * Matches the overlay order of
 * `unified_api_contracts.internal.architecture_v2.restriction_profiles.resolve_profile`:
 * base → flavour → (questionnaire no-op) → (env no-op).
 */
export function resolveTileLockState(
  personaId: PersonaId | string,
  tileId: TileId,
  flavour?: DemoFlavour,
): TileLockState {
  const profile = RESTRICTION_PROFILES[personaId as PersonaId];
  if (profile === undefined) {
    // Unknown persona → hidden (matches anon.yaml semantics + UAC fallback).
    return "hidden";
  }
  const override = flavour !== undefined ? profile.flavour_overrides[flavour] : undefined;
  if (override !== undefined && override[tileId] !== undefined) {
    return override[tileId] as TileLockState;
  }
  return profile.tiles[tileId];
}

export const KNOWN_PERSONA_IDS: readonly PersonaId[] = Object.keys(RESTRICTION_PROFILES).sort() as PersonaId[];
"""


# PM YAML + UAC Python use ``padlocked`` (terse, matches the canonical
# action verb). The UI's G1.3 ``TileLockState`` type at
# ``unified-trading-system-ui/lib/visibility/tile-lock-state.ts`` uses the
# more explicit ``padlocked-visible`` (distinguishing from a hypothetical
# ``padlocked-hidden`` variant). We translate at this sync boundary so
# neither side has to shift vocabulary.
_STATE_YAML_TO_UI: dict[str, str] = {
    "unlocked": "unlocked",
    "padlocked": "padlocked-visible",
    "hidden": "hidden",
}


def _translate_state(state: object) -> str:
    if not isinstance(state, str) or state not in _STATE_YAML_TO_UI:
        raise SystemExit(f"ERROR: unexpected tile state {state!r} — not in {sorted(_STATE_YAML_TO_UI.keys())}")
    return _STATE_YAML_TO_UI[state]


def _translate_tiles(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise SystemExit(f"ERROR: tiles must be a mapping, got {type(raw).__name__}")
    translated: dict[str, str] = {}
    for tile_id, state in raw.items():  # pyright: ignore[reportUnknownVariableType]
        if not isinstance(tile_id, str):
            raise SystemExit(f"ERROR: tile_id must be str, got {type(tile_id).__name__}")
        translated[tile_id] = _translate_state(state)
    return translated


def _load_profiles(pm_root: Path) -> list[dict[str, object]]:
    profiles_dir = pm_root / "codex" / "14-playbooks" / "demo-ops" / "profiles"
    if not profiles_dir.is_dir():
        raise SystemExit(f"ERROR: profiles directory not found at {profiles_dir}")

    profiles: list[dict[str, object]] = []
    for yaml_path in sorted(profiles_dir.glob("*.yaml")):
        with yaml_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle)  # pyright: ignore[reportUnknownMemberType]
        if not isinstance(raw, dict):
            raise SystemExit(f"ERROR: {yaml_path.name} top-level must be a mapping")
        # Translate YAML tile states → UI vocabulary at the sync boundary.
        # Whitelist only the fields that match RestrictionProfileYaml interface;
        # YAMLs may carry extra documentation fields (display_name, email,
        # questionnaire_response, walkthrough_hints, etc.) that the TS schema
        # does not accept. Drop them at the sync boundary.
        ALLOWED_FIELDS = {"persona_id", "base_audience", "description", "tiles", "flavour_overrides"}  # noqa: N806
        translated: dict[str, object] = {  # pyright: ignore[reportUnknownArgumentType]
            k: v
            for k, v in raw.items()
            if k in ALLOWED_FIELDS  # pyright: ignore[reportUnknownVariableType]
        }
        # ``description`` is required by the TS schema — fall back to a stub if
        # the YAML omits it (older profiles use ``notes`` for free-text).
        if "description" not in translated:
            translated["description"] = ""
        translated["tiles"] = _translate_tiles(raw.get("tiles"))  # pyright: ignore[reportUnknownMemberType]
        flavour_overrides_raw: object = raw.get("flavour_overrides", {})  # pyright: ignore[reportUnknownMemberType]  # noqa: qg-empty-fallback
        translated_overrides: dict[str, dict[str, str]] = {}
        if isinstance(flavour_overrides_raw, dict):
            for flavour, tile_map in flavour_overrides_raw.items():  # pyright: ignore[reportUnknownVariableType]
                if not isinstance(flavour, str):
                    raise SystemExit(f"ERROR: flavour key must be str, got {type(flavour).__name__}")
                translated_overrides[flavour] = _translate_tiles(tile_map)
        translated["flavour_overrides"] = translated_overrides
        profiles.append(translated)
    return profiles


def _render_ts(profiles: list[dict[str, object]]) -> str:
    # Deterministic ordering = sorted by persona_id
    sorted_profiles = sorted(profiles, key=lambda p: str(p.get("persona_id", "")))

    # Derive PersonaId union dynamically from YAML files so adding a new profile
    # does not require editing this script. The TS union must include every
    # persona_id that has a YAML — otherwise the TS compiler rejects the
    # generated Record<PersonaId, ...> entry.
    persona_ids = sorted({str(p.get("persona_id", "")) for p in sorted_profiles if p.get("persona_id")})
    persona_id_union = "\n".join([f'  | "{pid}"' for pid in persona_ids])
    persona_id_block = f"export type PersonaId =\n{persona_id_union};\n\n"

    body_lines: list[str] = [
        "export const RESTRICTION_PROFILES: Readonly<Record<PersonaId, RestrictionProfileYaml>> = {"
    ]
    for profile in sorted_profiles:
        persona_id = profile["persona_id"]
        body_lines.append(f'  "{persona_id}": {json.dumps(profile, sort_keys=True, indent=4)},'.replace("\n", "\n  "))
    body_lines.append("} as const;")
    body_lines.append("")
    return _HEADER_PREFIX + persona_id_block + _HEADER_SUFFIX + "\n".join(body_lines) + _FOOTER


def _resolve_paths(workspace_root: Path) -> tuple[Path, Path]:
    pm_root = workspace_root / "unified-trading-pm"
    ui_file = workspace_root / UI_MIRROR_REL
    return pm_root, ui_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument("--workspace-root", required=True, type=Path)
    group = parser.add_mutually_exclusive_group()
    _ = group.add_argument("--check", action="store_true", help="fail on drift (default)")
    _ = group.add_argument("--write", action="store_true", help="overwrite the UI mirror")
    args = parser.parse_args(argv)

    pm_root: Path
    ui_file: Path
    pm_root, ui_file = _resolve_paths(Path(args.workspace_root))  # pyright: ignore[reportAny]

    profiles = _load_profiles(pm_root)
    rendered = _render_ts(profiles)

    if args.write:  # pyright: ignore[reportAny]
        ui_file.parent.mkdir(parents=True, exist_ok=True)
        _ = ui_file.write_text(rendered, encoding="utf-8")
        print(f"OK: wrote {ui_file.relative_to(Path(args.workspace_root))}")  # pyright: ignore[reportAny]
        return 0

    # Default: --check
    if not ui_file.is_file():
        print(
            f"FAIL: {ui_file.relative_to(Path(args.workspace_root))} missing — run --write first",  # pyright: ignore[reportAny]
            file=sys.stderr,
        )
        return 1
    existing = ui_file.read_text(encoding="utf-8")
    if existing != rendered:
        print(
            "FAIL: restriction-profiles.ts drifted from PM YAML. "
            "Regenerate with: bash unified-trading-pm/scripts/propagation/sync-restriction-profiles-to-ui.sh --write",
            file=sys.stderr,
        )
        return 1
    print("OK: restriction-profiles.ts is up-to-date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
