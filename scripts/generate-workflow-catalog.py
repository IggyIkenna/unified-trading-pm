#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
"""Generate the CI/CD workflow catalog (the drill-down index) from the live `.github/workflows/*.yml`.

Writes `docs/repo-management/CICD-WORKFLOW-CATALOG.md` — one row per workflow:
`Workflow | Stage | Triggers | Concurrency | Mutates | Fires next`.

It is GENERATED FROM THE YAML so it cannot rot: re-run after any workflow add/trigger/concurrency change.
The top-down picture is the SVG (`generate-cicd-diagram.py`); this is the per-workflow drill-down beneath it.

Regenerate: python3 scripts/generate-workflow-catalog.py
SSOT: codex/08-workflows/ci-cd-flow.md § "Workflow catalog".
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import cast

import yaml  # fail-loud: pyyaml is a PM dev dep (same as generate-cicd-diagram.py); no fallback shim

# ── Stage classification (the 5 functional clusters). A workflow absent here renders as
# "unclassified" — a deliberate loud signal that a new workflow needs a home in this map. ──
STAGE_BY_WORKFLOW: dict[str, str] = {
    # Promotion & image build (commit→LDR→staging→main→image)
    "ldr-to-staging-promote": "promotion",
    "ldr-to-main-promote": "promotion",
    "staging-to-main": "promotion",
    "main-backmerge-to-ldr": "promotion",
    "staging-conflict-ldr-main-fallback": "promotion",
    "deterministic-promotion-conflict-resolve": "promotion",
    "promotion-lag-monitor": "promotion",
    "cloud-build-router": "promotion",
    "cloud-build-failure-watcher": "promotion",
    "publish-package": "promotion",
    # Quality gates, breaking detection & SIT
    "quality-gates-v2": "quality-gates",
    "python-quality-gates-v2": "quality-gates",
    "cascade-qg-ordering": "quality-gates",
    "sit-gate": "quality-gates",
    "sit-debounce-trigger": "quality-gates",
    "sit-starvation-detector": "quality-gates",
    "sit-unlock": "quality-gates",
    "readiness-verifier": "quality-gates",
    "workspace-quickmerge-validation": "quality-gates",
    "change-freeze-check": "quality-gates",
    "freeze-deferred-build-replay": "quality-gates",
    # Release machinery (semver / version / manifest / templates)
    "semver-agent": "release",
    "update-repo-version": "release",
    "request-major-bump": "release",
    "major-bump-issue-handler": "release",
    "reconcile-release-tags": "release",
    "supersede-stale-dep-update-prs": "release",
    "rollout-action-ref": "release",
    "hotfix-mode": "release",
    # ci_status SSOT, watchers & health
    "ci-status-update": "ci-status",
    "ci-status-reconciler": "ci-status",
    "ci-failure-watcher": "ci-status",
    "ldr-ci-monitor": "ci-status",
    "persist-cicd-event": "ci-status",
    "secret-health-check": "ci-status",
    "cassette-drift-check": "ci-status",
    "ruleset-drift-alert": "ci-status",
    "removed-symbols-workspace-sweep": "ci-status",
    # Agents, orchestration & alerts
    "escalate-to-orchestrator": "agents",
    "conflict-resolution-agent": "agents",
    "conflict-resolution-merged": "agents",
    "rules-alignment-agent": "agents",
    "plan-health-agent": "agents",
    "plan-notification": "agents",
    "agent-audit": "agents",
    "overnight-agent-orchestrator": "agents",
    "overnight-dead-man-switch": "agents",
    "fix-approval-timeout": "agents",
    "notify-slack": "agents",
    "build-smoke-all-repos": "agents",
    "cold-storage-cleanup": "agents",
}

STAGE_ORDER: list[str] = ["promotion", "quality-gates", "release", "ci-status", "agents", "unclassified"]
STAGE_TITLE: dict[str, str] = {
    "promotion": "Promotion & image build — commit → LDR → staging → main → image",
    "quality-gates": "Quality gates, breaking detection & SIT",
    "release": "Release machinery — semver / version / manifest / templates",
    "ci-status": "ci_status SSOT, watchers & health",
    "agents": "Agents, orchestration & alerts",
    "unclassified": "Unclassified — needs a stage in STAGE_BY_WORKFLOW",
}


def _load_yaml(path: Path) -> dict[str, object]:
    """Load a workflow yml. GHA's top-level `on:` is parsed by PyYAML(1.1) as the boolean key True."""
    data = cast("object", yaml.safe_load(path.read_text()))
    return cast("dict[str, object]", data) if isinstance(data, dict) else {}


def _on_block(data: dict[str, object]) -> dict[str, object]:
    """Return the `on:` mapping, tolerating the YAML-1.1 `on`→True key coercion."""
    data_any = cast("dict[object, object]", data)
    raw = data_any.get("on", data_any.get(True, {}))
    if isinstance(raw, dict):
        return cast("dict[str, object]", raw)
    if isinstance(raw, list):  # `on: [push, pull_request]`
        return {cast("str", k): {} for k in cast("list[object]", raw)}
    if isinstance(raw, str):  # `on: push`
        return {raw: {}}
    return {}


def _as_list(v: object) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in cast("list[object]", v)]
    if v is None:
        return []
    return [str(v)]


def summarize_triggers(on: dict[str, object]) -> str:
    """Human-readable trigger summary in a stable order."""
    parts: list[str] = []
    trigger_order = (
        "schedule", "push", "pull_request", "workflow_run",
        "repository_dispatch", "workflow_call", "workflow_dispatch", "issue_comment",
    )
    for key in trigger_order:
        if key not in on:
            continue
        body = on[key]
        if key == "schedule":
            body_list = cast("list[object]", body) if isinstance(body, list) else []
            crons: list[str] = []
            for entry in body_list:
                cron = cast("dict[str, object]", entry).get("cron")
                if cron is not None:
                    crons.append(str(cron))
            parts.append("schedule(" + ", ".join(crons) + ")")
        elif key in ("push", "pull_request"):
            br = _as_list(cast("dict[str, object]", body).get("branches")) if isinstance(body, dict) else []
            label = "push" if key == "push" else "PR"
            parts.append(f"{label}[{','.join(br)}]" if br else label)
        elif key == "workflow_run":
            d = cast("dict[str, object]", body) if isinstance(body, dict) else {}
            wfs = ",".join(_as_list(d.get("workflows")))
            br = ",".join(_as_list(d.get("branches")))
            parts.append(f"after:{wfs}" + (f"[{br}]" if br else ""))
        elif key == "repository_dispatch":
            types = _as_list(cast("dict[str, object]", body).get("types")) if isinstance(body, dict) else []
            parts.append("dispatch:" + ",".join(types) if types else "dispatch")
        elif key == "workflow_call":
            parts.append("callable")
        elif key == "workflow_dispatch":
            parts.append("manual")
        elif key == "issue_comment":
            parts.append("issue_comment")
    return " · ".join(parts) if parts else "—"


def summarize_concurrency(data: dict[str, object]) -> str:
    conc = data.get("concurrency")
    if isinstance(conc, str):
        return f"`{conc}`"
    if isinstance(conc, dict):
        d = cast("dict[str, object]", conc)
        group = str(d.get("group", "?"))
        cancel = d.get("cancel-in-progress", False)
        # Normalise ${{ github.workflow }}-${{ github.ref }} → <workflow>-<ref> for readability
        group = re.sub(r"\$\{\{\s*github\.workflow\s*\}\}", "<wf>", group)
        group = re.sub(r"\$\{\{\s*github\.ref\s*\}\}", "<ref>", group)
        group = re.sub(r"\$\{\{[^}]+\}\}", "<var>", group)
        flag = " cancel" if cancel is True else ""
        return f"`{group}`{flag}"
    return "—"


def detect_mutations(text: str) -> str:
    """Coarse but mechanical: what does this workflow change? Grepped from the run-step bodies."""
    flags: list[str] = []
    pushes_main = bool(re.search(r"git push[^\n]*\bmain\b", text)) or "HEAD:main" in text
    if "workspace-manifest.json" in text and ("git commit" in text or "git push" in text):
        flags.append("manifest→main" if pushes_main else "manifest")
    elif pushes_main:
        flags.append("→main")
    if re.search(r"push[^\n]*live-defi-rollout", text):
        flags.append("→LDR")
    if "gh pr create" in text or "create_pr" in text:
        flags.append("opens-PR")
    if "gh pr merge" in text:
        flags.append("merges-PR")
    if "ci_status_store" in text or "firestore" in text.lower():
        flags.append("Firestore")
    if re.search(r"""git tag\s+["'$v]""", text) or re.search(r"git push[^\n]*--tags", text):
        flags.append("tags")
    if "notify-slack" in text or "SLACK_" in text:
        flags.append("Slack")
    return ", ".join(flags) if flags else "read-only"


def detect_fires_next(text: str, listeners: dict[str, list[str]], name: str) -> str:
    """Downstream workflows from `gh workflow run`, `uses:` reusable calls, and repository_dispatch event_type."""
    nxt: set[str] = set()
    for m in re.finditer(r"gh workflow run\s+([A-Za-z0-9._-]+\.yml)", text):
        nxt.add(m.group(1).removesuffix(".yml"))
    for m in re.finditer(r"uses:\s*\./\.github/workflows/([A-Za-z0-9._-]+\.yml)", text):
        nxt.add(m.group(1).removesuffix(".yml"))
    # Tolerate `event_type=x`, `event-type: x`, and the escaped-JSON-in-shell form `\"event_type\":\"x\"`.
    for m in re.finditer(r"""event[_-]type\\?["']?\s*[=:]\s*\\?["']?([a-z][a-z0-9-]+)""", text):
        for wf in listeners.get(m.group(1), []):
            if wf != name:  # a workflow that both sends and listens for an event is not firing itself
                nxt.add(f"{wf}*")  # * = via repository_dispatch
    nxt.discard(name)  # self-reference (usage doc / comment) is not a downstream fire
    nxt.discard("notify-slack")  # ubiquitous reusable alert — noise in every row
    nxt.discard("persist-cicd-event")  # ubiquitous reusable event sink
    return ", ".join(sorted(nxt)) if nxt else "—"


def build_dispatch_listeners(workflows: dict[str, dict[str, object]]) -> dict[str, list[str]]:
    """event-type → [workflows that listen for it via on.repository_dispatch.types]."""
    listeners: dict[str, list[str]] = {}
    for name, data in workflows.items():
        rd = _on_block(data).get("repository_dispatch")
        if isinstance(rd, dict):
            for t in _as_list(cast("dict[str, object]", rd).get("types")):
                listeners.setdefault(t, []).append(name)
    return listeners


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    wf_dir = repo_root / ".github" / "workflows"
    out_path = repo_root / "docs" / "repo-management" / "CICD-WORKFLOW-CATALOG.md"

    paths = sorted(wf_dir.glob("*.yml"))
    if not paths:
        print(f"ERROR: no workflows under {wf_dir}", file=sys.stderr)
        sys.exit(1)

    raw_text: dict[str, str] = {p.stem: p.read_text() for p in paths}
    parsed: dict[str, dict[str, object]] = {p.stem: _load_yaml(p) for p in paths}
    listeners = build_dispatch_listeners(parsed)

    rows_by_stage: dict[str, list[str]] = {s: [] for s in STAGE_ORDER}
    for name in sorted(parsed):
        data = parsed[name]
        stage = STAGE_BY_WORKFLOW.get(name, "unclassified")
        triggers = summarize_triggers(_on_block(data))
        conc = summarize_concurrency(data)
        mutates = detect_mutations(raw_text[name])
        fires = detect_fires_next(raw_text[name], listeners, name)
        rows_by_stage[stage].append(f"| `{name}` | {triggers} | {conc} | {mutates} | {fires} |")

    lines: list[str] = [
        "<!-- GENERATED by scripts/generate-workflow-catalog.py — do not hand-edit; regenerate after changes. -->",
        "",
        "# CI/CD Workflow Catalog (auto-generated drill-down)",
        "",
        f"**{len(paths)} workflows** in `.github/workflows/`, grouped by pipeline stage. Top-down picture:",
        "`docs/repo-management/CI-CD-PIPELINE.svg`; narrative: `codex/08-workflows/ci-cd-flow.md`. This is the",
        "per-workflow index beneath them — regenerate with `python3 scripts/generate-workflow-catalog.py`.",
        "",
        "Columns: **Triggers** (schedule / push / PR / `after:` run / `dispatch:` event / callable / manual) ·",
        "**Concurrency** group (`cancel` = cancel-in-progress) · **Mutates** (coarse, grepped) · **Fires next**",
        "(`*` = via repository_dispatch; `notify-slack` / `persist-cicd-event` reusable calls elided).",
        "",
    ]
    for stage in STAGE_ORDER:
        rows = rows_by_stage[stage]
        if not rows:
            continue
        lines.append(f"## {STAGE_TITLE[stage]} ({len(rows)})")
        lines.append("")
        lines.append("| Workflow | Triggers | Concurrency | Mutates | Fires next |")
        lines.append("| -------- | -------- | ----------- | ------- | ---------- |")
        lines.extend(rows)
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n")
    counts = {s: len(rows_by_stage[s]) for s in STAGE_ORDER if rows_by_stage[s]}
    print(f"Wrote {out_path.relative_to(repo_root)} — {len(paths)} workflows: {counts}")
    if rows_by_stage["unclassified"]:
        names = [r.split("`")[1] for r in rows_by_stage["unclassified"]]
        print(f"⚠️  unclassified (add to STAGE_BY_WORKFLOW): {names}", file=sys.stderr)


if __name__ == "__main__":
    main()
