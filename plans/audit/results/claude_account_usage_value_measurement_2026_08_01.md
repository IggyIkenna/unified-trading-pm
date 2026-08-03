---
doc_type: audit-result
title: Real Claude Max-plan usage measurement — methodology, bugs found, and corrected fleet-wide value
summary: >-
  Measures real Claude Max-plan token usage/value from local Claude Code session transcripts across the 6-account fleet,
  replacing placeholder numbers used in the AI Compute Optimisation Strategy conversation. Found and fixed three
  measurement bugs (probe-copy duplication, insufficient uuid-dedup requiring requestId-dedup, unscoped-project
  contamination) plus a live Sonnet-5 intro-pricing correction, and retracted an unverifiable "$5,000/25x" external
  validation claim. Corrected result so far (2 of 3+ sources): ~$59,900 combined API-equivalent value against ~$3,400 of
  real Max-plan billing over the same window (~17.6x). Ikenna's machine and DeepSeek pricing remain unmeasured.
status: partial
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [audit, claude-accounts, cost-optimization, usage-measurement, token-usage]
related:
  - plans/audit/results/omniroute_free_tier_cost_analysis_2026_07_31.md
created: 2026-08-01
audited_scope:
  Real Claude Code token usage/value across the 6-account Max-plan fleet, measured from local session transcripts on the
  operator's personal host and the agent-orchestrator VM (i-0c9b283b31d6b5ca7); excludes Ikenna's personal machine and
  DeepSeek per-token pricing (open follow-ups below).
date: "2026-08-01"
auditor: claude-code (interactive session, slot NA)
parent_epic: orchestrator_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
---

> **Status note**: partial — methodology is validated and corrected, but 2 of the 4 follow-up todos below (Ikenna's
> machine, DeepSeek pricing) are still open. Nothing here blocks other work.

## Why this doc exists

Downstream of the "AI Compute Optimisation Strategy" conversation (operator + Ikenna + another agent, shared 2026-08-01)
proposing a token-usage/dollar-usage classifier to route work off the 6 Claude Max accounts. That strategy doc's core
baseline numbers (~$2,800/mo, ~560M tokens) were placeholders the strategy's own author flagged as "vague ... the true
real numbers are going to be different." This doc is the real measurement.

**Roster** (from `/active/unified-trading-system-repos/account-list.md`): 6 Claude Max accounts (sub A–F), not 7 — a 7th
was under consideration (constant usage outages were the reason) but never purchased. All 6 run through
`agent-orchestrator`'s account rotation on the orchestrator VM, and are also used interactively by the operator and
Ikenna directly.

## The tool

`agent-orchestrator/scripts/orchestrator/measure-claude-usage-value.py` — walks local Claude Code session transcripts
(the only ground truth; Max-plan/OAuth subscriptions have no Anthropic Usage/Cost Admin API, unlike metered API-key
orgs), dedupes correctly, prices at current per-model rates. Full rationale and the three bugs below are documented in
the script's own header — this doc is the results, not a second copy of the methodology.

**Re-run this** on any host to get a current number — it is not a one-shot report:

```bash
python3 agent-orchestrator/scripts/orchestrator/measure-claude-usage-value.py > usage.json
python3 agent-orchestrator/scripts/orchestrator/measure-claude-usage-value.py --summarize usage.json
```

## Three measurement bugs found and fixed (2026-08-01) — read before trusting any number from this class of analysis

1. **Naive per-file summation double-counts.** `agent-orchestrator/server/usage_tracker.py`'s periodic `/usage` probe
   (an ephemeral `CLAUDE_CONFIG_DIR` pointed at a throwaway `usage-probe*`/`usage-sub-*`/`up-sub-*` directory) resumes a
   real session to check quota, and that resume replays the full prior history into the probe's own transcript file.
   Verified: every duplicate turn UUID found in more than one file was also present in a real (non-probe) directory —
   100% copies, 0% unique probe-original data.
2. **Deduplicating by the transcript line's local `uuid` is not sufficient.** A session resume/replay can regenerate a
   brand-new local `uuid` for an already-billed turn. Found one Anthropic `requestId` (the real per-API-call identifier)
   recorded under 8 different local `uuid`s across 2 files. On this operator's personal host, 13,752 of 59,966 distinct
   `requestId`s (~23%) were duplicated this way; on the orchestrator VM it was far worse — 588,821 duplicate turns
   against 649,255 real ones (~47%), consistent with a fleet that constantly resumes/restarts many concurrent slots.
   **Fix: dedupe by `requestId`, not `uuid`.**
3. **The default `~/.claude/projects` tree is not scoped to one project.** It accumulates every project any Claude Code
   session on that machine has ever touched — found an entirely unrelated freelance project polluting the trading-system
   total. Fixed by scoping to a project-path substring by default.

**A fourth, pricing (not code) lesson**: Claude Sonnet 5 carries a temporary intro rate ($2/$10 per MTok vs. the
standard $3/$15) through 2026-08-31. Since Sonnet 5 is the dominant model by turn volume on the orchestrator VM, using
the standard rate instead of the live intro rate overstated that host's total by 33%. **Verify current per-model pricing
before every fresh run** — don't reuse a cached rate table blindly.

## What was retracted mid-session — do not reuse this claim

An earlier draft of this analysis cross-checked the measured total against a
"$5,000/month per fully-saturated Max 20x
account, ~25x value" figure pulled from a WebSearch summary. Traced it back: every source repeating that number is an
SEO content-mill article citing an unnamed "one developer's estimate" with no shown methodology — not Anthropic's own
data, and not independently corroborated (the sites likely cite each other). Anthropic's own published Max 20x limits
are stated in **hours of model access** (≈240–480 hrs/week Sonnet 4, ≈24–40 hrs/week Opus 4 as of the May 2026
rate-limit change), not dollars — converting hours to a dollar-equivalent requires a tokens-per-hour throughput
assumption Anthropic does not publish, which is exactly why different blogs' guesses at that conversion span a 3×–25×
range ($600–1,500/mo,
$5,000/mo, and one case study implying ~$1,875/mo all appear in the same search results). **Do not cite the $5,000/25x
figure as a real ceiling in future analysis** — there isn't a trustworthy external dollar-based ceiling available; the
measured number stands on its own methodology, not on an external "does this fit some blog's guess" check.

## Measured results (partial — two of at least three sources)

Both scoped to `unified-trading-system-repos`, `requestId`-deduped, priced at current rates (Sonnet 5 at its live intro
rate):

| Source                                        | Real turns |              Active days | Date range              |    USD value |
| --------------------------------------------- | ---------: | -----------------------: | ----------------------- | -----------: |
| Operator's personal host                      |    ~51,500 |                       35 | 2026-06-16 → 2026-07-31 |      ~$8,950 |
| Orchestrator VM (`i-0c9b283b31d6b5ca7`) fleet |    649,255 | 36 (of 64 calendar days) | 2026-05-29 → 2026-07-31 |     ~$50,900 |
| **Combined so far**                           |            |                          |                         | **~$59,900** |

Against the operator's own real-spend estimate (17 account-months of $200 Max plans ≈ $3,400 over the same ~3-month
window), that's roughly a **~17.6× multiplier** — real API-equivalent value drawn from flat-rate subscriptions, not
money actually billed. This is expected, not anomalous: it's the entire economic premise of a flat-rate plan, and the
operator's own independent report of "constant usage outages" (i.e., regularly hitting rate-limit ceilings) is
consistent with the accounts running at genuinely heavy utilization.

**Numbers above are approximate** — this doc was written from the tail end of a long verification conversation; re-run
the tool for exact current figures before using these in a decision.

## Open follow-ups (real work, not yet done)

- [ ] [SCRIPT] P1. **Measure Ikenna's personal machine** — run
      `agent-orchestrator/scripts/orchestrator/measure-claude-usage-value.py` on his host and fold the result into the
      combined total above. His usage is currently an unverified guess ("5–10x more than the operator's host"), not
      data.
- [ ] [SCRIPT] P2. **Price the DeepSeek turns** — `deepseek-v4-pro` and `deepseek-v4-flash` turns are captured by the
      tool (real turn counts exist) but have no entry in `RATES`, so they're excluded from every dollar total above. Get
      DeepSeek's actual per-token pricing and add it to the script's `RATES` table.
- [ ] [SCRIPT] P3. **Check the orchestrator VM's day-by-day recency trend.** The operator reported AO "started working
      properly" only in the last ~2 weeks despite existing for 2 months — the 36-active-days-of-64 figure is consistent
      with that, but the ~$50,900 figure is an average across the whole window and likely understates the _current_
      daily run-rate if activity is now heavily front-loaded into the recent period. Re-run with the full
      (non-summarized) output and bucket by date to check.
- [ ] [OPERATOR] P3. **Decide the AI Compute Optimisation Strategy's next step** — the task-rating/0-10 classification
      system the operator, Ikenna, and another agent were designing (capped-step escalation, objective test-pass
      triggers over model self-report, anchoring `opus-required`/`fable-required` at the top of the scale) was
      explicitly deferred mid-design ("we will work on this... first") — not started here. This doc's real numbers are
      the input that conversation needs before further design, not a replacement for it.

## Codex / related

- `agent-orchestrator/server/accounts.py` (`AccountProvider`) — the existing DeepSeek-routing seam this measurement work
  is adjacent to.
- `/active/unified-trading-system-repos/account-list.md` — the 6-account roster (sub A–F) with creds source, reset
  times, and billing dates.
- `/codex/06-coding-standards/model-tier-selection.md` — the qualitative opus/fable-required contract any future
  automated routing/classification system must not silently violate.
