---
doc_type: issue
title:
  context-threshold-nudge.sh's transcript-byte-count heuristic false-triggered the /pre-compact + /compact nudge at real
  usage ~29%, not anywhere near its intended 65% threshold
summary: >-
  During an interactive session, the `UserPromptSubmit` hook `cursor-configs/hooks/context-threshold-nudge.sh` fired its
  one-time nudge telling the assistant to stop and run `/pre-compact`, then tells the operator to run `/compact` — which
  happened. The operator then asked why, reporting real usage well under 30%. Cross-checked against the session's own
  transcript: the last assistant turn's real `message.usage` fields (`input_tokens` + `cache_creation_input_tokens` +
  `cache_read_input_tokens`) summed to ~293k of the 1M budget (~29%, matching the operator's own reading almost
  exactly), yet the hook's heuristic — raw transcript bytes since the last `compact_boundary` event, divided by 4 — must
  have computed ≥65% (650k) to fire. The hook's own header comment already documents two prior instances of this exact
  heuristic being wrong (a 5x-too-small budget constant, fixed 2026-07-23; counting the WHOLE transcript file instead of
  since-last-boundary, measured to overshoot by up to 1475% on one real session, fixed 2026-07-25) and explicitly flags
  the remaining failure mode as an open, unaddressed caveat: "large tool outputs / repeated system-reminder content can
  inflate transcript bytes beyond what actually occupies live context." This session is a clean reproduction of exactly
  that caveat — a session with many large tool outputs (parallel sub-agent completion reports, repeated full-file
  system-reminder dumps) whose raw transcript bytes grew well beyond what the harness's own internal context management
  (which prunes/summarizes old large tool results without necessarily emitting a formal `compact_boundary` event) was
  actually still holding live.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [claude-code, hooks, precompact, context-lifecycle, heuristic, false-positive]
related:
  [/codex/05-infrastructure/local-tmux-precompact-watcher.md, /codex/05-infrastructure/claude-code-settings-symlink.md]
created: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
source: [interactive-session-2026-08-03]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    unified-trading-pm/cursor-configs/hooks/context-threshold-nudge.sh,
    /codex/05-infrastructure/local-tmux-precompact-watcher.md,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
  ]
---

# What happened

`context-threshold-nudge.sh` runs on every `UserPromptSubmit`. It estimates context usage as
`(transcript bytes since the last compact_boundary event) / 4`, compares against 65% of a 1,000,000-token budget, and —
once, sentinel-gated per session — injects a message instructing the assistant to stop the current task, run
`/pre-compact`, then tell the operator to run `/compact`. It fired mid-session here. The operator's own reading of real
usage was under 30%.

Direct verification against this session's own transcript (`~/.claude/projects/.../<session>.jsonl`): the last
assistant-turn `message.usage` object —

```
{"input_tokens": 2, "cache_creation_input_tokens": 3893, "cache_read_input_tokens": 298570, "output_tokens": 486, ...}
```

— sums to `input_tokens + cache_creation_input_tokens + cache_read_input_tokens` ≈ **293-298k tokens**, i.e. **~29-30%
of the 1M budget**. This is the REAL number the Anthropic API reports for exactly "how many tokens of context did the
model see for this turn" — and it matches the operator's own reading almost exactly. For the hook's heuristic to have
crossed 65% (650k), its raw-byte estimate must have overshot the real figure by roughly 2x.

Confirmed this is NOT sub-agent (Task/Agent tool) chatter leaking into the byte count — this session's transcript has
**zero** `"isSidechain":true` lines; sub-agent transcripts are written to entirely separate files (`tasks/<id>.output`),
never merged into the main transcript. The inflation instead comes from ordinary main-thread content that legitimately
got WRITTEN to the transcript at full size (large tool outputs — this session ran 8 parallel scouting sub-agents, each
returning a multi-KB final report folded into the main conversation as plain text — plus at least one large config file
dumped verbatim via `<system-reminder>` more than once) but which the harness's own internal context management can
prune, truncate, or summarize out of the LIVE model context progressively, without necessarily emitting a formal
`compact_boundary` event to mark that pruning. The hook's byte count sees only what was ever written to disk; it has no
visibility into what the harness silently dropped from the live window afterward — exactly the caveat the script's own
header comment already named as unaddressed.

# The fix

Prefer the REAL usage data already present in the transcript over the byte-count estimate. Every assistant-turn line in
the transcript already carries `message.usage.{input_tokens,cache_creation_input_tokens,cache_read_input_tokens}` — the
exact token count the API reports for that turn's input, i.e. ground truth for "how much of the context window is
currently occupied," with no estimation needed. Use the LAST such value found in the transcript as the primary source;
fall back to the existing byte/4 heuristic only when no assistant-turn usage data exists yet (e.g. a freshly-started
session with no completed turn).

# Plan

- [x] [SCRIPT] P3. **Rewrite `context-threshold-nudge.sh` to compute `EST_TOKENS` from the last transcript line's
      `message.usage` fields (summed) when available, falling back to the existing byte/4 heuristic only when no
      assistant-turn usage data exists.** Update the nudge message to state whether the figure is `measured` (real
      usage) or `estimated` (heuristic fallback), so a future false-positive is distinguishable from a real one at a
      glance. Verify against this session's own transcript (expect the computed figure to land near the ~29-30%
      independently derived above, not a byte-count-inflated number) before shipping. — `unified-trading-pm@070d679f1`.
      Verified via `bash -x` traces against 3 cases run directly against this hook script: (1) this session's real
      transcript → `REAL_TOKENS=330394`, `SOURCE=measured`, correctly stayed silent (well under the 650000-token
      threshold, confirming the false positive is gone); (2) a synthetic transcript line with
      `cache_read_input_tokens=700000` → fired with `"Context usage is MEASURED at ~70%..."`; (3) a synthetic transcript
      with no assistant/usage line at all → `REAL_TOKENS=` empty, correctly fell back to `SOURCE=estimated`,
      `EST_TOKENS=19` (byte/4 on a 76-byte fixture).

# Progress Log

- **2026-08-03**: filed, diagnosed (real transcript `message.usage` cross-check ≈29-30%, matching the operator's own
  reading, vs the byte heuristic's false ≥65% read), fixed, and verified all in one session. See the todo's own evidence
  line for the fix commit + the 3 verification cases run. No residual follow-up — archiving next.
