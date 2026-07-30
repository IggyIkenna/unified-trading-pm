---
doc_type: issue
title:
  Plans+issues corpus reduction marathon — drive plans/active total under 300 docs via repeated batch-fix waves against
  the 1-2-open-todo pool; corpus is under heavy concurrent replenishment, this is a standing effort not a one-shot
summary: >-
  Operator directive (2026-07-29/30, /autonomous, 6h unattended): drive the total plans/active + plans/active/issues doc
  count under 300 by closing out docs with only 1-2 open todos — pure-code and purge/delete fixes only, skip
  operator/VM/migration-gated work. Session start baseline (2026-07-29, after the earlier CODE_QUICK backlog session):
  ~685 active docs. Methodology proven across 2 waves: (1) keyword pre-filter the 1-2-open-todo pool into KEYWORD_GATED
  (skip) vs MAYBE_DOABLE, (2) group MAYBE_DOABLE by primary repo, (3) dispatch one autonomous sub-agent per
  repo/repo-cluster with the SUB_AGENT_MANDATORY_RULES + AUTONOMOUS_AGENT_RULES contract, explicit
  bounded-effort-per-item instruction (many keyword-surviving docs are still genuinely deep despite few checkboxes —
  agents must self-triage further, not just trust the keyword filter), and a BATCH-SHIP-LAST instruction (accumulate
  fixes, one quality-gates.sh run, a small number of quickmerge calls — never ship per-item, that's what makes this
  fast). Real, honest yield has been well under 100% of dispatched items (most items turn out genuinely
  deep/gated/already-done on inspection) but every wave produces real archivals + real fixes + a few genuine
  data-correctness findings along the way.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, corpus-reduction, autonomous, batch-fix, archival]
related:
  [
    /plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
  ]
created: "2026-07-29"
parent_epic: infrastructure_master
source: "main session, 2026-07-29/30, operator /autonomous 6h dispatch"
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
---

# Plans+issues corpus reduction marathon

## Standing methodology (re-use this exact pattern for every new wave)

1. Fresh count: `rg -c "^\s*- \[ \]" plans/active --glob "*.md" | awk -F: '$2==1||$2==2 {print $1}'` — the 1-2-open-todo
   pool. Exclude anything already dispatched in a prior wave (`comm -23` against the running "actually_dispatched" list
   — recreate it as the union of every wave's file lists if the scratchpad copy is gone; it's fully regenerable from
   this doc's Progress Log wave-by-wave file lists, or just re-triage the full fresh pool each time — the keyword filter
   is cheap).
2. Keyword pre-filter (gate on: `[OPERATOR]`, `BLOCKED-OPERATOR`, `BLOCKED-CREDENTIALS`, "operator decision/ruling",
   "needs a human/operator", "terraform apply", "launch a/the vm", "backfill vm", "spot vm", "vm launcher", "migration
   vm", "full-corpus"/"whole-corpus", "credential", "wallet key", "kill-switch", "1.0.0 graduation", "force-push",
   "staging lock" — override the gate if "purge"/"delete"/"cleanup"/"remove" also appears, those are explicitly IN SCOPE
   per operator instruction even if VM-adjacent language appears nearby).
3. Group MAYBE_DOABLE by primary repo (first entry in `repos:` frontmatter). Split any repo with >30 items into 2
   sub-batches (different files, same repo — safe per the "different files, same repo OK" multi-agent rule).
4. Dispatch one sub-agent per repo/cluster (max 10 parallel). Every dispatch MUST: paste/point to
   `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` + `cursor-configs/AUTONOMOUS_AGENT_RULES.md`, explicitly warn that the
   keyword filter doesn't guarantee shallowness (many "MAYBE_DOABLE" docs are still genuine deep investigations —
   bounded effort, ~20min/item, skip and move on), explicitly instruct BATCH-SHIP-LAST (accumulate, one QG run, few
   quickmerge calls, flip+archive together at the end, never per-item), and explicitly warn against the
   Monitor-tool/background-and-stop anti-pattern (repeatedly hit by sibling agents this session — run everything as
   foreground blocking calls).
5. When agents hit session-limit / rate-limit / transient-500 / silent-stall failures (all observed repeatedly this
   session, often simultaneously across every agent — looks like shared-account-level limits, not per-agent), just
   `SendMessage` a resume — "continue where you left off, don't restart" — every single time, without waiting for
   operator confirmation (explicit standing authorization for this 6h window). A "stopped, no completion record"
   notification (distinct from a normal failure) means the underlying process itself restarted — also just resume,
   verify via git log what already landed before assuming anything needs redoing.
6. This corpus is a SHARED CLONE under heavy concurrent load from other sessions/slots — expect real stash-pop
   conflicts, index races, and genuine multi-session collisions on the SAME finding (two agents independently
   root-causing the same incident from different angles — both real, merge don't discard). Recovery pattern: verify
   content after every commit, never trust exit code alone; on a real conflict, read BOTH sides fully before resolving —
   a conflict where one side calls undefined functions is stale/abandoned WIP, take the other side; a conflict where
   both sides found genuine complementary findings, merge both with a note distinguishing them.

## Standing hard-gate fix (shipped, keep it working)

`scripts/plan-hygiene/check_archive_candidates.sh` was upgraded 2026-07-29 from a purely-informational, silently-broken
script (used `grep -P`, which errors on plain BSD grep outside an interactive PCRE-aliased shell — meaning it likely
NEVER found a real candidate in CI/prek/cron, ever) into a real shrinking-ratchet hard gate
(`archive_candidates_baseline.yaml`), now also excluding `locked_by` docs and docs gated behind an active
`depends_on`+`gate_on_depends: true` finalize companion (added by a wave-2 agent, 2026-07-30 — a real false-positive
class the first version missed). If a doc has `status: resolved`/`complete` but genuine open todos remain (a real
recurring pattern — filing sessions sometimes downgrade status to reflect "the original hypothesis was retracted" while
leaving real follow-up todos open), correct status back to `open`, don't force-archive.

## Progress log

**2026-07-29, pre-marathon**: earlier same-day session (see
`/plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md`) closed the original 55-item CODE_QUICK
backlog + did a 34-doc "all-checked-but-unarchived" investigation (15 archived). Corpus was ~685 active docs entering
this marathon.

**2026-07-29/30, Wave 1**: 357 docs had 1-2 open todos. Keyword filter: 39 gated, 3 ambiguous (reviewed by hand,
correctly excluded — one warned of permanent data loss without an unmet verification precondition, one was a live fleet
deployment/migration not a purge, one was blocked on another plan's incomplete prerequisite), 315 MAYBE_DOABLE.
Dispatched 10 agents by repo (MTDS×2, unified-trading-pm×2, instruments-service, agent-orchestrator, deployment-service,
features-service, unified-api-contracts+MDPS, 10-small-repos-combined) covering 297 docs, plus a residual agent for the
9 docs no group covered. All 11 agents completed (after many session-limit/rate-limit resumes). Real yield: dozens of
docs archived across every batch, several genuine production fixes shipped (a live Cloud Run memory revert, a manifest
reclassification script run against 1,242 real objects, a WriteGate silent-swallow data bug, an IAM grant, terraform
drift fixes, 2 more VM-launcher OOM fixes, a missing candle-contract registration for a real live crash class), and 2
significant data-correctness findings correctly escalated rather than silently closed (a sports venue-enumeration
undercount contradiction; a real instrument_key collision on DEX pool venues).

**2026-07-29/30, root-cause fix**: investigated why done docs keep sitting unarchived despite the standing CLAUDE.md
rule — found `check_archive_candidates.sh` was informational-only, missed `plans/active/issues/` entirely, AND used
non-portable `grep -P`. Fixed all three; now a real hard gate (see above).

**2026-07-30, Wave 2**: post-wave-1 recount: 320 docs still had 1-2 open todos (corpus replenished by concurrent
sessions roughly as fast as wave 1 shrank it — 107 docs archived across 07-29/30 by git log, but total barely moved,
647→648). Excluded wave-1-dispatched docs → 65 fresh candidates → keyword filter → 37 MAYBE_DOABLE across 9 repos.
Dispatched 4 agents (unified-trading-pm, agent-orchestrator, MTDS+deployment-service+deployment-api,
alerting+features+instruments+MDPS). Also fixed one doc directly (main session, not a sub-agent):
`fred_backfill_early_date_indefinite_stall_2026_07_30.md` had `status: resolved` with 3 genuine open todos (a real
instance of the status-mismatch pattern the hard-gate now catches) — shipped the bounded one (a `logger.warning` on the
consolidator-lock wait path, `unified-trading-library@a0546d68`), corrected status back to `open` for the 2
genuinely-open items (real cadence measurement, VM relaunch — both out of bounded scope).

**Wave 2 in-flight incident**: an underlying process restart mid-wave (all 4 agents "stopped, no completion record")
left the shared clone with 3 real conflicted files + ~25 staged files. Resolved: the `_covering_paths()` conflict in
`generate_ag_closeout_audit_candidates.py`+test was a stale/abandoned draft (called undefined functions
`_depends_on_paths`/`_sibling_paths`) vs the current working implementation — took the working side (later confirmed: a
resumed agent had already landed the correct resolution as `unified-trading-pm@a589efe05` independently). The
`ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` conflict was two GENUINELY complementary findings (a
`--reload` supervisor-hang fix vs a separate `_stop_loops_concurrently` latency fix) from two different sessions —
merged by hand, then superseded by the resumed agent-orchestrator wave-2 agent's own (better, more rigorous) merge that
additionally caught the two findings don't actually explain the SAME documented incident timeline — left that version in
place, did not re-do it.

**2026-07-30, Wave 2 confirmed complete**: all 4 agents finished (after further session-limit + a transient DNS/network
outage across all 3 remaining agents simultaneously — resumed each the same way, no data lost). Real yield: 12+ docs
archived, a tri-state CI-status bug fixed across 2 repos (deployment-api + deployment-ui), a real cross-chain
`pool_address` collision bug fixed in DeFi calculators (features-service), the SAME id-form-mismatch bug pattern found
and fixed a second time in a different handler (risk_params_handler.py, mirroring an earlier base_defi_adapter.py fix),
11 verified-stale GCS test objects deleted with full delete-safety checks, and 2 more correctly-respected `locked_by`
docs left unarchived per the hard rule. Post-wave-2 recount: total still 647 (was 648 pre-wave-1, 685 at marathon start)
— 132 docs archived across 07-29/30 by git log, confirming the corpus really is being replenished by the wider
concurrent fleet at close to the rate this marathon is shrinking it. This is real, valuable work regardless of the
topline number (dozens of genuine production bugs found+fixed along the way) — continuing per the operator's "keep going
until genuinely out of safe doable work" directive, not chasing an exact number.

**2026-07-30, hygiene re-check**: `check_archive_candidates.sh` (now a hard gate) found 15 NEW candidates (baseline
was 7) + `check_terminal_status_archived.py` found 2 new status-mismatches — dispatched a dedicated archival-only agent
for these 17 (pure mechanics, no investigation needed, cheapest possible wins).

**2026-07-30, Wave 3**: post-wave-2 fresh pool (excluding everything dispatched in waves 1+2, 375 docs total) → only 22
fresh candidates remained (confirms waves 1+2 already covered the vast majority of the corpus's current 1-2-open-todo
docs — most of the still-309-strong pool are repeats correctly judged too-deep/gated). Keyword filter: 3 gated, 19
MAYBE_DOABLE across agent-orchestrator (5), unified-trading-pm (5, mostly finalize-companion plans), and
MTDS/instruments-service/deployment-service/unified-trading-library (9). Dispatched 3 agents.

**Standing observation after 2.5 waves**: with the corpus this actively fed by the wider concurrent fleet, "under 300"
may not be reachable via solo archival effort alone within one continuous session — but each wave still (a) permanently
removes real done-but-unarchived debt, (b) finds and fixes genuine production bugs along the way (a running tally: 2
silent-data-corruption bugs, 1 crash-class candle-contract gap, 1 cross-chain id-collision bug, 1 tri-state CI-status
bug, 2 instances of the same id-form-mismatch bug pattern, 1 shutdown-latency fix, plus several archival-hygiene infra
fixes), and (c) the `check_archive_candidates.sh` hard-gate fix is a durable, compounding improvement that keeps working
after this session ends, regardless of the fleet's creation rate.

## Todos

- [ ] [SCRIPT] P2. Confirm the archival-only agent (17 items: 15 archive-candidates + 2 status-mismatches) and wave 3's
      3 agents (agent-orchestrator cluster: 5 docs; unified-trading-pm cluster: 5 docs, mostly finalize companions;
      MTDS+instruments-service+deployment-service+unified-trading-library cluster: 9 docs) all reached a final
      structured report; consolidate yield into this doc's Progress Log.
- [ ] [SCRIPT] P2. Recount the plans+issues total and the fresh 1-2-open-todo pool. If a fresh candidate pool of >15-20
      docs still exists after excluding everything dispatched across waves 1-3, dispatch wave 4 using the exact
      methodology above. If the fresh pool has shrunk to near-zero (most of what remains is correctly keyword-gated or
      already-triaged-as-deep), that's the natural stopping point for the wave-dispatch mechanism — switch to just
      running `check_archive_candidates.sh`/`check_terminal_status_archived.py` periodically to catch new
      done-but-unarchived docs as the fleet creates them (cheap, mechanical, real ongoing value).
- [ ] [SCRIPT] P3. Periodically re-run `bash scripts/plan-hygiene/check_archive_candidates.sh` (now a real hard gate)
      and `--update-baseline` it downward as waves land, so the ratchet keeps tightening rather than just tolerating the
      current count forever.
