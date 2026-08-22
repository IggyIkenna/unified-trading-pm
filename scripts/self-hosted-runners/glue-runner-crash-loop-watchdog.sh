#!/usr/bin/env bash
# glue-runner-crash-loop-watchdog.sh
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
#
# Periodically checks every github-glue-runner* systemd unit on THIS host for a crash-loop
# (SubState=auto-restart with a high NRestarts) and pages #ci-failures via a repository_dispatch
# to unified-trading-pm's ci-health.yml `glue-runner-alert` job -- the one alert path that stays
# reachable even when every self-hosted runner on this box is itself dead, because that job runs
# on ubuntu-latest (GitHub-hosted), not here.
#
# WHY THIS EXISTS: found 2026-07-28 -- every glue-runner pool crash-looped for ~3.5h
# (GCP_PROJECT missing from runtime env files, see
# plans/active/issues/glue_runner_gcp_project_missing_fleet_outage_2026_07_28.md) before a
# routine fleet CI sweep caught it by accident. No alerting existed for "the runner PROCESS
# itself is dead" -- only for CI job outcomes, which obviously never fire if the runner never
# came up to run anything in the first place.
#
# WEDGED-RUNNER DETECTION (2026-08-05, added alongside crash-loop): found live
# (market-tick-data-service, i-042a6332509482556) a `glue-*` unit that was neither crashing NOR
# progressing -- a single hung job (a deadlocked pytest run) kept its Runner.Worker alive for
# 21+ hours, holding ~5.6GB RSS. `Restart=always` never fired (the process never EXITED, it just
# hung), so the crash-loop check above is structurally blind to this failure mode. Worse,
# GitHub's own side had already stopped tracking the run (zero registered runners, job stuck
# `queued`) -- there was no live channel left for GitHub's own job-level `timeout-minutes` to
# reach, so nothing was ever going to kill it. Every subsequent commit for that repo queued
# forever with zero chance of pickup, silently, until this was caught by a live manual
# investigation. `is_wedged()` below catches this class going forward: a `@glue-N` instance
# (JIT-ephemeral, one job per process by design -- see github-glue-runner@.service's own
# comment) that has been `active` continuously for longer than any legitimate single job could
# take. Deliberately excludes `@writer-N` instances (long-lived by design, e.g. ci-status-update
# -- a long ActiveEnterTimestamp there is normal, not a symptom).
#
# GITHUB-API BUSY CORROBORATION (2026-08-07): the local journal-based idle check below
# (`is_idle_listening`) was STILL insufficient -- found live, same host, this same session:
# `glue-runner-crash-loop-watchdog` paged CRITICAL "wedged" on 4 healthy runners across 4
# DIFFERENT repos' pools (e2e-testing, strategy-service, market-tick-data-service, ml-service),
# all on i-042a6332509482556. SSM-verified 3.3s total CPU across 3h+ of "active" runtime for all
# 4, and GitHub's own runner API confirmed `status:online, busy:false` for every one -- healthy
# idle runners during a fleet-wide low-throughput window, not hung processes. See
# plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md.
# `runner_busy_status()` below now asks GitHub directly (the same ground truth the live
# investigation used to disprove the page) BEFORE falling back to the journal heuristic --
# resolving OWNER/REPO from the unit's own `Description` property, which
# `setup-glue-runners.sh`'s `render_unit()` ALWAYS stamps as `(OWNER/REPO)` (a same-value no-op
# for PM's own base pool, a real value for any second POOL_TAG'd pool on this host), so this
# works for every pool on the box with no new file and no new permission -- `systemctl show
# -p Description` is exactly as world-readable as every other property this script already
# reads. The token is the SAME `GH_PAT` identity this script already resolves for PM's own
# alert dispatch: confirmed reused verbatim across pools (README.md's `POOL_TAG=ao
# ... GH_TOKEN_SECRET=GH_PAT` example), and a token that can WRITE (register) a runner on a repo
# can certainly READ (list) that repo's runners, so no new credential is needed either.
#
# State-transition dedup (not "page every tick while true"): tracks which units are CURRENTLY
# alerted in a local state file; only pages on a NEW crash-loop/wedge detection and on RECOVERY,
# matching the workspace's own standing-condition alerting convention. The two conditions share
# one state file with disjoint key prefixes (bare unit name = crash-loop, `wedged::`-prefixed =
# wedged) so either can independently alert/recover on the same unit without clobbering the
# other's tracking.
#
# Credential reuse: dispatches AS unified-trading-pm's own existing glue-runner identity
# (GH_TOKEN_SECRET from /etc/github-glue-runner.env, read via its own isolated CLOUDSDK_CONFIG)
# -- no new credential to provision or leak; same secret PM's own runner pool already uses.
set -euo pipefail

RESTART_THRESHOLD="${GLUE_WATCHDOG_RESTART_THRESHOLD:-5}"
# 180min: comfortably above quality-gates-v2's own job-level `timeout-minutes: 135` (the longest
# any legitimate qg-slices job should ever run) plus real margin for JIT-registration/queueing
# delay before a job starts. The market-tick-data-service zombie this was built for ran 21+
# hours -- anything past 135min is already firmly in "something is wrong" territory, 180min just
# keeps a comfortable buffer against false-positiving a genuinely-slow-but-healthy run.
WEDGED_THRESHOLD_SEC="${GLUE_WATCHDOG_WEDGED_THRESHOLD_SEC:-10800}"
# Resolved live, never hardcoded: the alert messages below used to hard-code
# i-0c9b283b31d6b5ca7 (the OLD shared VM, pre-runner-fleet-split) -- a stale reference that
# would point an operator at a now-decommissioned box after any future host migration too.
# IMDSv2 (this host's own instance-id) is always correct for wherever the script is actually
# running.
THIS_INSTANCE_ID="$(curl -sf -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null \
  | xargs -I{} curl -sf -H "X-aws-ec2-metadata-token: {}" \
    "http://169.254.169.254/latest/meta-data/instance-id" 2>/dev/null || echo "unknown-host")"
# /var/lib is root-owned; /opt/github-glue-runners itself is ALSO root:root (only specific
# pre-created subdirs like .gcloud are ubuntu-owned) -- verified live, not assumed, after the
# first attempt at each hit Permission denied. The unit runs User=ubuntu, so state has to live
# under ubuntu's own home instead.
STATE_DIR="${GLUE_WATCHDOG_STATE_DIR:-/home/ubuntu/.local/state/glue-runner-watchdog}"
STATE_FILE="${STATE_DIR}/alerted-units"
# Unconfirmed wedge candidates awaiting a second confirming tick -- see the NEW-wedges loop's
# 2026-08-16 comment below for why this exists. Deliberately a SEPARATE file from STATE_FILE:
# STATE_FILE's header comment documents it as shared between exactly two disjoint prefix
# classes (bare = crash-loop, `wedged::` = wedge) whose recovery loops each skip lines outside
# their own prefix -- a THIRD prefix here would fall through the crash-loop recovery loop's
# `case "$unit" in wedged::*) continue ;; esac` unmatched and be mis-treated as a bogus
# crash-loop unit name. A dedicated file avoids that collision entirely.
WEDGE_CANDIDATE_FILE="${STATE_DIR}/wedge-candidates"
GH_REPO="IggyIkenna/unified-trading-pm"
PM_ENV_FILE="/etc/github-glue-runner.env"

mkdir -p "$STATE_DIR"
touch "$STATE_FILE"
touch "$WEDGE_CANDIDATE_FILE"

log() { echo "[glue-runner-watchdog] $*"; }

# Resolve a GH token the same way glue-runner-run.sh does for this exact repo. GH_TOKEN_SECRET/
# GCP_PROJECT/GLUE_GCLOUD_CONFIG come from the environment, NOT a direct read of PM_ENV_FILE --
# that file is 0600 root:root (same as every per-repo one), unreadable by this unit's own
# User=ubuntu. The systemd unit's `EnvironmentFile=` directive is what actually reads it (at
# root, before the privilege drop) and injects these as env vars; a bare sed-parse here silently
# failed on every tick (2026-08-05 finding -- see the .service file's own comment). Falls back
# to parsing PM_ENV_FILE directly only for a manual/local run outside systemd, where no
# EnvironmentFile injection happens and the invoking user presumably already has read access.
resolve_gh_token() {
  local secret="${GH_TOKEN_SECRET:-}" project="${GCP_PROJECT:-}" gcloud_cfg="${GLUE_GCLOUD_CONFIG:-}"
  if [ -z "$secret" ] && [ -r "$PM_ENV_FILE" ]; then
    secret="$(sed -n 's/^GH_TOKEN_SECRET=//p' "$PM_ENV_FILE" | head -1)"
    project="${project:-$(sed -n 's/^GCP_PROJECT=//p' "$PM_ENV_FILE" | head -1)}"
    gcloud_cfg="${gcloud_cfg:-$(sed -n 's/^GLUE_GCLOUD_CONFIG=//p' "$PM_ENV_FILE" | head -1)}"
  fi
  gcloud_cfg="${gcloud_cfg:-/opt/github-glue-runners/.gcloud}"
  CLOUDSDK_CONFIG="$gcloud_cfg" gcloud secrets versions access latest \
    --secret="$secret" --project="$project"
}

# <unit-name> is crash-looping if systemd is actively retrying it past the threshold AND its most
# recent exit was NOT clean. FOUND LIVE 2026-08-06 (i-042a6332509482556, glue-2/glue-3/glue-5 all
# false-paged the same tick): SubState=auto-restart + high NRestarts alone is NOT sufficient for a
# `@glue-N` instance -- per github-glue-runner@.service's own comment ("glue-*: one job per
# process, restart to re-register"), Restart=always fires on EVERY exit, including a clean
# `Runner listener exit with 0 return code, stop the service, no retry needed` after a
# successfully completed job. NRestarts is a lifetime counter that NEVER resets, so a healthy
# glue-N unit crosses RESTART_THRESHOLD within its first few jobs and then sits >= threshold
# FOREVER -- any poll landing in the ~5s window between a clean exit and the next job's start
# (RestartSec=5) pages a false CRITICAL "runner process is DOWN" alert on a unit that is, and
# always was, healthy. `Result` (systemd's verdict on the LAST completed run: "success" for exit
# 0, "exit-code"/"signal"/etc. for an actual failure) is the one property that distinguishes "just
# finished a job cleanly, about to restart" from "genuinely failing to start/run" -- gating on
# Result != success closes the false-positive without weakening real detection: the original
# 2026-07-28 GCP_PROJECT-missing incident this watchdog was built for exited non-zero every time
# (Result=exit-code), so it still trips this check.
is_crash_looping() {
  local unit="$1" substate restarts result
  substate="$(systemctl show "$unit" -p SubState --value 2>/dev/null || echo "")"
  restarts="$(systemctl show "$unit" -p NRestarts --value 2>/dev/null || echo "0")"
  result="$(systemctl show "$unit" -p Result --value 2>/dev/null || echo "")"
  [ "$substate" = "auto-restart" ] && [ "${restarts:-0}" -ge "$RESTART_THRESHOLD" ] && [ "$result" != "success" ]
}

# Seconds since <unit-name>'s current invocation started. Empty/unparseable timestamp -> 0
# (never false-positives a wedge on a systemd read hiccup).
unit_active_seconds() {
  local unit="$1" ts epoch now
  ts="$(systemctl show "$unit" -p ActiveEnterTimestamp --value 2>/dev/null || echo "")"
  [ -z "$ts" ] && { echo 0; return; }
  epoch="$(date -d "$ts" +%s 2>/dev/null || echo 0)"
  [ "${epoch:-0}" -eq 0 ] && { echo 0; return; }
  now="$(date +%s)"
  echo $(( now - epoch ))
}

# True iff <unit-name>'s own runner log shows it genuinely idle right now -- the LAST line
# matching either marker is "Listening for Jobs" (not "Running job: ..."). Cheap, local,
# no GitHub API call needed: Runner.Listener logs exactly one of these two lines per state
# transition, so the most recent one is authoritative for current state.
#
# FALLBACK ONLY as of 2026-08-07 (see the top-of-file GITHUB-API BUSY CORROBORATION comment) --
# is_wedged() now only reaches this when runner_busy_status() itself was inconclusive (API
# unreachable / token unresolvable / Description unparseable).
#
# Empty/unreadable journal -> treat as IDLE (flipped 2026-08-07; was "NOT idle"). This direction
# is the one that actually matches how journal retention/eviction behaves here: a genuinely idle
# unit logs "Listening for Jobs" ONCE, at the start of its (possibly multi-hour) wait, then
# nothing else -- that line is the OLDEST thing in its journal and the first to age out under
# retention pressure. A genuinely wedged unit's "Running job: ..." line is logged LATER (after
# "Listening for Jobs", once a job actually lands) and has been surviving right up to the
# moment it hung, so it is the LAST thing to age out, not the first. An empty read is therefore
# far more consistent with "the one-time idle line finally rotated away" than with "the
# in-progress line rotated away" -- and empirically, the old "fail toward alerting" direction is
# exactly what produced today's false CRITICAL page on 4 healthy idle runners (busy:false
# confirmed independently via GitHub's own API for all 4). The residual risk of this flip is a
# slower-to-detect (not undetected) genuine wedge on the rare tick where BOTH the GitHub API
# above AND the local journal are simultaneously inconclusive -- the next 5-minute tick still
# catches it.
is_idle_listening() {
  local unit="$1" last_line
  last_line="$(journalctl -u "$unit" --no-pager -o cat 2>/dev/null \
    | grep -E 'Listening for Jobs|Running job:' | tail -1)"
  [ -z "$last_line" ] && return 0
  [[ "$last_line" == *"Listening for Jobs"* ]]
}

# Resolve OWNER/REPO for <unit-name> from its own `Description` systemd property -- see the
# top-of-file GITHUB-API BUSY CORROBORATION comment for why this is always populated and always
# world-readable. Echoes "" on anything unparseable so callers degrade to the journal fallback
# instead of constructing a bogus API URL.
unit_owner_repo() {
  local unit="$1" desc
  desc="$(systemctl show "$unit" -p Description --value 2>/dev/null || echo "")"
  if [[ "$desc" =~ \(([^/[:space:]()]+/[^/[:space:]()]+)\)[[:space:]]*$ ]]; then
    echo "${BASH_REMATCH[1]}"
  else
    echo ""
  fi
}

# Memoized wrapper around resolve_gh_token() (defined above, for PM's own alert-dispatch
# identity) -- the busy-check below reuses that SAME identity for every pool on this host (see
# top-of-file comment for why that is safe), and memoizing avoids a redundant Secret Manager
# round-trip per wedge candidate within one tick.
_glue_gh_token_cache=""
cached_gh_token() {
  if [ -z "${_glue_gh_token_cache}" ]; then
    _glue_gh_token_cache="$(resolve_gh_token 2>/dev/null || echo "")"
  fi
  printf '%s' "${_glue_gh_token_cache}"
}

# GitHub's own authoritative answer to "does this runner actually have a job right now" for
# <unit-name> -- see the top-of-file GITHUB-API BUSY CORROBORATION comment for the incident this
# closes. Echoes exactly one of:
#   idle    - GitHub confirms busy:false -- healthy, never wedged, no further check needed.
#   busy    - GitHub confirms a job HAS been assigned this whole window -- genuinely stuck.
#   absent  - GitHub has already stopped tracking this runner name -- the original 2026-08-05
#             wedge signature (job stuck `queued`, runner deregistered out from under it).
#   ""      - inconclusive (owner/repo unparseable, token unresolvable, or the API call itself
#             failed) -- callers MUST fall back to is_idle_listening(), never treat "" as a
#             verdict either way.
runner_busy_status() {
  local unit="$1" owner_repo owner repo inst pool idx host runner_name token resp
  owner_repo="$(unit_owner_repo "$unit")"
  [ -n "$owner_repo" ] || { echo ""; return; }
  owner="${owner_repo%%/*}"
  repo="${owner_repo#*/}"
  inst="${unit#*@}"; inst="${inst%.service}"   # e.g. "github-glue-runner-mtds@glue-1.service" -> "glue-1"
  pool="${inst%-*}"; idx="${inst##*-}"
  host="$(hostname -s 2>/dev/null || echo "")"
  [ -n "$host" ] || { echo ""; return; }
  # Same construction as glue-runner-run.sh's RUNNER_NAME -- must match GitHub's registered name
  # exactly or the lookup below silently finds nothing (falls through to "absent").
  runner_name="${pool}-${host}-${idx}"
  token="$(cached_gh_token)"
  [ -n "$token" ] || { echo ""; return; }
  resp="$(curl -sf -H "Authorization: Bearer ${token}" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${owner}/${repo}/actions/runners?per_page=100" 2>/dev/null || echo "")"
  [ -n "$resp" ] || { echo ""; return; }
  printf '%s' "$resp" | python3 -c "
import sys, json
try:
    runners = json.load(sys.stdin).get('runners', [])
except Exception:
    print('')
    sys.exit(0)
for r in runners:
    if r.get('name') == '${runner_name}':
        print('busy' if r.get('busy') else 'idle')
        sys.exit(0)
print('absent')
" 2>/dev/null || echo ""
}

# When GitHub confirms `busy: true` for a runner, `unit_active_seconds` (systemd unit/PROCESS
# uptime) is NOT a reliable proxy for "how long has the CURRENT JOB been running" -- found live
# 2026-08-08: this JIT-ephemeral process does not always exit/re-register between jobs (contrary
# to the "one job per process" design assumption elsewhere in this file: NRestarts stayed flat
# across several distinct jobs on the same PID). execution-service/glue-1 paged "wedged, active
# 3.2h" while its OWN job history showed a ~3h9m gap with ZERO jobs assigned, then several
# short (1-3 min) jobs landing right before the page fired -- the process had been alive 3.2h,
# but the CURRENT job was only minutes old. Resolves the actual in-progress job's own
# `started_at` via the Actions API so is_wedged() can measure job age, not process age. Echoes
# epoch seconds since that job started, or "" if no matching in-progress job is found (API
# hiccup, runner_name mismatch, or the "busy" job already completed between the two checks) --
# callers must NOT treat "" as "not wedged", only as "fall back to the coarser signal".
current_job_started_epoch() {
  local unit="$1" owner_repo owner repo inst pool idx host runner_name token
  owner_repo="$(unit_owner_repo "$unit")"
  [ -n "$owner_repo" ] || { echo ""; return; }
  owner="${owner_repo%%/*}"
  repo="${owner_repo#*/}"
  inst="${unit#*@}"; inst="${inst%.service}"
  pool="${inst%-*}"; idx="${inst##*-}"
  host="$(hostname -s 2>/dev/null || echo "")"
  [ -n "$host" ] || { echo ""; return; }
  runner_name="${pool}-${host}-${idx}"
  token="$(cached_gh_token)"
  [ -n "$token" ] || { echo ""; return; }
  # Bounded to the 20 most-recent in-progress runs -- a single repo's glue pool realistically
  # never has more in-flight at once; an unmatched scan degrades to "" (caller falls back to
  # unit_active_seconds), it never silently clears a real wedge.
  OWNER="$owner" REPO="$repo" RUNNER_NAME="$runner_name" TOKEN="$token" python3 -c "
import json, os, subprocess, sys

owner, repo, runner_name, token = os.environ['OWNER'], os.environ['REPO'], os.environ['RUNNER_NAME'], os.environ['TOKEN']


def api(path):
    r = subprocess.run(
        ['curl', '-sf', '-H', f'Authorization: Bearer {token}',
         '-H', 'Accept: application/vnd.github+json',
         f'https://api.github.com/repos/{owner}/{repo}{path}'],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0 or not r.stdout:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


runs = api('/actions/runs?status=in_progress&per_page=20')
if not runs:
    print('')
    sys.exit(0)
for run in runs.get('workflow_runs', []):
    jobs = api(f\"/actions/runs/{run['id']}/jobs\")
    if not jobs:
        continue
    for j in jobs.get('jobs', []):
        if j.get('runner_name') == runner_name and j.get('status') == 'in_progress' and j.get('started_at'):
            print(j['started_at'])
            sys.exit(0)
print('')
" 2>/dev/null || echo ""
}

# Seconds since the CURRENT job on <unit-name> started, per current_job_started_epoch() --
# "" (not 0) when unresolvable, so callers can distinguish "confirmed short-running" from
# "couldn't determine, don't trust this".
job_active_seconds() {
  local unit="$1" started_at epoch now
  started_at="$(current_job_started_epoch "$unit")"
  [ -z "$started_at" ] && { echo ""; return; }
  epoch="$(date -d "$started_at" +%s 2>/dev/null || echo 0)"
  [ "${epoch:-0}" -eq 0 ] && { echo ""; return; }
  now="$(date +%s)"
  echo $(( now - epoch ))
}

# <unit-name> is wedged if it's a JIT-ephemeral glue-* instance (never writer-*, those are
# long-lived by design) that's been continuously active well past any legitimate single job
# AND is not simply idle waiting for its next job (2026-08-06 fix -- live false-positive:
# execution-service's glue-1 paged CRITICAL at 3.1h/48MB with GitHub's own API confirming
# `busy: false` and the runner's own log showing "Listening for Jobs" as its last line the
# entire window; a pool that simply hasn't had a new job in hours is healthy, not wedged --
# the ORIGINAL 2026-08-05 case this check was built for was a real hung job at 5.6GB RSS with
# "Running job: ..." as its last log line, a genuinely different signature this now
# distinguishes instead of conflating).
is_wedged() {
  local unit="$1" active_state busy job_sec
  case "$unit" in
    *@glue-*) : ;;      # JIT-ephemeral pool -- eligible
    *) return 1 ;;      # writer-* or anything else -- long-lived by design, never wedged
  esac
  active_state="$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || echo "")"
  [ "$active_state" = "active" ] || return 1   # crash-looping units are "activating", not "active"
  [ "$(unit_active_seconds "$unit")" -ge "$WEDGED_THRESHOLD_SEC" ] || return 1
  # PRIMARY signal (2026-08-07): GitHub's own busy status, when resolvable -- see
  # runner_busy_status()'s own comment for the false-positive class this closes.
  busy="$(runner_busy_status "$unit")"
  case "$busy" in
    idle) return 1 ;;    # GitHub confirms no job assigned -- healthy, never wedged
    busy)
      # 2026-08-08 fix: measure the ACTUAL current job's age, not process uptime -- see
      # current_job_started_epoch()'s comment for the false-positive this closes.
      job_sec="$(job_active_seconds "$unit")"
      if [ -n "$job_sec" ]; then
        [ "$job_sec" -ge "$WEDGED_THRESHOLD_SEC" ]
        return $?
      fi
      return 0   # job-level lookup inconclusive -- fall back to the coarser process-uptime signal
      ;;
    absent) return 0 ;;  # GitHub already stopped tracking this runner -- the 2026-08-05 signature
    *) ;;                # inconclusive ("") -- fall back to the local journal heuristic below
  esac
  ! is_idle_listening "$unit"
}

was_alerted()  { grep -qxF "$1" "$STATE_FILE" 2>/dev/null; }
mark_alerted() { echo "$1" >> "$STATE_FILE"; }
clear_alerted() {
  grep -vxF "$1" "$STATE_FILE" > "${STATE_FILE}.tmp" 2>/dev/null || true
  mv "${STATE_FILE}.tmp" "$STATE_FILE"
}

was_candidate()  { grep -qxF "$1" "$WEDGE_CANDIDATE_FILE" 2>/dev/null; }
mark_candidate() { echo "$1" >> "$WEDGE_CANDIDATE_FILE"; }
clear_candidate() {
  grep -vxF "$1" "$WEDGE_CANDIDATE_FILE" > "${WEDGE_CANDIDATE_FILE}.tmp" 2>/dev/null || true
  mv "${WEDGE_CANDIDATE_FILE}.tmp" "$WEDGE_CANDIDATE_FILE"
}

# Fire a repository_dispatch carrying the alert. Returns 0 ONLY on a confirmed-sent dispatch --
# callers gate mark_alerted/clear_alerted on this. Found live 2026-08-05: this used to always
# `return 0` (token failure) or swallow the gh api call's real exit with a trailing `|| true`,
# so mark_alerted fired unconditionally regardless of whether anything actually reached Slack --
# a broken credential path silently marked every condition "already alerted" on its first
# (failed) attempt, permanently suppressing the real page. Never lets a dispatch failure abort
# the whole tick under `set -e` -- callers wrap this in an `if`, not a bare call.
dispatch_alert() {
  local message="$1" severity="$2" dedup_key="$3" recovery="$4" token
  token="$(resolve_gh_token)" || { log "FATAL: could not resolve GH token, skipping dispatch for ${dedup_key} -- will retry next tick"; return 1; }
  jq -n \
    --arg message "$message" \
    --arg severity "$severity" \
    --arg dedup_key "$dedup_key" \
    --argjson recovery "$recovery" \
    '{event_type: "glue-runner-health", client_payload: {message: $message, severity: $severity, dedup_key: $dedup_key, cooldown_min: 30, recovery: $recovery}}' \
  | GH_TOKEN="$token" gh api "repos/${GH_REPO}/dispatches" --input - 2>&1 | sed 's/^/[glue-runner-watchdog] /'
}

# BUG fixed 2026-08-05 (found live: this watchdog never once alerted, confirmed via an empty
# alerted-units state file despite a REAL 89-restart agent-orchestrator crash-loop earlier this
# same session): a bare `systemctl list-units --type=service --all` with NO pattern argument
# does not reliably enumerate JIT-ephemeral glue-N template instances that have cycled out of
# systemd's in-memory unit cache between jobs — verified live, it returned only 1 line (this
# watchdog's OWN unit, self-matched by the old `grep glue` filter) even with ~68 real
# glue-runner units genuinely present on the host. Passing an explicit PATTERN argument forces
# systemd to actively resolve matching units instead of only reporting whatever's already
# "interesting" in its cache — confirmed live: `list-units --all "github-glue-runner*"` reliably
# returns all 68. This also naturally excludes the watchdog's own unit (named
# `glue-runner-crash-loop-watchdog.service`, no `github-` prefix), so the old `grep glue`
# self-match is gone too, not just papered over.
mapfile -t units < <(systemctl list-units --type=service --all --no-legend "github-glue-runner*" 2>/dev/null \
  | grep -v token-refresh | grep -v slot-refresh | awk '{print $1}')

currently_crashlooping=()
for unit in "${units[@]}"; do
  if is_crash_looping "$unit"; then
    currently_crashlooping+=("$unit")
  fi
done

# NEW crash-loops: page once, mark alerted.
for unit in "${currently_crashlooping[@]}"; do
  if ! was_alerted "$unit"; then
    restarts="$(systemctl show "$unit" -p NRestarts --value 2>/dev/null || echo "?")"
    log "NEW crash-loop: ${unit} (NRestarts=${restarts}) -- paging"
    if dispatch_alert \
      "\`${unit}\` is crash-looping on \`${THIS_INSTANCE_ID}\` (\`NRestarts=${restarts}\`, state \`activating (auto-restart)\`) -- the runner process is DOWN, not just slow." \
      "CRITICAL" \
      "glue-runner-crash-loop:${unit}" \
      "false"; then
      mark_alerted "$unit"
    fi
  fi
done

# RECOVERY: previously alerted, now healthy -- one bookend post, then clear the state.
# Skips `wedged::`-prefixed lines -- those belong to the wedged-detection block below, which
# owns its own recovery pass over the same shared state file.
if [ -s "$STATE_FILE" ]; then
  while IFS= read -r unit; do
    [ -z "$unit" ] && continue
    case "$unit" in wedged::*) continue ;; esac
    still_looping=false
    for u in "${currently_crashlooping[@]:-}"; do
      [ "$u" = "$unit" ] && still_looping=true && break
    done
    if [ "$still_looping" = false ]; then
      log "RECOVERED: ${unit} -- posting bookend"
      if dispatch_alert \
        "\`${unit}\` recovered -- no longer crash-looping on \`${THIS_INSTANCE_ID}\`." \
        "INFO" \
        "glue-runner-crash-loop:${unit}" \
        "true"; then
        clear_alerted "$unit"
      fi
    fi
  done < "$STATE_FILE"
fi

# ── Wedged-runner check (2026-08-05) ──────────────────────────────────────────
currently_wedged=()
for unit in "${units[@]}"; do
  if is_wedged "$unit"; then
    currently_wedged+=("$unit")
  fi
done

# NEW wedges: page once, mark alerted. When the job-level lookup is inconclusive (job_sec
# empty), require TWO consecutive ticks (10min at the default 5min cadence) before paging.
#
# 2026-08-16 fix: found live, 4 false CRITICAL wedge pages within ~1h across 4 different repos'
# glue-N units (deployment-service, trading-agent-service, deployment-api,
# market-data-processing-service) -- every one's actual GH Actions run history showed only
# short (seconds-to-minutes) successful jobs, never anything close to WEDGED_THRESHOLD_SEC, and
# `gh api .../actions/runners` confirmed `busy:false` minutes later for all four. Root cause:
# these units ARE long-lived (many hours of process uptime, contrary to the "one job per
# process" JIT design -- a known quirk, see the top-of-file 2026-08-08 note) but were actively
# cycling through many short jobs successfully. Each time a fresh job landed,
# runner_busy_status() correctly reported busy=true, but current_job_started_epoch()'s own
# in-progress-run lookup raced against these very-short jobs finishing before its second API
# call completed (an already-documented failure mode in that function's own comment) --
# job_active_seconds() returned "", and this loop used to treat that unconditionally as a
# confirmed wedge, re-triggering the exact process-uptime false-positive class 2026-08-08 was
# supposed to have already fixed. A confirmed job age >= threshold still pages immediately (no
# debounce needed -- it is the strong, unambiguous signal); only the "inconclusive" fallback
# path now debounces one extra tick, which costs nothing against a genuine multi-hour hang.
for unit in "${currently_wedged[@]}"; do
  key="wedged::${unit}"
  if ! was_alerted "$key"; then
    job_sec="$(job_active_seconds "$unit" 2>/dev/null || echo "")"
    if [ -z "$job_sec" ] && ! was_candidate "$unit"; then
      log "wedge candidate (unconfirmed, job age unresolvable): ${unit} -- waiting for next tick to confirm before paging"
      mark_candidate "$unit"
      continue
    fi
    clear_candidate "$unit"
    active_sec="$(unit_active_seconds "$unit")"
    active_hr="$(awk -v s="$active_sec" 'BEGIN{printf "%.1f", s/3600}')"
    mem_mb="$(awk -v b="$(systemctl show "$unit" -p MemoryCurrent --value 2>/dev/null || echo 0)" 'BEGIN{printf "%.0f", (b+0)/1024/1024}')"
    if [ -n "$job_sec" ]; then
      job_hr="$(awk -v s="$job_sec" 'BEGIN{printf "%.1f", s/3600}')"
      duration_note="current job active **${job_hr}h** (process itself up ${active_hr}h)"
    else
      duration_note="process continuously active for **${active_hr}h** (current job's own start time not resolvable across 2 consecutive ticks)"
    fi
    log "NEW wedge: ${unit} (${duration_note}, ${mem_mb}MB) -- paging"
    if dispatch_alert \
      "\`${unit}\` on \`${THIS_INSTANCE_ID}\` has ${duration_note} (>${WEDGED_THRESHOLD_SEC}s threshold, ${mem_mb}MB resident) -- a JIT glue-runner should cycle every job. This is very likely a hung job holding the process alive (Restart=always never fires because it never exits) rather than a slow one. \`systemctl restart ${unit}\` re-registers a fresh JIT token; check GitHub's own runner list for this repo first (\`gh api repos/<owner>/<repo>/actions/runners\`) -- an empty list confirms GitHub has already abandoned tracking this run and nothing else will unstick it." \
      "CRITICAL" \
      "$key" \
      "false"; then
      mark_alerted "$key"
    fi
  fi
done

# Candidate cleanup: any unit still tracked as an unconfirmed candidate but no longer in
# currently_wedged this tick recovered before its second confirming tick -- drop it so a later,
# unrelated NEW wedge occurrence for the same unit starts its own fresh 2-tick confirmation
# instead of paging immediately off stale candidate state.
if [ -s "$WEDGE_CANDIDATE_FILE" ]; then
  while IFS= read -r cand_unit; do
    [ -z "$cand_unit" ] && continue
    still_candidate_wedged=false
    for u in "${currently_wedged[@]:-}"; do
      [ "$u" = "$cand_unit" ] && still_candidate_wedged=true && break
    done
    [ "$still_candidate_wedged" = false ] && clear_candidate "$cand_unit"
  done < "$WEDGE_CANDIDATE_FILE"
fi

# RECOVERY: previously alerted as wedged, now either restarted (fresh ActiveEnterTimestamp) or
# gone -- one bookend post, then clear the state.
if [ -s "$STATE_FILE" ]; then
  while IFS= read -r key; do
    [ -z "$key" ] && continue
    case "$key" in
      wedged::*) unit="${key#wedged::}" ;;
      *) continue ;;
    esac
    still_wedged=false
    for u in "${currently_wedged[@]:-}"; do
      [ "$u" = "$unit" ] && still_wedged=true && break
    done
    if [ "$still_wedged" = false ]; then
      log "RECOVERED (wedge): ${unit} -- posting bookend"
      if dispatch_alert \
        "\`${unit}\` recovered -- no longer wedged on \`${THIS_INSTANCE_ID}\`." \
        "INFO" \
        "$key" \
        "true"; then
        clear_alerted "$key"
      fi
    fi
  done < "$STATE_FILE"
fi

if [ "${#currently_crashlooping[@]}" -eq 0 ]; then
  log "OK -- 0/${#units[@]} glue-runner units crash-looping"
else
  log "ALERT -- ${#currently_crashlooping[@]}/${#units[@]} glue-runner units crash-looping: ${currently_crashlooping[*]}"
fi

if [ "${#currently_wedged[@]}" -eq 0 ]; then
  log "OK -- 0/${#units[@]} glue-runner units wedged"
else
  log "ALERT -- ${#currently_wedged[@]}/${#units[@]} glue-runner units wedged: ${currently_wedged[*]}"
fi
