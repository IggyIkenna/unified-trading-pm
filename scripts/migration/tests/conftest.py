"""Make the script-under-test importable from this tests/ directory.

The migration script lives at ``scripts/migration/gcs_migration_bundle_2026_05_08.py``
which is not on the default Python path. This conftest prepends the parent
directory so ``from gcs_migration_bundle_2026_05_08 import ...`` resolves.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
