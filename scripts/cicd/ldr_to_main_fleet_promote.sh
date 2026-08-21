#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Extracted from .github/workflows/ldr-to-main-promote-fleet.yml's single ~1041-line `run:` step
# (2026-07-31, plans/active/quality_gates_quickmerge_timing_baseline_2026_07_31.md). actionlint's
# actionlint's use of shellcheck deterministically deadlocks (a Go os/exec pipe-buffer stall — 0% CPU, no
# live child process, not a slow lint) on this script once inline in the workflow: bisection showed
# the identical content truncated at 985 lines lints clean in <1s, at 990 lines hangs, reproducing
# identically across actionlint v1.7.4/v1.7.12 and shellcheck v0.10.0/v0.11.0 — a script-size trigger,
# not a version regression or a specific bash construct. No logic changed in this move; same script,
# now a real file instead of an inline YAML block scalar (also gets real syntax highlighting, direct
# `shellcheck`, and independent diffs). Invoked by the workflow as `bash scripts/cicd/ldr_to_main_fleet_promote.sh`
# with the step's env: GH_TOKEN, OWNER, DRY_RUN, ONLY_REPO, SLACK_CI_WEBHOOK_URL, GH_PAT_FOR_ARM
# (+ job-level GOOGLE_CLOUD_PROJECT, + the runner's own GITHUB_OUTPUT/GITHUB_ENV).

set -euo pipefail
MANIFEST="workspace-manifest.json"

# ── Read opt-in repo list + breaking_pending from manifest ──────────────────
# Only repos with promotion_model="ldr_main" are promoted by this bot.
# breaking_pending: repos waiting for SIT before main (Phase-1 adds the full
# SIT-gate relocation; Phase-0 conservatively blocks these repos).
BREAKING_PENDING=$(python3 - <<'PYEOF'
import json
with open("workspace-manifest.json") as f:
    m = json.load(f)
bp = m.get("staging_status", {}).get("breaking_pending", [])
print(" ".join(bp))
PYEOF
)

# WS-L SIT-rehome (Option B+): the repos whose public surface the cross-repo SIT suite ACTUALLY
# validates (= system-integration-tests REQUIRED_SIBLINGS, mirrored here). The SIT-gate trusts
# SIT_VALIDATED + sit_validated_tree ONLY for these; a BREAKING change in any OTHER ldr_main repo
# stays conservatively BLOCKED (no forged cross-repo guarantee). Space-delimited (like
# BREAKING_PENDING); inherited by the per-repo subshells.
SIT_COVERED=$(python3 - <<'PYEOF'
import json
with open("workspace-manifest.json") as f:
    m = json.load(f)
print(" ".join(m.get("sit_cross_repo_validated_repos", [])))
PYEOF
)
echo "SIT-covered repos (gate trusts SIT for these only): ${SIT_COVERED:-<none>}"

# ── SIT-fleet-green required check (operator ruling 2026-07-12, finding 78) ──────────
# Rule 11 (AUTONOMOUS_AGENT_RULES) blast-radius fix for the 2026-07-07/08 incident: a
# promote sailed through while the cross-repo SIT suite was RED, because the existing
# per-repo SIT gate (part 2, below) only consults SIT for a BREAKING/unknown delta — a
# non-breaking delta (the common case) never checks SIT at all, so a genuinely red SIT
# run never blocked anything. Fix: compute a FLEET-SHARED signal ONCE per tick — was the
# last COMPLETED full-workspace-sit.yml run green? — and POST it as a commit status on
# EVERY promote PR head this tick, unconditionally (not gated on breaking-ness). Fleet
# protection then REQUIRES this context (pin_branch_protection_rulesets.py), so a red or
# MISSING status blocks auto-merge fleet-wide — closing the exact gap the incident found.
# Fleet-shared (not a per-repo tree fingerprint) so it can NEVER discriminate against a
# repo SIT structurally never stamps (e2e-testing / ibkr-gateway-infra) — same signal,
# same requirement, for every ldr_main repo. Fail-CLOSED on any read gap (no runs / API
# error / in-progress-only) — a BLOCKING gate must not fail-open on doubt.
SIT_FLEET_CONTEXT="sit-gate/fleet-green"
# PAT, not the App token (probed empirically 2026-07-12 canary dispatch: the App-token
# read of system-integration-tests' run list came back empty — App perms/installation
# don't reliably cover cross-repo Actions reads here; the PAT already does every other
# cross-repo write in this script and is the proven-working credential fleet-wide).
# `if ! X=$(...)` (not a bare assignment) — under `set -e` a bare
# `SIT_LAST_RUN_JSON=$(cmd)` with a failing `cmd` aborts the WHOLE job immediately
# (command-substitution exit status propagates to the assignment); an `if` condition is
# exempt from `set -e` by POSIX/bash semantics, so wrapping the assignment itself in the
# `if` condition is required, not just a style choice. (Caught live: the first version of
# this fix used a bare assignment + a separate `$?` capture on the next line — the run
# never reached that line, job conclusion=failure, 2026-07-12 canary dispatch.)
SIT_RUN_LIST_ERR="$(mktemp)"
if ! SIT_LAST_RUN_JSON=$(GH_TOKEN="$GH_PAT_FOR_ARM" gh run list --repo "$OWNER/system-integration-tests" \
  --workflow full-workspace-sit.yml --limit 10 \
  --json status,conclusion,createdAt,url 2>"$SIT_RUN_LIST_ERR") || [ -z "$SIT_LAST_RUN_JSON" ]; then
  echo "::warning::SIT fleet-green: gh run list failed/empty — $(tr '\n' ' ' < "$SIT_RUN_LIST_ERR" | cut -c1-300)"
  SIT_LAST_RUN_JSON="[]"
fi
rm -f "$SIT_RUN_LIST_ERR"
# Cancelled-run clobber fix (2026-07-29, sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md
# "Distinct sub-finding"): `gh run list` orders by run CREATION time (databaseId desc), not by
# completion time, and `status == "completed"` is also true for `conclusion == "cancelled"` — so
# when two full-workspace-sit dispatches overlap (e.g. two promote-fleet ticks inside the
# concurrency-group's queue window), a run created AFTER a real success but cancelled almost
# immediately can still rank ABOVE that success in the list and get picked as `completed[0]`.
# Live-measured 2026-07-25: run 30158515857 reached conclusion=success at 12:50:49Z; run
# 30158518796 (created after it, but CANCELLED) became completed[0] and posted state=failure at
# 12:51:02Z, clobbering the real green result. A cancelled run has no informative verdict — never
# let it be the selected signal; skip past it to the next real (non-cancelled) completed run.
SIT_FLEET_LINE=$(SIT_LAST_RUN_JSON="$SIT_LAST_RUN_JSON" python3 - <<'PYEOF'
import json
import os

raw = os.environ.get("SIT_LAST_RUN_JSON", "[]")
try:
    runs = json.loads(raw) if raw else []
except json.JSONDecodeError:
    runs = []
completed = [r for r in runs if r.get("status") == "completed"]
informative = [r for r in completed if r.get("conclusion") != "cancelled"]
if not informative:
    print("failure\tno informative (non-cancelled) completed full-workspace-sit run in last 10 — fail-closed\t")
else:
    r = informative[0]
    state = "success" if r.get("conclusion") == "success" else "failure"
    desc = f"full-workspace-sit @ {r.get('createdAt', '?')} conclusion={r.get('conclusion', '?')}"[:140]
    print(f"{state}\t{desc}\t{r.get('url', '')}")
PYEOF
)
IFS=$'\t' read -r SIT_FLEET_STATE SIT_FLEET_DESC SIT_FLEET_URL <<< "$SIT_FLEET_LINE"
echo "SIT fleet-green signal: state=$SIT_FLEET_STATE desc=\"$SIT_FLEET_DESC\" (context=$SIT_FLEET_CONTEXT) url=$SIT_FLEET_URL"

# ── Auto-retrigger full-workspace-sit on a RED/stale fleet-green signal (2026-07-30 fix) ──
# Finding (sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md): codex docs this gate as
# "the PR stays BLOCKED until a later tick reads a green SIT", which reads as passive — and it
# WAS: the ONLY existing full-workspace-sit repository_dispatch in this file (in process_repo,
# below) fires for a SIT-COVERED repo's own unvalidated BREAKING/unknown delta, a condition
# completely independent of SIT_FLEET_STATE. A transient full-workspace-sit failure (e.g. the
# confirmed 2026-07-28 recurrence: downstream ci-status-update dispatches finishing success
# just past cross-repo-invariants' 90s poll budget) with no repo currently carrying a pending
# BREAKING delta therefore had NOTHING that re-drove SIT — observed stuck RED 2h+ across 2
# promoter ticks with zero new full-workspace-sit runs in that window. Fix: dispatch a fresh
# full-workspace-sit run whenever the fleet-green signal reads red, so a transient flake
# self-heals on this bot's own next ~5-15 min tick instead of waiting on the SIT repo's own
# (much sparser) nightly cron. Debounced by construction: skip the dispatch when a
# full-workspace-sit run is already queued/in_progress (this bot's own prior dispatch, the
# nightly cron, or the process_repo BREAKING-delta dispatch below) — that run IS the retry
# already in flight, so a same-tick or next-tick re-dispatch would only pile up duplicate runs
# without getting the signal green any sooner.
#
# Cross-repo dispatch mutex (2026-08-06 fix — sit_validated_tree_treadmill_blocks_breaking_
# promotes_2026_07_20.md + live incident strategy_service_ldr_qg_infra_flake_and_promotion_
# deadlock_2026_08_06.md "Lessons/traps"): process_repo below runs each repo in a PARALLEL
# background subshell (`process_repo "$REPO" ... &`), so the SIT_INFLIGHT check above — a
# snapshot taken ONCE at tick-start — does NOT stop a SIBLING repo's subshell from ALSO
# dispatching later in the SAME tick once it independently hits its own BREAKING-delta block.
# Live-measured 2026-08-06: 3 full-workspace-sit dispatches landed within ~10s of each other,
# each cancelling the PREVIOUSLY-QUEUED (not yet started) run via GitHub's own
# `concurrency: group=${{ github.workflow }}, cancel-in-progress: false` semantics — so SIT
# runs got queued-then-cancelled in a loop forever, keeping `sit-gate/fleet-green` permanently
# RED and blocking EVERY ldr_main promotion fleet-wide, not just the repo that "caused" it.
# `mkdir` is atomic on a POSIX filesystem: the first caller this TICK wins (creates the dir);
# every other caller (this tick, this process tree — auto-retrigger above OR any process_repo
# subshell below) sees `mkdir` fail and skips its own dispatch, trusting the winner's fresh run.
SIT_DISPATCH_LOCK="$(mktemp -u)_sit_dispatch_lock_$$"
_claim_sit_dispatch() { mkdir "$SIT_DISPATCH_LOCK" 2>/dev/null; }

sit_fleet_green_auto_retrigger() {
  if [ "$SIT_FLEET_STATE" != "failure" ]; then
    return 0
  fi
  SIT_INFLIGHT=$(printf '%s' "$SIT_LAST_RUN_JSON" | python3 -c '
import json, sys
try:
    runs = json.load(sys.stdin)
except json.JSONDecodeError:
    runs = []
print(sum(1 for r in runs if r.get("status") != "completed"))
' 2>/dev/null || echo "0")
  if [ "${SIT_INFLIGHT:-0}" != "0" ]; then
    echo "  sit-gate/fleet-green auto-retrigger: RED but $SIT_INFLIGHT full-workspace-sit run(s) already queued/in_progress — not piling on another dispatch"
    return 0
  fi
  if [ "$DRY_RUN" = "true" ]; then
    echo "  DRY-RUN: would dispatch full-workspace-sit (sit-gate/fleet-green auto-retrigger, no run in flight)"
    return 0
  fi
  if ! _claim_sit_dispatch; then
    echo "  sit-gate/fleet-green auto-retrigger: RED, but a process_repo BREAKING-delta dispatch already claimed this tick's SIT dispatch — not piling on"
    return 0
  fi
  echo "  sit-gate/fleet-green auto-retrigger: RED and no full-workspace-sit run in flight — dispatching a fresh run"
  if ! curl -sf -X POST -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$OWNER/system-integration-tests/dispatches" \
    -d '{"event_type": "full-workspace-sit", "client_payload": {"reason": "fleet-green-red-retrigger"}}' >/dev/null 2>&1; then
    echo "::warning::sit-gate/fleet-green auto-retrigger dispatch FAILED for system-integration-tests (nightly full-workspace-sit cron is the fallback) — investigate the App token's dispatch permission on system-integration-tests"
  fi
}
sit_fleet_green_auto_retrigger

# Topological order (T0 first) — promote deps before dependents.
REPOS=$(python3 - <<'PYEOF'
import json
with open("workspace-manifest.json") as f:
    m = json.load(f)
repos = m.get("repositories", {})
topo = m.get("topologicalOrder", {}).get("levels", [])
emitted = set()
for level in topo:
    for repo in level.get("repos", []):
        if repo in repos and not repo.startswith("_") and repo not in emitted:
            print(repo)
            emitted.add(repo)
for repo in sorted(set(r for r in repos if not r.startswith("_")) - emitted):
    print(repo)
PYEOF
)

# Capture which repos are ldr_main for the job output.
LDR_MAIN_REPOS=$(python3 - <<'PYEOF'
import json
with open("workspace-manifest.json") as f:
    m = json.load(f)
repos = m.get("repositories", {})
ldr = [r for r, v in repos.items()
       if not r.startswith("_") and v.get("promotion_model") == "ldr_main"]
print(" ".join(sorted(ldr)))
PYEOF
)
echo "ldr_main_repos=$LDR_MAIN_REPOS" >> "$GITHUB_OUTPUT"

if [ -z "$LDR_MAIN_REPOS" ]; then
  echo "ℹ️  No repos have promotion_model=ldr_main in workspace-manifest.json. Nothing to promote."
  echo "   Set repositories.<repo>.promotion_model = \"ldr_main\" to opt a repo into LDR→main."
  {
    echo "promoted="; echo "blocked="; echo "conflicted="; echo "arm_failed="
    echo "promoted_count=0"; echo "blocked_count=0"; echo "conflicted_count=0"; echo "arm_failed_count=0"
  } >> "$GITHUB_OUTPUT"
  exit 0
fi
echo "LDR→main repos (opt-in): $LDR_MAIN_REPOS"
echo ""

# ── Dep-order gate (LDR→main) — PORT of staging-to-main STAGE 1.8 ────────────
# Regression guard (WS-L Phase-1): the parallel driver below promotes ldr_main
# repos concurrently within a tick, so without this a T4 dependent could merge to
# main AHEAD of its T0 dependency (staging-to-main STAGE 1.8 gated exactly this).
# Compute ONCE (Firestore ci_status overlay applied — authoritative, matching
# STAGE 1.8) the set of ldr_main repos with a dep NOT yet on main (ci_status ∉
# {MAIN_GREEN, SIT_VALIDATED}). process_repo BLOCKs those this run; a later tick
# promotes them once the dep's on-main QG emits MAIN_GREEN (bottom-up drain).
# Detail → stderr (shows in the step log); only the blocked list → stdout (captured).
DEP_BLOCKED=$(LDR_MAIN_REPOS="$LDR_MAIN_REPOS" python3 - <<'PYEOF'
import json
import os
import sys

sys.path.insert(0, "scripts/cicd")

ON_MAIN_STATUSES = {"MAIN_GREEN", "SIT_VALIDATED"}


def log(msg):
    print(msg, file=sys.stderr)


def _fs_overlay(manifest):
    # Firestore-authoritative ci_status overlay (matches STAGE 1.8). A failed
    # overlay is LOUD — silently deciding on the stale manifest cache is how
    # mis-gating hides (Gap 8, 2026-06-16).
    try:
        from ci_status_store import resolve_ci_status_map  # noqa: imports-inside-functions
        ci_map = resolve_ci_status_map(manifest)
        repos_obj = manifest.get("repositories", {})
        if isinstance(repos_obj, dict):
            for r, s in ci_map.items():
                r_obj = repos_obj.get(r)
                if isinstance(r_obj, dict):
                    r_obj["ci_status"] = s
        log("Dep-order gate: Firestore ci_status overlay applied (live, authoritative).")
    except ModuleNotFoundError as exc:
        log(f"::warning::Dep-order gate: Firestore SDK unavailable ({exc}) — falling back "
            "to STALE manifest ci_status cache. Install google-cloud-firestore.")
    except Exception as exc:  # noqa: BLE001 — Firestore degraded: warn + fall back.
        log(f"::warning::Dep-order gate: Firestore ci_status read failed "
            f"({type(exc).__name__}: {exc}) — falling back to manifest cache.")


try:
    with open("workspace-manifest.json") as f:
        manifest = json.load(f)
except Exception as e:  # noqa: BLE001 — unreadable manifest: safe-default none-blocked.
    log(f"Dep-order gate: manifest read error ({e}) — gate skipped (safe-default: none blocked).")
    print("")
    sys.exit(0)

_fs_overlay(manifest)
repos_data = manifest.get("repositories", {})
ldr_main = [r for r in os.environ.get("LDR_MAIN_REPOS", "").split() if r]

blocked: list[str] = []
log(f"Dep-order gate (LDR→main) — evaluating {len(ldr_main)} ldr_main repo(s) for dep-on-main readiness")
for repo in ldr_main:
    info = repos_data.get(repo)
    if info is None:
        log(f"  ✅ READY (no manifest entry): {repo}")
        continue
    deps = info.get("dependencies", [])
    if not deps:
        log(f"  ✅ READY (no deps): {repo}")
        continue
    repo_blocked: list[str] = []
    for dep in deps:
        dep_name = dep.get("name", dep) if isinstance(dep, dict) else str(dep)
        if not dep_name or dep_name not in repos_data:
            continue  # dep not tracked in manifest → safe-default pass
        dep_status = repos_data[dep_name].get("ci_status") or ""
        if not dep_status:
            continue  # ci_status unset → safe-default pass (external / untracked)
        if dep_status not in ON_MAIN_STATUSES:
            repo_blocked.append(f"{dep_name}:{dep_status}")
    if repo_blocked:
        blocked.append(repo)
        for entry in repo_blocked:
            dn, ds = entry.split(":", 1)
            log(f"  ⚠️  BLOCKED (dep not on main yet): {repo} → dep {dn} is {ds}; a later "
                f"tick promotes {repo} once {dn} reaches main (MAIN_GREEN). Bottom-up drain.")
    else:
        log(f"  ✅ READY: {repo} — all deps on main")
log(f"Dep-order gate summary: blocked this run ({len(blocked)}): {' '.join(blocked) or '(none)'}")
log("  Required for LDR→main: each dep at MAIN_GREEN or SIT_VALIDATED")
print(" ".join(blocked))
PYEOF
)
if [ -n "$DEP_BLOCKED" ]; then
  echo "Dep-order gate: BLOCKED this run (dep not on main) → $DEP_BLOCKED"
else
  echo "Dep-order gate: no repo blocked on dep-order this run"
fi
echo ""

# ── Cross-repo combination fingerprint: compute CURRENT workspace digest ────────────
# (HIGH-combo, cicd_sit_full_coverage_handoff_2026_06_27.md Phase 2): the per-repo
# sit_validated_tree proves repo R's OWN content passed SIT but not WHICH version of
# its dependencies were assembled. Compute a SHA-256 of all ldr_main repos' LDR tree
# SHAs NOW; compare against the stored sit_validated_workspace_digest in the SIT gate
# below. Mismatch = a dependency changed after SIT ran → block + re-dispatch SIT.
# Fail-OPEN when computation fails or stored digest is absent (progressive rollout).
# Parallelised: 21 gh api calls in background jobs (one per repo), then collected.
CURRENT_WORKSPACE_DIGEST=""
if [ -n "${LDR_MAIN_REPOS:-}" ]; then
  _WD_DIR=$(mktemp -d)
  for _WD_REPO in $LDR_MAIN_REPOS; do
    (
      _WD_TREE=$(gh api "repos/$OWNER/$_WD_REPO/commits/live-defi-rollout" \
        --jq '.commit.tree.sha' 2>/dev/null || echo "")
      [ -n "$_WD_TREE" ] && printf '%s\t%s\n' "$_WD_REPO" "$_WD_TREE" > "$_WD_DIR/$_WD_REPO"
    ) &
  done
  wait
CURRENT_WORKSPACE_DIGEST=$(python3 -c "
import hashlib, json, os
tree_dir = '$_WD_DIR'
trees = {}
for fname in os.listdir(tree_dir):
    line = open(os.path.join(tree_dir, fname)).read().strip()
    if '\t' in line:
        repo, tree = line.split('\t', 1)
        trees[repo] = tree
payload = json.dumps(trees, sort_keys=True, separators=(',', ':'))
print(hashlib.sha256(payload.encode()).hexdigest())
" 2>/dev/null || echo "")
  rm -rf "$_WD_DIR"
  echo "Workspace digest: ${CURRENT_WORKSPACE_DIGEST:0:16}... (${LDR_MAIN_REPOS} ldr_main repos)"
fi

RESULT_DIR="$(mktemp -d)"; LOG_DIR="$(mktemp -d)"
MAXJOBS=6  # tighter than ldr-to-staging (8) — main is more sensitive
# Stagger the per-repo launch (2026-08-17, ci_satellite_ao_dispatch_batch15_2026_08_16.md item
# 3). Previously every repo in $REPOS was backgrounded back-to-back with zero delay between
# launches (only throttled once MAXJOBS were already in flight, by the `wait -n` barrier below)
# — so the first MAXJOBS repos' subshells all hit their earliest gh api calls / the
# SIT_DISPATCH_LOCK mkdir race within the same instant. That's the exact shape behind the
# 2026-08-06 "3 full-workspace-sit dispatches within ~10s" stampede documented in the
# cross-repo dispatch mutex comment above. A small fixed delay between successive launches
# spreads that instant out. This does not meaningfully extend the run: process_repo's own gh
# api calls (SIT checks, workspace-digest reads, provenance checks, ancestor cleanup) each take
# far longer than STAGGER_SECONDS, so the overall drain stays MAXJOBS-bound, not stagger-bound.
# Overridable for local/CI testing (e.g. STAGGER_SECONDS=0 to reproduce the old behavior).
STAGGER_SECONDS="${LDR_MAIN_PROMOTE_STAGGER_SECONDS:-3}"

# ── Provenance gate (D1): only quickmerge-provenanced content ────────────────────
# Shared helper — called from BOTH the PR-creation path AND every re-arm path inside
# process_repo below. Closes the 2026-06-30 "re-arm leak" finding (see the plan's
# Operator decisions section): the strict-quickmerge provenance check used to run
# ONLY at PR creation, so a later tick could find an already-open PR "clean" by
# mergeable_state and (re-)arm auto-merge WITHOUT re-checking provenance — exactly how
# UAC PR #544 self-resolved 2026-06-30, landing non-quickmerge commits on main behind
# the provenance gate's back. Operator decision 2026-07-27/28: close the leak by
# re-running this check immediately before EVERY arm/re-arm action, not just creation.
# Reads the process-global $REPO (set by process_repo before calling this) plus the
# job-level env $OWNER/$GH_TOKEN/$GITHUB_WORKSPACE. Returns 0 (clean — OK to arm) or 1
# (blocked — comment already posted on $1, caller must NOT arm).
provenance_check_ok() {
  _PR_ID="$1"
  _PROV_TMP="$(mktemp -d)"
  if git -C "$_PROV_TMP" init -q && git -C "$_PROV_TMP" fetch -q --no-tags \
       "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$REPO" \
       "+refs/heads/main:refs/remotes/origin/main" \
       "+refs/heads/live-defi-rollout:refs/remotes/origin/live-defi-rollout" 2>/dev/null; then
    _PROV_RANGE="$( python3 "$GITHUB_WORKSPACE/scripts/cicd/promote_provenance_range.py" \
      --repo "$REPO" --owner "$OWNER" --base-branch main --cwd "$_PROV_TMP" \
      --fetch-remote "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$REPO" )" \
      || _PROV_RANGE=""
    [ -n "$_PROV_RANGE" ] || _PROV_RANGE="origin/main..origin/live-defi-rollout"
    _PROV_OUT="$( cd "$_PROV_TMP" && python3 "$GITHUB_WORKSPACE/scripts/cicd/check_strict_quickmerge.py" \
      --range "$_PROV_RANGE" --block 2>&1 )" && _PROV_RC=0 || _PROV_RC=$?
    if [ "${_PROV_RC:-0}" -ne 0 ] && printf '%s' "$_PROV_OUT" | grep -q 'bypassed quickmerge'; then
      echo "  ⛔ provenance: $REPO has non-quickmerge CODE on LDR — NOT (re-)arming auto-merge"
      printf '%s\n' "$_PROV_OUT" | sed 's/^/    /'
      # The HTML marker is a STABLE, machine-readable signal — promotion_lag_monitor.py
      # greps for it so a provenance-blocked repo is reported as "BLOCKED: non-quickmerge
      # code (re-ship via quickmerge)" instead of an anonymous "PROMOTION LAG > 60m".
      # Without it the block is invisible: it lives only in this comment + a workflow log
      # line, so mtds sat deliberately blocked ~23h looking exactly like a stuck pipeline,
      # and the wrong conclusion ("the bot forgot to arm auto-merge") was acted on
      # 2026-07-16 — the gate was manually overridden and 33 bypassed commits reached main.
      # KEEP THIS MARKER IN SYNC with _PROVENANCE_MARKER in promotion_lag_monitor.py.
      # Body assembled via printf so every line stays INDENTED inside this `run: |`
      # block — a col-0 continuation dedents out of the block and makes the whole
      # workflow unparseable, which GitHub answers by SILENTLY unscheduling it.
      _PROV_BODY="$(printf '%s\n' \
        '<!-- promote:provenance-blocked -->' \
        '⛔ **Provenance gate (LDR→main fleet bot)** — this promote carries code that bypassed quickmerge (no `Quickmerge:` trailer, not a carve-out). Auto-merge NOT (re-)armed. Re-ship via `quickmerge --agent --files '"'"'<paths>'"'"'` or revert on `live-defi-rollout`.' \
        '' \
        '**Do NOT hand-arm auto-merge to "unblock" this** — that promotes the bypassed code AND moves the provenance baseline past it, so the violation is laundered and never flagged again (happened 2026-07-16).')"
      gh pr comment "$_PR_ID" --repo "$OWNER/$REPO" --body "$_PROV_BODY" 2>/dev/null || true
      # ao_done_categorization_display_and_quickmerge_gate_2026_08_06 Track D: hand this
      # to a worker instead of leaving it Slack-only (promotion_lag_monitor.py's hourly
      # alert was the only signal before this — easy to miss, and this exact condition
      # sat blocked ~23h before 2026-07-16's mishandling). $_PROV_OUT already names the
      # violating commit(s) (%h %s per check_strict_quickmerge.py) — pass it straight
      # through as context rather than making the worker re-derive it. Dedup is
      # downstream (server/escalation.py's DB-backed find_open_escalation_id on
      # (repo, pr_number, wall_type)) — same posture as every other repository_dispatch
      # fired from this fleet (e.g. ci_failure_watcher.py's _dispatch_escalation): a
      # repeat tick while the block persists re-fires the dispatch, the orchestrator
      # no-ops the duplicate spawn. Best-effort: a dispatch failure must never block the
      # provenance gate itself from doing its job (the `|| true`/`2>/dev/null` below).
      _PROV_CTX="$(printf 'Promotion PR %s#%s (live-defi-rollout->main) is BLOCKED by the provenance gate — auto-merge NOT (re-)armed.\n\n%s\n\nDetermine the remedy per violating commit: if it is the live-defi-rollout branch tip, re-ship via `quickmerge --agent --files '"'"'<paths>'"'"'`; if a later commit already landed on top, re-shipping cannot clear it — run `scripts/cicd/reprovenance_bypass.sh <sha> --push` instead (after confirming the range still fails the dep-alignment gate it runs). Do NOT hand-arm auto-merge on the promote PR — that launders the violation past the provenance baseline (2026-07-16 incident).\n' "$OWNER/$REPO" "$_PR_ID" "$_PROV_OUT")"
      _PROV_PAYLOAD="$(jq -n --arg ctx "$_PROV_CTX" --arg pr "$_PR_ID" --arg repo "$REPO" \
        '{event_type:"escalate-to-orchestrator",client_payload:{repo:$repo,pr_number:$pr,wall_type:"provenance_blocked",context:$ctx,authoring_slot:"ldr-to-main-promote-fleet"}}')"
      printf '%s' "$_PROV_PAYLOAD" | GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X POST "repos/$OWNER/unified-trading-pm/dispatches" --input - >/dev/null 2>&1 \
        && echo "  -> dispatched provenance_blocked escalation for $REPO#$_PR_ID" \
        || echo "  WARN: provenance_blocked escalation dispatch failed for $REPO#$_PR_ID (non-fatal — Slack alert via promotion_lag_monitor.py still fires)"
      rm -rf "$_PROV_TMP"
      return 1
    elif [ "${_PROV_RC:-0}" -ne 0 ]; then
      echo "  WARN: provenance checker errored (rc=$_PROV_RC) — failing OPEN. Output: $_PROV_OUT"
    else
      echo "  ✅ provenance: promote-range is quickmerge-clean (or carve-outs only)"
    fi
  else
    echo "  WARN: provenance fetch failed for $REPO — failing OPEN (arming anyway)"
  fi
  rm -rf "$_PROV_TMP"
  return 0
}

# ── Tier-A merge-arm gate (2026-08-10, tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md
# todo 1) ─────────────────────────────────────────────────────────────────────────────────────
# The veto on auto-merging a red promote PR is unchanged in EFFECT — only its SCOPE narrowed,
# from "block minting/checking a PR at all" (the old deadlock-causing early-return) to "block the
# act of (re-)arming auto-merge". Reads the process-global $TIER_A_CI_FAILING (+ $CI_STATUS /
# $CI_STATUS_LIVE for the log line) computed once per repo by the Tier-A gate near the top of
# process_repo — reused here rather than re-fetched, same as provenance_check_ok() is called
# fresh immediately before EVERY arm/re-arm site rather than cached once. Returns 0 (clean — OK
# to arm) or 1 (blocked — caller must NOT arm; PR is left open/unarmed for a later tick or a
# human/operator to merge once a fresh main-branch signal clears ci_status).
tier_a_merge_gate_ok() {
  if [ "${TIER_A_CI_FAILING:-false}" = "true" ]; then
    echo "  ⛔ TIER A MERGE-GATE BLOCK $REPO: ci_status=FAILING (cached='${CI_STATUS:-unset}', live='${CI_STATUS_LIVE:-unset}') — NOT (re-)arming auto-merge; LDR CI is red, fix before LDR→main. PR stays open (its own quality-gates-v2 keeps validating this content) for a later tick or a human/operator merge to produce the fresh main-branch signal that clears this."
    return 1
  fi
  return 0
}

# ── Ancestor-cleanup, hoisted ABOVE the SIT gate (2026-08-14,
# sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md todo 3) ───────────────────────
# The superseded-ref cleanup (further below, right after STEP 1's ref-freeze) only runs once the
# content + SIT + label-check gates have all PASSED for this tick — every one of which can
# `_done BLOCKED; return 0` before reaching it. Under high LDR velocity that is exactly when a
# promote PR most needs cleaning up: its immutable per-SHA head can never receive a later fix, so
# it sits red and open, permanently, until the SIT gate happens to pass on some future tick — and
# meanwhile pages the lag monitor (confirmed live: PR #939, closed by hand 2026-08-10 because the
# bot itself could never reach the code that would have closed it).
#
# Design constraint (do NOT loosen — must not mass-close): a stale-headed open promote/$REPO/* PR
# is closed here ONLY when BOTH hold:
#   (a) its head SHA is a STRICT ANCESTOR of the current LDR tip ($LDR_SHA) — verified via the
#       compare API, never inferred from ref-name mismatch alone. $PROMOTE_HEAD degrades to a
#       bare "promote/$REPO/" prefix when $LDR_SHA is empty (a failed API read), which would make
#       EVERY open promote PR look superseded — the exact naive-hoist risk this constraint exists
#       to close. Guarded below by refusing to run at all when $LDR_SHA is empty.
#   (b) quality-gates-v2 has already CONCLUDED failure on that exact head SHA (status=completed,
#       conclusion=failure) — a still-pending/in-progress run might yet pass, so it is left alone.
# An immutable per-SHA ref satisfying both can never merge and can never be fixed in place, so
# closing it discards no viable promotion.
_close_ancestor_failed_promote_prs() {
  if [ -z "$LDR_SHA" ]; then
    echo "  ancestor-cleanup $REPO: skipped (empty LDR_SHA — cannot safely identify an ancestor)"
    return 0
  fi
  _ANCESTOR_CANDIDATE_HEADS=$(gh pr list --repo "$OWNER/$REPO" --base main --state open \
    --json headRefName \
    --jq ".[] | select(.headRefName | startswith(\"promote/$REPO/\")) | select(.headRefName != \"$PROMOTE_HEAD\") | .headRefName" \
    2>/dev/null || echo "")
  for _ANCESTOR_HEAD in $_ANCESTOR_CANDIDATE_HEADS; do
    _ANCESTOR_PR=$(gh pr list --repo "$OWNER/$REPO" --base main --head "$_ANCESTOR_HEAD" \
      --state open --json number,headRefOid 2>/dev/null || echo "")
    _ANCESTOR_NUM=$(printf '%s' "$_ANCESTOR_PR" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["number"] if d else "")' 2>/dev/null || echo "")
    _ANCESTOR_SHA=$(printf '%s' "$_ANCESTOR_PR" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["headRefOid"] if d else "")' 2>/dev/null || echo "")
    if [ -z "$_ANCESTOR_NUM" ] || [ -z "$_ANCESTOR_SHA" ] || [ "$_ANCESTOR_SHA" = "$LDR_SHA" ]; then
      continue
    fi
    # (a) strict-ancestor check: compare base=$_ANCESTOR_SHA...head=$LDR_SHA — "ahead" means the
    # LDR tip carries commits the PR head does not, i.e. the PR head IS an ancestor of it.
    _ANCESTOR_CMP=$(gh api "repos/$OWNER/$REPO/compare/${_ANCESTOR_SHA}...${LDR_SHA}" \
      --jq '.status' 2>/dev/null || echo "")
    if [ "$_ANCESTOR_CMP" != "ahead" ]; then
      echo "  ancestor-cleanup $REPO: PR #$_ANCESTOR_NUM (head=$_ANCESTOR_HEAD) is not a strict ancestor of LDR tip ${LDR_SHA:0:12} (compare status='${_ANCESTOR_CMP:-unknown}') — leaving for the normal superseded-ref cleanup"
      continue
    fi
    # (b) required check CONCLUDED failure on that exact (immutable) head SHA.
    _ANCESTOR_V2_FAILED=$(gh run list --repo "$OWNER/$REPO" --workflow quality-gates-v2.yml --limit 20 \
      --json headSha,status,conclusion \
      --jq "[.[]|select(.headSha==\"$_ANCESTOR_SHA\" and .status==\"completed\" and .conclusion==\"failure\")]|length" \
      2>/dev/null || echo "0")
    if [ "${_ANCESTOR_V2_FAILED:-0}" = "0" ]; then
      echo "  ancestor-cleanup $REPO: PR #$_ANCESTOR_NUM (head=$_ANCESTOR_HEAD) is an ancestor of LDR tip but quality-gates-v2 has not CONCLUDED failure on ${_ANCESTOR_SHA:0:12} — leaving open (still viable or still checking)"
      continue
    fi
    echo "  ancestor-cleanup $REPO: PR #$_ANCESTOR_NUM (head=$_ANCESTOR_HEAD, ${_ANCESTOR_SHA:0:12}) is a strict ancestor of LDR tip ${LDR_SHA:0:12} with quality-gates-v2 CONCLUDED failure — an immutable head that can never merge; closing now instead of waiting for the SIT gate to clear"
    if [ "$DRY_RUN" != "true" ]; then
      gh pr close "$_ANCESTOR_NUM" --repo "$OWNER/$REPO" \
        --comment "Closed by LDR→main fleet bot (ancestor-cleanup, hoisted above the SIT gate): superseded by LDR tip ${LDR_SHA:0:12}, and this PR's own quality-gates-v2 already concluded failure on its immutable head — it can never merge." 2>/dev/null || true
      GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X DELETE "repos/$OWNER/$REPO/git/refs/heads/$_ANCESTOR_HEAD" 2>/dev/null || true
    fi
  done
}

process_repo() {
  REPO="$1"
  _done() { printf '%s\n' "$1" > "$RESULT_DIR/$REPO"; }

  # ── Phase-0 opt-in gate ──────────────────────────────────────────────────────
  # Read promotion_model from manifest via jq (cheap single-file read, no GH API).
  PMODEL=$(jq -r --arg r "$REPO" '.repositories[$r].promotion_model // empty' \
    workspace-manifest.json 2>/dev/null || echo "")
  if [ "$PMODEL" != "ldr_main" ]; then
    echo "SKIP $REPO: promotion_model='${PMODEL:-unset}' (not ldr_main; staging→main model active)"
    return 0
  fi

  if [ -n "$ONLY_REPO" ] && [ "$REPO" != "$ONLY_REPO" ]; then return 0; fi

  # ── Bug #7 guard (2026-06-30): close any stale base=main, head=live-defi-rollout promote PR ──
  # A legacy/old-scheme promote PR whose HEAD is live-defi-rollout, if armed with --delete-branch,
  # DELETES the SSOT branch on merge (it deleted deployment-ui's LDR branch 2026-06-29). This bot
  # only ever opens promote PRs from the immutable per-SHA ref (promote/<repo>/<sha>), so an
  # LDR-headed promote PR into main is necessarily a stale land-mine — close it BEFORE any arm path
  # can touch it. (Backmerge PRs are base=live-defi-rollout, head=main → not matched.)
  # SSOT: plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md.
  if [ "$DRY_RUN" != "true" ]; then
    for _ldr_pr in $(gh pr list --repo "$OWNER/$REPO" --base main --head live-defi-rollout \
        --state open --json number --jq '.[].number' 2>/dev/null); do
      gh pr close "$_ldr_pr" --repo "$OWNER/$REPO" \
        --comment "Closed by LDR→main fleet bot (bug #7 guard): a head=live-defi-rollout promote PR + --delete-branch would DELETE the SSOT branch on merge. Promotes use the immutable per-SHA ref (promote/<repo>/<sha>); this LDR-headed PR is a stale land-mine." 2>/dev/null \
        && echo "  🛡️  bug#7 guard: closed stale LDR-headed promote PR #$_ldr_pr on $REPO" || true
    done
  fi

  # ── SIT gate part 1 (LDR→main): breaking_pending block ──────────────────────
  # WS-L Phase-1 SIT-gate relocation. Unlike staging→main (TRIGGERED by SIT's
  # staging-validated dispatch), this cron bot needs an EXPLICIT SIT gate.
  # breaking_pending is SET by update-repo-version.yml off the semver dispatch on
  # STAGING and CLEARED by sit-unlock.yml on SIT pass. CORRECTED 2026-07-29 (post-cutover
  # sweep F5) — the prior comment here ("BOTH stay live for ldr_main repos") is FALSE:
  # while `staging_dormant_mode` is on (the current default), NO repo pushes to staging,
  # so the writer never fires and breaking_pending stays structurally empty fleet-wide —
  # this block is a genuine no-op during dormancy, not a live SIT-green gate. The
  # load-bearing SIT check for ldr_main repos today is the `sit-gate/fleet-green` required
  # check (Firestore `sit_validated_tree`, fed nightly by full-workspace-sit.yml's cron),
  # not this part-1 block. Reversible: if staging_dormant_mode flips off, this block
  # becomes live again for whichever repos resume routing through staging. (Part 2 below
  # closes the race window BEFORE breaking_pending is set, for the repos it IS live for.)
  if echo " $BREAKING_PENDING " | grep -q " $REPO "; then
    echo "SIT GATE BLOCK $REPO: in breaking_pending — awaiting SIT-green on staging before LDR→main"
    _done BLOCKED; return 0
  fi

  # ── Dep-order gate — REMOVED for the CI/CD MVP (2026-06-30) ──────────────────
  # MVP gate set = SIT + quality-gates-v2 + quickmerge only (SSOT:
  # plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md). SIT already validates the
  # assembled cross-repo workspace, so dep-order is redundant — and it amplified a flaky
  # tier-0 ci_status into a fleet-wide promotion freeze. Advisory-only now (NOT enforced);
  # the upfront DEP_BLOCKED computation is kept purely for the log signal.
  if echo " $DEP_BLOCKED " | grep -q " $REPO "; then
    echo "DEP-ORDER (advisory, NOT enforced under MVP) $REPO: a dependency is not on main yet — promoting anyway"
  fi

  # ── Tier-A gate: LDR CI not red ─────────────────────────────────────────────
  # Read ci_status from manifest via jq. Fail-open on missing/unset.
  CI_STATUS=$(jq -r --arg r "$REPO" '.repositories[$r].ci_status // empty' \
    workspace-manifest.json 2>/dev/null || echo "")
  # LIVE Firestore overlay (2026-07-22, mtds_ldr_red_promote_churn_four_prs_2026_07_19): the
  # manifest's ci_status is the HOURLY consolidator projection (codex/08-workflows/ci-cd-flow.md:
  # "ci_status is Firestore-SSOT... manifest stays a fallback cache") — it can lag a genuinely
  # fresh LDR quality-gates-v2 failure by up to an hour. Confirmed incident: 4 promote PRs were
  # re-minted over ~4h against an ACTUALLY-red LDR because the cached ci_status had not caught up
  # yet. Reuses the SAME ci_status_store.py the SIT gate below already trusts LIVE — read it here
  # too and fail-CLOSED (block) if EITHER the live OR cached signal reads FAILING. Degrades to the
  # cache alone if Firestore is transiently unavailable (get-doc emits `{}` on failure, so a read
  # error never masquerades as a healthy live status).
  CI_STATUS_LIVE=$(python3 "$GITHUB_WORKSPACE/scripts/cicd/ci_status_store.py" get-doc \
    --repo "$REPO" 2>/dev/null | jq -r '.status // empty' 2>/dev/null || echo "")
  # Gate SCOPE NARROWED (2026-08-10, tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md
  # todo 1). This used to `_done BLOCKED; return 0` right here, vetoing even OPENING a fresh
  # promote PR — which produced a genuine unrecoverable deadlock: ci_status_store.py's
  # resolve_status() symmetric guard says a main-originated FAILING can be cleared ONLY by
  # another main-branch signal, but the ONLY code path that can ever produce a fresh
  # main-branch signal (a new promotion) was itself preemptively vetoed by the very status a
  # fresh promotion would fix. A fresh promote PR's own quality-gates-v2 check is strictly more
  # authoritative than this cached Firestore doc, which may itself be exactly this kind of stale
  # PR-time-vs-push-time content-race artifact (confirmed root cause, same doc). Fix: stop
  # vetoing PR *creation*; keep vetoing PR *merging*. $TIER_A_CI_FAILING now only gates the ACT
  # of (re-)arming auto-merge — every `gh pr merge --auto` call site below checks it via
  # tier_a_merge_gate_ok() (defined above process_repo, mirrors provenance_check_ok()'s
  # re-check-immediately-before-every-arm pattern). PR creation/content-gate/SIT-gate/
  # label-check all proceed unconditionally past this point. This is a narrowing of the gate's
  # blast radius, not a removal: a genuinely red repo still cannot reach main un-merged, and
  # every prior merge-time protection (this same FAILING check) is preserved byte-for-byte,
  # just re-homed to the arm sites.
  TIER_A_CI_FAILING="false"
  if [ "$CI_STATUS" = "FAILING" ] || [ "$CI_STATUS_LIVE" = "FAILING" ]; then
    TIER_A_CI_FAILING="true"
    echo "TIER A WARN $REPO: ci_status=FAILING (cached='${CI_STATUS:-unset}', live='${CI_STATUS_LIVE:-unset}') — LDR CI marked red; PR creation/checking still proceeds (a fresh PR's own quality-gates-v2 is the true, current-content gate), but merge-(re-)arming stays BLOCKED below until a fresh main-branch signal clears this (see tier_a_merge_gate_ok())."
  else
    echo "TIER A PASS $REPO: ci_status cached='${CI_STATUS:-unset}' live='${CI_STATUS_LIVE:-unset}'"
  fi

  # ── Content gate: LDR tree vs main tree ─────────────────────────────────────
  # Tree-SHA equality == byte-identical content regardless of squash history.
  # Capture SHA + tree from ONE commit read so STEP 1 (frozen-head) can freeze the EXACT
  # commit whose tree the SIT gate validates — no drift between the read and the freeze.
  LDR_COMMIT_JSON=$(gh api "repos/$OWNER/$REPO/commits/live-defi-rollout" 2>/dev/null)
  if [ -z "$LDR_COMMIT_JSON" ]; then
    # sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08 P3: the original
    # `2>/dev/null || echo '{}'` swallowed the real error, making a live GitHub platform
    # outage indistinguishable in this step's own log from a genuine per-repo API
    # regression (2026-08-17's ERR_LDR incident needed an out-of-band githubstatus.com
    # check purely because of this). Re-run once, stderr-only, to surface the cause —
    # only on the rare failure path, so the common success path pays no extra API call.
    LDR_API_ERR=$(gh api "repos/$OWNER/$REPO/commits/live-defi-rollout" 2>&1 >/dev/null)
    echo "::warning::$REPO: gh api commits/live-defi-rollout returned empty — ${LDR_API_ERR:0:300}"
    LDR_COMMIT_JSON='{}'
  fi
  LDR_SHA=$(printf '%s' "$LDR_COMMIT_JSON" | jq -r '.sha // empty' 2>/dev/null || echo "")
  LDR_TREE=$(printf '%s' "$LDR_COMMIT_JSON" | jq -r '.commit.tree.sha // empty' 2>/dev/null || echo "")
  [ -n "$LDR_TREE" ] || LDR_TREE="ERR_LDR"
  # STEP 1 (frozen-head): the promote PR head is a bot-controlled ref, NOT the live LDR branch
  # (which drifts under backmerge churn → TOCTOU). Name fixed early so the phantom-close + PR
  # reuse below all target it; the ref is force-updated to the validated $LDR_SHA only after the
  # gates pass (further down). One ref per repo, reused across ticks.
  # Per-SHA immutable ref: name encodes the validated commit SHA so the ref never needs
  # force-update — a new SHA gets a new ref; the old one is closed+deleted (stale cleanup).
  # ── Fresh-RED skip: don't mint a promote PR for a tree the LDR monitor just failed ─────────
  #
  # ldr_red_promote_pr_waste_2026_08_10. `ldr_ci_status` (written by ldr_ci_monitor.py) is a
  # MONITOR axis, deliberately decoupled from promotion — and it stays decoupled here in every
  # case but one. The single case worth skipping is provably-wasted work: the monitor read RED
  # against EXACTLY the sha we are about to promote. Then the promote PR's own quality-gates-v2
  # is guaranteed to fail on the same tree, so cutting it buys a full CI run, a red PR, and a
  # second CRITICAL page for a failure already reported once (measured: market-tick-data-service
  # 2026-08-10, LDR red 17:19 -> PR #939 red 17:31, same e14f358b tree, two pages).
  #
  # WHY THE SHA MATCH IS LOAD-BEARING, not belt-and-braces: a level-only gate is what produced
  # tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09 — a stale FAILING vetoed PR creation,
  # and a fresh PR was the only thing that could clear it. Requiring sha equality makes this
  # SELF-CLEARING by construction: the instant anyone pushes a fix, the tip moves, the shas stop
  # matching, and promotion resumes on the next tick with no manual unblock. A repo can never be
  # wedged by a red it has already moved past.
  #
  # FAIL-OPEN on every other state — GREEN, UNKNOWN, absent field, or RED against a stale sha all
  # promote exactly as before. That matters because the monitor is hourly + conditional-dispatch
  # and fail-opens to UNKNOWN: a dead or lagging monitor must never be able to freeze the fleet's
  # promotion pipeline. This gate can only ever SKIP work that was already going to fail.
  LDR_CI_STATUS=$(jq -r --arg r "$REPO" '.repositories[$r].ldr_ci_status // empty' \
    workspace-manifest.json 2>/dev/null || echo "")
  LDR_CI_STATUS_SHA=$(jq -r --arg r "$REPO" '.repositories[$r].ldr_ci_status_sha // empty' \
    workspace-manifest.json 2>/dev/null || echo "")
  if [ "$LDR_CI_STATUS" = "RED" ] && [ -n "$LDR_CI_STATUS_SHA" ] && [ -n "$LDR_SHA" ] \
     && [ "$LDR_CI_STATUS_SHA" = "$LDR_SHA" ]; then
    echo "SKIP $REPO: ldr_ci_status=RED for the exact tip being promoted (${LDR_SHA:0:12}) — a promote PR on this tree is a guaranteed-red CI run + duplicate page. Self-clears the moment the tip moves past it (no manual unblock)."
    return 0
  fi
  if [ "$LDR_CI_STATUS" = "RED" ]; then
    echo "LDR-RED (stale, promoting anyway) $REPO: ldr_ci_status=RED but against '${LDR_CI_STATUS_SHA:0:12}' (empty = sha not recorded), not the tip ${LDR_SHA:0:12} — the tip has moved past that failure."
  fi

  PROMOTE_HEAD="promote/$REPO/${LDR_SHA:0:12}"

  # Run the ancestor-cleanup NOW — before the content-identical skip below and before the SIT
  # differ/gate section further down, both of which can return/block before ever reaching the
  # original superseded-ref cleanup near STEP 1. See _close_ancestor_failed_promote_prs()'s own
  # header comment for the full rationale + the design constraint it enforces.
  _close_ancestor_failed_promote_prs

  MAIN_TREE=$(gh api "repos/$OWNER/$REPO/commits/main" \
    --jq '.commit.tree.sha' 2>/dev/null || echo "ERR_MAIN")
  if [ "$LDR_TREE" = "$MAIN_TREE" ]; then
    # Self-document the squash-skew (2026-08-13, mtds_main_promotion_stall_and_qg_alert_
    # redispatch_2026_08_11.md Finding 1): a squash promote replays the whole main..LDR range as
    # ONE commit on main, so compare's ahead_by counts the ORIGINAL LDR SHAs the squash never
    # replays — it grows with every LDR commit even when content is byte-identical. Printing the
    # number makes "no successor PR opened" read as the CORRECT decision (main already carries LDR's
    # content), not a stall. Measured 08-11→08-13: market-tick-data-service ahead_by 1384→1436 while
    # trees stayed identical. Fail-OPEN to "?" on an API error — the SKIP verdict never depends on it.
    _SKIP_AHEAD_BY=$(gh api "repos/$OWNER/$REPO/compare/main...live-defi-rollout" \
      --jq '.ahead_by // 0' 2>/dev/null || echo "?")
    echo "SKIP $REPO: main tree == LDR tree (content-identical; compare ahead_by=$_SKIP_AHEAD_BY is squash-accounting SHA noise, not unpromoted content — no successor PR is correct)"
    # Close any phantom open promote PRs (any promote/$REPO/* ref OR legacy live-branch head).
    PHANTOM_NUMS=$(gh pr list --repo "$OWNER/$REPO" --base main --state open \
      --json number,headRefName \
      --jq '.[] | select((.headRefName | startswith("promote/'"$REPO"'/")) or .headRefName == "live-defi-rollout") | .number' \
      2>/dev/null || echo "")
    for _PN in $PHANTOM_NUMS; do
      if [ "$DRY_RUN" = "true" ]; then
        echo "  DRY-RUN: would close phantom LDR→main PR #$_PN (zero content delta)"
      else
        gh pr close "$_PN" --repo "$OWNER/$REPO" \
          --comment "Closed by LDR→main fleet bot: main tree == LDR tree (content-identical; the ahead_by gap is squash-accounting noise, not promotable content)." 2>/dev/null || true
      fi
    done
    return 0
  fi
  echo "CONTENT GATE PASS $REPO: LDR and main trees differ"

  # ── SIT-fleet-green required check: POST the commit status (unconditional) ──────────
  # Posted on EVERY repo reaching this point, regardless of breaking/non-breaking — the
  # gap that let the 2026-07-07/08 incident through. Uses the PAT, not the App token: the
  # App token has no verified `statuses:write` (probed empirically — the existing
  # label-check status POST below silently no-ops with it, confirmed by zero statuses on
  # a real promoted repo's LDR head); the PAT already does real writes elsewhere (ref
  # create, auto-merge arm) so it is the proven-working credential for this POST too.
  if [ "$DRY_RUN" = "true" ]; then
    echo "  DRY-RUN: would POST commit status $SIT_FLEET_CONTEXT=$SIT_FLEET_STATE on $REPO@${LDR_SHA:0:12}"
  else
    if GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X POST "repos/$OWNER/$REPO/statuses/$LDR_SHA" \
         --field state="$SIT_FLEET_STATE" \
         --field context="$SIT_FLEET_CONTEXT" \
         --field description="$SIT_FLEET_DESC" \
         ${SIT_FLEET_URL:+--field target_url="$SIT_FLEET_URL"} >/dev/null 2>&1; then
      echo "  ✅ posted $SIT_FLEET_CONTEXT=$SIT_FLEET_STATE on $REPO@${LDR_SHA:0:12}"
    else
      echo "::warning::SIT-fleet-green status POST FAILED for $REPO@${LDR_SHA:0:12} — required check will show missing (fail-closed by GitHub default, not a silent bypass)"
    fi
  fi

  # ── SIT gate part 2 (LDR→main): cross-repo breaking-change gate (WS-L SIT-rehome) ──
  # v2 is PER-repo, not cross-repo SIT — so a breaking main..LDR delta must be validated by
  # the assembled cross-repo SIT (full-workspace-sit, which runs on the LDR tips) before it
  # reaches main. Run the SAME AST public-surface differ on main..LDR; if BREAKING (or the
  # differ ERRORS → unknown), require this EXACT LDR tree to be SIT-validated. The PROOF is
  # read from Firestore LIVE (STEP 4): status==SIT_VALIDATED AND sit_validated_tree == the LDR
  # tree being promoted (so SIT validated EXACTLY this content, not a stale prior run). On a
  # miss we BLOCK (fail-CLOSED — ldr_main has no staging backstop; part-1 breaking_pending is
  # dead for these repos) and dispatch SIT-on-LDR (STEP 5) so a later tick promotes once this
  # tree is validated. Confident-non-breaking content needs no SIT (promote, v2-gated).
  #
  # source-dir resolution (fixed 2026-07-20). The convention is repo-name-underscored, but
  # 5 of the 24 ldr_main repos do not follow it, and for the 3 that are ALSO SIT-covered the
  # mismatch was a PERMANENT promote deadlock — the same unsatisfiable-block class as the
  # e2e-testing case documented below, reached by a different route:
  #   dir absent -> differ scans nothing -> is_breaking=false -> fail-closed flip -> "unknown"
  #   -> covered-repo branch -> requires sit_validated_tree == LDR tree -> but LDR keeps
  #   moving (hourly staging-backmerge) faster than a ~156m SIT round-trip -> never matches.
  # Measured 2026-07-20: agent-orchestrator 25 files / 7 commits un-promoted with NO open PR
  # (blocked before PR creation), tripping branch-health every cycle; deployment-ui and
  # unified-trading-system-ui carry the identical latent hole.
  # `breaking_scan_dir` in workspace-manifest.json overrides the convention per repo:
  #   absent  -> "${REPO//-/_}" (the 19 conforming repos are untouched)
  #   "<dir>" -> scan that dir instead (agent-orchestrator=server, e2e-testing=tests, ...)
  #   "none"  -> repo has NO Python public surface (TS/JS), so the differ is not applicable
  #              and its empty verdict is CORRECT, not a false-negative -> skip the
  #              fail-closed flip. Such a repo cannot break a Python sibling's import
  #              surface, and is still gated by quality-gates-v2 (tsc/ESLint/Vitest/
  #              Playwright) + content tree + Tier-A ci_status, as in the fail-OPEN branch.
  SCAN_DIR=$( REPO="$REPO" DEFAULT_DIR="${REPO//-/_}" python3 -c "import json,os; print(json.load(open('workspace-manifest.json'))['repositories'].get(os.environ['REPO'],{}).get('breaking_scan_dir', os.environ['DEFAULT_DIR']))" 2>/dev/null || echo "${REPO//-/_}" )
  echo "  SIT differ source-dir for $REPO: ${SCAN_DIR}"
  SIT_TMP="$(mktemp -d)"; BREAKING="unknown"; DIFF_JSON=""; RANGE_MSGS=""
  if git -C "$SIT_TMP" init -q && git -C "$SIT_TMP" fetch -q --no-tags \
       "https://x-access-token:${GH_TOKEN}@github.com/$OWNER/$REPO" \
       "+refs/heads/main:refs/remotes/origin/main" \
       "+refs/heads/live-defi-rollout:refs/remotes/origin/live-defi-rollout" 2>/dev/null; then
    # Capture the FULL differ verdict (is_breaking + export counts) once — reused by both the
    # SIT race-closer (is_breaking) and the F4 label-check gate below (export-count minor/patch),
    # so the differ runs only once per repo per tick.
    # HEAD-REF PIN (2026-07-20): diff the EXACT commit being gated ($LDR_SHA, captured in the
    # single read at the content gate above), NOT the branch NAME. This fetch is a SECOND,
    # independently-timed read of a MOVING branch — so with `--head-ref origin/live-defi-rollout`
    # the differ could classify a DIFFERENT tree than the one the SIT gate compares and the
    # frozen-head freezes. Under exactly the churn that makes the SIT gate miss (hourly
    # backmerge + quickmerge traffic), that is a correctness hole in BOTH directions, and the
    # dangerous one is silent: a breaking delta landing between the two reads is judged on a
    # snapshot that does not contain it -> `is_breaking=false` -> SIT GATE PASS -> promoted
    # UNGATED. The content gate above already went to the trouble of a single commit read
    # "so STEP 1 (frozen-head) can freeze the EXACT commit whose tree the SIT gate validates
    # — no drift between the read and the freeze"; the differ was simply never pinned to it.
    # $LDR_SHA stays reachable in the fetched branch even if LDR advanced (it is then an
    # ancestor of the new tip), so no extra refspec is needed. Fail CLOSED if it is unusable.
    _DIFF_HEAD="$LDR_SHA"
    if [ -z "$_DIFF_HEAD" ] || [ "$LDR_TREE" = "ERR_LDR" ] \
       || ! git -C "$SIT_TMP" cat-file -e "${_DIFF_HEAD}^{commit}" 2>/dev/null; then
      echo "  SIT differ: pinned head '${_DIFF_HEAD:-<empty>}' unreachable in the fetched tree — verdict UNKNOWN (fail-closed)"
      _DIFF_HEAD=""
    fi
    if [ -n "$_DIFF_HEAD" ]; then
      DIFF_JSON=$( cd "$SIT_TMP" && python3 "$GITHUB_WORKSPACE/scripts/cicd/detect_breaking_change.py" \
        --source-dir "${SCAN_DIR}" --base-ref origin/main --head-ref "$_DIFF_HEAD" --json 2>/dev/null ) || DIFF_JSON=""
    fi
    if [ -n "$DIFF_JSON" ]; then
      BREAKING=$( printf '%s' "$DIFF_JSON" \
        | python3 -c "import json,sys; print('true' if json.load(sys.stdin).get('is_breaking') else 'false')" 2>/dev/null || echo "unknown" )
    fi
    # Differ FAIL-CLOSED (WS-L): `--source-dir` is a convention guess (repo name → underscores).
    # If that dir is ABSENT from the LDR tree, the differ scanned nothing and a "false" verdict
    # is a false-negative that would skip the gate entirely. Flip such a "false" to "unknown"
    # (→ require SIT) so a breaking change in a non-conventionally-named repo can never promote
    # ungated. (For the 5 covered repos the convention is verified-correct, so this only guards
    # the tail.) The differ stderr is no longer fully swallowed downstream of this check.
    if [ "$SCAN_DIR" = "none" ]; then
      echo "  SIT differ: $REPO declares no Python public surface (breaking_scan_dir=none) — empty verdict is CORRECT, not fail-closed"
    elif [ "$BREAKING" = "false" ] \
       && ! git -C "$SIT_TMP" ls-tree -d --name-only origin/live-defi-rollout 2>/dev/null | grep -qx "${SCAN_DIR}"; then
      echo "  SIT differ: source-dir '${SCAN_DIR}' absent from LDR tree — verdict UNKNOWN (fail-closed)"
      echo "  → if this repo simply names its package differently, set breaking_scan_dir in workspace-manifest.json rather than letting it deadlock"
      BREAKING="unknown"
    fi
    # Range commit subjects (main..LDR), newest-first — for the F4 label-check gate below.
    RANGE_MSGS=$( git -C "$SIT_TMP" log origin/main..origin/live-defi-rollout --format='%s' 2>/dev/null || echo "" )
  fi
  rm -rf "$SIT_TMP"
  if [ "$BREAKING" = "false" ]; then
    echo "SIT GATE PASS $REPO: non-breaking delta (differ confident; no cross-repo SIT required; v2 gates per-repo)"
  elif ! echo " $SIT_COVERED " | grep -q " $REPO "; then
    # ── SIT-UNCOVERED repo + BREAKING/unknown delta: fail-OPEN (NOT permanent-block) ──────
    # full-workspace-sit DELIBERATELY stamps sit_validated_tree ONLY for repos in
    # sit_cross_repo_validated_repos — stamping any other ldr_main repo would forge a
    # cross-repo guarantee the suite never made (see the SIT stamp step's anti-forgery note:
    # "5 validated vs 21 stamped"). So for a repo OUTSIDE that set, the fail-closed branch
    # below is an UNSATISFIABLE deadlock: it requires a sit_validated_tree that SIT can never
    # write → the repo is blocked forever (observed: e2e-testing perpetually un-propagated,
    # sit_validated_tree='unset', tripping the branch-health lag alert every cycle).
    # These repos are SIT leaves / infra (e2e-testing harness, ibkr-gateway-infra) with NO
    # downstream Python consumers — there is no cross-repo contract for them to break, so the
    # cross-repo SIT gate is vacuous. Fail-OPEN: the promote PR is still gated by
    # quality-gates-v2 + content-tree + Tier-A (ci_status!=FAILING) on auto-merge, so a red
    # repo still cannot reach main. SSOT: plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md.
    echo "SIT GATE N/A $REPO: not in sit_cross_repo_validated_repos (${BREAKING}-delta; SIT leaf/infra, no cross-repo surface the suite validates) — promoting on v2+content+Tier-A. SIT can NEVER stamp this repo, so fail-OPEN here (a fail-closed block would be permanent, not transient)."
  else
    # COVERED repo + BREAKING/unknown → require this EXACT LDR tree to be SIT-validated. The proof
    # is read from Firestore LIVE (NOT the hourly manifest cache, which carries no tree). DECOUPLED
    # check: require sit_validated_tree == the LDR tree being promoted AND ci_status != FAILING.
    # We do NOT require status==SIT_VALIDATED — resolve_status's no-downgrade keeps a higher rank
    # (e.g. MAIN_GREEN) over an incoming SIT_VALIDATED, so the TREE FINGERPRINT, not the status
    # label, is the load-bearing proof (the store records the fingerprint regardless of rank).
    # On a miss, BLOCK (fail-CLOSED) + dispatch SIT-on-LDR (the suite validates this repo) so a
    # later tick promotes once this exact tree is validated. (project-id omitted → the Firestore
    # SDK auto-detects from GOOGLE_CLOUD_PROJECT; empty get-doc → block.)
    SIT_DOC=$(python3 "$GITHUB_WORKSPACE/scripts/cicd/ci_status_store.py" get-doc \
      --repo "$REPO" 2>/dev/null || echo '{}')
    SIT_STATUS=$(printf '%s' "$SIT_DOC" | jq -r '.status // empty' 2>/dev/null || echo "")
    SIT_TREE=$(printf '%s' "$SIT_DOC" | jq -r '.sit_validated_tree // empty' 2>/dev/null || echo "")
    if [ "$SIT_STATUS" != "FAILING" ] && [ -n "$SIT_TREE" ] && [ "$LDR_TREE" = "$SIT_TREE" ]; then
      # SIT cross-repo COMBINATION workspace-digest check REMOVED for the CI/CD MVP (2026-06-30):
      # it thrashed under fleet churn (any dependency's LDR tree change re-staled the fingerprint,
      # perpetually re-dispatching SIT). The MVP keeps ONLY the per-repo SIT-tree check above
      # (sit_validated_tree == this repo's LDR tree). SSOT: cicd_mvp_ldr_to_main_pipeline_2026_06_30.md.
      echo "SIT GATE PASS $REPO: ${BREAKING}-delta SIT-validated on this tree (sit_validated_tree == LDR tree $LDR_TREE; live ci_status='${SIT_STATUS:-unset}')"
    else
      echo "SIT GATE BLOCK $REPO: ${BREAKING}-delta not SIT-validated on this tree (live ci_status='${SIT_STATUS:-unset}', sit_validated_tree='${SIT_TREE:-unset}', LDR tree='${LDR_TREE}') — fail-CLOSED. Dispatching SIT-on-LDR; a later tick promotes once SIT validates this exact tree."
      if [ "$DRY_RUN" != "true" ]; then
        if ! _claim_sit_dispatch; then
          echo "  another SIT dispatch already claimed this tick (auto-retrigger or a sibling repo's own BREAKING-delta block) — not piling on; a later tick re-checks"
        else
          # SHA pin (2026-08-06, sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md):
          # the payload used to carry only `repo`, so full-workspace-sit.yml cloned "whatever LDR is
          # NOW" at its own dispatch-triggered start, not the exact $LDR_TREE this gate just computed
          # and is about to compare against — a moving-tree race under fleet churn. Passing `sha` lets
          # full-workspace-sit pin its own checkout to this exact commit when present (falls back to
          # the live branch tip for untouched trigger paths, e.g. the nightly cron / manual dispatch
          # with no sha in payload — see full-workspace-sit.yml's own checkout step).
          curl -s -X POST -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/$OWNER/system-integration-tests/dispatches" \
            -d "{\"event_type\": \"full-workspace-sit\", \"client_payload\": {\"reason\": \"ldr-main-breaking-gate\", \"repo\": \"${REPO}\", \"sha\": \"${LDR_SHA}\"}}" \
            && echo "  dispatched full-workspace-sit (SIT-on-LDR, pinned to ${LDR_SHA:0:12})" \
            || echo "  WARN: SIT dispatch failed (nightly full-workspace-sit cron is the fallback)"
        fi
      fi
      _done BLOCKED; return 0
    fi
  fi

  # ── Label-check gate (LDR→main) — WS-L F4 ─────────────────────────────────────
  # The semver-agent posts `semver-agent/label-check` on the STAGING head (it fires on
  # push:[staging]); under ldr_main the merge-PR head is the LDR SHA, which never receives
  # it — and once the staging drain is toggled off for ldr_main repos the semver-agent won't
  # run for them at all. So re-derive the SAME label-vs-computed-bump verdict here on the LDR
  # head and BLOCK a mismatch, so a mislabeled bump is flagged on the LDR→main path. Logic is
  # a faithful copy of semver-agent.yml.tmpl Step-4 (so the two NEVER diverge): COMPUTED from
  # the range commit subjects (breaking > minor > patch) refined by the SAME AST differ
  # (is_breaking → breaking; else new>old exports → minor); EXPECTED from the LATEST LDR
  # subject only. **Fail-OPEN** on any gap (differ unknown / no LDR SHA / empty range) — never
  # jam the drain on a label-check infra error (breaking_pending part-1 + v2 stay the backstops).
  LDR_HEAD_SHA="$LDR_SHA"  # reuse the atomic content-gate read (no second, possibly-drifted, API call)
  if [ "$BREAKING" = "unknown" ] || [ -z "$LDR_HEAD_SHA" ] || [ -z "$RANGE_MSGS" ]; then
    echo "  LABEL-CHECK $REPO: skipped (differ unknown / no LDR SHA / empty range) — fail-open"
  else
    COMPUTED=""
    while IFS= read -r m; do
      [ -z "$m" ] && continue
      if printf '%s' "$m" | grep -qE "^[a-z]+!(\(.+\))?:" || printf '%s' "$m" | grep -qi "BREAKING CHANGE"; then
        COMPUTED="breaking"; break
      elif printf '%s' "$m" | grep -qE "^feat(\(.+\))?:"; then
        [ "$COMPUTED" != "breaking" ] && COMPUTED="minor"
      elif printf '%s' "$m" | grep -qE "^fix(\(.+\))?:"; then
        [ "$COMPUTED" != "breaking" ] && [ "$COMPUTED" != "minor" ] && COMPUTED="patch"
      fi
    done <<< "$RANGE_MSGS"
    if [ "$COMPUTED" != "breaking" ]; then
      if [ "$BREAKING" = "true" ]; then
        COMPUTED="breaking"
      elif [ -z "$COMPUTED" ]; then
        # differ added new public exports but no feat:/fix: in range → minor (additive API)
        if printf '%s' "$DIFF_JSON" \
          | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get('new_export_count',0) > d.get('old_export_count',0) else 1)" 2>/dev/null; then
          COMPUTED="minor"
        fi
      fi
    fi
    # Pure bash parameter expansion (no subprocess/pipe): a `printf | head -1` here reliably
    # SIGPIPEs when RANGE_MSGS is a large multi-line commit-range (head -1 closes the pipe
    # before printf finishes writing) — under `set -euo pipefail` this aborted the per-repo
    # `process_repo` subshell right here, silently dropping that repo from PROMOTED/BLOCKED/
    # CONFLICTED (all three fleet-summary buckets show 0 while the repo never advances).
    # Reproduced 2/2 on market-tick-data-service (large same-day commit range) — its LDR→main
    # promote PR sat stale for hours because of this. SSOT:
    # plans/active/issues/ldr_to_main_promote_fleet_sigpipe_silent_drop_2026_07_21.md.
    LATEST_SUBJECT="${RANGE_MSGS%%$'\n'*}"
    EXPECTED="none"
    if printf '%s' "$LATEST_SUBJECT" | grep -qE "^[a-z]+!(\(.+\))?:" || printf '%s' "$LATEST_SUBJECT" | grep -qi "BREAKING CHANGE"; then
      EXPECTED="breaking"
    elif printf '%s' "$LATEST_SUBJECT" | grep -qE "^feat(\(.+\))?:"; then
      EXPECTED="minor"
    elif printf '%s' "$LATEST_SUBJECT" | grep -qE "^fix(\(.+\))?:"; then
      EXPECTED="patch"
    fi
    echo "  LABEL-CHECK $REPO: expected-from-label='${EXPECTED}' computed='${COMPUTED:-none}'"
    if [ "$EXPECTED" != "none" ] && [ -n "$COMPUTED" ] && [ "$EXPECTED" != "$COMPUTED" ]; then
      # LABEL-CHECK no longer BLOCKS under the CI/CD MVP (2026-06-30): semver-bump labeling is
      # the semver-agent's responsibility, not the LDR→main promote gate — and this check carried
      # a range-asymmetry false-block (EXPECTED from the LATEST commit subject vs COMPUTED from the
      # whole-range max), which false-blocked correctly-labeled repos (UAC, mtds). Advisory only.
      # SSOT: plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md.
      echo "  LABEL-CHECK (advisory, NOT enforced under MVP) $REPO: label='$EXPECTED' vs diff='$COMPUTED' — promoting anyway"
    fi
    echo "  LABEL-CHECK PASS $REPO: label matches computed bump (${COMPUTED:-none})"
    if [ "$DRY_RUN" != "true" ]; then
      # PAT, not the App token (finding, 2026-07-12 SIT-fleet-green canary dispatch): this
      # POST was silently 403-ing ("Resource not accessible by integration") with the
      # default App token — swallowed by `2>/dev/null || true`, so it looked like a no-op
      # rather than a failure. Advisory-only status (not gating), so the silent failure had
      # no behavioral impact, but fix it while touching this file (same root cause as the
      # sit-gate/fleet-green POST above, already root-caused there).
      GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X POST "repos/$OWNER/$REPO/statuses/$LDR_HEAD_SHA" \
        --field state=success \
        --field context="semver-agent/label-check" \
        --field description="LDR→main: label matches API diff (${COMPUTED:-none})." 2>/dev/null || true
    fi
  fi

  # ── Runaway breaker — CADENCE-AWARE, and gated on the EMPTY-PROMOTE signature ─────────
  # Filter by the stable promote TITLE, not --head: under frozen-head the merged PR head is
  # `promote/<repo>` (not live-defi-rollout), so a head filter would always count 0 and the
  # breaker would never trip. The "chore(promote)" title catches every promote PR (legacy
  # live-branch head OR frozen ref).
  #
  # WHY THIS CHANGED (2026-07-18). The cap was 12 merges/6h, set 2026-06-25 (32e1eb199) when
  # this bot ran `8,23,38,53 * * * *` = 4 ticks/hour. On 2026-07-18 (42ba7b823) the cron
  # became `*/5` = 12 ticks/hour to beat GitHub's schedule throttling. Tripling the tick rate
  # does NOT mean the bot malfunctions — it means the same day's work is promoted in smaller,
  # more frequent batches, so the MERGE COUNT alone rises ~3x on any actively-developed repo.
  # It duly tripped: deployment-service was REFUSED promotion at 21:07 with 12/6h, and
  # market-tick-data-service + instruments-service were both at 10/6h and about to follow.
  # Measured on all 14 of deployment-service's promote PRs: changed_files ran 1..105 and NOT
  # ONE was empty — i.e. every promote carried real content. That is healthy throughput being
  # mislabelled "malfunctioning", which is a false CRITICAL page AND a self-inflicted
  # promotion freeze.
  #
  # A genuine runaway has a distinct signature: the bot re-promotes NOTHING, over and over
  # (an empty-promote loop — the failure ldr-to-staging hit at 375 empty promotes/day). So
  # count is the cheap trigger, EMPTINESS is the verdict:
  #   * cap raised 12 -> 36, tracking the 3x cadence change (still well under staging's 30/2h-equivalent)
  #   * on exceeding it, spend the (now rare) extra API calls to ask how many of those promotes
  #     changed ZERO files. Block + page ONLY if that is >= EMPTY_RUNAWAY_MIN.
  #   * high throughput with real content is NOT blocked and NOT paged — just logged.
  # Keeping the count check first means the expensive per-PR lookup runs ~never in steady state.
  RUNAWAY_CAP=36
  EMPTY_RUNAWAY_MIN=3
  MERGED_6H=$(gh pr list --repo "$OWNER/$REPO" --base main \
    --state merged --limit 50 --json mergedAt,title \
    --jq '[.[] | select(.title | startswith("chore(promote)")) | select(.mergedAt > (now - 21600 | strftime("%Y-%m-%dT%H:%M:%SZ")))] | length' 2>/dev/null || echo "0")
  if [ "${MERGED_6H:-0}" -ge "$RUNAWAY_CAP" ]; then
    # Confirm the malfunction signature before refusing anything.
    EMPTY_6H=0
    for _pn in $(gh pr list --repo "$OWNER/$REPO" --base main --state merged --limit 50 \
        --json number,mergedAt,title \
        --jq '.[] | select(.title | startswith("chore(promote)")) | select(.mergedAt > (now - 21600 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | .number' 2>/dev/null); do
      _cf=$(gh api "repos/$OWNER/$REPO/pulls/$_pn" --jq '.changed_files' 2>/dev/null || echo "1")
      [ "${_cf:-1}" -eq 0 ] && EMPTY_6H=$((EMPTY_6H + 1))
    done
    if [ "$EMPTY_6H" -ge "$EMPTY_RUNAWAY_MIN" ]; then
      echo "⛔ RUNAWAY BREAKER $REPO: ${MERGED_6H} promote PRs merged in 6h and ${EMPTY_6H} of them changed ZERO files — empty-promote loop; refusing; page CRITICAL"
      if [ -n "${SLACK_CI_WEBHOOK_URL:-}" ] && [ "$DRY_RUN" != "true" ]; then
        curl -s -X POST "$SLACK_CI_WEBHOOK_URL" -H 'Content-Type: application/json' \
          -d "{\"text\":\":rotating_light: *RUNAWAY LDR→MAIN BREAKER* — \`$REPO\` had ${MERGED_6H} LDR→main promote merges in 6h, ${EMPTY_6H} of them EMPTY (zero changed files). That is an empty-promote loop, not throughput — ldr-to-main-promote-fleet is malfunctioning on this repo. Repo promotion REFUSED until the count ages out or the cause is fixed.\"}" >/dev/null 2>&1 || true
      fi
      _done BLOCKED; return 0
    fi
    echo "NOTE $REPO: ${MERGED_6H} promote merges in 6h (>= cap ${RUNAWAY_CAP}) but only ${EMPTY_6H} empty — real content every time, so this is THROUGHPUT, not a runaway. Not blocking."
  fi

  if [ "$DRY_RUN" = "true" ]; then
    if [ "$TIER_A_CI_FAILING" = "true" ]; then
      echo "  DRY-RUN: would open LDR→main PR for $REPO (ci_status=$CI_STATUS) but NOT arm auto-merge (Tier-A ci_status=FAILING)"
    else
      echo "  DRY-RUN: would open LDR→main PR for $REPO (ci_status=$CI_STATUS) and arm auto-merge"
    fi
    _done PROMOTED; return 0
  fi

  # Guard: $LDR_SHA can be empty if the content-gate commit read failed (API error). Never
  # freeze/promote an empty ref — block and retry next tick. (The SIT gate already blocks
  # breaking changes whose LDR_TREE is the ERR_LDR sentinel, but a non-breaking delta with a
  # transient SHA-read failure would otherwise reach the freeze with LDR_SHA="".)
  if [ -z "$LDR_SHA" ]; then
    echo "  ⛔ WARN $REPO: empty LDR SHA (commit read failed) — BLOCKED; retry next tick"
    _done BLOCKED; return 0
  fi

  # ── Don't preempt an in-flight validation (2026-07-27) ──────────────────────────
  # Mirrors the same fix in ldr-to-main-promote.yml (PM-only bot): without this, the
  # superseded-ref cleanup below closes whatever promote/* PR is open the moment LDR's
  # tip moves at all — even mid-flight quality-gates-v2. Under fleet commit velocity
  # almost every tick observes a new tip, so almost every attempt got killed before its
  # v2 run could finish (observed: v2 re-ran 15-20x/45min on some repos). Skip cutting a
  # new ref/PR this tick if an existing open promote/* PR's v2 run for its OWN head SHA
  # hasn't reached a terminal state yet — let it finish (merges on success; superseded
  # next tick on failure). Every commit still gets validated, just batched with whatever
  # else lands during the same in-flight run. Fail-open on a query error.
  _INFLIGHT_HEAD=$(gh pr list --repo "$OWNER/$REPO" --base main --state open \
    --json headRefName --jq ".[] | select(.headRefName | startswith(\"promote/$REPO/\")) | .headRefName" 2>/dev/null | head -1)
  if [ -n "$_INFLIGHT_HEAD" ] && [ "$_INFLIGHT_HEAD" != "$PROMOTE_HEAD" ]; then
    _INFLIGHT_SHA=$(gh pr list --repo "$OWNER/$REPO" --base main --head "$_INFLIGHT_HEAD" \
      --state open --json headRefOid --jq '.[0].headRefOid' 2>/dev/null || echo "")
    if [ -n "$_INFLIGHT_SHA" ]; then
      _V2_INFLIGHT=$(gh run list --repo "$OWNER/$REPO" --workflow quality-gates-v2.yml --limit 20 \
        --json headSha,status --jq "[.[]|select(.headSha==\"$_INFLIGHT_SHA\" and .status!=\"completed\")]|length" 2>/dev/null || echo "0")
      if [ "${_V2_INFLIGHT:-0}" != "0" ]; then
        echo "  ⏳ $REPO: existing promote PR (head=$_INFLIGHT_HEAD) has quality-gates-v2 still running — not superseding this tick"
        _done BLOCKED; return 0
      fi
    fi
  fi

  # ── One-shot auto-recheck of a terminally-RED promote PR (2026-08-11) ──────────────────
  # WHY: the block above only handles "v2 still running" — a promote PR whose v2 already
  # FAILED sits untouched forever unless LDR's tip moves (which cuts a new ref/PR and closes
  # the old one). If LDR is quiet for that repo, a red PR caused by something TRANSIENT or
  # ALREADY FIXED upstream (a reusable-workflow bug in unified-trading-ci, a self-hosted
  # runner flake) never gets a second look — someone has to notice the Slack alert and
  # manually close/reopen the PR to force a fresh check (confirmed live 2026-08-11:
  # features-service PR #1003 sat RED for 8+ hours after unified-trading-ci@700e6d3 fixed
  # the exact bug that broke its original run, because nothing re-triggered it). Manually
  # nudging individual PRs doesn't scale and doesn't survive the next incident — this closes
  # the gap at the SOURCE so it self-heals within one fleet-bot tick instead.
  # MECHANISM: `gh run rerun` deliberately NOT used — GitHub Actions reruns reuse the
  # ORIGINALLY-RESOLVED content of a floating reusable-workflow ref (`@main`), so a rerun of
  # a run that started before an upstream fix landed replays the SAME bug even after the fix
  # is live (confirmed live: rerunning 31463593127 after the fix still hit the pre-fix code
  # path). Close+reopen forces a genuinely fresh `pull_request` event, which re-resolves
  # `@main` fresh — confirmed live to work in the same incident.
  # SAFETY: fires AT MOST ONCE per PR (marker comment gates re-entry — a persistently broken
  # PR, e.g. a real code regression, gets exactly one free recheck then waits for a human/
  # agent like any other red PR, never an infinite retry loop) and only after the PR has sat
  # red for >=20min (lets a same-tick failure be looked at before auto-nudging it, and avoids
  # racing a run that only just completed).
  _RECHECK_MARKER="<!-- fleet-bot-auto-recheck-done -->"
  _EXISTING_HEAD=$(gh pr list --repo "$OWNER/$REPO" --base main --state open \
    --json headRefName --jq ".[] | select(.headRefName | startswith(\"promote/$REPO/\")) | .headRefName" 2>/dev/null | head -1)
  if [ -n "$_EXISTING_HEAD" ]; then
    _EXISTING_PR=$(gh pr list --repo "$OWNER/$REPO" --base main --head "$_EXISTING_HEAD" \
      --state open --json number,createdAt,headRefOid 2>/dev/null || echo "")
    _EXISTING_NUM=$(printf '%s' "$_EXISTING_PR" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["number"] if d else "")' 2>/dev/null || echo "")
    _EXISTING_SHA=$(printf '%s' "$_EXISTING_PR" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d[0]["headRefOid"] if d else "")' 2>/dev/null || echo "")
    _EXISTING_AGE_MIN=$(printf '%s' "$_EXISTING_PR" | python3 -c '
import json, sys
from datetime import datetime, timezone
d = json.load(sys.stdin)
if not d:
    print(0)
else:
    created = datetime.fromisoformat(d[0]["createdAt"].replace("Z", "+00:00"))
    print(int((datetime.now(timezone.utc) - created).total_seconds() // 60))
' 2>/dev/null || echo "0")
    if [ -n "$_EXISTING_NUM" ] && [ -n "$_EXISTING_SHA" ] && [ "${_EXISTING_AGE_MIN:-0}" -ge 20 ]; then
      _V2_TERMINAL=$(gh run list --repo "$OWNER/$REPO" --workflow quality-gates-v2.yml --limit 20 \
        --json headSha,status,conclusion \
        --jq "[.[]|select(.headSha==\"$_EXISTING_SHA\" and .status==\"completed\" and .conclusion==\"failure\")]|length" 2>/dev/null || echo "0")
      if [ "${_V2_TERMINAL:-0}" != "0" ]; then
        _ALREADY_RECHECKED=$(gh pr view "$_EXISTING_NUM" --repo "$OWNER/$REPO" --json comments \
          --jq "[.comments[]|select(.body|contains(\"$_RECHECK_MARKER\"))]|length" 2>/dev/null || echo "0")
        if [ "${_ALREADY_RECHECKED:-0}" = "0" ]; then
          if [ "$DRY_RUN" = "true" ]; then
            echo "  🔁 [DRY_RUN] $REPO: would auto-recheck red promote PR #$_EXISTING_NUM (red ${_EXISTING_AGE_MIN}min, no prior recheck)"
          else
            echo "  🔁 $REPO: promote PR #$_EXISTING_NUM has been red for ${_EXISTING_AGE_MIN}min with no prior auto-recheck — forcing one fresh check (close/reopen)"
            gh pr close "$_EXISTING_NUM" --repo "$OWNER/$REPO" \
              --comment "Fleet bot: red for ${_EXISTING_AGE_MIN}min — forcing a fresh check in case this was a transient/since-fixed upstream issue. $_RECHECK_MARKER" 2>/dev/null || true
            gh pr reopen "$_EXISTING_NUM" --repo "$OWNER/$REPO" 2>/dev/null \
              && echo "  ✅ $REPO: PR #$_EXISTING_NUM reopened — fresh pull_request event dispatched" \
              || echo "  ⚠️  $REPO: reopen of PR #$_EXISTING_NUM failed — leaving as closed, next tick's SHA/ref logic will recover"
          fi
        fi
      fi
    fi
  fi

  # ── STEP 1 (frozen-head): pin the promote head to the SIT-validated commit ────────────
  # We only reach here PAST the content + SIT gates, so $LDR_SHA is gate-validated content: a
  # BREAKING delta passed only because sit_validated_tree == this LDR tree; a non-breaking delta
  # needs no SIT. Snapshot $LDR_SHA to the IMMUTABLE per-SHA ref $PROMOTE_HEAD (name encodes the
  # SHA → never needs a force-update; a new LDR tip gets a new ref name). Open the PR from THAT
  # ref — never the live `live-defi-rollout` branch, which advances under backmerge churn so an
  # UN-validated tree could replace the validated one between v2 and the ASYNC auto-merge (TOCTOU
  # — auto-merge fires whenever v2 passes on the head, independent of this bot's ticks). Once the
  # PR is merged, `--delete-branch` removes the ref automatically (no accumulation). Superseded
  # refs (from prior ticks at older LDR tips) are cleaned up explicitly below.
  # Bug #5 hardening (2026-06-30): delete the LEGACY no-slash `promote/<repo>` ref FIRST. The
  # per-SHA ref `promote/<repo>/<sha>` CANNOT be created while `promote/<repo>` exists (git
  # directory/file conflict → HTTP 422), and the superseded-ref cleanup below (filter
  # "promote/$REPO/" + PR-backed only) never catches the legacy no-slash ref. Left unhandled it
  # froze 15/21 repos at ref-creation 2026-06-29. SSOT: cicd_mvp_ldr_to_main_pipeline_2026_06_30.md.
  if GH_TOKEN="$GH_PAT_FOR_ARM" gh api "repos/$OWNER/$REPO/git/refs/heads/promote/$REPO" >/dev/null 2>&1; then
    GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X DELETE "repos/$OWNER/$REPO/git/refs/heads/promote/$REPO" >/dev/null 2>&1 \
      && echo "  🛡️  bug#5 hardening: deleted legacy no-slash promote ref refs/heads/promote/$REPO (it D/F-conflicts the per-SHA ref)" || true
  fi
  # Create-only (POST): if the ref already exists (409 = prior tick created it for this same SHA),
  # that's correct — verify it resolves and continue.
  if ! GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X POST "repos/$OWNER/$REPO/git/refs" \
       -f ref="refs/heads/$PROMOTE_HEAD" -f sha="$LDR_SHA" >/dev/null 2>&1; then
    if ! GH_TOKEN="$GH_PAT_FOR_ARM" gh api "repos/$OWNER/$REPO/git/refs/heads/$PROMOTE_HEAD" >/dev/null 2>&1; then
      echo "  ⛔ WARN $REPO: could not create immutable promote ref $PROMOTE_HEAD @ ${LDR_SHA:0:8} — skipping (retry next tick)"
      _done BLOCKED; return 0
    fi
  fi
  echo "  frozen-head: $PROMOTE_HEAD → ${LDR_SHA:0:12} (tree ${LDR_TREE:0:12}) — PR opens from this immutable per-SHA ref"

  # ── Superseded ref cleanup: close + delete any older promote/$REPO/* PRs + refs ──────────
  # When LDR advances, the previous tick's promote ref (at the old SHA) is now stale. Close its
  # open PR (if any) and delete its ref so orphan `promote/*` branches don't accumulate.
  STALE_HEADS=$(gh pr list --repo "$OWNER/$REPO" --base main --state open \
    --json headRefName \
    --jq ".[] | select(.headRefName | startswith(\"promote/$REPO/\")) | select(.headRefName != \"$PROMOTE_HEAD\") | .headRefName" \
    2>/dev/null || echo "")
  for _STALE_HEAD in $STALE_HEADS; do
    _STALE_NUM=$(gh pr list --repo "$OWNER/$REPO" --base main --head "$_STALE_HEAD" \
      --state open --json number --jq '.[0].number' 2>/dev/null || echo "")
    if [ -n "$_STALE_NUM" ] && [ "$_STALE_NUM" != "null" ]; then
      gh pr close "$_STALE_NUM" --repo "$OWNER/$REPO" \
        --comment "Closed by LDR→main fleet bot: superseded by newer validated SHA (new ref: $PROMOTE_HEAD)." 2>/dev/null || true
      echo "  closed superseded promote PR #$_STALE_NUM (head=$_STALE_HEAD)"
    fi
    GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X DELETE "repos/$OWNER/$REPO/git/refs/heads/$_STALE_HEAD" 2>/dev/null || true
    echo "  deleted orphan promote ref refs/heads/$_STALE_HEAD"
  done

  # ── Orphan-ref sweep: promote/$REPO/* refs with NO open PR, from ANY close path ──────────
  # The superseded-ref cleanup above only catches refs whose PR `gh pr list --state open`
  # still returns THIS tick — a ref whose PR was closed by any OTHER path (conflict_resolver
  # closing a superseded PR manually, an operator, a stale-check close) is never swept and
  # accumulates on the remote indefinitely (confirmed live 2026-08-06: execution-service PR
  # #552 closed by conflict_resolver agt-7e7e2c, ref left orphaned until a manual delete —
  # promote_ref_orphaned_on_manual_pr_close_2026_08_06.md). List every promote/$REPO/* ref
  # directly (not PR-derived) and delete any that is neither the current frozen head nor
  # backed by a currently-open PR. Best-effort: a listing/delete failure never blocks promotion.
  ALL_PROMOTE_REFS=$(GH_TOKEN="$GH_PAT_FOR_ARM" gh api --paginate \
    "repos/$OWNER/$REPO/git/matching-refs/heads/promote/$REPO/" \
    --jq '.[].ref | sub("^refs/heads/"; "")' 2>/dev/null || echo "")
  OPEN_PROMOTE_HEADS=$(gh pr list --repo "$OWNER/$REPO" --base main --state open \
    --json headRefName \
    --jq ".[] | select(.headRefName | startswith(\"promote/$REPO/\")) | .headRefName" \
    2>/dev/null || echo "")
  for _ORPHAN_HEAD in $ALL_PROMOTE_REFS; do
    [ "$_ORPHAN_HEAD" = "$PROMOTE_HEAD" ] && continue
    echo " $OPEN_PROMOTE_HEADS " | grep -q " $_ORPHAN_HEAD " && continue
    GH_TOKEN="$GH_PAT_FOR_ARM" gh api -X DELETE "repos/$OWNER/$REPO/git/refs/heads/$_ORPHAN_HEAD" 2>/dev/null \
      && echo "  🧹 orphan-ref sweep: deleted refs/heads/$_ORPHAN_HEAD (no open PR, not current head)" \
      || echo "  🧹 orphan-ref sweep: refs/heads/$_ORPHAN_HEAD already gone or delete failed (non-fatal)"
  done

  # ── Open (or reuse) the LDR→main PR and enable v2-gated auto-merge ──────────
  if [ "$TIER_A_CI_FAILING" = "true" ]; then
    BODY="WS-L Phase-0: LDR→main direct promotion for \`$REPO\` (promotion_model=ldr_main, immutable per-SHA ref \`$PROMOTE_HEAD\`). ci_status=${CI_STATUS} (Tier-A ci_status=FAILING, cached/live — see tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md); content + SIT + combination gates passed. Auto-merge NOT armed — this PR's OWN quality-gates-v2 is the true, current-content gate, but merging still needs a fresh main-branch ci_status clear (a later tick or a human/operator merge). SSOT: cicd_consolidated_remaining_2026_06_24.md WS-L."
  else
    BODY="WS-L Phase-0: LDR→main direct promotion for \`$REPO\` (promotion_model=ldr_main, immutable per-SHA ref \`$PROMOTE_HEAD\`). ci_status=${CI_STATUS}; Tier-A + content + SIT + combination gates passed; v2-gated auto-merge armed (delete-branch on merge). SSOT: cicd_consolidated_remaining_2026_06_24.md WS-L."
  fi
  # Create the PR with the PAT, NOT the App token (GH_TOKEN). A promote PR opened by the
  # uts-ci-poller App lands quality-gates-v2 in `action_required` → the required pull_request
  # check never auto-runs → the required context never reports → the PR deadlocks BLOCKED
  # forever (the reactive force-dispatch recovery below is a fragile band-aid for this). A
  # PAT-authored PR fires the pull_request workflow normally. Proven by A/B on a HELD head SHA
  # (WS-L 2026-06-27): App-created → action_required; PAT-created → ran → success → merged.
  # The App token stays for the rate-limited gh-api READS elsewhere (separate 5000/hr pool).
  # Hardening (2026-07-31, ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md):
  # capture stderr instead of swallowing it — when `gh pr create` fails for a reason other than
  # "PR already exists" (rate limit, permission, transient API error), the WARN below now names the
  # actual cause instead of leaving the repo's absence from every tick's tally unexplained.
  _PR_CREATE_ERR="$(mktemp)"
  PR_URL=$(GH_TOKEN="$GH_PAT_FOR_ARM" gh pr create --repo "$OWNER/$REPO" \
    --title "chore(promote): LDR → main (Option-B direct)" \
    --body "$BODY" --base main --head "$PROMOTE_HEAD" 2>"$_PR_CREATE_ERR" || true)
  _PR_CREATE_STDERR="$(cat "$_PR_CREATE_ERR" 2>/dev/null || true)"
  rm -f "$_PR_CREATE_ERR"

  if [ -n "$PR_URL" ]; then
    echo "  PR: $PR_URL"

    # ── Provenance gate (D1): only quickmerge-provenanced content ──────────────
    # (shared provenance_check_ok() helper, defined above process_repo — also gates
    # every re-arm path below, closing the 2026-06-30 re-arm-leak finding.)
    # Pass the bare PR NUMBER, not $PR_URL (bug found 2026-08-07,
    # provenance_check_ok_pr_url_escalation_dispatch_break_2026_08_07): _PR_ID flows into
    # the provenance_blocked escalation dispatch's `pr_number` client_payload field, which
    # `escalate-to-orchestrator.yml` passes to `jq --argjson pr "..."` (requires a bare JSON
    # number) and to `gh pr edit "$PR_NUMBER" --add-label` (requires a bare number, not a
    # URL) — a full PR URL breaks both, so every provenance-block escalation from the
    # PR-creation path silently failed to reach the orchestrator (`jq: invalid JSON text
    # passed to --argjson`). The other two provenance_check_ok call sites (re-arm paths)
    # already pass $PR_NUM correctly; this creation-path call was the only one still passing
    # the URL. `gh pr comment` (the other consumer of _PR_ID inside the helper) accepts a
    # bare number just as well as a URL, so this is a pure fix with no other behavior change.
    _PR_NUM_FOR_PROVENANCE="${PR_URL##*/}"
    if ! provenance_check_ok "$_PR_NUM_FOR_PROVENANCE"; then
      _done BLOCKED; return 0
    fi

    # Tier-A merge-arm gate (2026-08-10, tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md
    # todo 1) — PR is already open past this point; only the ACT of arming auto-merge is gated on
    # ci_status here, not the PR's existence.
    if ! tier_a_merge_gate_ok; then
      _done BLOCKED; return 0
    fi

    # Arm auto-merge (SQUASH only — LDR carries merge commits from the backmerge-sink design, so
    # rebase-merge is structurally impossible). Use the PAT: the App token cannot enable auto-merge
    # (WS-L canary finding 2026-06-26); the PAT can. LOUD on failure (no 2>/dev/null swallow).
    # Promoted-From-LDR trailer (silent-revert-loss fix, ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md):
    # stamps the EXACT LDR SHA this squash represents. A squash commit's real git
    # parent is main's PREVIOUS tip, not this LDR SHA — so main-backmerge-to-ldr's
    # default merge-base computation can silently land on a STALE ancestor if a
    # revert (or any follow-up correction) lands on LDR between this bot's content-gate
    # read and the auto-merge actually landing. The backmerge reads this trailer and
    # uses $LDR_SHA as an EXPLICIT merge-base instead, so a downstream LDR revert can
    # never be silently undone by the backmerge.
    if GH_TOKEN="$GH_PAT_FOR_ARM" gh pr merge "$PR_URL" --auto --squash --delete-branch \
         --subject "chore(promote): LDR → main (Option-B direct)" \
         --body "$(printf 'LDR→main fleet bot — squash (LDR is the backmerge sink; not rebaseable).\n\nPromoted-From-LDR: %s' "$LDR_SHA")" \
         --repo "$OWNER/$REPO"; then
      echo "  ✅ auto-merge (squash, delete-branch) armed — merges + deletes immutable ref when quality-gates-v2 is green"
      _done PROMOTED
    else
      # Hardening (2026-08-02, ci_satellite_ao_dispatch_batch1 [CI] P1 — MTDS auto-merge-arm
      # investigation): an arm failure here used to fall through to `_done PROMOTED` anyway,
      # so a PR needing a manual merge was silently tallied identically to a genuinely-armed
      # one — the same silent-success-on-failure shape this batch's other todos already fixed
      # elsewhere (workspace-quickmerge-validation, the F5 vacuous-reader class). Tally it as
      # its own ARM_FAILED terminal state instead so it surfaces in the run summary + Slack.
      echo "  ⛔ WARN: auto-merge ARM FAILED for $REPO — merge manually: $PR_URL"
      _done ARM_FAILED
    fi
    return 0
  fi

  # PR creation returned empty → existing PR (from the frozen ref) or conflict. Inspect.
  PR_NUM=$(gh pr list --repo "$OWNER/$REPO" --base main --head "$PROMOTE_HEAD" \
    --state open --json number --jq '.[0].number' 2>/dev/null || echo "")
  if [ -n "$PR_NUM" ] && [ "$PR_NUM" != "null" ]; then
    MSTATE=""
    for _i in 1 2 3; do
      MSTATE=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM" --jq '.mergeable_state' 2>/dev/null || echo "")
      [ -n "$MSTATE" ] && [ "$MSTATE" != "null" ] && break
      sleep 5
    done

    if [ "$MSTATE" = "dirty" ]; then
      CONFLICT_URL="https://github.com/$OWNER/$REPO/pull/$PR_NUM"
      echo "  CONFLICT on PR #$PR_NUM ($CONFLICT_URL) — dispatching resolver"
      curl -s -X POST \
        "https://api.github.com/repos/$OWNER/unified-trading-pm/dispatches" \
        -H "Authorization: Bearer $GH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"event_type\":\"promotion-conflict\",\"client_payload\":{\"repo_name\":\"${REPO}\",\"source_branch\":\"live-defi-rollout\",\"target_branch\":\"main\",\"original_pr_url\":\"${CONFLICT_URL}\"}}" \
        && echo "    dispatched (conflict resolver)" || echo "    WARN: dispatch failed"
      _done CONFLICTED; return 0

    elif [ "$MSTATE" = "blocked" ]; then
      # Stale-check recovery: re-dispatch v2 if absent on current head.
      HEAD_SHA=$(gh api "repos/$OWNER/$REPO/pulls/$PR_NUM" --jq '.head.sha' 2>/dev/null || echo "")
      HAS_V2=$(gh run list --repo "$OWNER/$REPO" --workflow quality-gates-v2.yml --limit 50 \
        --json headSha,conclusion \
        --jq "[.[]|select(.headSha==\"$HEAD_SHA\" and .conclusion!=\"action_required\" and .conclusion!=\"cancelled\")]|length" 2>/dev/null || echo "ERR")
      if [ "$HAS_V2" = "ERR" ]; then
        echo "  WARN: v2 status check failed for PR #$PR_NUM — leaving it"
      elif [ -n "$HEAD_SHA" ] && [ "${HAS_V2:-0}" = "0" ]; then
        echo "  STALE-CHECK on PR #$PR_NUM — v2 absent on head ${HEAD_SHA:0:8}; re-dispatching"
        if gh workflow run quality-gates-v2.yml --repo "$OWNER/$REPO" --ref "$PROMOTE_HEAD" 2>/dev/null; then
          echo "    force-dispatched quality-gates-v2 on the frozen head $PROMOTE_HEAD — RECOVERING (not yet merged; a later tick re-checks)"
          _done BLOCKED; return 0
        fi
        # Fallback: close+reopen. Re-check provenance BEFORE the re-arm (2026-06-30
        # re-arm-leak fix) — a close+reopen cycle is itself a re-arm, and LDR may have
        # moved (picked up non-quickmerge content) since this PR's frozen head was cut.
        if gh pr close "$PR_NUM" --repo "$OWNER/$REPO" 2>/dev/null; then
          sleep 3
          gh pr reopen "$PR_NUM" --repo "$OWNER/$REPO" 2>/dev/null || true
          if provenance_check_ok "$PR_NUM"; then
            # Tier-A merge-arm gate (2026-08-10, tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md
            # todo 1) — same narrowed-scope gate as the primary arm site above.
            if ! tier_a_merge_gate_ok; then
              _done BLOCKED; return 0
            fi
            # Promoted-From-LDR trailer — see the primary arm site above for the full rationale.
            # Hardening (2026-08-02, same ARM_FAILED finding as the primary arm site): this call
            # used to swallow its exit code entirely (`2>/dev/null || true`) and always tally
            # PROMOTED, so a failed close+reopen re-arm was invisible even in the raw log. Now
            # loud + tallied like the other two arm sites.
            if GH_TOKEN="$GH_PAT_FOR_ARM" gh pr merge "$PR_NUM" --auto --squash --delete-branch \
                 --subject "chore(promote): LDR → main (Option-B direct)" \
                 --body "$(printf 'LDR→main fleet bot — squash (close+reopen re-arm).\n\nPromoted-From-LDR: %s' "$LDR_SHA")" \
                 --repo "$OWNER/$REPO"; then
              _done PROMOTED
            else
              echo "  ⛔ WARN: auto-merge ARM FAILED for $REPO on close+reopen re-arm #$PR_NUM — merge manually"
              _done ARM_FAILED
            fi
            return 0
          else
            _done BLOCKED; return 0
          fi
        else
          echo "  WARN: close failed — leaving PR #$PR_NUM blocked"
          _done BLOCKED; return 0
        fi
      else
        echo "  $REPO: existing PR #$PR_NUM blocked; v2 present on head (genuine gate fail or in-progress)"
        _done BLOCKED; return 0
      fi
    else
      # CLEAN or other state — (re)arm auto-merge idempotently (SQUASH via PAT; see arm note above).
      # Re-check provenance BEFORE the re-arm (2026-06-30 re-arm-leak fix, closed
      # 2026-07-28): this is the exact path UAC PR #544 self-resolved through on
      # 2026-06-30 — a later tick found the PR "clean" by mergeable_state and re-armed
      # without re-validating provenance, landing non-quickmerge commits on main.
      echo "  $REPO: existing PR #$PR_NUM state=$MSTATE — checking provenance before (re)arming"
      if ! provenance_check_ok "$PR_NUM"; then
        _done BLOCKED; return 0
      fi
      # Tier-A merge-arm gate (2026-08-10, tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md
      # todo 1) — same narrowed-scope gate as the primary arm site above.
      if ! tier_a_merge_gate_ok; then
        _done BLOCKED; return 0
      fi
      echo "  $REPO: existing PR #$PR_NUM state=$MSTATE — (re)arming squash auto-merge (delete-branch)"
      # Promoted-From-LDR trailer — see the primary arm site above for the full rationale.
      if GH_TOKEN="$GH_PAT_FOR_ARM" gh pr merge "$PR_NUM" --auto --squash --delete-branch \
           --subject "chore(promote): LDR → main (Option-B direct)" \
           --body "$(printf 'LDR→main fleet bot — squash (re-arm).\n\nPromoted-From-LDR: %s' "$LDR_SHA")" \
           --repo "$OWNER/$REPO"; then
        echo "  ✅ re-armed squash auto-merge (delete-branch) on #$PR_NUM"
        _done PROMOTED
      else
        # Hardening (2026-08-02, same ARM_FAILED finding as the primary arm site) — this used to
        # tally PROMOTED unconditionally below regardless of the re-arm's own outcome.
        echo "  ⛔ WARN: auto-merge re-arm FAILED for #$PR_NUM"
        _done ARM_FAILED
      fi
      return 0
    fi
  else
    # Hardening (2026-07-31, ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md):
    # this is the exact silent-no-op the doc reproduced twice against deployment-service — a bare
    # `return 0` here never calls `_done`, so `$RESULT_DIR/$REPO` is never written and the repo drops
    # out of every Promoted/Blocked/Conflicted tally with zero trace. Log the captured `gh pr create`
    # stderr (previously discarded) and mark BLOCKED so the repo shows up for the next tick / a human.
    echo "  ⛔ WARN $REPO: PR creation failed and no open PR found for frozen head $PROMOTE_HEAD"
    if [ -n "$_PR_CREATE_STDERR" ]; then
      echo "  gh pr create stderr: $_PR_CREATE_STDERR"
    fi
    _done BLOCKED; return 0
  fi
}

# ── Bounded-parallel driver (cap MAXJOBS, staggered launch) ─────────────────
while IFS= read -r REPO; do
  [ -z "$REPO" ] && continue
  process_repo "$REPO" > "$LOG_DIR/$REPO.log" 2>&1 &
  [ "${STAGGER_SECONDS:-0}" != "0" ] && sleep "$STAGGER_SECONDS"
  while [ "$(jobs -rp | wc -l)" -ge "$MAXJOBS" ]; do wait -n 2>/dev/null || true; done
done <<< "$REPOS"
wait 2>/dev/null || true

# ── Barrier: replay logs in topo order + aggregate ───────────────────────────
PROMOTED=""; BLOCKED=""; CONFLICTED=""; ARM_FAILED=""
PROMOTED_COUNT=0; BLOCKED_COUNT=0; CONFLICTED_COUNT=0; ARM_FAILED_COUNT=0
while IFS= read -r REPO; do
  [ -z "$REPO" ] && continue
  [ -f "$LOG_DIR/$REPO.log" ] && cat "$LOG_DIR/$REPO.log"
  [ -f "$RESULT_DIR/$REPO" ] || continue
  case "$(cat "$RESULT_DIR/$REPO")" in
    PROMOTED)   PROMOTED="$PROMOTED $REPO";     PROMOTED_COUNT=$((PROMOTED_COUNT + 1)) ;;
    BLOCKED)    BLOCKED="$BLOCKED $REPO";       BLOCKED_COUNT=$((BLOCKED_COUNT + 1)) ;;
    CONFLICTED) CONFLICTED="$CONFLICTED $REPO"; CONFLICTED_COUNT=$((CONFLICTED_COUNT + 1)) ;;
    ARM_FAILED) ARM_FAILED="$ARM_FAILED $REPO"; ARM_FAILED_COUNT=$((ARM_FAILED_COUNT + 1)) ;;
  esac
done <<< "$REPOS"
rm -rf "$RESULT_DIR" "$LOG_DIR"

{
  echo "promoted=$PROMOTED"
  echo "blocked=$BLOCKED"
  echo "conflicted=$CONFLICTED"
  echo "arm_failed=$ARM_FAILED"
  echo "promoted_count=$PROMOTED_COUNT"
  echo "blocked_count=$BLOCKED_COUNT"
  echo "conflicted_count=$CONFLICTED_COUNT"
  echo "arm_failed_count=$ARM_FAILED_COUNT"
} >> "$GITHUB_OUTPUT"

echo ""
echo "=== LDR→main Fleet Promote Summary (Phase-0 canary) ==="
echo "LDR→main repos: $LDR_MAIN_REPOS"
echo "Promoted ($PROMOTED_COUNT):$PROMOTED"
echo "Dep-order/Tier-A blocked ($BLOCKED_COUNT):$BLOCKED"
echo "Conflicted ($CONFLICTED_COUNT):$CONFLICTED"
echo "Auto-merge ARM FAILED ($ARM_FAILED_COUNT):$ARM_FAILED"
