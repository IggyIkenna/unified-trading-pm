#!/usr/bin/env python3
"""Generate the Unified Trading Platform UI/UX Redesign Vision PowerPoint.

Uses real strategy data, SMA model, and actual P&L components from the system.
Run: python3 unified-trading-pm/scripts/generate-ui-vision-pptx.py

Entry point only — the deck implementation lives in the sibling
``scripts/ui_vision_pptx/`` package (design tokens / slide builders / assembly),
split by responsibility per the >900-line PM-script hygiene item in
``plans/active/codex_violations_ratchet_to_five_2026_06_10.md`` Phase 1 P3.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui_vision_pptx.build import main

if __name__ == "__main__":
    main()
