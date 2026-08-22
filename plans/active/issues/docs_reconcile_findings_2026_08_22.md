---
doc_type: issue
title:
  docs-reconcile 2026-08-22 — 5 numeric/content discrepancies needing live-system or domain-owner verification, not a
  mechanical fix
summary: >-
  From the 2026-08-22 docs-reconcile autonomous sweep (multi-agent Phase 1 self-consistency hunt over the 28 codex
  docs touched since the prior run). 19 of 24 genuinely-confirmed self-consistency contradictions found this run were
  mechanical (fixed + shipped directly, see the run's own commits). These 5 are different: each is a plausible-but-
  unconfirmed numeric or scoping discrepancy where picking a number without live-system access risked being
  confidently wrong, especially on 4 of the 5 which sit on customer-facing commercial-model pages.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, execution-service]
scope: [engineer, admin]
tags: [docs-reconcile, self-consistency, commercial-model, needs-verification]
related:
  [
    /plans/active/issues/docs_reconcile_bigger_scope_findings_2026_08_19.md,
    /plans/active/issues/docs_reconcile_findings_2026_08_17.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
    /codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html,
  ]
created: 2026-08-22
last_reviewed: 2026-08-22
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /codex/04-architecture/defi-execution-overview.md,
    /codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html,
    /codex/14-customer-journeys/commercial-model/platform-architecture.html,
    /codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html,
  ]
supersedes:
superseded_by:
depends_on: []
source: [docs-reconcile autonomous sweep, dispatch agt-a33599, 2026-08-22]
assigned_role: infra
drift_direction: advance-docs
---

# docs-reconcile 2026-08-22 — 5 discrepancies needing verification before a confident fix

## 1. `defi-execution-overview.md` — "only credentials" liveness rule has no stated carve-out for the SDK-dependency exception it then relies on

Line ~277: **"Every protocol connector must be LIVE-CAPABLE in code. The only thing allowed to be missing at rest is
credentials."** Lines ~307-317 then describe `JitoConnector`/`JitoRestakingConnector`/`SolBlazeConnector` as correctly
staying `supports_live = False` specifically because their target programs need an SDK ("`spl-stake-pool` or an
Anchor IDL decoder") "this repo does not yet depend on" — explicitly framed as "the fail-closed guard working as
intended, not an unmirrored declaration." The PRACTICAL intent of the "only credentials" rule (no connector should
silently claim live-coverage it doesn't have) is honored here — these 3 correctly declare `False`, so audits don't
over-count them. But the rule's own wording doesn't officially carve out "a genuinely-external SDK dependency not yet
integrated" as a second legitimate reason to be missing at rest, alongside credentials — a reader taking the rule
literally would read the Jito section as a violation the doc is defending rather than an intended exception.

**Options:**
- **A. [REC] Whoever owns this doc's next substantive edit adds the SDK-dependency carve-out explicitly to the rule
  statement itself** ("...missing at rest is credentials, or a genuinely-external SDK dependency not yet integrated,
  provided the connector still declares `supports_live=False` and is excluded from coverage claims") — lowest-risk,
  makes the already-intended exception visible at the rule's own definition site instead of only in a later section.
- B. Leave as-is — the Jito section's own defense is sufficient context for a careful reader, and broadening the rule's
  wording risks inviting other, less-legitimate "missing dependency" excuses in future connectors.

## 2. `strategy-service-deep-dive.html` §11 — per-chain venue-key table sums to 128, but the section's own headline states 121

Lines ~4025-4032 vs ~4057-4126: the section states **"121 DeFi protocol×chain capability entries"** as the registry
total, but the per-chain "Live venue keys" column immediately below sums to **128** (47+17+16+10+9+8+7+6+2+2+1+1+1+1).
Lower confidence than the 8 items fixed this run — the per-chain table's own caption cites the broader
`VENUE_DATA_TYPE_CAPABILITIES` registry rather than a DeFi-only slice, which could legitimately explain some of the
gap, but every visible row in the table is a DeFi protocol, so a 7-entry gap (128−121) isn't obviously accounted for
by that framing alone. Needs a live `grep`/import against the actual registry to resolve which total (if either) is
current.

## 3. `platform-architecture.html` §9 — "192 declared venues" headline vs a 177-sum breakdown table directly below it

Lines ~9770-9774 vs ~9811-9837: the stat-row states **"192 — Venues declared in the platform's market-data capability
registry, across every asset group."** The breakdown table immediately below (same section, captioned "Declared
venues by asset group") sums to **177** (DeFi 103 + Sports 39 + CeFi 25 + TradFi 8 + Prediction 2). Possible
non-contradictory reading: the sibling page `platform-external-api-walkthrough.html` states the identical
relationship correctly as **"177 of 192 declared"** elsewhere, and this page's own breakdown-table caption already
notes "not every declared venue has market data wired yet" — suggesting 192 = total declared, 177 = the subset with
data actually wired, and the breakdown table may only be showing the wired subset despite being captioned "declared."
Not fixed here because resolving which reading is correct (and whether the table's caption or its content is the
part that's wrong) needs a check against the live venue-capability registry, not a text-only inference.

## 4. `platform-architecture.html` — a backfill-completion percentage cited twice for what reads as the same "July 2026 review" checkpoint, ~50% vs 75%

Lines ~3776-3777 vs ~10102-10110: "As of **the July programme review** that backfill was **roughly half complete**"
vs a Programme-status table (captioned "As issued, **July 2026 review**") stating "Historical backfill ... **75%**
... Compute." Medium confidence this is a real discrepancy: §4's figure is explicitly scoped to "your specific slice"
(a named prospect's 4 CeFi venues), while §13's table row appears platform-wide/unscoped — plausibly two different
denominators for the same review date rather than one wrong number, but the doc never states that disambiguation for
this specific pair, so a reader has no way to tell without asking. Needs whoever owns the backfill-progress figures to
either add an explicit scope label to one or both numbers, or confirm they really do disagree and correct one.

## 5. `platform-external-api-walkthrough.html` — "every group reads 0 ready" callout sits directly above a tree showing "CeFi — 20 ready"

Lines ~2460-2465 vs ~2469: a callout explains **why every group still reads 0 ready** ("a strict grader with checks
still being wired up returns zero by construction"), immediately followed by a readiness tree: **"CeFi — 20 ready /
2 not-ready / 3 unverified."** Lower confidence — the callout is scoped to the full 8-leg readiness model while the
tree is scoped to just the single `market_tick_data` BATCH leg, so this may not be a true contradiction, just two
different readiness legs sitting in immediate visual juxtaposition with opposite headline numbers (0 vs 20) and no
explicit cross-reference distinguishing them. **[REC]** the low-cost fix, if this is confirmed correct scoping, is
simply to add one clause to the callout or the tree header naming which leg each one covers, so a reader isn't left
to infer it — doesn't require resolving any actual number.

## Progress Log

- **2026-08-22 (docs-reconcile, dispatch agt-a33599)**: filed. 19 of 24 confirmed self-consistency findings from this
  same sweep were mechanical and already shipped directly (`unified-trading-pm@884963c740` — 7 codex SSOTs;
  `unified-trading-pm@b2583c8a0a` — 4 commercial-model HTML pages). 3 further candidates were independently
  adversarially re-verified and REFUTED (plausible non-contradictory readings confirmed on direct re-read, not
  applied): `portfolio-allocator.md`'s "no blanket total" framing next to directly-countable per-group table counts;
  `strategy-execution-protocol.md`'s "unverified" hedge sitting next to a conclusion that independently rests on the
  T4-tier-ban argument in the same sentence, not on the hedged claim; `paper-batch-live-reconciliation.md`'s
  `last_executed` field vs a later-dated run citation, which trace to two different named verifiers in the doc, not
  one field going stale.
