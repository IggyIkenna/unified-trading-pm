#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Group D — openapi.json drift gate. **DEPRECATED 2026-05-16 — DO NOT WIRE INTO QG.**

ORIGINAL INTENT: compare committed `unified-trading-api/openapi.json` against the
mirrored `unified-trading-system-ui/lib/registry/openapi.json`; drift = UI types stale.

WHY DEPRECATED (per ikenna-main investigation in
`plans/active/issues/openapi_mirror_drift_2026_05_16.md` § INVESTIGATION):
the two files are structurally different by design:
  - unified-trading-api/openapi.json: 61 paths — slim FastAPI facade
  - unified-trading-system-ui/lib/registry/openapi.json: 479 paths — AGGREGATED mirror
    of multiple backends (deployment-api, client-reporting-api, etc.)

Full-file hash comparison will ALWAYS show drift; the script's semantic is wrong.

CORRECT SEMANTIC (deferred to post-cutover): walk the canonical aggregator output
(some script merges all backend openapi specs) and compare against the UI mirror's
hash. Until that aggregator is identified, this script is a no-op.

Exit-code semantics (legacy; left in place for future canonical-aggregator wiring):
  0 — both hashes match
  1 — drift detected
  2 — argument / IO error

Origin: governance_qg_automation_gaps_post_cutover_2026_05_12.md § Group D
        (UI-13 — Generated-artefact drift gate).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import cast

DEFAULT_API_PATH = Path("unified-trading-api/openapi.json")
DEFAULT_UI_PATH = Path("unified-trading-system-ui/lib/registry/openapi.json")


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenAPI drift gate (unified-trading-api ↔ UI mirror).")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
        help="Workspace root to resolve relative paths against",
    )
    parser.add_argument(
        "--api-path",
        type=Path,
        default=DEFAULT_API_PATH,
        help=f"Relative path to API openapi.json (default: {DEFAULT_API_PATH})",
    )
    parser.add_argument(
        "--ui-path",
        type=Path,
        default=DEFAULT_UI_PATH,
        help=f"Relative path to UI mirrored openapi.json (default: {DEFAULT_UI_PATH})",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print drift status but always exit 0 (transition mode)",
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    api_rel: Path = cast(Path, ns.api_path)
    ui_rel: Path = cast(Path, ns.ui_path)
    warn_only: bool = cast(bool, ns.warn_only)

    api_path = workspace_root / api_rel
    ui_path = workspace_root / ui_rel

    if not api_path.is_file():
        print(f"ERROR: API openapi.json missing: {api_path}", file=sys.stderr)
        return 2
    if not ui_path.is_file():
        print(f"ERROR: UI openapi.json mirror missing: {ui_path}", file=sys.stderr)
        return 2

    api_hash = _hash_file(api_path)
    ui_hash = _hash_file(ui_path)

    print(f"API openapi.json   ({api_rel}): sha256={api_hash[:12]}...")
    print(f"UI  openapi mirror ({ui_rel}):  sha256={ui_hash[:12]}...")

    if api_hash == ui_hash:
        print("\n✅ No drift — UI mirror matches API source.")
        return 0

    drift_msg = (
        "\n❌ DRIFT — UI's openapi.json mirror is out of sync with unified-trading-api/openapi.json.\n"
        "   This means the auto-generated types in unified-trading-system-ui/lib/types/api-generated.ts\n"
        "   may not reflect the backend's actual API surface.\n"
        "   Re-sync via: bash unified-trading-system-ui/scripts/sync-openapi.sh\n"
        "   (or whichever script regenerates from the API server's runtime openapi.json)."
    )

    if warn_only:
        print(drift_msg.replace("❌ DRIFT", "⚠️  DRIFT (warn-only mode)"))
        print("\n(--warn-only set — exiting 0 despite drift; flip the QG step to non-warn once cleared.)")
        return 0

    print(drift_msg)
    return 1


if __name__ == "__main__":
    sys.exit(main())
