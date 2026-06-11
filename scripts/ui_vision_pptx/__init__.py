"""UI/UX Redesign Vision PPTX generator package.

Split from the original single-file ``scripts/generate-ui-vision-pptx.py``
(1,717 lines) by responsibility per the >900-line PM-script hygiene item in
``plans/active/codex_violations_ratchet_to_five_2026_06_10.md`` Phase 1 P3:

- :mod:`deck_style` — design tokens + shared drawing primitives
- :mod:`slides_overview` — slides 01-04 (hero, problem, SMA hierarchy, exploration-to-live)
- :mod:`slides_surfaces` — slides 05-07 (command center, strategy analytics, markets + ops)
- :mod:`slides_principles` — slides 08-09 (implementation path, temporal universality)
- :mod:`build` — deck assembly + save

The original path ``scripts/generate-ui-vision-pptx.py`` remains the entry point.
"""
