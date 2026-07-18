# Rehost overlays

Recorded human judgement for workflows whose self-hosted flip changed more than `runs-on:`.

`hosted_form.py` reverts the flip mechanically, which is enough for most workflows. It is **not** enough when the flip
also deleted work the glue image already does, or added a workaround that only makes sense on a shared, non-root,
long-lived host. For those, the judgement lives here and is re-applied to **current live** on every `snapshot`, so the
baseline tracks the live file instead of freezing at the flip.

| file                   | meaning                                                           |
| ---------------------- | ----------------------------------------------------------------- |
| `<workflow>.yml.patch` | apply this diff to `hosted_form(live)`                            |
| `<workflow>.yml.ok`    | reviewed — `hosted_form(live)` is already a valid hosted baseline |

An overlay that stops applying is a **loud** failure: the workflow drops back to `history-logic-stale`, `verify` reports
it, and `restore` refuses it without `--force`. That is the signal live has moved far enough to need re-reviewing — not
something to force past.

## Current overlays (reconciled 2026-07-18)

| workflow                                   | why                                                                                                                                                                                                                                                       |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cassette-drift-check`                     | flip deleted `Set up Python` (3.13) + `Install uv`; hosted needs both. Also drops the now-false "No actions/setup-python" rationale.                                                                                                                      |
| `removed-symbols-workspace-sweep`          | flip deleted `Set up Python` (3.12) + `Install checker dependency (PyYAML)`.                                                                                                                                                                              |
| `rules-alignment-agent`                    | glue runs npm as a non-root user, so a later commit set `NPM_CONFIG_PREFIX` to a user-writable dir. On hosted the runner **can** write the default prefix, so this reverts to the plain `npm install -g` that `plan-health-agent.yml` already uses there. |
| `ldr-docs-gate`                            | born self-hosted (2026-07-17), no hosted ancestor. Its checker is stdlib-only but the repo pins `requires-python = ">=3.13,<3.14"`, which the glue slot venv supplies and `ubuntu-latest` does not.                                                       |
| `deterministic-promotion-conflict-resolve` | `.ok` — the flip's only non-`runs-on` change was a prettier re-wrap.                                                                                                                                                                                      |
| `escalate-to-orchestrator`                 | `.ok` — same, a prettier reflow of `description:`/`options:`.                                                                                                                                                                                             |
| `workspace-quickmerge-validation`          | `.ok` — `Install jq` became a guarded `Ensure jq` that installs only when missing; portable, and the file documents it as hosted-safe.                                                                                                                    |
