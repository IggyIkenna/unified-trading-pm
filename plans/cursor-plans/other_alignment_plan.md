# PM–Codex–Code Alignment: Version Tracking Design

**Status:** Proposal — Under Team Review
**Author:** Architecture discussion (Mar 2026)
**Context:** 60-repo workspace, multi-agent delivery, high velocity

---

## Problem Statement

We work across three layers simultaneously:

```
PM (plans, epics, tasks)
  ↓ becomes
Codex (specs, patterns, architecture docs)
  ↓ drives
Code (services, libraries, interfaces)
```

At high velocity with multiple agents (Cursor, Claude Code, etc.) working in parallel, these three layers drift apart. A plan references a spec that has been superseded. An agent writes code against a codex doc that was updated last week. A new engineer reads a doc that no longer matches what the code does.

**The core question:** How do we make drift detectable and enforceable — like a failing unit test — rather than invisible until something breaks?

---

## Two Approaches Evaluated

### Approach A: Central Manifest as Source of Truth (proposed initially)

All version state lives in `workspace-manifest.json`. A post-merge GitHub Action syncs repo versions into the manifest after every merge. A drift checker script compares manifest versions against codex doc headers.

**How it works:**
- `workspace-manifest.json` holds `versions.{repo}` = current `pyproject.toml` version
- Codex docs carry a header asserting `service_version: "0.3.1"` (read from manifest)
- After every merge to main in any repo, a GitHub Action fires → syncs manifest → regenerates DAG
- A pre-agent gate checks: `manifest[repo] == doc.service_version` before any task starts

**Pros:**
- Single version state location — no distributed state to go out of sync
- Codex docs only need one field updated per repo bump (not per file)
- Manifest already exists and is partially wired to CI
- Low agent overhead: agents update one manifest entry, not N file headers

**Cons:**
- Requires cross-repo GitHub Action plumbing (post-merge webhook from each repo → PM repo)
- Drift check requires reading `workspace-manifest.json` (cross-repo I/O)
- Coarse granularity: repo-level only, not doc-level or file-level
- Does not record *which specific spec* a code file was built against
- An agent can complete code without ever touching the manifest → undetected drift

---

### Approach B: Per-File Header Provenance (proposed by team)

Every file that changes as part of a task carries a header recording which codex document and version it was built against. The codex doc itself carries its own `doc_version` independently of the repo/service version.

**How it works:**

**Codex doc** (the spec):
```markdown
---
doc_version: "1.2"
codex_version: "0.1.0"
last_modified: "2026-03-04"
describes: market-data-processing-service
status: stable
---
```

**Code file** (the implementation):
```python
# codex-ref: 02-data/batch/per-service/market-data-processing-service.md
# doc-version: 1.2
# codex-version: 0.1.0
# last-modified: 2026-03-04
```

**PM task/plan** (the work order):
```yaml
spec_doc: 02-data/batch/per-service/market-data-processing-service.md
spec_doc_version: "1.2"
codex_version: "0.1.0"
created: "2026-03-04"
```

When the codex doc is updated (spec changes), `doc_version` bumps from `1.2` → `1.3`. Any code file still carrying `doc-version: 1.2` is now detectably stale — it references a superseded spec.

**`doc_version` is independent of the service/repo version.** The module-level repo version (in `pyproject.toml`) only bumps when code ships. The `doc_version` bumps whenever the specification changes — these are different events.

**Pros:**
- Precise provenance: every file records exactly which spec version it was built against
- Drift check is purely local (compare two files, no manifest lookup)
- Makes the task contract explicit: agent is given a doc version, must deliver matching code
- Unit test is trivially obvious: `code.doc_version == spec.doc_version` → pass/fail
- Works for any file type: `.py`, `.md`, `.yaml`, `.sh`, `.ts`
- No cross-repo infrastructure required — check runs anywhere, even offline

**Cons:**
- Higher agent discipline required: every file edit must include header update
- Agents frequently forget to update headers → need enforcement in quality gates
- At scale (thousands of files), headers add noise to file diffs
- `doc_version` bumping is manual — requires agents to increment it correctly
- Code files do NOT need to carry headers for files unrelated to any spec (scoping must be clear)

---

## Recommended: Combine Both (Layered Approach)

Neither approach alone covers all cases. The winning design uses both at different granularities:

| Layer | Versioning mechanism | What it tracks |
|---|---|---|
| Repo/service | `pyproject.toml` version → `workspace-manifest.json` | "This service shipped version X" |
| Codex doc | YAML front-matter `doc_version` | "This spec is at revision Y" |
| Code file | `# codex-ref:` comment header | "This file implements spec doc Y" |
| PM plan | YAML header `spec_doc_version` | "This task was created against spec Y" |

**Enforcement checks (all are pass/fail):**

| Check | Compares | Blocks |
|---|---|---|
| `header_present` | File has codex-ref header | Merging code without provenance |
| `doc_version_match` | `code.doc_version == spec.doc_version` | Code built against stale spec |
| `codex_version_match` | `code.codex_version == codex pyproject.toml version` | Code referencing old codex epoch |
| `doc_version_monotonic` | `new_doc_version > old_doc_version` | Version going backwards |
| `manifest_synced` | `manifest[repo] == pyproject.toml version` | Manifest drift from actual code |
| `plan_spec_current` | `plan.spec_doc_version == spec.doc_version` | Agent starting on stale plan |

All checks are string/semver comparisons. No network calls. Complete check runs in under 2 seconds.

---

## Scope: Which Files Carry Headers?

**Yes — carry `codex-ref` header:**
- Any code file changed as part of a task that was created from a codex spec doc
- All codex spec docs (service-specific: `per-service/`, `per-service-live/`, etc.)
- PM task/plan files in `plans/ai/`

**No — do not carry `codex-ref` header:**
- Generic utility files not tied to a specific spec (e.g. `utils/date_utils.py`)
- `__init__.py`, `conftest.py`, test fixtures
- Infrastructure files (`Dockerfile`, `cloudbuild.yaml`, `pyproject.toml`)
- Codex cross-cutting pattern docs (e.g. `06-coding-standards/quality-gates.md`) — these describe workspace-wide standards, not a specific service

The rule: **if the file exists because a specific codex spec says it should**, it carries a header. If it's infrastructure or a workspace-wide pattern file, it doesn't.

---

## `doc_version` Bumping Rules

| Event | Action |
|---|---|
| Spec doc content changes (schema, API, pattern) | Bump `doc_version` minor: `1.2` → `1.3` |
| Spec doc restructured significantly or rewritten | Bump `doc_version` major: `1.2` → `2.0` |
| Formatting/typo fix only | No bump |
| Code file updated to implement latest spec | Update `doc-version` in header to match current spec |
| `codex_version` bumps (whole codex ships a release) | Update `codex-version` in header |

`doc_version` is managed by the agent doing the edit — it is **not** automated. This is intentional: the version is a human-meaningful signal, not a git artifact.

---

## Implementation Phases

### Phase 1: Cursor rule + doc headers (1–2 days, fully agent-doable)
- Add cursor rule: `codex-ref-header.mdc` — enforces header on all spec-driven file changes
- Add YAML front-matter to all codex per-service docs (lobster workflow, one agent pass ~200 docs)
- Add `doc_version: "1.0"` and `codex_version: "0.1.0"` as starting baseline

### Phase 2: Enforcement script (1 day)
- Write `scripts/validation/check-alignment-drift.py` (~100 lines Python)
- Wire into `unified-trading-codex/scripts/quality-gates.sh`
- Wire as Step 0 of `plans/tasks/cursor/TEMPLATE.md`

### Phase 3: Manifest sync (1–2 days, requires GitHub setup)
- GitHub Action in each repo fires `repository_dispatch` to `unified-trading-pm` after version bump
- `scripts/manifest/sync-versions-from-repos.py` reads all `pyproject.toml` files → updates manifest
- Adds `manifest_synced` check to per-repo quality-gates

### Phase 4: PM plan headers (ongoing, integrated into task creation)
- Update `TEMPLATE.md` to require `spec_doc` and `spec_doc_version` in every new plan
- Add `plan_spec_current` check to pre-agent gate

---

## Open Questions for Team Discussion

1. **`doc_version` format:** Semantic (`1.2`) vs. date-based (`2026-03-04`) vs. integer (`42`)? Semantic is most expressive but requires agent discipline. Date-based is automatic but loses ordering when multiple edits happen in a day.

2. **Header in code files — comment vs. docstring?** A module-level comment (`# codex-ref: ...`) is invisible to runtime but noisy in diffs. A module docstring (`"""codex-ref: ..."""`) is cleaner but changes the module's public interface. A dedicated `__codex__.py` per package avoids per-file headers entirely.

3. **Enforcement strictness:** Should `doc_version_match` be a hard blocker or a warning in CI? Blocking is safer but will cause friction when specs are updated faster than code. Warning + a staleness threshold (e.g., allow 1 minor version behind) may be more practical.

4. **Cross-cutting pattern docs:** How do files that implement workspace-wide patterns (not service-specific specs) get tracked? Should they reference the `06-coding-standards/` section version instead?

5. **Retroactive coverage:** Do we add headers to all existing files, or only files touched going forward? Full retroactive coverage is a one-time lobster workflow (~2 hours). Partial coverage means the check can only run on files that have headers, reducing enforcement completeness initially.

---

## Summary

| | Approach A (Manifest) | Approach B (Headers) | Combined |
|---|---|---|---|
| Granularity | Repo-level | File-level | Both |
| Agent overhead | Low | Medium | Medium |
| Infrastructure needed | GitHub Actions webhook | Cursor rule + quality gate | Both |
| Drift detection speed | Minutes (post-merge) | Immediate (pre-commit) | Immediate |
| Cross-repo I/O required | Yes | No | Minimal |
| Testability | Good | Excellent | Excellent |
| Long-term maintenance | Low | Medium | Medium |

The combined approach gives the most complete coverage. Phase 1 + Phase 2 (headers + enforcement script) deliver 80% of the value and can ship in 2–3 days. Phase 3 (manifest sync) adds the repo-level layer on top.

---

*For questions or to propose changes to this design, update this doc and bump `doc_version`.*
