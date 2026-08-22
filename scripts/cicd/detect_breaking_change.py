#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Content-based breaking-change detector for the CI/CD breaking-gate.

Replaces the version-phase heuristic (`bump_type == minor on a 0.x repo`) and the
crude `git diff __init__.py | grep '^-'` text-diff that flagged ANY removed line —
including reformatting, import reordering, and docstring edits — as "breaking".

A change is BREAKING only if the **public API / schema surface** changed in a way
that can break a consumer's import or call:

  * a public exported name (in ``__all__`` or a public top-level def/class) was
    removed or renamed;
  * a public function/method signature changed incompatibly (a required parameter
    added, a parameter removed/renamed, positional order changed, ``*args``/``**kwargs``
    dropped);
  * a public class was removed, or a public method on it was removed;
  * a Pydantic/dataclass FIELD (annotated class attribute) was removed, renamed, or
    its type annotation changed (schema/contract surface — the UAC case);
  * an HTTP route (``@app.get`` / ``@router.post`` …) was removed;
  * a module-level dict/list/set constant tagged ``# @contract-surface`` lost a
    top-level key or a collection-member/inner-key (the UAC registry-data-dict case —
    e.g. ``INSTRUMENT_TYPES_BY_VENUE: dict[str, set[str]]`` losing ``"SPOT_PAIR"`` from
    a venue's set stays the same annotated, exported dict, invisible to every other
    check above, but is a real contract break for consumers that enumerate it).

NOT breaking: added names, added *optional* (defaulted) parameters, added methods,
added fields, docstring/comment/body changes, reformatting, reordering, an ADDED
key/member/inner-key on a tagged registry constant.

Stdlib-only (``ast`` + ``subprocess`` + ``git``) — no external dependency so it can
run inside any repo's semver-agent job without a fleet-wide pin.

Usage (inside a checked-out repo):
    detect_breaking_change.py --source-dir <pkg_dir> --base-ref <sha> --head-ref HEAD [--json]

Exit code is always 0 (the verdict is the payload). Prints ``is_breaking=true|false``
on the last stdout line so a shell can ``tail -1``; with ``--json`` prints a full report.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import cast

CONTRACT_SURFACE_MARKER = "@contract-surface"
"""Comment tag placed directly above a module-level registry dict/list/set constant
to opt it into literal-level contract-surface diffing (see ``_diff_registry_value``).
Precedent: the manifest ``schema_version`` bump is an explicit, deliberate signal that
a data contract changed (``/codex/02-data/availability-manifest-and-data-status.md``);
this marker is the same idea applied to a plain Python data registry — an explicit,
grep-able tag rather than a name/path heuristic the differ would have to guess at.
"""

CROSS_REPO_REGISTRY_ALLOWLIST: frozenset[str] = frozenset(
    {
        "SOURCE_PRIORITY",
        "VENUE_TO_ADAPTER_KEY",
        "VENUE_PREFIX_TO_PROTOCOL",
        "DEFI_VENUE_TO_PROTOCOL",
        "CEFI_PERP_VENUE_API_ENDPOINTS",
    }
)
"""Narrow, explicit set of cross-repo registry constants whose resolved VALUE (not just
its name/export status) drives a downstream consumer's runtime behaviour purely by being
looked up at import time — the exact class root-caused in
``uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`` (``a2beed46`` removed
``massive`` from ``SOURCE_PRIORITY``'s tradfi list; every other check in this differ reads
that as "same exported name, same annotation" = non-breaking).

Deliberately **decoupled from ``is_breaking``** — see that doc's blocker 1: a routine
recalibration (e.g. ``EMISSION_LATENCY_MS_BY_SOURCE``, not in this allowlist) is a value
edit too, and coupling value-detection to ``is_breaking`` would false-break the fleet on
every benign tweak to an allowlisted-adjacent constant. This signal only ever feeds the
separate ``registry_value_changed``/``registry_value_changed_names`` fields (see
``main()``), which a caller can use to trigger a *targeted re-dispatch* of direct
dependents — never the promotion-blocking gate itself.

Extend this set only for a constant that is genuinely READ by another repo at runtime
(grep its consumers before adding) — this is not a general "track every constant" switch,
it stays narrow by design.
"""

_CONFIG_YAML_ALLOWLIST: frozenset[str] = frozenset(
    {
        "unified_api_contracts/config/cloud-providers.yaml",
    }
)
"""Repo-relative paths of non-Python config files that get the SAME decoupled
value-changed treatment as ``CROSS_REPO_REGISTRY_ALLOWLIST`` (path-scoped, not
AST-scoped — these aren't Python so there's no AST to canonicalize). Path-scoped: a repo
that doesn't carry a given path here is silently skipped (``_git_show`` returns None),
so this list is safe to share verbatim across every repo's copy of this script."""


def _git_show(ref: str, path: str) -> str | None:
    """Return file content at ``ref:path`` or None if it does not exist there."""
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None


def _git_changed_py(base_ref: str, head_ref: str, source_dir: str) -> list[str]:
    """List .py files under ``source_dir`` that DIFFER between base and head.

    A public-surface change can only originate in a file whose content changed (or was
    added/removed) — so we only need to parse the changed set, not the whole repo. This
    keeps the differ fast (a handful of files per promotion) instead of forking ``git
    show`` over thousands of unchanged files.
    """
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}..{head_ref}", "--", source_dir],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return sorted({ln for ln in out.splitlines() if ln.endswith(".py")})


# A changed path matching one of these is DEFINITELY not release-worthy on its own — pure
# CI/docs/lockfile/metadata churn. Deliberately SHORT and conservative: anything not matched
# here counts as "real" (biases toward false-positive "something changed", never a silent
# false-negative miss — the exact failure class this signal exists to close, see
# `_source_touched`'s docstring).
_NON_FUNCTIONAL_PATH_RE = re.compile(
    r"^(\.github/|docs/|\.gitleaks\.toml$|\.gitignore$|README\.md$|CHANGELOG\.md$|"
    r"uv\.lock$|poetry\.lock$|package-lock\.json$|pyproject\.toml$)"
)


def _source_touched(base_ref: str, head_ref: str) -> bool:
    """True if ANY file changed between base and head that isn't pure CI/docs/lockfile noise.

    Deliberately REPO-WIDE, not scoped to ``--source-dir`` — unlike every other check in this
    module. `--source-dir` is derived by convention (``<repo>-name`` -> ``<repo>_name``) and
    that convention does not hold for every repo (e.g. e2e-testing's real content lives under
    `scripts/`/`tests/`, not a package dir named `e2e_testing/`); a squash-promote commit
    (`chore(promote): LDR -> main`) also destroys the individual feat:/fix: commit-message
    prefixes semver-agent's message-based classifier depends on. Both signals can go blind on
    the SAME promotion, at which point a repo that keeps shipping real work never tags again —
    measured live 2026-08-09 as a fleet-wide RELEASE TAG STALL on 6 repos where genuinely
    nothing shippable changed (correct: no bump) and a 7th (e2e-testing) where real `scripts/
    *.py` changes were invisible to the source-dir-scoped check (bug: should have bumped).
    This denylist-based, repo-wide check is the single content-based signal both semver-agent
    (bump decision) and reconcile_release_tags.py (stall-alert decision) key off of, so the two
    scripts' notions of "did anything shippable change" cannot silently diverge again.
    """
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}..{head_ref}"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        return True  # fail-safe: an unresolvable diff must never silently suppress a real signal
    changed = [ln for ln in out.splitlines() if ln.strip()]
    return any(not _NON_FUNCTIONAL_PATH_RE.match(p) for p in changed)


@dataclass
class Signature:
    """A back-compat-relevant view of a callable signature."""

    posonly: list[str] = field(default_factory=list)
    args: list[str] = field(default_factory=list)
    required: list[str] = field(default_factory=list)  # params with NO default
    kwonly_required: list[str] = field(default_factory=list)
    has_vararg: bool = False
    has_kwarg: bool = False

    @classmethod
    def from_node(cls, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Signature:
        a = node.args
        posonly = [p.arg for p in a.posonlyargs]
        args = [p.arg for p in a.args]
        ndef = len(a.defaults)
        positional = posonly + args
        required = positional[: len(positional) - ndef] if ndef else positional
        # drop conventional self/cls for methods
        required = [r for r in required if r not in ("self", "cls")]
        kwonly_required = [p.arg for p, d in zip(a.kwonlyargs, a.kw_defaults, strict=False) if d is None]
        return cls(
            posonly=posonly,
            args=[x for x in args if x not in ("self", "cls")],
            required=required,
            kwonly_required=kwonly_required,
            has_vararg=a.vararg is not None,
            has_kwarg=a.kwarg is not None,
        )

    def breaks_from(self, old: Signature) -> str | None:
        """Return a reason string if going old->self is backward-incompatible."""
        # a new REQUIRED positional/keyword param breaks existing callers
        new_required = [r for r in self.required if r not in old.required]
        # filter: a genuinely new required positional is breaking; but if the param
        # merely moved from optional->required keep it; both are breaking.
        added_required = [r for r in self.required if r not in old.args and r not in old.required]
        if added_required:
            return f"added required parameter(s) {added_required}"
        new_kwonly_req = [r for r in self.kwonly_required if r not in old.kwonly_required]
        if new_kwonly_req:
            return f"added required keyword-only parameter(s) {new_kwonly_req}"
        # a removed param that callers may pass positionally/by-keyword
        removed = [a for a in (old.required + old.args) if a not in (self.required + self.args)]
        if removed and not self.has_kwarg:
            return f"removed parameter(s) {removed}"
        # positional order change of the shared required prefix
        shared = [r for r in old.required if r in self.required]
        if shared != [r for r in self.required if r in old.required]:
            return "reordered required positional parameters"
        # dropping **kwargs / *args that old accepted
        if old.has_kwarg and not self.has_kwarg:
            return "dropped **kwargs"
        if old.has_vararg and not self.has_vararg:
            return "dropped *args"
        _ = new_required  # kept for clarity; subsumed by added_required
        return None


@dataclass
class PublicSurface:
    exports: set[str] = field(default_factory=set)  # __all__ / public top-level names
    functions: dict[str, Signature] = field(default_factory=dict)  # qualname -> sig
    classes: set[str] = field(default_factory=set)
    methods: dict[str, Signature] = field(default_factory=dict)  # Class.method -> sig
    fields: dict[str, str] = field(default_factory=dict)  # Class.field -> annotation
    routes: set[str] = field(default_factory=set)  # "GET /path" decorators
    registry: dict[str, object] = field(default_factory=dict)  # tagged constant -> literal snapshot
    registry_values: dict[str, object] = field(default_factory=dict)  # allowlisted constant -> literal snapshot


def _annotation_str(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except (ValueError, AttributeError, RecursionError):
        return "?"


def _is_enum_base(b: ast.expr) -> bool:
    """True if a class base looks like an Enum (Enum / StrEnum / IntEnum / IntFlag / Flag / ReprEnum)."""
    name = b.id if isinstance(b, ast.Name) else (b.attr if isinstance(b, ast.Attribute) else "")
    return name.endswith("Enum") or name in ("Flag", "IntFlag", "ReprEnum")


def _route_decorators(node: ast.AST) -> set[str]:
    routes: set[str] = set()
    decorators: list[ast.expr] = cast("list[ast.expr]", getattr(node, "decorator_list", []))
    for dec in decorators:
        if (
            isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Attribute)
            and dec.func.attr in ("get", "post", "put", "delete", "patch")
        ):
            val = dec.func.value
            base = getattr(val, "id", getattr(val, "attr", ""))
            if base in ("app", "router"):
                path = ""
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    path = str(dec.args[0].value)
                routes.add(f"{dec.func.attr.upper()} {path}")
    return routes


def _marker_above(lines: list[str], lineno: int, window: int = 12) -> bool:
    """True if a ``# @contract-surface`` comment appears in the ``window`` lines
    immediately preceding the 1-indexed AST ``lineno`` (allows a short explanatory
    comment block between the tag and the declaration it tags)."""
    start = max(0, lineno - 1 - window)
    return any(CONTRACT_SURFACE_MARKER in ln for ln in lines[start : lineno - 1])


def _resolve_literal(node: ast.expr, env: dict[str, str]) -> object:
    """Best-effort literal evaluation of a registry constant's AST value.

    Unlike ``ast.literal_eval`` this also resolves a bare ``ast.Name`` against ``env`` —
    the registry convention of declaring ``BINANCE_SPOT = "BINANCE-SPOT"`` then using
    the bare name as a dict key/member elsewhere in the same file. Raises ``ValueError``
    on anything else non-literal (a call, comprehension, attribute access, ...) so the
    caller can skip just that one entry rather than guess at its meaning.
    """
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise ValueError(f"unresolved name {node.id!r}")
    if isinstance(node, ast.Tuple):
        # tuple, not list: a dict key must be hashable (e.g. SOURCE_PRIORITY's
        # `(asset_group, data_type)` tuple keys) — a plain `ast.List` value stays a
        # python list below since list-VALUE order is itself meaningful (priority lists).
        return tuple(_resolve_literal(e, env) for e in node.elts)
    if isinstance(node, ast.List):
        return [_resolve_literal(e, env) for e in node.elts]
    if isinstance(node, ast.Set):
        return {_resolve_literal(e, env) for e in node.elts}
    if isinstance(node, ast.Dict):
        out: dict[object, object] = {}
        for k, v in zip(node.keys, node.values, strict=True):
            if k is None:  # a `**other` unpack — too dynamic to track safely
                raise ValueError("dict unpacking (**) is not literal-resolvable")
            out[_resolve_literal(k, env)] = _resolve_literal(v, env)
        return out
    raise ValueError(f"non-literal node {type(node).__name__}")


def _resolve_registry_dict(node: ast.expr, env: dict[str, str]) -> dict[str, object] | None:
    """Best-effort literal snapshot of a tagged registry constant's TOP-LEVEL keys.

    A per-key value that isn't statically resolvable (e.g. a computed list
    comprehension, as `VENUES_BY_ASSET_GROUP["defi"]` currently is) is DROPPED rather
    than aborting the whole constant — every other, literal key stays diffable. Returns
    None if ``node`` isn't a dict literal at all (nothing to snapshot).
    """
    if not isinstance(node, ast.Dict):
        return None
    out: dict[str, object] = {}
    for k, v in zip(node.keys, node.values, strict=True):
        if k is None:
            continue
        try:
            key = _resolve_literal(k, env)
            val = _resolve_literal(v, env)
        except ValueError:
            continue
        if isinstance(key, str):
            out[key] = val
    return out


def _resolve_allowlisted_value(node: ast.expr, env: dict[str, str]) -> object | None:
    """Best-effort full literal snapshot of an allowlisted constant's value (any shape —
    dict, list, set, tuple-keyed dict — unlike ``_resolve_registry_dict`` this is not
    restricted to top-level-dict-with-str-keys). Returns None on anything non-literal
    (e.g. a constructor call like ``CollateralAcceptance(...)``) rather than raising —
    that constant is simply not diffable this way, not a differ crash."""
    try:
        return _resolve_literal(node, env)
    except ValueError:
        return None


def _process_class_def(node: ast.ClassDef, surf: PublicSurface) -> None:
    """Fold one module-level class's methods/fields/enum-members into ``surf``."""
    surf.classes.add(node.name)
    surf.exports.add(node.name)
    # Enum members are a CONTRACT surface (consumers match on the member + its serialized
    # value — e.g. UAC StrEnums like DefiErrorCode). They are PLAIN `ast.Assign` (FOO = "foo"),
    # NOT annotated, so the AnnAssign branch below misses them. Capture them into `fields`
    # (keyed Class.MEMBER, value = the literal) so a removed/renamed member OR a changed value
    # trips the removed-field / changed-field-value breaking checks. Gate on an Enum base.
    is_enum = any(_is_enum_base(b) for b in node.bases)
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not item.name.startswith("_") or item.name in ("__init__",):
                surf.methods[f"{node.name}.{item.name}"] = Signature.from_node(item)
            surf.routes |= _route_decorators(item)
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            fname = item.target.id
            if not fname.startswith("_"):
                surf.fields[f"{node.name}.{fname}"] = _annotation_str(item.annotation)
        elif is_enum and isinstance(item, ast.Assign):
            _val = item.value
            val_repr = repr(_val.value) if isinstance(_val, ast.Constant) else "<enum member>"
            for tgt in item.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_"):
                    surf.fields[f"{node.name}.{tgt.id}"] = val_repr


def _process_module_annassign(node: ast.AnnAssign, lines: list[str], env: dict[str, str], surf: PublicSurface) -> None:
    """Fold one module-level annotated constant into ``surf`` — including registry
    contract-surface tracking (closes the gap from
    breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md): a module-level
    dict constant tagged `# @contract-surface` is diffed at the LITERAL level (removed
    top-level key / removed collection-member / removed inner key is breaking) —
    invisible to every other check, which only sees the unchanged name + unchanged
    `dict[...]` annotation.
    """
    assert isinstance(node.target, ast.Name)
    if not node.target.id.startswith("_"):
        surf.exports.add(node.target.id)
    if _marker_above(lines, node.lineno):
        snapshot = _resolve_registry_dict(node.value, env)
        if snapshot is not None:
            surf.registry[node.target.id] = snapshot
    if node.target.id in CROSS_REPO_REGISTRY_ALLOWLIST:
        value = _resolve_allowlisted_value(node.value, env)
        if value is not None:
            surf.registry_values[node.target.id] = value


def _process_module_assign(node: ast.Assign, env: dict[str, str], surf: PublicSurface) -> None:
    """Fold one module-level plain assignment into ``surf`` + accumulate ``env``."""
    for tgt in node.targets:
        if isinstance(tgt, ast.Name) and not tgt.id.startswith("_") and tgt.id != "__all__":
            surf.exports.add(tgt.id)
        if isinstance(tgt, ast.Name) and tgt.id in CROSS_REPO_REGISTRY_ALLOWLIST and len(node.targets) == 1:
            value = _resolve_allowlisted_value(node.value, env)
            if value is not None:
                surf.registry_values[tgt.id] = value
    if (
        len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ):
        env[node.targets[0].id] = node.value.value


def extract_surface(source: str, module: str) -> PublicSurface:
    """Extract the public API surface of one module's source text."""
    surf = PublicSurface()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return surf

    lines = source.splitlines()
    # name -> string-literal value, accumulated left-to-right as we walk the module
    # (the registry convention: `BINANCE_SPOT = "BINANCE-SPOT"` defined BEFORE it is
    # used as a dict key/member further down the same file).
    env: dict[str, str] = {}

    # __all__ if declared
    declared_all: set[str] | None = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if (
                isinstance(tgt, ast.Name)
                and tgt.id == "__all__"
                and isinstance(node.value, (ast.List, ast.Tuple, ast.Set))
            ):
                declared_all = {
                    e.value for e in node.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)
                }

    # Keyed by BARE name (not module-qualified) so a symbol MOVED between internal
    # modules — while staying exported — is not mistaken for a removal (it has the same
    # bare key in both refs). Collisions across modules are rare for public symbols and,
    # for a breaking GATE, err harmlessly toward "run SIT".
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                surf.functions[node.name] = Signature.from_node(node)
                surf.exports.add(node.name)
            surf.routes |= _route_decorators(node)
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            _process_class_def(node, surf)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            _process_module_annassign(node, lines, env, surf)
        elif isinstance(node, ast.Assign):
            _process_module_assign(node, env, surf)

    # If __all__ is declared, the export surface is exactly it (the intentional public API) —
    # minus by-convention-private (underscore-prefixed) names. Listing a ``_name`` in __all__ is
    # self-contradictory (private by PEP 8, "public" by __all__) and is used for internal-but-
    # cross-module-shared constants; the cross-repo breaking gate must not treat removing one as a
    # public-API break, consistent with how every other branch above already filters ``_``-names.
    if declared_all is not None:
        surf.exports = {n for n in declared_all if not n.startswith("_")}
    return surf


def merge(a: PublicSurface, b: PublicSurface) -> PublicSurface:
    out = PublicSurface()
    out.exports = a.exports | b.exports
    out.functions = {**a.functions, **b.functions}
    out.classes = a.classes | b.classes
    out.methods = {**a.methods, **b.methods}
    out.fields = {**a.fields, **b.fields}
    out.routes = a.routes | b.routes
    out.registry = {**a.registry, **b.registry}
    out.registry_values = {**a.registry_values, **b.registry_values}
    return out


def surface_at(ref: str, paths: list[str]) -> PublicSurface:
    """Build the public surface at ``ref`` restricted to the given changed ``paths``."""
    surf = PublicSurface()
    for path in paths:
        content = _git_show(ref, path)
        if content is None:
            continue  # file absent at this ref (added at head / removed at head)
        module = path.replace("/", ".").removesuffix(".py")
        surf = merge(surf, extract_surface(content, module))
    return surf


def _diff_registry_value(name: str, old: object, new: object) -> list[str]:
    """Structural literal diff for one `# @contract-surface`-tagged registry constant.

    Recurses through the 3 shapes this closes the gap for (dict-of-set, dict-of-list,
    dict-of-dict — INSTRUMENT_TYPES_BY_VENUE / VENUES_BY_ASSET_GROUP /
    VENUE_DATA_TYPE_CAPABILITIES). A removed top-level key, or a removed inner
    collection-member/dict-key, is breaking; an added one is not (mirrors the
    additive-OK rule everywhere else in this differ). A type mismatch (e.g. a value
    that failed literal resolution on one side) is silently skipped — best-effort,
    never a crash.
    """
    reasons: list[str] = []
    if isinstance(old, dict) and isinstance(new, dict):
        removed_keys = sorted(str(k) for k in (set(old) - set(new)))
        if removed_keys:
            reasons.append(f"registry {name}: removed key(s) {removed_keys}")
        for k in sorted(set(old) & set(new), key=str):
            reasons.extend(_diff_registry_value(f"{name}[{k!r}]", old[k], new[k]))
    elif isinstance(old, set) and isinstance(new, set):
        removed = sorted(str(m) for m in (old - new))
        if removed:
            reasons.append(f"registry {name}: removed member(s) {removed}")
    elif isinstance(old, list) and isinstance(new, list):
        removed = sorted(str(m) for m in (set(old) - set(new)))
        if removed:
            reasons.append(f"registry {name}: removed member(s) {removed}")
    return reasons


def _canon_key(k: object) -> str:
    """Stable sort/compare key for a (possibly non-str, e.g. tuple) dict key."""
    return repr(k)


def _canonicalize_value(v: object) -> object:
    """Order-normalize a resolved literal for the DECOUPLED value-changed comparison:
    dict KEY ORDER never matters (a reorder in source is not a value change — sorted by
    ``repr`` of the key), but LIST ORDER IS PRESERVED (a registry like
    ``SOURCE_PRIORITY``'s per-cell vendor list is a priority order — reordering it *is*
    a behavior change, unlike a dict-key reorder). Sets/frozensets are already
    order-free. Returns a hashable, ``==``-comparable structure."""
    if isinstance(v, dict):
        return tuple(sorted(((_canon_key(k), _canonicalize_value(val)) for k, val in v.items()), key=lambda kv: kv[0]))
    if isinstance(v, list):
        return tuple(_canonicalize_value(x) for x in v)
    if isinstance(v, tuple):
        return tuple(_canonicalize_value(x) for x in v)
    if isinstance(v, (set, frozenset)):
        return frozenset(_canonicalize_value(x) for x in v)
    return v


def registry_value_changes(old: PublicSurface, new: PublicSurface) -> list[str]:
    """DECOUPLED signal (deliberately NOT folded into ``is_breaking`` / ``diff_surfaces`` —
    see ``CROSS_REPO_REGISTRY_ALLOWLIST``'s docstring for why). Returns the sorted names of
    every allowlisted constant whose order-normalized resolved value differs between
    ``old`` and ``new``. A constant only present on one side (added/removed entirely) is
    NOT reported here — that's already covered by the export-name diff above; this signal
    is specifically for "same name, same shape, different content"."""
    changed: list[str] = []
    for name in sorted(CROSS_REPO_REGISTRY_ALLOWLIST):
        if name not in old.registry_values or name not in new.registry_values:
            continue
        if _canonicalize_value(old.registry_values[name]) != _canonicalize_value(new.registry_values[name]):
            changed.append(name)
    return changed


def config_yaml_value_changes(base_ref: str, head_ref: str) -> list[str]:
    """Same decoupled treatment as ``registry_value_changes``, path-scoped to
    ``_CONFIG_YAML_ALLOWLIST`` instead of AST-scoped (these aren't Python). Normalizes
    away comment-only lines, trailing whitespace, and blank lines before comparing, so a
    pure reformat/comment edit is not flagged — a real key/value change is. A path absent
    from THIS repo (``_git_show`` returns None) is silently skipped, so the same allowlist
    is safe to share verbatim across every repo's copy of this script."""
    changed: list[str] = []
    for path in sorted(_CONFIG_YAML_ALLOWLIST):
        old_text = _git_show(base_ref, path)
        new_text = _git_show(head_ref, path)
        if old_text is None or new_text is None:
            continue  # not present on one side in this repo -- out of scope for this signal
        if _normalize_yaml_text(old_text) != _normalize_yaml_text(new_text):
            changed.append(path)
    return changed


def _normalize_yaml_text(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.append(stripped)
    return lines


def diff_surfaces(old: PublicSurface, new: PublicSurface) -> list[str]:
    """Return a list of BREAKING reasons (empty == non-breaking)."""
    reasons: list[str] = []

    # 1) Export-name set is the authoritative public API a consumer imports. A name gone
    #    from the union public surface (was public, now absent everywhere scanned) = breaking.
    removed_exports = sorted(old.exports - new.exports)
    if removed_exports:
        reasons.append(f"removed public export(s): {removed_exports}")

    # 2) A public class that disappeared AND is no longer exported anywhere = removed
    #    (a class merely MOVED between modules keeps its bare key + export → not flagged).
    removed_classes = sorted((old.classes - new.classes) - new.exports)
    if removed_classes:
        reasons.append(f"removed public class(es): {removed_classes}")

    # 3) Signature changes of symbols present in BOTH refs (real incompatible change,
    #    not a move). A function gone but still exported (moved) is ignored here.
    for name, old_sig in sorted(old.functions.items()):
        new_sig = new.functions.get(name)
        if new_sig is None:
            if name in new.exports:
                continue  # moved, still exported
            reasons.append(f"removed public function: {name}")
            continue
        why = new_sig.breaks_from(old_sig)
        if why:
            reasons.append(f"function {name}: {why}")

    for qual, old_sig in sorted(old.methods.items()):
        cls = qual.split(".", 1)[0]
        new_sig = new.methods.get(qual)
        if new_sig is None:
            # only a real removal if the owning class is still public (else class-level move/removal covers it)
            if cls in new.exports or cls in new.classes:
                reasons.append(f"removed public method: {qual}")
            continue
        why = new_sig.breaks_from(old_sig)
        if why:
            reasons.append(f"method {qual}: {why}")

    # 4) Schema/contract fields (the UAC case): a removed/renamed/retyped field on a class
    #    still present is a contract break.
    removed_fields = sorted(set(old.fields) - set(new.fields))
    removed_fields = [f for f in removed_fields if f.split(".", 1)[0] in (new.exports | new.classes)]
    if removed_fields:
        reasons.append(f"removed schema field(s): {removed_fields}")
    for qual in sorted(set(old.fields) & set(new.fields)):
        if old.fields[qual] != new.fields[qual]:
            reasons.append(f"changed field type {qual}: {old.fields[qual]!r} -> {new.fields[qual]!r}")

    removed_routes = sorted(old.routes - new.routes)
    if removed_routes:
        reasons.append(f"removed HTTP route(s): {removed_routes}")

    # 5) Registry data-dict contract surface (the UAC INSTRUMENT_TYPES_BY_VENUE case,
    #    issue: breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md): a
    #    `# @contract-surface`-tagged constant's removed top-level key or removed
    #    collection-member/inner-key is breaking even though the name stayed exported
    #    with the same annotation — invisible to every check above.
    for name in sorted(set(old.registry) & set(new.registry)):
        reasons.extend(_diff_registry_value(name, old.registry[name], new.registry[name]))

    return reasons


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", required=True, help="package dir, e.g. unified_trading_library")
    ap.add_argument("--base-ref", required=True, help="git ref of the promoted/previous version")
    ap.add_argument("--head-ref", default="HEAD")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()
    source_dir = cast(str, args.source_dir)
    base_ref = cast(str, args.base_ref)
    head_ref = cast(str, args.head_ref)
    as_json = cast(bool, args.as_json)

    changed = _git_changed_py(base_ref, head_ref, source_dir)
    # Always include the package top-level __init__.py — it is the authoritative declared
    # public API (__all__); the export-set diff is the primary breaking signal even when
    # __init__.py itself did not change in this promotion.
    init_py = f"{source_dir.rstrip('/')}/__init__.py"
    scan = sorted(set(changed) | {init_py})
    old = surface_at(base_ref, scan)
    new = surface_at(head_ref, scan)
    reasons = diff_surfaces(old, new)
    is_breaking = bool(reasons)
    source_touched = _source_touched(base_ref, head_ref)

    # DECOUPLED signal (see CROSS_REPO_REGISTRY_ALLOWLIST docstring) — never folded into
    # `reasons`/`is_breaking`, only exposed as its own field for a caller to drive a
    # targeted re-dispatch of direct dependents.
    registry_value_changed_names = registry_value_changes(old, new) + config_yaml_value_changes(base_ref, head_ref)
    registry_value_changed = bool(registry_value_changed_names)

    if as_json:
        print(
            json.dumps(
                {
                    "is_breaking": is_breaking,
                    "reasons": reasons,
                    "base_ref": base_ref,
                    "head_ref": head_ref,
                    "source_dir": source_dir,
                    "old_export_count": len(old.exports),
                    "new_export_count": len(new.exports),
                    "source_touched": source_touched,
                    "registry_value_changed": registry_value_changed,
                    "registry_value_changed_names": registry_value_changed_names,
                },
                indent=2,
            )
        )
    else:
        if reasons:
            print("BREAKING — public-surface changes:")
            for r in reasons:
                print(f"  - {r}")
        else:
            print("non-breaking — no public API/schema surface change detected")
        print(f"is_breaking={'true' if is_breaking else 'false'}")
        print(f"source_touched={'true' if source_touched else 'false'}")
        if registry_value_changed_names:
            print("registry value(s) changed (decoupled signal, NOT is_breaking):")
            for n in registry_value_changed_names:
                print(f"  - {n}")
        print(f"registry_value_changed={'true' if registry_value_changed else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
