# Coverage Override Policy

## Goal

Only the workspace admin (GitHub user `IggyIkenna`) may push a PR that fails the coverage-regression gate (current
coverage < `MIN_COVERAGE` floor in `scripts/quality-gates.sh`). Everyone else hits a hard block.

Enforcement is **defence-in-depth** — local checks catch mistakes early, remote checks are the real teeth.

## Layer 1 — Local quickmerge check

Implemented in the canonical [`scripts/quickmerge.sh`][qm] (propagated to every repo). Behaviour:

1. `bash scripts/quality-gates.sh` runs inside Phase 3 as usual.
2. Output is captured to a temp log.
3. If QG fails AND the log contains any of `Required test coverage of X% not reached`,
   `Coverage failure: total of X% is less than fail-under=Y%`, `fail_under`, or `cov-fail-under` → classify as
   **coverage regression**.
4. Without `--admin-override-coverage`, quickmerge exits 1 and prints the fix: either write tests or escalate to admin.
5. With `--admin-override-coverage`:
   - quickmerge calls `gh api user --jq .login` to resolve the invoker's GitHub username
   - rejects anyone whose login != `$COVERAGE_ADMIN_USER` (default `IggyIkenna`, env-overridable for tests)
   - appends every attempt — accepted _and_ rejected — to [`coverage-override-audit.log`](coverage-override-audit.log)
6. Any OTHER QG failure (lint, typecheck, codex, regular test fail) is **not** bypassable by the override flag.

### Caveats

- This runs on the developer's machine. A committer with repo access can edit `scripts/quickmerge.sh` to remove the
  check. That's why Layer 2 exists.
- Single-source-of-truth: edit the canonical copy at `unified-trading-pm/scripts/quickmerge.sh`, then rollout:
  ```bash
  for r in $(ls -d */ | grep -v unified-trading-pm); do
      [ -f "$r/scripts/quickmerge.sh" ] && cp unified-trading-pm/scripts/quickmerge.sh "$r/scripts/"
  done
  ```

## Layer 2 — GitHub branch protection (the real enforcement)

Set once per repo; applies to every contributor regardless of what their local scripts say.

### Required settings on `live-defi-rollout`, `staging`, `main`

Settings → Branches → Add rule → Branch name pattern:

```
live-defi-rollout
staging
main
```

Enable:

- ☑ **Require a pull request before merging**
  - ☑ Require approvals: **1**
  - ☑ Dismiss stale PR approvals when new commits are pushed
  - ☑ Require review from Code Owners (optional but recommended)
- ☑ **Require status checks to pass before merging**
  - ☑ Require branches to be up to date
  - Required checks:
    - `quality-gates` (the GHA workflow that runs `scripts/quality-gates.sh` with the same
      `--cov-fail-under=$MIN_COVERAGE` as local quickmerge)
    - `semver-agent` (for `staging` and `main`)
- ☑ **Restrict who can push to matching branches**
  - Pushes: organisation admins only
- ☑ **Do not allow bypassing the above settings**
- ☑ **Allow force pushes**: **disabled**
- ☑ **Allow deletions**: **disabled**
- ☑ **Allow admins to bypass**: (this is the admin escape hatch — IggyIkenna, as org admin, is the only user who can
  merge past a failing `quality-gates` check)

### CLI rollout (avoid clicking 27 × 3 = 81 forms)

```bash
# Requires org admin PAT.
gh api --method PUT /repos/IggyIkenna/<repo>/branches/live-defi-rollout/protection \
    --input branch-protection.json
```

Store a single `branch-protection.json` template in `unified-trading-pm/ops/branch-protection-template.json` and apply
via [`scripts/propagation/apply-branch-protection.sh`](../scripts/propagation/) (new script — follow the pattern in
`scripts/propagation/rollout-workflow-templates.sh`).

## Layer 3 — Audit log

Every invocation of `--admin-override-coverage` — whether the user is allowed or not — is appended to
[`coverage-override-audit.log`](coverage-override-audit.log). Format:

```
2026-04-19T14:22:17Z REPO=execution-service USER=IggyIkenna RESULT=accepted MSG="fix(live): hotfix override"
2026-04-19T14:25:03Z REPO=market-tick-data-service USER=<non-admin> RESULT=rejected (not IggyIkenna)
```

Inspect with:

```bash
tail -f unified-trading-pm/ops/coverage-override-audit.log
```

Any rejected attempt = someone tried to bypass. Review with them directly. Any accepted attempt = the admin took a
documented shortcut. Each entry includes the commit message, so the reason is captured.

## Change-of-admin procedure

The admin username is `IggyIkenna` hard-coded as the default of `COVERAGE_ADMIN_USER` in [`scripts/quickmerge.sh`][qm].
To change:

1. Edit the default in the canonical PM copy.
2. Propagate to all repos (same script shown above).
3. Update GitHub branch-protection org-admin list.
4. The change itself must ship through the override (since the admin is changing) — log it in the audit trail with a
   clear commit message.

## References

- [quickmerge.sh — canonical][qm] — lines parsing `--admin-override-coverage` and the Phase-3 QG capture/detect/gate
  block
- [coverage_ratchet_policy_2026_04_19.md](../plans/active/coverage_ratchet_policy_2026_04_19.md) — the ratchet that sets
  each repo's `MIN_COVERAGE`
- [coverage-floor-guard.sh](../scripts/coverage-floor-guard.sh) — system-floor governance (70) + per-repo exception
  files

[qm]: ../scripts/quickmerge.sh
