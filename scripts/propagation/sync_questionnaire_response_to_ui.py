# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Check (and optionally emit) the UAC ↔ UI parity for QuestionnaireResponse.

G1.10 §Deviations flagged the next schema expansion as the trigger to ship
a sync-script. UAC commit `32d5fd7` (2026-04-21) added 7 Reg-Umbrella axes;
the UI mirror at ``lib/questionnaire/types.ts`` was hand-synced in the
same wave. This script codifies the contract: future axis / enum changes
fail the UI quality-gate on drift.

Scope of this first cut (2026-04-22):

* **``--check``** reads UAC ``QuestionnaireResponse`` + its 6 Literal /
  enum companions via Python introspection and confirms every Literal
  member + field name appears in the UI's ``lib/questionnaire/types.ts``.
  Exit 1 on any drift.
* **``--write``** is intentionally NOT implemented yet — full Pydantic →
  TS codegen is a bigger lift and the hand-sync covers today's needs.
  Invoking ``--write`` prints an actionable error pointing at the Reg
  Umbrella commit pattern.

Consumers:

* ``unified-trading-pm/scripts/propagation/sync-questionnaire-response-to-ui.sh``
  (shell wrapper).
* ``unified-trading-system-ui/scripts/quality-gates.sh`` — runs
  ``--check`` as a pre-base-ui hook so every UI push gates on drift.

SSOT:

* ``plans/active/questionnaire_response_sync_script_2026_04_22.md``
* ``plans/active/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md`` §Deviations
"""

from __future__ import annotations

import argparse
import importlib
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Final, get_args

TS_MIRROR_REL = Path("unified-trading-system-ui/lib/questionnaire/types.ts")
UAC_MODULE_PATH: Final[str] = "unified_api_contracts.internal.architecture_v2.restriction_profiles"


# Pydantic field name → expected TS type-alias name in `types.ts`. Field
# order mirrors QuestionnaireResponse declaration. Optional Reg-Umbrella
# axes come last; those may land before corresponding TS fields if the UI
# author forgets to sync, which is exactly what this check exists to
# catch.
EXPECTED_FIELDS: Final[tuple[str, ...]] = (
    "categories",
    "instrument_types",
    "venue_scope",
    "strategy_style",
    "service_family",
    "fund_structure",
    "licence_region",
    "targets_3mo",
    "targets_1yr",
    "targets_2yr",
    "own_mlro",
    "entity_jurisdiction",
    "supported_currencies",
)


def _iter_literal_values(obj: object) -> Iterable[str]:
    """Extract string values from a ``Literal[...]`` annotation."""

    for arg in get_args(obj):
        if isinstance(arg, str):
            yield arg


def _load_uac_literals() -> dict[str, tuple[str, ...]]:
    """Return ``{enum_alias: (members,)}`` from UAC introspection.

    Keys are the Python-side alias names (``QuestionnaireCategory``,
    ``QuestionnaireInstrumentType``, …). Each maps to the Literal member
    strings. Fails loud if the module or any expected alias is missing.
    """

    module = importlib.import_module(UAC_MODULE_PATH)
    aliases = {
        "QuestionnaireCategory": module.QuestionnaireCategory,
        "QuestionnaireInstrumentType": module.QuestionnaireInstrumentType,
        "QuestionnaireStrategyStyle": module.QuestionnaireStrategyStyle,
        "QuestionnaireServiceFamily": module.QuestionnaireServiceFamily,
        "QuestionnaireFundStructure": module.QuestionnaireFundStructure,
        "QuestionnaireLicenceRegion": module.QuestionnaireLicenceRegion,
    }
    return {name: tuple(_iter_literal_values(obj)) for name, obj in aliases.items()}


def _load_uac_field_names() -> tuple[str, ...]:
    """Return the ordered tuple of ``QuestionnaireResponse`` field names."""

    module = importlib.import_module(UAC_MODULE_PATH)
    response_cls = module.QuestionnaireResponse
    return tuple(response_cls.model_fields.keys())


def _read_ts_mirror(workspace_root: Path) -> str:
    path = workspace_root / TS_MIRROR_REL
    if not path.is_file():
        raise FileNotFoundError(f"TS mirror not found at {path}")
    return path.read_text(encoding="utf-8")


def _check_literal_members_present(ts_source: str, alias_name: str, members: Iterable[str]) -> list[str]:
    """Return list of members missing from the TS source."""

    missing: list[str] = []
    for member in members:
        # TS mirror wraps literals in double-quotes.
        pattern = re.compile(rf'"{re.escape(member)}"')
        if not pattern.search(ts_source):
            missing.append(f"{alias_name}.{member!r}")
    return missing


def _check(workspace_root: Path) -> int:
    uac_literals = _load_uac_literals()
    uac_fields = _load_uac_field_names()

    if set(uac_fields) != set(EXPECTED_FIELDS):
        extra = set(uac_fields) - set(EXPECTED_FIELDS)
        missing = set(EXPECTED_FIELDS) - set(uac_fields)
        print(
            "DRIFT: UAC QuestionnaireResponse field set does not match "
            "script's EXPECTED_FIELDS tuple. Update "
            "sync_questionnaire_response_to_ui.py EXPECTED_FIELDS, then "
            f"re-run --check. extra={sorted(extra)} missing={sorted(missing)}",
            file=sys.stderr,
        )
        return 1

    ts_source = _read_ts_mirror(workspace_root)

    failures: list[str] = []
    for field_name in uac_fields:
        # Each Pydantic field is mirrored on the TS interface; we check
        # the field-name appears verbatim in the interface definition.
        if not re.search(rf"\b{re.escape(field_name)}\b", ts_source):
            failures.append(
                f"UAC field '{field_name}' not found in TS mirror {TS_MIRROR_REL}",
            )

    for alias_name, members in uac_literals.items():
        missing = _check_literal_members_present(ts_source, alias_name, members)
        failures.extend(missing)

    if failures:
        print(
            f"DRIFT: UI TypeScript mirror at {TS_MIRROR_REL} diverges from UAC schema:",
            file=sys.stderr,
        )
        for line in failures:
            print(f"  - {line}", file=sys.stderr)
        print(
            "\nFix options:\n"
            "  1. Update the TS mirror by hand to match UAC "
            "(canonical SSOT is Pydantic).\n"
            "  2. Follow the 2026-04-21 Reg-Umbrella commit pattern:\n"
            "     - extend QuestionnaireResponse in UAC,\n"
            "     - add corresponding TS types to lib/questionnaire/types.ts,\n"
            "     - re-run this --check to confirm parity.",
            file=sys.stderr,
        )
        return 1

    print("OK: QuestionnaireResponse UI mirror parity confirmed.")
    return 0


def _write_stub() -> int:
    print(
        "--write mode is intentionally not implemented. The initial cut "
        "of sync_questionnaire_response_to_ui.py (2026-04-22) only ships "
        "--check drift detection. Full Pydantic → TS codegen is deferred; "
        "follow the 2026-04-21 Reg-Umbrella hand-sync pattern:\n"
        "  1. edit UAC restriction_profiles.py,\n"
        "  2. edit UI lib/questionnaire/types.ts to match,\n"
        "  3. run --check to confirm.",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        required=True,
        type=Path,
        help="Absolute path to the unified-trading-system-repos checkout.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_const",
        dest="mode",
        const="check",
        help="Check TS mirror against UAC (default).",
    )
    mode.add_argument(
        "--write",
        action="store_const",
        dest="mode",
        const="write",
        help="(Not yet implemented — see --check + manual sync.)",
    )
    parser.set_defaults(mode="check")
    args = parser.parse_args(argv)

    workspace_root: Path = args.workspace_root.resolve()
    if not workspace_root.is_dir():
        print(
            f"--workspace-root {workspace_root} is not a directory",
            file=sys.stderr,
        )
        return 2

    uac_src = workspace_root / "unified-api-contracts"
    if not uac_src.is_dir():
        print(
            f"UAC source not found at {uac_src}",
            file=sys.stderr,
        )
        return 2

    # Make UAC importable without requiring workspace pip-install wiring.
    sys.path.insert(0, str(uac_src))

    if args.mode == "check":
        return _check(workspace_root)
    return _write_stub()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "EXPECTED_FIELDS",
    "main",
]
