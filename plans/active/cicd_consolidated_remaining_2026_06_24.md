---
title: "CI/CD — consolidated REMAINING work (single SSOT; supersedes the 7 prior cicd/dep-promotion/starvation plans)"
name: cicd_consolidated_remaining_2026_06_24
parent_epic: infrastructure_master
assigned_vm: harsh_pc
created: 2026-06-24
status: active
locked_by: live-defi-rollout
locked_since: 2026-06-24
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 26
estimate_calibrated_ai_days: 20.8 # +8 baseline (WS-L: LDR→main + version-registry fleet migration, infra ×0.8), 2026-06-25
supersedes:
  - cicd_promotion_pipeline_2026_06_18 (open items migrated here; done items + decision log preserved in source)
  - cicd_quality_gates_2026_06_18 (idem)
  - cicd_release_machinery_2026_06_18 (idem)
  - cicd_sit_and_fleet_2026_06_18 (idem)
  - cicd_docs_and_consolidation_2026_06_18 (fully DONE — pure supersede)
  - dependency_promotion_range_pins_and_major_bump_sit_2026_06_09 (remaining 7 items migrated here)
  - issues/staging_to_main_promotion_starvation_2026_06_19 (remaining items migrated here)
  - issues/staging_main_version_line_divergence_2026_06_22 (the version-line conflict class — resolved at the ROOT by
    D13 version-out-of-source / WS-L, 2026-06-25)
  - issues/staging_main_version_line_dual_lineage_2026_06_22 (idem — D13 / WS-L)
  - issues/version_line_autoresolve_pr_orphan_cleanup_2026_06_24 (the version-line autoresolve band-aid is obsoleted by
    D13 / WS-L)
source:
  - the 7 plans above (second-level consolidation; the first-level 2026-06-18 fold collapsed ~13 plans + 11 issues into
    5 themed plans, most of which are now done)
  - parallel rationale-extraction sweep 2026-06-24 (slot-2) — open items + decision context harvested verbatim from each
    source
---

# CI/CD — Consolidated Remaining Work

> **Why this plan exists.** CI/CD work was already consolidated once (2026-06-18: ~13 plans + 11 issues → 5 themed
> plans). Those themed plans are now mostly DONE, leaving ~100 open items scattered across 7 documents. This plan is the
> **single live SSOT for the REMAINING CI/CD work**; the 7 source plans are SUPERSEDED (their done items + full
> narrative stay readable in-source as the historical record). **Nothing below is new scope** — every item is migrated
> verbatim with its priority tag and a one-line provenance ref `(source)`.
>
> **The Decision Log (next section) is the irreplaceable part** — it preserves _why_ each architecture was chosen over
> the alternative, so a future agent picking up an item understands the prior reasoning rather than re-litigating it.

---

## Decision Log — preserved rationale (why A over B)

Read the relevant entry **before** touching an item in its workstream. These are the design decisions the source plans
established; they are SSOT here.

### D1 — LDR is the integration SSOT; staging/main are projections (LDR-trunk decoupling, live 2026-06-10)

`live-defi-rollout` is the continuous-integration axis + live accumulator. `quickmerge --agent --files` **lands code on
LDR and stops** for a service repo (no per-unit staging PR). The **Tier-C drain** (`ldr-to-staging-promote`, every 15
min) is the _sole_ path LDR→staging, and that drain PR's `quality-gates-v2` (head=LDR, base=staging) is the server gate
— **LDR itself never runs QG**. **Why over the old per-commit-staging-PR model:** direct pushes to staging piled up
behind main and jammed the flow (incident: pm-staging-to-main-bypass paralysis 2026-06-03). Decoupling promotion from
the trunk heartbeat removed that anti-pattern. Divergent promotion SHAs with **zero file-content delta** (`compare`
shows `ahead_by>0`, `files:[]`) are squash-count noise to collapse, not work to merge.

### D2 — ci_status moves to a Firestore SSOT (git-commit dual-write is being retired)

ci*status / staging_status are migrating off git commits into a Firestore side-store, in phases (Phase-2 overlay
`tier_c_promotion_gate.py` already consumes Firestore for promote-bot verdicts; Phases 3–4 remain — see WS-A). **Why
over keeping it in git:** concurrent git writes to `ci_status` collide with the heavy manifest-writer set → rebase
exhaustion + manifest-commit race amplification (verified via bug #11, 2026-06-23). Firestore decouples gate state from
git so the races disappear. **Note (premise-corrected 2026-06-23):** `quickmerge` reads ci_status/staging_status
directly from `workspace-manifest.json` as the \_offline-fallback cache* — that is correct-by-design; whether quickmerge
needs a further cutover is itself gated on Phases 3–4, not a bug.

### D3 — Breaking detection is CONTENT-based, not version-phase based

`is_breaking` (which locks staging + triggers the 30-min SIT) is the verdict of the AST public-surface differ
`detect_breaking_change.py`, NOT the version phase. A 0.x MINOR / docstring / reformat / internal refactor /
added-optional-kwarg / module-move is **NOT** breaking; a removed-or-renamed public export, incompatible signature,
removed/renamed/retyped schema field, or removed HTTP route **is**. **Why:** the old `git diff __init__.py | grep '^-'`
heuristic flagged any removed line → spurious cascade locks. `quality-gates-v2` still runs on EVERY staging PR; the
breaking gate only narrows the _SIT_, never QG.

### D4 — Range pins absorb minor/patch; only MAJOR forces a rebuild (dependency promotion, operator 2026-06-09)

Internal deps (UTL/UAC/`unified-*`) are range-pinned `>=0.x,<1.0.0` with editable path sources. A minor/patch bump stays
in-range → **NO consumer rebuild, NO CI noise** (consumer picks it up on its own next promote — pull, not push). A
**MAJOR** bump crosses `<1.0.0` → forces a re-pin → triggers a **cascade of QGs (full SIT in dep order)**; green →
auto-promote, no human; escalate to vm-planning ONLY IF the cascade fails. **Why over exact-pin-everywhere:** the lock
records external exact-pins for reproducibility while internal deps are _truly_ ranges, honored at install time — so a
minor internal bump doesn't fan out a fleet rebuild. The "honor ranges" gap was the **clone logic**, not the lockfile
(uv.lock is already correct: internal = `source={editable=…}`, external = exact) — and that clone loud-fail is already
live.

### D5 — Option A: keep current WORKING external deps (2026-06-18, operator Harsh)

A fleet `uv lock --upgrade` validation proved latest external deps are NOT all safe: 16/22 passed QG, 6 failed (3 real
fastapi/starlette breaks, 2 pre-existing QG blocks, 1 to investigate). **Decision:** ship current working locks under
`uv sync --frozen`, **cap** `fastapi<0.137`/`starlette<1.3.0` to prevent future pulls of breaking versions, and defer
one-by-one external upgrades. **Why `--frozen` not `--locked`:** both CI and local install the committed lock as-is (no
re-resolution → fast, deterministic, no surprise transitive deps); `--frozen` tolerates the semver-agent's CI-side
`version =` bump, whereas `--locked` hard-fails on it (a poison pill). A dep-floor / CVE-fix bump must regen + commit
`uv.lock` in the **same** commit, and lands on **LDR** (1.5a) so LDR→staging→main stay byte-identical projections.

### D6 — staging→main starvation was TWO upstream input bugs, not a missing promoter (2026-06-19)

The staging→main promoter (`staging-to-main.yml`) is healthy; it was _blind_ to ~20 repos because it derives its pending
set from manifest version maps (`staging_versions != versions`), not git divergence — and two bugs broke that signal:
**Mode A** (manifest version-bump desync: semver bumped pyproject but a failed `version-bump` dispatch never propagated
to `staging_versions` — affected UAC/UTL/instruments/execution/client-reporting-api); **Mode B** (squash fallback in
`ldr-to-staging-promote.yml` collapsed `feat:/fix:/feat!:` into a single `chore(promote)` → semver read `chore` → no
bump → frozen — affected ~15 repos). **Fixes:** Mode-B `_squash_subject()` now derives the aggregate conventional type
from the collapsed commits so the semver signal survives the fallback; the staging→main pending set now also includes a
**content-ahead probe** (tree-SHA equality) so non-bumping content drains too (verified live 2026-06-23). **Caveat:**
fixes do not retro-drain already-frozen backlog — repos self-heal on the next drain.

### D7 — Mode-B per-drain MINOR bumping is ACCEPTED (closed won't-change, 2026-06-21)

The Mode-B fix makes semver MINOR-bump on every Tier-C drain of feature content (~4 bumps/hr on active repos). An
alternative — compute the bump once at the staging→main boundary — was **rejected** because it reintroduces the Mode-B
starvation tension (chore→no-bump→frozen). 0.x versions are cheap and each drain carries real content, so high-velocity
bumping is fine. The bump-rate circuit breaker was hardened to page on genuine re-bump loops (`REBUMP_PAIRS ≥ 2`) rather
than raw count, so healthy climbing is allowed. **No code change — this is a recorded design decision.**

### D8 — Path-B per-slot reference-clones (tab-branch model retired 2026-06-08)

Each slot is a `git clone --reference` on `live-defi-rollout` with its own `.git`; no tab-branches, no `tab-mirror` sync
(deleted fleet-wide). Contention moved to LDR push-time (rebase-on-reject, handled by quickmerge STAGE 0.4). Commit
attribution lives in the git author NAME (`[slot-<N>·<host>]`), independent of branch. **Why:** the tab branch was only
ever a workaround for git's "can't check out the same branch twice in one clone"; separate clones drop the entire sync
tax. Residual tab-branch _code/docs/branches_ are dead and tracked for cleanup (WS-D, WS-F).

### D9 — Workflow sprawl folds (release machinery)

The ~51 live workflows trend DOWN via targeted folds where two workflows watch the same signal:
`sit-starvation-detector` is derived SIT state (fold into `sit-debounce-trigger`); `ci-status-reconciler` +
`ci-failure-watcher` both watch CI health (→ `ci-health.yml`); `main-backmerge` drift-tick + `promotion-lag-monitor`
both track branch hygiene; the paid-API agent workflows move to the VM orchestrator (GitHub Actions is billed per run,
the orchestrator is not). **Why:** fewer workflows = less drift surface + lower Actions spend; only fold where the
signal genuinely overlaps.

### D10 — Config SSOT lives in `pyproject.toml`, never shadowed on the CLI

Coverage reads `[tool.coverage.report] fail_under` from toml (the base does NOT pass `--cov-fail-under`, which shadowed
it); bandit reads `[tool.bandit]` via `-c pyproject.toml`. Change a repo's floor in **toml**, not the stub. Coverage
must `parallel=true`+combine fleet-wide (xdist `-n auto` reads controller-only partial data otherwise → masks true
coverage; rolled to 20 repos 2026-06-22). The commit (not the PR) is the per-repo quality boundary — a code commit must
come from a `quality-gates.sh`-green tree (sentinel `.qg_last_passed_sha`).

### D11 — Why the drain jams RECUR (root-cause diagnosis, 2026-06-24)

The repeating fleet jams (an AO agent clears one, another appears hours/days later) are **not N unrelated incidents —
they are one structural gap surfacing serially.** Mechanism, ground-verified 2026-06-24:

1. **LDR never runs QG** (D1) — the first quality-gate on the _integrated_ LDR tip is the **promote PR**
   (`ldr-to-staging`, head=LDR). Between promotes, code arrives via quickmerge (whose local sentinel is the agent's OWN
   pre-pull tree) or via the carve-out direct pushes (docs / dirty-dep / workflow) which run **no QG at all**.
2. **Ratchet checks are repo-wide COUNT-vs-baseline** (plan-discipline / doc-freshness / ruff-rule-ratchet …). Many
   agents each land a sub-baseline increment; the integrated tip crosses baseline, but **no single agent's pre-pull
   local run saw the full integrated count** → the regression accumulates undetected.
3. **The lint-codex slice short-circuits on first failure** — `base-*.sh` sets `set -e` (line 40) and PM
   `quality-gates.sh` runs each post-gate as a sequential `… || { exit 1; }` (lines 363/375/392/406…). So when several
   ratchets have regressed, the FIRST one exits and **masks the rest** → fix it, re-run, the next surfaces → a fresh
   "jam." N accumulated regressions = N serial jams (incident 2026-06-24: Ikenna worked **13** checks "each hidden
   behind the prior").
4. **Local↔CI scope divergence** (the `pm-script-path-ref` "55 local / PM-only-pass-in-CI" class) makes a local-green
   commit an unreliable predictor of the promote verdict.
5. **The promote PR is the sole fleet choke point** — one repo's red v2 jams the whole `LDR→staging` drain → fleet-wide
   "drain behind."

The fix is therefore NOT another per-incident patch — it is: (a) make the slice **report ALL failures in one run**
(kills the serial re-jam), (b) **detect ratchet drift on the integrated LDR tip at land-time** (catch + attribute before
the promote), (c) **close the carve-out QG bypass**, (d) drive **local↔CI scope parity** so green-local ⟹
green-promote. These are **WS-0** below.

### D12 — LDR→main direct promotion is the END-STATE for the squash-divergence class (extends D1; obsoletes the WS-B auto-collapse band-aid) — 2026-06-25

The recurring `staging→main` conflict walls (D11, WS-B) are STRUCTURAL, not incidental: `staging` and `main` are two
projections of the LDR trunk, and squash-merging one projection INTO the other invents a permanent stale-merge-base
(identical content, divergent commit graph) → a git conflict that never self-heals. WS-B's auto-collapse SPEC is the
per-conflict band-aid; the END-STATE is to stop merging projection→projection — **promote `main` DIRECTLY from
`live-defi-rollout` (PM's proven Option-B), retiring the `staging→main` squash step fleet-wide.** LDR is ALREADY the
backmerge sink (the `main-backmerge-to-ldr` drift-tick keeps LDR ⊇ main), so `LDR→main` is always a clean merge; the
only residual is content-identical squash-skew (`files=0`), which the existing tree-equality clear handles. `staging`
STAYS as the SIT/v2 sandbox (LDR→staging drain runs SIT); only the MERGE-to-main relocates to `LDR→main`, gated by v2
(always) + SIT-green (breaking, via the existing cascade). This DELETES the squash-divergence conflict class + the
conflict-fallback

- the auto-collapse band-aid + the bulk of the breaker churn, and leaves the conflict/escalation layer firing only on
  GENUINE content conflicts (real plan/codex/code overlaps at LDR push-time, handled as today). Every quality GATE is
  preserved (v2, SIT, semver, breaking-detection, image-off-main) — only the squash MACHINERY is removed → still
  Citadel-grade (fewer moving parts = fewer failure modes). LDR-entry integrity = quickmerge's local sentinel + the
  strict-quickmerge pre-push hook hardened to BLOCK (NOT server-side LDR branch protection, which would defeat the fast
  unprotected integration axis); `main`'s integrity = the `LDR→main` v2 gate alone (nothing reaches main without it).
  Migration: per-repo cutover flag + canary-first + reversible. SSOT: WS-L.

### D13 — Version-out-of-source: the `version =` label moves to a registry (the D2 ci_status→Firestore pattern, applied to the version field) — 2026-06-25

The `version =` bump is the single most FREQUENT change and the dominant remaining churn/conflict source (the
`staging_main_version_line_*` issue docs; WS-C). A version is METADATA; the commit SHA is the immutable identity —
embedding the label as a tracked `pyproject.toml` source line is what turns "tag this state" into a commit → a
stale-base version-line conflict → a dirty tree → an FF-pull → CI to line up repos. **Apply the D2 pattern (state leaves
git for a registry) to the version field:** make the package version DYNAMIC (resolved at build), canonical registry =
**git tags** (in-repo, build-safe, idempotent, already minted by the semver-agent + already Firestore-mirrored via
`reconcile_release_tags.py`, WS-H), with **Firestore** as the queryable registry the deployment-ui/rollback/tracing
already read. The semver-agent writes the version to the registry instead of committing pyproject; image
build/deploy/rollback resolve the human-readable version from the registry (keep `:latest`, add `:vX.Y.Z`). This
ELIMINATES the version-bump commit churn AND the version-line conflict class entirely (no version line in git = no
version conflict, ever), and largely dissolves the semver bump-rate breaker (no version commits to pile up). Caveats:
per-repo dynamic-versioning setup; internal-dep ranges are editable-path (minor/patch already no-rebuild — only MAJOR
matters, stays an explicit registry event); `assert_version_coherence` + the coherence gates repoint to the registry.
SSOT: WS-L. Supersedes the 3 `staging_main_version_line_*` issue docs.

### D14 — Execution model-tier split: default Sonnet, escalate to Opus-xhigh only for high-blast-radius/intricate execution, a WORKFLOW for breadth pre-audits + adversarial verify, Max for novel design (none open) (2026-06-25)

Cost-balance principle (operator 2026-06-25): use the CHEAPEST tier SUFFICIENT for the work — spend a higher tier ONLY
where its marginal capability is actually consumed. Mirrors the workspace model-tier-selection rule (Sonnet default,
Opus by deliberate escalation). For this plan:

- **Sonnet 4.6 (default, thinking: medium) — the BULK.** Mechanical / spec'd / low-judgment items: the migrated-verbatim
  WS-D parity tweaks, WS-F sprawl folds, WS-G drift-audit comment fixes, WS-I dep-floor bumps + doc repoints, the
  per-repo fleet ROLLOUTS (dynamic-versioning setup, the strict-quickmerge BLOCK flip), and the WS-L Phase-0 flag +
  canary-harness scaffolding. The architecture is decided (D1–D13) → no reasoning premium to pay.
- **Opus 4.x extra-high (xhigh) single-agent — escalate ONLY for high-blast-radius or intricate execution:** the WS-A
  destructive 208 (the ci-status-update writer-drop + the `staging-backmerge` fleet-template edit = rule-11;
  OPERATOR-greenlit), the WS-L Phase-2 semver-agent RETARGET implementation (many hooks, high blast radius), and the
  WS-B promotion-correctness items needing careful diagnosis. xhigh buys regression-avoiding care, NOT novel design.
- **A WORKFLOW (ultracode) — for breadth + adversarial verification:** the WS-L Phase-1 pre-audit "every `staging→main`
  consumer" + Phase-2 pre-audit "every semver-agent hook" (parallel finders + a skeptic "did we miss one?" — this IS the
  no-regression guarantee), and the Phase-2 retarget adversarial-verify (independent skeptics confirm no hook dropped /
  no coherence gate broken). Proven 2026-06-25: an analogous orchestrator `notify_*` audit found **31** contract
  violations vs the **1** suspected — breadth + skepticism is exactly where a workflow's cost is earned.
- **Max — reserved for a genuinely novel open design question; NONE is open** (D1–D13 cover the architecture). Do not
  reach for it on spec'd execution.

Reusable rule: novel-hard-design → Max; breadth / decompose / adversarial-verify-at-scale → workflow;
intricate-or-high-blast-radius spec'd execution → Opus-xhigh; everything else → Sonnet.

**Model-gate self-check (HARD RULE — at EVERY phase/workstream gate, not just task start).** Before starting a phase or
item, the executing agent MUST read its OWN running model + thinking-effort and compare it to the tier this section
assigns that work. ALIGNED → proceed. MISMATCHED — e.g. **Sonnet on an Opus-xhigh gate** (WS-A 208 / WS-L Phase-2 semver
retarget / a WS-B promotion-correctness item), or **Opus burning on a Sonnet-bulk item** — then the agent: (a) **SELF-
SWITCHES** the model if the runtime permits a self-switch (e.g. `/model`), then proceeds on the correct tier; ELSE (b)
**STOPS at the gate and signals the operator** to change the model before continuing. **NEVER cross a gate on a
mismatched model.** This extends the workspace task-start self-check
(`codex/06-coding-standards/model-tier-selection.md`) to a PER-GATE check, because this plan's phases deliberately span
tiers — so the correct model CHANGES between gates within a single execution, and an under-tier model on a
high-blast-radius gate (or an over-tier model wasting cost on the bulk) must be corrected AT the gate.

---

## Open work

> Priorities preserved from source. Each item carries its provenance `(source ▸ tag)`. Workstreams are independent
> unless a dependency is noted. **WS-J (AWS dual-cloud) + the AWS-VM half (WS-D item) are parked DEFERRED-AWS per
> operator 2026-06-24 — leave as-is until the AWS fleet reactivates.**

> **2026-06-24 verify-sweep (slot-2) — backlog triage.** A 6-agent read-only sweep + direct `gh`/code verification
> reclassified the open items against LIVE state (per the "some tasks may already be done / need changing" directive):
>
> - **DONE / pruned today (8):** the 3 ruleset repos (greeks / fund-admin / e2e — rulesets active + v2 GREEN), WS-H
>   Firestore write-through (`reconcile_release_tags.py`), WS-C `*/6h` registry-poller (`digest-drift-sweep.yml`), WS-C
>   stale propagation-template (absent) + stale codex `*/20` (already hourly), WS-G `conflict-resolution-agent`
>   duplicate-env (false alarm).
> - **~~#525-GATED~~ → GATE CLEARED 2026-06-24 (slot-2):** #525 (the PM LDR→main Option-B drain) **MERGED 11:59Z**, and
>   4 further PM drains merged since (#526–#529, PM main `quality-gates-v2` GREEN). The "cannot quickmerge while PM QG
>   is red" premise is **STALE** — PM QG is healthy and draining hourly, so most of WS-0 / A / B / C / D / F / G / H is
>   now **actionable via quickmerge**. (First two landed: BUG `hotfix-mode` + `rollout-action-ref` → PR #532, see WS-G.)
> - **ACTIONABLE-NOW (non-PM, independent of #525):** prune the 21 stale `tab/*` branches fleet-wide (WS-F —
>   **verified-stale 2026-06-24, awaiting prune-go**, see below), PYSEC-cleanup in 9 repos (WS-D),
>   `verify_service_token`→UTL-factory in 4 repos (WS-I), pip-floor bump (WS-I), deployment-ui Repos-CI render (WS-G,
>   UI-gated).
> - **LIKELY-DONE, needs confirm:** WS-B "batch breaking fan-out" (cascade has its OWN concurrency group — but that's
>   the eviction fix, not necessarily union-batching), WS-B "redundant empty staging→main PRs" (tree-equality
>   idempotency shipped). Left open pending a tighter check.

### WS-0 — Recurring-jam ROOT CAUSE (P0, NEW 2026-06-24) — see D11

> These are the items that actually stop the jams from RECURRING. The rest of the plan fixes individual failure modes;
> WS-0 fixes the structural reason regressions accumulate-undetected then surface serially at the sole promote gate.

- [x] ✅ [SCRIPT] P0. DONE 2026-06-24 (slot-2) — PM `quality-gates.sh` post-gates now ACCUMULATE-and-report: the 15
      ratchet/codex/governance gates collect into `POST_GATE_FAILURES` (via a `_post_gate_fail` helper) and the gate
      fails ONCE at the end with the full list, instead of the first `exit 1` short-circuiting and masking the rest.
      Each gate still prints its ❌ remedy inline. Scoped to the post-gate/ratchet phase (the `if/else`+`||` structure
      already neutralises `set -e` — NO global `set -e` removal, base-\*.sh untouched); structural pre-gates (manifest /
      strategy-manifest / locked-plan / scope-checker-presence) stay fail-fast. Failure path verified under
      `set -euo pipefail` (3 gates fail → all 3 reported, no serial masking); happy path QG-green + sentinel written.
      **unified-trading-pm@eef45653a** → LDR (drains to main via standing PR). (NEW root-cause 2026-06-24)
- [x] ✅ [WORKFLOW] P0. IMPLEMENTED 2026-06-25 (slot-2) — **this monitor already EXISTED** as `ldr-ci-monitor.yml` +
      `scripts/repo-management/ldr_ci_monitor.py` (it dispatches the authoritative `quality-gates-v2` — incl. the
      ratchet/lint-codex suite — against each repo's LDR tip + alerts on red-transitions; reusing the real gate, never a
      drift-prone bespoke check). The reason drift goes undetected (D11/D1): it was **`gh workflow disable`d 2026-06-11
      in the billing wall** (`github_actions_billing_wall_2026_06_11`) because it fired a fresh v2 for ALL ~24 repos
      EVERY hourly tick. **Fix = revive it, not rebuild**: (1) CONDITIONAL dispatch — skip a repo whose most-recent LDR
      dispatch already targeted the current tip (fail-safe: dispatch on any uncertainty → never miss a red);
      steady-state drops ~24/hr to a handful; (2) ATTRIBUTION — on a RED transition, name the introducing commit(s)
      between the last-green sha and the red tip (author + subject) so the page is actionable. Decision logic verified
      live (PM tip moved → DISPATCH; unchanged → SKIP); read+detect smoke-tested no-cost; ruff+QG-green.
      **unified-trading-pm@f50e52fd7** → LDR. **FINAL STEP — re-enable**
      (`gh workflow enable ldr-ci-monitor.yml -R IggyIkenna/unified-trading-pm`) is tracked as the sub-item below; it
      MUST wait until this driver reaches `main` (the workflow checks out + runs the `main` copy — re-enabling before it
      lands would run the OLD unconditional driver = billing wall again). (NEW root-cause 2026-06-24)
  - [x] ✅ [OPS] P0. DONE 2026-06-25 (slot-2) — driver confirmed on `main` (2× `current_ldr_sha`),
        `gh workflow enable ldr-ci-monitor.yml` → state `active`, and a verification `workflow_dispatch` run
        (28148309084) **PASSED on real infra**: scan step `completed/success`, `No LDR CI transitions detected`,
        `Conditional dispatch: fired 17, skipped 0 unchanged LDR tip(s)` — exactly the expected one-time catch-up burst
        (17 repos whose tips moved during the 13-day disable; skipped-0 is correct since none had a run for their
        current tip yet). **2nd run (28148425221) PROVES the cost-cap engages:
        `Conditional dispatch: fired 1, skipped 16`** — the 16 catch-up tips are now covered → skipped; only 1 changed
        tip re-fired. So the billing wall (≈24 unconditional dispatches/tick) CANNOT recur, while LDR ratchet drift is
        now monitored hourly. No `! gh`/`Traceback` either run. The monitor is LIVE again. Closes
        `github_actions_billing_wall_2026_06_11` ▸ "re-enable ldr-ci-monitor after its fixes". (NEW 2026-06-25)
- [x] ✅ [SCRIPT] P1. ADDRESSED 2026-06-25 (slot-2) via the named **"or fold into the WS-0 LDR monitor"** branch: WS-0
      #2's revived+re-enabled `ldr-ci-monitor` runs the FULL `quality-gates-v2` (ratchets incl.) against the LDR tip
      hourly — so drift introduced by ANY carve-out direct push (docs / dirty-dep / workflow) is now DETECTED within ~2h
      **with commit attribution**, regardless of how it bypassed the per-push QG. The core risk this item names
      ("undetected drift") is closed (DETECTION, hourly + attributed). Residual (optional, faster) → the sub-item below.
      **Supersedes** the WS-C P3 "audit how a lint-red commit reached SIT LDR". (NEW root-cause 2026-06-24)
  - [ ] [SCRIPT] P3. OPTIONAL faster path — a push-time pre-push ratchet/lint check on the carve-out paths (immediate
        PREVENTION vs the monitor's ~2h DETECTION). Nice-to-have now that the monitor covers detection; only worth it if
        the ~2h detection window proves too slow in practice. (NEW 2026-06-25)
- [x] ✅ [SCRIPT] P1. Ratchet/codex local↔CI SCOPE parity — make every ratchet/codex check scan the SAME path set
      locally and in CI (kill the `pm-script-path-ref` whole-workspace-vs-PM-only divergence class) so a local-green
      commit reliably predicts the promote v2. Concretizes the WS-D parity catch-all for the ratchet-scope case. (NEW
      root-cause 2026-06-24) — **unified-trading-pm@4e2eb376f** | Root: `check_architectural_ratchets.py` was the ONLY
      divergent check (ST-19/PB-19/UI-18 globs target service repos; codex/plan/runbook checks are PM-scoped). Two
      fixes: (1) PM `quality-gates.sh` line 466 had wrong path `${REPO_ROOT}/scripts/...` (silently skipped since file
      never existed there); corrected to `${REPO_ROOT}/unified-trading-pm/scripts/...`. (2) STEP 5.100 added to
      `base-service.sh` so each service repo CI enforces applicable ratchets via
      `check_architectural_ratchets.py --workspace-root $REPO_ROOT` — in service CI `$REPO_ROOT/<repo>/...` = checkout →
      own-repo ratchet fires, other-repo globs find 0 files (correct pass). base-service.sh is sourced at runtime (never
      copied), so fleet enforcement is immediate with no rollout. STEP 5.100 verified PASS on PM QG. PR #560 → main.

### WS-A — ci_status → Firestore SSOT (Phases 3–4) — see D2

> **Design decisions (operator-confirmed 2026-06-25, slot-2 implementation discussion):**
>
> - **Consolidator runtime = GHA hourly cron, NOT Cloud Run** (supersedes line 205's original "Cloud Run Job +
>   Scheduler"). The job is <1 min of real work (one strongly-consistent Firestore collection query + a manifest JSON
>   edit + one commit; the DAG SVG is gitignored so it is NOT regenerated into the commit). A GHA cron already has
>   checkout + a write-scoped token; Cloud Run would need a PAT baked into the job to push to GitHub — added
>   complexity + a secret surface for a trivial, billing-trivial (~24 runs/day) job. Promote to Cloud Run only if
>   cadence ever needs sub-minute (it won't — promote bots already read live Firestore).
> - **Firestore consistency**: single-doc reads AND collection queries (`stream()`) are strongly consistent (sub-second)
>   — there is NO minute-scale read lag. The only interval-staleness is the manifest **projection** (the
>   offline-fallback cache), which is exactly why the readers migrate to read Firestore directly. Promote gates already
>   read live Firestore (Phase 2).
> - **Writer side is already done**: `ci_status` has a single-writer architecture (Guard 1 =
>   `check_ci_status_bot_only.py` — only `ci-status-update[bot]` may change it) and that one funnel already dual-writes
>   Firestore (`ci-status-update.yml:202`). So there is NO fleet of writers to migrate; Phase 3 is the reader side +
>   dropping the git half. (`staging_status` is mentioned in D2 "in the same spirit" but is a separate lower-frequency
>   field — out of WS-A scope; follow-on.)
> - **Ordering-robustness is a PREREQUISITE for retiring the reconciler** (Finding from the implementation discussion):
>   `resolve_status` is rank-based, not sha/timestamp-aware, so a STALE green arriving after a fresh fail can clear it
>   (`prev=FAILING, new=FEATURE_GREEN` → advances). Today `ci-status-reconciler.yml` backstops that. So the store must
>   become ordering-safe (reject a write older than the stored one) BEFORE line 208 retires the reconciler — added as
>   the new item below.

- [x] ✅ [CODE] P2. Phase-3 consolidator — **GHA hourly cron** (`ci-status-consolidator.yml` +
      `scripts/cicd/ci_status_consolidator.py`): projects the Firestore `get_all()` aggregate →
      `workspace-manifest.json` ci_status, ONE skip-ci commit/interval — replaces the per-transition manifest commit.
      (promotion_pipeline ▸ ci_status_firestore) — **DONE 2026-06-25 slot-2: PM@a9be370. project() copies the resolved
      Firestore status verbatim (no re-resolve), writes only changed values (no reformat churn), heals a manifest commit
      lost to a push race. 9 unit tests; end-to-end dry-run against prod (25 docs, no-op when in sync); positive
      change-detection smoke; actionlint clean. Cron inert until it reaches main (Option-B drain).**
- [x] ✅ [CODE] P2. Store ordering-robustness — reject a write older than the stored doc, so retiring the git reconciler
      can't let a stale green clear a fresh fail (NEW prerequisite for 208, slot-2 2026-06-25). (promotion_pipeline ▸
      ci_status_firestore) — **DONE 2026-06-25 slot-2: PM@067ed3e. `is_stale_write()` rejects a non-FAILING write for a
      STRICTLY-OLDER `commit_ts` (ISO-8601) than the stored doc; FAILING always surfaces, `main` always authoritative,
      legacy no-ts callers never blocked (fully backward-compat). `ci-status-update.yml` resolves the tested sha's
      committer date via the GitHub API (consumer sha not in PM history) → passes `--commit-ts`, activating the guard
      PM-only (no fleet-template change). Tests: is_stale_write truth table + set_status
      stale-reject/newer-accept/ts-carry-forward.**
- [x] ✅ [CI] P2. **[REFRAMED slot-2, then CORRECTED 2026-06-25 Ikenna/Opus — Guard-2 ci_status is KEPT, NOT moot.]**
      ~~Migrate the backmerge ci_status readers~~ / ~~drop the moot Guard-2 ci_status branch with 208~~. **The slot-2
      premise — "ci_status leaves the manifest at 208, so there is nothing left to conflict on" — is FALSE and
      self-contradicts the shipped consolidator (205): `ci-status-consolidator` projects Firestore → manifest ci_status
      **on main** (the hourly cron's default branch), so ci_status REMAINS a main-authoritative manifest field.**
      Guard-2 (`reconcile_manifest_backmerge.py::_REPO_CI_FIELDS`) therefore correctly auto-resolves the
      consolidator-on-main vs LDR-stale conflict to main (theirs); removing it = zero benefit + slightly MORE dam risk
      (a both-changed ci*status would escalate to a human PR instead of auto-resolving to the Firestore-authoritative
      value). Also corrected: the Guard-2 logic is a **PM-only script**
      (`scripts/cicd/reconcile_manifest_backmerge.py`), NOT a fleet-template edit — the backmerge `.yml` only \_calls*
      it and the `[ -f … ]` guard never both-exists-and-conflicts in a service repo (no manifest there). So **no rule-11
      rollout** and **no change** — Guard-2 stays as-is. (promotion_pipeline)
- [x] ✅ [CODE] P2. Orchestrator dashboard / `server/` ci_status read path → Firestore collection query (operator-facing
      visibility). (promotion_pipeline) — **DONE-BY-DIAGNOSIS 2026-06-25 slot-2: the operator-facing ci_status display
      is ALREADY Firestore-backed.** `agent-orchestrator` reads `ci_status` in ZERO files (server/ + dashboard/ + src/
      all empty) — the premise that it has a manifest-ci_status read path is false. The real operator display is
      **deployment-api → deployment-ui** (Repos-CI table), and deployment-api already reads Firestore-authoritative via
      `deployment_api/routes/_ci_status_firestore_store.py` (the Phase-2 reader, manifest as fallback), called from
      `_repo_ci_manifest.py` (`ci_override = resolve_ci_status_map(manifest)`). No migration needed.
- [x] ✅ [CI] P2. **Phase-3 DESTRUCTIVE — DONE 2026-06-25 (Ikenna/Opus-xhigh, operator-greenlit; PM@84978082d, PR #575
      LDR→main auto-merge armed).** Dropped the git-commit half (ci-status-update.yml writes the Firestore SSOT only —
      no manifest commit / DAG regen; set_status un-gated from best-effort) + **removed the `manifest-update`
      concurrency group** (THE LYNCHPIN the plan under-specified: `cancel-in-progress:false` cancelled pending runs
      under burst → the dropped-transition class, e.g. the MDPS MAIN_GREEN drop hand-fixed earlier today; per-repo
      Firestore CAS handles ordering so unbounded concurrency is safe + drop-free) + retired `ci-status-reconciler.yml`
      (+ dead `ci_status_reconciler.py` / test / catalog map). Store CLI gains `--emit-transition` (GHA-agnostic
      prev→written for the notify gating). Empirically de-risked: the reconciler was DISABLED since the 2026-06-11
      billing wall (last run 06-12) and the fleet ran 2 weeks on Firestore-SSOT + consolidator + v2-direct-dispatch +
      is_stale_write/no-downgrade guards. (promotion_pipeline)
- [x] ✅ [VERIFY] P2. Phase-4 — full drain → ZERO ci_status commits; gates behave identically; dashboard live
      (end-to-end validation). (promotion_pipeline) — **DONE 2026-06-27 slot-3: verified
      `git log --all --oneline --grep="ci: update ci_status"` = 0 hits on all main branches; only consolidator's
      `ci: consolidate ci_status from Firestore` pattern exists. WS-A Firestore migration fully drained.**
- [x] ✅ [CODE] P3. `set_status` explicit txn `max_attempts` / retry on Aborted/DeadlineExceeded (Firestore
      eventual-consistency resilience, Finding 2). (promotion_pipeline) — **DONE 2026-06-25 slot-2: PM@067ed3e.
      `set_status(max_attempts=10)` makes the transactional Aborted-retry budget explicit; an outer 3× loop retries
      transient `DeadlineExceeded`/`ServiceUnavailable`/`RetryError` (matched by exception NAME so the module stays
      SDK-free at import). Shipped with the ordering guard above.**
- [x] ✅ [SCRIPT] P3. **DONE 2026-06-25 (with 208, PM@84978082d).** Dropped `_align_workspace_manifest.py`'s static
      `"ci_status": "LOCAL_PASS"` default (the last straggler — a writer-of-default the consolidator overwrote within
      the hour anyway; now ci_status is consolidator-owned, absent == "unset" until a repo's first v2 run).
      `generate_workspace_dag.py` left unchanged per the slot-2 diagnosis (the consolidator keeps the manifest ci_status
      ≤1h fresh, so a viz reading the manifest cache is fine; the LIVE readers — deployment-api
      `_ci_status_firestore_store`, promote bots' `tier_c_promotion_gate` — already read Firestore).
      (promotion_pipeline)
- [x] ✅ [DOCS] P2. Phase-4 — codex SSOT + CLAUDE.md one-liner ("ci_status is Firestore-backed"). (promotion_pipeline)
      **DONE 2026-06-25 (PM@267b304cc, PR #578).** codex `ci-cd-flow.md`: recorded the 208 write-side (Firestore-only,
      no manifest commit / no concurrency group, hourly consolidator owns the manifest cache, reconciler retired,
      Guard-2 ci_status KEPT) + updated the drift-tick / skip-marker-safe examples off the retired per-transition
      writer. CLAUDE.md: ci_status-Firestore-SSOT regression guard + sharpened the promotion-PR skip-marker rule
      (triggers from anywhere in the message incl. the body). **Phase-4 VERIFY (drain → zero ci_status commits) still
      open** — needs real multi-repo agent traffic; deferred to the next active working day (no organic transitions to
      observe now).

#### WS-A Progress Log (slice 1 — additive; slot-2 2026-06-25)

- **Task-zero foundation check (DONE):** queried the `ci_status` Firestore collection (prod `central-element-323112`,
  REST API) — **25/25 active repos present**, fresh `updated_at` (within hours), correct statuses + branch fields. The
  dual-write (`ci-status-update.yml:202`) is genuinely live, not hollow → reader migration + consolidator are safe to
  build on.
- **205 consolidator (DONE, PM@a9be370):** shipped. **Footgun caught + resolved:** the literal `[skip ci]` in my commit
  BODY (describing the workflow) suppressed v2 on the LDR tip → standing PR #559 went BLOCKED with 0 checks. Resolved by
  a clean follow-up flip commit (no `[skip ci]` in its message) → re-triggered v2 on #559 → **#559 MERGED** (PM main
  `1a8cd1421`). **Lesson for the rest of WS-A: never write the literal `[skip ci]`/`[ci skip]` in a commit message body
  — write "skip-ci" instead.**
- **Ordering guard + 210 (DONE, PM@067ed3e):** `is_stale_write` + `commit_ts` + `max_attempts`/transient-retry shipped;
  `ci-status-update.yml` activates the guard by resolving the tested sha's committer date via the GitHub API. The
  reconciler can now be retired safely (the store rejects a stale green over a fresh fail).
- **Reader-migration diagnosis (206/207/211) — RESOLVED WITHOUT NEW MIGRATION (slot-2 2026-06-25):** investigated every
  ci_status reader. (a) **207 already done** — deployment-api reads Firestore-authoritative
  (`_ci_status_firestore_store.py`); agent-orchestrator reads ci_status nowhere (0 refs). (b) **206 is not a reader** —
  the backmerge only manifest-CONFLICT-resolves ci_status (Guard-2), which goes no-op when ci_status leaves the manifest
  → destructive-phase removal. (c) **211 needs no additive migration** — `_align` sets a static default (consolidator
  overwrites it), `generate_workspace_dag` is a viz the consolidator keeps ≤1h fresh; the live readers (deployment-api,
  promote bots) already read Firestore. **Net: the additive slice is COMPLETE.** The load-bearing pieces (consolidator
  keeps the manifest a fresh cache + ordering guard makes reconciler-retirement safe) are shipped; the remaining work
  (206 Guard-2 removal, 211 `_align` default removal) is all coupled to the DESTRUCTIVE phase (208).
- **⏸️ PAUSED for operator before the DESTRUCTIVE phase (208)** per the agreed cadence — drop the ci-status-update
  git-commit half + retire `ci-status-reconciler.yml` + the coupled Guard-2 / `_align`-default cleanups. Awaiting
  operator go.
- **TAKEOVER (2026-06-25, Harsh → Ikenna):** the additive slice is DONE (consolidator `a9be3704c` + ordering-guard
  `067ed3e74`, both on `main`; cron `ci-status-consolidator.yml` LIVE hourly :08; prod dry-run green — 25/25 repos in
  the `ci_status` Firestore collection). 207/206/211 were closed BY DIAGNOSIS (deployment-api already Firestore-first;
  agent-orchestrator reads ci_status in zero files; 206/211 are destructive-phase-coupled, not additive
  reader-migrations) — do NOT redo them. The ONLY remaining work is the DESTRUCTIVE phase (208), operator-gated; resume
  by reading this Progress Log then greenlighting it. Higher-blast-radius parts = the writer-drop + the
  `staging-backmerge` fleet-template edit (rule-11 rollout). **Gotcha (logged): NEVER put the literal
  `[skip ci]`/`[ci skip]` in a commit BODY** — it suppresses v2 on the PR head → blocks the drain (caught + recovered
  this session). Nothing is broken/blocked; the pause is a deliberate checkpoint, no loop armed.
- **🔗 De-risks D13 / WS-L Phase 2 (version-out-of-source):** WS-A IS the proof-of-pattern for D13 — "move a per-commit
  state field OUT of git into the Firestore SSOT + retire the git-commit dual-write." Completing 208 (ci_status fully
  Firestore-backed, zero git commits, the store's `is_stale_write` ordering guard replacing the reconciler backstop)
  validates the EXACT mechanism the version registry reuses (`reconcile_release_tags.py` already mirrors version↔tag to
  Firestore). **Sequence WS-A 208 BEFORE WS-L Phase 2 where practical** — the version retarget then rides proven
  machinery instead of co-developing the Firestore-out-of-git pattern twice.

#### WS-A Progress Log (slice 2 — DESTRUCTIVE phase 208; Ikenna/Opus-xhigh 2026-06-25)

- **Operator greenlit 208 on Opus** (D14 model gate: 208 = Opus-xhigh). Shipped PM@84978082d, PR #575 (LDR→main,
  auto-merge armed). Four parts, all PM-only:
  - **Part A — ci-status-update.yml → Firestore-SSOT (the core).** `set_status` (Firestore CAS) is now the PRIMARY write
    (un-gated, not best-effort); dropped the manifest write + `[skip ci]` commit + DAG regen. The Slack notify-gating
    (notify_worthy / severity / sit_pass) now derives from the store's RESOLVED `(prev, written)` via a new
    `ci_status_store.py --emit-transition` flag (keeps the store GHA-agnostic). **Removed the `manifest-update`
    concurrency group — THE LYNCHPIN the plan under-specified:** `cancel-in-progress:false` cancelled pending runs under
    burst (many repos' v2 finishing at once) → silently DROPPED ci_status transitions (the MDPS MAIN_GREEN drop
    hand-fixed earlier today). With the git commit gone there's no write-contention to serialise and the per-repo
    Firestore CAS handles same-repo ordering → unbounded concurrency is safe AND drop-free, which is what makes
    reconciler-retirement safe. permissions narrowed contents:write→read. actionlint clean.
  - **Part B — retired `ci-status-reconciler.yml`** + deleted dead `ci_status_reconciler.py` + its test + catalog map
    (catalog regenerated, consolidator added). **Empirically safe:** the reconciler was DISABLED at the 2026-06-11
    billing wall (last run 06-12) — the fleet ran 2 weeks without it. Its functions are all now covered: stale-green
    race → `is_stale_write` (210); missed-MAIN_GREEN downgrade → `resolve_status` no-downgrade; FEATURE→STAGING
    auto-advance → A1 inheritance (the LDR→staging PR's v2 dispatches STAGING_GREEN pre-merge); dropped Drift 0/1/2 →
    eliminated by the Part-A concurrency-group removal. **Residual (low):** a RARE dispatch network-failure with no
    subsequent repo commit could leave a base repo below MAIN_GREEN (blocking dependents) with no auto-backstop — low
    probability (base repos commit often → self-heal on next v2), visible (staging-to-main logs the blocked repo),
    recoverable (manual re-dispatch ~1 min). Worth a lightweight "repo green-on-main but ci_status below MAIN_GREEN"
    alert as a P3 follow-up.
  - **Part C — dropped `_align`'s static `ci_status` default** (consolidator owns it; absent == unset).
  - **Part D — SKIPPED with a finding (Guard-2 ci_status is NOT moot).** The plan's premise "ci_status leaves the
    manifest at 208" is false + self-contradicts the shipped consolidator (205), which keeps projecting ci_status to the
    manifest **on main** (cron default branch). So ci_status stays main-authoritative and Guard-2's take-theirs is still
    correct; removing it = 0 benefit + slight dam risk. Also: the Guard-2 logic is a PM-only script, not a
    fleet-template edit (no rule-11). See the corrected 206 item above.
- **🚩 SYSTEMIC FINDING (flag to operator, candidate WS-B/D item):** the local QG **version-alignment gate** reads the
  self/dep versions from `workspace-manifest.json`'s `versions` map, but the **main→LDR backmerge SKIPS `[skip ci]`
  manifest-automation commits by design** — so LDR's `versions` map (+ pyproject/uv.lock) perpetually LAGS main's
  semver-agent bumps, and the gate blocks EVERY local commit on LDR until someone hand-syncs
  (`git checkout origin/main -- workspace-manifest.json pyproject.toml uv.lock`). I hit this on 208 (PM self 1.2.534 vs
  main 1.2.536, +12 lagging deps, all clean upgrades). It self-resolved on the remote mid-session (the align commit
  became empty on rebase), but this is recurring friction for every PM-on-LDR agent. Fix candidates: (a) let the
  backmerge propagate `[skip ci]` version-surface commits, or (b) have the gate compare against
  `origin/live-defi-rollout` not `origin/main`, or (c) a periodic version-surface sync job. Not fixed here (out of 208
  scope). **→ now formalized as a WS-C `- [ ]` P2 todo (2026-06-25).**
- **Deferred → Phase-4 (after #575 reaches main — PM default branch; repository_dispatch fires the main copy):** (a)
  [VERIFY] full drain → prove ZERO `ci: update ci_status … [skip ci]` commits on the integration branches + gates behave
  identically; (b) [DOCS] codex `ci-cd-flow.md` + CLAUDE.md one-liner ("ci_status is Firestore-backed; the manifest is
  an hourly-consolidated offline cache"). Both items remain unchecked below.

#### WS-A Progress Log (slice 3 — recovery hygiene + pipeline diagnosis 2026-06-26)

- **✅ VERSION-ALIGNMENT BACKMERGE-LAG FIX (PM@031be7a01, PR #592).** Recurring friction (hit ~5× in one session): the
  QG `version-alignment-gate.sh` hard-BLOCKED whenever the main→LDR backmerge lagged — main bumps via a promote, LDR's
  manifest trails until the backmerge bot runs, so a slot CURRENT with LDR got false-blocked on a version it doesn't
  control (even pure doc edits). Fix: Check 1 (behind-your-branch) still hard-BLOCKs (genuine stale checkout); Check 2-3
  (version-behind-main) BLOCKs only if ALSO behind your branch — when current with your branch it WARNs (the drift is
  the pending backmerge; not the agent's to fix; quickmerge's dep-tier gate is the precise dep guard). Shared gate →
  fleet-wide. Verified: bash -n + shellcheck clean; WARN path deterministically tested (manifest forced behind main +
  current-with-LDR → non-blocking rc=0); aligned full run still green. Same backmerge-lag class as the
  deployment-service straggler from the diagnosis.
- **✅ AUTO DOCS-ONLY QG TIER (PM@9873a8c31) — operator ask, content-derived (not a flag).** Doc-only edits no longer
  run the heavy gate, but WITHOUT the old `--skip-*` flags that agents abused on code changes. `base-service/library/ui`
  now inspect the uncommitted changeset; if EVERY file is pure documentation (`.md/.mdc/.rst/.txt` + doc assets), they
  skip TESTS + TYPECHECK + the codex code-body (lint/format + doc-validators still run); ANY source/config file
  (`.py/.ts/.json/.yaml/.toml/.sh`/workflows) forces the FULL gate — one `.py` can't be dodged. Keys off UNCOMMITTED
  changes, so the server `quality-gates-v2` (committed PR) always runs the FULL gate — the backstop. Docs-only writes
  the green sentinel (complete for a doc-only changeset). Robustness: capture-non-doc-and-test-empty (avoids a
  `grep -qv` combo that a wrapped interactive `grep` mis-handled — real grep in `bash script.sh` is fine, but the form
  is now wrapper-proof). Validated: classification unit-tested in clean bash (md+md→docs-only;
  md+py/json/yaml/toml→full; empty→full); the `.sh` changeset itself correctly ran the FULL gate (no false docs-only).
  This is the implemented slice of the long-planned change-scoped fast tier (`QG_FAST`/quality_gates_speed).

- **Pipeline "stall" diagnosis (operator-requested, dashboard looked jammed).** Verified against ground truth: the fleet
  is NOT jammed — promoter (`staging-to-main`, hourly), Tier-C drain (every few min),
  `staging-conflict-ldr-main-fallback` (hourly), SIT, and the consolidator all run GREEN. The dashboard's reds were
  **stale snapshots**: (a) the staging→main squash wall (staging diverges both-ways from main as main advances and
  staging lags) is **auto-drained by the fallback via clean LDR→main PRs** — it merged features-service #708, ml-service
  #217, strategy-service #345, unified-api-contracts #500 at 11:45–11:58; (b) UAC's "ruff root-blocker" was stale (green
  by 11:53); (c) ci_status reds were the manifest CACHE lagging the hourly consolidation. **The illusion is
  consolidator/fallback hourly cadence vs a continuously-advancing main; the structural cure is the WS-L LDR→main
  migration (no staging↔main merge-base to go stale).**
- **✅ FIX: consolidator clears stale `ci_failure_reason` on recovery (PM@9244dec79).** The hourly consolidator
  projected Firestore `status` + `codebase_health` but never touched the manifest-only legacy `ci_failure_reason`, so a
  recovered repo kept a stale red reason (alerting-service: `ci_status` flipped STAGING_GREEN but `ci_failure_reason`
  still read "QG exit 1 (from batch 6 agent)"). `project()` now blanks it whenever Firestore reports a non-FAILING
  status (+3 unit tests). Triggered an out-of-band consolidator + fallback run during the diagnosis to clear the live
  symptoms.
- **DEFERRED (→ resolved by ldr_main migration, per operator):** a repo whose main→LDR backmerge chronically lags gets
  STARVED by the fallback (it skips "main not fully contained in LDR" each run — deployment-service sat ~26h until its
  backmerge converged, then drained via #287). Migrating such repos to `ldr_main` removes the staging→main dependency
  entirely (the fleet bot drains LDR→main directly), so no separate watchdog is being built.

#### #ci-failures alert-machinery triage (slice 3b — operator-requested 8h sweep, 2026-06-26; PM@62319297f)

Read the last 8h of #ci-failures (via `SLACK_ALERTS_READER_BOT_TOKEN`), root-caused each class, fixed the **machinery**
so they don't recur (not by-hand symptom fixes). All three shipped in one commit (full QG green, sentinel-verified
quickmerge):

- **✅ FIX-1 — update-repo-version / reconcile-staging-versions concurrent-bump rebase conflict (was 3× CRITICAL).** A
  concurrent manifest commit landing on `main` between checkout and push made the 5-attempt rebase-retry loop's
  `git pull --rebase` conflict on `workspace-manifest.json` + the append-only `manifest-mutations.jsonl`, then die FATAL
  on attempt 1 (the `git pull` non-zero under `bash -e` aborted the step before the retry), **silently losing the
  version bump** (incident: deployment-service 0.95.0). Fix: a semantic **manifest merge driver**
  (`scripts/cicd/manifest_merge_driver.py` — max-semver per version key, union `breaking_pending`, recurse dicts,
  FAIL-SAFE→exit 1 on a genuine non-version scalar divergence) + `merge=union` for the audit jsonl + reuse of the
  existing `semvermax` pyproject driver + `keepours` uv.lock, all wired runner-local by
  `scripts/cicd/setup_manifest_merge_drivers.sh` and mapped in a committed `.gitattributes`. The loop now also
  `git rebase --abort`s a genuine conflict cleanly (never pushes a half-rebased tree) and relocks+amends uv.lock when
  the driver resolves a pyproject bump. +9 unit tests; **proven end-to-end on a real `git rebase`** (the exact incident
  scenario auto-resolved: deployment-service 0.95.0 kept, PM→max(1.2.543,1.2.544)=544 no-regress, breaking_pending
  unioned, both jsonl appends kept). Benefits ALL manifest writers (update-repo-version, reconcile, staging-to-main,
  backmerge).
- **✅ FIX-2 — change-freeze CRITICAL→WARNING advisory + garbled-reason fix.** An EXPECTED scheduled freeze (US/EU
  session open, daily) posted `:x: CRITICAL` because `notify-freeze-block` passed `conclusion: failure`, which
  notify-slack's truthful-severity rule force-promotes to CRITICAL. A freeze block is an expected control outcome →
  `conclusion: ""` (WARNING advisory, `:warning:`). The `check` job **still exit-1s as the gate** (cloud-build-router
  depends on that). Also dropped the comma-garbled `notes` from the reason (the quoted CSV `affects_venues`
  `"databento,ibkr"` mis-split under `IFS=, read`, producing the `ibkr",NYSE/...` string; block columns 8-9 sit before
  it so blocking was always correct).
- **✅ FIX-3 — ci-status-update no-op regression re-alert.** "`is now FAILING (was FAILING)`" re-fired a fresh CRITICAL
  on every push to an already-red branch — the regression clause `[ "$WRITTEN" = "FAILING" ]` lacked the prev-guard the
  recovery clause already had. Now gates on a genuine transition (`WRITTEN=FAILING AND PREV!=FAILING`), matching the
  documented "steady-state is anti-spam" intent.
- **Real (non-noise) signals, already self-healed — reported, no machinery fix:** (a) **promotion-lag** features-service
  LDR→staging (277 ahead, oldest commit ~4d) = the staging squash-wall class → **resolved by the in-flight WS-L LDR→main
  migration**, not a monitor bug; (b) **cloud-build** features@a822a01 / ml@386e959
  `ImportError: cannot import name 'SINK_MATRIX' from unified_api_contracts.events` = cross-repo **version-cascade lag**
  (UAC added SINK_MATRIX ~2h prior; the next features build went green once the constraint bump propagated). Observation
  for the operator: a consumer can land code using a not-yet-released dep symbol and red the Cloud Build until the
  cascade catches up — inherent to the cascade window; the systemic cure (atomic cross-repo release) is large and out of
  scope for this alert sweep.

### WS-B — staging→main promotion correctness + drain robustness — see D1, D6

> **⬆️ PRIORITY BUMPED P1→P0 (2026-06-24, operator-directed).** The starvation is actively forcing manual drains (see
> the deployment-service note below) — the two upstream root fixes (Mode A manifest version-bump desync + Mode B Tier-C
> squash-fallback eating semver labels, per D6) should land before more repos need hand-draining.
>
> **NOTE 2026-06-24 (2nd incident) — manual force-sync drains are a TRAP; the promoter must COLLAPSE not MERGE
> zero-content-delta divergence.** deployment-service got stuck AGAIN ~2h after the first drain: the central
> `staging-to-main.yml` promoter is healthy (it ran, computed "11 version-delta", armed auto-merge on 10 repos) but
> **SKIPPED deployment-service because its staging↔main was CONFLICTING — with `main...staging files=0` (IDENTICAL
> content)**. The conflict was pure git-history/SHA divergence (squash-merge lineage), which git can't auto-merge even
> at zero content delta, and which the promoter's `CURE_B_VERSION_AUTORESOLVE` (version-line only) doesn't cover. **Root
> cause = the FIRST force-sync** (the projections re-diverged on independent version bumps + the
> `admin-force-sync-all-to-main.sh` pre-format step). **Two concrete bugs this surfaced:** (1) **`admin-force-sync`'s
> ruff/prettier pre-format is NON-IDEMPOTENT on a moving LDR** — each run reformatted a DIFFERENT file
> (`vm_zombie_watchdog_aws.py`, then `heartbeat_stall_watcher.py`) because it ff's to the latest (not-fully-ruff-clean)
> LDR tip then reformats, so back-to-back `main` then `staging` runs produce DIVERGENT SHAs → never converge (the
> `--stag-branch` run also tripped the Gap-2 rewind guard as LDR advanced mid-op). A clean collapse needs a
> **reformat-FREE** force-push of the exact same LDR SHA to both branches (add a `--no-format` flag, or push
> `origin/live-defi-rollout` by ref, not local HEAD). (2) **the promoter should COLLAPSE (force-sync to LDR) a `files=0`
> divergence rather than open a merge PR that can only CONFLICT** — detect `compare(main,staging).files==[]` and
> force-align instead of merge. **It DID eventually unstick** (force-pushing `main`→LDR-content made the open
> staging→main PR#264 mergeable → it merged; main caught up `0.80`→`0.82`, content-identical) — but only after a messy
> multi-pass that re-staled the Cloud Build mirror again. **STOP hand-draining; land the D6 Mode-A/B fixes + add the
> collapse-not-merge + reformat-free behaviours here.** Composes with the force-push CB-mirror hazard
> (`issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md`).
>
> **PROGRESS 2026-06-24 (bug 1 of 2 FIXED):** `admin-force-sync-all-to-main.sh` now has a **`--no-format`** flag
> (PM#531, merged) — gates the non-idempotent ruff/prettier pre-format so a clean collapse pushes byte-identical trees
> to main+staging (no spurious reformat diff). **This addresses the ROOT of the recurring stick:** code-reading the
> promoter showed it is ALREADY robust — it auto-clears tree-identical divergence
> (`_tree_sha(staging)==_tree_sha(main)`, L955–980), Cure-B (`CURE_B_VERSION_AUTORESOLVE`) auto-resolves version-LINE
> conflicts, and only a GENUINE non-version content conflict escalates to the conflict-resolution-agent.
> deployment-service kept escalating because the force-sync reformat injected a **spurious non-version diff**. With
> `--no-format`, a future collapse is version-line-only → Cure-B handles it → NO escalation, NO manual drain. **Use
> `--no-format` for any future collapse.**
>
> **REMAINING (the riskier bug 2):** make the promoter AUTO-COLLAPSE a content-lossless (tree-equal-modulo-version, or
> reformat-only) divergence instead of escalating. This needs the promoter to **force-update a service repo's `main` ref
> past branch protection** — a capability the workflow deliberately does NOT have today (it merges via protected,
> v2-gated `gh pr create` + auto-merge; the only `git push` is the FF manifest bookkeeping to PM's own main). Adding a
> protection-bypass force-ref-update to the fleet-wide `*/15` promoter is **security-sensitive + fleet-critical** (a bug
> force-pushes a wrong SHA to every repo's main) — it needs deliberate design + review + a tight guard (only when
> `staging_tree == main_tree` modulo the bumped version line), NOT a hasty edit. The D6 Mode-A/B upstream fixes remain
> too.

#### SPEC — Safe auto-collapse of a content-lossless staging→main divergence (bug 2, implementation-ready)

**Goal:** when a staging→main promotion is `dirty` (git 3-way conflict) but the NET content delta is lossless (≤ the
bumped `version` line), promote it automatically — WITHOUT ever force-pushing a protected branch. The trick: don't try
to "resolve" the divergent histories in place; **rebuild the promotion as a single clean commit on top of `main`** and
merge THAT through the existing protected, v2-gated PR path.

**Non-negotiable safety constraints**

1. **Never force-push / force-update a protected branch** (`main`/`staging`) from the fleet `*/15` promoter. The only
   push is to a throwaway UNPROTECTED feature branch; the actual main update is a normal v2-gated PR auto-merge (same
   gate as every other promotion). This is what makes it safe — no new bypass capability, no "wrong SHA force-pushed
   fleet-wide".
2. **Fire ONLY when provably content-lossless.** Confirm the ONLY differing file is `pyproject.toml` and the ONLY
   differing line is `^version = `. Implementation: `gh api compare/main...staging` is squash-inflated → instead diff
   the trees: list `.files` from the compare AND independently verify via `git diff --stat origin/main origin/staging`
   in a shallow checkout; require `files == ["pyproject.toml"]` AND the pyproject hunk touches only the `version` line.
   ANY other delta → DO NOT collapse; escalate as today.
3. **Kill-switch:** gate the whole behaviour behind repo/org var `STAGING_TO_MAIN_AUTOCOLLAPSE` (default `false` →
   opt-in).
4. **Rate-limit:** at most `K=3` auto-collapses per run, so a logic bug can't fan out across the fleet in one tick.
5. **Auditable + reversible:** log pre-collapse `main` SHA + the resolution branch name; it's a normal PR (revert-able).

**Mechanism (per repo R, only after Cure-B fails on a `dirty` PR):**

1. **Lossless check** (constraint 2). Not lossless → skip (escalate unchanged).
2. **Build a clean resolution branch** (a clean descendant of `main`, so the PR can't conflict):
   - `git fetch origin main staging`
   - `git checkout -B promote/collapse-<R>-<short-staging-sha> origin/main`
   - `git checkout origin/staging -- .` — take staging's ENTIRE tree (lossless ⇒ this changes only the version line)
   - write `version = max(main_ver, staging_ver)` (semver) into `pyproject.toml`
   - `git commit -m "chore(collapse): staging→main content-lossless align — version max [skip-cascade]"`
   - `git push origin HEAD:promote/collapse-<R>-<sha>` — **UNPROTECTED feature branch; no bypass needed**
3. **Open the PR** `promote/collapse-<R>-<sha> → main`, `gh pr merge --auto --squash`. It descends cleanly from `main` ⇒
   conflict-free ⇒ v2 runs ⇒ auto-merges via the SAME protected path as every promotion.
4. **Close the old conflicting `staging→main` PR** (superseded; comment-link the new one).
5. After merge, `main` tree == `staging` tree ⇒ the existing tree-equal auto-clear (L955–980) clears the quarantine and
   the version-promote step reconciles the manifest on the next `*/15` tick. The `[skip-cascade]` marker (mirror the
   existing no-bump guard) suppresses a spurious dependency-update cascade since content is unchanged.

**Why it's strictly safer than the force-ref-update idea:** no protected-branch force-push exists anywhere in the path;
`main`'s content provably changes by ONLY the version line; every gate (v2, protection) still fires; blast radius is
bounded by the kill-switch + the K-per-run cap + the lossless guard.

**Rollout:** land with `STAGING_TO_MAIN_AUTOCOLLAPSE=false`; enable for `deployment-service` ONLY first; watch 2–3
`*/15` cycles (does it open the collapse PR + merge + clear quarantine?); then fleet-enable. Add a unit/dry-run test:
synthetic content-lossless-divergence fixture (mocked `gh`) → assert it builds the resolution branch + opens the PR +
does NOT fire when a non-version file differs.

**Composes with bug 1:** with `--no-format` already landed, the common case is pure version-line and Cure-B handles it;
this SPEC is the defence-in-depth for the residual `dirty` divergent-history case where git's stale merge-base defeats
Cure-B's in-place resolve.

> **NOTE 2026-06-24 — deployment-service manually DRAINED (its 33-file starvation is CLEARED):** to unblock the
> data-pipeline auto-kill monitor fix (which had to reach `main` so the next `deployment-api:latest` build carries it +
> the cloudbuild `redeploy-monitor-jobs` step auto-re-pins the monitor jobs), deployment-service was force-synced
> `main`+`staging` ← `live-defi-rollout` via `admin-force-sync-all-to-main.sh --repo deployment-service`
> (relax→force→restore; protection verified restored: main `enforce_admins=true`, rulesets `active`). Result: the
> 346-commit/300-file divergence collapsed to a single version-line (main `0.77.0`, staging `0.78.0`). **So
> deployment-service no longer needs draining — but the force-sync ADDED a `versions`/`staging_versions` split for it
> that the manifest-hygiene item below must reconcile.** The other ~19 starving repos still need the systemic fix.

- [x] ✅ [AGENT] P0. Manifest hygiene (post-drain): reconcile manifest `versions`/`staging_versions` to the drained
      pyproject versions where `assert_version_coherence.py` (warn-only) shows a split; next semver/promote cycle also
      realigns it. **NOTE 2026-06-24: 14 VERSION_SPLITs currently flagged (warn-only); deployment-service force-sync
      (above) added one more (main 0.77.0 / staging 0.78.0) — confirms this is still live.** (starvation ▸ P0) —
      unified-trading-pm@3980fe489 | assert_version_coherence.py → ✅ All repo versions coherent (0 violations)
- [x] ✅ [SCRIPT] P0. **Bug 1/2 — `admin-force-sync --no-format`** (PM#531, merged): gate the non-idempotent
      ruff/prettier pre-format so a clean collapse pushes byte-identical trees → version-line-only conflict → Cure-B
      handles it, no escalation. Addresses the root of the recurring stick. (starvation ▸ P0)
- [x] ✅ [WORKFLOW] P1. **Bug 2/2 — promoter auto-collapse a content-lossless `dirty` divergence — IMPLEMENTED + TESTED
      (PM@01ba0ca74, shipping LDR→main; INERT until `STAGING_TO_MAIN_AUTOCOLLAPSE=true`).**
      `scripts/cicd/auto_collapse_lossless_promote.sh` (takes staging's FINAL tree as ONE clean commit on main → can't
      conflict → v2-gated PR; NO protected force-push) + guard test `test_auto_collapse_lossless_guard.sh` (3/3:
      version-only→collapse, any other diff→escalate) + `staging-to-main.yml` Merge-step wiring (after Cure-B `dirty`,
      opt-in + K=3/run cap + downgrade guard). **Rollout:** set the repo/org var for deployment-service first, watch 2–3
      `*/15` cycles, then fleet-enable. Rebuild the promotion as ONE clean commit on top of `main` (take staging's
      tree + `version=max`) on an UNPROTECTED `promote/collapse-<repo>-<sha>` branch → merge via the existing v2-gated
      protected PR path; **never force-push a protected branch.** Guards: lossless check (only
      `pyproject.toml`/`version` differs), kill-switch `STAGING_TO_MAIN_AUTOCOLLAPSE` (default off), K=3/run cap,
      single-repo rollout first. Edit `staging-to-main.yml` Merge step (L612+) AFTER the Cure-B `dirty` branch.
      (starvation ▸ P1)
- [x] ✅ [WORKFLOW] P2. `staging-to-main` "Commit manifest update" race ROOT fix — re-derive the mutation onto fresh
      `origin/main` inside the retry loop so commits are conflict-free and bookkeeping lands every run. (Alert
      mitigation already SHIPPED PM@706b8f414: abort conflicting rebase, 5→8 attempts, `::warning::`+`exit 0` on
      exhaustion. Root fix (a)/(c) remains.) (promotion_pipeline ▸ bug #11) — unified-trading-pm@e12d3969b | Root: on
      push rejection, `git reset HEAD^` + fetch fresh `origin/main` + semantic re-derive (start from fresh main, apply
      our mutations: versions/staging_versions/staging_commits/staging_status/main_commits/promotion_failures+
      quarantine/repositories[promoted].ci_status) → re-commit → retry push. No rebase → no textual JSON conflict.
      Preserves concurrent ci-status-update/semver-agent writes by taking fresh main for non-owned keys. PR #562 → main.
- [x] ✅ [SCRIPT] P2. Durable fix for the staging-unlock / check-staging-lock refresh gap — re-run open-PR required
      checks after the lock clears (else a lock-blocked PR stays blocked post-unlock). (promotion_pipeline ▸
      contract_hardening #20) — ALREADY SHIPPED: `refresh-open-prs` job in
      `scripts/workflow-templates/staging-lock-     check.yml` (triggered by
      `repository_dispatch: [staging-locked, staging-unlocked]`) deployed fleet-wide (24/24 repos); `sit-unlock.yml`
      already dispatches `staging-unlocked` to all repos. Landed PM@d18cb11b9. Verified 2026- 06-25: all 24
      `staging-lock-check.yml` copies have the `refresh-open-prs` job.
- [x] ✅ [SCRIPT] P2. Lock writes `[skip ci]` → backmerge skips → stale `staging_status` in the LDR copy; reconcile
      non-quickmerge readers (promote bots / direct manifest readers). (promotion_pipeline ▸ contract_hardening #21) —
      unified-trading-pm@db40364b1 | quickmerge.sh STAGE-informational lock warning (lines 1585–1598) was reading the
      local LDR file; changed to `git show origin/main:workspace-manifest.json` (STAGE 1.5 already fetched it). Promote
      bots + staging-lock-check already read from `origin/main`/GitHub API → only remaining stale reader was this
      informational path.
- [x] ✅ [WORKFLOW] P2. Batch a breaking fan-out into ONE cascade over the union of dependents (stop per-consumer
      serialization). (promotion_pipeline ▸ contract_hardening #29) — ALREADY RESOLVED by Phase 1.5a (2026-06-18):
      `update-dependency-version.yml` now commits `chore(deps):` on LDR (not `feat!:` staging PR) → dep-update commits
      yield PATCH bumps → no per-consumer cascade dispatch. ONE cascade fires from source library's
      `update-repo-version.yml` (`cascade-qg-ordering.yml` computes union of all transitive deps). Verified:
      `update-dependency-version.yml` has zero `cascade-qg-trigger` dispatches (grep confirmed).
- [x] ✅ [SCRIPT] P2. Consumer re-pin breaking verdict — run `detect_breaking_change.py` on the consumer surface
      (re-pins still unconditionally `feat!`). (promotion_pipeline ▸ contract_hardening #31) — see D3. — ALREADY
      RESOLVED by Phase 1.5a (2026-06-18): `update-dependency-version.yml` line 309 commits `chore(deps):` not `feat!:`
      for MAJOR/breaking re-pins. Dep re-pins (only `pyproject.toml`+`uv.lock`) have no public-API surface change →
      `detect_breaking_change.py` returns `is_breaking=false` via the normal staging-PR flow → no cascade lock. `feat!:`
      was the unconditional human-override token; bots now use `chore(deps):` per line 291-293 comment.
- [x] ✅ [SCRIPT] P2. Review `cloud-build-router.yml` membership in the `manifest-update` concurrency group
      (non-replayable payload → eviction risk). (promotion_pipeline ▸ contract_hardening #27) —
      unified-trading-pm@3dadfdbd9 | Root: `cancel-in-progress: false` still allows only ONE pending run fleet-wide per
      group; in a fleet fan-out (2+ repos dispatch `qg-passed` simultaneously), intermediate payloads are evicted
      because GitHub queues only one pending run per group. Fix: moved to
      `cloud-build-router-${{ github.event.client_payload.repo || github.run_id }}` — per-repo scoping means different
      repos build concurrently (no eviction), same-repo serialises (no race on deployed_versions write). Manifest write
      already has `|| true` on push (soft-failure, no regression from decoupling). PR #561 → main.
- [x] ✅ [SCRIPT] P1.5. Verify the LDR→staging drain resolves all deps at the staging ref (no mixed-ref clone). Composes
      with WS-D dep-clone ref-determinism. (promotion_pipeline ▸ ldr_trunk) — VERIFIED: deps cloned at
      `live-defi-rollout` HEAD (CONTENT-FIRST, 2026-06-11 operator decision, python-quality-gates-v2.yml:359). No
      mixed-ref issue — both repo-under-test and dep clones are at LDR, matching local QG semantics exactly.
- [x] ✅ [CICD] P2. Downstream conflict fallout — re-check the secondary stuck PRs (staging→main promotes + LDR→main
      fallbacks + main→LDR backmerges) that conflicted during the 2026-06-21 storm; most auto-resolve, a few may need a
      rebase. (starvation) — Checked 2026-06-25: (1) unified-cloud-interface: 6 stale March-2026 `auto/` PRs (#16–#21)
      CONFLICTING → closed (content already in main via LDR, files=0 vs main). (2) agent-orchestrator #469 staging→main
      CONFLICTING — ci-failure-watcher is active (runs hourly, last at 08:10 UTC; PR created 08:12 UTC; next run will
      auto-recover/escalate). (3) All other service repos: zero stuck/conflicting promo PRs.
- [ ] [CICD] P3. EXPLORE: why the 0.24.0 fan-out used the retired staging-direct pattern despite consumers having the
      LDR-direct template since 06-18 (likely: `repository_dispatch` runs the handler from the repo's stale default
      branch). Confirm so it can't recur. (starvation)
- [ ] [WORKFLOW] P3. Redundant empty staging→main PRs across consecutive `*/15` runs (NICE-TO-HAVE) — re-check
      tree-equality at PR-create time or auto-close empty BLOCKED PRs. (promotion_pipeline ▸ bug #11)
- [ ] [SCRIPT] P3. Host stale-PR / stale-checkout monitoring (Track D) — extend slot Slack monitoring.
      (promotion_pipeline ▸ ldr_trunk)

### WS-C — semver + version surface — see D4, D5, D7

- [x] ✅ [SCRIPT] P1. Lossy dispatch queue — make `update-repo-version` records loss-proof (verified-live root cause:
      bumps disappear mid-flight). (release_machinery ▸ semver) — **unified-trading-pm@6132dc8f1 | DEFECT-1 root fix**:
      dedicated `version-bump` concurrency group (not `manifest-update`) prevents
      ci-status-update/sit-gate/cloud-build-router from evicting queued version-bump runs (observed: 6 cancelled runs
      2026-06-09). Loss-proof receipt: new "Log dispatch-received" step writes audit entry before any processing;
      "processed" entry added by commit step; gap detects lost bumps. Manifest push retries 5× with rebase (unchanged).
- [x] ✅ [SCRIPT] P2. Fleet rollout — semver-agent bounded-scan + Option-C to 23 repos (confirmed on 2; 21 unswept).
      (release_machinery ▸ contract_hardening #6) — ALREADY COMPLETE: verified 2026-06-25 — all 24 repos carry both
      fixes: (1) BASELINE=0.0.0 branch bounded-scan (lines 316-333 of semver-agent.yml: "SPURIOUS 0.0.0 → bounded scan
      from last release commit"); (2) Option-C `[skip ci]`-drop on version bump commits (line 629: "NO [skip ci]"). Grep
      confirmed 24/24 repos have `SPURIOUS 0.0.0.*BOUNDED scan` marker.
- [ ] [SCRIPT] P2. Decouple SIT-harness hygiene from cascade validity (route harness lint to a fix-task, not a cascade
      block). (release_machinery)
- [ ] [SCRIPT] P2. Retry-cap is alert-only — teach the watcher to diff the failing-slice log + dispatch a fix on cap.
      (release_machinery)
- [x] ✅ [SCRIPT] P2. Action-pin existence gate — resolve `uses:@ref` vs tags pre-rollout (the node24 phantom-tag
      class). (release_machinery) — **DONE 2026-06-25 slot-2: PM@ab4a7be (PR #558).
      `scripts/validation/check-action-pins.py` resolves every `uses: owner/repo@ref`
      (`gh api repos/<o>/<r>/commits/<ref>` — dereferences tag/branch/SHA) across `.yml`/`.yaml`/`.yml.tmpl`, fails on
      any unresolved ref; network-graceful (no-ops under `--block-network`, real work in CI/pre-rollout). Wired as a
      pre-flight ABORT gate in `rollout-workflow-templates.sh`. Unit tests cover the parser; negative-smoked that
      `astral-sh/setup-uv@v8` is flagged while `checkout@v5` passes; live-smoked 5 real template pins resolve.**
- [ ] [SCRIPT] P3. ~~Add the `required_approving_review_count>0` flag~~ → **REFRAMED to REPORT-ONLY (slot-2 2026-06-25
      diagnosis)**: the literal "enforce `>0`" ask CONTRADICTS the live auto-merge design — the `require-quality-gates`
      ruleset (verified live on unified-trading-library main) carries ONLY a `required_status_checks` rule, NO
      `pull_request` review rule, so `required_approving_review_count=0` is INTENTIONAL (agents can't approve their own
      PRs; requiring approvals would deadlock every quickmerge auto-merge fleet-wide). Enforcing `>0` would red-jam the
      fleet. The only safe form is a **report-only** column in `verify_branch_protection_check_names.py` surfacing the
      per-ruleset approval count for operator visibility — never a hard-fail. Low value (the 0 is by design); confirm
      with operator whether report-only visibility is wanted before building. (release_machinery ▸ contract_hardening
      #18)
- [ ] [PROCESS] P3. Audit how a lint-red commit reached SIT LDR (the QG-before-commit miss). (release_machinery ▸
      semver)
- [x] [CI] P2. `major-bump-issue-handler.yml:183` is a second staging-direct writer — reroute the `/approve`-gated 1.0.0
      graduation bump from `staging` to `live-defi-rollout` (LDR-is-SSOT consistency; kept scoped out of 1.5a).
      (dependency_promotion) ✅ — template SSOT + PM own copy + 24-repo fleet rollout; PM@6927a536f + per-repo
      `ci(workflow-templates):` commits pushed to all repos' LDR 2026-06-25
- [x] ✅ [SCRIPT] P2. `propagate-canonical-versions.py` silently SKIPS ceiling-first specs — `_replace_dep_spec()`
      returns on the FIRST separator found; for `"fastapi<1.0.0,>=0.115.0"` it mis-parses → returns unchanged. Parse at
      the EARLIEST operator position across all operators. (dependency_promotion) — **DONE 2026-06-25 slot-2: PM@f9ba669
      (PR #557). `_replace_dep_spec` now collects every operator's index and splits on `min(positions)` → ceiling-first
      specs propagate. Regression guard `tests/unit/test_propagate_canonical_versions.py` (ceiling-first replaces +
      unconstrained-ceiling-first does NOT false-match); smoke-proved the OLD first-found logic left the ceiling-first
      spec unchanged. Unblocks line 344.**
- [x] ✅ [INFRA] P2. Canonical-dependency alignment is advisory + has pre-existing drift — reconcile the two sources
      (`workspace-constraints.toml` ↔ `canonical-dependency-manifest.json`), cap pyarrow (5 repos) + python-multipart
      (fund-admin). Depends on the propagation-bug fix above. (dependency_promotion) — **VERIFIED 2026-06-25 slot-1**:
      zero value mismatches between the two sources (123 constraints / 110 manifest / 15 internal unified-\* in
      constraints only by design / 2 extras-notation entries in manifest only). All per-repo pyarrow caps
      (`>=23.0.1,<24.0.0`) already present in 6 repos; python-multipart cap (`>=0.0.31,<1.0.0`) in 3 repos. Propagation
      bug fix (PM@f9ba669) already applied. No edits needed.
- [x] ✅ [SCRIPT] P2. Registry-poller for the rebuild-without-bump digest edge — **DONE (verified 2026-06-24 slot-2)**:
      `digest-drift-sweep.yml` runs `schedule: 0 */6 * * *`, resolves `:latest`'s digest and dispatches
      `dependency-update` with `base_image_digest` idempotently. (dependency_promotion)
- [x] ✅ [SCRIPT] P3. `--ignore-vuln` block is duplicated across `base-service.sh` + `base-library.sh` (drifted once →
      UTL Mode-B fail; synced 2026-06-18). Extract to a SINGLE shared shell constant (`qg-common.sh`
      `PIP_AUDIT_IGNORE_VULNS`). (dependency_promotion) — **DONE 2026-06-27 slot-3: added `QG_PIP_AUDIT_COMMON_IGNORES`
      to `qg-common.sh`; replaced hardcoded lists in `base-service.sh` + `base-library.sh` with
      `${QG_PIP_AUDIT_COMMON_IGNORES}` reference. PM@473671748024f5 (PR #602).**
- [x] ✅ [SCRIPT] P2. **Version-surface lag blocks every PM-on-LDR agent (the local QG version-alignment gate).** The
      gate reads self/dep versions from `workspace-manifest.json`'s `versions` map and compares LOCAL vs `origin/main`,
      but `main→LDR` backmerge SKIPS `[skip ci]` semver-automation commits by design → LDR's version surface perpetually
      LAGS main → the gate blocks every local commit on LDR until a hand-sync
      (`git checkout origin/main -- workspace-manifest.json pyproject.toml uv.lock`). Hit on 208 (PM self 1.2.534 vs
      main 1.2.536, +12 lagging deps, all clean upgrades). Fix candidates: (a) backmerge propagates the `[skip ci]`
      version-surface commits, or (b) gate compares vs `origin/live-defi-rollout` not `origin/main`, or (c) a periodic
      version-surface sync job. **INTERIM** — WS-L Phase-2 (version-out-of-source, D13) dissolves this class entirely
      (no version line in git → no lag), so prefer the cheap (b) as a stopgap and let WS-L Phase-2 retire it. (NEW
      2026-06-25 Ikenna/Opus — formalizes the WS-A 208 SYSTEMIC FINDING from the WS-A progress log) — **DONE 2026-06-27
      slot-3: applied option (b) — `version-alignment-gate.sh` now fetches + compares vs `origin/live-defi-rollout` (not
      `origin/main`). Gate emits non-blocking WARN when current with branch but behind LDR; hard BLOCK only on genuine
      branch drift (Check 1). PM@473671748024f5 (PR #602).**
- [x] ✅ [SCRIPT] P3. Stale duplicate `scripts/propagation/templates/update-dependency-version.yml` — **ALREADY DONE
      (verified 2026-06-24 slot-2)**: the file is ABSENT (already deleted); no `scripts/propagation/templates/` consumer
      remains for it. Nothing to do. (dependency_promotion)
- [x] ✅ [DOCS] P3. Stale codex value `codex/08-workflows/ci-cd-flow.md` drift-tick `*/20` — **ALREADY CORRECT (verified
      2026-06-24 slot-2)**: the doc already says hourly (`0 * * * *`) at lines 504-505 ("relaxed from `*/20`
      2026-06-11"); no line asserts the drift-tick IS `*/20`. The `:460` reference was stale. Nothing to do.
      (dependency_promotion)

### WS-L — END-STATE: LDR→main direct promotion + version-out-of-source (strategic; supersedes the WS-B/WS-C interim band-aids) — see D12, D13

> **This is NEW strategic scope (decided 2026-06-25), distinct from the migrated-verbatim items above.** It is the
> structural END-STATE for the conflict/churn classes that WS-B (auto-collapse) and WS-C (version surface) currently
> band-aid per-incident. It is a real fleet-wide CI/CD migration — gated behind a per-repo flag + canary, never a
> big-bang; the `staging→main` squash step + the `version =` source line are RETIRED at the end, and until then the
> interim mechanisms (WS-B auto-collapse, the version-line autoresolve) remain the safety net. Reversible at every phase
> via the flag. **The shared semver-agent retarget (Phase 2) is the HIGH-RISK surface — it gets the heaviest test
> coverage + the canary.** Composes with: WS-A (the Firestore-SSOT precedent + machinery), WS-B (retires the
> auto-collapse band-aid), WS-C (folds the version surface), WS-E (SIT relocation), WS-H (the gh-rate + CI-minute saving
> is the payoff).

**Phase 0 — baseline + harness (do FIRST):**

- [x] ✅ [VERIFY] P1. **MEASURED 2026-06-25 (slot-1).** Fleet QG-v2 duration × promotion frequency × wasted-run rate —
      real numbers below. (NEW 2026-06-25)

  **CI-Cost Baseline (measured 2026-06-25, GH API — 23-repo fleet, 24h window):**

  | Metric                                  | Value                                                                                  |
  | --------------------------------------- | -------------------------------------------------------------------------------------- |
  | Fleet QG-v2 runs/24h (19 active repos)  | ~300 runs                                                                              |
  | QG-v2 avg duration (service repos)      | 183s (range 105–321s)                                                                  |
  | Fleet QG-v2 total CI-time/day           | **~915 CI-min/day**                                                                    |
  | PM orchestration runs/24h               | ~345 runs (ci-status-update 103, ldr-to-staging ~50, staging-to-main ~32, others ~160) |
  | QG-v2 runs on promote branches (wasted) | ~20% of fleet v2 = ~60 runs/24h = ~183 CI-min/day                                      |
  | PM staging-to-main runs/24h             | 32, avg 170s = ~91 CI-min/day                                                          |

  **WS-L (LDR→main) projected saving** — eliminating the staging→main v2 layer:
  - Eliminate staging-to-main.yml runs: 32 × 170s = **91 CI-min/day**
  - Eliminate per-repo staging→main PR v2: ~60 runs × 183s = **183 CI-min/day**
  - **Total: ~274 CI-min/day (~4.6 CI-hours/day)** + conflict/retry waste elimination
  - PAT-REST rate: ~96% of PM API calls (WS-H token-pool split saves most of this)

- [x] ✅ [INFRA] P1. **IMPLEMENTED 2026-06-25 (slot-1).** Per-repo cutover flag via `workspace-manifest.json`
      `repositories.<repo>.promotion_model = "ldr_main"` + canary harness:
      `.github/workflows/ldr-to-main-promote-fleet.yml` committed to LDR (actionlint-clean, QG-green). **INERT by
      design**: (a) schedule/push only fires from main (this lives on LDR until Phase-1 canary-enables); (b) no repo has
      `promotion_model=ldr_main` yet — every repo is skipped. Phase-0 scope: per-repo flag gate (jq read from manifest),
      Tier-A CI gate, breaking_pending block (conservative: wait for SIT), tree-equality content gate, provenance gate,
      runaway breaker (cap 12/6h, tighter than staging's 30), stale-check recovery, conflict dispatch
      (`target_branch: main`), dry_run mode. Tested clean via `actionlint`. **Final step — push to LDR then
      `workflow_dispatch --ref live-defi-rollout --input dry_run=true`** verifies the "no ldr_main repos" early-exit
      path (zero-cost, non-destructive). (NEW 2026-06-25)

**Phase 1 — LDR→main direct promotion (extend PM Option-B fleet-wide):**

- [x] ✅ [DESIGN] P1. **DONE 2026-06-26 (Ikenna/Opus orchestrator + 4 Sonnet read-only finders).** Pre-audit of EVERY
      `staging→main` consumer — the no-regression manifest. Coverage (exact): 53 PM `.github/workflows`, ~504 PM scripts
      (56 staging-referencing), deployment-ui + deployment-api operator dashboard, 24 service repos'
      `.github/workflows` + the branch-protection rulesets. The plan's named-6 list was incomplete — the audit found ~20
      PM-workflow + ~22 PM-script + ~12 dashboard consumers and the design correction below. Embedded manifest +
      surfaced risks follow. (NEW 2026-06-25)

  **🔑 DESIGN CORRECTION (supersedes the "atomic machinery swap" framing at the item below):** Phase 1 does NOT remove
  the `staging` branch or the LDR→staging drain. A `ldr_main` repo STILL needs LDR→staging in Phase 1 because (a) SIT
  runs on `staging` for breaking changes and (b) **the semver-agent only bumps the version on the staging PR's
  v2-green** — there is NO LDR-side version path until WS-L Phase 2 (version-out-of-source). So Phase 1 relocates ONLY
  the _final merge-to-main_ (`staging→main` ⇒ `LDR→main`); LDR→staging + SIT + semver STAY LIVE for `ldr_main` repos.
  **If the LDR→staging drain is gated OFF for a `ldr_main` repo, a breaking change DEADLOCKS** (no `staging` entry ⇒
  `sit-debounce` never lists it ⇒ SIT never fires ⇒ `breaking_pending` never clears ⇒ the LDR→main bot blocks forever).
  This is the #1 no-regression constraint — see the ⚠️ on the line-below item. **VERIFIED 2026-06-26 (adversarial
  pass):** semver triggers ONLY on `staging` (`semver-agent.yml` `on:` = `workflow_run` v2-on-staging +
  `push:[staging]`); the fleet bot blocks on `breaking_pending` (`ldr-to-main-promote-fleet.yml` L188–191);
  `sit-debounce`'s pending set requires a `staging_versions` entry (L96–103). NUANCE: if `staging` is bypassed BEFORE
  `breaking_pending` is even set (it is written by `update-repo-version.yml` off the semver dispatch, which is
  `branch=staging`), the failure is SILENT DRIFT — no version bump, no SIT, no main gate — rather than an explicit
  block; either way the breaking change cannot promote correctly. So Phase 1 KEEPS the drain; the deadlock is a guard
  against over-applying the "one machinery set" reading.

  **WHY EXACTLY ONE CI v2 STAYS at the LDR→main promote (no-regression — do NOT "optimize" it away):** the WS-L
  motivation is that local QG already ran via quickmerge, so re-running v2 a SECOND time at `staging→main` on
  already-green content is pure waste (operator 2026-06-25) — CORRECT, and that redundant second suite is exactly what
  WS-L removes. But the promote-time v2 is NOT redundant and MUST remain: local QG runs on the agent's PRE-PULL tree,
  not the integrated LDR tip (D11), and concurrent agents + the carve-out direct pushes (docs / dirty-dep / workflow,
  which skip QG entirely) mean the promote tip is a COMBINATION no single local run ever gated. So the irreducible gate
  is exactly ONE v2 on the actual integrated tip that reaches `main` (= the operator's "the promotion still runs one v2,
  same as staging→main would"). The hardened pre-push hook (Phase-1 item below) + WS-D local↔CI parity TIGHTEN
  local-green→promote-green but do NOT make the promote-time v2 removable while LDR is a fast, unprotected, concurrent
  axis. And SIT (the cross-repo breaking-change gate) is COMPLEMENTARY to v2 (per-repo code quality) — enhancing SIT
  (the operator's intent) strengthens the breaking-change axis but does NOT replace the per-repo v2. Net: WS-L goes from
  TWO v2 suites per promotion (the LDR→staging PR + the staging→main PR) to ONE (the LDR→main PR) — the gate COUNT drops
  by one, the gate itself stays.

  **Embedded manifest — fate of each consumer class under `ldr_main`:**
  - **RELOCATE (the new merge path):** `ldr-to-main-promote-fleet.yml` (gate = v2 always + SIT-green for breaking; MUST
    also dep-order-gate deps at `MAIN_GREEN` not `STAGING_GREEN` — verify/implement). Already model-agnostic:
    `promote_provenance_range.py --base-branch main`, `check_strict_quickmerge.py` (`PROMOTED_REFS`).
  - **STAY LIVE for `ldr_main` — do NOT gate off:** `ldr-to-staging-promote.yml`, `tier_c_promotion_gate.py`, the full
    SIT chain (`sit-gate`/`sit-unlock`/`sit-debounce-trigger`/`cascade-qg-ordering` + SIT-repo `smoke-test-gate.yml`),
    `semver-agent.yml`(+`.tmpl`), `staging-backmerge-to-ldr.yml`, `staging-lock-check.yml`,
    `reconcile-staging-versions.yml`, **`main-backmerge-to-ldr.yml` (critical — keeps LDR⊇main)**,
    `ci-status-update`/`-consolidator`, `reconcile-release-tags.yml`; branch-protection (staging keeps
    `check-staging-lock`, main keeps `quality-gates-v2`). Confirmed: per-repo `quality-gates-v2.yml` fires on
    `pull_request: base=main`, so an `LDR→main` PR IS v2-gated; NO service repo carries a local `staging→main` workflow
    (0/24) — `staging-to-main.yml` is PM-central, the only merge-to-main workflow to gate.
  - **GO INERT per `ldr_main` repo (staging→MAIN merge machinery):** `staging-to-main.yml` (skip `ldr_main` — today only
    excludes PM via `MAIN_DIRECT_REPOS`), `conflict-resolution-merged.yml` `staging-validated` retry.
  - **RETIRE per `ldr_main` repo (squash-divergence class is impossible under LDR→main):**
    `staging-conflict-ldr-main-fallback.yml`, `auto_collapse_lossless_promote.sh`, `auto_resolve_version_promote.sh` (+
    the WS-B auto-collapse SPEC, item below).

  **🚩 HIGH-risk no-regression items — ADVERSARIALLY VERIFIED 2026-06-26 (4 fresh refute-mandate finders + Opus
  synthesis, quoted-code evidence); verdict noted per item:**
  - [x] ✅ [WORKFLOW] P1. **DONE 2026-06-26 (PM@0e39f0433, PR #582 → main, v2-gated): `staging-to-main.yml` now skips
        `ldr_main` repos** — the 5 `MAIN_DIRECT_REPOS` sites (159/218/268/529/663) dynamically union any repo with
        `promotion_model == "ldr_main"`, so the staging→main merge + its cures never fire on a `ldr_main` repo (kills
        the double-promote-vs-fleet-bot hazard). actionlint-clean; PROVEN INERT (union = ∅ today, no repo flagged →
        byte-identical behavior). Original finding: it skips only PM via the hardcoded
        `MAIN_DIRECT_REPOS = {"unified-trading-pm"}` (lines 159/218/268/529/657/663). For a `ldr_main` repo whose
        `staging` branch is ahead of `main`, it will CREATE a `staging→main` PR (~L795) and fire the cures on it
        (`auto_resolve_version_promote.sh` L834 / `auto_collapse_lossless_promote.sh` L849) — running CONCURRENTLY with
        the `ldr-to-main-promote-fleet` bot = a **double-promote hazard** (two PRs racing the same repo to main). Fix:
        generalize the skip to read `promotion_model == "ldr_main"`. This is the REAL locus of the cure-dispatch risk
        (see RETRACTED below). (WS-L Phase-1 pre-audit; verified 2026-06-26)
  - [x] ✅ [SCRIPT] P1. **DONE 2026-06-26 (PM@565d28830, PR #588 → main, v2-gated) — STAGE 1.8 dep-order gate ported
        onto the fleet bot.** Was: `ldr-to-main-promote-fleet.yml` did topological _ordering_ only (no dep-status gate)
        and promoted repos in PARALLEL within a tick (L363) → a T4 dependent could reach `main` AHEAD of its T0
        dependency (regression vs `staging-to-main.yml` STAGE 1.8). Fix: ported STAGE 1.8 faithfully — compute ONCE
        (Firestore ci_status overlay, authoritative, via `ci_status_store.resolve_ci_status_map`) the `DEP_BLOCKED` set
        of `ldr_main` repos with a dep not yet on main (ci_status ∉ {MAIN_GREEN, SIT_VALIDATED}); `process_repo` BLOCKs
        those this run; a later tick promotes them once the dep's on-main QG emits MAIN_GREEN (bottom-up drain).
        Safe-defaults match STAGE 1.8 (no manifest entry / no deps / dep untracked / dep ci_status unset → READY).
        Validated: actionlint-clean, embedded python compiles, **functional smoke against the live manifest+Firestore
        correctly blocked alerting-service while dep `unified-api-contracts` read FAILING** (its LDR v2 was red 09:57Z)
        — gate working exactly as designed; the Firestore overlay also beat the stale manifest cache (which still showed
        UAC=MAIN_GREEN). Fleet-rollout dep-order regression now CLOSED. (WS-L Phase-1 pre-audit; verified 2026-06-26)
  - [ ] [WORKFLOW] P1. **[DEFER-TO-PHASE-2 — operator-directed 2026-06-26: throwaway scaffolding, LEFT OFF as a canary
        diagnostic.]** `semver-agent/label-check` enforcement is bypassed under `ldr_main`: the per-repo semver-agent
        posts the status on the **staging HEAD SHA** (`semver-agent.yml` ~L479) = the staging→main PR head today (so a
        FAILING label-check blocks that merge), but under `ldr_main` the merge-PR head is the **LDR SHA**, which never
        receives it. **Decision: do NOT relocate it now.** The label-check still POSTS on the staging SHA, so the
        diagnostic (does the semver label match the API diff?) stays VISIBLE — relocating only adds ENFORCEMENT on the
        LDR→main PR, which SIT (genuinely-breaking changes) + close canary watching cover; and Phase 2
        (version-out-of-source) removes the pyproject version line, reworking label-check, so relocating now is
        discarded work. Residual: a mislabeled-but-not-actually-breaking bump could reach `main` un-flagged in Phase 1 —
        acceptable for a watched leaf canary. (WS-L Phase-1 pre-audit; verified 2026-06-26)
  - [x] ✅ [CODE] P1. **deployment-api half DONE 2026-06-26 (deployment-api@540f9de):**
        `ManifestView.promotion_model_for(repo)` accessor + `promotion_model` on `RepoOverviewDict`/`_overview_row` + 4
        unit tests; QG green, on LDR.
  - [x] ✅ [UI] P1. **DONE 2026-06-26 (deployment-ui@fc291c6) — classifyStall promotion_model-aware + LifecyclePrefetch
        test fixed.** `classifyStall` (`src/lib/repoCi.ts`) returns "none" (not `staging-to-main`-stuck) for `ldr_main`
        repos + `promotion_model` on `RepoCiOverviewRow` (`client.ts`) + 2 regression tests (`repoCi.test.ts`). UI QG
        green (84 tests, build, codex checks); change verified NON-REGRESSING against the repos e2e (stash-test,
        identical before/after). `pw:L2` caveat: the repos e2e suite has 3 PRE-EXISTING reds in UNRELATED specs
        (sub-item) — not caused/touched by this change; classifyStall is covered at the unit layer (correct layer for a
        pure-fn change). The package-lock env-churn from the sub-agent's `npm install` was intentionally NOT shipped
        (eslint-config-prettier already in the committed lock). (WS-L Phase-1)
    - [x] ✅ [UI] P2. **FIXED 2026-06-26 (deployment-ui@fc291c6) — LifecyclePrefetchContext test red.** ROOT CAUSE
          (corrected — NOT a window-leak): the provider's mount effect does
          `Promise.allSettled([backfill, live,     fetchMonitor(experiments), fetchMonitor(scheduled)])` and dispatches
          only AFTER all four settle; the 3 async tests didn't stub global `fetch`, so the two monitor fetches hit the
          absent dev server and HUNG → allSettled never settled → backfill/live never dispatched → `waitFor` timed out.
          Fix: stub `globalThis.fetch` in `beforeEach` (test-only). All 6 pass (633ms, was 3.65s). (NEW 2026-06-26)
    - [x] ✅ [UI] P3. **DONE 2026-06-26 (deployment-ui@0f9acfc, bg-agent) — all 3 e2e reds fixed; UI gate green + pw:L2
          ✓ (290 smoke).** Root causes were genuine drift, fixed at the fixture/spec layer (no component weakened): (1)
          `repos-stuck-panel.spec.ts:10` — `failing_check` chip now appears on TWO PRs (pm#547 + execution-service#89) →
          Playwright strict-mode violation → added `.first()` (still asserts ≥1 renders). (2)
          `repos-promotion-blocked.spec.ts:94` — Image cell refactored to DUAL-cloud GCP+AWS (operator 2026-06-22); old
          testIds (`image-build-time`/`-sha`/`-log-link`) gone → added `image_gcp` to `mockRepoCiRow`, retargeted to
          `image-gcp`/`image-sha-gcp`. (3) `:110` — `image-last-success` moved to the drilldown (already covered at
          `:79`) → spec now checks `image-sha-gcp` shows the failed-build SHA. Files: 2 specs + `src/lib/mock-api.ts`.
          (NEW 2026-06-26)
  - [ ] [SCRIPT] P2. **[DEFER-TO-PHASE-2 — operator-directed 2026-06-26: throwaway, LEFT UNGUARDED as a canary
        diagnostic.]** `_repo_ci_manifest.py::pending_version_bumps()` (L258–281) compares `staging_versions` vs
        `versions` with no `promotion_model` guard. **Decision: do NOT guard it now** — leaving it ungated makes it a
        canary HEALTH SIGNAL: a PERSISTENT pending-bump on the canary means the version isn't converging
        staging→LDR→main (a real bug to catch); a guard would HIDE that. In Phase 1 staging stays live so versions
        converge per-promote (only TRANSIENTLY pending, like any repo) → the bump-rate breaker should NOT false-arm;
        Phase 2 removes version commits entirely. Add a guard ONLY if the breaker actually false-arms during the canary.
        (WS-L Phase-1 pre-audit; verified 2026-06-26)
  - [x] ✅ [WORKFLOW] P2. **(NEW) `deterministic-promotion-conflict-resolve.yml` defaults `target_branch=staging`**
        (L36–39) — the LDR→main promoter must dispatch it (or equivalent) with `target_branch=main` for LDR→main
        conflicts; confirm the take-LDR resolution handles a `main` target. (WS-L Phase-1 pre-audit; verified
        2026-06-26) — **DONE-BY-ANALYSIS 2026-06-27 slot-3: `ldr-to-main-promote-fleet.yml:469` dispatches
        `deterministic-promotion-conflict-resolve` with explicit `target_branch: main`; the resolver uses
        `github.event.client_payload.target_branch || inputs.target_branch` (L69) so it is already fully parameterized
        for `main`. No code change needed.**
  - [x] ✅ [INFRA] P1. **DONE 2026-06-26 — canary = `alerting-service`** (managed rulesets; deps UTL/UAC already on main
        so the fleet-bot dep-order gap can't bite; sole dependent = the SIT harness, handled by the SIT cascade). The 8
        UNMANAGED repos (agent-orchestrator, e2e-testing, features-service, fund-administration-service, greeks-service,
        ml-service, unified-trading-api, unified-trading-system-ui) still need the `pin_branch_protection_rulesets.py`
        `REPOS`-list extension before THEY can canary (their `LDR→main` PR runs v2 but it is NOT required-to-merge).
        (WS-L Phase-1 pre-audit; verified 2026-06-26)

  **✅ Findings RETRACTED by the adversarial pass (kept for the record — do NOT re-raise):**
  - **`ci_failure_watcher.py` promotion_model guard — FALSE-POSITIVE.** The watcher does NOT call
    `auto_resolve_version_promote.sh`/`auto_collapse_lossless_promote.sh` (those live in `staging-to-main.yml`); it only
    close+reopens / escalates REAL open PRs returned by `gh pr list`, so it cannot fire a cure on a phantom PR. The real
    locus is `staging-to-main.yml` (first item above).
  - **`promotion_lag_monitor.py` false-alert — FALSE-POSITIVE (no action).** The monitor has NO `staging→main` leg; its
    4 directions (`LDR→main`, `LDR→staging`, `main→LDR`, `staging→LDR`) all stay legitimate under `ldr_main`, so it does
    not false-alert. Dropped from the action list.
  - **`cloud-build-router.yml` staging-image path — NO breakage (low-risk note only).** It builds a `-staging` image
    only on a `branch=staging` dispatch, but `quality-gates-v2.yml` dispatches `qg-passed` only on `push:[main]` (A3,
    2026-06-10) → image is already off-main; the staging arm is vestigial. Residual: a pre-A3
    `freeze-deferred-build- replay` payload with `branch=staging` could replay to a staging tag (very low prob;
    retention-bounded).

- [x] ✅ [WORKFLOW] P1. **DONE 2026-06-26 (PM@87bf99a16, PR #588 → main, v2-gated) — SIT gate relocated onto the fleet
      bot.** `staging-to-main` got its SIT gate for FREE (it's TRIGGERED by SIT's `staging-validated` dispatch); the
      cron fleet bot has no such trigger, so it needs an EXPLICIT gate. Two parts: **(1) breaking_pending block** — the
      SIT-green signal, SET by `update-repo-version.yml` (off the semver dispatch on staging) and CLEARED by
      `sit-unlock.yml` on SIT pass; **both stay live for `ldr_main`** (LDR→staging drain + SIT cascade untouched), so it
      releases when SIT goes green — NO deadlock (the design-correction's #1 worry, now closed by tracing the
      lifecycle). **(2) breaking-detection race-closer** — breaking_pending is set DOWNSTREAM by the staging drain,
      leaving a window where a breaking change is on LDR but unmarked; the cron bot could promote it ungated (v2 is
      per-repo, NOT cross-repo SIT). Closed by running the SAME AST public-surface differ SIT relies on
      (`detect_breaking_change.py`) on `main..LDR`: a BREAKING delta must be SIT-validated (`ci_status=SIT_VALIDATED`
      AND LDR tree == staging tree, so SIT validated EXACTLY this content); non-breaking promotes v2-gated; fail-open on
      detect error (part-1 is the durable backstop). source-dir = repo-underscored (fleet `SOURCE_DIR` convention).
      Validated: actionlint-clean, detector functionally smoke-tested on alerting-service (main..LDR = non-breaking →
      gate passes, promote proceeds). `staging` stays the SIT/v2 sandbox. (NEW 2026-06-25; done 2026-06-26)
- [x] ✅ [WORKFLOW] P1. **CANARY DONE 2026-06-26 (alerting-service) — LDR→main direct promote PROVEN end-to-end.** The
      fleet bot (`ldr-to-main-promote-fleet.yml`, dispatched `--ref main only_repo=alerting-service`) ran the full cycle
      on a real 1-file delta (alerting-service README codex-ref fix, quickmerge'd to LDR): opt-in gate SELECTED it →
      Tier-A pass (ci_status=MAIN_GREEN) → content gate (LDR≠main trees) → **provenance gate quickmerge-clean** → opened
      **LDR→main PR alerting-service#200** (Option-B path, NOT staging→main) → **v2 PASSED** (run 28227530488, 1m58s) →
      **merged to main** (squash; merge-commit e9549c52, 08:53:43Z); content confirmed on `main`. **Skip-guard HELD:
      ZERO staging→main PR was ever created for alerting-service** (the #582 change works). LDR↔main converged to
      `files:0` (harmless squash skew — LDR is the backmerge sink). Reversible (remove the flag). Prereqs verified live:
      #582 + fleet bot both on main; baseline dry-run no-op; post-flip dry-run selected the repo. alerting-service@PM
      manifest flip = PM#584; staging-to-main skip = PM#582 (PM@0e39f0433). **🚩 ONE GAP CAUGHT (blocks fleet rollout) —
      sub-item.** (NEW 2026-06-25)
  - [x] ✅ [WORKFLOW] P1. **FIXED 2026-06-26 (PM@cfa2d5a46, PR #585) — fleet-bot auto-merge now arms.** Root cause: the
        bot preferred `--auto --rebase`, but **LDR can NEVER rebase onto main** (merge commits from the backmerge-sink),
        and the `--auto --squash` fallback under the **App token couldn't enable auto-merge**; a manual
        `--auto --squash` with the **PAT** armed instantly. Fix: all 3 arm sites now arm `--auto --squash` via
        `GH_PAT_FOR_ARM` (squash primary, rebase dropped, LOUD on failure). PROVEN: the next promote (alerting-service
        #202) showed `auto_merge:true` and **auto-merged to main with zero manual intervention**. Cleaner long-term =
        grant the App `enablePullRequestAutoMerge` + switch the arm back to the App token (optional). (NEW 2026-06-26)
  - [x] ✅ [VERIFY] P1. **FULL REAL-TEST PASSED 2026-06-26 (alerting-service) — real code, both directions.** **GREEN:**
        a real CODE change (extract `_LATENCY_BUCKETS` in `metrics.py`) → quickmerge → fleet bot opened LDR→main PR #202
        → **auto-merged to main at 09:33:57Z with NO manual touch** (the arm fix). **RED-1 (entry gate):** an off-by-one
        regression in `circuit_breaker.py` (`>=`→`>`) → `quality-gates.sh` **RED (exit 1)** (broke a real test:
        `assert 'WARN'=='CRITICAL'`) → quickmerge rejects → never reaches LDR. **RED-2 (server gate):** the same
        regression on a throwaway branch → PR #203 to main → **v2 FAILED → `mergeable_state: blocked`** → cannot merge
        to main (throwaway branch/PR cleaned up). So real code auto-flows to main AND regressions are blocked at BOTH
        gates. (NEW 2026-06-26)
  - [x] ✅ [SCRIPT] P2. **(NEW — real-test finding) basedpyright is WARN-ONLY in the fleet QG** — `quality-gates.sh`
        printed "23 basedpyright error(s) — set `BASEDPYRIGHT_MAX_ERRORS` to enforce" and stayed GREEN (exit 0). So
        **type-error regressions are NOT caught** by the gate (only lint / test / banned-pattern are). Enforce a
        basedpyright error ceiling (ratchet, only-goes-down) so type regressions are blocked. (NEW 2026-06-26,
        alerting-service canary) — **DONE 2026-06-27 slot-3: (1) `base-service.sh` auto-reads
        `[tool.quality-gates] basedpyright_max_errors` from pyproject.toml (D10 pattern — no env var required); (2)
        alerting-service `pyproject.toml` sets `basedpyright_max_errors = 21` (actual count 21/21); QG now prints "21/21
        errors within ceiling — ratchet down as errors fixed". PM@473671748024f5 (PR #602); alerting-service@84d5e88d.**
  - [x] ✅ [SCRIPT] P3. **DONE 2026-06-26 (alerting-service@0d2dbe8, bg-agent) — GCS-403 test noise removed.** Root
        cause: `test_get_storage_client_returns_client` called `get_storage_client()` un-mocked → real GCS connect → 403
        (test SA lacks `storage.objects.create`) → atexit/logging noise. Fix = mock
        `unified_trading_library.get_storage_client` with a full-interface `MagicMock` (hermetic; no network). QG green
        (97s), no 403 in output. (Pre-existing unused-mock warn-only lint at other tests in the file is NOT introduced
        by this change — line nums shifted +14; left as-is.) (NEW 2026-06-26)
- [x] ✅ [WORKFLOW] P1. **DONE 2026-06-26 (PM@02f2c4971, PR #588 → main, v2-gated) — staging→main-MERGE reactors guarded
      for `ldr_main`.** A read-only blast-radius map (Opus) enumerated every staging-reaction site; an adversarial
      re-verification against the TRUE model **corrected an over-guard**: because the Tier-C `ldr-to-staging-promote`
      drain stays LIVE, **staging keeps FULLY mirroring LDR** for `ldr_main` repos — only the staging→**MAIN MERGE**
      folds. So the ONLY real guard sites are reactors that act on the staging→main merge itself: **(1)
      `staging-conflict-ldr-main-fallback.yml`** — skip `ldr_main` (staging perpetually diverges both-ways from main for
      them → permanent false "JAMMED" → it would open a parallel `--merge` LDR→main PR racing the fleet bot's squash PR;
      the fleet bot is the single owner of their LDR→main path); **(2) `quickmerge.sh` STAGE 1.5 staging-lock** — skip
      for `ldr_main` `--hotfix` (their hotfix promotes LDR→main, never staging→main, so an unrelated repo's
      staging-cascade lock must not false-block it; the dep-version/tier gates stay live — they guard
      deps-behind-**main**, still valid). **Already-done sub-parts:** #582 promoter (`MAIN_DIRECT_REPOS`) + fc291c6
      deployment-ui stall classifier. **Deliberately LEFT LIVE (agent over-flagged; verified):**
      `promotion_lag_monitor.py` (LDR↔staging lag legs stay valid — staging mirrors LDR via the live drain; guarding
      would suppress real stuck-drain alerts) + `reconcile-staging-versions.yml` (staging branch + semver stay live for
      `ldr_main` → `staging_versions` stays accurate; guarding would feed the dashboard/coherence-check an absent
      value). Self-gating reactors confirmed needing NO guard: `ci_failure_watcher.py`, `reconcile-release-tags.yml`,
      `sit-unlock`/`conflict-resolution-merged` (fleet-wide dispatches whose per-repo filtering already lives in the
      now-guarded `staging-to-main.yml`). Gate impl = manifest `promotion_model == "ldr_main"` (jq in the workflow;
      `python3.13` read in quickmerge — the flag is stable + normally-backmerged, unlike the `[skip ci]` lock, so the
      local copy is authoritative). Validated: actionlint+YAML clean, `bash -n` + `shellcheck -S error` clean,
      `promotion_model` read smoke-tested (alerting-service=ldr_main skips; others apply). Coverage: the
      `base main --head staging` PR-creation fingerprint appears in ONLY staging-to-main.yml (done) +
      staging-conflict-fallback (guarded) + reconcile-release-tags (comment) → the staging→main-merge actor set is fully
      covered. (ORIGINAL spec below kept for context.)
- [x] ~~[WORKFLOW] P1.~~ **The `PROMOTION_MODEL` flag gates the ENTIRE machinery set, not just the merge path —
      quickmerge + monitors + alerts shift ATOMICALLY with it, and the inactive side goes INERT (workflow-level `if:`
      guard → does NOT trigger) to save redundant GH-Actions spend + stop spurious staging-reaction alerts
      (operator-directed 2026-06-25):** when a repo is on `ldr_main` — (a) **quickmerge** retargets: it still lands on
      LDR, but the staging→main-promotion gates fold away (STAGE 1.5 staging-lock + the dep-version/tier gates were
      `staging→main` concerns → under LDR→main they fold into the `LDR→main` promote's v2/SIT); (b) the
      **staging-reaction monitors/alerts MUST stop firing on staging diffs / staging QG-greens** — the `staging-to-main`
      promoter, `staging-conflict-ldr-main-fallback`, `promotion-lag-monitor`'s staging↔main leg, the
      `staging`-QG-green→promote triggers, and the deployment-ui `staging→main` stall classifier (those signals are
      IRRELEVANT once `staging` is only the SIT sandbox); (c) the NEW `LDR→main` monitors/alerts activate. When the flag
      is OFF (default), the NEW machinery is the stale/non-triggering side (built on LDR, gated OFF) and the OLD
      `staging→main` machinery stays live. **Exactly ONE machinery set is live per repo — NEVER both** (no double-run =
      no redundant GH-Actions minutes, no double-alerting). Implement the gate at each workflow's `if:`/job-condition
      reading `vars.PROMOTION_MODEL` (per-repo or org var), so flipping the var is the single ATOMIC cutover-and-revert
      switch. (NEW 2026-06-25, operator-directed) **⚠️ PRE-AUDIT REFINEMENT (2026-06-26):** "exactly ONE machinery set"
      must mean only the staging→**MAIN MERGE** machinery folds away — the **LDR→staging + SIT + semver machinery STAYS
      LIVE** for `ldr_main` repos in Phase 1 (semver has no LDR-side path until Phase 2; gating it off deadlocks
      breaking changes). See the DESIGN-CORRECTION block on the pre-audit item above. **🟢 OPERATOR-CONFIRMED REQUIRED
      (2026-06-26)** — not optional/hygiene; this is the cost-saving (the redundant `staging→main` machinery runs on
      EVERY repo EVERY cycle) that justifies the migration. **Gate impl = manifest-based**
      `repositories[repo].promotion_model == "ldr_main"` (the de-facto pattern shipped in #582 + the fleet bot +
      deployment-api `ManifestView.promotion_model_for` + deployment-ui `row.promotion_model`), NOT the original
      `vars.PROMOTION_MODEL` framing (a per-repo/org var can't gate per-repo inside a monorepo manifest). **Already
      done:** staging→main promoter (#582 dynamic `MAIN_DIRECT_REPOS`) + the deployment-ui `staging→main` stall
      classifier (fc291c6 `classifyStall` `promotion_model` guard). **Remaining:** (a) quickmerge STAGE-1.5 staging-lock
      fold-away; (b) the staging-reaction monitor guards (`staging-conflict-ldr-main-fallback`, `promotion-lag-monitor`
      staging↔main leg, staging-QG-green→promote triggers).
- [x] ✅ [INFRA] P2. **DONE 2026-06-26 (PM@2f4b7db20) — strict-quickmerge BLOCK + full-QG-always + airtight sentinel
      (operator policy).** Three parts: **(a) pre-push hook BLOCKS by default** (`--block` baked into
      `pre-push-strict-quickmerge.sh`; was WARN-unless-`STRICT_QUICKMERGE_BLOCK=1`) — every code push must go via
      quickmerge; carve-outs (docs/plans/.github/bot/[skip ci]/already-promoted) still pass; `--no-verify` is the only
      escape, backstopped by the server v2. **(b) full QG mandatory in quickmerge** — `--agent` NO LONGER implies
      `--skip-tests` (the real gap: every agent commit was skipping the test gate); `--skip-tests`/`--skip-typecheck`/
      `--skip-codex` are REJECTED (hard error). The model: `quality-gates.sh` runs the full gate + stamps a
      green-sentinel SHA; quickmerge verifies that sentinel (fast-greens an unchanged tree) or runs the full gate
      itself, then opens the PR — `quality-gates.sh` untouched (still a low-level tool with its flags; the enforcement
      is at the push boundary). **(c) SENTINEL INTEGRITY (the teeth, found during impl):** the green sentinel must mean
      "a COMPLETE gate passed on this tree" — but `base-service.sh` missed `SKIP_TYPECHECK` in its write-guard,
      `base-library.sh` missed `SKIP_TYPECHECK`/`RUN_LINT`/`ACT_MODE`, and `base-ui.sh` wrote `.qg_last_passed_sha`
      **UNCONDITIONALLY**. So `quality-gates.sh --skip-typecheck` (or a UI `--lint`) wrote a ship-ready sentinel →
      quickmerge would fast-green an unverified tree. All three base scripts now write the sentinel ONLY on a complete
      run (parity with the documented contract). Validated: `bash -n` + `shellcheck -S error` clean; guard logic
      unit-tested (full→WRITE, every partial→SKIP); full PM QG green (96s, sentinel written); quickmerge gate-then-open
      verified live. Codex docs (`quality-gates.md`, `feature-branch-workflow.md`) rewritten to the gate-then-open
      model. (NEW 2026-06-25; done 2026-06-26) **Rollout note:** the base scripts are the fleet SSOT (per-repo
      `quality-gates.sh` are stubs that source PM's copy), so this is live fleet-wide once on `main`; the pre-push
      hook's `--block` reaches a slot on its next `setup-tab-worktrees.sh` hook (re)install.
- [ ] [WORKFLOW] P2. Retire `staging→main` squash + the conflict-fallback + the WS-B auto-collapse SPEC per repo once it
      is on `ldr_main` (they become dead code). (NEW 2026-06-25)

**Phase 1 fleet rollout — flip leaf repos onto `ldr_main` in canary-style waves (post-alerting-service canary):**

- [x] ✅ [INFRA] P1. **WAVE 1 SHIPPED 2026-06-26 (PM@1240b730a, operator-greenlit) — 3 low-traffic pure leaves onto
      `ldr_main`:** `client-reporting-api`, `fund-administration-service`, `greeks-service` (manifest
      `promotion_model: "ldr_main"`, mirroring the alerting-service canary placement). Selected as pure leaves (NO prod
      repo depends on them — only the SIT/e2e test harnesses; verified from `workspace-manifest.json` dependency edges)
      with low change-rate, matching the canary's risk profile. Reversible (remove the flag). On LDR; reaches main via
      the standing `*/15` ldr-to-main-promote, after which the fleet bot owns their LDR→main path + `staging-to-main`
      auto-skips them (dynamic `MAIN_DIRECT_REPOS` union, #582). **Wave plan:** W2 = the bulk of leaves (MTDS/MDPS/
      features/ml/strategy/execution/instruments/trading-agent/batch-live-reconciliation/unified-trading-api/
      unified-trading-system-ui/deployment-ui/deployment-api/deployment-service); W3 LAST (highest blast radius) =
      unified-trading-library/unified-api-contracts/agent-orchestrator; excluded/verify-first = e2e-testing/
      system-integration-tests/ibkr-gateway-infra (non-standard pipelines), unified-trading-pm (already Option-B). (NEW
      2026-06-26)
  - [x] ✅ [VERIFY] P1. **WAVE 1 WATCH DONE 2026-06-26** — flags reached `main` via PR #594; fleet-bot dry-run
        (run 28249292738) **SELECTED all 3 new repos** into the opt-in set
        (`LDR→main repos (opt-in): alerting-service     client-reporting-api fund-administration-service greeks-service`),
        all `✅ READY — all deps on main` (STAGE-1.8 dep gate), all `TIER A PASS … MAIN_GREEN`, content gate
        `SKIP — main tree == LDR tree` (no pending delta = correct steady state; promotes real code when it appears). No
        staging→main double-promote (recognized as `ldr_main`). Machinery pickup PROVEN identical to the canary. (NEW
        2026-06-26)
- [x] ✅ [INFRA] P1. **WAVE 2 SHIPPED 2026-06-26 (PM@c45c6462a, PR #595 → main auto-merge; operator-greenlit "start the
      next wave") — 14 leaf services onto `ldr_main`:** market-tick-data-service, market-data-processing-service,
      features-service, ml-service, strategy-service, execution-service, instruments-service, trading-agent-service,
      batch-live-reconciliation-service, unified-trading-api, unified-trading-system-ui, deployment-ui, deployment-api,
      deployment-service. Now **18 repos flagged** (canary + W1 + W2). All pure leaves (only SIT/e2e harness consumers);
      `deployment-api`→`deployment-service` dep-order handled by the fleet bot's STAGE-1.8 dep gate. Reversible. Leaves
      ONLY W3 (highest blast radius — unified-trading-library/unified-api-contracts/agent-orchestrator) + the
      excluded/verify-first set (e2e-testing/system-integration-tests/ibkr-gateway-infra non-standard pipelines; PM is
      already Option-B). (NEW 2026-06-26)
  - [x] ✅ [VERIFY] P1. **WAVE 2 WATCH** — same checks as W1 across the 14, post main-merge of #595. (NEW 2026-06-26) —
        **DONE 2026-06-27 slot-3: fleet bot latest run confirmed all 14 Wave-2 repos selected
        (promotion_model=ldr_main); dep-order gate correctly blocked deployment-api while UAC was being promoted same
        tick; 4 repos promoted in latest tick; no spurious promotions. Fleet healthy.**
- [x] ✅ [INFRA] P1. **WAVE 3 SHIPPED 2026-06-26 (PM@eedf686f0; operator-greenlit "kick off the remaining items") —
      FLEET FLAG-FLIP COMPLETE, 21 repos on `ldr_main`.** Final high-blast-radius set: `unified-trading-library` (T1),
      `unified-api-contracts` (T0 — both depended on by ~everyone), `agent-orchestrator` (T0). Phase-1 keeps SIT + the
      LDR→staging drain LIVE for these, so a breaking change is still cross-repo-gated before main (the #1 no-regression
      constraint). **Excluded (verify-first / special):** e2e-testing, system-integration-tests, ibkr-gateway-infra
      (non-standard pipelines), unified-trading-pm (already Option-B). Reversible per-repo (remove the flag). (NEW
      2026-06-26)
  - [x] ✅ [VERIFY] P1. **WAVE 3 WATCH** — same checks as W1, post main-merge; watch UTL/UAC especially (their breaking
        changes red the fleet — confirm SIT gates them before the LDR→main bot promotes). (NEW 2026-06-26) — **DONE
        2026-06-27 slot-3: verified `workspace-manifest.json` has UTL/UAC/agent-orchestrator with
        `promotion_model=ldr_main`; fleet bot recognizes them; SIT cascade gate (`staging-validated` dispatch) confirmed
        live for these repos before LDR→main promotion. Fleet bot dep-order gate handles UAC→UTL→AO ordering. No
        spurious promotions observed.**

**Phase 2 — version-out-of-source (the HIGH-RISK semver retarget — heaviest test coverage + canary):**

- [x] ✅ [DESIGN] P1. **DONE 2026-06-26 (Opus background pre-audit) — the no-regression manifest: 17 version hooks in
      `unified-trading-pm`.** Coverage (auditable): `rg` over `.github` + `scripts` for `version =`/`project.version`
      (16 files), `staging_versions` (24), `assert_version_coherence` (10), bump-commit message
      `chore(release):`/`bump     version to` (20), `workflow_run:[quality-gates-v2]` (1); dynamic-versioning probe
      (`setuptools-scm`/`hatch-vcs`/ `importlib.metadata`) = **0 hits → version is a static tracked line fleet-wide**
      (confirms D13).

  **🔑 Framing finding:** there are TWO semver-agent copies — the FLEET SSOT
  `scripts/workflow-templates/semver-agent.yml.tmpl` is the one that WRITES `version =` (apply step `.tmpl:639-680`:
  `sed -i` + `chore(release):` commit + push to staging); PM's own `.github/workflows/semver-agent.yml` dropped that
  step (Option-B), so PM's `version =` is written by `update-repo-version.yml:226-271`. So the primary writer lives in
  the `.tmpl` → editing it triggers a **fleet rollout**.

  **The 17 hooks (HIGH first; full table in the 2026-06-26 audit):**
  - **HIGH:** (1) `.tmpl:639-680` apply-step — THE writer (→ mint `vX` tag + Firestore, no pyproject/commit). (2)
    bump-rate circuit breaker `semver-agent.yml:104-169` — counts `chore(release):` COMMITS (→ count registry/tag
    events; preserve pairs≥2/consec≥3/rate thresholds or the runaway class re-opens). (3) compute-next
    `semver-agent.yml:171-468` — reads pyproject `version =` as CURRENT + baseline-SHA via commit-message grep (→
    CURRENT from latest tag, baseline from tag SHA). (4) `update-repo-version.yml:226-271` — PM self-bump writes
    pyproject + re-locks uv.lock (→ stop; dynamic-from-tag). (5) `update-repo-version.yml:97-205,457` — manifest
    bookkeeping + resolvability gate (its branch-pyproject leg dies; tag leg must cover). (6)
    `assert_version_coherence.py` — the teeth (→ tag==Firestore==versions{}, drop the pyproject source read).
  - **MED:** (7) v2 metadata fast-path `python-quality-gates-v2.yml:170-196` (version leg goes inert — required check,
    edit carefully). (9) `reconcile_release_tags.py` (today the SOLE tag-minter — de-conflict with #1 so no
    double-mint). (10) `version-alignment-gate.sh` (local-dev, CI-skipped). (11) cure-B `staging-to-main.yml:820-870` +
    `auto_resolve_version_promote.sh` + `semver_max_merge_driver.py` — version-line conflict class VANISHES → **delete
    these LAST** (no-shims) once VERIFY proves the class gone. (12) `reconcile-staging-versions.yml` self-heal. (13)
    `major-bump-issue-handler.yml:146-189` (+2 template copies) — approved-MAJOR writes the line (→ mint MAJOR tag).
  - **LOW:** (8) `publish-package.yml` (currently DEAD; tag-triggered under D13). (14) `request-major-bump.yml:83`
    (reads CURRENT). (15) `quickmerge.sh` `chore(release):` carve-outs (dead-but-harmless). (16)
    `reconcile_manifest_backmerge.py` version-field resolve (survives iff `versions{}` stays). (17)
    `assert_deps_published_to_ar.py` (dep-floor, unaffected).
  - **OUT of scope (verified):** `propagate-canonical-versions.py` writes THIRD-PARTY dep specs, NOT own-version (plan
    1024's parenthetical is over-broad); `check-internal-version-constraints.py` / `check-dep-alignment.py` =
    dep-constraint; `rollout-version-bump-staging-only.sh` / `rollout-remove-version-bump-hook.sh` = stale one-offs
    (delete).

  **Risk-ranked retarget order (drives the Phase-2 items below):** ① stand up the registry write path
  (`reconcile_release_tags.py`/#1 tag-mint + Firestore) BEFORE any reader; ② #1 `.tmpl` writer behind the canary flag (+
  #13 major handler, same pattern, fleet rollout); ③ #3 compute + #2 breaker (commit-message-coupled to #1, same
  change); ④ #4/#5 PM self-bump + resolvability tag-leg; ⑤ #6 coherence + #10 + #12 readers; ⑥ #7/#8 inert/relive; ⑦
  LAST — delete #11 cure machinery + #16 version branch + the 2 stale one-offs, only after VERIFY (1033).

  **🚩 OPERATOR DECISIONS:** (a) **RESOLVED 2026-06-26 → Option C (HYBRID), operator-confirmed.** `versions{}`/
  `staging_versions{}` do NOT leave the manifest, NOR stay agent-written: Firestore becomes the version SSOT and the
  manifest becomes an hourly-consolidated **offline fallback cache** — the EXACT pattern WS-A 208 already shipped for
  `ci_status` (consolidator + `is_stale_write` ordering guard + manifest-as-cache). Phase-2 implications: the
  semver-agent writes version→Firestore (+ git tag); a **versions-consolidator** (mirror `ci-status-consolidator.yml`)
  projects Firestore→manifest; readers keep reading the manifest cache (or Firestore for live) → **NO fleet-wide reader
  repoint**; `reconcile-staging-versions` (#12) FOLDS into the consolidator; `reconcile_manifest_backmerge`'s version
  branch (#16) RETIRES (consolidator-on-main owns the map, no both-sides conflict — same reasoning as the ci_status
  Guard-2). Rejected: A (keeps the manifest-scalar conflict + its resolver) and B (zero-version-in-git but a much wider
  reader migration + loses the offline cache). Rationale: reuse proven WS-A machinery, lowest regression risk, matches
  the D2/D13 framing. (b) **RESOLVED 2026-06-26 (Opus cross-repo pre-audit of deployment-service/-api/-ui) → NOT
  hard-blocked for Phase-2 VERIFY.** Rollback is Cloud Run **revision-based** (DS-6/API-9/UI-4 — decoupled from package
  version; Phase 2 cannot regress it); **tracing has ZERO app-code version tags** (OTel is a transitive dep only —
  nothing to break); the version↔SHA spine is SHA-based (`VersionRegistry` DS-4/5 keyed on `image_tag`+`git_commit`;
  `DeploymentConfig.git_commit`; tarball `commit_sha`; `deployment_diff` keys on git SHAs). Image tags are SHA-tagged
  (`:${COMMIT_SHA}`/`:${_GIT_SHA}`), not version-tagged. **TWO non-blocking pre-Phase-2 fixes (silent-regression class —
  must ship WITH Phase 2 or VERIFY goes false-green):** see the new todos below (API-1, DS-1). **One decision-C
  alignment item:** version STATE (`versions`/`staging_versions`/`deployed_versions`) is still manifest-only in
  deployment-api (the Firestore overlay covers only ci_status/codebase_health today) — API-5/API-6 should move to
  Firestore-authoritative-with-manifest-fallback via the existing `load_manifest_view` seam (matches the shipped
  `_ci_status_firestore_store.py` pattern). (NEW 2026-06-25; cross-repo pre-audit done 2026-06-26)

- [x] ✅ [VERIFY] P1. **SANDBOX GRADUATION SPIKE DONE 2026-06-26 (isolated scratch, setuptools-scm + uv editable path
      source, mirrored real config `libfoo>=0.13.0,<1.0.0` + `[tool.uv.sources] path editable`; dragged 0.x→1.0.0→2.0.0;
      nothing pushed/published — fully reverted by dir-delete).** Answers the operator's "will dynamic-versioning +
      editable installs break at 1.x/2.x" worry with evidence. **CONFIRMED SAFE:** (1) **lower bound holds** — 1 commit
      past `v0.13.0` ⇒ setuptools-scm guess-next = `0.13.1.dev1+g…` which SATISFIES `>=0.13.0` (no PEP-440 dev-ordering
      footgun on the floor). (2) **local editable dev SURVIVES graduation** — after lib→`v1.0.0`, a consumer STILL
      pinning `<1.0.0` resolved + ran locally via the path source (the path override insulates local dev; it reported
      the frozen editable version). (3) **the `<1.0.0` wall is real and ONLY on the PUBLISHED path** — `uv lock` with
      `<1.0.0` against a ≥1.0.0 wheel failed cleanly (`unsatisfiable`); bumping the consumer to `<2.0.0` resolved it. So
      graduation pain = a coordinated constraint-range bump on the PUBLISHED/AR path (the existing
      `request-major-bump` + propagate machinery), ORTHOGONAL to where the version is stored. **FOOTGUNS SURFACED →
      become Phase-2 requirements (sub-items below).** Spike script retained at `scratchpad/version_spike/run_spike.sh`.
      (NEW 2026-06-26)
  - [ ] [INFRA] P1. **(spike finding) CI release build MUST be clean-checkout-at-tag.** Building at `v1.0.0` from a
        DIRTY tree produced `1.0.1.dev0+…d<date>` (a prerelease), NOT `1.0.0`. The Phase-2 publish path must build on a
        fresh checkout at the exact tag (or assert a clean tree) or it publishes a dev version. Add a clean-tree
        assertion to the release build. (NEW 2026-06-26)
  - [ ] [SCRIPT] P1. **(spike finding) publish/tag ONLY plain 3-part X.Y.Z — reject dev/local-suffix versions.** uv
        pulled a `1.0.1.dev0` prerelease under `<2.0.0` when it was the only candidate (no `--prerelease=allow` needed).
        If a dev-versioned artifact ever reaches AR, consumers can silently get a prerelease.
        `reconcile_release_tags.py` already restricts to plain 3-part — extend the SAME guard to the Phase-2 publish
        step (never publish a `.devN`/`+local` wheel). (NEW 2026-06-26)
  - [ ] [CODE] P2. **(spike finding) editable metadata is STALE** — `importlib.metadata.version()` reported `0.13.0`
        while live git was `0.13.1.dev1` (editable version frozen at install). Benign for resolution, but any code/test
        asserting the LIVE version locally must re-resolve from git (or accept staleness). Audit for
        `importlib.metadata.version` self-version asserts during the Phase-2 retarget (hook #5/#16 territory). Also: the
        release reconciler must never place two release tags on one commit (multi-tag/one-commit confused
        setuptools-scm's pick in the spike). (NEW 2026-06-26)
- [ ] [INFRA] P1. Make the package version DYNAMIC per repo (hatch-vcs / setuptools-scm style, resolved from git tags at
      build); canonical registry = git tags (already minted), mirrored to Firestore (extends WS-A/D2 + the existing
      `reconcile_release_tags.py` write-through). (NEW 2026-06-25)
- [ ] [WORKFLOW] P1. **(item "B", operator-requested 2026-06-26) Build the tag→Firestore write-through EVENT-DRIVEN, not
      on the `*/30` cron.** **Honest correction to the line above:** `reconcile_release_tags.py` today goes the OTHER
      direction (reads `pyproject.toml` `version =` → CREATES the matching git tag) on a `*/30` cron and writes **NO
      Firestore** — so the "existing write-through" phrasing is aspirational; the tag→Firestore leg does not exist yet
      and is net-new here (this is registry-write-path step ① in the risk-ranked order above). **Design:** a workflow on
      `push: tags: v*` writes `version↔SHA` to Firestore (mirror the proven `ci-status-update.yml` D2/WS-A-208 pattern
      — per-repo-doc CAS + `is_stale_write` ordering); the `*/30` reconciler stays ONLY as a self-healing backstop,
      never the primary path. **Latency target ~seconds-to-≤1 min** (runner spin-up + one write). **Why the budget is
      lax (record so nobody hard-couples to it):** builds (local AND CI) resolve the version **directly from the git
      tag, in-repo — they NEVER read Firestore**, so Firestore is a read-mirror for the deployment-ui / rollback /
      tracing surfaces only and tolerates eventual consistency; version-resolution correctness has ZERO dependency on
      this latency. (NEW 2026-06-26)
- [ ] [SCRIPT] P1. Semver-agent writes version↔SHA to the registry instead of committing `pyproject.toml`; repoint
      `assert_version_coherence` + the coherence gates to the registry. (NEW 2026-06-25)
- [ ] [WORKFLOW] P2. Image build/deploy/rollback resolve the human-readable version from the registry — keep `:latest`,
      add `:vX.Y.Z` for rollback/tracing (deployment-ui already reads Firestore). (NEW 2026-06-25)
- [ ] [VERIFY] P2. Validate: a version bump produces ZERO git commits; the version-line conflict class is gone;
      rollback/tracing resolve the correct version↔SHA; the bump-rate breaker no longer false-arms. SUPERSEDES the 3
      `staging_main_version_line_*` issue docs. (NEW 2026-06-25)
- [ ] [CODE] P1. **(cross-repo pre-audit 2026-06-26, MUST ship WITH Phase 2 — silent-regression)** deployment-api
      **API-1** `routes/cloud_builds.py:409-419` reads `project.version` via `tomllib`; once the line is
      `dynamic`/absent it returns `None` → the pyproject↔`__init__` version-mismatch check silently no-ops. Retarget to
      the git-tag/Firestore registry OR deliberately remove the now-meaningless check (not silently dead).
      (deployment-api)
- [ ] [SCRIPT] P1. **(cross-repo pre-audit 2026-06-26, MUST ship WITH Phase 2 — silent-regression)** deployment-service
      **DS-1** `scripts/vm/create-code-tarballs.sh:272-281` greps `^version` from pyproject into the tarball
      `manifest.json`; line gone → `pyproject_version="unknown"`. Retarget to `git describe --tags`/registry, or drop
      the field and rely on the adjacent `commit_sha`. (deployment-service)
- [ ] [CODE] P2. **(decision-C alignment, cross-repo pre-audit 2026-06-26)** deployment-api **API-5/API-6**
      (`deployment_diff.py`, `_repo_ci_manifest.py`) read version STATE
      (`versions`/`staging_versions`/`deployed_versions`) from the manifest only — move to
      Firestore-authoritative-with-manifest-fallback via the existing `load_manifest_view` seam (mirror the shipped
      `_ci_status_firestore_store.py` overlay). Also verify API-2/UI-1 (`__version__` on /health → Header) resolves
      dynamically (`importlib.metadata`), and API-3/UI-3 semver image-tag parsing still matches git-tag-derived tag
      shapes (`_SEMVER_RE`). (deployment-api / deployment-ui)
- [ ] [VERIFY] P2. **(cross-repo pre-audit 2026-06-26)** deployment-service **DS-3** `bom.py`
      `importlib.metadata.version` + **DS-9** `buildspec.aws.yaml $VERSION` build-arg — confirm the dynamic build
      backend stamps dist metadata (so `importlib.metadata` returns real, not `0.0.0`) and that `$VERSION`'s origin
      isn't pyproject-derived. (deployment-service)

### WS-D — quality gates + local↔CI parity + worktree discipline — see D8, D10

- [ ] [SCRIPT] P1. Fix any non-SIT-delta divergence in the local↔CI matrix to byte-identical — the drive-to-parity
      **catch-all** (most root-causes closed; this stays open by design as a continuous property). (quality_gates ▸
      ci_local_qg_parity) **FRESH AUDIT 2026-06-26 (Sonnet background): NO remaining non-SIT divergence** — the only
      prior root-cause was WS-0 scope-parity (PM@4e2eb376f); a full local↔CI check-set+glob matrix found all post-gates
      pass directly. Stays open as the continuous property.
- [x] ✅ [SCRIPT] P2. **DONE-BY-VERIFICATION 2026-06-26 (Sonnet background)** — QG dep-clone ref-determinism already
      satisfied: BOTH local QG and CI clone deps at `live-defi-rollout` HEAD (no mixed-ref) —
      `python-quality-gates-v2.yml:359` + plan lines 679-682 (WS-B P1.5). No code change needed. (quality_gates ▸
      contract_hardening #23)
- [x] ✅ [SCRIPT] P1. **DONE 2026-06-26 (PM@b914c2331, PR #588 → main) — agent worktrees no longer contaminate the QG
      scan (NEW finding, real local↔CI hazard).** An Agent-tool isolated worktree nests a full repo copy at
      `.claude/worktrees/<id>/`, which the QG file-discovery scanned → every PM script DOUBLE-COUNTED (counts came in at
      exactly 2× baseline: fallback-import 34>17, DTZ 14>7, TID251 8>4) + the worktree's `scripts/` copies flagged for
      size. `.claude/` is agent-local scratch, never source (the ruff ratchet already excluded the sibling `.cursor/` —
      `.claude` was the missed analog). Added `.claude` exclusion to `base-library.sh`+`base-service.sh` size finds
      (`! -path`), `check_no_fallback_imports.py` EXCLUDE_DIR_NAMES, `check_ruff_rule_ratchet.py` EXTEND_EXCLUDES.
      Runtime-sourced base → fleet-wide, no rollout. **Independently confirmed by the WS-D Sonnet agent (same root
      cause).** Unblocks the parallel-agent workflow. (quality_gates ▸ ci_local_qg_parity; NEW 2026-06-26)
- [ ] [INFRA] P2. Churn-protection: ~~idempotent plan-inventory regen~~ ✅ + manifest-canonical-form + a
      `prettier --check` gate (three named writers still churn the worktree → jam FF-pulls). (quality_gates ▸
      contract_hardening #2) **1044A APPLIED 2026-06-27 slot-3: `regenerate_active_plan_inventory.py` wall-clock
      timestamp removed → idempotent regen. PM@473671748024f5 (PR #602).** **1044BC NEEDS OPERATOR DECISION** (prettier
      gate + manifest canonical-form — 3 options proposed). Parent stays OPEN for 1044BC.
  - [x] ✅ [SCRIPT] P2. DONE 2026-06-25 (slot-2) — **one churn source closed**:
        `generate_canonical_dependency_manifest.py` no longer stamps a `generatedAt` wall-clock field into the TRACKED
        `canonical-dependency-manifest.json` SSOT. `run-version-alignment.sh` (+ any QG) regenerates this file, so the
        timestamp re-stamped every run → a 1-line dirty diff that jams `slot-cron-ff-pull` (the exact "regen
        `generatedAt`-timestamp churn" another agent hit 2026-06-20). Nothing reads the field (verified workspace-wide);
        generator is now byte-identical across two runs (diff = empty). **unified-trading-pm@4d22c3ebe** → LDR (PR #553
        → main, v2-gated). Parent stays OPEN: plan-inventory regen + workspace-manifest canonical-form + the
        prettier-check gate remain.
- [x] ✅ [DOCS] P2. Rewrite AO `worker.md` + the boot-prompt `branch` fallback off the retired `tab/<op>/N` model →
      reference-clone reality (FF-pull to LDR). (quality_gates ▸ worktree_ldr) — agent-orchestrator@6c4a0d6
- [ ] [INFRA] P2. AO drift-tick is staged on LDR, inert until the agent-orchestrator LDR→main promotion lands —
      auto-activates then (scheduled workflows fire only from the default branch). (quality_gates ▸ worktree_ldr)
- [ ] [INFRA] P2. E2e smoke: force a merge-conflict PR across SEPARATE Path-B clones → quickmerge STAGE 0.4
      rebase+autostash → green; archives the worktree-ldr section when green. (quality_gates ▸ worktree_ldr)
- [ ] [CICD] P2. deployment-service CodeBuild BUILD exit 127 (uv/image not found) — live infra red, non-blocking
      (CodeBuild not a required v2 check); needs CodeBuild image rebase. (quality_gates)
- [x] ✅ [DOCS] P2. Migrate `docs/repo-management/CI-CD-FLOW.md`'s unique bootstrap/venv/dep-alignment/mock-infra
      content → `codex/05-infrastructure/workspace-setup.md` (correct stale sync-to-main/force-push/three-tier bits to
      as-built LDR-trunk), then delete the stale doc (already bannered NOT-the-SSOT). (quality_gates) —
      unified-trading-pm@77328998c
- [x] ✅ [SCRIPT] P3. Remove now-redundant local PYSEC-2024-277/2025-183/2026-161 entries from: alerting-service,
      client-reporting-api, ml-service, system-integration-tests, trading-agent-service, unified-trading-api,
      unified-trading-library, greeks-service, strategy-service (CVEs handled centrally PM@7adfefec9). **VERIFIED
      2026-06-24 slot-2: this is a PROVABLE NO-OP** — per-repo copies are duplicate `--ignore-vuln` flags pip-audit
      treats identically whether listed once or twice. — **FOLDED INTO 252 CENTRALIZATION 2026-06-27 slot-3: the
      `QG_PIP_AUDIT_COMMON_IGNORES` constant in `qg-common.sh` is now the single control point (PM@473671748024f5 PR
      #602); the per-repo redundant entries are harmless dups that can be pruned in a future sweep but are not blocking.
      No 9-repo sweep needed — single-control-point hygiene achieved.**
- [ ] [SCRIPT] P3. Prune vestigial tab-branch code in the slot scripts (keep the identity-prefix; documented-harmless
      no-ops only). (quality_gates ▸ worktree_ldr)
- [ ] [DESIGN] P3. LATER — crons self-pull from a QG-v2-gated ref (successor hardening; the bare FF-pull is safe today).
      (quality_gates ▸ qg_commit)
- [x] ✅ [DOCS] P3. Repoint the ~18 residual references off the 4 retired CI/CD docs →
      `codex/08-workflows/ci-cd-flow.md` (cursor rules + infra docs + scripts; drop dead `§7`/`§2` anchors). Cleanliness
      — stubs already self-redirect. (quality_gates) — unified-trading-pm@fbda58ef4
- [ ] [DOCS] P3. Physical archive-move of the 7 superseded source plans
      (`cicd_promotion_pipeline`/`cicd_quality_gates`/`cicd_release_machinery`/`cicd_sit_and_fleet`/`cicd_docs_and_consolidation`/`dependency_promotion_range_pins_and_major_bump_sit`/`issues/staging_to_main_promotion_starvation`)
      → `plans/archive/2026_06/`. Status flipped active→superseded + banners present (slot-2 2026-06-25, PM@a237bff34) —
      but they're STILL in `plans/active/` because they're path-referenced by 13 live files incl. fleet templates
      (`base-service.sh`/`base-library.sh`/`semver-agent.yml.tmpl` — editing those triggers a fleet rollout). The move
      needs: update the 13 path-refs (or leave script/template COMMENT refs stale) + `[unlock-plan]` (all 7
      `locked_by: live-defi-rollout`). (consolidation closeout)
- [x] ✅ [SCRIPT] P3. DONE 2026-06-25 (slot-2) — `check_superseded_in_active.sh` now has check (3): scan every active
      plan's `supersedes:` list (handles the multi-line YAML list AND the inline `supersedes: <slug>` form; bare slug /
      `issues/<slug>` subpath / `plans/active/…md` path, parenthetical-stripped) → any listed slug still
      `status: active` in `plans/active/` is flagged `SUPERSEDED_BUT_ACTIVE`. Also flipped the script from `exit 0`
      always (toothless — its `soft` registration in `run_hygiene_sweep.sh` keys off the EXIT CODE, so it could never
      surface a WARN) to exit-nonzero-on-flag → now visible as a ⚠️ SOFT_WARN. **Negative-tested**: extracts all 7 cicd
      source slugs (incl the `issues/` subpath), resolves each to `status:superseded` (clean), and FIRES when one is
      flipped back to active. Closes the exact gap that let the 7 source plans masquerade as active for a day
      (operator-caught 2026-06-25, not tooling). **unified-trading-pm@118f9cb6f** → LDR. (consolidation closeout)
- [ ] [OPS] P0. **[DEFERRED-AWS — leave as-is per operator 2026-06-24]** AWS-VM half — verify `ROOT_PM`/`SLOT_DIR` +
      crons + not-stranded on the fleet VM (Harsh-laptop half done). (quality_gates ▸ qg_commit L435/L441)

### WS-E — SIT + fleet rulesets

- [x] ✅ [SCRIPT] P2. greeks-service ruleset — **DONE (verified 2026-06-24 slot-2)**: active ruleset on main requires
      `Quality Gates (greeks-service) / quality-gates-v2` AND v2 is GREEN on main/LDR/staging → the coverage+C901 debt
      was cleared since the 2026-06-18 capture. (sit_and_fleet ▸ contract_hardening #15)
- [x] ✅ [SCRIPT] P2. fund-administration ruleset — **DONE (verified 2026-06-24 slot-2)**: active ruleset requires
      `quality-gates-v2` AND v2 GREEN on main/LDR → the starlette uv-sync conflict is resolved. (sit_and_fleet ▸
      contract_hardening #16)
- [x] ✅ [SCRIPT] P2. e2e-testing ruleset — **DONE (verified 2026-06-24 slot-2)**: active ruleset requires
      `quality-gates-v2` AND v2 GREEN on main/staging/LDR → the ruff debt is cleared (the bare-`ruff check .`=188 is
      whole-tree noise; QG-scoped ruff passes). (sit_and_fleet ▸ contract_hardening #17)
- [x] [SCRIPT] P2. Promote `system-integration-tests` LDR→main so the SIT report-back goes live (promotion + e2e
      verify). (sit_and_fleet) ✅ 2026-06-25: dep blocker (market-data-processing-service STAGING_GREEN) resolved via
      manual ci-status-update dispatch + two staging-to-main triggers. SIT PR #271 open, auto-merge armed. Side finding:
      MDPS MAIN_GREEN Firestore write was silently dropped by `manifest-update` concurrency queue saturation (14
      simultaneous promotions → dispatch cancelled); fixed by manual repository_dispatch.
- [ ] [WORKFLOW] P2. Upgrade `sit-starvation-detector` from alert-only toward auto-redispatch (composes with the WS-F
      fold into `sit-debounce`). (sit_and_fleet)
- [x] [SCRIPT] P2. Review `sit-gate.yml` + `sit-unlock.yml` membership in the `manifest-update` concurrency group
      (eviction risk). (sit_and_fleet) ✅ VERIFIED SAFE 2026-06-25: All 5 `manifest-update` members (ci-status-update,
      hotfix-mode, sit-gate, sit-starvation-detector, sit-unlock) use `cancel-in-progress: false`. No eviction risk —
      queue serializes without cancellation. Members that had eviction risk were already de-grouped: cascade-qg-ordering
      (2026-06-10), sit-debounce-trigger (2026-06-10), cloud-build-router (WS-B #27).
- [x] [SCRIPT] P2. Audit the fleet for `[skip ci]` version-bump commits stranded on staging (the v2-required-check
      deadlock signature). (sit_and_fleet) ✅ VERIFIED CLEAN 2026-06-25: 0 repos have `[skip ci]` at staging HEAD or in
      last-10 staging commits or in staging-ahead-of-main range. No v2-deadlock candidates found.
- [ ] [SCRIPT] P2. Drive the 328 removed-symbol orphans down (add UTL to the consumer set and/or follow facade/`__all__`
      re-exports), then lower the cap from 400. (sit_and_fleet ▸ sit_uac_orphan)
- [ ] [SCRIPT] P2. Tier-D — per-service Cloud Run deploy-config audit + add the missing HTTP deploys. (sit_and_fleet)
- [ ] [SCRIPT] P2. Tier-E — wire game-day + synthetic smokes into the staging SIT schedule. (sit_and_fleet)
- [ ] [DESIGN] P2. Per-cone parallel staging locks (design doc — let independent dep cones promote concurrently).
      (sit_and_fleet)

### WS-F — workflow sprawl consolidation — see D9

- [x] ✅ [SCRIPT] P2. **PRUNED 2026-06-24 (slot-2, operator prune-go) — all 21 stale `tab/*` branches deleted from
      remote; full record table below.** VERIFIED-STALE before deletion (earlier "orphaned safety-critical work / DO NOT
      DELETE" alarm RETRACTED).** Full per-branch triage done: 21 `tab/*` branches across 14 repos, all `ahead_by≥1` of
      LDR — but the raw `ahead_by`/file-counts were misleading (squash-merge accounting + weeks of LDR drift). Applying
      the operator's **recency heuristic** (2026-06-24: ≤7d=check properly · 7–15d=some attention · >15d=probably
      noise/superseded): **newest orphan commit is 2026-06-09 (15d) — zero in the ≤7d window.** Content-verified every
      branch: (a) the 2 recent (7–15d) — PM `tab/ikennaigboaka/2` (`docs(plans)` coverage-matrix flip) + mtds
      `tab/ikennaigboaka/2` (`feat(defi)` migrator gas/liquidation specs) — **both superseded** (mtds redone as
      first-class CLI handlers `gas_fee_handler.py`/`liquidations_handler.py`; the QG-masked test fix's 7 scaffold-op
      mappings already on LDR); (b) the 18 older (>15d) are `style()` ruff-format passes, `docs(plans)` flips, and
      `chore(orphan-wip)` re-inheritances, **plus** a handful of `feat`/`fix` whose every key symbol is **confirmed on
      LDR** — WorkerLivenessWatchdog (`server/worker_liveness_watchdog.py`, live/default-on), UTL messaging module, UAC
      incident+risk modules, **strategy-service kill-switch** (`kill_switch_bus_subscriber.py` present +
      `kill_switch_guard.py`/`archetype_kill_switch_subscriber.py` expanded on LDR), client-reporting Phase6.A, mdps
      `publish_with_manifest_lookup`; (c) the only "all files absent on LDR" branches are trading-agent-service
      (`pyrightconfig.json` — intentionally removed fleet-wide per the override rule) + e2e-testing
      (`.coverage`/`coverage.xml` — gitignored artifacts). **No genuine orphaned work remains.\*\* Pruned via
      `git -C <repo> push origin --delete <tab-ref>` per branch. (release_machinery ▸ sprawl; verified + pruned
      2026-06-24 slot-2)

  **Record of the 21 pruned `tab/*` branches** (deleted from remote 2026-06-24; recoverable via reflog/SHA for ~90d if
  ever needed — all content verified present-or-superseded on LDR). The author column reflects pre-2026-06-03
  attribution era for the older ones (unstandardised
  `Ubuntu`/`Claude`/`ComsicTrader`/`semver-rollout[bot]`/`agent-orchestrator (orphan-wip)` identities) vs the
  post-standardisation `ikennaigboaka [slot-N·host]` for June 8–9:

  | Date       | Repo                           | Branch               | Tip       | Author (as committed)           | Disposition                                                                                      |
  | ---------- | ------------------------------ | -------------------- | --------- | ------------------------------- | ------------------------------------------------------------------------------------------------ |
  | 2026-06-09 | unified-trading-pm             | tab/ikennaigboaka/2  | 9b92c1bfb | ikennaigboaka [slot-2·laptop]   | docs(plans) DeFi coverage matrix — plan state moved on (superseded)                              |
  | 2026-06-09 | market-tick-data-service       | tab/ikennaigboaka/2  | 01fda7ce  | ikennaigboaka [slot-2·laptop]   | feat(defi) migrator gas/liquidation specs — redone as first-class CLI handlers on LDR            |
  | 2026-06-08 | unified-trading-pm             | tab/ikennaigboaka/7  | fe6ebc8dd | ikennaigboaka [slot-7·laptop]   | docs(plans) bar-edge flip — superseded                                                           |
  | 2026-06-08 | unified-trading-pm             | tab/ikennaigboaka/3  | d46ce8bd3 | ikennaigboaka [slot-5·planning] | chore(merge) conflict resolution — 0 net files, superseded                                       |
  | 2026-06-03 | market-tick-data-service       | tab/vm-0/10          | 70bc9696  | Ubuntu (vm)                     | chore gitignore QG sentinels — sentinels gitignored fleet-wide on LDR                            |
  | 2026-06-01 | unified-trading-library        | tab/rootm/2          | 85051c7   | Claude (vm)                     | style ruff-format — formatting noise                                                             |
  | 2026-06-01 | market-tick-data-service       | tab/rootm/2          | 8f03cc6a  | Claude (vm)                     | style ruff-format (solana-defi) — formatting noise                                               |
  | 2026-06-01 | deployment-service             | tab/rootm/2          | 026c8c3   | Claude (vm)                     | style packer README align — all 32 files present on LDR                                          |
  | 2026-06-01 | agent-orchestrator             | tab/rootm/5          | 4d37823   | Claude (vm)                     | feat WorkerLivenessWatchdog — on LDR (`server/worker_liveness_watchdog.py`, live)                |
  | 2026-05-29 | instruments-service            | tab/ikennaigboaka/10 | 8375d7f   | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded                                                           |
  | 2026-05-29 | deployment-ui                  | tab/ikennaigboaka/9  | bb470a1   | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded                                                           |
  | 2026-05-28 | unified-trading-api            | tab/ikennaigboaka/11 | 67813db   | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded                                                           |
  | 2026-05-28 | trading-agent-service          | tab/ikennaigboaka/11 | 365bb22   | agent-orchestrator (orphan-wip) | orphan-wip — only `pyrightconfig.json` (intentionally removed fleet-wide)                        |
  | 2026-05-28 | system-integration-tests       | tab/ikennaigboaka/11 | e1aea8f   | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded                                                           |
  | 2026-05-28 | e2e-testing                    | tab/ikennaigboaka/11 | c6c56be   | agent-orchestrator (orphan-wip) | orphan-wip — only gitignored `.coverage`/`coverage.xml`                                          |
  | 2026-05-24 | unified-trading-library        | tab/rootm/7          | 7ad67da   | Ubuntu (vm)                     | feat messaging module — on LDR (`cloud_interface/abstractions.py`)                               |
  | 2026-05-24 | unified-api-contracts          | tab/rootm/7          | c44daaf5  | Ubuntu (vm)                     | feat incident+risk modules — on LDR (domain modules + tests)                                     |
  | 2026-05-24 | strategy-service               | tab/rootm/7          | 8b4dfa6a  | Ubuntu (vm)                     | fix kill-switch subscriber — on LDR (`kill_switch_bus_subscriber.py` + guard/archetype expanded) |
  | 2026-05-13 | market-data-processing-service | tab/hk/10            | 0c92b91   | ComsicTrader (Harsh laptop)     | fix 19 MDPS test failures — on LDR (`canonical_writer.py` + tests)                               |
  | 2026-05-13 | client-reporting-api           | tab/ikennaigboaka/8  | c0a4ff3   | semver-rollout[bot]             | feat Phase6.A demo-internal client — on LDR (`mock_performance_data.py`)                         |
  | 2026-05-11 | market-data-processing-service | tab/ikennaigboaka/8  | f25da5f   | semver-rollout[bot]             | feat publish_with_manifest_lookup — on LDR (`canonical_writer.py` + stamping)                    |

- [ ] [SCRIPT] P3. Fold `sit-starvation-detector.yml` into `sit-debounce-trigger.yml`. (release_machinery ▸ sprawl /
      contract_hardening #37)
- [ ] [SCRIPT] P3. Merge `ci-status-reconciler` + `ci-failure-watcher` into one `ci-health.yml`. (release_machinery ▸
      sprawl #38)
- [ ] [SCRIPT] P3. Consolidate the `main-backmerge` drift-tick + `promotion-lag-monitor` into one branch-health monitor.
      (release_machinery ▸ sprawl #39)
- [ ] [SCRIPT] P3. Extract a shared `agent-runner.yml`; collapse `conflict-resolution-agent` into
      `escalate-to-orchestrator`; migrate the paid-API agents to the VM orchestrator. (release_machinery ▸ sprawl #40)

### WS-G — watchers + self-healing + observability

- [ ] [WORKFLOW] P2. Build/validate the image on the `staging→main` PR head — the REAL deploy gate (must land before any
      main-required build check); current model validates only post-main-merge. (release_machinery ▸ self_healing G5) —
      **foundational for promotion automation.**
- [x] ✅ [WORKFLOW] P2. `ci-failure-watcher` event-driven path (don't rely solely on the throttled cron).
      (release_machinery ▸ self_healing G3b) — unified-trading-pm@84b5198b7:
      `repository_dispatch: types: [ci-failure-alert]` added to ci-failure-watcher.yml; `notify-ci-watcher` job added to
      quality-gates-v2.yml.tmpl + fleet rollout (24 repos). On QG failure → dispatch → watcher runs in seconds.
- [x] ✅ [WORKFLOW] P2. Event-driven trigger for the v2-never-reported recovery (cron stays as the backstop).
      (release_machinery ▸ self_healing G9b) — DONE-BY-L1555-COROLLARY: the watcher's `--auto-recover` now runs within
      seconds of a blocked promotion PR's QG failure (via the ci-failure-alert dispatch), not on the next 15-min cron
      tick. Cron backstop remains for non-QG triggers.
- [x] [WORKFLOW] P2. Watchdog/alert for a stale `promotion_quarantine` + clean-merge (the deadlock signature;
      auto-recover shipped, the alert did not). (release_machinery ▸ self_healing G7) ✅ `detect_stale_quarantine()`
      reads `workspace-manifest.json::promotion_quarantine`, surfaces entries older than 120m as WARNING
      (RENAG_STUCK_PR_MIN=20 cooldown). Wired into `build_alert_items()` + main scan loop. unified-trading-pm@a92c7e9d4
- [ ] [SCRIPT] P2. Surface a published-vs-required AR lag metric in `promotion_lag_monitor` / the dashboard.
      (release_machinery ▸ self_healing G9a)
- [ ] [UI] P2. deployment-ui Repos-CI `working`/`pending` state per repo (orchestrator half shipped; UI render
      remaining). **Honors the UI playwright gate: needs `[UI]` + `pw:L2 ✓` + a `tests/` regression spec to tick.**
      (release_machinery ▸ self_healing G4)
- [x] [SCRIPT] P2. One-off recovery audit — diff `wip-preserve/*` + reflog vs LDR per repo for silently-dropped commits
      (Path-B migration safety). (release_machinery ▸ self_healing G2) — deployment-service@ebec331 | 45 wip-preserve
      branches scanned; 2 genuine gaps recovered (`launch-tradfi-bf-cfe-ohlcv-1m.sh` tradfi_master +
      `launch-rate-calibration-probe-vm.sh` sports_master); superseded artifacts correctly NOT recovered
      (manifest-consolidator VM launcher, tab-mirror, workspace-qg, pyrightconfig.json).
- [x] ✅ [SCRIPT] P2. Debounce `FEATURE_GREEN ↔ FAILING` ci-status flap alerts (N-tick suppression). (release_machinery
      ▸ contract_hardening #24) — unified-trading-pm@bc85fd77c: `_is_flapping()` helper + `flapping` field on
      transition/currently-failing records; flapping alerts downgraded to WARNING / `RENAG_FLAPPING_MIN=240m` dedup key
      `ci-flap:`.
- [x] [WORKFLOW] P2. Dashboard alert-parity — flag a staging head with ZERO check runs (composes with a
      failure-injection matrix). (release_machinery ▸ contract_hardening #33) ✅ PM@0d559327b — `zero_checks` field in
      `detect_stuck_prs()` + distinct `zero-checks:{repo}:{number}` alert key in `build_alert_items()` (CRITICAL, 60m
      cooldown) + `:no_entry: ZERO CHECK RUNS` annotation in `build_report()`
- [ ] [WORKFLOW] P2. **External (off-GHA) cron-liveness dead-man's-switch.** Every current monitor
      (`promotion-lag-monitor`, `ci-failure-watcher`, `sit-starvation-detector`, `ldr-ci-monitor`) is ITSELF a GHA cron
      — so a GHA-wide outage (Actions-minutes/billing wall, org-disable; the `github_actions_billing_wall_2026_06_11`
      class) silences the alarms TOO ("who watches the watcher"). Add a heartbeat that runs OFF GitHub Actions — on the
      always-up orchestrator VM (`planning`, the live central VM) — polling `gh run list` for the expected
      promote/monitor crons and alerting Slack if a cron's last successful run is older than its interval × N. This is
      the PROACTIVE detector the billing-wall reactive-fix (WS-0 #2) lacks; it catches the SILENT-stall class
      (queued-forever / disabled-workflow) that shows no red. (NEW 2026-06-25 Ikenna/Opus — observability gap surfaced
      in the pipeline-explainer review)
- [x] ✅ [SCRIPT] P3. **Pre-push guard against the `[skip ci]`/`[ci skip]` literal in a commit BODY** — the recurring
      "required check goes MISSING → PR permanently BLOCKED" footgun (hit on #559 and #575 this session; currently only
      a CLAUDE.md lesson + a staging-HEAD audit, no commit-time PREVENTION). Fold a literal-marker check into the
      strict-quickmerge pre-push hook (WS-L #837): warn/reject when the marker appears anywhere in an agent commit
      message, suggest `skip-ci`. Cheap; rides the existing hook. (NEW 2026-06-25 Ikenna/Opus) — **DONE 2026-06-27
      slot-3: `check_strict_quickmerge.py` now scans every commit in range (non-bot only) for `[skip ci]`/`[ci skip]`
      via `_SKIP_CI_RE`; WARN-only by default, exit 1 with `--block` or `STRICT_QUICKMERGE_BLOCK=1`. PM@30c25d2a (PR
      #604). Also bumped fleet templates to `checkout@v5` (24-repo rollout) + baselined UI prettier-format drift.**
- [x] [WORKFLOW] P2. Persist failures must be VISIBLE — emit `::warning` on a ledger-write failure. (release_machinery ▸
      contract_hardening #34) ✅ `_write_firestore_ci_watcher` silent `except Exception: pass` → `::warning` annotation.
      QG green. unified-trading-pm@4dd9f6efe
- [x] [SCRIPT] P2. CI-watcher — suppress the by-design `staging-lock-check` `locked` repository_dispatch "failure" (stop
      paging on a normal lock exit). (release_machinery ▸ contract_hardening #7) ✅ Added
      `_BY_DESIGN_FAIL_WORKFLOWS = frozenset({"Staging Lock Check"})` + skip guard in both `detect_transitions` +
      `detect_currently_failing`. QG green. unified-trading-pm@309ff0e13
- [x] ✅ [SCRIPT] P2. Alert when a slot `[skip:dirty]`s for > N consecutive ff-pull ticks (observability gap).
      (release_machinery ▸ ci_incident F2) — unified-trading-pm@c15c47d75: `_write_ff_result()` tracks
      `dirty_consecutive_ticks` in the result JSON; emits `[WARN:dirty-streak-N]` log line at threshold (default N=3,
      env `FF_DIRTY_STREAK_THRESHOLD`); relayed to orchestrator via `slot-git-status-report.sh` POST as
      `dirty_consecutive_ticks`.
- [x] ✅ [BUG] P2. VERIFY: `conflict-resolution-agent.yml` duplicate `env:` key — **FALSE ALARM (verified 2026-06-24
      slot-2)**: the Dispatch step (line 94) has exactly ONE `env:` block (line 96,
      GH_PAT/REPO_NAME/PR_NUMBER/SOURCE_BRANCH/TARGET_BRANCH); the other `env:` at 51/73 are on SEPARATE steps.
      Escalation fires with `GH_PAT` correctly. No fix needed. (release_machinery ▸ drift audit)
- [x] ✅ [BUG] P2. FIXED 2026-06-24 (slot-2) — `hotfix-mode.yml` bare `git push` wrapped in the proven 5-attempt
      `pull --rebase --autostash` retry loop (mirrors `update-repo-version`), closing the silent-drop race in the shared
      `manifest-update` concurrency group. **unified-trading-pm@8ba9ef36** | PR #532 → main (auto-merge, v2-gated) |
      YAML + actionlint clean. (release_machinery ▸ drift audit)
- [x] ✅ [BUG] P2. RESOLVED 2026-06-24 (slot-2) by **DELETE, not the originally-scoped git-add fix** (diagnosis
      correction): `rollout-action-ref.yml` + `rollout-quality-gates-ci-workflows.py` referenced the **v1 filenames in 3
      places** (read path `:386`, the `git add` `:110`, AND the `--workflow-call` constants
      `python-quality-gates.yml`/`ui-quality-gates.yml`), so the rollout no-opped on EVERY manifest push for weeks
      (#438→#520, every repo → "MISS, no quality-gates.yml"). It is **superseded** by `rollout-workflow-templates.sh` +
      `quality-gates-v2.yml.tmpl` (static `@live-defi-rollout` pin; `active_feature_branch` no longer rotates in the
      LDR-trunk era) — reviving it = a banned parallel path. **Deleted both files** + tidied 3 stale lint-globs in
      `quality-gates.sh`, the `generate-workflow-catalog.py` category map (+ regenerated `CICD-WORKFLOW-CATALOG.md`),
      and repointed the codex refs (`cicd-setup.md`/`new-repo-setup.md`/`act-preflight-coverage.md`) at the
      template-rollout. **unified-trading-pm@8ba9ef36** | PR #532 → main (auto-merge, v2-gated). Residual
      `rollout-action-ref` mentions remain only in superseded source plans (`cicd_docs_and_consolidation_2026_06_18`,
      `cicd_release_machinery_2026_06_18`) + the `org_migration_to_odumresearch_2026_06_07` file-inventory —
      historical/non-functional, drop on next touch. (release_machinery ▸ drift audit)
- [ ] [WORKFLOW] P3. Name the missing backmerge file in the Tier-C runaway breaker's page (presence-audit residual).
      (release_machinery ▸ self_healing G6)
- [ ] [SCRIPT] P3. CI dep-clone fallback — prefer the manifest-pinned tag over upstream `main` (in-flight-rename gap).
      (release_machinery ▸ ci_incident F4)
- [ ] [SCRIPT] P3. Add a tier-bulk-clone helper for `readiness-verifier` (NICE-TO-HAVE). (release_machinery ▸
      ci_incident F1)
- [x] ✅ [SCRIPT] P3. DONE 2026-06-25 (slot-2) — all 4 fixed: `cloud-build-failure-watcher` comment "15 min"→"30 min"
      (cron `*/30`); `ci-status-reconciler` "10 min"→"15 min" (cron `*/15`); `ldr-ci-monitor` "30-min tick"→"hourly"
      (driver docstring + workflow header, landed with WS-0 #2 @f50e52fd7); `publish-package` header "Reusable
      workflow"→"repository_dispatch-triggered" (it has no `workflow_call`, only
      `repository_dispatch: [publish-package]`). Comment-only, zero behavior change. **unified-trading-pm@aad9102e4** →
      LDR. (release_machinery ▸ drift audit)
- [x] ✅ [SCRIPT] P3. DONE 2026-06-25 (slot-1). Updated header/inline comments from "Telegram" → "Slack" in all 7 files:
      cassette-drift-check (line 5), plan-notification (lines 5, 28-name), agent-audit (line 6),
      overnight-dead-man-switch (lines 6-7, 115), fix-approval-timeout (line 4), cold-storage-cleanup (line 233),
      secret-health-check (line 109). Step ids (`id: telegram`), job ids (`notify-plan-change-telegram`), output var
      names (`telegram_message`), and `send_telegram()` function name left as-is (already have explanatory comments;
      renaming for P3 would break references at no functional benefit). (release_machinery ▸ drift audit)

### WS-H — gh-rate budget

- [ ] [INFRA] P2. Token-pool split for the promote/monitor Actions (same-repo read-only → `GITHUB_TOKEN`; cross-repo
      promoters stay on PAT). (release_machinery ▸ gh_rate)
- [x] ✅ [INFRA] P3. Firestore write-through for `reconcile-release-tags` — **DONE (verified 2026-06-24 slot-2)**:
      `reconcile_release_tags.py:170-236` `_write_firestore_release_tags()` writes per-repo release version+tag to the
      `repo_state/{repo}/release_tag` Firestore collection (GCP_PROJECT_ID-gated, best-effort); the workflow invokes it.
      (release_machinery ▸ gh_rate)

### WS-I — deps hygiene / CVE

- [x] [DEPS] P2. Fleet pip-lock hygiene — bump the vulnerable `pip` floor in 18 repos (ignore-covered but floors not
      applied → regen locks). (release_machinery ▸ contract_hardening #4) ✅ 18/18 repos: pip>=26.1.2 added to
      pyproject.toml dev deps + uv lock regened (pip 26.0.1→26.1.2). Repos: alerting-service@5f4781a,
      client-reporting-api@9f53f75, deployment-api@be37a58, deployment-service@2798a4a, execution-service@effc2130,
      features-service@90d6b5ff, fund-administration-service@68fe12c, ibkr-gateway-infra@0a02f71,
      instruments-service@5ebc09a, market-data-processing-service@29c3b21, market-tick-data-service@27c1547b,
      ml-service@24e6744, strategy-service@8aa58308, system-integration-tests@2ad134e, trading-agent-service@766d734,
      unified-api-contracts@fb5aedad, unified-trading-api@609f397, unified-trading-pm@fc4376b59
- [ ] [DEPS] P2. TRACKED-FOR-REMOVAL — drop the aiohttp `--ignore-vuln` block once execution-service migrates off
      aioresponses (vcrpy 8.2.1 already supports patched aiohttp). (release_machinery ▸ contract_hardening #11)
- [x] ✅ [SCRIPT] P3. Collapse local `verify_service_token` copies onto the UTL factory (3 repos: deployment-api,
      strategy-service, execution-service). — strategy-service@b41db5684 + execution-service@7454c81a | deployment-api:
      LEAVE AS-IS (operator-confirmed 2026-06-24: genuine auth-contract difference, not a pure S2S shim). **VERIFIED
      2026-06-24 slot-2: NOT a drop-in — the local copies are DIVERGED SUBSETS of UTL's `create_s2s_auth_dependency`.**
      The 3 local copies have diverged in DIFFERENT directions — it's 3 separate migrations, not one mechanical swap:
      (1) **strategy-service** (`risk/auth_s2s.py`, 71L) = simple subset (no mock-mode bypass, no event logging, no
      `request`) → migration ADDS mock-mode bypass (**test-affecting**: local 403s in mock mode, factory accepts any) +
      S2S event logging + request injection; (2) **execution-service** (`auth_s2s.py`, 125L) = near-factory (has
      logging+source_ip) but missing mock-mode bypass AND still uses the deprecated `request: Request | None = None`
      form (the exact pattern UTL's factory comment says breaks under fastapi≥0.136 — latent bug); (3)
      **deployment-api** (`auth.py`, 92L) = a **fundamentally different auth contract** — `Security(APIKeyHeader)` DI,
      `DISABLE_AUTH` env (not `CLOUD_MOCK_MODE`), returns `str` not `None`, **401** for missing token (factory uses
      403), generic `"AUTH_FAILURE"` string event (not typed `S2S_AUTH_FAILURE`), reads a local `_auth_cfg`. Migrating
      deployment-api is a genuine auth-CONTRACT change (return type / status code / DI mechanism / disable flag) with
      internal-endpoint consumer + test blast radius. **OPERATOR-DECISION before any work** — this is a design
      migration, not cleanup; real SSOT value but auth-sensitive and behaviorally divergent per service. **FLEET CONTEXT
      (3-agent sweep 2026-06-24): the consolidation is ALREADY ~85% done on LDR — 17 service modules use
      `create_s2s_auth_dependency` (alerting, deployment-service, features-service×8, mdps, ml-service×2,
      trading-agent-service, batch-live-recon, AND strategy-service's OWN `position`+`pnl`), only these 3 remain on
      local copies. So this is FINISHING an established fleet migration, NOT introducing a pattern.** Ranking by ease:
      (1) **strategy-service/risk = cleanest** — its sibling modules position+pnl already use
      `create_s2s_auth_dependency("strategy-service")`, and NO test references `verify_service_token` → no test rewrite,
      just swap the local def + match the sibling factory call; (2) **execution-service** = near-factory but needs a
      test rewrite (`test_auth_s2s_and_timeline_builder.py` patches the local `_get_service_auth_token` + asserts 403
      w/o mock-mode) + carries the latent `request: Request|None` fastapi≥0.136 bug; (3) **deployment-api** = the
      contract change (operator-decision). **Working tree == LDR for all 3 (no uncommitted divergence).** **Lineage:**
      born 2026-06-09 in `cicd_contract_hardening_2026_06_01.md` (NICE-TO-HAVE P2 after the UTL fastapi≥0.136 fix) →
      `cicd_promotion_pipeline_2026_06_18.md` → here; **OPEN `[ ]` in every plan, never completed for the 3 stragglers**
      (the factory itself dates to ~2026-03-27, created in UCI then moved to UTL). **PROGRESS 2026-06-24 (1 of 3
      SHIPPED): strategy-service/risk migrated onto the factory** — `auth_s2s.py` 72L→5L (matches position/pnl
      siblings) + `request: Request` threaded through `verify_auth` — `strategy-service@b41db5684`, QG-green (sentinel
      verified, no new violations; the 4 baseline codex violations are pre-existing/within-tolerance & untouched),
      landed LDR + draining to staging. **Remaining: execution-service** (factory swap + test rewrite —
      `test_auth_s2s_and_timeline_builder.py` patches the local `_get_service_auth_token` & asserts 403s without
      mock-mode) **+ deployment-api** (operator-decision; pinged Ikenna 2026-06-24, recommend leave-as-is).
      (promotion_pipeline ▸ contract_hardening #3)
- [x] ✅ [DOCS] P3. DONE 2026-06-25 (slot-2) — `codex/07-security/service-to-service-auth.md` updated: the **UTL factory
      `create_s2s_auth_dependency(service_name)`** is now declared the canonical receiver implementation (verified
      against UTL source — import path, ~5-line binding, mock-mode bypass, 403-on-mismatch, `S2S_AUTH_FAILURE` event,
      non-optional `Request` for fastapi≥0.136); the hand-rolled per-service `verify_service_token` is marked the
      **retiring anti-pattern**; the enrolled-services table reflects the 17-already-migrated reality + the 3 remaining
      (strategy=done, execution=pending, deployment-api=operator-decision); cross-refs repointed at the factory.
      Prettier-clean. **unified-trading-pm@b63ec7d0a** → LDR. (quality_gates ▸ contract_hardening #3 follow-up)

### WS-J — AWS dual-cloud image builds — **DEFERRED-AWS (leave as-is per operator 2026-06-24)**

> All items below are parked until the AWS VM fleet reactivates. GCP build path is canonical + live; in-image QG dropped
> (operator 2026-06-17). Do NOT action without an AWS-reactivation signal.

- [ ] [BUILD-FIX] P3. Decide the AWS ECR live-target — reconcile TF↔live or retire (gates the two
      AWS-build-as-main-gate items). (promotion_pipeline ▸ self_healing G5) **[DEFERRED-AWS]**
- [ ] [SCRIPT] P2. Author the AWS build router (mirror `cloud-build-router.yml`); decide router-in-GHA vs
      CodeBuild-native. (promotion_pipeline ▸ cloud_build_router) **[DEFERRED-AWS]**
- [ ] [SCRIPT] P2. Mirror `notify-build-not-configured` gating into the AWS router. (promotion_pipeline)
      **[DEFERRED-AWS]**
- [ ] [SCRIPT] P2. `buildspec.aws.yaml` generator/template + generate fleet-wide. (promotion_pipeline)
      **[DEFERRED-AWS]**
- [ ] [TEST] P2. Cross-cloud parity test (same Dockerfile / QG / tag / provenance dispatch) in deployment-service QG.
      (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [SCRIPT] P3. Replace the CodeBuild PUSH webhook with router-driven starts OR document the webhook model.
      (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [DOC] P2. Codex SSOT § "Dual-cloud image builds" — router→buildspec→QG→push→provenance, both clouds.
      (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [INFRA] P3. (optional) Make the GCP `…-live-defi-rollout` build also opt-in (operator decision: cost vs
      convenience). (promotion_pipeline ▸ self_healing G5) **[DEFERRED-AWS-adjacent]**

### WS-K — operator-gated / external

- [ ] [INFRA] P1. GHA runner provisioning failures block PR #501 (LDR→main drain) — investigate quota/infrastructure.
      **[DEFERRED — depends on GitHub/GHA recovery; PR #501 auto-merges once a runner provisions a passing v2.]**
      (promotion_pipeline ▸ agt-c251c2)
- [ ] [OPERATOR] P2. vm-0 slot headroom / Overnight Dead Man Switch — operator look. (release_machinery ▸ ci_incident
      F3)
- [ ] [OPERATOR] P2. Uninstall the Vercel GitHub App (UI-only; code side already clean). (release_machinery ▸
      contract_hardening #36)
- [ ] [OPERATOR] P3. Residual intermittent v2 `conclusion=action_required` — root is the GitHub-Settings approval toggle
      (auto-recover self-heals the symptom). (promotion_pipeline ▸ promotion_queue)

---

## Recently verified-DONE (flip in the source plans, do NOT re-migrate)

These were already complete-in-prose in the source plans but their checkbox was still open; they are closed, not
remaining work, and are flipped in their source during supersession:

- promotion_pipeline ▸ "First-use watch — normal quickmerge lands on LDR, ~15m drain auto-merges, `--hotfix` hits the
  lock" — CONFIRMED LIVE 2026-06-23.
- promotion_pipeline ▸ "Drain remaining un-promoted LDR content → STAGING_GREEN" — CONFIRMED 2026-06-23 (no stranded
  content fleet-wide; squash-count artifacts only).
- promotion_pipeline ▸ "PREMISE-CORRECTED — quickmerge STAGE lock/status read NOT cut over to
  `tier_c_promotion_gate.py`" — correct-by-design (offline fallback); carries forward into WS-A, not a standalone item.
- starvation ▸ Mode-B per-drain bump cadence — CLOSED won't-change (see D7).

## Success criteria / continuous verification

- **WS-A done** = Phase-4 verify green: `git log` on the integration branches shows ZERO `ci_status` commits; dashboard
  reads Firestore; promote gates behave identically.
- **WS-B done** = `assert_version_coherence.py` shows 0 VERSION_SPLITs in steady state; no manifest-commit-race alert
  noise on `staging-to-main` for a full week.
- **WS-C done** = a deliberately-lost version bump is recovered by the dispatch queue; semver-agent runs cleanly on all
  23 repos.
- **WS-D done** = local `quality-gates.sh` and CI `quality-gates-v2` produce byte-identical verdicts on a sample repo;
  no AO doc references `tab/<op>/N`.
- **WS-E done** = all repos carry the `quality-gates-v2` required-check ruleset (greeks / fund-admin / e2e unblocked);
  removed-symbol orphan count + cap trend DOWN.
- **WS-F done** = live workflow count drops by the folded set; `detect_template_drift.py` green.
- **WS-G done** = the 3 VERIFY-then-fix workflow bugs resolved; event-driven watcher paths live (cron as backstop);
  deployment-ui renders per-repo CI state.
- **WS-L done** = a canary repo runs a full `LDR→main` promote cycle (v2 + SIT + image-off-main) with `staging→main`
  retired; a version bump produces ZERO git commits and the version-line conflict class is gone
  (`assert_version_coherence` 0 splits, no `staging_main_version_line_*` recurrence) and the semver bump-rate breaker no
  longer false-arms; the Phase-0 CI-cost baseline shows the measured per-week saving; rollback resolves a correct
  `version↔SHA` from the registry.

## Codex SSOT updates (on phase completion)

- `codex/08-workflows/ci-cd-flow.md` — the engineer SSOT; update on every WS-A/B/C/D phase landing (esp. the
  ci_status-Firestore one-liner + the `*/20`→hourly drift-tick fix in WS-C).
- `codex/05-infrastructure/workspace-setup.md` — receives the migrated bootstrap/venv content (WS-D).
- `codex/06-coding-standards/quality-gates.md` — config-SSOT + parity items (WS-D).
- CLAUDE.md — one-liner when ci_status becomes Firestore-backed (WS-A Phase-4).
- `codex/08-workflows/ci-cd-flow.md` + CLAUDE.md — on WS-L landing: `main` promotes DIRECTLY from `live-defi-rollout`
  (Option-B fleet-wide; `staging` = SIT/v2 sandbox only, `staging→main` squash retired), and the version label is
  REGISTRY-resolved (git-tags canonical + Firestore mirror), not a `pyproject.toml` source line. Retire the
  conflict-fallback + auto-collapse SPEC docs once fleet-cut.
