"""Slides 01-04 — hero, problem statement, SMA hierarchy, exploration-to-live."""

from .deck_style import (
    ACCENT_AMBER,
    ACCENT_BLUE,
    ACCENT_CYAN,
    ACCENT_GREEN,
    ACCENT_ORANGE,
    ACCENT_PURPLE,
    ACCENT_RED,
    ACCENT_TEAL,
    BG_CARD,
    BG_ELEVATED,
    BG_SECONDARY,
    FONT_MONO,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
    add_breadcrumb,
    add_card,
    add_kpi_card,
    add_lifecycle_rail,
    add_nav_bar,
    add_pill,
    add_text_box,
    set_slide_bg,
)


def slide_01_hero(prs):
    """Title + Command Center hero with real data."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)

    # Nav + lifecycle + breadcrumb
    add_nav_bar(slide, active_idx=0, show_as_of=True, as_of_text="Live")
    add_lifecycle_rail(slide, active_idx=3, top=0.48)
    add_breadcrumb(slide, ["Odum Delta One", "Apex Capital", "DEFI_ETH_STAKED_BASIS_SCE_1H", "cfg-2.4.0"], top=0.9)

    # Title block
    add_text_box(slide, 0.3, 1.2, 8, 0.3, "Unified Trading Platform", font_size=28, bold=True, color=TEXT_PRIMARY)
    add_text_box(slide, 0.3, 1.6, 8, 0.3, "UI / UX Redesign Vision", font_size=14, color=TEXT_SECONDARY)
    add_text_box(
        slide,
        0.3,
        1.95,
        8,
        0.25,
        "From 11 disconnected tools to 4 daily-use surfaces + 3 specialist tools.",
        font_size=10,
        color=TEXT_TERTIARY,
    )

    # Badges
    add_pill(slide, 9.0, 1.25, 1.6, "Plan 2026-03-17", ACCENT_CYAN, 8)
    add_pill(slide, 10.7, 1.25, 0.7, "Draft", ACCENT_AMBER, 8)
    add_pill(slide, 11.5, 1.25, 1.5, "Architecture", ACCENT_BLUE, 8)

    # KPI cards with sparklines
    add_kpi_card(slide, 0.3, 2.4, "Firm PnL", "+$1.42m", "  +0.8% 1d", ACCENT_GREEN, "up")
    add_kpi_card(slide, 2.5, 2.4, "Net Exposure", "$4.2m", "1.2x levered", ACCENT_CYAN, "volatile")
    add_kpi_card(slide, 4.7, 2.4, "Margin Health", "82%", "$340k free", ACCENT_AMBER, "flat")
    add_kpi_card(slide, 6.9, 2.4, "Live Strategies", "12", "9 ok, 2 warn, 1 paused", ACCENT_BLUE, "flat")
    add_kpi_card(slide, 9.1, 2.4, "Alerts", "3 crit", "2 high", ACCENT_RED, "down")

    # Strategy performance table
    add_card(slide, 0.3, 3.9, 6.5, 3.1, BG_ELEVATED)
    add_text_box(slide, 0.5, 4.0, 4, 0.25, "Strategy Performance", font_size=12, bold=True, color=TEXT_PRIMARY)
    add_text_box(
        slide,
        0.5,
        4.25,
        6,
        0.2,
        "Click strategy name -> analytics  |  Click status -> filtered positions",
        font_size=8,
        color=TEXT_MUTED,
    )

    # Table headers
    cols = [
        ("Strategy", 0.5, 2.2),
        ("Arch", 2.7, 0.6),
        ("St", 3.3, 0.4),
        ("PnL", 3.8, 0.8),
        ("Sharpe", 4.6, 0.6),
        ("DD", 5.3, 0.5),
        ("Trend", 5.9, 0.5),
    ]
    for label, x, w in cols:
        add_text_box(slide, x, 4.5, w, 0.2, label, font_size=8, bold=True, color=TEXT_MUTED)

    # Table rows — REAL strategies
    rows = [
        ("DEFI_ETH_STAKED_BASIS", "Yield", ACCENT_GREEN, "L", "+$289k", "2.5", "3.3%"),
        ("DEFI_ETH_BASIS_SCE_1H", "Arb", ACCENT_GREEN, "L", "+$412k", "2.1", "4.1%"),
        ("DEFI_USDT_LENDING_SCE", "Yield", ACCENT_GREEN, "L", "+$91k", "1.8", "2.1%"),
        ("DEFI_ETH_RECURSIVE", "Yield", ACCENT_AMBER, "W", "+$188k", "1.9", "5.2%"),
        ("TRADFI_SPY_ML_DIR_1H", "Dir", ACCENT_GREEN, "L", "+$67k", "1.4", "3.9%"),
        ("SPORTS_HT_ML_V2.1", "Dir", ACCENT_GREEN, "L", "+$44k", "1.6", "1.8%"),
        ("SPORTS_ARB", "Arb", ACCENT_GREEN, "L", "+$31k", "1.3", "2.4%"),
    ]
    y = 4.75
    for name, arch, status_color, st, pnl, sharpe, dd in rows:
        add_text_box(slide, 0.5, y, 2.2, 0.2, name, font_size=9, font_name=FONT_MONO, color=ACCENT_CYAN)
        add_text_box(slide, 2.7, y, 0.6, 0.2, arch, font_size=9, color=TEXT_TERTIARY)
        add_text_box(slide, 3.3, y, 0.4, 0.2, f"  {st}", font_size=9, font_color_override=status_color)
        pnl_color = ACCENT_GREEN if pnl.startswith("+") else ACCENT_RED
        add_text_box(slide, 3.8, y, 0.8, 0.2, pnl, font_size=9, font_name=FONT_MONO, font_color_override=pnl_color)
        add_text_box(slide, 4.6, y, 0.6, 0.2, sharpe, font_size=9, font_name=FONT_MONO, color=TEXT_SECONDARY)
        add_text_box(slide, 5.3, y, 0.5, 0.2, dd, font_size=9, font_name=FONT_MONO, color=TEXT_SECONDARY)
        y += 0.35

    # P&L + Risk Attribution panel
    add_card(slide, 7.0, 3.9, 3.0, 3.1, BG_ELEVATED)
    add_text_box(slide, 7.2, 4.0, 2.8, 0.25, "P&L + Risk Attribution", font_size=11, bold=True, color=TEXT_PRIMARY)
    add_text_box(slide, 7.2, 4.25, 2.8, 0.2, "Same 6D, two sides", font_size=8, color=TEXT_MUTED)

    attrib_rows = [
        ("Funding", "+$412k", "$8.2m"),
        ("Basis", "+$355k", "14 bps"),
        ("Staking Yield", "+$145k", "LTV .72"),
        ("Delta", "+$61k", "$2.4m net"),
        ("Greeks", "-$8k", "Delta:-0.98"),
        ("Slippage", "-$61k", "---"),
        ("Gas/Fees", "-$44k", "---"),
        ("Recon Pending", "-$18k", "4 breaks"),
    ]
    add_text_box(slide, 7.2, 4.5, 1.2, 0.2, "Component", font_size=8, bold=True, color=TEXT_MUTED)
    add_text_box(slide, 8.4, 4.5, 0.7, 0.2, "P&L", font_size=8, bold=True, color=TEXT_MUTED)
    add_text_box(slide, 9.1, 4.5, 0.8, 0.2, "Exposure", font_size=8, bold=True, color=TEXT_MUTED)
    y = 4.75
    for comp, pnl, exp in attrib_rows:
        add_text_box(slide, 7.2, y, 1.2, 0.18, comp, font_size=8, color=TEXT_SECONDARY)
        pnl_c = ACCENT_GREEN if pnl.startswith("+") else ACCENT_RED
        add_text_box(slide, 8.4, y, 0.7, 0.18, pnl, font_size=8, font_name=FONT_MONO, font_color_override=pnl_c)
        add_text_box(slide, 9.1, y, 0.8, 0.18, exp, font_size=8, font_name=FONT_MONO, color=TEXT_TERTIARY)
        y += 0.3

    # Alerts panel
    add_card(slide, 10.2, 3.9, 2.85, 1.5, BG_ELEVATED)
    add_text_box(slide, 10.35, 4.0, 2.5, 0.25, "Alerts & Incidents", font_size=11, bold=True, color=TEXT_PRIMARY)
    alerts = [
        ("CRIT", "Kill switch: DEFI_ETH_BASIS", ACCENT_RED),
        ("HIGH", "Feature freshness 92s lag EU", ACCENT_AMBER),
        ("MED", "Recon break: Apex SMA", ACCENT_AMBER),
    ]
    y = 4.35
    for sev, msg, color in alerts:
        add_text_box(slide, 10.35, y, 0.5, 0.2, sev, font_size=8, bold=True, font_color_override=color)
        add_text_box(slide, 10.85, y, 2.1, 0.2, msg, font_size=8, color=TEXT_SECONDARY)
        y += 0.35

    # Health panel
    add_card(slide, 10.2, 5.6, 2.85, 1.4, BG_ELEVATED)
    add_text_box(slide, 10.35, 5.7, 2.5, 0.25, "Health & Freshness", font_size=11, bold=True, color=TEXT_PRIMARY)
    services = [
        ("features-delta-one", "92s", "30s", ACCENT_AMBER),
        ("execution-service", "2s", "5s", ACCENT_GREEN),
        ("risk-and-exposure", "4s", "10s", ACCENT_GREEN),
        ("pnl-attribution", "8s", "15s", ACCENT_GREEN),
    ]
    y = 6.05
    for svc, fresh, sla, color in services:
        add_text_box(slide, 10.35, y, 1.5, 0.18, svc, font_size=7, font_name=FONT_MONO, color=TEXT_SECONDARY)
        add_text_box(slide, 11.85, y, 0.4, 0.18, fresh, font_size=7, font_name=FONT_MONO, font_color_override=color)
        add_text_box(slide, 12.3, y, 0.4, 0.18, sla, font_size=7, font_name=FONT_MONO, color=TEXT_MUTED)
        y += 0.3


def slide_02_problem(prs):
    """Before/After — real UI names, real duplication."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)

    add_text_box(slide, 0.5, 0.4, 8, 0.4, "The core insight", font_size=28, bold=True, color=TEXT_PRIMARY)
    add_text_box(
        slide,
        0.5,
        0.85,
        10,
        0.3,
        "The dark theme and component library are already institutional. The problem is information architecture.",
        font_size=12,
        color=TEXT_SECONDARY,
    )

    # Before
    add_card(slide, 0.5, 1.5, 5.8, 4.5, BG_ELEVATED)
    add_text_box(slide, 0.7, 1.6, 5, 0.3, "Before: 11 isolated UIs", font_size=16, bold=True, color=ACCENT_RED)
    add_text_box(
        slide,
        0.7,
        1.95,
        5,
        0.3,
        "Duplicate deployments. Duplicate P&L. Duplicate alerts. Manual port-hopping.",
        font_size=9,
        color=TEXT_TERTIARY,
    )

    before_uis = [
        ("strategy-ui :5175", "execution-analytics-ui :5174", "90% identical routes"),
        ("trading-analytics-ui :5180", "client-reporting-ui :5182", "Both show P&L"),
        ("batch-audit-ui :5181", "logs-dashboard-ui :5178", "Same API :8013"),
        ("live-health-monitor-ui :5177", "settlement-ui :5176", "Both show positions"),
        ("onboarding-ui :5173", "deployment-ui :5183", "Both have /deployments"),
    ]
    y = 2.35
    for ui1, ui2, problem in before_uis:
        add_text_box(slide, 0.7, y, 2.2, 0.2, ui1, font_size=8, font_name=FONT_MONO, color=TEXT_SECONDARY)
        add_text_box(slide, 2.9, y, 0.3, 0.2, "<->", font_size=8, color=TEXT_MUTED)
        add_text_box(slide, 3.2, y, 2.2, 0.2, ui2, font_size=8, font_name=FONT_MONO, color=TEXT_SECONDARY)
        add_text_box(slide, 5.4, y, 0.8, 0.2, problem, font_size=7, font_color_override=ACCENT_RED)
        y += 0.35

    # Key failures
    failures = [
        "No workflow coherence (Design -> ... -> Reconcile invisible)",
        "No entity hierarchy (Fund -> Client -> Strategy never navigable)",
        "No cross-UI navigation (users type port numbers)",
        "/deployments in 10 of 11 UIs",
        "P&L in 3 different UIs with no canonical home",
    ]
    y = 4.2
    for f in failures:
        add_text_box(slide, 0.7, y, 5.3, 0.2, f"  {f}", font_size=9, color=TEXT_SECONDARY)
        y += 0.3

    # After
    add_card(slide, 6.8, 1.5, 6.0, 4.5, BG_ELEVATED)
    add_text_box(slide, 7.0, 1.6, 5, 0.3, "After: one operating model", font_size=16, bold=True, color=ACCENT_GREEN)
    add_text_box(
        slide,
        7.0,
        1.95,
        5,
        0.3,
        "4 daily-use surfaces + 3 specialist tools. Connected by hierarchy, lifecycle, and deep links.",
        font_size=9,
        color=TEXT_TERTIARY,
    )

    surfaces = [
        ("Trading Command Center", ":5177", "OBSERVE, INTERVENE", "Live now", ACCENT_GREEN),
        ("Strategy Analytics", ":5175", "DESIGN, SIMULATE, PROMOTE", "Historical", ACCENT_BLUE),
        ("Market Intelligence", ":5180", "EXPLAIN, RECONCILE", "Post-trade", ACCENT_PURPLE),
        ("Operations Hub", ":5183", "DEPLOY, DIAGNOSE", "Ops time", ACCENT_AMBER),
    ]
    y = 2.4
    for name, port, verbs, time_h, color in surfaces:
        add_card(slide, 7.0, y, 5.6, 0.5, BG_CARD)
        add_text_box(slide, 7.15, y + 0.05, 2.5, 0.2, name, font_size=11, bold=True, font_color_override=color)
        add_text_box(slide, 7.15, y + 0.27, 1.0, 0.18, port, font_size=7, font_name=FONT_MONO, color=TEXT_MUTED)
        add_text_box(slide, 8.3, y + 0.27, 2.0, 0.18, verbs, font_size=7, color=TEXT_TERTIARY)
        add_text_box(slide, 10.8, y + 0.15, 1.5, 0.18, time_h, font_size=8, font_color_override=color)
        y += 0.58

    tools = [
        ("Config & Onboarding", ":5173", ACCENT_CYAN),
        ("ML Platform", ":5179", ACCENT_ORANGE),
        ("Reporting & Settlement", ":5182", ACCENT_TEAL),
    ]
    y += 0.15
    add_text_box(slide, 7.0, y, 3, 0.2, "Specialist tools:", font_size=9, color=TEXT_MUTED)
    y += 0.3
    x = 7.0
    for name, port, color in tools:
        add_pill(slide, x, y, 1.7, f"{name} {port}", color, 7)
        x += 1.85

    # Thesis
    add_card(slide, 0.5, 6.3, 12.3, 0.6, BG_SECONDARY)
    add_text_box(
        slide,
        0.7,
        6.38,
        11.5,
        0.5,
        "Citadel-grade: the complexity stays; the navigation becomes legible. 7 repos, 7 ports, zero duplication.",
        font_size=12,
        color=TEXT_PRIMARY,
        bold=True,
    )


def slide_03_sma_hierarchy(prs):
    """SMA model + three parallel hierarchies (P&L, Position, Risk)."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)

    add_text_box(slide, 0.5, 0.4, 10, 0.4, "SMA model & entity hierarchy", font_size=28, bold=True, color=TEXT_PRIMARY)
    add_text_box(
        slide,
        0.5,
        0.85,
        10,
        0.3,
        "Separately managed accounts: one strategy template, isolated client instances, positions diverge by design.",
        font_size=11,
        color=TEXT_SECONDARY,
    )

    # SMA diagram
    add_card(slide, 0.5, 1.4, 6.0, 2.8, BG_ELEVATED)
    add_text_box(slide, 0.7, 1.5, 5, 0.3, "Unit of execution", font_size=14, bold=True, color=TEXT_PRIMARY)
    add_text_box(
        slide,
        0.7,
        1.85,
        5.5,
        0.2,
        "(strategy_id, client_id, config_version)  =  one async task, one position set",
        font_size=9,
        font_name=FONT_MONO,
        color=ACCENT_CYAN,
    )

    sma_rows = [
        ("DEFI_ETH_STAKED_BASIS_SCE_1H", "odum", "v2.4.0", "Live", ACCENT_GREEN),
        ("DEFI_ETH_STAKED_BASIS_SCE_1H", "apex_capital", "v2.4.0", "Live", ACCENT_GREEN),
        ("DEFI_ETH_STAKED_BASIS_SCE_1H", "meridian_fund", "v2.3.1", "Paper", ACCENT_AMBER),
        ("DEFI_ETH_BASIS_SCE_1H", "odum", "v3.2.1", "Live", ACCENT_GREEN),
        ("TRADFI_SPY_ML_DIR_1H", "odum", "v1.0.0", "Live", ACCENT_GREEN),
        ("SPORTS_HT_ML_V2.1", "apex_capital", "v2.1.0", "Live", ACCENT_GREEN),
    ]

    headers = [("Strategy Template", 0.7, 2.8), ("Client", 3.5, 0.9), ("Config", 4.5, 0.6), ("Status", 5.3, 0.5)]
    for label, x, w in headers:
        add_text_box(slide, x, 2.15, w, 0.2, label, font_size=8, bold=True, color=TEXT_MUTED)

    y = 2.4
    for strat, client, cfg, status, color in sma_rows:
        add_text_box(slide, 0.7, y, 2.8, 0.18, strat, font_size=7, font_name=FONT_MONO, color=ACCENT_CYAN)
        add_text_box(slide, 3.5, y, 0.9, 0.18, client, font_size=8, color=TEXT_SECONDARY)
        add_text_box(slide, 4.5, y, 0.6, 0.18, cfg, font_size=7, font_name=FONT_MONO, color=TEXT_TERTIARY)
        add_text_box(slide, 5.3, y, 0.5, 0.18, status, font_size=8, font_color_override=color)
        y += 0.3

    add_text_box(
        slide,
        0.7,
        3.75,
        5.5,
        0.2,
        "Same strategy code, different fills, different positions. This is expected and normal.",
        font_size=8,
        color=TEXT_MUTED,
    )

    # Three parallel hierarchies
    add_card(slide, 6.8, 1.4, 6.0, 2.8, BG_ELEVATED)
    add_text_box(
        slide,
        7.0,
        1.5,
        5,
        0.3,
        "Three parallel hierarchies (batch + live)",
        font_size=14,
        bold=True,
        color=TEXT_PRIMARY,
    )
    add_text_box(
        slide,
        7.0,
        1.85,
        5.5,
        0.2,
        "Each has a batch (historical) and live (real-time) variant. Same drill path, different data source.",
        font_size=9,
        color=TEXT_TERTIARY,
    )

    hierarchies = [
        (
            "P&L Hierarchy",
            "All -> Client -> Strategy -> Venue -> Component",
            "Funding, basis, staking yield, delta, greeks, slippage, gas, recon",
            ACCENT_GREEN,
            "Market Intelligence",
        ),
        (
            "Position Hierarchy",
            "All -> Client -> Strategy -> Venue -> Instrument",
            "Net qty, avg price, unrealized PnL, margin used, health factor",
            ACCENT_BLUE,
            "Trading Command Center (live) / Reporting (EOD)",
        ),
        (
            "Risk / Exposure Hierarchy",
            "All -> Client -> Strategy -> Venue -> Risk Dim",
            "Delta exp, funding exp, basis spread, LTV, greeks, margin util",
            ACCENT_PURPLE,
            "Trading Command Center",
        ),
    ]
    y = 2.2
    for name, path, components, color, home in hierarchies:
        add_text_box(slide, 7.0, y, 2.5, 0.2, name, font_size=10, bold=True, font_color_override=color)
        add_text_box(slide, 7.0, y + 0.22, 5.5, 0.18, path, font_size=8, font_name=FONT_MONO, color=TEXT_SECONDARY)
        add_text_box(slide, 7.0, y + 0.42, 5.5, 0.18, components, font_size=7, color=TEXT_MUTED)
        add_text_box(slide, 7.0, y + 0.6, 5.5, 0.15, f"Home: {home}", font_size=7, font_color_override=color)
        y += 0.85

    # Strategy archetypes
    add_card(slide, 0.5, 4.5, 12.3, 2.6, BG_ELEVATED)
    add_text_box(
        slide,
        0.7,
        4.6,
        10,
        0.3,
        "Strategy archetypes — groupable, not just by asset class",
        font_size=16,
        bold=True,
        color=TEXT_PRIMARY,
    )
    add_text_box(
        slide,
        0.7,
        4.95,
        10,
        0.2,
        "Strategies share patterns across asset classes. Groups by archetype, filters by asset class.",
        font_size=9,
        color=TEXT_TERTIARY,
    )

    archetypes = [
        (
            "Arbitrage",
            "Exploit price discrepancies across venues or legs",
            ["DEFI_ETH_BASIS_SCE_1H", "SPORTS_ARB", "CEFI cross-exchange"],
            ACCENT_CYAN,
        ),
        (
            "Market Making",
            "Continuous quoting, earn spread/fees",
            ["DEFI_ETH_USDT_MM_LP_V3", "CEFI_BTC_MM_BINANCE", "SPORTS_MM_BETFAIR"],
            ACCENT_AMBER,
        ),
        (
            "Directional",
            "ML-driven or signal-driven position taking",
            ["TRADFI_SPY_ML_DIR_1H", "SPORTS_HT_ML_V2.1", "CEFI_MOMENTUM"],
            ACCENT_BLUE,
        ),
        (
            "Yield",
            "Earn yield from lending, staking, or funding rates",
            ["DEFI_USDT_LENDING_SCE", "DEFI_ETH_STAKED_BASIS", "DEFI_ETH_RECURSIVE"],
            ACCENT_GREEN,
        ),
    ]

    x = 0.7
    for name, desc, examples, color in archetypes:
        add_card(slide, x, 5.3, 2.85, 1.6, BG_CARD)
        add_text_box(slide, x + 0.15, 5.4, 2.5, 0.25, name, font_size=13, bold=True, font_color_override=color)
        add_text_box(slide, x + 0.15, 5.7, 2.5, 0.3, desc, font_size=8, color=TEXT_SECONDARY)
        ey = 6.05
        for ex in examples:
            add_text_box(slide, x + 0.15, ey, 2.5, 0.18, ex, font_size=7, font_name=FONT_MONO, color=TEXT_TERTIARY)
            ey += 0.2
        x += 3.05

    add_text_box(
        slide,
        0.7,
        7.0,
        10,
        0.2,
        "ML Training is a deep-dive sub-view of Directional strategies — not a separate archetype.",
        font_size=9,
        color=TEXT_MUTED,
        bold=True,
    )


def slide_04_exploration_to_live(prs):
    """Exploration-to-Live config flow — shared pattern across Strategy, ML, Execution."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_bg(slide)

    add_text_box(
        slide,
        0.5,
        0.4,
        10,
        0.4,
        "Exploration to live — one pattern, three domain views",
        font_size=28,
        bold=True,
        color=TEXT_PRIMARY,
    )
    add_text_box(
        slide,
        0.5,
        0.85,
        10,
        0.3,
        "Strategy, ML, and Execution configs follow the same flow shape. Each domain adds its own nuances.",
        font_size=11,
        color=TEXT_SECONDARY,
    )

    # Shared flow steps
    add_card(slide, 0.5, 1.4, 12.3, 1.0, BG_ELEVATED)
    add_text_box(
        slide, 0.7, 1.5, 10, 0.2, "Shared flow shape (all three domains):", font_size=10, bold=True, color=TEXT_PRIMARY
    )

    steps = [
        "Configure\nGrid Params",
        "Generate\nConfigs",
        "Run Batch\n(Sharded)",
        "Analyse\nResults",
        "Select\nCandidates",
        "Promote\nto Live",
    ]
    x = 0.7
    for i, step in enumerate(steps):
        c = ACCENT_CYAN if i < 3 else ACCENT_GREEN if i < 5 else ACCENT_AMBER
        add_card(slide, x, 1.8, 1.8, 0.45, BG_CARD)
        lines = step.split("\n")
        add_text_box(slide, x + 0.05, 1.82, 1.7, 0.2, lines[0], font_size=9, bold=True, font_color_override=c)
        if len(lines) > 1:
            add_text_box(slide, x + 0.05, 2.0, 1.7, 0.18, lines[1], font_size=8, color=TEXT_TERTIARY)
        if i < 5:
            add_text_box(slide, x + 1.85, 1.92, 0.15, 0.2, "->", font_size=10, color=TEXT_MUTED)
        x += 2.0

    # Three domain columns
    domains = [
        (
            "Strategy Config",
            ACCENT_BLUE,
            "Strategy Analytics",
            [
                "Instruments + venues + algos",
                "param grid: mode x timeframe x category",
                "Sharded by category/venue/date",
                "Sharpe, PnL, drawdown, win rate",
                "DimensionalGrid multi-select",
                "Cross-link to Ops /deploy",
            ],
        ),
        (
            "ML Model Config",
            ACCENT_ORANGE,
            "ML Platform",
            [
                "Model arch + hyperparameters",
                "grid: lr x layers x dropout x timeframe",
                "GPU training jobs (Cloud Run)",
                "Accuracy, loss, Sharpe improvement",
                "Best model per instrument",
                "Deploy to ml-inference-service",
            ],
        ),
        (
            "Execution Config",
            ACCENT_PURPLE,
            "Strategy Analytics (Execution tab)",
            [
                "Algo type + venue routing",
                "grid: algo x instrument x benchmark",
                "Replay on historical tick data",
                "Alpha bps, slippage, fill rate",
                "Best algo per venue+instrument",
                "Update execution-service config",
            ],
        ),
    ]

    x = 0.5
    for name, color, surface, steps in domains:
        add_card(slide, x, 2.6, 3.9, 4.2, BG_ELEVATED)
        add_text_box(slide, x + 0.2, 2.7, 3.5, 0.25, name, font_size=14, bold=True, font_color_override=color)
        add_text_box(slide, x + 0.2, 3.0, 3.5, 0.2, f"Surface: {surface}", font_size=8, color=TEXT_MUTED)

        labels = ["Configure", "Generate", "Run Batch", "Analyse", "Select", "Promote"]
        y = 3.3
        for i, (label, detail) in enumerate(zip(labels, steps, strict=False)):
            add_text_box(
                slide, x + 0.2, y, 0.8, 0.18, f"0{i + 1} {label}", font_size=8, bold=True, font_color_override=color
            )
            add_text_box(slide, x + 1.1, y, 2.5, 0.18, detail, font_size=8, color=TEXT_SECONDARY)
            y += 0.38
        x += 4.1

    add_card(slide, 0.5, 7.0, 12.3, 0.4, BG_SECONDARY)
    add_text_box(
        slide,
        0.7,
        7.05,
        11.5,
        0.3,
        "No auto-deploy. Promote creates reviewed handoff via cross-link to Ops Hub with deploy form.",
        font_size=10,
        color=TEXT_PRIMARY,
        bold=True,
    )
