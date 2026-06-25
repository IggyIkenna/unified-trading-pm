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
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 14.4
supersedes:
  - cicd_promotion_pipeline_2026_06_18 (open items migrated here; done items + decision log preserved in source)
  - cicd_quality_gates_2026_06_18 (idem)
  - cicd_release_machinery_2026_06_18 (idem)
  - cicd_sit_and_fleet_2026_06_18 (idem)
  - cicd_docs_and_consolidation_2026_06_18 (fully DONE — pure supersede)
  - dependency_promotion_range_pins_and_major_bump_sit_2026_06_09 (remaining 7 items migrated here)
  - issues/staging_to_main_promotion_starvation_2026_06_19 (remaining items migrated here)
source:
  - the 7 plans above (second-level consolidation; the first-level 2026-06-18 fold collapsed ~13 plans + 11 issues into 5 themed plans, most of which are now done)
  - parallel rationale-extraction sweep 2026-06-24 (slot-2) — open items + decision context harvested verbatim from each source
---

# CI/CD — Consolidated Remaining Work

> **Why this plan exists.** CI/CD work was already consolidated once (2026-06-18: ~13 plans + 11 issues → 5 themed
> plans). Those themed plans are now mostly DONE, leaving ~100 open items scattered across 7 documents. This plan is the
> **single live SSOT for the REMAINING CI/CD work**; the 7 source plans are SUPERSEDED (their done items + full
> narrative stay readable in-source as the historical record). **Nothing below is new scope** — every item is migrated
> verbatim with its priority tag and a one-line provenance ref `(source)`.
>
> **The Decision Log (next section) is the irreplaceable part** — it preserves *why* each architecture was chosen over
> the alternative, so a future agent picking up an item understands the prior reasoning rather than re-litigating it.

---

## Decision Log — preserved rationale (why A over B)

Read the relevant entry **before** touching an item in its workstream. These are the design decisions the source plans
established; they are SSOT here.

### D1 — LDR is the integration SSOT; staging/main are projections (LDR-trunk decoupling, live 2026-06-10)

`live-defi-rollout` is the continuous-integration axis + live accumulator. `quickmerge --agent --files` **lands code on
LDR and stops** for a service repo (no per-unit staging PR). The **Tier-C drain** (`ldr-to-staging-promote`, every
15 min) is the *sole* path LDR→staging, and that drain PR's `quality-gates-v2` (head=LDR, base=staging) is the server
gate — **LDR itself never runs QG**. **Why over the old per-commit-staging-PR model:** direct pushes to staging piled up
behind main and jammed the flow (incident: pm-staging-to-main-bypass paralysis 2026-06-03). Decoupling promotion from
the trunk heartbeat removed that anti-pattern. Divergent promotion SHAs with **zero file-content delta**
(`compare` shows `ahead_by>0`, `files:[]`) are squash-count noise to collapse, not work to merge.

### D2 — ci_status moves to a Firestore SSOT (git-commit dual-write is being retired)

ci_status / staging_status are migrating off git commits into a Firestore side-store, in phases (Phase-2 overlay
`tier_c_promotion_gate.py` already consumes Firestore for promote-bot verdicts; Phases 3–4 remain — see WS-A).
**Why over keeping it in git:** concurrent git writes to `ci_status` collide with the heavy manifest-writer set →
rebase exhaustion + manifest-commit race amplification (verified via bug #11, 2026-06-23). Firestore decouples gate
state from git so the races disappear. **Note (premise-corrected 2026-06-23):** `quickmerge` reads ci_status/staging_status
directly from `workspace-manifest.json` as the *offline-fallback cache* — that is correct-by-design; whether quickmerge
needs a further cutover is itself gated on Phases 3–4, not a bug.

### D3 — Breaking detection is CONTENT-based, not version-phase based

`is_breaking` (which locks staging + triggers the 30-min SIT) is the verdict of the AST public-surface differ
`detect_breaking_change.py`, NOT the version phase. A 0.x MINOR / docstring / reformat / internal refactor /
added-optional-kwarg / module-move is **NOT** breaking; a removed-or-renamed public export, incompatible signature,
removed/renamed/retyped schema field, or removed HTTP route **is**. **Why:** the old `git diff __init__.py | grep '^-'`
heuristic flagged any removed line → spurious cascade locks. `quality-gates-v2` still runs on EVERY staging PR; the
breaking gate only narrows the *SIT*, never QG.

### D4 — Range pins absorb minor/patch; only MAJOR forces a rebuild (dependency promotion, operator 2026-06-09)

Internal deps (UTL/UAC/`unified-*`) are range-pinned `>=0.x,<1.0.0` with editable path sources. A minor/patch bump
stays in-range → **NO consumer rebuild, NO CI noise** (consumer picks it up on its own next promote — pull, not push).
A **MAJOR** bump crosses `<1.0.0` → forces a re-pin → triggers a **cascade of QGs (full SIT in dep order)**; green →
auto-promote, no human; escalate to vm-planning ONLY IF the cascade fails. **Why over exact-pin-everywhere:** the lock
records external exact-pins for reproducibility while internal deps are *truly* ranges, honored at install time — so a
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

The staging→main promoter (`staging-to-main.yml`) is healthy; it was *blind* to ~20 repos because it derives its
pending set from manifest version maps (`staging_versions != versions`), not git divergence — and two bugs broke that
signal: **Mode A** (manifest version-bump desync: semver bumped pyproject but a failed `version-bump` dispatch never
propagated to `staging_versions` — affected UAC/UTL/instruments/execution/client-reporting-api); **Mode B** (squash
fallback in `ldr-to-staging-promote.yml` collapsed `feat:/fix:/feat!:` into a single `chore(promote)` → semver read
`chore` → no bump → frozen — affected ~15 repos). **Fixes:** Mode-B `_squash_subject()` now derives the aggregate
conventional type from the collapsed commits so the semver signal survives the fallback; the staging→main pending set
now also includes a **content-ahead probe** (tree-SHA equality) so non-bumping content drains too (verified live
2026-06-23). **Caveat:** fixes do not retro-drain already-frozen backlog — repos self-heal on the next drain.

### D7 — Mode-B per-drain MINOR bumping is ACCEPTED (closed won't-change, 2026-06-21)

The Mode-B fix makes semver MINOR-bump on every Tier-C drain of feature content (~4 bumps/hr on active repos). An
alternative — compute the bump once at the staging→main boundary — was **rejected** because it reintroduces the Mode-B
starvation tension (chore→no-bump→frozen). 0.x versions are cheap and each drain carries real content, so high-velocity
bumping is fine. The bump-rate circuit breaker was hardened to page on genuine re-bump loops (`REBUMP_PAIRS ≥ 2`)
rather than raw count, so healthy climbing is allowed. **No code change — this is a recorded design decision.**

### D8 — Path-B per-slot reference-clones (tab-branch model retired 2026-06-08)

Each slot is a `git clone --reference` on `live-defi-rollout` with its own `.git`; no tab-branches, no `tab-mirror`
sync (deleted fleet-wide). Contention moved to LDR push-time (rebase-on-reject, handled by quickmerge STAGE 0.4).
Commit attribution lives in the git author NAME (`[slot-<N>·<host>]`), independent of branch. **Why:** the tab branch
was only ever a workaround for git's "can't check out the same branch twice in one clone"; separate clones drop the
entire sync tax. Residual tab-branch *code/docs/branches* are dead and tracked for cleanup (WS-D, WS-F).

### D9 — Workflow sprawl folds (release machinery)

The ~51 live workflows trend DOWN via targeted folds where two workflows watch the same signal: `sit-starvation-detector`
is derived SIT state (fold into `sit-debounce-trigger`); `ci-status-reconciler` + `ci-failure-watcher` both watch CI
health (→ `ci-health.yml`); `main-backmerge` drift-tick + `promotion-lag-monitor` both track branch hygiene; the paid-API
agent workflows move to the VM orchestrator (GitHub Actions is billed per run, the orchestrator is not). **Why:** fewer
workflows = less drift surface + lower Actions spend; only fold where the signal genuinely overlaps.

### D10 — Config SSOT lives in `pyproject.toml`, never shadowed on the CLI

Coverage reads `[tool.coverage.report] fail_under` from toml (the base does NOT pass `--cov-fail-under`, which shadowed
it); bandit reads `[tool.bandit]` via `-c pyproject.toml`. Change a repo's floor in **toml**, not the stub. Coverage
must `parallel=true`+combine fleet-wide (xdist `-n auto` reads controller-only partial data otherwise → masks true
coverage; rolled to 20 repos 2026-06-22). The commit (not the PR) is the per-repo quality boundary — a code commit must
come from a `quality-gates.sh`-green tree (sentinel `.qg_last_passed_sha`).

### D11 — Why the drain jams RECUR (root-cause diagnosis, 2026-06-24)

The repeating fleet jams (an AO agent clears one, another appears hours/days later) are **not N unrelated incidents — they
are one structural gap surfacing serially.** Mechanism, ground-verified 2026-06-24:

1. **LDR never runs QG** (D1) — the first quality-gate on the *integrated* LDR tip is the **promote PR** (`ldr-to-staging`,
   head=LDR). Between promotes, code arrives via quickmerge (whose local sentinel is the agent's OWN pre-pull tree) or via
   the carve-out direct pushes (docs / dirty-dep / workflow) which run **no QG at all**.
2. **Ratchet checks are repo-wide COUNT-vs-baseline** (plan-discipline / doc-freshness / ruff-rule-ratchet …). Many agents
   each land a sub-baseline increment; the integrated tip crosses baseline, but **no single agent's pre-pull local run saw
   the full integrated count** → the regression accumulates undetected.
3. **The lint-codex slice short-circuits on first failure** — `base-*.sh` sets `set -e` (line 40) and PM `quality-gates.sh`
   runs each post-gate as a sequential `… || { exit 1; }` (lines 363/375/392/406…). So when several ratchets have regressed,
   the FIRST one exits and **masks the rest** → fix it, re-run, the next surfaces → a fresh "jam." N accumulated regressions
   = N serial jams (incident 2026-06-24: Ikenna worked **13** checks "each hidden behind the prior").
4. **Local↔CI scope divergence** (the `pm-script-path-ref` "55 local / PM-only-pass-in-CI" class) makes a local-green commit
   an unreliable predictor of the promote verdict.
5. **The promote PR is the sole fleet choke point** — one repo's red v2 jams the whole `LDR→staging` drain → fleet-wide
   "drain behind."

The fix is therefore NOT another per-incident patch — it is: (a) make the slice **report ALL failures in one run** (kills
the serial re-jam), (b) **detect ratchet drift on the integrated LDR tip at land-time** (catch + attribute before the
promote), (c) **close the carve-out QG bypass**, (d) drive **local↔CI scope parity** so green-local ⟹ green-promote. These
are **WS-0** below.

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
>   4 further PM drains merged since (#526–#529, PM main `quality-gates-v2` GREEN). The "cannot quickmerge while PM QG is
>   red" premise is **STALE** — PM QG is healthy and draining hourly, so most of WS-0 / A / B / C / D / F / G / H is now
>   **actionable via quickmerge**. (First two landed: BUG `hotfix-mode` + `rollout-action-ref` → PR #532, see WS-G.)
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

- [x] ✅ [SCRIPT] P0. DONE 2026-06-24 (slot-2) — PM `quality-gates.sh` post-gates now ACCUMULATE-and-report: the 15 ratchet/codex/governance gates collect into `POST_GATE_FAILURES` (via a `_post_gate_fail` helper) and the gate fails ONCE at the end with the full list, instead of the first `exit 1` short-circuiting and masking the rest. Each gate still prints its ❌ remedy inline. Scoped to the post-gate/ratchet phase (the `if/else`+`||` structure already neutralises `set -e` — NO global `set -e` removal, base-*.sh untouched); structural pre-gates (manifest / strategy-manifest / locked-plan / scope-checker-presence) stay fail-fast. Failure path verified under `set -euo pipefail` (3 gates fail → all 3 reported, no serial masking); happy path QG-green + sentinel written. **unified-trading-pm@eef45653a** → LDR (drains to main via standing PR). (NEW root-cause 2026-06-24)
- [x] ✅ [WORKFLOW] P0. IMPLEMENTED 2026-06-25 (slot-2) — **this monitor already EXISTED** as `ldr-ci-monitor.yml` + `scripts/repo-management/ldr_ci_monitor.py` (it dispatches the authoritative `quality-gates-v2` — incl. the ratchet/lint-codex suite — against each repo's LDR tip + alerts on red-transitions; reusing the real gate, never a drift-prone bespoke check). The reason drift goes undetected (D11/D1): it was **`gh workflow disable`d 2026-06-11 in the billing wall** (`github_actions_billing_wall_2026_06_11`) because it fired a fresh v2 for ALL ~24 repos EVERY hourly tick. **Fix = revive it, not rebuild**: (1) CONDITIONAL dispatch — skip a repo whose most-recent LDR dispatch already targeted the current tip (fail-safe: dispatch on any uncertainty → never miss a red); steady-state drops ~24/hr to a handful; (2) ATTRIBUTION — on a RED transition, name the introducing commit(s) between the last-green sha and the red tip (author + subject) so the page is actionable. Decision logic verified live (PM tip moved → DISPATCH; unchanged → SKIP); read+detect smoke-tested no-cost; ruff+QG-green. **unified-trading-pm@f50e52fd7** → LDR. **FINAL STEP — re-enable** (`gh workflow enable ldr-ci-monitor.yml -R IggyIkenna/unified-trading-pm`) is tracked as the sub-item below; it MUST wait until this driver reaches `main` (the workflow checks out + runs the `main` copy — re-enabling before it lands would run the OLD unconditional driver = billing wall again). (NEW root-cause 2026-06-24)
  - [ ] [OPS] P0. Re-enable `ldr-ci-monitor.yml` (`gh workflow enable ldr-ci-monitor.yml -R IggyIkenna/unified-trading-pm`) ONCE the conditional-dispatch driver (f50e52fd7) is on `main` (verify: `gh api repos/IggyIkenna/unified-trading-pm/contents/scripts/repo-management/ldr_ci_monitor.py --jq .sha` resolves a blob containing `current_ldr_sha`). First re-enabled tick fires a one-time catch-up burst (~24 repos whose tips moved during the 13-day disable), then steady-state is cheap. Closes `github_actions_billing_wall_2026_06_11` ▸ "re-enable ldr-ci-monitor after its fixes". (NEW 2026-06-25)
- [ ] [SCRIPT] P1. Close the carve-out QG bypass — docs / dirty-dep / workflow direct pushes to LDR run no QG, so a plan/doc/ratchet-relevant push can introduce undetected drift; add a lightweight ratchet/lint pre-push check on the carve-out paths (or fold into the WS-0 LDR monitor). **Supersedes** the WS-C P3 "audit how a lint-red commit reached SIT LDR" (turns the audit into a fix). (NEW root-cause 2026-06-24)
- [ ] [SCRIPT] P1. Ratchet/codex local↔CI SCOPE parity — make every ratchet/codex check scan the SAME path set locally and in CI (kill the `pm-script-path-ref` whole-workspace-vs-PM-only divergence class) so a local-green commit reliably predicts the promote v2. Concretizes the WS-D parity catch-all for the ratchet-scope case. (NEW root-cause 2026-06-24)

### WS-A — ci_status → Firestore SSOT (Phases 3–4) — see D2

- [ ] [CODE] P2. Phase-3 consolidator (Cloud Run Job + Scheduler): writes Firestore aggregate → manifest, one commit/interval — the authoritative writer that replaces the git+Firestore dual-write. (promotion_pipeline ▸ ci_status_firestore)
- [ ] [CI] P2. Migrate `staging-backmerge-to-ldr.yml` + `main-backmerge-to-ldr.yml` ci_status readers to Firestore collection queries. (promotion_pipeline) — blocked on the consolidator above.
- [ ] [CODE] P2. Orchestrator dashboard / `server/` ci_status read path → Firestore collection query (operator-facing visibility). (promotion_pipeline) — blocked on consolidator.
- [ ] [CI] P2. Phase-3 — drop the git-commit half of the dual-write; retire `ci-status-reconciler.yml` (kills the manifest-commit race source). (promotion_pipeline)
- [ ] [VERIFY] P2. Phase-4 — full drain → ZERO ci_status commits; gates behave identically; dashboard live (end-to-end validation). (promotion_pipeline)
- [ ] [CODE] P3. `set_status` explicit txn `max_attempts` / retry on Aborted/DeadlineExceeded (Firestore eventual-consistency resilience, Finding 2). (promotion_pipeline)
- [ ] [SCRIPT] P3. `_align_workspace_manifest.py` + `generate_workspace_dag.py` → read snapshot/store instead of git ci_status. (promotion_pipeline)
- [ ] [DOCS] P2. Phase-4 — codex SSOT + CLAUDE.md one-liner ("ci_status is Firestore-backed"). (promotion_pipeline)

### WS-B — staging→main promotion correctness + drain robustness — see D1, D6

> **⬆️ PRIORITY BUMPED P1→P0 (2026-06-24, operator-directed).** The starvation is actively forcing manual drains (see
> the deployment-service note below) — the two upstream root fixes (Mode A manifest version-bump desync + Mode B
> Tier-C squash-fallback eating semver labels, per D6) should land before more repos need hand-draining.
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
> `origin/live-defi-rollout` by ref, not local HEAD). (2) **the promoter should COLLAPSE (force-sync to LDR) a
> `files=0` divergence rather than open a merge PR that can only CONFLICT** — detect `compare(main,staging).files==[]`
> and force-align instead of merge. **It DID eventually unstick** (force-pushing `main`→LDR-content made the open
> staging→main PR#264 mergeable → it merged; main caught up `0.80`→`0.82`, content-identical) — but only after a messy
> multi-pass that re-staled the Cloud Build mirror again. **STOP hand-draining; land the D6 Mode-A/B fixes + add the
> collapse-not-merge + reformat-free behaviours here.** Composes with the force-push CB-mirror hazard
> (`issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md`).
>
> **PROGRESS 2026-06-24 (bug 1 of 2 FIXED):** `admin-force-sync-all-to-main.sh` now has a **`--no-format`** flag
> (PM#531, merged) — gates the non-idempotent ruff/prettier pre-format so a clean collapse pushes byte-identical trees to
> main+staging (no spurious reformat diff). **This addresses the ROOT of the recurring stick:** code-reading the promoter
> showed it is ALREADY robust — it auto-clears tree-identical divergence (`_tree_sha(staging)==_tree_sha(main)`,
> L955–980), Cure-B (`CURE_B_VERSION_AUTORESOLVE`) auto-resolves version-LINE conflicts, and only a GENUINE non-version
> content conflict escalates to the conflict-resolution-agent. deployment-service kept escalating because the force-sync
> reformat injected a **spurious non-version diff**. With `--no-format`, a future collapse is version-line-only → Cure-B
> handles it → NO escalation, NO manual drain. **Use `--no-format` for any future collapse.**
>
> **REMAINING (the riskier bug 2):** make the promoter AUTO-COLLAPSE a content-lossless (tree-equal-modulo-version, or
> reformat-only) divergence instead of escalating. This needs the promoter to **force-update a service repo's `main` ref
> past branch protection** — a capability the workflow deliberately does NOT have today (it merges via protected, v2-gated
> `gh pr create` + auto-merge; the only `git push` is the FF manifest bookkeeping to PM's own main). Adding a
> protection-bypass force-ref-update to the fleet-wide `*/15` promoter is **security-sensitive + fleet-critical** (a bug
> force-pushes a wrong SHA to every repo's main) — it needs deliberate design + review + a tight guard (only when
> `staging_tree == main_tree` modulo the bumped version line), NOT a hasty edit. The D6 Mode-A/B upstream fixes remain too.

#### SPEC — Safe auto-collapse of a content-lossless staging→main divergence (bug 2, implementation-ready)

**Goal:** when a staging→main promotion is `dirty` (git 3-way conflict) but the NET content delta is lossless (≤ the
bumped `version` line), promote it automatically — WITHOUT ever force-pushing a protected branch. The trick: don't try to
"resolve" the divergent histories in place; **rebuild the promotion as a single clean commit on top of `main`** and merge
THAT through the existing protected, v2-gated PR path.

**Non-negotiable safety constraints**

1. **Never force-push / force-update a protected branch** (`main`/`staging`) from the fleet `*/15` promoter. The only push
   is to a throwaway UNPROTECTED feature branch; the actual main update is a normal v2-gated PR auto-merge (same gate as
   every other promotion). This is what makes it safe — no new bypass capability, no "wrong SHA force-pushed fleet-wide".
2. **Fire ONLY when provably content-lossless.** Confirm the ONLY differing file is `pyproject.toml` and the ONLY differing
   line is `^version = `. Implementation: `gh api compare/main...staging` is squash-inflated → instead diff the trees:
   list `.files` from the compare AND independently verify via `git diff --stat origin/main origin/staging` in a shallow
   checkout; require `files == ["pyproject.toml"]` AND the pyproject hunk touches only the `version` line. ANY other delta
   → DO NOT collapse; escalate as today.
3. **Kill-switch:** gate the whole behaviour behind repo/org var `STAGING_TO_MAIN_AUTOCOLLAPSE` (default `false` → opt-in).
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
3. **Open the PR** `promote/collapse-<R>-<sha> → main`, `gh pr merge --auto --squash`. It descends cleanly from `main`
   ⇒ conflict-free ⇒ v2 runs ⇒ auto-merges via the SAME protected path as every promotion.
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

- [ ] [AGENT] P0. Manifest hygiene (post-drain): reconcile manifest `versions`/`staging_versions` to the drained pyproject versions where `assert_version_coherence.py` (warn-only) shows a split; next semver/promote cycle also realigns it. **NOTE 2026-06-24: 14 VERSION_SPLITs currently flagged (warn-only); deployment-service force-sync (above) added one more (main 0.77.0 / staging 0.78.0) — confirms this is still live.** (starvation ▸ P0)
- [x] ✅ [SCRIPT] P0. **Bug 1/2 — `admin-force-sync --no-format`** (PM#531, merged): gate the non-idempotent ruff/prettier pre-format so a clean collapse pushes byte-identical trees → version-line-only conflict → Cure-B handles it, no escalation. Addresses the root of the recurring stick. (starvation ▸ P0)
- [x] ✅ [WORKFLOW] P1. **Bug 2/2 — promoter auto-collapse a content-lossless `dirty` divergence — IMPLEMENTED + TESTED (PM@01ba0ca74, shipping LDR→main; INERT until `STAGING_TO_MAIN_AUTOCOLLAPSE=true`).** `scripts/cicd/auto_collapse_lossless_promote.sh` (takes staging's FINAL tree as ONE clean commit on main → can't conflict → v2-gated PR; NO protected force-push) + guard test `test_auto_collapse_lossless_guard.sh` (3/3: version-only→collapse, any other diff→escalate) + `staging-to-main.yml` Merge-step wiring (after Cure-B `dirty`, opt-in + K=3/run cap + downgrade guard). **Rollout:** set the repo/org var for deployment-service first, watch 2–3 `*/15` cycles, then fleet-enable. Rebuild the promotion as ONE clean commit on top of `main` (take staging's tree + `version=max`) on an UNPROTECTED `promote/collapse-<repo>-<sha>` branch → merge via the existing v2-gated protected PR path; **never force-push a protected branch.** Guards: lossless check (only `pyproject.toml`/`version` differs), kill-switch `STAGING_TO_MAIN_AUTOCOLLAPSE` (default off), K=3/run cap, single-repo rollout first. Edit `staging-to-main.yml` Merge step (L612+) AFTER the Cure-B `dirty` branch. (starvation ▸ P1)
- [ ] [WORKFLOW] P2. `staging-to-main` "Commit manifest update" race ROOT fix — re-derive the mutation onto fresh `origin/main` inside the retry loop so commits are conflict-free and bookkeeping lands every run. (Alert mitigation already SHIPPED PM@706b8f414: abort conflicting rebase, 5→8 attempts, `::warning::`+`exit 0` on exhaustion. Root fix (a)/(c) remains.) (promotion_pipeline ▸ bug #11)
- [ ] [SCRIPT] P2. Durable fix for the staging-unlock / check-staging-lock refresh gap — re-run open-PR required checks after the lock clears (else a lock-blocked PR stays blocked post-unlock). (promotion_pipeline ▸ contract_hardening #20)
- [ ] [SCRIPT] P2. Lock writes `[skip ci]` → backmerge skips → stale `staging_status` in the LDR copy; reconcile non-quickmerge readers (promote bots / direct manifest readers). (promotion_pipeline ▸ contract_hardening #21)
- [ ] [WORKFLOW] P2. Batch a breaking fan-out into ONE cascade over the union of dependents (stop per-consumer serialization). (promotion_pipeline ▸ contract_hardening #29)
- [ ] [SCRIPT] P2. Consumer re-pin breaking verdict — run `detect_breaking_change.py` on the consumer surface (re-pins still unconditionally `feat!`). (promotion_pipeline ▸ contract_hardening #31) — see D3.
- [ ] [SCRIPT] P2. Review `cloud-build-router.yml` membership in the `manifest-update` concurrency group (non-replayable payload → eviction risk). (promotion_pipeline ▸ contract_hardening #27)
- [ ] [SCRIPT] P1.5. Verify the LDR→staging drain resolves all deps at the staging ref (no mixed-ref clone). Composes with WS-D dep-clone ref-determinism. (promotion_pipeline ▸ ldr_trunk)
- [ ] [CICD] P2. Downstream conflict fallout — re-check the secondary stuck PRs (staging→main promotes + LDR→main fallbacks + main→LDR backmerges) that conflicted during the 2026-06-21 storm; most auto-resolve, a few may need a rebase. (starvation)
- [ ] [CICD] P3. EXPLORE: why the 0.24.0 fan-out used the retired staging-direct pattern despite consumers having the LDR-direct template since 06-18 (likely: `repository_dispatch` runs the handler from the repo's stale default branch). Confirm so it can't recur. (starvation)
- [ ] [WORKFLOW] P3. Redundant empty staging→main PRs across consecutive `*/15` runs (NICE-TO-HAVE) — re-check tree-equality at PR-create time or auto-close empty BLOCKED PRs. (promotion_pipeline ▸ bug #11)
- [ ] [SCRIPT] P3. Host stale-PR / stale-checkout monitoring (Track D) — extend slot Slack monitoring. (promotion_pipeline ▸ ldr_trunk)

### WS-C — semver + version surface — see D4, D5, D7

- [ ] [SCRIPT] P1. Lossy dispatch queue — make `update-repo-version` records loss-proof (verified-live root cause: bumps disappear mid-flight). (release_machinery ▸ semver)
- [ ] [SCRIPT] P2. Fleet rollout — semver-agent bounded-scan + Option-C to 23 repos (confirmed on 2; 21 unswept). (release_machinery ▸ contract_hardening #6)
- [ ] [SCRIPT] P2. Decouple SIT-harness hygiene from cascade validity (route harness lint to a fix-task, not a cascade block). (release_machinery)
- [ ] [SCRIPT] P2. Retry-cap is alert-only — teach the watcher to diff the failing-slice log + dispatch a fix on cap. (release_machinery)
- [ ] [SCRIPT] P2. Action-pin existence gate — resolve `uses:@ref` vs tags pre-rollout (the node24 phantom-tag class). (release_machinery)
- [ ] [SCRIPT] P2. Add the `required_approving_review_count>0` flag to `verify_branch_protection_check_names.py` (audit-coverage gap: checks present but approval-count=0 bypasses review). (release_machinery ▸ contract_hardening #18)
- [ ] [PROCESS] P3. Audit how a lint-red commit reached SIT LDR (the QG-before-commit miss). (release_machinery ▸ semver)
- [ ] [CI] P2. `major-bump-issue-handler.yml:183` is a second staging-direct writer — reroute the `/approve`-gated 1.0.0 graduation bump from `staging` to `live-defi-rollout` (LDR-is-SSOT consistency; kept scoped out of 1.5a). (dependency_promotion)
- [ ] [SCRIPT] P2. `propagate-canonical-versions.py` silently SKIPS ceiling-first specs — `_replace_dep_spec()` returns on the FIRST separator found; for `"fastapi<1.0.0,>=0.115.0"` it mis-parses → returns unchanged. Parse at the EARLIEST operator position across all operators. (dependency_promotion) — latent; safe to defer until the next canonical rollout (1.5b capped via scoped sed).
- [ ] [INFRA] P2. Canonical-dependency alignment is advisory + has pre-existing drift — reconcile the two sources (`workspace-constraints.toml` ↔ `canonical-dependency-manifest.json`), cap pyarrow (5 repos) + python-multipart (fund-admin). Depends on the propagation-bug fix above. (dependency_promotion)
- [x] ✅ [SCRIPT] P2. Registry-poller for the rebuild-without-bump digest edge — **DONE (verified 2026-06-24 slot-2)**: `digest-drift-sweep.yml` runs `schedule: 0 */6 * * *`, resolves `:latest`'s digest and dispatches `dependency-update` with `base_image_digest` idempotently. (dependency_promotion)
- [ ] [SCRIPT] P3. `--ignore-vuln` block is duplicated across `base-service.sh` + `base-library.sh` (drifted once → UTL Mode-B fail; synced 2026-06-18). Extract to a SINGLE shared shell constant (`qg-common.sh` `PIP_AUDIT_IGNORE_VULNS`). (dependency_promotion)
- [x] ✅ [SCRIPT] P3. Stale duplicate `scripts/propagation/templates/update-dependency-version.yml` — **ALREADY DONE (verified 2026-06-24 slot-2)**: the file is ABSENT (already deleted); no `scripts/propagation/templates/` consumer remains for it. Nothing to do. (dependency_promotion)
- [x] ✅ [DOCS] P3. Stale codex value `codex/08-workflows/ci-cd-flow.md` drift-tick `*/20` — **ALREADY CORRECT (verified 2026-06-24 slot-2)**: the doc already says hourly (`0 * * * *`) at lines 504-505 ("relaxed from `*/20` 2026-06-11"); no line asserts the drift-tick IS `*/20`. The `:460` reference was stale. Nothing to do. (dependency_promotion)

### WS-D — quality gates + local↔CI parity + worktree discipline — see D8, D10

- [ ] [SCRIPT] P1. Fix any non-SIT-delta divergence in the local↔CI matrix to byte-identical — the drive-to-parity **catch-all** (most root-causes closed; this stays open by design as a continuous property). (quality_gates ▸ ci_local_qg_parity)
- [ ] [SCRIPT] P2. QG dep-clone ref-determinism — resolve all deps at the same ref (no mixed-ref clone). Composes with WS-B P1.5. (quality_gates ▸ contract_hardening #23)
- [ ] [INFRA] P2. Churn-protection: idempotent plan-inventory regen + manifest-canonical-form + a `prettier --check` gate (three named writers still churn the worktree → jam FF-pulls). (quality_gates ▸ contract_hardening #2)
  - [x] ✅ [SCRIPT] P2. DONE 2026-06-25 (slot-2) — **one churn source closed**: `generate_canonical_dependency_manifest.py` no longer stamps a `generatedAt` wall-clock field into the TRACKED `canonical-dependency-manifest.json` SSOT. `run-version-alignment.sh` (+ any QG) regenerates this file, so the timestamp re-stamped every run → a 1-line dirty diff that jams `slot-cron-ff-pull` (the exact "regen `generatedAt`-timestamp churn" another agent hit 2026-06-20). Nothing reads the field (verified workspace-wide); generator is now byte-identical across two runs (diff = empty). **unified-trading-pm@4d22c3ebe** → LDR (PR #553 → main, v2-gated). Parent stays OPEN: plan-inventory regen + workspace-manifest canonical-form + the prettier-check gate remain.
- [ ] [DOCS] P2. Rewrite AO `worker.md` + the boot-prompt `branch` fallback off the retired `tab/<op>/N` model → reference-clone reality (FF-pull to LDR). (quality_gates ▸ worktree_ldr)
- [ ] [INFRA] P2. AO drift-tick is staged on LDR, inert until the agent-orchestrator LDR→main promotion lands — auto-activates then (scheduled workflows fire only from the default branch). (quality_gates ▸ worktree_ldr)
- [ ] [INFRA] P2. E2e smoke: force a merge-conflict PR across SEPARATE Path-B clones → quickmerge STAGE 0.4 rebase+autostash → green; archives the worktree-ldr section when green. (quality_gates ▸ worktree_ldr)
- [ ] [CICD] P2. deployment-service CodeBuild BUILD exit 127 (uv/image not found) — live infra red, non-blocking (CodeBuild not a required v2 check); needs CodeBuild image rebase. (quality_gates)
- [ ] [DOCS] P2. Migrate `docs/repo-management/CI-CD-FLOW.md`'s unique bootstrap/venv/dep-alignment/mock-infra content → `codex/05-infrastructure/workspace-setup.md` (correct stale sync-to-main/force-push/three-tier bits to as-built LDR-trunk), then delete the stale doc (already bannered NOT-the-SSOT). (quality_gates)
- [ ] [SCRIPT] P3. Remove now-redundant local PYSEC-2024-277/2025-183/2026-161 entries from: alerting-service, client-reporting-api, ml-service, system-integration-tests, trading-agent-service, unified-trading-api, unified-trading-library, greeks-service, strategy-service (CVEs handled centrally PM@7adfefec9). **VERIFIED 2026-06-24 slot-2: this is a PROVABLE NO-OP** — `base-service.sh:1224` appends those 3 PYSEC ignores to the per-repo `PIP_AUDIT_EXTRA_ARGS`, so per-repo copies are duplicate `--ignore-vuln` flags that pip-audit treats identically whether listed once or twice. The only value is "single control point" hygiene, which is **subsumed by the line-252 centralization** (extract the ignore block to a shared `qg-common.sh` constant — a PM change, #525-gated). **DON'T run a standalone 9-repo QG+ship sweep for a no-op; fold into 252.** (quality_gates ▸ contract_hardening #8)
- [ ] [SCRIPT] P3. Prune vestigial tab-branch code in the slot scripts (keep the identity-prefix; documented-harmless no-ops only). (quality_gates ▸ worktree_ldr)
- [ ] [DESIGN] P3. LATER — crons self-pull from a QG-v2-gated ref (successor hardening; the bare FF-pull is safe today). (quality_gates ▸ qg_commit)
- [ ] [DOCS] P3. Repoint the ~18 residual references off the 4 retired CI/CD docs → `codex/08-workflows/ci-cd-flow.md` (cursor rules + infra docs + scripts; drop dead `§7`/`§2` anchors). Cleanliness — stubs already self-redirect. (quality_gates)
- [ ] [DOCS] P3. Physical archive-move of the 7 superseded source plans (`cicd_promotion_pipeline`/`cicd_quality_gates`/`cicd_release_machinery`/`cicd_sit_and_fleet`/`cicd_docs_and_consolidation`/`dependency_promotion_range_pins_and_major_bump_sit`/`issues/staging_to_main_promotion_starvation`) → `plans/archive/2026_06/`. Status flipped active→superseded + banners present (slot-2 2026-06-25, PM@a237bff34) — but they're STILL in `plans/active/` because they're path-referenced by 13 live files incl. fleet templates (`base-service.sh`/`base-library.sh`/`semver-agent.yml.tmpl` — editing those triggers a fleet rollout). The move needs: update the 13 path-refs (or leave script/template COMMENT refs stale) + `[unlock-plan]` (all 7 `locked_by: live-defi-rollout`). (consolidation closeout)
- [x] ✅ [SCRIPT] P3. DONE 2026-06-25 (slot-2) — `check_superseded_in_active.sh` now has check (3): scan every active plan's `supersedes:` list (handles the multi-line YAML list AND the inline `supersedes: <slug>` form; bare slug / `issues/<slug>` subpath / `plans/active/…md` path, parenthetical-stripped) → any listed slug still `status: active` in `plans/active/` is flagged `SUPERSEDED_BUT_ACTIVE`. Also flipped the script from `exit 0` always (toothless — its `soft` registration in `run_hygiene_sweep.sh` keys off the EXIT CODE, so it could never surface a WARN) to exit-nonzero-on-flag → now visible as a ⚠️ SOFT_WARN. **Negative-tested**: extracts all 7 cicd source slugs (incl the `issues/` subpath), resolves each to `status:superseded` (clean), and FIRES when one is flipped back to active. Closes the exact gap that let the 7 source plans masquerade as active for a day (operator-caught 2026-06-25, not tooling). **unified-trading-pm@118f9cb6f** → LDR. (consolidation closeout)
- [ ] [OPS] P0. **[DEFERRED-AWS — leave as-is per operator 2026-06-24]** AWS-VM half — verify `ROOT_PM`/`SLOT_DIR` + crons + not-stranded on the fleet VM (Harsh-laptop half done). (quality_gates ▸ qg_commit L435/L441)

### WS-E — SIT + fleet rulesets

- [x] ✅ [SCRIPT] P2. greeks-service ruleset — **DONE (verified 2026-06-24 slot-2)**: active ruleset on main requires `Quality Gates (greeks-service) / quality-gates-v2` AND v2 is GREEN on main/LDR/staging → the coverage+C901 debt was cleared since the 2026-06-18 capture. (sit_and_fleet ▸ contract_hardening #15)
- [x] ✅ [SCRIPT] P2. fund-administration ruleset — **DONE (verified 2026-06-24 slot-2)**: active ruleset requires `quality-gates-v2` AND v2 GREEN on main/LDR → the starlette uv-sync conflict is resolved. (sit_and_fleet ▸ contract_hardening #16)
- [x] ✅ [SCRIPT] P2. e2e-testing ruleset — **DONE (verified 2026-06-24 slot-2)**: active ruleset requires `quality-gates-v2` AND v2 GREEN on main/staging/LDR → the ruff debt is cleared (the bare-`ruff check .`=188 is whole-tree noise; QG-scoped ruff passes). (sit_and_fleet ▸ contract_hardening #17)
- [ ] [SCRIPT] P2. Promote `system-integration-tests` LDR→main so the SIT report-back goes live (promotion + e2e verify). (sit_and_fleet)
- [ ] [WORKFLOW] P2. Upgrade `sit-starvation-detector` from alert-only toward auto-redispatch (composes with the WS-F fold into `sit-debounce`). (sit_and_fleet)
- [ ] [SCRIPT] P2. Review `sit-gate.yml` + `sit-unlock.yml` membership in the `manifest-update` concurrency group (eviction risk). (sit_and_fleet)
- [ ] [SCRIPT] P2. Audit the fleet for `[skip ci]` version-bump commits stranded on staging (the v2-required-check deadlock signature). (sit_and_fleet)
- [ ] [SCRIPT] P2. Drive the 328 removed-symbol orphans down (add UTL to the consumer set and/or follow facade/`__all__` re-exports), then lower the cap from 400. (sit_and_fleet ▸ sit_uac_orphan)
- [ ] [SCRIPT] P2. Tier-D — per-service Cloud Run deploy-config audit + add the missing HTTP deploys. (sit_and_fleet)
- [ ] [SCRIPT] P2. Tier-E — wire game-day + synthetic smokes into the staging SIT schedule. (sit_and_fleet)
- [ ] [DESIGN] P2. Per-cone parallel staging locks (design doc — let independent dep cones promote concurrently). (sit_and_fleet)

### WS-F — workflow sprawl consolidation — see D9

- [x] ✅ [SCRIPT] P2. **PRUNED 2026-06-24 (slot-2, operator prune-go) — all 21 stale `tab/*` branches deleted from remote; full record table below.** VERIFIED-STALE before deletion (earlier "orphaned safety-critical work / DO NOT DELETE" alarm RETRACTED).** Full per-branch triage done: 21 `tab/*` branches across 14 repos, all `ahead_by≥1` of LDR — but the raw `ahead_by`/file-counts were misleading (squash-merge accounting + weeks of LDR drift). Applying the operator's **recency heuristic** (2026-06-24: ≤7d=check properly · 7–15d=some attention · >15d=probably noise/superseded): **newest orphan commit is 2026-06-09 (15d) — zero in the ≤7d window.** Content-verified every branch: (a) the 2 recent (7–15d) — PM `tab/ikennaigboaka/2` (`docs(plans)` coverage-matrix flip) + mtds `tab/ikennaigboaka/2` (`feat(defi)` migrator gas/liquidation specs) — **both superseded** (mtds redone as first-class CLI handlers `gas_fee_handler.py`/`liquidations_handler.py`; the QG-masked test fix's 7 scaffold-op mappings already on LDR); (b) the 18 older (>15d) are `style()` ruff-format passes, `docs(plans)` flips, and `chore(orphan-wip)` re-inheritances, **plus** a handful of `feat`/`fix` whose every key symbol is **confirmed on LDR** — WorkerLivenessWatchdog (`server/worker_liveness_watchdog.py`, live/default-on), UTL messaging module, UAC incident+risk modules, **strategy-service kill-switch** (`kill_switch_bus_subscriber.py` present + `kill_switch_guard.py`/`archetype_kill_switch_subscriber.py` expanded on LDR), client-reporting Phase6.A, mdps `publish_with_manifest_lookup`; (c) the only "all files absent on LDR" branches are trading-agent-service (`pyrightconfig.json` — intentionally removed fleet-wide per the override rule) + e2e-testing (`.coverage`/`coverage.xml` — gitignored artifacts). **No genuine orphaned work remains.** Pruned via `git -C <repo> push origin --delete <tab-ref>` per branch. (release_machinery ▸ sprawl; verified + pruned 2026-06-24 slot-2)

  **Record of the 21 pruned `tab/*` branches** (deleted from remote 2026-06-24; recoverable via reflog/SHA for ~90d if ever needed — all content verified present-or-superseded on LDR). The author column reflects pre-2026-06-03 attribution era for the older ones (unstandardised `Ubuntu`/`Claude`/`ComsicTrader`/`semver-rollout[bot]`/`agent-orchestrator (orphan-wip)` identities) vs the post-standardisation `ikennaigboaka [slot-N·host]` for June 8–9:

  | Date | Repo | Branch | Tip | Author (as committed) | Disposition |
  | --- | --- | --- | --- | --- | --- |
  | 2026-06-09 | unified-trading-pm | tab/ikennaigboaka/2 | 9b92c1bfb | ikennaigboaka [slot-2·laptop] | docs(plans) DeFi coverage matrix — plan state moved on (superseded) |
  | 2026-06-09 | market-tick-data-service | tab/ikennaigboaka/2 | 01fda7ce | ikennaigboaka [slot-2·laptop] | feat(defi) migrator gas/liquidation specs — redone as first-class CLI handlers on LDR |
  | 2026-06-08 | unified-trading-pm | tab/ikennaigboaka/7 | fe6ebc8dd | ikennaigboaka [slot-7·laptop] | docs(plans) bar-edge flip — superseded |
  | 2026-06-08 | unified-trading-pm | tab/ikennaigboaka/3 | d46ce8bd3 | ikennaigboaka [slot-5·planning] | chore(merge) conflict resolution — 0 net files, superseded |
  | 2026-06-03 | market-tick-data-service | tab/vm-0/10 | 70bc9696 | Ubuntu (vm) | chore gitignore QG sentinels — sentinels gitignored fleet-wide on LDR |
  | 2026-06-01 | unified-trading-library | tab/rootm/2 | 85051c7 | Claude (vm) | style ruff-format — formatting noise |
  | 2026-06-01 | market-tick-data-service | tab/rootm/2 | 8f03cc6a | Claude (vm) | style ruff-format (solana-defi) — formatting noise |
  | 2026-06-01 | deployment-service | tab/rootm/2 | 026c8c3 | Claude (vm) | style packer README align — all 32 files present on LDR |
  | 2026-06-01 | agent-orchestrator | tab/rootm/5 | 4d37823 | Claude (vm) | feat WorkerLivenessWatchdog — on LDR (`server/worker_liveness_watchdog.py`, live) |
  | 2026-05-29 | instruments-service | tab/ikennaigboaka/10 | 8375d7f | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded |
  | 2026-05-29 | deployment-ui | tab/ikennaigboaka/9 | bb470a1 | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded |
  | 2026-05-28 | unified-trading-api | tab/ikennaigboaka/11 | 67813db | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded |
  | 2026-05-28 | trading-agent-service | tab/ikennaigboaka/11 | 365bb22 | agent-orchestrator (orphan-wip) | orphan-wip — only `pyrightconfig.json` (intentionally removed fleet-wide) |
  | 2026-05-28 | system-integration-tests | tab/ikennaigboaka/11 | e1aea8f | agent-orchestrator (orphan-wip) | orphan-wip re-inheritance — superseded |
  | 2026-05-28 | e2e-testing | tab/ikennaigboaka/11 | c6c56be | agent-orchestrator (orphan-wip) | orphan-wip — only gitignored `.coverage`/`coverage.xml` |
  | 2026-05-24 | unified-trading-library | tab/rootm/7 | 7ad67da | Ubuntu (vm) | feat messaging module — on LDR (`cloud_interface/abstractions.py`) |
  | 2026-05-24 | unified-api-contracts | tab/rootm/7 | c44daaf5 | Ubuntu (vm) | feat incident+risk modules — on LDR (domain modules + tests) |
  | 2026-05-24 | strategy-service | tab/rootm/7 | 8b4dfa6a | Ubuntu (vm) | fix kill-switch subscriber — on LDR (`kill_switch_bus_subscriber.py` + guard/archetype expanded) |
  | 2026-05-13 | market-data-processing-service | tab/hk/10 | 0c92b91 | ComsicTrader (Harsh laptop) | fix 19 MDPS test failures — on LDR (`canonical_writer.py` + tests) |
  | 2026-05-13 | client-reporting-api | tab/ikennaigboaka/8 | c0a4ff3 | semver-rollout[bot] | feat Phase6.A demo-internal client — on LDR (`mock_performance_data.py`) |
  | 2026-05-11 | market-data-processing-service | tab/ikennaigboaka/8 | f25da5f | semver-rollout[bot] | feat publish_with_manifest_lookup — on LDR (`canonical_writer.py` + stamping) |
- [ ] [SCRIPT] P3. Fold `sit-starvation-detector.yml` into `sit-debounce-trigger.yml`. (release_machinery ▸ sprawl / contract_hardening #37)
- [ ] [SCRIPT] P3. Merge `ci-status-reconciler` + `ci-failure-watcher` into one `ci-health.yml`. (release_machinery ▸ sprawl #38)
- [ ] [SCRIPT] P3. Consolidate the `main-backmerge` drift-tick + `promotion-lag-monitor` into one branch-health monitor. (release_machinery ▸ sprawl #39)
- [ ] [SCRIPT] P3. Extract a shared `agent-runner.yml`; collapse `conflict-resolution-agent` into `escalate-to-orchestrator`; migrate the paid-API agents to the VM orchestrator. (release_machinery ▸ sprawl #40)

### WS-G — watchers + self-healing + observability

- [ ] [WORKFLOW] P2. Build/validate the image on the `staging→main` PR head — the REAL deploy gate (must land before any main-required build check); current model validates only post-main-merge. (release_machinery ▸ self_healing G5) — **foundational for promotion automation.**
- [ ] [WORKFLOW] P2. `ci-failure-watcher` event-driven path (don't rely solely on the throttled cron). (release_machinery ▸ self_healing G3b)
- [ ] [WORKFLOW] P2. Event-driven trigger for the v2-never-reported recovery (cron stays as the backstop). (release_machinery ▸ self_healing G9b)
- [ ] [WORKFLOW] P2. Watchdog/alert for a stale `promotion_quarantine` + clean-merge (the deadlock signature; auto-recover shipped, the alert did not). (release_machinery ▸ self_healing G7)
- [ ] [SCRIPT] P2. Surface a published-vs-required AR lag metric in `promotion_lag_monitor` / the dashboard. (release_machinery ▸ self_healing G9a)
- [ ] [UI] P2. deployment-ui Repos-CI `working`/`pending` state per repo (orchestrator half shipped; UI render remaining). **Honors the UI playwright gate: needs `[UI]` + `pw:L2 ✓` + a `tests/` regression spec to tick.** (release_machinery ▸ self_healing G4)
- [ ] [SCRIPT] P2. One-off recovery audit — diff `wip-preserve/*` + reflog vs LDR per repo for silently-dropped commits (Path-B migration safety). (release_machinery ▸ self_healing G2)
- [ ] [SCRIPT] P2. Debounce `FEATURE_GREEN ↔ FAILING` ci-status flap alerts (N-tick suppression). (release_machinery ▸ contract_hardening #24)
- [ ] [WORKFLOW] P2. Dashboard alert-parity — flag a staging head with ZERO check runs (composes with a failure-injection matrix). (release_machinery ▸ contract_hardening #33)
- [ ] [WORKFLOW] P2. Persist failures must be VISIBLE — emit `::warning` on a ledger-write failure. (release_machinery ▸ contract_hardening #34)
- [ ] [SCRIPT] P2. CI-watcher — suppress the by-design `staging-lock-check` `locked` repository_dispatch "failure" (stop paging on a normal lock exit). (release_machinery ▸ contract_hardening #7)
- [ ] [SCRIPT] P2. Alert when a slot `[skip:dirty]`s for > N consecutive ff-pull ticks (observability gap). (release_machinery ▸ ci_incident F2)
- [x] ✅ [BUG] P2. VERIFY: `conflict-resolution-agent.yml` duplicate `env:` key — **FALSE ALARM (verified 2026-06-24 slot-2)**: the Dispatch step (line 94) has exactly ONE `env:` block (line 96, GH_PAT/REPO_NAME/PR_NUMBER/SOURCE_BRANCH/TARGET_BRANCH); the other `env:` at 51/73 are on SEPARATE steps. Escalation fires with `GH_PAT` correctly. No fix needed. (release_machinery ▸ drift audit)
- [x] ✅ [BUG] P2. FIXED 2026-06-24 (slot-2) — `hotfix-mode.yml` bare `git push` wrapped in the proven 5-attempt `pull --rebase --autostash` retry loop (mirrors `update-repo-version`), closing the silent-drop race in the shared `manifest-update` concurrency group. **unified-trading-pm@8ba9ef36** | PR #532 → main (auto-merge, v2-gated) | YAML + actionlint clean. (release_machinery ▸ drift audit)
- [x] ✅ [BUG] P2. RESOLVED 2026-06-24 (slot-2) by **DELETE, not the originally-scoped git-add fix** (diagnosis correction): `rollout-action-ref.yml` + `rollout-quality-gates-ci-workflows.py` referenced the **v1 filenames in 3 places** (read path `:386`, the `git add` `:110`, AND the `--workflow-call` constants `python-quality-gates.yml`/`ui-quality-gates.yml`), so the rollout no-opped on EVERY manifest push for weeks (#438→#520, every repo → "MISS, no quality-gates.yml"). It is **superseded** by `rollout-workflow-templates.sh` + `quality-gates-v2.yml.tmpl` (static `@live-defi-rollout` pin; `active_feature_branch` no longer rotates in the LDR-trunk era) — reviving it = a banned parallel path. **Deleted both files** + tidied 3 stale lint-globs in `quality-gates.sh`, the `generate-workflow-catalog.py` category map (+ regenerated `CICD-WORKFLOW-CATALOG.md`), and repointed the codex refs (`cicd-setup.md`/`new-repo-setup.md`/`act-preflight-coverage.md`) at the template-rollout. **unified-trading-pm@8ba9ef36** | PR #532 → main (auto-merge, v2-gated). Residual `rollout-action-ref` mentions remain only in superseded source plans (`cicd_docs_and_consolidation_2026_06_18`, `cicd_release_machinery_2026_06_18`) + the `org_migration_to_odumresearch_2026_06_07` file-inventory — historical/non-functional, drop on next touch. (release_machinery ▸ drift audit)
- [ ] [WORKFLOW] P3. Name the missing backmerge file in the Tier-C runaway breaker's page (presence-audit residual). (release_machinery ▸ self_healing G6)
- [ ] [SCRIPT] P3. CI dep-clone fallback — prefer the manifest-pinned tag over upstream `main` (in-flight-rename gap). (release_machinery ▸ ci_incident F4)
- [ ] [SCRIPT] P3. Add a tier-bulk-clone helper for `readiness-verifier` (NICE-TO-HAVE). (release_machinery ▸ ci_incident F1)
- [x] ✅ [SCRIPT] P3. DONE 2026-06-25 (slot-2) — all 4 fixed: `cloud-build-failure-watcher` comment "15 min"→"30 min" (cron `*/30`); `ci-status-reconciler` "10 min"→"15 min" (cron `*/15`); `ldr-ci-monitor` "30-min tick"→"hourly" (driver docstring + workflow header, landed with WS-0 #2 @f50e52fd7); `publish-package` header "Reusable workflow"→"repository_dispatch-triggered" (it has no `workflow_call`, only `repository_dispatch: [publish-package]`). Comment-only, zero behavior change. **unified-trading-pm@aad9102e4** → LDR. (release_machinery ▸ drift audit)
- [ ] [SCRIPT] P3. Drop stale "Telegram alert" comments / `send_telegram()` names (impl is Slack; Telegram retired 2026-06-02) in: secret-health-check, cassette-drift-check, plan-notification, agent-audit, overnight-dead-man-switch, fix-approval-timeout, cold-storage-cleanup. (release_machinery ▸ drift audit)

### WS-H — gh-rate budget

- [ ] [INFRA] P2. Token-pool split for the promote/monitor Actions (same-repo read-only → `GITHUB_TOKEN`; cross-repo promoters stay on PAT). (release_machinery ▸ gh_rate)
- [x] ✅ [INFRA] P3. Firestore write-through for `reconcile-release-tags` — **DONE (verified 2026-06-24 slot-2)**: `reconcile_release_tags.py:170-236` `_write_firestore_release_tags()` writes per-repo release version+tag to the `repo_state/{repo}/release_tag` Firestore collection (GCP_PROJECT_ID-gated, best-effort); the workflow invokes it. (release_machinery ▸ gh_rate)

### WS-I — deps hygiene / CVE

- [ ] [DEPS] P2. Fleet pip-lock hygiene — bump the vulnerable `pip` floor in 18 repos (ignore-covered but floors not applied → regen locks). (release_machinery ▸ contract_hardening #4)
- [ ] [DEPS] P2. TRACKED-FOR-REMOVAL — drop the aiohttp `--ignore-vuln` block once execution-service migrates off aioresponses (vcrpy 8.2.1 already supports patched aiohttp). (release_machinery ▸ contract_hardening #11)
- [x] ✅ [SCRIPT] P3. Collapse local `verify_service_token` copies onto the UTL factory (3 repos: deployment-api, strategy-service, execution-service). — strategy-service@b41db5684 + execution-service@7454c81a | deployment-api: LEAVE AS-IS (operator-confirmed 2026-06-24: genuine auth-contract difference, not a pure S2S shim). **VERIFIED 2026-06-24 slot-2: NOT a drop-in — the local copies are DIVERGED SUBSETS of UTL's `create_s2s_auth_dependency`.** The 3 local copies have diverged in DIFFERENT directions — it's 3 separate migrations, not one mechanical swap: (1) **strategy-service** (`risk/auth_s2s.py`, 71L) = simple subset (no mock-mode bypass, no event logging, no `request`) → migration ADDS mock-mode bypass (**test-affecting**: local 403s in mock mode, factory accepts any) + S2S event logging + request injection; (2) **execution-service** (`auth_s2s.py`, 125L) = near-factory (has logging+source_ip) but missing mock-mode bypass AND still uses the deprecated `request: Request | None = None` form (the exact pattern UTL's factory comment says breaks under fastapi≥0.136 — latent bug); (3) **deployment-api** (`auth.py`, 92L) = a **fundamentally different auth contract** — `Security(APIKeyHeader)` DI, `DISABLE_AUTH` env (not `CLOUD_MOCK_MODE`), returns `str` not `None`, **401** for missing token (factory uses 403), generic `"AUTH_FAILURE"` string event (not typed `S2S_AUTH_FAILURE`), reads a local `_auth_cfg`. Migrating deployment-api is a genuine auth-CONTRACT change (return type / status code / DI mechanism / disable flag) with internal-endpoint consumer + test blast radius. **OPERATOR-DECISION before any work** — this is a design migration, not cleanup; real SSOT value but auth-sensitive and behaviorally divergent per service. **FLEET CONTEXT (3-agent sweep 2026-06-24): the consolidation is ALREADY ~85% done on LDR — 17 service modules use `create_s2s_auth_dependency` (alerting, deployment-service, features-service×8, mdps, ml-service×2, trading-agent-service, batch-live-recon, AND strategy-service's OWN `position`+`pnl`), only these 3 remain on local copies. So this is FINISHING an established fleet migration, NOT introducing a pattern.** Ranking by ease: (1) **strategy-service/risk = cleanest** — its sibling modules position+pnl already use `create_s2s_auth_dependency("strategy-service")`, and NO test references `verify_service_token` → no test rewrite, just swap the local def + match the sibling factory call; (2) **execution-service** = near-factory but needs a test rewrite (`test_auth_s2s_and_timeline_builder.py` patches the local `_get_service_auth_token` + asserts 403 w/o mock-mode) + carries the latent `request: Request|None` fastapi≥0.136 bug; (3) **deployment-api** = the contract change (operator-decision). **Working tree == LDR for all 3 (no uncommitted divergence).** **Lineage:** born 2026-06-09 in `cicd_contract_hardening_2026_06_01.md` (NICE-TO-HAVE P2 after the UTL fastapi≥0.136 fix) → `cicd_promotion_pipeline_2026_06_18.md` → here; **OPEN `[ ]` in every plan, never completed for the 3 stragglers** (the factory itself dates to ~2026-03-27, created in UCI then moved to UTL). **PROGRESS 2026-06-24 (1 of 3 SHIPPED): strategy-service/risk migrated onto the factory** — `auth_s2s.py` 72L→5L (matches position/pnl siblings) + `request: Request` threaded through `verify_auth` — `strategy-service@b41db5684`, QG-green (sentinel verified, no new violations; the 4 baseline codex violations are pre-existing/within-tolerance & untouched), landed LDR + draining to staging. **Remaining: execution-service** (factory swap + test rewrite — `test_auth_s2s_and_timeline_builder.py` patches the local `_get_service_auth_token` & asserts 403s without mock-mode) **+ deployment-api** (operator-decision; pinged Ikenna 2026-06-24, recommend leave-as-is). (promotion_pipeline ▸ contract_hardening #3)
- [x] ✅ [DOCS] P3. DONE 2026-06-25 (slot-2) — `codex/07-security/service-to-service-auth.md` updated: the **UTL factory `create_s2s_auth_dependency(service_name)`** is now declared the canonical receiver implementation (verified against UTL source — import path, ~5-line binding, mock-mode bypass, 403-on-mismatch, `S2S_AUTH_FAILURE` event, non-optional `Request` for fastapi≥0.136); the hand-rolled per-service `verify_service_token` is marked the **retiring anti-pattern**; the enrolled-services table reflects the 17-already-migrated reality + the 3 remaining (strategy=done, execution=pending, deployment-api=operator-decision); cross-refs repointed at the factory. Prettier-clean. **unified-trading-pm@b63ec7d0a** → LDR. (quality_gates ▸ contract_hardening #3 follow-up)

### WS-J — AWS dual-cloud image builds — **DEFERRED-AWS (leave as-is per operator 2026-06-24)**

> All items below are parked until the AWS VM fleet reactivates. GCP build path is canonical + live; in-image QG dropped
> (operator 2026-06-17). Do NOT action without an AWS-reactivation signal.

- [ ] [BUILD-FIX] P3. Decide the AWS ECR live-target — reconcile TF↔live or retire (gates the two AWS-build-as-main-gate items). (promotion_pipeline ▸ self_healing G5) **[DEFERRED-AWS]**
- [ ] [SCRIPT] P2. Author the AWS build router (mirror `cloud-build-router.yml`); decide router-in-GHA vs CodeBuild-native. (promotion_pipeline ▸ cloud_build_router) **[DEFERRED-AWS]**
- [ ] [SCRIPT] P2. Mirror `notify-build-not-configured` gating into the AWS router. (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [SCRIPT] P2. `buildspec.aws.yaml` generator/template + generate fleet-wide. (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [TEST] P2. Cross-cloud parity test (same Dockerfile / QG / tag / provenance dispatch) in deployment-service QG. (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [SCRIPT] P3. Replace the CodeBuild PUSH webhook with router-driven starts OR document the webhook model. (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [DOC] P2. Codex SSOT § "Dual-cloud image builds" — router→buildspec→QG→push→provenance, both clouds. (promotion_pipeline) **[DEFERRED-AWS]**
- [ ] [INFRA] P3. (optional) Make the GCP `…-live-defi-rollout` build also opt-in (operator decision: cost vs convenience). (promotion_pipeline ▸ self_healing G5) **[DEFERRED-AWS-adjacent]**

### WS-K — operator-gated / external

- [ ] [INFRA] P1. GHA runner provisioning failures block PR #501 (LDR→main drain) — investigate quota/infrastructure. **[DEFERRED — depends on GitHub/GHA recovery; PR #501 auto-merges once a runner provisions a passing v2.]** (promotion_pipeline ▸ agt-c251c2)
- [ ] [OPERATOR] P2. vm-0 slot headroom / Overnight Dead Man Switch — operator look. (release_machinery ▸ ci_incident F3)
- [ ] [OPERATOR] P2. Uninstall the Vercel GitHub App (UI-only; code side already clean). (release_machinery ▸ contract_hardening #36)
- [ ] [OPERATOR] P3. Residual intermittent v2 `conclusion=action_required` — root is the GitHub-Settings approval toggle (auto-recover self-heals the symptom). (promotion_pipeline ▸ promotion_queue)

---

## Recently verified-DONE (flip in the source plans, do NOT re-migrate)

These were already complete-in-prose in the source plans but their checkbox was still open; they are closed, not
remaining work, and are flipped in their source during supersession:

- promotion_pipeline ▸ "First-use watch — normal quickmerge lands on LDR, ~15m drain auto-merges, `--hotfix` hits the lock" — CONFIRMED LIVE 2026-06-23.
- promotion_pipeline ▸ "Drain remaining un-promoted LDR content → STAGING_GREEN" — CONFIRMED 2026-06-23 (no stranded content fleet-wide; squash-count artifacts only).
- promotion_pipeline ▸ "PREMISE-CORRECTED — quickmerge STAGE lock/status read NOT cut over to `tier_c_promotion_gate.py`" — correct-by-design (offline fallback); carries forward into WS-A, not a standalone item.
- starvation ▸ Mode-B per-drain bump cadence — CLOSED won't-change (see D7).

## Success criteria / continuous verification

- **WS-A done** = Phase-4 verify green: `git log` on the integration branches shows ZERO `ci_status` commits; dashboard reads Firestore; promote gates behave identically.
- **WS-B done** = `assert_version_coherence.py` shows 0 VERSION_SPLITs in steady state; no manifest-commit-race alert noise on `staging-to-main` for a full week.
- **WS-C done** = a deliberately-lost version bump is recovered by the dispatch queue; semver-agent runs cleanly on all 23 repos.
- **WS-D done** = local `quality-gates.sh` and CI `quality-gates-v2` produce byte-identical verdicts on a sample repo; no AO doc references `tab/<op>/N`.
- **WS-E done** = all repos carry the `quality-gates-v2` required-check ruleset (greeks / fund-admin / e2e unblocked); removed-symbol orphan count + cap trend DOWN.
- **WS-F done** = live workflow count drops by the folded set; `detect_template_drift.py` green.
- **WS-G done** = the 3 VERIFY-then-fix workflow bugs resolved; event-driven watcher paths live (cron as backstop); deployment-ui renders per-repo CI state.

## Codex SSOT updates (on phase completion)

- `codex/08-workflows/ci-cd-flow.md` — the engineer SSOT; update on every WS-A/B/C/D phase landing (esp. the ci_status-Firestore one-liner + the `*/20`→hourly drift-tick fix in WS-C).
- `codex/05-infrastructure/workspace-setup.md` — receives the migrated bootstrap/venv content (WS-D).
- `codex/06-coding-standards/quality-gates.md` — config-SSOT + parity items (WS-D).
- CLAUDE.md — one-liner when ci_status becomes Firestore-backed (WS-A Phase-4).
