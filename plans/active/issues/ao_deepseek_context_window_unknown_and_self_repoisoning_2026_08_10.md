---
doc_type: issue
title:
  DeepSeek's real context window is unknown, its learned value re-poisons every few minutes, and the fallback prior is
  almost certainly wrong
summary: >-
  DeepSeek sessions reported ~5x their real context on 2026-08-10 (11 of 21 working slots at 100%, three thrashing)
  because the learned window was ~5x too SMALL — deepseek-v4-pro held calibrated_window=82,715 against its own
  watermark_tokens=266,764. The impossible-window guard now shipped (agent-orchestrator@4af78dc99) stops that class, but
  it leaves a WORSE question open: with the bad calibration ignored, both DeepSeek models now fall back to model_tier's
  1,000,000 prior, and the measured evidence says the true window is nearer 180-270K. That is the DANGEROUS direction —
  under-reporting is exactly what let a session run to a hard wedge in the 2026-08-08 incident. Root cause of the
  DeepSeek-vs-Claude asymmetry is measured and recorded below: DeepSeek's usage is ~99.4% cache_read_input_tokens and
  its pane renders a real CLI percentage almost every turn, so it calibrates constantly, where sonnet-5 almost never
  does.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, deepseek, measurement, context-probe, worker-lifecycle]
related:
  [
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator observation 2026-08-10 ("with deepseek we got this context bloating issue reappearing, is deepseek pro and
  flash set to 1m or 500k?"), measured live via read-only SSM in the same session.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_probe.py,
    agent-orchestrator/server/model_tier.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
  ]
---

# DeepSeek's real context window is unknown and its learned value re-poisons itself

## Measured evidence (orchestrator VM, 2026-08-10, read-only)

Live `message.usage` from the newest transcript of each session:

| session         | model             | input | cache_read | cache_creation | token_total |  pane % |
| --------------- | ----------------- | ----: | ---------: | -------------: | ----------: | ------: |
| orch-slot-2     | deepseek-v4-pro   |   963 |    162,304 |              0 |     163,267 |  **91** |
| orch-slot-19    | deepseek-v4-flash |   168 |    227,584 |              0 |     227,752 | **100** |
| orch-agent-main | deepseek-v4-flash |    80 |     70,784 |              0 |      70,864 |    none |

Learned-registry state at the same moment, and how fast it moves:

| model             | calibrated_window | watermark_tokens | corpus figure (2026-08-08) |
| ----------------- | ----------------: | ---------------: | -------------------------: |
| deepseek-v4-pro   |  82,715 → 180,191 |          266,764 |                    425,572 |
| deepseek-v4-flash | 178,952 → 254,635 |          327,909 |                    917,159 |

Both `calibrated_window` values moved between two reads minutes apart — this is a live re-poisoning loop, not a stale
artifact.

## Why DeepSeek and not sonnet-5 (the operator's question, answered from data)

Two measured asymmetries, both visible in the table above:

1. **DeepSeek's pane renders a real CLI percentage nearly every turn** (91%, 100%), and those readings are
   calibration-eligible (`derive_calibration_pct` returns them — they are genuinely CLI-rendered, not the heuristic).
   `context_probe`'s own docstring records that the `"N% context used"` readout matched **0 of 11** live worker panes on
   Claude, because the CLI only renders it near the ceiling. So Claude sessions almost never calibrate; DeepSeek
   sessions calibrate constantly. More calibration events on a wrong denominator = faster, repeated poisoning.
2. **DeepSeek usage is ~99.4% `cache_read_input_tokens`** with `cache_creation` at exactly 0, a very different shape
   from Claude's. `token_total()` sums input + cache_read + cache_creation, so for DeepSeek it is essentially a pure
   cache-read count.

Combined: a session whose pane says 100% at 227,752 tokens writes `calibrated_window = 227,752`. If the CLI's own
denominator for a DeepSeek session is not the model's true window, every one of those frequent calibrations is wrong,
and they keep overwriting each other.

## The open question this leaves — and why it is P0

The shipped guard (`agent-orchestrator@4af78dc99`) refuses a window smaller than the observed watermark, at write AND
read time. That correctly stops the "reports 5x its real context" bloat. But with the bad calibration ignored, both
models now resolve to **`model_tier`'s 1,000,000 prior**, while every measurement above points at a true window nearer
**180-270K**.

Under-reporting is the dangerous direction: it is precisely what
`/plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md` records as
letting a session sail past every threshold and run to the model's hard limit. So the fleet may have traded
over-compaction for under-compaction, and neither is correct until the real number is established.

## Todos

- [x] ✅ [BACKEND] P0. Establish DeepSeek's ACTUAL usable context window for both `deepseek-v4-pro` and
      `deepseek-v4-flash` from evidence rather than the shared 1M prior — e.g. the largest `token_total` observed
      immediately before a `compact_boundary` across many sessions, which is a lower bound the provider itself enforced.
      Done-when: a per-model figure with its sample size and method is recorded in this doc's Progress Log. **DONE
      2026-08-10 (slot-19)** — per-model lower bounds recorded in the Progress Log below: pro ≈ 325K (57 boundaries / 26
      sessions), flash ≈ 468K (266 boundaries / 117 sessions); zero boundaries ≥500K for either model (the 1M prior is
      unsupported by any observed compaction).
- [ ] [BACKEND] P0. Give `model_tier.context_window()` a DeepSeek-specific prior from todo 1 instead of falling through
      to the 1M default. The current fallback is a Claude number applied to a non-Claude model, and it is the value in
      force right now. Done-when: a unit test asserts the DeepSeek prior is not the 1M default, and the live registry
      resolves both models to it.
- [ ] [BACKEND] P1. Decide whether a DeepSeek pane percentage may calibrate at all. If the CLI's denominator for a
      DeepSeek-backed session is not that model's real window, `derive_calibration_pct` is authoritative about the CLI,
      but the CLI is not authoritative about DeepSeek — in which case DeepSeek must be excluded from calibration and
      learn from the watermark alone. Done-when: the decision plus its evidence is recorded here and enforced in
      `observe()`.
- [ ] [BACKEND] P1. Verify `token_total()` is the right measure for a provider whose usage is ~99.4% cache-read with
      zero cache-creation. Confirm cache_read is genuinely resident context and not a cumulative counter (a cumulative
      counter would inflate every DeepSeek reading without bound). Done-when: the finding is recorded, with the raw
      per-turn usage series from one session as evidence.
- [ ] [BACKEND] P2. Add a standing invariant check to the registry: alert when any model's `calibrated_window` moves by
      more than a set fraction between polls. Both DeepSeek entries moved ~2x within minutes and nothing noticed — that
      oscillation is itself the signal a denominator is wrong.

## Progress Log

- 2026-08-10 — Filed from a live operator-reported "context bloating" symptom. Impossible-window guard shipped
  (`agent-orchestrator@4af78dc99`, write + read side) and the two contradictory entries were purged out-of-band, which
  cleared the immediate 5x over-reporting. The purge deliberately left both models on the 1M prior, which todo 2 must
  correct — that is a knowingly-temporary state, not a resolution.
- **slot-19 2026-08-10 (todo 1 — usable-window measurement from evidence)**: scanned all 615 transcripts under
  `~/.claude-configs/*/projects/**/*.jsonl` that carry a `compact_boundary` system record; for each boundary read
  `compactMetadata.preTokens` (the CLI's own pre-compact token count) and cross-checked it against `token_total()` of
  the last real assistant usage record before the boundary (same formula as `server/context_probe.py::token_total`);
  model classified per-boundary from that assistant record's `message.model`; streamed line-by-line (bounded memory);
  only `deepseek-v4-pro`/`deepseek-v4-flash` kept. Observations span 2026-08-04 → 2026-08-10.

  | model             | boundaries | distinct sessions | max preTokens (CLI) | max computed token_total |  median |  auto (CLI) max | manual (AO) max |
  | ----------------- | ---------: | ----------------: | ------------------: | -----------------------: | ------: | --------------: | --------------: |
  | deepseek-v4-pro   |         57 |                26 |             325,175 |                  324,819 | 121,772 |   259,441 (n=5) |  325,175 (n=52) |
  | deepseek-v4-flash |        266 |               117 |             468,339 |                  467,336 | 167,522 | 190,798 (n=139) | 468,339 (n=127) |

  **Per-model usable-window figure (lower bound the provider enforced): `deepseek-v4-pro ≈ 325K`,
  `deepseek-v4-flash ≈ 468K`** — the largest context each model's sessions demonstrably held immediately before a
  compaction (pro: session `821c940a-…` @2026-08-10T09:37; flash: session `3e4676d0-…` @2026-08-07T01:24). Supporting
  facts: (1) computed `token_total` matches the CLI's own `preTokens` within ~0.2% (max deltas pro 356 / flash 1,003) —
  validates `token_total` as a resident-context measure and directly addresses todo 4's cumulative-counter concern (a
  cumulative cache-read counter could not track the CLI's independent per-boundary count); (2) **zero** compact
  boundaries ≥500K for either model — nothing in the corpus supports the current 1M prior; (3) auto-triggered (CLI's own
  decision) boundaries cluster at 169-259K (pro) / 179-191K (flash) — consistent with the CLI defaulting the unknown
  DeepSeek model string to a ~200K window (why DeepSeek panes read ~100% at ~200-227K, the opening symptom), while AO's
  manual/forced compactions reached 325K/468K. Recommend todo 2 seed `model_tier.context_window()`'s DeepSeek prior from
  these lower bounds (not 1M), and todo 3 treat the CLI's ~200K denominator as the mis-calibration source. Note: the
  learned registry's current watermarks (pro 324,819 / flash 427,391) already match or under-cut these figures — the
  live probe only reads current-session tails, so the historical max (flash 468,339) is not yet in the registry.
