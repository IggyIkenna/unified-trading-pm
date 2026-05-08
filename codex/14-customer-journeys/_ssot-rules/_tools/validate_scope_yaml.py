"""Validate rule 12 service-family scope YAML (G1.11).

Reads ``codex/14-playbooks/_ssot-rules/12-service-family-scope-rules.yaml``
and asserts schema correctness:

* Top-level ``rule_id == 12`` + ``rule_name`` present.
* Closed ServiceFamily enum: {IM, RegUmbrella, DART, DART_reporting_only,
  admin, IM_desk}. No other families allowed.
* Each family has ``surfaces`` (non-empty list of strings),
  ``excludes`` (list of strings), ``route_allowlist`` (non-empty list of
  glob patterns).
* Pattern sanity: each glob starts with ``/`` or ``!/`` (negation).

Exits 0 on success; 1 on schema error; 2 on missing file.

Usage:
    python codex/14-playbooks/_ssot-rules/_tools/validate_scope_yaml.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Final

import yaml

_YAML_PATH: Final = Path(__file__).resolve().parent.parent / "12-service-family-scope-rules.yaml"

_CLOSED_FAMILIES: Final[frozenset[str]] = frozenset(
    {"IM", "RegUmbrella", "DART", "DART_reporting_only", "admin", "IM_desk"}
)


def _validate(raw: dict[str, object]) -> list[str]:
    errors: list[str] = []

    if raw.get("rule_id") != 12:
        errors.append(f"rule_id must be 12 (got {raw.get('rule_id')!r})")
    if not raw.get("rule_name"):
        errors.append("rule_name must be non-empty")

    families = raw.get("service_families", {})
    if not isinstance(families, dict):
        return errors + ["'service_families' must be a mapping"]

    actual = set(families.keys())
    unknown = actual - _CLOSED_FAMILIES
    if unknown:
        errors.append(f"unknown service families: {sorted(unknown)} (closed enum: {sorted(_CLOSED_FAMILIES)})")
    missing = _CLOSED_FAMILIES - actual
    if missing:
        errors.append(f"missing required service families: {sorted(missing)}")

    for name, family in families.items():
        if not isinstance(family, dict):
            errors.append(f"service_families['{name}'] must be a mapping")
            continue

        surfaces = family.get("surfaces", [])
        if not isinstance(surfaces, list) or not surfaces:
            errors.append(f"{name}.surfaces must be a non-empty list")
        else:
            for idx, item in enumerate(surfaces):
                if not isinstance(item, str):
                    errors.append(f"{name}.surfaces[{idx}] must be a string")

        excludes = family.get("excludes", [])
        if not isinstance(excludes, list):
            errors.append(f"{name}.excludes must be a list (may be empty)")

        allowlist = family.get("route_allowlist", [])
        if not isinstance(allowlist, list) or not allowlist:
            errors.append(f"{name}.route_allowlist must be a non-empty list")
        else:
            for idx, pattern in enumerate(allowlist):
                if not isinstance(pattern, str):
                    errors.append(f"{name}.route_allowlist[{idx}] must be a string")
                    continue
                if not (pattern.startswith("/") or pattern.startswith("!/")):
                    errors.append(f"{name}.route_allowlist[{idx}] = {pattern!r} must start with '/' or '!/'")

    return errors


def main() -> int:
    if not _YAML_PATH.is_file():
        print(f"ERROR: rule 12 YAML not found at {_YAML_PATH}", file=sys.stderr)
        return 2

    with _YAML_PATH.open("r", encoding="utf-8") as handle:
        try:
            raw = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            print(f"FAIL: YAML parse error — {exc}", file=sys.stderr)
            return 1

    if not isinstance(raw, dict):
        print("FAIL: top-level must be a mapping", file=sys.stderr)
        return 1

    errors = _validate(raw)
    if errors:
        print(f"FAIL: {len(errors)} validation error(s):", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: rule 12 service-family scope YAML valid ({len(raw['service_families'])} families).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
