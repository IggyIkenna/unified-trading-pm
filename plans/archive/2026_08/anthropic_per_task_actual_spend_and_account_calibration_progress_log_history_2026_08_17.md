---
doc_type: plan
title: Progress Log history — Anthropic per-task actual spend calibration (2026-08-10/11 sessions)
summary: >-
  Pure historical reference — the 2026-08-10/11 diagnosis, first (uncorrected) calibration pass, feasibility probe,
  laptop-contamination probe, cache-transfer reasoning, the ~190x controlled measurement, cost-structure breakdown,
  and session lessons extracted verbatim from
  `anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md`'s Progress Log to bring that still-active
  plan back under the line-cap hard gate (was 1014L). Every figure this history still feeds forward is already
  restated at its point of use in the parent plan; nothing here is the current SSOT for anything actionable.
status: complete
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, billing, cost-attribution, pricing, anthropic, calibration, progress-log-history]
related:
  [/plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data_engineering
effort: low
drift_direction: none
locked_by:
locked_since:
context_scope: []
supersedes:
superseded_by:
depends_on:
source: "line-cap extraction, 2026-08-17 (slot-21) — see parent plan's 'Deferred work after 2026-08-10' entry"
---

> 🟢 **ARCHIVED 2026-08-17** (na-eligibility-audit, ao tranche) — 0 tracked todos, pure Progress-Log-history extraction
> per `task_template.md`'s Finding-J convention. Parent plan:
> `/plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md`.

# Progress Log history — Anthropic per-task actual spend calibration

> No open todos here. This doc exists only so the parent plan's Progress Log narrative from 2026-08-10/11 stays
> readable somewhere instead of being deleted. The parent plan is the SSOT for everything actionable; this is backup
> detail only.

### 2026-08-10 — Diagnosis + first calibration pass (interactive session, read-only)

**Root cause of the blank $ column**: `deepseek_usage._PRICE_PER_MILLION` contained exactly two entries, both DeepSeek.
Every Claude turn priced to `None`, and `state_store.slots.window_task_usage_totals`'s deliberate "any unpriced row
nulls the whole window" rule blanked the aggregate. Not a data gap — a missing price table.

**Live unpriced distribution** (`task_usage`, 2,622 rows):

| provider       | model                     |  rows | unpriced |
| -------------- | ------------------------- | ----: | -------: |
| anthropic/null | `claude-sonnet-5`         | 1,738 |    1,738 |
| anthropic      | `claude-sonnet-4-6`       |   213 |      213 |
| null/anthropic | `claude-opus-4-8`         |    22 |       22 |
| anthropic/null | `<synthetic>`, mislabeled |     8 |        8 |
| deepseek       | `deepseek-v4-pro`         |   505 |        0 |
| deepseek       | `deepseek-v4-flash`       |   125 |        1 |

**First calibration pass** — list-priced value consumed in each fully-consumed weekly window vs subscription cost.
Method (A) = `task_usage` scoped by `account_id`; method (B) = transcripts resolved via `agents.account_id`. Sonnet-5
valued at its standard rate.

| account            | tier  |   (A) |   (B) | published band        |
| ------------------ | ----- | ----: | ----: | --------------------- |
| sub-c-ikenna-odum  | max20 | 46.0x |  4.7x | 6-10x                 |
| sub-d-odum1default | **pro (corrected 2026-08-16 — see parent plan's Progress Log; recomputed at the $4.52 Pro denominator)** | 350.1x | 187.3x | 6-10x (excluded — Pro) |
| sub-f-odum2default | max20 | 22.4x | 23.0x | 6-10x                 |
| sub-e-odum3default | max20 |  7.7x |  3.5x | 6-10x                 |
| sub-a-ikenna       | pro   |  107x | 63.8x | 3-6x (excluded — Pro) |

**Verdict: not a usable multiplier yet.** Method (A) is a strict subset of the same turns as (B) and should be a lower
bound, yet reads higher for 4 of 5 accounts. That inversion isolates the two defects now tracked as todos 1-3:
`task_usage` double-counts (whole-session one-offs + overlapping windows), and transcript attribution silently loses
every pre-compaction session. `sub-f` is the only account where both methods converge (22.4x vs 23.0x), consistent with
it having rotated sessions least. Shipping any multiplier from this spread would bake a 3x-107x error into the cost
column, so the attribution fixes gate the pricing work.

### 2026-08-10 — Calibration feasibility probe (read-only): what data does NOT exist

Follow-up to the operator's question "anything we need to research to avoid an unfair representation, and do we only
measure fully-consumed windows?" — four findings that reshaped the todo list:

1. **No usage-meter history exists.** `account_usage` is keyed by `account_id` alone — 8 rows, 8 distinct accounts,
   current state only. Every past weekly and 5-hour window is unrecoverable, so today there is exactly ONE weekly
   observation per account and ZERO historical 5h observations. Retroactive 5h calibration is impossible; sampling has
   to start now (todo 1) or the same n=1 problem persists indefinitely. This is the most time-critical item in the plan.
2. **Most accounts are 5-hour-bound, not weekly-bound.** `representative_claim`: `five_hour` for sub-a, sub-b, sub-d,
   sub-e, sub-f; `seven_day` only for sub-c. Weekly-only calibration therefore measures the non-binding constraint for 5
   of 6 accounts.
3. **No overage was ever paid** — `overage_status='rejected'` on every account (`out_of_credits` for sub-a/sub-b,
   `org_level_disabled` for sub-c/d/e/f). The subscription price is the full cost for these windows, so the denominator
   of the multiplier needs no overage adjustment. One less confound.
4. **Double-counting is NOT the main driver of the 6x spread.** Measured: only **162 overlapping `task_usage` row
   pairs** (both windows known) and **3 rows with `assigned_at IS NULL`** (2 anthropic, 1 deepseek) doing whole-session
   counting. Against 2,622 rows that is ~6% — real (todo 3 still fixes it) but far too small to explain a 6x spread. The
   leading explanation is **coverage**: `sub-e`'s window opens 2026-08-05 23:00 while `account_id` capture began ~08-06,
   so its first day is structurally missing, and it is precisely the account with the fewest attributed rows (49). This
   is what todo 5's capture-era gate exists to prevent. Partially answers todo 4 — the remaining piece is the token
   volume inside those 162 pairs.

Also unresolved and now tracked: the `weekly_sonnet_pct` sub-meter is NULL/0 on every account, so there is currently no
per-model quota signal to validate a scalar multiplier against (todo 7); and ~78% of our list-priced value is cache
reads, whose quota weighting is unknown (todo 8).

### 2026-08-10 — Laptop-side probe: the contamination is confined to ONE account

Operator flagged that the same Claude accounts are used on their laptop (including the session authoring this plan), so
agent-orchestrator-only token sums would understate consumption and bias the multiplier DOWNWARD. Measured on the
laptop:

- **The laptop's interactive login is `iggy2london@gmail.com` = `sub-b-iggy2london`** (`~/.claude.json` `oauthAccount`).
- **Local slot config dirs went dormant 2026-08-04** (`~/.claude-configs/orch-slot-90{1..5}`, `orch-slot-99` — newest
  transcript 2026-08-04 14:35), while every current calibration window opens 2026-08-05 or later.
- ~~Therefore `sub-c`, `sub-d`, `sub-e`, `sub-f` are pure agent-orchestrator for their current windows.~~ **RETRACTED
  same day — see the account-switch entry below. No account can be certified laptop-free.**
- `sub-b` is genuinely contaminated and cannot be split: **local transcripts carry no account identifier** (fields are
  `cwd`, `effort`, `entrypoint`, `gitBranch`, `sessionId`, `requestId`, `timestamp`, `version` — no account/org id). It
  is also the only account not at 100% weekly (63%), consistent with being the shared one.

**CORRECTION to the 2026-08-10 feasibility probe — overage WAS paid.** That entry recorded "no overage was ever paid,
the denominator needs no adjustment", reading `overage_status='rejected'`. That reading was wrong: `rejected` +
`out_of_credits` means overage is currently REFUSED because the pool is exhausted, not that none was consumed. The
laptop account's live `/usage` payload shows `extra_usage.used_credits = 15078` of `monthly_limit = 20000` (GBP, 2
decimal places) — **£150.78 of real additional billing this month**. Cost denominators must be subscription + extra
usage, with currency recorded (todo 8).

**Anthropic exposes no dollar figure for subscription usage** — `limit_dollars` / `used_dollars` / `remaining_dollars`
are in the `/usage` schema but `null` for both the `five_hour` and `seven_day` windows; only `extra_usage` carries
money. **This does NOT block calibration** (operator correction, same day): we know what we pay, so the subscription
price is the anchor and Anthropic only ever needed to supply the consumption side. An earlier note here framed the
missing dollar field as a blocker — it is not; it merely removes an independent cross-check.

**Window cost formula (operator ruling 2026-08-10)**: `7 / days_in_month x monthly_price`, with the window required to
sit entirely inside one calendar month. For max20 in August 2026 that is `7/31 x $200 = $45.16` — a 1.9% correction to
the $46.00 (averaged 4.348 weeks/month) used in the first pass. All five current windows satisfy the within-month
constraint.

**Re-run of the clean accounts against the corrected denominator**, valued at the published August rates INCLUDING the
Sonnet-5 promotion (the correct valuation for an August window):

| account            | list value (promo) | multiplier |             at standard rates |
| ------------------ | -----------------: | ---------: | ----------------------------: |
| sub-c-ikenna-odum  |          $1,455.53 |      32.2x |                         46.9x |
| sub-d-odum1default (**pro, corrected 2026-08-16 — recomputed at the $4.52 Pro denominator, see parent plan's Progress Log**) |          $1,088.19 |     240.8x |                        350.7x |
| sub-f-odum2default |            $699.73 |      15.5x |                         22.8x |
| sub-e-odum3default |            $274.89 |       6.1x | 7.8x (excluded — capture era) |

**The denominator is now exact and the spread survives it** — 15.5x to 32.2x across three clean, identically-entitled
max20 accounts. The residual error is therefore entirely in the NUMERATOR (attribution coverage), which todos 2-6
address; no further denominator precision will close it.

**Timing trap**: the Sonnet-5 promo expires 2026-08-31, so the identical token volume becomes ~50% more valuable at list
on 2026-09-01. The multiplier jumps by half with no change in usage or spend — hence todo 10's requirement that every
multiplier carry its valuation date and rate set.

**AO is discarding most of the `/usage` payload** (todo 9): it keeps `weekly_pct` and `five_hour_pct` and drops the
`seven_day_opus` / `seven_day_sonnet` per-model sub-meters, the `limits[]` array with model-scoped buckets
(`kind: weekly_scoped`, `scope.model.display_name: "Fable"`), and the whole `extra_usage` block. Those per-model
sub-meters are exactly the quota-weight signal todo 7 was written to go hunting for.

### 2026-08-10 — Why the 190x DOES transfer to AO: identical cache profiles

Operator question: if the quota meter is weighted by the cache discount, how would that change the calibrated 190x?

- **If the meter is price-weighted** (cache reads counted at 0.1x, as they are billed), quota consumed is proportional
  to list value and **the multiplier is workload-INDEPENDENT** — 190x transfers to any mix unchanged.
- **If the meter counts raw tokens equally**, 190x is specific to a 99%-cache-read mix, and cache-light work measures
  HIGHER (the same quota buys full-rate tokens instead of 0.1x ones). So 190x is a FLOOR, not a ceiling.

**Either way it transfers to AO**, because AO's workload sits at the same point on the curve — measured cache-read share
of total tokens: **laptop 98.90%** (1,267,416,118 / 1,281,547,098) vs **AO on `sub-c` 98.54%** (5,527,290,327 /
5,609,037,297). The two are the same shape, so the metering hypothesis does not change the transfer. The meter
experiment is therefore a REFINEMENT for pricing genuinely cache-light work (a short one-shot task), not a blocker on
using ~190x for AO today.

### 2026-08-10 (evening) — Deferred work snapshot (superseded — calibration code has since landed)

| item                                                        | state / why deferred                                                                                                                                                                                                      | blocked on                       |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **Land the calibration code on LDR**                        | **Not done — WRITTEN AND GATED, not shipped.** Full QG green at 17:53 (3,306 tests, basedpyright/tsc/vitest clean) and its own 94 tests pass; blocked only by a PEER session's in-flight refactor in this shared checkout | a peer session finishing (below) |
| **Land the per-account axis** (state store/API/UI/pw)       | **Not done — same block, plus a direct file collision**: the `account_id` filter lives in `server/state_store/slots.py`, which the peer is mid-refactor on                                                                | same                             |
| Verify the reservation held (todo 11)                       | **Cannot be done yet** — needs the first post-reset window                                                                                                                                                                | Wednesday resets                 |
| Pro + max20 multipliers (todos 14, 21)                      | **Cannot be done yet** — needs a post-reset window on `sub-a-ikenna` / `sub-e-odum3default`                                                                                                                               | Wednesday resets                 |
| Reprice `--apply` on the live VM                            | **Operator-owned** — mutates ~1,993 production rows; run the dry run first                                                                                                                                                | operator                         |
| Audit the 23 `agents/` role files for sequential-step prose | **Not done** — cheap, and the guidance is undermined wherever a role doc walks an agent through one command per step                                                                                                      | nobody                           |
| Plan line-cap extraction                                    | **DONE 2026-08-17** — this history doc IS that extraction.                                                                                                                                                                  | nobody                           |

**The block, precisely** (so the next session does not re-diagnose it): a peer session is running a large git-status
single-source-of-truth refactor in this same checkout — `server/orm.py`, `server/failover.py`, `server/routes/state.py`,
`server/routes/git_health.py`, `server/state_store/slots.py`, `server/worker_liveness/`, `notifications/slack.py` and
six test files, all dirty and uncommitted. `quickmerge` re-gates against the WHOLE working tree, and the tree is red for
exactly one reason: `ruff format --check` wants to reformat `server/worker_liveness/_git_alerts.py`, a file this plan
never touched. Everything else passes. Formatting it would be editing a peer's mid-refactor WIP, so it was left alone.
**Resolution is to re-run `quickmerge` once that refactor lands** — no rework is needed, and nothing here is at risk,
because the calibration code is a strict superset of a tree that already went green. (This blocker cleared — the
calibration code's `[x]` checkmarks in the parent plan's Todos are the evidence.)

### Session lessons 2026-08-10/11 — shipping through a shared, actively-mutated checkout

- **A backup taken from a checkout another process is mutating is NOT a backup.** Three "wipes" this session were one
  cause: a peer session running `pull --rebase --autostash` + `safe-doc-push` reconcile quarantines the shared
  checkout's dirty state into stashes (`stash@{0}: safety-snapshot: pre-reconcile quarantine (15 autostash entries)` —
  it contained the missing files). Worse, TWO of my three backups were taken AFTER that reverting had begun, so
  restoring from them silently RE-INTRODUCED the reverts. Only backup #1 held the settings registration / CLAUDE.md rule
  / SSOT fix; only backup #3 held the later lint fix. The ship set had to be reconstructed PER FILE from whichever
  snapshot held the good version, verified by grepping content markers. **Verify markers before trusting any restore.**
- **`git stash list` is the first thing to check when a file "vanishes"** in this workspace, not the last. The stash
  message literally says "quarantine". Checking it the first time would have saved most of the night.
- **The window is the enemy, not the race.** edit -> ~10-min gate -> commit loses to a peer reconciling every ~5 min, no
  matter how correct each step is. The fix is an isolated CLONE (own `.git`, on LDR), not a worktree — PM's full gate
  cannot run in a worktree at all (`unified_api_contracts` absent; symlinking `.venv` does NOT fix it).
- **Four independent PRE-EXISTING blockers sat between a green tree and a PM commit**, none caused by this work:
  VERSION_SPLIT (manifest cache claiming an unminted tag), the QG worktree self-audit, the duration meta-gate under host
  load, and two codex docs tipping past 90 days at midnight. Each is filed with its own issue doc.
- **`quality-gates.sh` is NOT a superset of the commit hooks.** QG lints only `server/`-equivalent paths; the pre-commit
  hook also lints staged `tests/` and `scripts/` and `cursor-configs/`. A fully green gate then failed the commit twice
  on ruff findings the gate never looked at. Filed.
- **A truncated read is not evidence of absence** — cost a wrong "fix" that broke a WORKING pointer
  (`setup-workspace-config-symlink.sh` does exist; `ls | head -15` had cut off before it). This is now a CLAUDE.md rule.
- **Verify a "shipped" claim by ARTIFACT, not by the script's success line.** A failed quickmerge left the test file
  staged and the implementation gone — invisible from a commit message. Two other slots caught a false "landed" claim in
  minutes using per-artifact checks on origin (`git cat-file -e origin/<b>:<path>`, grep the registration).

### Session lessons (carry these, they cost real time)

1. **Dedupe transcript lines by `requestId` for TOKENS, but UNION content blocks across all lines sharing it.** Claude
   Code writes one JSONL line per content block. Keeping only the first line silently drops `tool_use`/`thinking` blocks
   and produced two wrong figures in this session (89% thinking, 71% tool-free turns) before correction.
2. **`overage_status: rejected` + `out_of_credits` means overage WAS used and the pool is now exhausted** — not that
   none was ever paid. Cost `GBP 150.78` was invisible under the first reading.
3. **`~/.claude-accounts/*.env` files gate HEADLESS slot spawns only.** Their absence says nothing about interactive
   use, which goes through `claude /login`. This invalidated a "provably clean account" claim.
4. **`account_usage` and `~/.claude.json` are both CURRENT-STATE only.** No history exists for the usage meters or the
   laptop login; past windows are unrecoverable, which is why the samplers are P0.
5. **A checker that takes a path argument may ignore it.** `check_reference_paths.py` scans all 2,042 files regardless,
   and its `--only` mode reads the git index — so validating a single unstaged file needs a different approach.
6. **This checkout is ~98 commits behind origin and cannot `git pull --ff-only`** (peer sessions' untracked files block
   it). Local validators therefore disagree with the pre-commit hooks, which run against origin in an isolated worktree.
   Trust the hook, not the local run.

### 2026-08-10 — AO account rotation timeline, and the cache-accounting verification

**AO burns accounts to exhaustion then rotates**, rather than spreading load — measured from `task_usage` + `agents`:
`sub-e` 08-06 00:18 -> 08-08 (49 tasks, exhausted), `sub-f` 08-06 22:53 -> 08-09 23:44 (166, exhausted), `sub-c` 08-07
19:27 -> 08-09 18:46 (274, exhausted), `sub-d` 08-07 19:35 -> 08-10 09:14 (216, exhausted), `sub-b` 08-09 19:14 -> live
(172, 63%), `sub-a` pro 08-06 -> 08-10 (128, exhausted). DeepSeek volume spikes on 08-10 exactly as the Anthropic pool
empties. The `agents` table attributes further back than `task_usage` does (sub-d from 08-02, sub-b and sub-c from
08-04) and is the usable attribution source for the pre-08-06 window where `task_usage.account_id` is null.

**Cache accounting verified correct** (operator challenge): the flat `cache_creation_input_tokens` equals the
`cache_creation` 5m+1h breakdown EXACTLY over the controlled window (11,711,885 = 747,496 + 10,964,389, zero per-turn
mismatches), the four token classes are disjoint so summing cannot double count, and no server-tool calls were billed
(`web_search=0`, `web_fetch=0`). The gross figure therefore already incorporates cache pricing at published rates (read
0.1x, write 1.25x/2.0x) — it does NOT assume an uncached workload.

**Open question the multiplier's transferability rests on**: we know what Anthropic CHARGES for cache, but not what its
quota METER counts. If the meter weights cache reads like any other token, 7% of weekly bought 1.28B tokens
(~18.3B/week); if it largely ignores them, 7% bought ~14.1M non-cache tokens (~201M/week). One observation cannot
separate these, and they imply very different multipliers for differently-shaped work. Testable with a second window at
a very different cache-read share — tracked in the parent plan (todo 8).

### 2026-08-10 — CONTROLLED MEASUREMENT: ~190x on a clean laptop-only window (best datapoint to date)

Operator supplied a controlled experiment that removes every contamination problem above: a 4h25m window
(`2026-08-10 10:02:35Z -> 14:27:34Z`) that was **strictly laptop, strictly `iggy2london@gmail.com` (`sub-b`), zero AO**,
across which the weekly meter moved **57% -> 64% = 7%**. Actual money spent is therefore `0.07 x $45.16 = $3.16`.

Measured from the laptop's own transcripts (tabs 1-4 + subagents), deduped by `requestId`:

| model           | turns |    cache read |    output | documented cost |
| --------------- | ----: | ------------: | --------: | --------------: |
| claude-opus-5   | 1,998 |   745,335,541 | 1,617,949 |         $459.02 |
| claude-sonnet-5 | 1,125 |   522,080,577 |   788,135 |         $137.82 |
| **total**       | 3,123 | 1,267,416,118 | 2,406,084 |     **$598.71** |

**Multiplier = $598.71 / $3.16 = ~190x at August promo rates (~212x at standard).** Against 15-32x from the contaminated
AO-side attempts and 6-10x published — confirming the AO figures were understated exactly as the contamination analysis
predicted.

Notes that make this the reference measurement:

- **Opus dominates cost, not turn count**: 77% of documented value off 64% of turns ($5/$25 vs Sonnet-5's promo $2/$10),
  and Opus cache reads alone are $373. Model mix, not volume, drives equivalent value — a Sonnet-only window would value
  at roughly a third.
- **Compaction replay is real and large**: 3,270 replay lines were skipped against 3,123 genuinely billed turns — over
  half of transcript lines re-write already-billed calls. Deduping on `requestId` (stable across replay) is what makes
  the number trustworthy; naive counting roughly doubles it. Same mis-measurement class the pre-compact trigger hit.
- AO touched `sub-b` only twice inside the window, both known mislabeled-telemetry rows (`deepseek-v4-pro` /
  `<synthetic>` model strings), worth at most ~$37 — immaterial.
- **Caveats**: 57->64 is integer-rounded, so the true delta is 6.5-7.5% and the range ~176-204x; and if heavy Opus use
  draws on a scoped `seven_day_opus` bucket rather than `weekly_all`, the 7% understates consumption and would pull the
  multiplier DOWN — the one open risk, already tracked as the per-model quota-weight todo.

### 2026-08-10 — Cost structure: cache reads are 80% of the bill, and 90% of calls are un-batched

Decomposition of the controlled window's $598.71 by token class, and where the reducible waste is.

| class                   |    cost | share |
| ----------------------- | ------: | ----: |
| cache read              | $477.09 | 79.7% |
| cache write             |    ~$73 | 12.2% |
| output (incl. thinking) |  $48.33 |  8.1% |
| input (uncached)        |  ~$0.04 |   ~0% |

**Cache reads dominate four-to-one.** Mean cache read per API call is **405,833 tokens**, and within-session context
growth is only **1.37x** (344k -> 471k first-vs-last quartile), so compaction is working and cost is **linear in CALL
COUNT at a ~406k constant**, not quadratic in context. Every call re-reads the full prefix regardless of how small its
work is.

**89.9% of API calls make exactly one tool call; only 4.0% batch 2+.** Because cost is linear in calls, merging X% of
calls saves X% of cache reads: 25% -> 317M tokens, 50% -> 634M tokens (~$239, ~40% of the total bill, i.e. roughly
double the work per weekly quota window). Independent tool calls (multiple reads, parallel greps) batch at zero quality
cost; genuinely dependent ones cannot. The second, equally linear lever is resident context size itself.

**Thinking is 68.8% of output tokens** (Opus 66.9%, Sonnet 72.8%) but only ~$33 of $599 — **5.5% of cost**. Thinking
depth is not the spend lever; cache reads are.

**Method correction**: an earlier pass reported 89% thinking and claimed 71% of turns made no tool call. Both were
artifacts of deduping transcript lines by `requestId` and keeping only the FIRST line — Claude Code writes one JSONL
line per content block, all sharing a requestId, so `tool_use`/`thinking` blocks logged on later lines were dropped.
Token totals were unaffected (usage is per API call and was correctly counted once); only the content statistics were
wrong. Content must be UNIONED across all lines sharing a requestId.

### 2026-08-10 — RETRACTION: the laptop switches accounts, so no account is certifiably clean

Operator correction: "we literally switched accounts today and we switch often." Investigated every account-history
source on the laptop. Findings:

- **Only three login observations survive on disk, showing TWO different accounts**: `2026-08-02 23:41` =
  `ikenna@odum-research.com` (**`sub-c-ikenna-odum`**, from a stale `.claude.json.tmp` file), and `2026-08-10 12:36` +
  `14:32` = `iggy2london@gmail.com` (`sub-b`). So `sub-c` — named a clean calibration subject hours earlier — was itself
  a laptop login inside the same month.
- **No switch history exists anywhere**: `~/.claude/telemetry` carries no account-bearing fields,
  `~/.claude/session-env` is empty, `~/.claude/backups` spans only today, and local transcripts have no account
  identifier. The timeline is unrecoverable.
- **The "sub-d is doubly clean" inference was also wrong.** `~/.claude-accounts/*.env` files serve HEADLESS AO slot
  spawns; interactive login goes through `claude /login` and requires no env file, so their absence says nothing about
  interactive use.

**Consequence**: no account can currently be certified laptop-free, and every per-account multiplier is a LOWER BOUND of
unknown tightness. The useful invariant is directional — laptop contamination only ever removes tokens from the
numerator, never adds them — so contamination biases the multiplier DOWN and `max(measured)` is the closest to truth.
That yields a defensible fleet floor today of **>= 32.2x at August 2026 promo rates for max20**, still far above the
published 6-10x band. Fixed by todo 3 (start logging login identity now — same "cannot recover the past" property as the
meter sampler) and todo 6 (report lower bounds and a max, never an average).

**Incidental findings**: every cache write on this fleet is 1h TTL (`ephemeral_5m_input_tokens` = 0 across 17,446+
sampled turns), so only the 2.0x cache-write tier matters; cache-read volume is enormous (5.2B tokens on `sub-c` in one
week), which is what pushes measured value so far above the published band — nearly free on a subscription, expensive at
list rates. A bare `sonnet` model alias appears on 68 turns and would keep poisoning rows even after the canonical model
ids are registered.

## Progress Log

- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:6ceab83d2ca79e5c]: ARCHIVE — zero todos ever tracked; pure Progress-Log-history extraction, doc's own banner states its full scope is backup detail only. Archived per the 6-step ritual to plans/archive/2026_08/ (status: complete, nature: record) per task_template.md's own Finding-J convention.
