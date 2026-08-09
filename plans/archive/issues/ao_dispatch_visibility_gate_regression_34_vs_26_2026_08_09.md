---
doc_type: issue
title:
  ao-dispatch-visibility gate regressed 26→34 accidental exclusions fleet-wide — blocks every quickmerge, not caused by
  any single owned edit
summary: >-
  `check_ao_dispatch_visibility_gate.py`'s corpus-wide ratchet (disk-vs-backlog todo delta) jumped from its baseline of
  26 accidental (undeclared) exclusions to 34 sometime between 2026-08-09T00:48Z (last confirmed green, my own
  successful quickmerge push at that time) and 2026-08-09T01:1x-ish (first observed red, this doc's filing). The gate is
  corpus-wide and unconditional (runs on every quickmerge regardless of --files scope), so it currently blocks ANY
  slot's ability to ship anything via quickmerge. Confirmed via `git stash` that my own 3 staged files (an unrelated
  archival) contribute ZERO new exclusions — the 8 newly-crossed docs span cefi/ci/defi/infra/sports/prediction/issues
  tranches I don't own, each with its own `[TAG] P<n>.` todo line the parser reads as "excluded" (a BLOCKED-*/DEFERRED-
  BY-DESIGN/stretch-shaped sentence not carrying the actual declared marker token at the start of its own line).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch-visibility, ratchet-regression, ci-cd, blocking, quickmerge]
related: [/plans/archive/issues/ao_dispatch_visibility_gate_regression_sports_blocked_upstream_marker_2026_08_08.md]
created: 2026-08-09
parent_epic: infrastructure_master
source: cicd-worker-slot30, discovered while shipping unrelated promote_ref_orphaned_on_manual_pr_close archival
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: ikennaigboaka [slot-17], unified-trading-pm@64dcc4074
context_scope:
  [
    /scripts/quality_gates/check_ao_dispatch_visibility_gate.py,
    /scripts/quality_gates/ao_dispatch_visibility_baseline.yaml,
  ]
---

> **🟢 ARCHIVED 2026-08-09** — `status: resolved` with all 9 todos `[x]`; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. All 8 per-tranche remediation todos landed (mostly self-resolved by concurrent fleet commits
> ahead of pickup) and the final P3 baseline-ratchet todo shipped `unified-trading-pm@64dcc4074`
> (`max_accidental_exclusions` 28→0, `max_zero_dispatchable_docs` 25→9). See Progress Log below.

# ao-dispatch-visibility gate regression blocks fleet-wide shipping

## Evidence

- Baseline (`ao_dispatch_visibility_baseline.yaml`): 26 accidental exclusions tolerated.
- Live measured (2026-08-09, `python3 scripts/quality_gates/check_ao_dispatch_visibility_gate.py --json`):
  `{"docs": 241, "accidental_exclusions": 34, "declared_exclusions": 12, "zero_dispatchable_docs": 26}` — 34 > 26.
- **Not caused by my own change**: `git stash push -u -- <my 3 files>` then re-running the gate on the resulting
  clean-HEAD tree reproduced the SAME failure — confirming this is pre-existing on `origin/live-defi-rollout` HEAD
  (fetched, 0 behind at time of check), not introduced by anything I staged.
- **Recently regressed, not long-standing**: my own quickmerge push ~15-20 min earlier (commit `9013b7b5a`, the
  codex-doc-freshness fix) ran this exact gate and it printed
  `✅ AO dispatch-visibility gate passed (at-or-below baseline)` — so the corpus crossed from ≤26 to 34 in that short
  window, almost certainly from other slots' concurrent plan-doc commits landing on the shared `live-defi-rollout`
  branch.
- **34 newly/currently-accidental docs span every tranche** (spot-checked via `--json` output): cefi (2), ci (3),
  cross-cutting (2), defi (2), infra (3), prediction (1), sports (6), plus several `issues/` docs (canonical-path,
  capability-wizard, credential-checker, deployment-scripts, deribit, e2e-defi, sports×4, vm-billing) — genuinely
  fleet-wide, not one tranche's fault, not one owner's fix.

## Impact

**Was blocking, now unblocked.** Unlike most of this session's other ratchets, this one is NOT scoped to staged files —
it re-measures the full 241-doc corpus on every quickmerge run regardless of `--files`. A prior commit
(`unified-trading-pm@6ec2599`, 2026-08-09T01:20:18Z — the same commit that filed this issue doc) already re-baselined
`max_accidental_exclusions`/`max_zero_dispatchable_docs` to 34/26, so the gate has been GREEN (exit 0) since then. The
remaining 34 accidental exclusions are real backlog debt (see Investigation findings below), not an active blocker.

## Investigation findings (2026-08-09, cicd-worker slot 4)

**Verdict: case (a) — real drift, stable, NOT case (b) a spreading parser bug.**

- **Root cause of the 26→34 jump**: two agent-orchestrator commits landed on `live-defi-rollout` in the same ~30-min
  window as this issue's filing: `a0eb343` (2026-08-08T23:54:40Z, fixes the sibling doc's `[TAG][BLOCKED-<token>]`
  no-space-combo false-accidental bug) and `03e1809` (2026-08-09T00:52:17Z, **tightens** `_is_declared` to require the
  marker open the checkbox line itself — a marker at the head of a _continuation_ line no longer counts as declared,
  because measurement showed 7/9 continuation-line "declarations" were prose soft-wraps landing mid-sentence, 2 of which
  were stale resolution notes). The tightening commit landed BEFORE the 01:20:18Z re-baseline, so 34 is the correct
  post-tightening count, not a moving target — confirmed stable: a fresh `origin/live-defi-rollout` pull + re-run (this
  session) measures the exact same `34 accidental / 26 zero-dispatchable`, matching the baseline exactly with zero drift
  despite ~40+ min of concurrent fleet commits in between.
- **Spot-checked 3 of the 30 newly-flagged docs to confirm the exclusions are genuine, not a parser artifact**:
  - `cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12_finalize_2026_08_08.md` todo 1: the ONLY `BLOCKED-` text in
    the block is a quoted citation of _another_ doc's stale line
    (`"lighter Tardis entitlement (BLOCKED-CREDENTIALS, scaffold correct)"`) — the todo itself is active work ("flip the
    checkbox if not already `[x]`"), not blocked. A genuine accidental false-positive: `_is_non_dispatchable` scans the
    whole block for the token regardless of quoting context.
  - `ci_satellite_ao_dispatch_batch1_2026_07_26.md` todo: `BLOCKED-CREDENTIALS` appears only as a conditional
    instruction ("If the billing token is unavailable, record `BLOCKED-CREDENTIALS` rather than estimating") — same
    false-positive shape, not a live hold.
  - `infra_capture_and_devops_leftovers_2026_07_06.md` todo 1: a genuine `BLOCKED-PREREQUISITES` status IS present, but
    written mid-paragraph as a dated status update ("**STATUS 2026-07-07 06:31 UTC — BLOCKED-PREREQUISITES**...") deep
    in a long continuation block, not at the checkbox line's head — exactly the shape the 03e1809 tightening now
    correctly refuses to treat as declared. The block's own later text suggests the named prereqs have since landed, so
    this one likely also needs a content re-verify, not just a marker move.
- **Conclusion**: all three spot-checks are genuine per-doc authoring debt (either a false-positive substring match
  needing the todo rewritten to avoid quoting the token verbatim, or a real-but-mis-positioned marker needing either
  re-verification + removal or a move to the checkbox line's head) — exactly what the gate is designed to surface, not a
  parser regex gap. No further parser fix is warranted; case (b) is ruled out.

## Todos

- [x] ✅ [DEVOPS] P1. Investigate whether the 26→34 jump is (a) real drift needing individual doc fixes or (b) a
      parser/marker-vocabulary regression still spreading. — unified-trading-pm (docs-only). **Verdict: case (a),
      confirmed stable, gate already GREEN** — see "Investigation findings" above.
- [x] ✅ [DOCS] P2. Fix the 3 cefi-tranche accidental exclusions:
      `cefi_onchain_perp_batch_venue_allowlist_gap_2026_07_12_finalize_2026_08_08.md`,
      `cefi_satellite_ao_dispatch_batch10_2026_08_08.md`, `cefi_satellite_ao_dispatch_batch10_2026_08_08_finalize.md`.
      Per todo: either rewrite to avoid quoting a live-hold-marker token verbatim outside its own declared position (the
      false-positive shape — see "Investigation findings" above for the exact marker vocabulary this refers to;
      deliberately not respelled here, to avoid re-tripping this same gate on this very todo), or move a genuinely-live
      marker to open the checkbox line. Re-run `check_ao_dispatch_visibility_gate.py --json` after each doc to confirm
      it drops off the flagged list. Repo: unified-trading-pm. **Done**: all 3 docs rewrote their quoted/mid-sentence
      marker references (none were genuinely-live blocks) to avoid the literal `BLOCKED-CREDENTIALS` /
      `BLOCKED-OPERATOR-DECISION` token outside a declared position; re-ran `dispatch_visibility_report` — all 3 dropped
      off the flagged list, `check_ao_dispatch_visibility_gate.py` confirms `accidental_exclusions` 34→30, gate exit 0.
- [x] ✅ [DOCS] P2. Fix the 4 ci-tranche accidental exclusions: `ci_satellite_ao_dispatch_batch1_2026_07_26.md`,
      `ci_satellite_ao_dispatch_batch4_2026_07_31.md`, `ci_satellite_ao_dispatch_batch5_2026_08_02.md` (1 each),
      `ci_satellite_ao_dispatch_batch6_2026_08_08.md` (2). Same remedy as above. Repo: unified-trading-pm. **Done**:
      batch1/batch4/batch5 rewrote their quoted/mid-sentence `BLOCKED-CREDENTIALS` conditional-instruction phrasing
      (none were genuinely-live blocks — same false-positive shape as the cefi fix) to a paraphrase that no longer
      spells the literal token; re-ran `dispatch_visibility_report` after each — all 3 dropped off the flagged list.
      `ci_satellite_ao_dispatch_batch6_2026_08_08.md` has ZERO open `- [ ]` todos on disk as of this session (all done)
      — its 2 flagged exclusions from the issue's original 2026-08-09 measurement are moot, already resolved by another
      slot before this todo was picked up; confirmed it does not appear in the current `--json` report at all (only its
      `_finalize` sibling does, cleanly declared/backlog-matched, 0 excluded).
      `check_ao_dispatch_visibility_gate.py     --json` before/after my 3 doc edits: `accidental_exclusions` 28→25 (gate
      exit 0 throughout — this axis churns with concurrent fleet commits per the script's own buffer note, so the
      absolute number moved further between measurements; the -3 delta from my edits is confirmed via the doc-level
      `excluded: []` check above).
- [x] ✅ [DOCS] P2. Fix the 2 cross_cutting-tranche accidental exclusions:
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`,
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`. Same remedy as above. Repo: unified-trading-pm.
      **Done**: batch1's `data_completion_to_100_all_ag_2026_06_21.md` residual todo paraphrased its 3
      `BLOCKED-CREDENTIALS` mid-sentence mentions (describing OTHER docs' status, not this todo's own — same
      false-positive shape as cefi/ci) to "status: awaiting credentials" phrasing; batch1b's
      `mvp_scope_catalogue_tagging_2026_06_08.md` residual todo paraphrased its 2 stale `BLOCKED-OPERATOR-DECISION`
      mentions (a resolved, already-corrected historical reference inside a "this clause is stale" retag note — the
      `_STALE_MARKER_*_RE` resolution-language guards don't recognize "was corrected"/"is stale" as resolution verbs, so
      both mentions still read as live) to "awaiting an operator decision" / "awaiting-operator-decision framing".
      Re-ran `check_ao_dispatch_visibility_gate.py --json`: both docs now show `excluded: []` (were 1 each);
      `accidental_exclusions` 25→23, gate exit 0.
- [x] ✅ [DOCS] P2. Fix the 2 defi-tranche accidental exclusions: `defi_satellite_ao_dispatch_batch6_2026_07_30.md`,
      `defi_satellite_ao_dispatch_batch9_2026_08_06_finalize.md`. Same remedy as above. Repo: unified-trading-pm.
      **Done**: both were the false-positive shape (a stale/quoted mid-sentence marker reference, neither todo itself
      genuinely blocked) — another slot landed the identical remedy on `origin/live-defi-rollout` concurrently; hit 2
      rounds of same-file merge conflicts reconciling this session's own duplicate edits against it, took the
      already-landed upstream wording both times ("previously operator-decision-gated classification" / "the 2
      conflict-parked operator-decision-gated items"). Also fixed an unrelated fabricated commit-SHA citation (two
      unresolvable rebased-away SHAs, real equivalents `413f5aad3`/`f8fcd10f1`) blocking the corpus-wide
      `plan-commit-sha-evidence` gate for everyone — that fix too was independently landed by another slot before this
      session's own commit reached origin, so the duplicate dropped out as empty during rebase. Re-ran
      `check_ao_dispatch_visibility_gate.py --json` on the final clean origin tip: `accidental_exclusions` is now 0
      fleet-wide (every tranche todo below has landed), gate exit 0.
- [x] ✅ [DOCS] P2. Fix the 3 infra-tranche accidental exclusions: `infra_capture_and_devops_leftovers_2026_07_06.md` (2
      — incl. the genuinely-live-but-mispositioned `BLOCKED-PREREQUISITES` status spot-checked above; re-verify whether
      the named prereqs have since landed before deciding declare-vs-remove),
      `infra_capture_and_devops_leftovers_finalize_2026_07_25.md`, `infra_satellite_ao_dispatch_batch1_2026_07_26.md`.
      Repo: unified-trading-pm. **Done**: diagnosed all 3 docs first
      (`infra_capture_and_devops_leftovers_2026_07_06.md`'s 2 markers were genuinely stale, not live —
      `BLOCKED-PREREQUISITES` from 2026-07-07 superseded by the 2026-07-25 confirmation both named prereqs landed; the
      `BLOCKED-OPERATOR-DECISION` mid-paragraph mentions superseded by the 2026-07-28 freeze-lift ruling + the
      2026-08-06 "RULED ... AUTHORIZED" note already in the same todos. The finalize sibling's
      `BLOCKED-OPERATOR-DECISION` mention was the same false-positive shape, quoting the parent's pre-2026-08-06 status.
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s `BLOCKED-PLAYWRIGHT` mention was an illustrative
      downstream-consequence example inside backticks, not a live hold on that todo) and paraphrased all 3 locally to
      drop the literal token, no content/decision change. On `git pull --rebase --autostash` before shipping, hit 3-way
      conflicts on all 3 plan docs — another slot had independently landed equivalent (same-shape, slightly different
      wording) fixes on origin first. Took origin's already-pushed version for all 3 (`git checkout HEAD -- <3 files>`
      post-rebase) rather than re-landing a duplicate — same intent, no need to race a second edit onto the same lines.
      Re-ran `check_ao_dispatch_visibility_gate.py --json` after reconciling: all 3 docs show `excluded: []`, gate exit
      0 (fleet-wide `accidental_exclusions` now measures 0).
- [x] ✅ [DOCS] P2. Fix the 1 prediction-tranche accidental exclusion (2 markers in the same doc):
      `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`. Same remedy as above. Repo: unified-trading-pm. **Done —
      already moot, resolved by another slot before this todo was picked up (2026-08-09).** Commit `84f363ff6`
      (`unified-trading-pm@84f363ff6`, "docs(plans): reclassify prek_stash_restore_race NA->planning" — an unrelated
      commit message, but its diff also carried this fix) had already rewritten both markers before this task
      dispatched: the Betfair back+lay todo's two `BLOCKED-CREDENTIALS` mid-paragraph mentions →
      "credential-blocked"/"credential-blocked at the time", and the Kalshi todo's `BLOCKED-OPERATOR-DECISION`
      mid-paragraph mention → "was operator-decision-gated as of 2026-07-31" — neither was a genuinely-live block (both
      resolved: the Betfair session-token gap cleared 2026-08-05 per that todo's own "RESOLVED" note, the Kalshi
      order-placement question RULED 2026-08-06). Confirmed via `check_ao_dispatch_visibility_gate.py --json`: this
      doc's only remaining `excluded` entry is the `[SCRIPT] P1. DEFERRED-BY-DESIGN.` Phase-5 todo, which is
      `declared: true` (marker opens its own checkbox line) — zero accidental exclusions in this doc; corpus-wide
      `accidental_exclusions` measures 0 (down from 34 at filing).
- [x] ✅ [DOCS] P2. Fix the 5 sports-tranche (non-issues) accidental exclusions:
      `sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md`,
      `sports_satellite_ao_dispatch_batch5_2026_07_26.md`, `sports_satellite_ao_dispatch_batch5_2026_07_26_finalize.md`.
      Same remedy as above. Repo: unified-trading-pm. **Done — moot, already resolved by fleet drift before pickup**:
      `check_ao_dispatch_visibility_gate.py --json` (fresh `origin/live-defi-rollout` pull, corpus now 281 docs)
      measures fleet-wide `accidental_exclusions: 0` — the gate's own summary. Confirmed at the doc level: all 3 named
      docs report `excluded: []` (0 flagged todos each) in the current report; `batch10_finalize` carries no
      `BLOCKED-`/`DEFERRED-BY-DESIGN` token at all, and `batch5`/`batch5_finalize` DO still contain several such tokens
      mid-continuation-block but none of them are currently mismatched against the backlog (disk_open == backlog_open
      for both), so no doc edit was needed — same "already fixed by another slot / corpus moved past it before this todo
      was picked up" shape as the `ci_satellite_ao_dispatch_batch6` finding above. No content change required.
- [x] ✅ [DOCS] P2. Fix the 10 `plans/active/issues/` accidental exclusions:
      `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`,
      ~~`ao_dispatch_visibility_gate_regression_sports_blocked_upstream_marker_2026_08_08.md`~~ (already resolved +
      archived 2026-08-09 — its flagged todo was its own "grep the corpus" todo, now `[x]`; archived docs drop out of
      this gate's scan entirely, see
      `/plans/archive/issues/ao_dispatch_visibility_gate_regression_sports_blocked_upstream_marker_2026_08_08.md`),
      `ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md`,
      `capability_wizard_analysis_findings_2026_06_11.md`,
      `credential_ask_orphan_checker_ping_format_stale_2026_07_27.md`,
      `deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`,
      `deribit_combo_perpetual_partition_move_2026_07_21.md`, `e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`,
      `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md`,
      `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` (1 each),
      `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` (2),
      `vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md`. Same remedy as above. Repo:
      unified-trading-pm. **Done — moot, already resolved by fleet drift before pickup (2026-08-09, cicd-worker
      slot 14)**: fresh `origin/live-defi-rollout` pull (corpus now 283 docs) +
      `check_ao_dispatch_visibility_gate.py     --json` measures fleet-wide `accidental_exclusions: 0`. Checked all 10
      named docs individually: 8 show `excluded: []` (no flagged todos at all);
      `capability_wizard_analysis_findings_2026_06_11.md` and `deribit_combo_perpetual_partition_move_2026_07_21.md`
      still carry `BLOCKED-` markers but both report `declared: true` (the marker opens its own checkbox line — a
      legitimate declared exclusion, not an accidental one). No doc content edit needed — same "self-resolved by
      concurrent fleet commits ahead of pickup" shape noted by every other tranche's fix in this doc's Progress Log.
- [x] ✅ [SCRIPT] P3. Once all 8 remediation todos above land (accidental_exclusions measures at/near 0 on a fresh
      pull), re-run `check_ao_dispatch_visibility_gate.py --update-baseline` to ratchet `max_accidental_exclusions` back
      down from 34 toward 0 — never leave the baseline sitting at absorbed debt once the debt is paid off. Repo:
      unified-trading-pm. **Done**: fresh measurement (after building the agent-orchestrator sibling `.venv` via
      `uv sync`, required for the gate's subprocess delegation to run for real instead of degrading to the no-op/skip
      path) showed `accidental_exclusions=0`, `zero_dispatchable_docs=9`, `ineffective_declarations=4` fleet-wide,
      confirmed stable across a re-measure on a fresh rebase. Ran `--update-baseline`: `max_accidental_exclusions` 28→0,
      `max_zero_dispatchable_docs` 25→9, `max_ineffective_declarations` unchanged at 4 (no warnings — a pure
      ratchet-down, not a raise). Gate re-verified GREEN with the new baseline — unified-trading-pm@64dcc4074. Hit two
      unrelated pre-existing fleet-wide QG blockers while shipping (both corpus-wide, unconditional re-scans that block
      Pass-1 QG regardless of `--files` scope, not caused by this change): (1) `check_cloudbuild_template_drift.py` red
      on `client-reporting-api` (count 3→4, an already-open repo-blocker `RB-b7866b60`) — fixed by forward-porting the
      template's already-updated `_RUN_INIMAGE_QG` guard into `client-reporting-api/cloudbuild.yaml`'s quality-gates
      step (client-reporting-api@9b28914, verified ancestor of origin), then resolved the repo-blocker myself since the
      root cause was fixed; (2) `check_evidence_backed_completion.py` sub-rule B red (23→24, filed
      `evidence_backed_completion_regression_24_vs_23_2026_08_09.md` + repo-blocker `RB-ca63ec01`, joined as a waiter —
      root-caused and resolved by another slot before I needed to fix it myself). Both blockers verified GREEN before
      this final ship.

## Progress Log

- **infra-worker slot 8, 2026-08-09**: fixed the infra-tranche todo (3 docs) — diagnosed + paraphrased all 3 stale/
  false-positive markers locally, then hit a rebase conflict on every one of them (another slot landed an equivalent fix
  on origin first); took origin's version rather than duplicate-race a second edit. Verified via
  `check_ao_dispatch_visibility_gate.py --json`: all 3 docs `excluded: []`, fleet-wide `accidental_exclusions` now 0.
- **cicd-worker slot 30, 2026-08-09**: filed while blocked shipping an unrelated archival (promote-ref-orphan issue
  resolution). Did not attempt to fix the 8+ individual docs myself — out of scope (spans tranches I don't own, not
  small/quick per the fix-vs-file-and-wait triage). Retrying my own blocked quickmerge periodically; will update this
  doc if/when it self-resolves (another slot's commit) or note if it needs to be escalated further.
- **cicd-worker slot 4, 2026-08-09**: investigation complete — see "Investigation findings" above. Confirmed case (a),
  gate already GREEN via the pre-existing 6ec2599 re-baseline, no fleet-wide blocking remains. Filed the actual
  per-tranche remediation as tracked todos below (mechanical/judgment doc fixes, out of scope for this 1h investigate
  task) rather than fixing all 34 inline. Todo 1 (this investigation) flipped done.
- **cicd-worker slot 16, 2026-08-09**: picked up the sports-tranche (non-issues) remediation todo. Fresh-pulled
  `origin/live-defi-rollout` (corpus now 281 docs, up from 241 at filing) and re-ran
  `check_ao_dispatch_visibility_gate.py --json`: fleet-wide `accidental_exclusions` already reads 0 — the whole
  regression has self-resolved via concurrent fleet commits (other slots' doc fixes + corpus churn) ahead of this todo
  being picked up. Confirmed at doc level: all 3 named sports docs show `excluded: []`. No content edit needed; flipped
  the checkbox done with the finding recorded inline. Note for whichever slot picks up the remaining
  defi/infra/prediction/`issues/`-tranche todos below: the same fleet-wide-0 state likely means those are ALSO moot by
  now — worth a fresh `--json` re-check before doing any manual doc surgery, rather than assuming the original
  per-tranche breakdown from filing time still holds.
- **cicd-worker slot 15, 2026-08-09**: picked up the prediction-tranche todo
  (`prediction_satellite_ao_dispatch_batch6_2026_07_29.md`). Found it already moot — `unified-trading-pm@84f363ff6` (an
  unrelated-titled commit, "reclassify prek_stash_restore_race NA->planning") had already rewritten both flagged markers
  before this task dispatched. Verified live via `check_ao_dispatch_visibility_gate.py --json`: corpus-wide
  `accidental_exclusions` is now 0 (down from 34 at filing); this doc's only excluded todo is `declared: true`. No new
  doc edit needed for the marker fix itself — flipped this todo's checkbox citing the evidence.
- **cicd-worker slot 14, 2026-08-09**: picked up the `plans/active/issues/` tranche todo (10 named docs). Same
  self-resolved shape as every prior tranche: fresh pull (corpus now 283 docs) +
  `check_ao_dispatch_visibility_gate.py --json` measures fleet-wide `accidental_exclusions: 0`. Per-doc check confirmed
  all 10 named docs are clean — 8 with zero flagged todos, 2 (`capability_wizard_analysis_findings_2026_06_11.md`,
  `deribit_combo_perpetual_partition_move_2026_07_21.md`) with `declared: true` markers (legitimate, not accidental). No
  content edit needed; flipped the checkbox. **All 8 per-tranche remediation todos are now done.** The remaining P3 todo
  (re-run `--update-baseline`) is separate scope — the current baseline (`max_accidental_exclusions: 28`, already
  ratcheted down from 34 by an earlier slot) still tolerates well above the live-measured 0, so the gate stays green
  regardless; leaving the baseline ratchet-down itself for whichever slot picks up that todo.
- **cicd-worker slot 17, 2026-08-09**: picked up the final P3 todo. Built the agent-orchestrator sibling `.venv`
  (`uv sync`) so the gate could run for real (was degrading to a no-op skip without it); measured
  `accidental_exclusions=0` fleet-wide, ran `--update-baseline` (`max_accidental_exclusions` 28→0,
  `max_zero_dispatchable_docs` 25→9), shipped unified-trading-pm@64dcc4074. Along the way hit and cleared 2 unrelated
  pre-existing fleet-wide QG blockers (cloudbuild-template-drift on client-reporting-api; an evidence-backed-completion
  sub-rule B regression) — see the todo's own **Done** note for detail. **All 9 todos in this doc are now done; ready to
  archive.** `archive_exempt: true` set TEMPORARILY on this same commit (per
  `/codex/12-agent-workflow/commit-push-flip-rule.md`'s flip-then-mv ordering — never combine the checkbox flip with the
  `git mv` archival in one commit, since a path-scoped `git log -- <plan_ref>` on the OLD path can miss the transition
  once the same commit also moves the file) — the immediate next commit removes it, sets `status: resolved`, adds the
  archive banner, and does the `git mv` to `plans/archive/issues/`.
