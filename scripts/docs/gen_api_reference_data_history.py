#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: standing — regenerates platform-api-reference.html §08 "Data history" drilldown
# Delete-when: the data-history section is retired from the client artefacts
# Re-run: from unified-api-contracts/.venv (imports its registries); output is an HTML fragment to paste into §08.
# The rendered numbers have a date on them — re-run after any registry change (venues/data_types/leagues).
# Trap hit building this: venue_instrument_type_triples() returns (triples, unresolved) — render unresolved
#   honestly; a blanket asset-group roster over-fans phantom instrument types (ASTER options bug class).
from __future__ import annotations

import html
from collections import defaultdict

from unified_api_contracts.canonical.crosscutting.defi import ChainKind
from unified_api_contracts.registry.market_data_categories import VENUE_DATA_TYPE_CAPABILITIES
from unified_api_contracts.registry.sports_bookmaker_league_coverage import BOOKMAKER_LEAGUE_COVERAGE
from unified_api_contracts.registry.venue_asset_group import classify_venue_asset_group
from unified_api_contracts.registry.venue_instrument_type_axis import venue_instrument_type_triples

triples, unresolved = venue_instrument_type_triples()

_UNRESOLVED = "\x00unresolved"
_NO_INSTRUMENT_TYPE = "\x00none"

# venue -> instrument_type -> set(data_type)
venue_it_dt: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
for v, it, dt in triples:
    venue_it_dt[v][it or _NO_INSTRUMENT_TYPE].add(dt)
for v, dt in unresolved:
    venue_it_dt[v][_UNRESOLVED].add(dt)


def it_label(it: str) -> str:
    if it == _NO_INSTRUMENT_TYPE:
        return "(no instrument type — venue-wide)"
    if it == _UNRESOLVED:
        return "(instrument type not resolvable from the roster axis — registry gap)"
    return it


ag_venues: dict[str, list[str]] = defaultdict(list)
for v in VENUE_DATA_TYPE_CAPABILITIES:
    ag = classify_venue_asset_group(v)
    ag_venues[ag].append(v)

AG_ORDER = ["cefi", "defi", "tradfi", "sports", "prediction"]
AG_LABEL = {"cefi": "CeFi", "defi": "DeFi", "tradfi": "TradFi", "sports": "Sports", "prediction": "Prediction"}

CHAIN_LOOKUP = {ck.name: ck.value for ck in ChainKind}


def esc(s: object) -> str:
    return html.escape(str(s))


def since_label(date_str: str | None) -> str:
    return esc(date_str) if date_str else "not declared"


def defi_chain(venue: str) -> tuple[str, str | None]:
    parts = venue.split("-")
    if len(parts) >= 2 and parts[-1] in CHAIN_LOOKUP:
        return "-".join(parts[:-1]), CHAIN_LOOKUP[parts[-1]]
    return venue, None


def leaf_table(rows: list[tuple[str, str | None]]) -> str:
    """rows: list of (data_type, declared_since)."""
    out = [
        '<div class="tree-body scroll-x"><table><thead>'
        "<tr><th>Data type</th><th>Declared since</th></tr></thead><tbody>"
    ]
    for dt, since in rows:
        out.append(f"<tr><td><code>{esc(dt)}</code></td><td>{since_label(since)}</td></tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def league_table(dt: str, since: str | None, leagues: list[str]) -> str:
    out = [
        f'<details class="tree"><summary><span class="nm"><code>{esc(dt)}</code></span>'
        f'<span class="meta"><span class="u">{len(leagues)} leagues</span></span></summary>'
        '<div class="tree-body scroll-x"><table><thead>'
        "<tr><th>League</th><th>Declared since</th></tr></thead><tbody>"
    ]
    for lg in leagues:
        out.append(f"<tr><td><code>{esc(lg)}</code></td><td>{since_label(since)}</td></tr>")
    out.append("</tbody></table></details>")
    return "".join(out)


def render_instrument_type(venue: str, it: str, dts: list[str]) -> tuple[str, int]:
    """Returns (html, shard_count) for one instrument_type node under a venue."""
    record = VENUE_DATA_TYPE_CAPABILITIES[venue]
    is_sports = classify_venue_asset_group(venue) == "sports"
    leagues = sorted(BOOKMAKER_LEAGUE_COVERAGE.get(venue, [])) if is_sports else []

    plain_rows: list[tuple[str, str | None]] = []
    league_blocks: list[str] = []
    for dt in dts:
        avail = record.data_types.get(dt)
        since = avail.batch_start_date if avail else None
        if is_sports and leagues:
            league_blocks.append(league_table(dt, since, leagues))
        else:
            plain_rows.append((dt, since))

    body = ""
    if plain_rows:
        body += leaf_table(plain_rows)
    body += "".join(league_blocks)

    shard_count = len(dts)
    label = it_label(it)
    node = (
        f'<details class="tree"><summary><span class="nm">{esc(label)}</span>'
        f'<span class="meta"><span class="u">{shard_count} data type'
        f"{'s' if shard_count != 1 else ''}</span></span></summary>"
        f"{body}</details>"
    )
    return node, shard_count


def render_venue(venue: str) -> tuple[str, int]:
    """Returns (html, shard_count) for one venue node."""
    its = venue_it_dt.get(venue, {})
    ag = classify_venue_asset_group(venue)

    if ag == "defi":
        _protocol, chain = defi_chain(venue)
        chain_label = chain or "(chain not encoded in venue token)"
        it_nodes = []
        total = 0
        for it in sorted(its):
            node, cnt = render_instrument_type(venue, it, sorted(its[it]))
            it_nodes.append(node)
            total += cnt
        chain_node = (
            f'<details class="tree"><summary><span class="nm">{esc(chain_label)}</span>'
            f'<span class="meta"><span class="u">{total} shard{"s" if total != 1 else ""}</span></span></summary>'
            f'<div class="tree-body">{"".join(it_nodes)}</div></details>'
        )
        venue_body = chain_node
        shard_count = total
    else:
        it_nodes = []
        shard_count = 0
        for it in sorted(its):
            node, cnt = render_instrument_type(venue, it, sorted(its[it]))
            it_nodes.append(node)
            shard_count += cnt
        venue_body = "".join(it_nodes)

    venue_node = (
        f'<details class="tree"><summary><span class="nm"><code>{esc(venue)}</code></span>'
        f'<span class="meta"><span class="u">{shard_count} shard'
        f"{'s' if shard_count != 1 else ''}</span></span></summary>"
        f'<div class="tree-body">{venue_body}</div></details>'
    )
    return venue_node, shard_count


def render_asset_group(ag: str) -> tuple[str, int, int]:
    venues = sorted(ag_venues.get(ag, []))
    venue_nodes = []
    total_shards = 0
    for v in venues:
        node, cnt = render_venue(v)
        venue_nodes.append(node)
        total_shards += cnt
    ag_node = (
        f'<details class="tree"><summary><span class="nm">{esc(AG_LABEL[ag])}</span>'
        f'<span class="meta">{len(venues)} venue{"s" if len(venues) != 1 else ""} '
        f"&middot; {total_shards} shard{'s' if total_shards != 1 else ''}</span></summary>"
        f'<div class="tree-body">{"".join(venue_nodes)}</div></details>'
    )
    return ag_node, len(venues), total_shards


ag_blocks = []
grand_venues = 0
grand_shards = 0
per_ag_summary = []
for ag in AG_ORDER:
    node, vcount, scount = render_asset_group(ag)
    ag_blocks.append(node)
    grand_venues += vcount
    grand_shards += scount
    per_ag_summary.append((AG_LABEL[ag], vcount, scount))

fragment = f"""
  <section id="s8">
    <div class="sec-head">
      <span class="num">08</span>
      <h2>Data history &mdash; every shard, drill down</h2>
    </div>
    <p class="lede">
      Every date below is read straight from the platform's capability registry
      (<code>VENUE_DATA_TYPE_CAPABILITIES</code>),
      per shard &mdash; asset group, venue, chain (DeFi), instrument type, data type, and league (Sports, where a
      league-level shard exists). Open only the branch you need.
    </p>
    <details class="sec-body" open>
      <summary>Browse the data history &mdash; asset group, venue, chain, instrument type, data type</summary>
      <p style="font-size: 0.95rem; color: var(--ink-3)">
        {grand_venues} venues across {len(AG_ORDER)} asset groups, {grand_shards} declared (venue, instrument type,
        data type) shards total
        ({" &middot; ".join(f"{lbl} {v}/{s}" for lbl, v, s in per_ag_summary)} &mdash; venues/shards).
        <b>Declared since: not declared</b> means the capability is live-only &mdash; reachable on the streaming path
        with no batch start date, because nothing has backfilled it yet. That is a statement about which path exists
        today, not a claim that the capability itself is not real.
      </p>
      {"".join(ag_blocks)}
    </details>
  </section>
"""

import sys

sys.stdout.write(fragment)  # pipe to a file of your choosing

print("grand_venues", grand_venues, "grand_shards", grand_shards)
print("per_ag_summary", per_ag_summary)
print("fragment_chars", len(fragment))
print("fragment_lines", fragment.count("\n"))
