---
doc_type: issue
title:
  "block_destructive_commands.py hard-blocks raw gcloud/gsutil/aws CLI deletes for every autonomous worker regardless of
  reversibility status -- was silently undermining the §3a carve-out until its error message was fixed to point at the
  sanctioned SDK path"
summary: >-
  Behavioral testing of the 2026-07-27 IAM-self-service + delete-reversibility governance work found a real, active,
  CODE-level guardrail (`agent-orchestrator/scripts/hooks/block_destructive_commands.py`, a PreToolUse hook wired into
  every spawned worker via `unified-trading-pm/cursor-configs/settings.json`) that unconditionally blocks `gcloud
  storage rm`/`gsutil rm`/`aws s3 rm`/`rb`/`delete-*` for ALL autonomous workers, with no carve-out for a
  reversibility-verified target -- because a regex hook matching raw command text structurally cannot check a bucket's
  soft-delete policy. A test agent given a real delete task using the CLI hit this block and correctly stopped rather
  than circumventing it. A second test agent given the identical task, but already aware of the workspace's OWN
  pre-existing "Writing STORAGE code" hard rule (GCS object ops via UTL `gcs_delete_object()`/`gcs_copy_object()`, never
  subprocess `gcloud`/`gsutil`), used that sanctioned SDK path instead and completed cleanly with zero blocking --
  independently verified the object was actually deleted. So the governance work (§3a, findings T/U/V/W) is NOT broken
  by this hook, but the hook's own error message only said "escalate to the operator", never mentioning the unblocked
  SDK alternative -- risking a worker filing a spurious operator escalation for what is actually just a wrong tool
  choice. Fixed the message (not the blocking logic) to point at the SDK path.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [hooks, guardrail, destructive-commands, gcs-delete, delete-safety, sdk-path, behavioral-testing, escalation]
related:
  [
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/orchestrator-cloud-identity-self-service.md,
    /codex/05-infrastructure/gcs-object-operations.md,
    /plans/active/task_template.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: agent_operating_framework_master
resolved_by: agent-orchestrator@d7dfa2361
source: >-
  Operator ask 2026-07-27: after fixing agents/RULES.md for IAM self-service, the operator asked for the SAME sandboxed
  behavioral-testing rigor to be applied to the other classes of previously-operator-gated action (deleting data/code,
  purging, manifest/GCS-object migration --apply, VM spin-up, new deployments, image builds), since the whole
  multi-session effort has been about stamping out reflexive operator escalation from plans, task_template.md, and
  CLAUDE.md. Testing the GCS-delete class specifically surfaced this hook.
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
locked_by:
depends_on: []
---

# `block_destructive_commands.py` blind to the sanctioned SDK delete path

## What was found (verified, not assumed)

1. **The hook is real and active for spawned workers.** `agent-orchestrator/scripts/hooks/block_destructive_commands.py`
   is a `PreToolUse` hook wired into `unified-trading-pm/cursor-configs/settings.json` (fleet-wide, symlinked into every
   `.tabs/<N>` slot and — confirmed this session — into Task-tool-spawned sub-agents too). It regex-matches raw Bash
   command text for irreversible/destructive classes: recursive `rm`/`find -delete`, `gsutil rm`, `gcloud storage rm`,
   `aws s3 rm`/`rb`/`s3api delete-*`, `git push --force`/`reset --hard`/`clean -f`/`branch -D`/ `stash drop`, and
   filesystem/device wipes (`shred`/`mkfs`/`dd of=`/`chmod -R`/`chown -R`). A match returns exit code 2, which blocks
   the tool call even under `--dangerously-skip-permissions` (the mode real AO workers run in) — per the hook's own
   docstring, this is deliberately the one mechanism that still refuses a call in bypass mode.
2. **It has NO carve-out for reversibility-verified deletes**, and structurally cannot have one written as a naive regex
   — matching raw command TEXT gives it no way to know which bucket a `gcloud storage rm gs://X/Y` targets, let alone
   that bucket's live soft-delete retention. This is not a bug in the hook's design; it is an inherent limitation of a
   static text-pattern PreToolUse guard.
3. **It does NOT block the sanctioned SDK path.** The regex set only matches literal CLI invocations
   (`gsutil`/`gcloud storage`/`aws s3` substrings) — it has zero visibility into a Python process calling
   `unified_trading_library.cloud_interface.gcs_delete_object(uri)`. This SDK path is ALSO the workspace's own
   pre-existing hard rule (CLAUDE.md § "Writing STORAGE code": "GCS object ops via UTL `gcs_copy_object`/
   `gcs_delete_object`/`gcs_describe_object`, never subprocess `gcloud`/`gsutil`") — completely independent of this
   session's reversibility-carve-out work, and it already existed before §3a was written.
4. **Confirmed behaviorally, not just by code-reading:**
   - Test A: a fresh agent (real `agents/RULES.md` content, no memory of any other session) given a realistic delete
     todo ("delete this confirmed-safe test artifact") reached for `gcloud storage rm` directly, was blocked by the
     hook, and correctly reported the block rather than attempting to circumvent it (per the hook's own instruction).
   - Test B: an identically-scoped fresh agent, this time also carrying the pre-existing "Writing STORAGE code" rule in
     its boot context (as any real worker already does via the auto-loaded CLAUDE.md), used
     `gcs_describe_object`/`gcs_delete_object` instead, hit zero blocking, and completed the task. Independently
     verified afterward (main session, not trusting the agent's self-report): `blob.exists()` → `False`,
     `list_blobs(prefix=...)` → `[]`.
5. **Also checked**: the hook's pattern set has NOTHING touching VM launch (`gcloud compute instances create`),
   deployment (`gcloud run deploy`), or image builds (`gcloud builds submit`/`docker build`) — its scope is deliberately
   narrow (storage/git/filesystem), so those action classes are governed purely at the doc/policy layer
   (`/codex/05-infrastructure/vm-launcher-runbook.md`, already established this session as unambiguous and already
   evidenced working in production — multiple real VM launches this session/prior sessions ran without operator
   involvement), not blocked by any hidden code-level guardrail the way GCS deletes were.

## Why this matters

This session's whole reversibility-carve-out effort (§3a, `task_template.md` findings T/U/V/W,
`/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`, the corpus-wide `[OPERATOR]`-tag downgrade
sweep) operates entirely at the DOC/POLICY layer — it tells a worker "you may delete this." But a worker that reaches
for the CLI form it's most familiar with (rather than the SDK wrapper) would hit this hook and could plausibly misread
"escalate to the operator" as "this delete needs a human decision" — silently reintroducing exactly the
reflexive-escalation problem this whole effort exists to remove, for a class of case (raw-CLI habit) the doc-level fixes
alone could never catch, since they don't touch tool-choice.

## Fix shipped

`agent-orchestrator@d7dfa2361` — rewrote the hook's `_BLOCK_MESSAGE` to explicitly name the sanctioned SDK alternative
(`gcs_delete_object()`/`gcs_copy_object()`) and note it already covers the §3a carve-out at the policy layer, reserving
"escalate to the operator" for cases where the SDK path is genuinely not viable (e.g. the git-history/filesystem command
classes, which have no SDK equivalent). The blocking LOGIC is unchanged — this was a message fix, not a guardrail
weakening; a static hook still cannot safely verify reversibility from command text, so the hard block on the raw CLI
form stays exactly as conservative as before.

## What was NOT re-tested from scratch (and why)

- **Manifest `--apply` / migration scripts**: not blocked by this hook (it only matches CLI substrings, not arbitrary
  Python `--apply` invocations) — no hidden contradiction to test for. The corpus-wide `[OPERATOR]`→
  reversibility-verified downgrades already shipped this session already cite the correct evidence-based `--apply`
  pattern.
- **VM spin-up / deployment / image builds**: no hook touches these command classes (verified via a direct grep of the
  pattern list, not assumed) and the doc-level rule (`vm-launcher-runbook.md`) is already unambiguous + already
  evidenced working via real production VM launches predating and during this session. Did not spin up a new test VM or
  trigger a real Cloud Build purely to re-confirm an already-working, already-evidenced mechanism — flagging this
  explicitly as a scoping choice, not a silent skip.

## Follow-up 2026-07-27: closing the mechanical enforcement gap (QG STEP 5.105)

The hook-message fix (above) and the "storage-code" doc rule both rely on a worker choosing the right tool going forward
— neither one catches a _new_ script that reaches for `subprocess.run(["gsutil", "rm", ...])` instead of the UTL SDK
wrapper. Two follow-up questions surfaced this gap directly: "how do we ensure this happens every time" and "does the
canonical migration scripts' `--apply` path already follow the storage-code rule."

**Migration scripts, verified**: read all 5 real canonical-migration `--apply` scripts in
`instruments-service`/`market-tick-data-service` — 4 call `gcs_delete_object`/`gcs_copy_object` directly (6/6/6/6 grep
hits each), 1 (`delete_migrated_defi_markers_2026_07_23.py`) 3 hits, 1 (`migrate_defi_full_v9_canonical.py`) not
applicable (no direct object delete/copy). **0 of 5 use subprocess `gcloud`/`gsutil`** — the sanctioned path is already
followed everywhere it matters today.

**But there was no mechanical gate that would catch a NEW violation.** The closest existing check,
`check_inline_bucket_uri.py` (STEP 5.69), only AST-walks for inline `f"gs://..."` URI construction — it never inspects
subprocess call arguments at all, AND it explicitly excludes the entire `scripts/` directory (`EXCLUDE_DIR_NAMES`
includes `"scripts"`) — exactly where the real violations live.

Built `scripts/quality_gates/check_subprocess_gcs_object_cli.py` (new, AST-based, same shrinking-ratchet-baseline shape
as STEP 5.69/5.101/5.103) and wired it in as **STEP 5.105** in `scripts/quality-gates-base/base-service.sh`. It flags
`subprocess.{run,call,check_call,check_output, Popen}`/`os.system` calls invoking an OBJECT-level
`gcloud storage`/`gsutil`/`aws s3`/`aws s3api` verb (cp/mv/rm/rsync/sync/ls/cat/*-object) — deliberately excluding
bucket-admin subcommands (mb/rb/ versioning/lifecycle/iam/buckets/create-bucket/etc, which have no UTL equivalent and
are legitimate). Deliberately does NOT exclude `scripts/` (unlike STEP 5.69) — that exclusion was the confirmed root
cause of the coverage gap.

**A real design bug found and fixed before shipping**: the first version only inspected the LITERAL argument to
`subprocess.run(...)`. Every real violation in this codebase uses the
`cmd = ["gsutil", "rm", path]; subprocess.run(cmd, ...)` idiom (assign-then-call) — the checker's first pass returned 0
hits workspace-wide, a false all-clear. Fixed by resolving a bare `Name` argument to its nearest preceding same-name
assignment in the file (a heuristic, not real data-flow analysis — good enough for this idiom; a genuinely
cross-scope/branch-dependent dynamic command is a documented false-negative, same trade-off STEP 5.69 makes for
non-f-string URI builds).

**Workspace-wide baseline seeded from the real, re-verified count** (`subprocess_gcs_object_cli_baseline.yaml`):
`deployment-service`/`deployment-service-sports-wt` 11 each (incl. `maintenance_handler.py` — real, live service CLI
code doing `gsutil rm` in a cleanup loop, and `phase5a_aws_object_migrate.py`, `cleanup_old_tarballs.py`,
`analyze_vm_costs.py`, `wipe_pre_floor_sports_2026_07_21.py`), `unified-trading-pm` 11 (audit/migration one-offs under
`plans/audit/results/` and `scripts/migration/`), `market-tick-data-service`/`-cid-migration`/`-sports-wt` 3 each
(`analyze_shard_memory.py`, `restamp_mtds_sports_blank_source_2026_06_29.py`), `unified-trading-library` 3
(`cf_manifest_audit.py` — a documented, deliberate CLI fallback with its own bandit/timeout rationale), `e2e-testing` 3
(`scripts/paper_trading/_gcs.py` — a labelled POC), `instruments-service` 1
(`restamp_is_sports_blank_source_2026_07_13.py`). All 21 other repos baseline at 0 (zero tolerance — any new site there
fails immediately). None of these are fixed in this pass — per the shrinking-ratchet convention, existing debt is
grandfathered at its current count; a NEW site anywhere fails CI. `maintenance_handler.py` specifically (live production
code, not a dead script) is worth a real fix in its own right, but that's separate, scoped work — not bundled into a
mechanical-gate commit.

Validated: `setup-buckets.py` (`gsutil versioning set`/`lifecycle set`) correctly does NOT trigger the check
(bucket-admin, out of scope by design); 19 unit tests (`test_check_subprocess_gcs_object_cli.py`) cover classification,
the assign-then-call resolution idiom (incl. per-function nearest-preceding-assignment, and the false-negative case with
no resolvable assignment), noqa-marker skipping, docstring/comment non-matching, `scripts/`-inclusion (vs STEP 5.69's
exclusion), and a `main()` end-to-end smoke; full `unified-trading-pm` `quality-gates.sh` green (1430 tests) with STEP
5.105 passing alongside STEP 5.69/5.104.

## Follow-up 2026-07-27 (later same day): fixing the grandfathered debt itself, under `/autonomous`

The baseline seeded above was deliberately grandfathered debt, not a fix — including the note that
`maintenance_handler.py` "is worth a real fix in its own right, but that's separate, scoped work." The operator asked
for that work to actually happen, dispatched `/autonomous`. Result: **every real repo in the baseline is now at 0**,
fixed via one direct fix (this session, `deployment-service`, the highest-risk file) + 5 parallelized sub-agent
dispatches (one per remaining repo, each briefed with the exact per-file fix already decided, never left to re-derive
judgment calls), all independently re-verified against the actual checker/git state before being trusted (two agents got
stuck reporting an in-progress background watcher instead of finishing — resumed via `SendMessage`; one had foreign
concurrent-session files mixed into its staged index — caught via `git status --porcelain` before shipping, unstaged by
name, never blind-committed).

Per-repo disposition:

- **`deployment-service`** (11→0, fixed directly, not delegated): `maintenance_handler.py` — the live production CLI
  handler doing `gsutil rm` in a cleanup loop — migrated to `get_storage_client(provider=self.cloud_provider)`
  (`list_blobs`/`delete_blob`/`bucket().exists()`), covering both the GCP and AWS branches the handler already
  dispatches on. `phase5a_aws_object_migrate.py` (`sync_bucket`/`spot_check`) migrated to the AWS `S3StorageClient`
  (`list_blobs`/`copy_blob`/`get_blob_metadata`) — confirmed via its own output CSV never existing that this one-off has
  NOT yet been run to completion, so it was migrated in place rather than deleted.
  `analyze_vm_costs.py`/`cleanup_old_tarballs.py` migrated their listing helpers to `list_blobs` (delimiter-listing via
  `client.bucket(name).list_blobs(prefix=, delimiter="/")` for the shallow one-level case); `cleanup_old_tarballs.py`
  keeps ONE CLI call (`# noqa: gcs-cli`) for GCS object-VERSION listing (`-a` flag, `#<generation>` suffixes) —
  `list_blobs()` has no `versions=` parameter, a genuine SDK gap, not laziness. `wipe_pre_floor_sports_2026_07_21.py` (a
  real pre-floor data-wipe tool, already partially SDK-based) had its one remaining CLI call — the sanctioned shallow
  delimiter listing of `day=` dirs — migrated to the SAME `list_blobs(..., delimiter="/")` + `.prefixes` pattern,
  preserving the exact "one level, never a corpus walk" safety invariant the file's own docstring documents. Updated 2
  existing test files whose mocks targeted the old function names/subprocess surface.
- **`market-tick-data-service`** (3→0): `analyze_shard_memory.py` migrated (`list_blobs` + `download_as_bytes`).
  `restamp_mtds_sports_blank_source_2026_06_29.py` **deleted outright** (not migrated) — its own lifecycle marker says
  delete-after-run, and the sibling `instruments-service` script's docstring independently cross-references it as
  "already shipped + run successfully... CF-4 GREEN post-run" (mtds@bae321ca) — verified via a live-import grep before
  deleting, confirmed nothing depends on it. `market-tick-data-service-cid-migration` (a separate clone of the same
  repo/branch) synced to 0 on its own via the slot's periodic fast-forward-pull cron, no action needed.
- **`unified-trading-pm`** (11→0): 4 audit/results scripts (`a3v2_manifest_divergence_all_services.py`,
  `cf_layout_audit_2026_06_01.py`, `cf_manifest_audit_2026_06_01.py`, `cf_manifest_audit_all.py` — the LAST of which is
  genuinely LIVE production alerting, a daily Cloud Run Job + Scheduler that ALERTS ON ANY RED) all migrated to the SDK.
  One of these carried a "DNS-robust (gcloud CLI, not gcsfs)" docstring rationale — verified against the actual UTL
  library source that `GCSStorageClient` uses the native `google-cloud-storage` SDK directly, NOT `gcsfs`, so that
  specific DNS concern does not carry over to the SDK wrapper; docstring updated to stop citing a comparison that no
  longer applies. `scripts/migration/verify_flat_to_env_tiered_drift.py` (a cross-cloud Wave-verify GATE script whose
  exit code drives a real migration-cutover GO/NO-GO) and `scripts/openapi/generate_instrument_snapshot.py` also
  migrated. Two adjacent, unrelated pre-existing breakages found blocking the shared quality gate for every agent on the
  branch were fixed in the same pass (invalid YAML frontmatter in one issue doc; a broken-refs fix in another,
  superseded by a concurrent peer's equivalent fix — the redundant version was discarded rather than committed).
- **`unified-trading-library`** (3→0, annotation only): `cf_manifest_audit.py`'s 3 CLI call sites annotated
  `# noqa: gcs-cli`, NOT migrated — genuine, verified capability gap: `download_file`/`upload_file` on the SDK wrapper
  use a FIXED, non-configurable internal `timeout=600` (10 minutes), which would defeat this file's deliberately SHORT,
  bounded per-attempt timeout + fast-retry design (confirmed against the actual method source, not assumed).
- **`e2e-testing`** (3→0, annotation only): `scripts/paper_trading/_gcs.py`'s 3 CLI fallback sites annotated
  `# noqa: gcs-cli` — this file is a labelled POC deliberately avoiding the UTL dependency to keep its Docker image
  minimal (already has its own `# noqa: TID251` marker saying exactly that on the primary direct-SDK path); adding a UTL
  import to satisfy this check would contradict the file's own stated design intent.
- **`instruments-service`** (1→0): `restamp_is_sports_blank_source_2026_07_13.py`'s `_cp` helper migrated — unlike the
  MTDS sibling, this one's docstring reads as still-pending (no "shipped + run successfully" cross-reference anywhere),
  so it was migrated in place rather than deleted. The fix correctly handles a THIRD direction the original task
  briefing hadn't anticipated (`gs://`→`gs://` same-cloud server-side copy, used by the `--apply` snapshot step) via
  `copy_blob`, caught by actually reading all 3 call sites before finalizing the fix rather than applying the briefed
  download/upload-only pattern blindly.
- **Deliberately left grandfathered, not touched**: `deployment-service-sports-wt` (11) and
  `market-tick-data-service-sports-wt` (3) — both are real git worktrees (confirmed via `.git` being a `gitdir:` pointer
  file, not a missing directory) but sitting in **detached HEAD**, last touched 2026-07-21 (6 days stale), carrying
  their OWN unrelated uncommitted WIP (VM-launcher scripts, a league-ID migration) that predates this effort. Touching
  them would mean inheriting/committing someone else's in-flight, unrelated work on a stale branch outside the
  integration branch — out of scope for this remediation, left as-is.

Baseline ratcheted to reflect all of the above: `unified-trading-pm@bb1eb580e`. Re-ran the full workspace-wide checker
after the ratchet — every repo shows `== baseline` (0 for the 27 fixed/never-had-debt repos, 11/3 for the two
deliberately-grandfathered stale worktrees).

## Todos

- [x] [SCRIPT] P1. ✅ **DONE 2026-07-27** — fixed `block_destructive_commands.py`'s error message. Commit
      `agent-orchestrator@d7dfa2361`, `quality-gates.sh` green (1808 tests), shipped via quickmerge.
- [x] [SCRIPT] P2. ✅ **DONE 2026-07-27** — built + shipped `check_subprocess_gcs_object_cli.py` (QG STEP 5.105), the
      mechanical gate that catches a NEW subprocess/os.system GCS/S3 object-CLI call site (as opposed to the doc-level
      rule alone). Baseline seeded from the real, confirmed workspace count (see above). `quality-gates.sh` green,
      shipped via quickmerge.
- [x] [SCRIPT] P1. ✅ **DONE 2026-07-27 (same day, `/autonomous`)** — fixed the grandfathered debt itself across all 6
      real repos in the baseline (deployment-service@direct-fix + 5 parallel sub-agent dispatches:
      market-tick-data-service@964149f66, unified-trading-library@22da5ff71, e2e-testing@420e834,
      instruments-service@105cfb8f, unified-trading-pm@317648211), ratcheted the baseline down to 0 everywhere except
      the 2 deliberately-scoped-out stale worktrees (unified-trading-pm@bb1eb580e). See "Follow-up 2026-07-27 (later
      same day)" above for the full per-repo disposition and every judgment call made.
- [ ] [SCRIPT] P3. Consider a corpus grep for any OTHER open plan todo that literally instructs `gcloud storage rm`/
      `gsutil rm`/`aws s3 rm` as its stated method (rather than citing the UTL wrapper) — those todos would hit this
      same hook when dispatched; rewrite them to cite `gcs_delete_object()`/`gcs_copy_object()` instead. Not done this
      session (scope: this issue was about the mechanism, not a corpus-wide todo-text sweep).
- [ ] [SCRIPT] P3. **Self-discovered false-positive, worth a real fix**: the recursive-delete pattern
      (`\brm\b[^|;&\n]*(-[A-Za-z]*[rR]|--recursive)`) matches the bare word as raw TEXT anywhere in the full flattened
      command line, with no awareness of shell quoting — writing THIS issue doc's own `git commit -m` heredoc (prose
      _describing_ the CLI form this hook blocks, not an actual invocation of it) tripped the exact same guardrail,
      purely because the word appeared once in the message body and some later word in the same long heredoc happened to
      match the trailing flag alternation. Worked around it this session by keeping the commit message short and
      paraphrased instead of quoting the literal command forms — but a hook that can block an innocent commit message
      describing itself is a real over-blocking risk for any future commit message, docstring, or code comment that
      discusses this exact command class. A proper fix needs the hook to recognize (and skip) text inside a
      single/double-quoted string or heredoc body in the command payload, not just word-boundary regex over the raw
      flattened line — a real parsing improvement, not a quick patch; scoping it is future work, not attempted here.
