"""Assemble + save the UI/UX Redesign Vision deck."""

from pptx import Presentation
from pptx.util import Emu

from .deck_style import SLIDE_H, SLIDE_W
from .slides_overview import (
    slide_01_hero,
    slide_02_problem,
    slide_03_sma_hierarchy,
    slide_04_exploration_to_live,
)
from .slides_principles import slide_08_implementation, slide_09_temporal
from .slides_surfaces import (
    slide_05_command_center,
    slide_06_strategy_analytics,
    slide_07_markets_ops,
)


def main() -> None:
    prs = Presentation()
    prs.slide_width = Emu(int(SLIDE_W))
    prs.slide_height = Emu(int(SLIDE_H))

    slide_01_hero(prs)
    slide_02_problem(prs)
    slide_03_sma_hierarchy(prs)
    slide_04_exploration_to_live(prs)
    slide_05_command_center(prs)
    slide_06_strategy_analytics(prs)
    slide_07_markets_ops(prs)
    slide_09_temporal(prs)
    slide_08_implementation(prs)

    output = "unified-trading-pm/plans/active/UI_Platform_Redesign_Vision_v2.pptx"
    prs.save(output)
    print(f"Saved: {output}")
    print("  9 slides with temporal universality, sparklines, as-of picker")
