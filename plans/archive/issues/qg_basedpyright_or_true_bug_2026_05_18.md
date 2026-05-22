---
title: "QG basedpyright || true bug — exit code always 0, errors silently swallowed"
created: 2026-05-18
author: slot-6 (hk)
source:
  - base-service.sh line ~467 (wait $BP_PID || true; PYRIGHT_EXIT=$?)
  - batch-live-reconciliation-service — 16 basedpyright errors were silently passing QG
locked_by: live-defi-rollout
---

> **🟡 SUBSUMED BY MEGA AUDIT** — findings absorbed by **Phase D cross-cutting QG ratchet plan** per
> [mega_audit_and_plan_beefup_progression_2026_05_20.md](mega_audit_and_plan_beefup_progression_2026_05_20.md) (slot-1
> triage 2026-05-20). The `|| true` bug + 16 silent batch-live-reconciliation errors are the canonical QG-ratchet item;
> fix + regression test fold into D-QG-ratchet. Do NOT work standalone.

## What I found

`base-service.sh` captures basedpyright's exit code as:

```bash
wait $BP_PID || true
PYRIGHT_EXIT=$?
```

With `|| true`, PYRIGHT_EXIT is **always 0** regardless of whether basedpyright found errors. The
`if [ "$PYRIGHT_EXIT" -ne 0 ]` block that triggers `log_fail "Type check FAILED"` NEVER fires.

The only remaining catch is the warnings check:

```bash
WARN_COUNT=$(echo "$PYRIGHT_OUT" | grep -c " warning:" || :)
```

This catches warnings but NOT errors. A repo with "16 errors, 0 warnings" passes QG as if type-checked clean.

**Confirmed:** `batch-live-reconciliation-service` had 16 basedpyright errors (14 from pyarrow missing type stubs + 2
`reportAny` cast violations) — QG reported "✅ ALL QUALITY GATES PASSED" for all prior commits despite these errors.
Fixed in batch-live-reconciliation@983e4ad.

**Root cause:** `|| true` was added to prevent `set -e` from killing the script when basedpyright exits non-zero. But it
inadvertently also zeroed out `PYRIGHT_EXIT`.

## Why it matters

- **All repos with basedpyright errors are silently passing type checks.** The zero-error type-check guarantee that the
  QG is supposed to enforce does not hold.
- Repos that have type errors are shipping to `live-defi-rollout` without any CI gate.
- Difficult to audit scope — need to run `basedpyright $SOURCE_DIR/` in every repo to find affected repos.

## Recommended decision

**Fix in base-service.sh:**

```bash
# OLD (broken):
wait $BP_PID || true
PYRIGHT_EXIT=$?

# FIX (captures actual exit code without triggering set -e):
wait $BP_PID; PYRIGHT_EXIT=$?; true
```

With `set -e`, `;` does NOT protect against non-zero intermediate commands — use this instead:

```bash
{ wait $BP_PID; PYRIGHT_EXIT=$?; } || true
```

The `|| true` applies to the block; `PYRIGHT_EXIT=$?` always succeeds (assignment exit = 0), so the `|| true` is no-op
but the inner `PYRIGHT_EXIT=$?` correctly captured the wait exit code.

**Pre-fix sweep required:** Before landing the fix, scan all 26 active Python repos for basedpyright errors
(`timeout 120 .venv/bin/basedpyright $SOURCE_DIR/`) and fix each one. Otherwise the QG fix will immediately break all
repos with pre-existing errors.

**Scope owned by slot 2** (workspace-wide audit). Batch-live-reconciliation already cleaned (983e4ad) — 0 errors after
fix.

**Priority:** P1 — affects type safety guarantee for all 26 active repos.
