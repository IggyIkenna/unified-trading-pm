#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Standalone checker — Cloud Build TEMPLATE-vs-CONSUMER drift ratchet.

``scripts/propagation/rollout-cloudbuild.py`` overwrites every consumer repo's
``cloudbuild.yaml`` from ``configs/cloudbuild-*-template.yaml``. The template
was measured 2026-07-20 to be BEHIND all 19 consumers — a real rollout would
have silently DROPPED two production fixes fleet-wide (authenticated
``--unshallow`` fetch, the ``0.0.0.dev0`` VERSION fallback). The template was
forward-ported and the rollout tool now REFUSES to write content it would
drop (``find_dropped_markers`` in ``rollout-cloudbuild.py``, shipped
2026-07-28) — but nothing DETECTS the drift itself, so the same trap reopens
the moment a repo fixes something the template does not learn.

This checker renders every ``configs/cloudbuild-*-template.yaml`` for every
consumer that maps to it (reusing ``rollout-cloudbuild.py``'s OWN
``generate_cloudbuild()``/``find_dropped_markers()`` — the single source of
truth for repo_type -> template substitution and content-drop detection; this
checker never re-implements Cloud Build template rendering) and diffs the
render against the consumer's COMMITTED ``cloudbuild.yaml``. "Drift" here
means content the CONSUMER carries that the TEMPLATE does not (a whole step,
a ``secretEnv``/``availableSecrets`` entry, or a step-arg/script line) — the
exact shape of the 2026-07-20 near-miss.

Covers ALL FIVE templates (``-service-``, ``-api-``, ``-ui-``, ``-infra-``,
``-sit-``) over every consumer repo `rollout-cloudbuild.py --apply` (default,
no ``--include-library``) would actually touch — the drift checker's scope is
deliberately identical to the rollout tool's real write-scope, since that is
the actual blast radius. ``library``-type repos are excluded (they carry
hand-maintained custom cloudbuild, never template-rendered, matching the
rollout tool's own default).

Shape — **baseline ratchet** (NOT zero-tolerance from day 1; per-repo drift is
often INTENTIONAL — e.g. deployment-api's ``vendor-deps``/``deploy``/
``redeploy-monitor-jobs`` steps — and must be baselined, not "fixed"):

  1. Load ``cloudbuild_template_drift_baseline.yaml`` — a per-repo count of
     currently-known drift markers (content the consumer carries the
     template's render does not).
  2. Render + diff every consumer against its mapped template.
  3. count <= baseline -> OK (WARN when strictly below, so the operator
     ratchets the baseline DOWN). count > baseline -> ERROR (exit 1): the
     template fell FURTHER behind this repo — a NEW divergence landed.

The baseline ONLY shrinks: re-run with ``--update-baseline`` after
forward-porting a fix into the template (or reconciling the consumer).

A repo whose render (or live file) cannot be parsed as YAML is an
unconditional FAIL, never baseline-able — the comparison itself is
unavailable, and treating that as "clean" would be the "None means it's
fine" mistake the rollout tool's own guard was written to avoid.

Wired into quality gates at TWO points, deliberately:

  * ``unified-trading-pm/scripts/quality-gates.sh`` runs it FLEET-WIDE (no
    ``--repo``), which catches the other direction — a TEMPLATE edit in PM that
    leaves consumers behind.
  * ``quality-gates-base/base-service.sh`` STEP 5.108 and ``base-ui.sh``
    ``[5.108]`` run it scoped to the CONSUMER (``--repo <this repo>``), so a
    cloudbuild.yaml edit fails in the repo that introduced it.

The consumer-scoped half was added 2026-08-12 after the PM-only wiring let a
consumer land drift with a green gate and surface it as a fleet-wide PM commit
block on an unrelated agent's machine, twice in two days. SSOT:
``/plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md``.
(This docstring previously said "NOT wired into quality-gates.sh ... run
standalone until that wiring is decided" — stale since the PM wiring landed, and
it is why the consumer-side gap read as an open design question rather than a
gap.)

Usage::

    # fleet-wide sweep (default workspace root = sibling of unified-trading-pm):
    python check_cloudbuild_template_drift.py

    # single consumer:
    python check_cloudbuild_template_drift.py --repo deployment-api

    # ratchet the baseline DOWN after forward-porting a fix into the template:
    python check_cloudbuild_template_drift.py --update-baseline

Exit codes: 0 = clean / at-or-below baseline; 1 = over baseline or a repo is
unparseable; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Final

import yaml

# ── Constants ────────────────────────────────────────────────────────────────

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
ROLLOUT_SCRIPT_PATH: Final[Path] = SCRIPT_DIR.parent / "propagation" / "rollout-cloudbuild.py"


# ── Rollout-tool loading (reuse, never re-implement, template rendering) ─────


def load_rollout_module() -> ModuleType:
    """Load ``rollout-cloudbuild.py`` by file path (it is not a package).

    Reusing its ``generate_cloudbuild()`` (repo_type -> template + real
    substitutions) and ``find_dropped_markers()`` (the parsed-YAML,
    marker-based content diff) keeps template-rendering and drop-detection in
    exactly ONE place. Raises LOUDLY if the module cannot be loaded — a drift
    check built on stale/re-implemented rendering logic is worse than no
    check at all.
    """
    spec = importlib.util.spec_from_file_location("rollout_cloudbuild_for_drift_check", ROLLOUT_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load rollout-cloudbuild module at {ROLLOUT_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ── Baseline ─────────────────────────────────────────────────────────────────


def _baseline_path() -> Path:
    return Path(__file__).resolve().parent / "cloudbuild_template_drift_baseline.yaml"


@dataclass(frozen=True)
class Baseline:
    """Per-repo allowed counts of template-vs-consumer drift markers."""

    counts: dict[str, int] = field(default_factory=dict)
    note: str = ""

    def allowed(self, repo: str) -> int:
        return int(self.counts.get(repo, 0))


def load_baseline(path: Path | None = None) -> Baseline:
    baseline_file = path if path is not None else _baseline_path()
    if not baseline_file.exists():
        return Baseline()
    raw = yaml.safe_load(baseline_file.read_text(encoding="utf-8")) or {}
    repos_raw = raw.get("repos") or {}
    counts: dict[str, int] = {}
    for repo, val in repos_raw.items():
        if isinstance(val, dict):
            counts[str(repo)] = int(val.get("count", 0))
        else:
            counts[str(repo)] = int(val)
    return Baseline(counts=counts, note=str(raw.get("note") or ""))


def write_baseline(counts: dict[str, int], existing: Baseline, path: Path | None = None) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means the template fell further behind;
    forward-port the fix, don't bake the gap in)."""
    baseline_file = path if path is not None else _baseline_path()
    merged: dict[str, dict[str, int]] = {}
    all_repos = set(counts) | set(existing.counts)
    for repo in sorted(all_repos):
        if repo not in counts:
            # Not scanned this run (scoped --repo) — carry the existing row
            # forward verbatim rather than zeroing it (same defect class as
            # check_ruff_rule_ratchet, incident 2026-06-10).
            merged[repo] = {"count": existing.allowed(repo)}
            continue
        observed = int(counts[repo])
        prior = existing.allowed(repo)
        merged[repo] = {"count": min(observed, prior) if repo in existing.counts else observed}
    header = (
        "# Baseline for check_cloudbuild_template_drift.py.\n"
        "#\n"
        "# This is a SHRINKING ratchet. `repos[<repo>].count` is the number of\n"
        "# content markers (whole steps, secretEnv/availableSecrets entries, step\n"
        "# args/script lines) that repo's committed cloudbuild.yaml carries which\n"
        "# its mapped configs/cloudbuild-*-template.yaml render does NOT. A repo\n"
        "# whose live count EXCEEDS its baseline fails — the template fell FURTHER\n"
        "# behind this repo (a new divergence landed).\n"
        "#\n"
        "# LOWER a count (re-run `--update-baseline`) the moment the template is\n"
        "# forward-ported or the consumer is reconciled. NEVER raise a count.\n"
        "# Repos not listed default to count=0. Intentional per-repo drift (e.g.\n"
        "# deployment-api's vendor-deps/deploy/redeploy-monitor-jobs steps) is\n"
        '# expected to live here PERMANENTLY, baselined rather than "fixed".\n'
        "#\n"
        "# SSOT: plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md\n"
        "# + plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md.\n"
    )
    body = yaml.safe_dump(
        {
            "note": existing.note or "Seeded 2026-07-28 — ci_satellite_ao_dispatch_batch1 [INFRA] P2.",
            "repos": merged,
        },
        sort_keys=True,
        default_flow_style=False,
        allow_unicode=True,
    )
    _ = baseline_file.write_text(header + body, encoding="utf-8")


# ── Scanning ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RepoDrift:
    repo: str
    template: str
    dropped: list[str]

    @property
    def count(self) -> int:
        return len(self.dropped)


def scan_drift(
    rollout_mod: ModuleType, workspace_root: Path, repo_filter: str | None = None
) -> tuple[dict[str, RepoDrift], list[str]]:
    """Render every template via the rollout tool's own mapping and diff each
    render against the matching consumer's committed cloudbuild.yaml.

    Mirrors ``rollout-cloudbuild.py`` ``main()``'s own default write-scope
    exactly (``SKIP_REPOS``, ``library`` excluded, a repo_type with no Docker
    cloudbuild renders ``None`` and is skipped) — this checker's consumer set
    is deliberately identical to what a default ``rollout-cloudbuild.py
    --apply`` run would actually touch, since that is the real blast radius.

    Returns ``(per-repo drift, unparseable-repo names)``. A repo with no
    on-disk ``cloudbuild.yaml`` (not yet onboarded to Cloud Build) is skipped
    entirely — not scored, not a failure.
    """
    manifest = rollout_mod.load_manifest()
    repos = rollout_mod.get_repos(manifest)
    if repo_filter:
        repos = {repo_filter: repos[repo_filter]} if repo_filter in repos else {}

    drift: dict[str, RepoDrift] = {}
    unparseable: list[str] = []
    for repo_name, repo_info in sorted(repos.items()):
        if repo_name in rollout_mod.SKIP_REPOS:
            continue
        if not isinstance(repo_info, dict):
            continue
        repo_type = repo_info.get("type") or ""
        if repo_type == "library":
            continue
        rendered = rollout_mod.generate_cloudbuild(
            repo_name, repo_info, deploy_via_dispatch=bool(repo_info.get("deploy_via_dispatch"))
        )
        if rendered is None:
            continue
        consumer_path = workspace_root / repo_name / "cloudbuild.yaml"
        if not consumer_path.exists():
            continue
        live_content = consumer_path.read_text(encoding="utf-8")
        template_name = rollout_mod.TYPE_TO_TEMPLATE.get(repo_type, "")
        dropped = rollout_mod.find_dropped_markers(live_content, rendered)
        if dropped is None:
            unparseable.append(repo_name)
            continue
        drift[repo_name] = RepoDrift(repo=repo_name, template=template_name, dropped=dropped)
    return drift, unparseable


# ── main ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Cloud Build template-vs-consumer drift ratchet. Runs fleet-wide in unified-trading-pm's "
            "quality-gates.sh, and scoped to a single consumer (--repo) in base-service.sh STEP 5.108 / base-ui.sh."
        )
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Defaults to the rollout tool's own WORKSPACE_ROOT (sibling of unified-trading-pm).",
    )
    parser.add_argument("--repo", default=None, help="Limit to a single consumer repo.")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Rewrite the baseline with the observed counts (clamped DOWN — never raised).",
    )
    parser.add_argument(
        "--baseline-file",
        type=Path,
        default=None,
        help="Override the baseline yaml path (unit tests only).",
    )
    parser.add_argument(
        "--configs-dir",
        type=Path,
        default=None,
        help="Override the templates dir (unit tests only).",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Override workspace-manifest.json path (unit tests only).",
    )
    args = parser.parse_args(argv)

    rollout_mod = load_rollout_module()
    if args.configs_dir is not None:
        rollout_mod.CONFIGS_DIR = args.configs_dir
    if args.manifest_path is not None:
        rollout_mod.MANIFEST_PATH = args.manifest_path
    workspace_root: Path = args.workspace_root.resolve() if args.workspace_root else rollout_mod.WORKSPACE_ROOT

    baseline = load_baseline(args.baseline_file)
    drift, unparseable = scan_drift(rollout_mod, workspace_root, args.repo)

    observed: dict[str, int] = {repo: rd.count for repo, rd in drift.items()}
    failures: list[str] = []
    info_lines: list[str] = []
    by_template: dict[str, list[str]] = {}
    for repo, rd in sorted(drift.items()):
        by_template.setdefault(rd.template, []).append(repo)
        allowed = baseline.allowed(repo)
        if rd.count > allowed:
            over = rd.dropped[allowed:] if allowed < len(rd.dropped) else rd.dropped
            sample = "; ".join(over[:10])
            # NOT a diff. The baseline stores only an integer per repo (`Baseline.counts`),
            # so this checker CANNOT know which markers are new — `over` is simply the tail
            # of the ordered marker list. Labelling it "New" was actively misleading: on
            # 2026-08-12 it surfaced `vendor-deps` (pre-existing intentional drift, named as
            # such in the baseline file's own header) as new, and a reader built a table
            # attributing the failure to two steps when only one had changed.
            failures.append(
                f"[FAIL] {repo} ({rd.template}): {rd.count} drift marker(s) > baseline {allowed}. "
                f"Marker(s) above the baseline COUNT — POSITIONAL, i.e. the last {len(over)} by file order, "
                f"NOT necessarily the ones that changed (the baseline stores a count, not marker identities; "
                f"to find what actually changed, diff this repo's cloudbuild.yaml against its last known-good "
                f"revision): {sample}" + (" ..." if len(over) > 10 else "")
            )
        elif rd.count < allowed:
            info_lines.append(
                f"[WARN] {repo} ({rd.template}): {rd.count} < baseline {allowed} — ratchet the baseline DOWN "
                f"(re-run `--update-baseline`)."
            )
        else:
            info_lines.append(f"[OK]   {repo} ({rd.template}): {rd.count} (== baseline)")

    for repo in unparseable:
        failures.append(f"[FAIL] {repo}: rendered template or live cloudbuild.yaml did not parse as YAML.")

    if args.update_baseline:
        write_baseline(observed, baseline, args.baseline_file)
        print(f"[check_cloudbuild_template_drift] baseline updated at {args.baseline_file or _baseline_path()}")
        for line in sorted(f"  {r}: {c}" for r, c in observed.items()):
            print(line)
        return 0

    print(f"[check_cloudbuild_template_drift] templates measured: {len(by_template)}")
    for template_name in sorted(by_template):
        repos_for_template = by_template[template_name]
        drifted = sum(1 for r in repos_for_template if drift[r].count > 0)
        print(f"  {template_name}: {drifted}/{len(repos_for_template)} consumer(s) carry undrained content")
    for line in info_lines:
        print(line)
    for line in failures:
        print(line, file=sys.stderr)
    if failures:
        # Both failure shapes start "[FAIL] <repo>" — the drift one continues " (<template>):",
        # the unparseable one continues ":". Strip either so the repo name is clean.
        offenders = ", ".join(sorted({line.split()[1].rstrip(":") for line in failures if len(line.split()) > 1}))
        print(
            f"\n-> THE OFFENDING CONTENT IS IN: {offenders}. If you are shipping unified-trading-pm, this is "
            "NOT your change: this checker is a post-gate in PM's quality-gates.sh, so a consumer repo's drift "
            "fails PM's gate, withholds the .qg_last_passed_sha sentinel, and blocks EVERY PM code ship on "
            "every host until it is drained. Fix it in the repo named above.\n"
            "-> What it means: that consumer's cloudbuild.yaml carries content its mapped template does not, so "
            "the next `rollout-cloudbuild.py --apply` on it would either be refused (would-drop-content guard) "
            "or, if the guard is ever bypassed, silently regress it.\n"
            "-> Remedy: forward-port the content into the template. `--update-baseline` is SHRINK-ONLY and will "
            "REFUSE to raise a count — silently: it prints the observed (higher) number and leaves the file "
            "unchanged, which reads like a failed write. It is not a way to unblock a ship.\n"
            "-> SSOT: /plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md. "
            "Baseline: unified-trading-pm/scripts/quality_gates/cloudbuild_template_drift_baseline.yaml "
            "(NEVER raise a count).",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
