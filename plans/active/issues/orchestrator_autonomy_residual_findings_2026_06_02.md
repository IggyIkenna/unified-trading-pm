---
title:
  "orchestrator_autonomy_audit_remediation residual open findings — F1 (running VM behind LDR HEAD), F2 (vm-ml
  stopped/SSM-degraded), FM3 (foreign-repo playwright-report not gitignored) — surfaced when the parent plan was
  archived 2026-06-01 with these still open"
created: 2026-06-02
author: ikenna (slot-1)
source:
  - plans/archive/2026_06/orchestrator_autonomy_audit_remediation_2026_06_01.md (archived with Findings F1/F2 open + FM3
    deferred to "those repos' owners" with NO named successor plan — violates the archival deferred-work HARD RULE)
  - bash scripts/orchestrator/verify_fleet_autonomy_health.sh @ 2026-06-02T05:19Z (vm-orchestrator behind=3 flags=4/4
    ver=0.6.0; api-host behind=0; 9 epic VMs ssm-send-command-failed)
  - aws ec2 describe-instances 2026-06-02T05:20Z (2 RUNNING:
      vm-orchestrator i-007e8d99d12831578 + agent-orchestrator-vm-1
    i-0c9b283b31d6b5ca7; 9 STOPPED: cefi/defi/ml/operator-ops/prediction/sports/tradfi/trading-core/cross-cutting)
  - deployment-ui/.gitignore (no playwright-report line) + git ls-files (1 tracked playwright-report artifact) @
    2026-06-02
parent_epic: plans/epics/orchestrator_master.md
locked_by: orchestrator_autonomy_residual_findings_2026_06_02
---

## What I found

The `orchestrator_autonomy_audit_remediation_2026_06_01` plan was archived 2026-06-01 stating "all phases complete." All
four phases of **code** did ship + QG-green + deploy. But three items in the plan's own Findings / deferred-work banner
were **not actually closed**, and the archive carried them silently (the FM3 deferral names no successor plan, which is
the archival deferred-work HARD RULE):

### F1 — running VM behind LDR HEAD; FF-cron not keeping it current

2026-06-01 run found 3 VMs behind LDR HEAD (vm-orchestrator −6, vm-operator-ops −5, vm-prediction −6). As of
2026-06-02T05:19Z the fleet has consolidated to **2 running VMs**, and the picture is:

- **vm-orchestrator** (i-007e8d99d12831578, RUNNING) — `behind=3` vs `origin/live-defi-rollout`, flags=4/4, ver=0.6.0.
  The FF-pull cron is supposed to keep its agent-orchestrator worktree current and is not (3 commits stale: `478b3ff`
  slack-auth-alert, `11c2212` docs, `1fe3386` api-host swap-headroom). Root cause to confirm: dirty/diverged worktree
  blocking FF, or wedged `slot-cron-ff-pull.sh`, or the agent-orchestrator base-branch resolution.
- **api-host / agent-orchestrator-vm-1** (i-0c9b283b31d6b5ca7, RUNNING) — `behind=0`, flags=4/4, `/health` ver=NA
  (central health on :8765 not :8026 — known, not an outage).

### F2 — vm-ml SSM-degraded → now STOPPED

2026-06-01 finding: vm-ml SSM execution returned Status=Failed for every command (suspected disk-full from the
historical 142k-line backlog bloat or a wedged SSM agent), so its autonomy flags + currency were unverified. As of
2026-06-02 **vm-ml (i-02294132088f23e50) is STOPPED** along with the other 8 epic VMs — the fleet was intentionally
consolidated to 2. The SSM-broken state is therefore latent, not live; but it MUST be cleared (disk + SSM agent)
**before vm-ml is next started**, or the same wedge recurs on boot.

### FM3 — foreign-repo playwright-report still tracked + not gitignored, no successor plan

The archived plan deferred the belt-and-suspenders (`git rm --cached` + `.gitignore playwright-report/` in
**deployment-ui** + **user-management-ui**) to "those repos' owners" with **no named successor plan** — a deferred-work
HARD RULE gap. Confirmed still open 2026-06-02: `deployment-ui/.gitignore` has no `playwright-report` line and
`git ls-files` still shows 1 tracked `playwright-report` artifact. (The agent-orchestrator-side FM3,
`restore_generated_artifacts`, did ship @1f9af64 — only the foreign-repo half is open.)

## Why it matters

- **F1**: a running orchestrator VM silently 3 commits behind LDR is the exact "stale server code" state the worktree
  model + FF-cron exist to prevent. If the FF cron is wedged it will keep drifting; this is also the canonical signal
  the deploy-currency gate watches.
- **F2**: a stopped VM that wedged SSM on its last run will wedge again on next boot — and SSM-broken means it can't be
  remediated remotely (SSM itself can't execute). Needs disk-clear + SSM-agent restart on/just-after boot.
- **FM3**: a tracked regenerated artifact is precisely what triggers FM3 working-tree pathologies (orphan-wip commits of
  build output) on those UI repos' slots. Leaving it tracked + un-gitignored re-arms the failure on every respawn.

## Recommended decision

1. **F1** — SSM into vm-orchestrator, inspect the agent-orchestrator worktree, FF (or force-reset to
   `origin/live-defi-rollout` if dirty/diverged — operator-authorized 2026-06-02), restart orchestrator, confirm
   `slot-cron-ff-pull.sh` is installed + last-run <10min. Re-run `verify_fleet_autonomy_health.sh` to confirm behind=0.
2. **F2** — gate vm-ml's next start on a disk-headroom + SSM-agent-health check; document the
   clear-disk-then-restart-SSM recipe in the start path. Until vm-ml is needed, leave stopped (no live risk).
3. **FM3** — file/hand to the deployment-ui + user-management-ui owners: `git rm --cached` the tracked playwright-report
   artifact + add `playwright-report/` to each repo's `.gitignore`. Out of agent-orchestrator scope but now NAMED here
   so it is no longer a silent deferral.

This issue doc archives once all three are resolved (per issue-doc-lifecycle: surfaces UNACKED work; closes when acked
into shipped code / owning repo).

## Resolution (2026-06-02, operator-driven fleet refresh)

**F1 — RESOLVED.** Root cause was NOT a missing ao-self-pull cron — vm-orchestrator HAD the `*/15` ao-self-pull root
cron all along. It was **skipping every run**: `data/state/fleet_registry.json` was not in `.gitignore` (only the
`state.db*`/`state.json` files were), so `git status` was never clean and `ao-self-pull.sh`'s dirty-guard
(`skip on any porcelain output`) bailed before the FF. Fixed by ignoring the whole `data/state/` runtime dir wholesale
(agent-orchestrator `b055f1a`; nothing under it is tracked). Both RUNNING VMs FF'd to current HEAD, **clean**,
ao-self-pull verified functional ("already current"): vm-orchestrator (i-007e8d99…) + api-host/agent-orchestrator-vm-1
(i-0c9b283b…).

**F2 — RESOLVED.** vm-ml's SSM came back Online after a stop/start (it was a stopped/wedged instance, not a
running-but-broken one). All 9 stopped epic VMs were started, FF'd to current HEAD (behind=0, dirty=0), ao-self-pull
cron confirmed present, and **re-stopped** (fleet stays consolidated to 2 running). Disk pressure relieved on the tight
ones (operator-ops 100%→93%, defi 98%→86%, prediction 97%→80% via `.npm`/`.cache`/journal clear); the stale
non-canonical `server/orchestrator.db` on operator-ops (a second un-ignored runtime DB, the lone dirty file there) was
moved aside.

**FM3 — partially obsoleted + remaining half NAMED.** `user-management-ui` is ARCHIVED (folded into
`unified-trading-system-ui` 2026-05) so only **deployment-ui** remains: still has a tracked `playwright-report` artifact
and no `playwright-report/` `.gitignore` line. See open todo below.

**Also done this session (related):** agent-orchestrator `main` FF'd to `7f0bdbf` (== LDR; main is agent-orchestrator's
canonical branch per the repo exception) — operator-authorized override of the HS256-retirement soak gate. Fresh
**AMI built from main** after fixing two pre-existing bugs in the (previously never-successfully-run) packer build path:
(1) warm-cache cloned PRIVATE repos over unauth'd https → inject `gh_pat` as a git `insteadOf` cred, scrubbed in cleanup
(deployment-service `b5e4f01`); (2) `uv` installed under `/home/ubuntu/.local/bin` (HOME preserved by `sudo -E`) but the
symlink logic only checked `/root/*` → `uv: command not found` → resolve wherever it landed (deployment-service
`823ec84`).

**AMI produced:** `ami-008943905b499a3f4` (ap-northeast-1, `agent-orchestrator-20260602-055620`, Branch tag
`live-defi-rollout` == main == `7f0bdbf`, State=available). Consume via `AMI_ID=ami-008943905b499a3f4 bash
deployment-service/scripts/vm/launch-epic-vm-aws.sh --vm-id <id>` (the launcher's AMI_ID is optional; cold-bootstrap is
the fallback). A 3rd packer bug was fixed to get here: `--global` insteadOf went to /root/.gitconfig but warm-cache's
`sudo -E` git reads /home/ubuntu/.gitconfig → switched to `--system` /etc/gitconfig (deployment-service `5186179`).

## Remaining open todos — ALL CLOSED 2026-06-02

- [x] ✅ [SCRIPT] P2. **deployment-ui FM3** — DONE (deployment-ui `8f1fe86`): `git rm --cached playwright-report/index.html`
      + `playwright-report/` added to the repo-specific-exceptions section of `deployment-ui/.gitignore` (survives the
      central-template sync). `unified-trading-system-ui` (which now holds the user-management/auth functionality folded
      in from the archived `user-management-ui`) already ignored it + tracked 0 such files — no work needed there.
      Non-behavioral repo-hygiene change; no UI surface touched (playwright gate N/A).
- [x] ✅ [INFRA] P2. **Epic-VM disk-bloat guard** — DONE (agent-orchestrator `5508efa`, on LDR + main):
      `scripts/vm-disk-guard.sh` vacuums regenerable caches (npm `_cacache`, uv/pip wheels) + the journal when root
      usage ≥ THRESHOLD (default 80%); touches nothing under repos/data/state; always exits 0. `bootstrap_vm.sh` Step
      7.5 idempotently ensures the root cron (every 6h) so AMI-launched + re-provisioned VMs inherit it. Installed +
      proven on both RUNNING VMs (vm-orchestrator caught at 94%→84%, api-host 61%→57%). **The 9 stopped epic VMs** get
      the script via the AMI/LDR clone but their crontab is only ensured by `bootstrap` — see the one residual below.

## One residual — CLOSED 2026-06-02

- [x] ✅ [SCRIPT] P3. **vm-disk-guard cron installed on all 9 stopped epic VMs** — started all 9, installed the root cron
      (every 6h) + test-ran the guard (freed space on most: cefi 82→75%, trading-core 89→71%, sports/tradfi 57→48%),
      then re-stopped. The cron now persists in each VM's EBS crontab, so all 11 fleet VMs (2 running + 9 stopped) carry
      it. **Root cause of the high usage (corrected after a real `du`):** NOT the repo footprint — it was **`/tmp` (9G
      on vm-orchestrator) full of 3-4-day-old throwaway test/QG/repro venvs (`vm-venv`, `vm-repro-venv*`, `test_venv*` @
      ~1.7G each) + stale QG logs/parquets**. The cache-only guard couldn't reclaim it (it skipped /tmp). Enhanced the
      guard (agent-orchestrator `2c7ec6b`, LDR+main) to age-gate-vacuum stale `/tmp` (older than TMP_AGE_DAYS=2, excluding
      live systemd-private + X11/ICE sockets) → vm-orchestrator dropped **84%→52%** (/tmp 9.0G→83M). The legit baseline
      (~11G: 8 slot worktrees + venvs in /home) is correct and stays. The 9 stopped VMs reclaim their stale /tmp on next
      boot (updated script via clone + already-installed cron).

**Better fix — /tmp is now a capped tmpfs (the real answer to "why does /tmp persist at all"):** /tmp's contract is
transient/safe-to-wipe, so it is now RAM-backed (`tmpfs /tmp ... size=2G,mode=1777`) — auto-clears on reboot and the 2G
cap makes a runaway test/repro venv fail fast instead of wedging the 30G root. Safe on the 16G+ fleet VMs (tmpfs uses RAM
only as files exist). Baked into `bootstrap_vm.sh` Step 7.6 (agent-orchestrator `70b916e`, LDR+main); **active on both
running VMs** (vm-orchestrator + api-host, verified healthy :8026=200 / central :8765=200 after the live remount); fstab
written on all 9 stopped VMs (activates on their next start). All 9 also brought to freshest code (`70b916e`) + both
disk-guard crons (6h + @reboot). The `vm-disk-guard` /tmp branch is now belt-and-suspenders behind the tmpfs.

This issue doc is fully resolved (F1/F2/FM3 + disk-guard all closed) — ready to archive into the orchestrator epic.
