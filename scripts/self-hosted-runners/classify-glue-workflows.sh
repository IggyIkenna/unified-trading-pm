#!/usr/bin/env bash
# Epic: deployment_and_user_management_master (CI/CD cost reduction — B1)
# Lifecycle: permanent
# Delete-when: glue host retired (B2/B3)
#
# classify-glue-workflows.sh — for every unified-trading-pm workflow, print whether it should MOVE to
# the self-hosted `glue` runners or STAY on GitHub-hosted, from its TRIGGERS.
#
# Rule: KEEP on hosted if it is a real test gate (quality-gates*) OR is pull_request-triggered
# (CPU-heavy / dev-facing). MOVE if it is IO-bound automation glue (repository_dispatch / schedule /
# push / workflow_dispatch only). Advisory — eyeball the output before flipping any runs-on.
#
# STATE column (added 2026-07-28, self_hosted_runner_pm_core_workflows_2026_07_28.md): the MOVE/MOVE-C
# verdict is PURELY trigger-derived and NEVER re-checks a file's CURRENT `runs-on:` value — so a workflow
# already migrated to `[self-hosted, glue]` keeps printing MOVE forever, on every future rerun, identically
# to one still on `ubuntu-latest`. Found the hard way: the 2026-07-28 Wave-2 audit read this script's raw
# "39 MOVE" count as "39 files still needing migration" without checking each file's actual current
# `runs-on:` line — a real, separate re-verification found 38 of those 39 were ALREADY fully self-hosted
# (only `cloud-build-router.yml`'s `record-cloud-build-result` job remained `ubuntu-latest`). The STATE
# column below closes that gap so a future rerun distinguishes "pending" (still needs the flip) from
# "done" (already migrated, MOVE is now a no-op verdict) without a manual per-file re-grep.
set -euo pipefail

WF_DIR="${WF_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.github/workflows" && pwd)}"
[ -d "${WF_DIR}" ] || { echo "no workflows dir at ${WF_DIR}" >&2; exit 1; }
# fleet workflow-templates dir (rolled out to every repo); may be absent
TMPL_DIR="$(cd "${WF_DIR}/../../scripts/workflow-templates" 2>/dev/null && pwd || true)"

# CROSS-REPO REUSABLES (KEEP-R): workflows called by OTHER repos via
#   `uses: <owner>/unified-trading-pm/.github/workflows/<name>@<ref>`.
# A reusable's jobs run on the CALLER's runners. Our `glue` runners are repo-scoped to PM (personal
# accounts can't register org runners), so they are invisible to the calling repo — flipping runs-on
# here would hang the job in EVERY calling repo (same failure mode as KEEP-T). Regenerate the list:
#   rg -o "uses:.*unified-trading-pm/\.github/workflows/[a-z0-9-]+\.yml" */.github/workflows/ \
#     | sed -E 's#.*/##; s/@.*//' | sort -u
# (python-quality-gates-v2 is already KEEP via the quality-gates match; image-build-validate is the
#  other cross-repo reusable — called by 24 repos' image-build-gate.yml to gate staging→main promote.)
REUSABLE_CROSSREPO="image-build-validate.yml"

# FAILURE-INDEPENDENCE MONITORS (KEEP-M): a dead-man-switch / watcher whose whole value is detecting
# that OUR infra (incl. this very VM) is broken MUST run on infra independent of what it watches. If it
# ran on the glue pool, a VM outage would silently take out BOTH the detection AND the alert (the
# alerter is on the down box). These are light (a few $/mo total) and GitHub-hosted is the right home —
# KEPT HOSTED by operator decision 2026-07-16:
#   - overnight-dead-man-switch:   detects the overnight orchestrator (which runs on this VM) failing.
#   - ci-health:                   fleet-wide workflow-failure detector + stuck-PR auto-recovery.
#   - cloud-build-failure-watcher: the ONLY detector for out-of-band Cloud Build failures.
#   - ldr-ci-monitor:              per-repo "is LDR green?" signal.
#   - branch-health:               promotion-lag / drift / AR-lag monitor.
#   - glue-pool-starvation-monitor: the dead-man-switch FOR the glue pool itself (own header:
#     "MUST run on a GitHub-hosted runner, never `glue` itself... a dead-man-switch that ran on
#     the pool it watches would go dark exactly when it is needed") — found missing from this
#     list 2026-07-28 despite its own docstring's identical, incident-backed reasoning to the
#     other five; the schedule/workflow_dispatch-only trigger shape made it fall through to a
#     bare MOVE verdict, contradicting the file's own header.
#   - stale-build-watcher: found live 2026-07-29 (new file, landed on the shared branch after the
#     original six were audited) — same failure-independence shape as cloud-build-failure-watcher:
#     it MEASURES whether a Cloud Build actually happened (via GCP/GH API calls) independent of the
#     build pipeline itself. If the glue pool it would otherwise run on is the thing that's down or
#     misbehaving, a self-hosted copy of this watcher goes dark at exactly the moment the "did the
#     build actually happen" check is needed most — the identical reasoning as the other seven.
KEEP_MONITORS="overnight-dead-man-switch.yml ci-health.yml cloud-build-failure-watcher.yml ldr-ci-monitor.yml branch-health.yml glue-pool-starvation-monitor.yml stale-build-watcher.yml"

# HOSTED DEPENDENCIES (KEEP-D): a shared reusable on a KEEP workflow's CRITICAL path. A reusable's runs-on is
# independent of its caller, so a self-hosted reusable would break its HOSTED caller during a VM outage even though the
# caller itself is hosted. notify-slack is the alert carrier for ALL the KEEP-M monitors (each `notify` job → it), so if
# it moved, a down-VM would let the monitors DETECT a failure but be unable to PAGE — defeating the reason they stay
# hosted. Alert-only frequency → cheap to keep hosted. Regenerate: for each KEEP workflow, list its `uses: ./…` reusables
# and keep any that are on an alert/independence-critical path.
KEEP_HOSTED_DEPS="notify-slack.yml"

# CONVERT TO COMPOSITE ACTION (MOVE-C): a high-frequency reusable that ALSO straddles (called by both KEEP and MOVE
# workflows) but, unlike notify-slack, fires on EVERY run → material $. Flipping its runs-on can't satisfy both sides
# (hosted callers would hang on a down VM). The fix (operator 2026-07-16, option C): rewrite it as a composite ACTION
# (`.github/actions/<name>/action.yml`) so it runs as STEPS inside each caller's own job → on the caller's runner
# (movers → VM/$0, KEEP callers → hosted, no hang), AND it stops being a separate 1-min-minimum billed job (the A3/A4
# win). "MOVE-C" = moves off hosted by CONVERSION, do NOT flip its runs-on; it leaves the workflow set once converted.
CONVERT_TO_ACTION="persist-cicd-event.yml"

printf '%-40s %-6s %-8s %s\n' "WORKFLOW" "VERDICT" "STATE" "TRIGGERS (on:)"
printf '%-40s %-6s %-8s %s\n' "--------" "------" "-----" "--------------"
move=0 keep=0 move_pending=0 move_done=0
for f in "${WF_DIR}"/*.yml; do
  base="$(basename "${f}")"
  # extract the `on:` block: from a line starting `on:` up to the next top-level key
  on_block="$(awk '/^on:/{grab=1} grab{print} /^[a-zA-Z]/ && !/^on:/ && grab>1{exit} grab{grab++}' "${f}")"
  has() { printf '%s' "${on_block}" | grep -qE "^[[:space:]]*$1\b"; }
  trig=""
  for t in pull_request repository_dispatch schedule push workflow_dispatch workflow_call; do
    has "${t}" && trig+="${t} "
  done
  [ -z "${trig}" ] && trig="(none/manual)"

  # HEAVY-compute detection: a job that BUILDS locally (docker image / wheel) is CPU/RAM-heavy and must NOT run on the
  # light glue VM — keep it hosted. NOTE: `gcloud builds triggers run` / `codebuild start-build` only DISPATCH to the
  # cloud (light on the runner), so they are NOT heavy.
  heavy=""
  grep -qiE 'docker build|docker buildx|buildx build|docker/build-push|(uv|poetry|python -m) build|twine upload|npm (run )?build|pytest' "${f}" && heavy="1"

  # TEMPLATED detection: this workflow is a fleet template (scripts/workflow-templates/) rolled out to EVERY repo.
  # Only PM has glue runners, so flipping the TEMPLATE runs-on to self-hosted would hang it in the other ~24 repos.
  # And hand-editing PM's per-repo copy is banned. So a templated glue workflow stays HOSTED (or needs a conditional).
  tmpl=""
  if [ -n "${TMPL_DIR}" ] && { [ -e "${TMPL_DIR}/${base}" ] || [ -e "${TMPL_DIR}/${base}.tmpl" ]; }; then
    tmpl="1"
  fi

  # NO-runs-on detection: a workflow whose jobs are ALL `uses:` (a pure reusable caller) has no
  # runner of its own — the REUSABLE's runs-on decides, and a caller cannot override it. There is
  # literally nothing to flip, so calling it MOVE is a lie that costs someone an afternoon.
  #
  # FOUND THE HARD WAY 2026-07-16: agent-audit.yml was picked as the D6 canary off a profile of LOC /
  # triggers / capabilities that never asked "does this have a runs-on?". It doesn't — its one job is
  # `uses: .../python-quality-gates-v2.yml@main`, i.e. it runs on whatever QG (a KEEP) specifies, and
  # is pinned at @main so an LDR flip is inert twice over. Verdict KEEP-U: it can only move if the
  # reusable it calls moves, which for quality-gates-v2 we have deliberately decided against.
  no_runs_on=""
  grep -qE '^[[:space:]]*runs-on:' "${f}" || no_runs_on="1"

  # The ${LIST} expansions in the elif chain below are UNQUOTED ON PURPOSE: word-splitting is what
  # turns each space-separated list into one candidate per line for `grep -qx`. Quoting them would
  # emit a single line and silently match nothing — the "fix" would be the bug. The directive sits
  # here because shellcheck only accepts one in front of a complete compound command (SC1123), not
  # on an individual elif branch.
  # shellcheck disable=SC2086
  if printf '%s' "${base}" | grep -qiE 'quality-gates' || has pull_request; then
    verdict="KEEP"; keep=$((keep+1))
  elif [ -n "${no_runs_on}" ]; then
    verdict="KEEP-U"; keep=$((keep+1)) # pure reusable CALLER — no runs-on of its own; the callee's runner wins
  elif [ -n "${heavy}" ]; then
    verdict="KEEP*"; keep=$((keep+1)) # kept because it builds locally (heavy compute)
  elif [ -n "${tmpl}" ]; then
    verdict="KEEP-T"; keep=$((keep+1)) # templated multi-repo — do NOT flip the template (only PM has runners)
  elif printf '%s\n' ${REUSABLE_CROSSREPO} | grep -qx "${base}"; then
    verdict="KEEP-R"; keep=$((keep+1)) # cross-repo reusable — flipping hangs the calling repos (only PM has glue runners)
  elif printf '%s\n' ${KEEP_MONITORS} | grep -qx "${base}"; then
    verdict="KEEP-M"; keep=$((keep+1)) # failure-independence monitor — must NOT run on the infra it watches
  elif printf '%s\n' ${KEEP_HOSTED_DEPS} | grep -qx "${base}"; then
    verdict="KEEP-D"; keep=$((keep+1)) # shared reusable on a KEEP workflow's critical path (alert carrier) — stay hosted
  elif printf '%s\n' ${CONVERT_TO_ACTION} | grep -qx "${base}"; then
    verdict="MOVE-C"; move=$((move+1)) # move off hosted by CONVERTING to a composite action (runs as a step) — do NOT flip runs-on
  else
    verdict="MOVE"; move=$((move+1))
  fi

  # STATE (MOVE/MOVE-C only): does this file actually still have a real (non-comment) `runs-on:
  # ubuntu-latest` line, or was it already flipped to self-hosted in a prior pass? A MOVE verdict
  # alone can't tell you which — see the header comment for why.
  state="-"
  if [ "${verdict}" = "MOVE" ] || [ "${verdict}" = "MOVE-C" ]; then
    if grep -qE '^[[:space:]]*runs-on:[[:space:]]*ubuntu-latest\b' "${f}"; then
      state="pending"; move_pending=$((move_pending+1))
    else
      state="done"; move_done=$((move_done+1))
    fi
  fi
  printf '%-40s %-6s %-8s %s\n' "${base}" "${verdict}" "${state}" "${trig}"
done
echo
printf 'MOVE (→ PM-local direct flip): %d [%d pending / %d already self-hosted]   KEEP (→ GitHub-hosted): %d\n' \
  "${move}" "${move_pending}" "${move_done}" "${keep}"
echo '  KEEP* = local build/heavy compute · KEEP-T = fleet template (multi-repo; only PM has runners → keep hosted)'
echo '  KEEP-R = cross-repo reusable (caller-runner-scoped; flip hangs callers) · KEEP-M = failure-independence monitor'
echo '  KEEP-U = pure reusable CALLER — no runs-on of its own, so there is nothing to flip (the callee picks the runner)'
echo '  KEEP-D = shared reusable on a KEEP workflow'"'"'s critical path (e.g. the notify-slack alert carrier) — stay hosted'
echo '  MOVE-C = moves off hosted by CONVERTING the reusable to a composite action (runs as a step on the caller) — do NOT flip runs-on'
echo '  STATE pending = still runs-on: ubuntu-latest, needs the flip · STATE done = already runs-on: [self-hosted, glue] (no action)'
echo 'Flip only MOVE workflows whose STATE is "pending": runs-on: ubuntu-latest → runs-on: [self-hosted, glue]. Migrate one first.'
