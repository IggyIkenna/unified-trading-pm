---
title: "✅ RESOLVED 2026-05-09 — PM validate_plan_links.py mds_dir AttributeError fixed (verified 2026-05-09 audit)"
created: 2026-05-08
resolved: 2026-05-09
author: agent-5-tab5-orchestrator
status: resolved
source:
  - unified-trading-pm/scripts/validators/validate_plan_links.py:28 (now reads args.plans_dir correctly)
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

## ✅ RESOLUTION 2026-05-09

Per cluster 9 retry audit 2026-05-09: `validate_plan_links.py:24` now uses `args.plans_dir` (correct attribute name); no
`mds_dir` reference exists in the script. Step 6 PRODUCTION READINESS VALIDATORS no longer crashes with the
AttributeError. Issue ready for archive.

---

# Original issue (resolved — kept for archaeology)

# PM validate_plan_links.py crashes during production-readiness QG step

> **Severity**: P2 — workspace-wide QG infrastructure issue. Every service repo's `bash scripts/quality-gates.sh` Step 6
> "PRODUCTION READINESS VALIDATORS" fails on this AttributeError. **Blast radius**: every service running QG on
> `live-defi-rollout`. **Suggested owner**: PM scripts maintainer.

## What I found

Running alerting-service QG (and presumably every other service):

```
[0;34m── [6/6] PRODUCTION READINESS VALIDATORS ──[0m
OK: All checklists have phase_9_deployable_enhancements (items 38-41)
OK: workspace-manifest.json valid (schema + topological)
Traceback (most recent call last):
  File "unified-trading-pm/scripts/validators/validate_plan_links.py", line 72, in <module>
    sys.exit(main())
  File "unified-trading-pm/scripts/validators/validate_plan_links.py", line 28, in main
    plans_dir: Path = cast(Path, args.mds_dir).resolve()
                                 ^^^^^^^^^^^^
AttributeError: 'Namespace' object has no attribute 'mds_dir'
```

The `args.mds_dir` reference at line 28 is broken — argparse never populates that attribute under whatever flag set the
validator was invoked with.

## Why it matters

- Every service's `bash scripts/quality-gates.sh` Step 6 fails with this exact traceback. Local QG signal is therefore
  unreliable (every push needs a manual "is this MY failure?" check).
- Per CLAUDE.md "QG failure attribution" rule, agents are continuing to push past it (alerting-service, UAC, others this
  cycle). This is correct behaviour but pollutes the failure-mode signal.
- Likely a recent rename of `mds_dir` → some other arg name (`md_dir`?) without updating call-sites.

## Recommended decision

PM script maintainer fixes the AttributeError + lifts the workspace-wide QG-attribution exemption (per CLAUDE.md
"Temporary exception" 2026-05-07 → ~2026-05-09 window). Quick fix likely:

```python
# Either rename the argument or fix the access:
plans_dir: Path = cast(Path, args.md_dir).resolve()  # if rename happened
# OR
parser.add_argument("--mds-dir", ...)  # if the flag is missing
```

`grep -rE "args\.(mds_dir|md_dir)" unified-trading-pm/scripts/` will surface the right resolution.
