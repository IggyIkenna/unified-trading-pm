---
doc_type: issue
title:
  "Codex doc-freshness ratchet went RED on the calendar, not on a change — 2 docs hit 91d and now fail every
  unified-trading-pm quality-gates.sh run, blocking all PM code commits"
summary: >-
  Measured 2026-08-11. `check_codex_doc_freshness.py` (ratchet mode, 90d staleness limit) reports 2 NEW violations:
  `/codex/05-infrastructure/live-deployment-monitoring.md` and `/codex/05-infrastructure/strategy-vm-launcher-shape.md`,
  both `last_reviewed: 2026-05-12`, both now 91d old. Neither doc changed — they aged past the limit overnight, so the
  gate flipped RED for a clean tree. Because it is a post-gate check in `quality-gates.sh`, it fails Pass 1 for EVERY PM
  code commit (no sentinel written → `quickmerge` Pass 2 refuses), for every agent on every host, until the
  `last_reviewed` dates are honestly refreshed. Confirmed general, not specific to any pending change. NOT re-baselined:
  `--baseline-write` would hand-raise a ratchet, which CLAUDE.md bans outright.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, quality-gates, ratchet, codex-hygiene, blocking]
related:
  [/plans/active/ci_consolidated_closeout_2026_07_25.md, /codex/12-agent-workflow/measurement-claims-discipline.md]
created: 2026-08-11
author: claude (interactive session, slot-3)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: cicd
drift_direction: advance-code
depends_on: []
source:
  [
    "hit live 2026-08-11 gating an unrelated pure-docs change in unified-trading-pm; the failing check named the two
    docs directly via scripts/quality_gates/check_codex_doc_freshness.py",
  ]
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    scripts/quality_gates/check_codex_doc_freshness.py,
    /codex/05-infrastructure/live-deployment-monitoring.md,
    /codex/05-infrastructure/strategy-vm-launcher-shape.md,
  ]
---

# A time-triggered ratchet turns every agent's next commit red

## What was measured

```
Scanned 316 codex doc(s) across 4 cutover-critical surface(s); 2 violation(s) (staleness limit: 90d).
  - /codex/05-infrastructure/live-deployment-monitoring.md: stale (91d old; last_reviewed=2026-05-12)
  - /codex/05-infrastructure/strategy-vm-launcher-shape.md: stale (91d old; last_reviewed=2026-05-12)
❌ Regression: 2 NEW violation(s) not in the baseline snapshot
```

Both are `status: current`, neither was edited. They crossed 90d by the passage of time. The check is a post-gate step
in `quality-gates.sh`, so Pass 1 exits non-zero and no `.qg_last_passed_sha` is written — and `quickmerge` Pass 2
refuses without the sentinel. That is every PM code commit, every agent, every host, starting today.

## Why this was not simply cleared

Three exits were available and two are closed:

- **`--baseline-write`** — re-baselining accepts the 2 violations as debt. That is hand-raising a QG ratchet, which
  CLAUDE.md bans without qualification ("never raise, only lower"). Not taken.
- **Bump `last_reviewed` to today** — one line, unblocks everyone in seconds, and is a LIE unless someone actually
  re-read the docs against reality. `last_reviewed` means "a human/agent checked this doc still matches the system", and
  one of these two covers the live-capital launcher path (`launch-strategy-live-vm.sh`, Copper MPC,
  `--dry-run-live-cutover-passed`). Stamping it unread is exactly the failure
  `/codex/12-agent-workflow/measurement-claims-discipline.md` was written to stop — claiming a property that was not
  measured. Not taken.
- **Actually review both docs** — the correct fix, and real work: 208 + 126 lines covering the live/forward deployment
  event contract and both strategy VM launchers. It needs someone who can verify the claims against the current scripts
  and services. That is this issue's todo.

## Todos

- [x] [DEVOPS] P1. **Re-review `/codex/05-infrastructure/live-deployment-monitoring.md`.** ✅ Done by a peer session,
      unified-trading-pm@3895be718f. It was a REAL review, not a date stamp: it caught a genuine path drift —
      `heartbeat_daemon.py` had moved from `deployment-service/deployment_service/vm/` to
      `deployment-service/scripts/vm/`, and the doc still pointed at the old location in two places. Corrected, then
      dated `last_reviewed: 2026-08-11`.
- [x] [DEVOPS] P1. **Re-review `/codex/05-infrastructure/strategy-vm-launcher-shape.md`.** ✅ Done by the same peer
      session, unified-trading-pm@3895be718f — also substantive: the doc said "the two strategy VM launchers" when two
      MORE have since been added under `deployment-service/scripts/vm/` (`launch-strategy-backtest-grid-vm.sh`,
      `launch-strategy-test-vm.sh`). Rather than silently widening the scope it added an explicit
      `SCOPE (verified 2026-08-11)` banner stating the doc is authoritative for the two CAPITAL-BEARING launchers only
      and that neither new script touches custody or real capital — so "two" now means "the two in scope", not "the only
      two that exist". Dated `last_reviewed: 2026-08-11`. **Gate verified GREEN after both**:
      `check_codex_doc_freshness.py` → `Scanned 316 codex doc(s) … 0 violation(s)`, `✅ At-or-below baseline`. PM code
      commits are unblocked; the ratchet was never re-baselined.
- [ ] [DEVOPS] P2. **Decide whether a calendar-triggered ratchet should be able to block commits at all.** The content
      of these docs did not change; the clock moved. A staleness sweep that hard-fails Pass 1 converts a documentation
      hygiene signal into a fleet-wide commit outage on an arbitrary morning, and the only fast exits are a banned
      re-baseline or a dishonest date — which is a design that pressures agents toward the dishonest one. Options to
      weigh: WARN-only for pure-age violations while staying HARD for content-drift ones; a grace band; or a scheduled
      pre-expiry nudge (the docs were 89d stale yesterday and nothing said so). Repo: unified-trading-pm.

## Note for whoever picks this up

Both docs are `status: current` and may well be entirely accurate — 91 days is not evidence of wrongness. The work is
the reading, not a rewrite. Expect the honest outcome to be "read it, still correct, dated today" for at least one.

---

## Update 2026-08-12 — the second RED was a checker bug, not 6 more stale docs

The morning after the fix above, the gate went RED again naming **6** docs from the `last_reviewed: 2026-05-13` cohort,
and it was recorded (in the 2026-08-12 deferred-work table) as "needs 6 honest re-reviews, blocking every PM code
commit". **That premise was wrong, and the correction is the point of this update.**

A stale local checkout was the whole story. Measured in one slot, before and after `git pull` (32 commits behind):

|                       | gate verdict                                                         | how it printed each violating path               |
| --------------------- | -------------------------------------------------------------------- | ------------------------------------------------ |
| local HEAD, 32 behind | `❌ Regression: 6 NEW violation(s) not in the baseline`              | repo-relative path, prefixed by the PM repo name |
| after sync to origin  | `✅ At-or-below baseline (0 new violations; 6 known, 6 at baseline)` | repo-relative path, unprefixed                   |

Same 6 docs, same dates, same 91d age — only the **path prefix** changed. The baseline stores repo-relative paths
(`codex/…`), the old checker emitted workspace-relative ones (`unified-trading-pm/codex/…`), so _every_ baselined
violation failed the set-membership test and re-reported as NEW. Fixed on origin by a peer as
`unified-trading-pm@9343990a17` — _"fix(qg): anchor codex-doc-freshness baseline paths to resolved PM root, not raw
`--workspace-root`"_.

**The transferable lesson**: a ratchet comparing a computed key against a stored key can fail OPEN into a false
regression, and it looks exactly like real debt — it names real files with real stale dates. The tell is the count
matching the _baseline_ count exactly (`6 total, 6 known-at-baseline` — every known violation "new"), which is a
set-mismatch signature, not an ageing signature. **Re-run a ratchet from a synced tree before believing it**, and treat
"all N known violations are simultaneously new" as a checker bug until proven otherwise. Cost of not doing so here: a
full day of planned work queued against a blocker that a `git pull` cleared.

## Update 2026-08-12 — the gate holds formally-retired docs to the live re-review cadence

Found while triaging those 6. **Three of them are not live docs at all:**

| doc                                                         | `status`     | `superseded_by`                     |
| ----------------------------------------------------------- | ------------ | ----------------------------------- |
| `/codex/02-data/data-catalogue-schema.md`                   | `superseded` | `service-shard-status-catalogue.md` |
| `/codex/05-infrastructure/ui-dependency-matrix.md`          | `superseded` | `ui-architecture.md`                |
| `/codex/05-infrastructure/ui-functionality-requirements.md` | `superseded` | `ui-architecture.md`                |

`_check_doc()` reads only `last_reviewed` and compares its age — the string `status` does not occur anywhere in
`check_codex_doc_freshness.py` (0 matches, whole file). So a doc explicitly marked retired, and pointing at its
replacement, is required to be re-reviewed every 90 days forever, on the same cadence as a live SSOT.

That is a standing generator of the exact dishonest-stamp pressure the P2 todo above is about, and worse here: an
"honest re-review" of a superseded doc has no honest outcome. You cannot verify it against current code — it is
_supposed_ to be wrong — so the only available actions are to stamp it unread or to re-review a doc nobody should be
reading. All three name their replacement, so the machine already has everything it needs to tell retired from stale.

## Todos (added 2026-08-12)

- [x] [SCRIPT] P2. ✅ **Exempt formally-retired docs from the staleness window in `check_codex_doc_freshness.py`** —
      operator-approved and SHIPPED 2026-08-12, `unified-trading-pm@c92375f05b`. Verified on origin by marker
      (`_is_retired_with_successor` present; `violation_count: 3` in the baseline blob), not by exit code. The commit
      was briefly held by an unrelated fleet-wide ratchet failure
      (`/plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`), resolved by its owning
      session the same morning. `_is_retired_with_successor()` skips `superseded|deprecated|archived` ONLY when a
      non-empty `superseded_by` is present; the exempt set is PRINTED as `exempt-retired` rather than dropped silently.
      Baseline ratcheted DOWN 6 → 3 by removing exactly the 3 retired entries (hand-edited removal — no
      `--baseline-write`, nothing added). Gate verified green under BOTH invocation styles (standalone
      `--workspace-root .` and quality-gates.sh's parent-root form):
      `✅ At-or-below baseline (0 new; 3 known, 3 at     baseline)`. 26 unit tests pass, including the mute-button guard
      (retired WITHOUT a successor stays stale), a `status: current` + stray `superseded_by` case,
      list/empty-list/blank-string successors, case-insensitivity, and a non-string `status` that must neither crash nor
      exempt. **Original proposal, for the record:** Proposal: skip `status: superseded|deprecated|archived`, but ONLY
      when the doc names its replacement (`superseded_by` non-empty) — so the exemption rewards pointing at the
      successor instead of becoming a way to mute the gate by editing one field. Docs affected today: the 3 tabled
      above. Keep them counted in the report as `exempt-retired` rather than dropping them silently, so the surface
      stays visible. This is a governance-semantics change to a gate, so it needs an explicit operator OK before
      shipping, not just a green run — raise it, don't merge it unilaterally. Repo: unified-trading-pm. Done when: the
      checker distinguishes retired from stale, and `codex_doc_freshness_baseline.yaml` shrinks by exactly the retired
      docs (baseline is shrink-only — no `--baseline-write`). **Measured surprise on implementation**: the exempt set is
      **5**, not the 3 this issue predicted — `bucket-naming-and-config.md` and `sports-integration-plan.md` are also
      retired-with-successor, but were still inside the 90d window so they had never surfaced as violations. They would
      have expired later and cost another round of the same pointless review. That is the argument for fixing the rule
      rather than the 3 instances: the instance list was never the real population.
- [ ] [DEVOPS] P3. **Decide the endgame for the 3 retired docs above, independent of the gate change.** A `superseded`
      doc that still sits on a cutover-critical surface is discoverable by grep and can mislead an agent into
      implementing against it. Options: SUPERSEDED banner at the top pointing at the replacement (the workspace's stated
      convention), or archival off the scanned surface. All three name a replacement, so the successor is always
      recoverable and no doc here is orphaned — this is a tidiness and grep-noise decision, not a data-loss one. Repo:
      unified-trading-pm.

## Update 2026-08-12 — a fourth failure mode: a genuine YAML syntax error reports as "no-frontmatter"

Hit live authoring a NEW codex doc (`agent-orchestrator-ci-escalation-wall-types.md`). The gate reported
`no-frontmatter` — which reads as "you forgot the `---` block" — but the file plainly had one. `_parse_frontmatter()`
(line ~122) wraps `yaml.safe_load(raw)` in `except yaml.YAMLError: return None`, and `_check_parsed()` maps ANY `None`
to the SAME `"no-frontmatter"` reason regardless of whether frontmatter was truly absent or present-but-unparseable —
confirmed by direct reproduction: `_parse_frontmatter()` returned `None`, but manually running `text.find("\n---\n", 4)`
found the closing delimiter fine (`end=1584`); the actual failure was `yaml.safe_load` raising
`ScannerError: could not find expected ':'` on the `summary:` field, whose plain (unquoted, no `>-`/`|` block indicator)
multi-line value contained a literal `": "` inside a sentence ("WALL_TYPES accepts: what triggers it") — YAML's
plain-scalar grammar treats an internal `": "` as a would-be mapping-key separator. Fixed the doc (added `>-` to
`summary:`, and removed the ambiguous colon besides) — confirmed via `check_codex_doc_freshness.py --workspace-root .`
going from 1 new violation to 0.

**The transferable lesson**: same shape as the two Updates above (a real-looking violation whose true cause is a
checker/mechanism bug, not the named doc's content) — but this one is a plain code smell (broad `except` collapsing two
distinct failure classes into one ambiguous verdict), not a data/path bug, so it is a different fix. Before trusting a
`no-frontmatter` verdict on a doc that visibly HAS a `---` block: run `_parse_frontmatter()` directly (or just
`yaml.safe_load` the block) to see the REAL exception — the ratchet's own message will send you looking for a missing
delimiter that was never missing.

- [ ] [SCRIPT] P3. **Distinguish "no-frontmatter" from "frontmatter present but failed to parse" in
      `check_codex_doc_freshness.py`.** Give `_parse_frontmatter()` a way to signal which case occurred (e.g. return a
      sentinel/raise a typed exception the caller catches, or a `(fm, reason)` tuple) so `_check_parsed()` can emit a
      distinct violation reason (`"yaml-parse-error"` with the caught exception's message as `detail`) instead of
      silently reusing `"no-frontmatter"` for both. Low urgency (P3) since the underlying doc-authoring bug is what
      actually blocks a commit either way — this is purely about the diagnostic pointing the next person at the right
      fix on the first read instead of a false "you're missing the frontmatter block entirely" lead. Repo:
      unified-trading-pm.
