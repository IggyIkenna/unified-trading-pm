#!/usr/bin/env python3
# Epic: infrastructure_master
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
  * an HTTP route (``@app.get`` / ``@router.post`` …) was removed.

NOT breaking: added names, added *optional* (defaulted) parameters, added methods,
added fields, docstring/comment/body changes, reformatting, reordering.

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
import subprocess
import sys
from dataclasses import dataclass, field
from typing import cast


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
    # Module-level dict constants explicitly tagged `# @contract-surface` (the UAC
    # registry-data-dict case — INSTRUMENT_TYPES_BY_VENUE et al.). name -> a snapshot
    # tree built by `_registry_value` (see there for the shape).
    registries: dict[str, dict[str, object]] = field(default_factory=dict)


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


_CONTRACT_SURFACE_MARKER = "@contract-surface"


def _has_contract_surface_marker(lines: list[str], assign_lineno: int) -> bool:
    """True if a comment block immediately above ``assign_lineno`` (1-indexed) tags the
    constant it precedes as contract surface — ``# @contract-surface`` anywhere in a
    run of ``#``-comment lines directly touching the assignment (no blank-line gap).
    Lets a registry constant self-declare its contract status at the definition site
    (module-owner-maintained) instead of a differ-side allowlist that drifts from the
    registries it's meant to track.
    """
    i = assign_lineno - 2  # 0-indexed line directly above the assignment
    while i >= 0:
        stripped = lines[i].strip()
        if not stripped.startswith("#"):
            return False
        if _CONTRACT_SURFACE_MARKER in stripped:
            return True
        i -= 1
    return False


def _module_str_constants(tree: ast.Module) -> dict[str, str]:
    """Top-level ``NAME = "literal"`` bindings in this module.

    A registry dict's keys are frequently module constants, not inline literals
    (``{BINANCE_SPOT: {"SPOT_PAIR"}, ...}`` — venue_constants.py declares
    ``BINANCE_SPOT = "BINANCE-SPOT"`` earlier in the same file). Resolving these is
    required for ``_registry_key`` to see the real venue string instead of silently
    dropping every Name-keyed entry (which, for INSTRUMENT_TYPES_BY_VENUE, is most of
    the dict — including OKX_SPOT/BYBIT_SPOT, the exact venues the original
    23fa3a99-class incident's SPOT_PAIR capability now lives under post-Option-A).
    """
    out: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not (isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name):
                out[tgt.id] = node.value.value
    return out


def _registry_key(node: ast.expr, name_consts: dict[str, str]) -> str | None:
    """Resolve one dict KEY node to its string value: a literal, or a Name bound to a
    module-level string constant (see ``_module_str_constants``)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return name_consts.get(node.id)
    return None


def _registry_value(node: ast.expr, name_consts: dict[str, str]) -> frozenset[str] | dict[str, object] | None:
    """Snapshot one VALUE inside a tagged registry dict, recursively.

    - a ``Set``/``List``/``Tuple`` of string constants -> its member set (a removed
      member is the exact ``23fa3a99`` bug class: SPOT_PAIR dropped from OKX's set);
    - a ``Dict`` -> a nested key->snapshot map (a removed KEY is breaking, e.g. a
      removed ``data_type`` under ``VENUE_DATA_TYPE_CAPABILITIES[venue]``);
    - anything else (a literal date string, a computed expression, ...) -> None,
      "opaque" — we do not track VALUE mutations of a leaf, only key/member removal.
    """
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        members = {e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
        return frozenset(members) if len(members) == len(node.elts) else None
    if isinstance(node, ast.Dict):
        out: dict[str, object] = {}
        for key_node, val_node in zip(node.keys, node.values, strict=False):
            key = _registry_key(key_node, name_consts)
            if key is not None:
                out[key] = _registry_value(val_node, name_consts)
        return out
    return None


def extract_surface(source: str, module: str) -> PublicSurface:
    """Extract the public API surface of one module's source text."""
    surf = PublicSurface()
    lines = source.splitlines()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return surf

    name_consts = _module_str_constants(tree)

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
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and not tgt.id.startswith("_") and tgt.id != "__all__":
                    surf.exports.add(tgt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and isinstance(node.value, ast.Dict):
            # Module-level annotated dict constant (e.g. ``NAME: dict[str, set[str]] = {...}``)
            # explicitly tagged ``# @contract-surface`` — a registry data-dict whose literal
            # keys/collection-members ARE the contract (the UAC INSTRUMENT_TYPES_BY_VENUE case).
            # Untagged AnnAssigns are left alone (not added to exports either) — this is an
            # opt-in extension, not a change to the general export/field surface.
            if _has_contract_surface_marker(lines, node.lineno):
                snapshot = _registry_value(node.value, name_consts)
                if isinstance(snapshot, dict):
                    surf.registries[node.target.id] = snapshot

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
    out.registries = {**a.registries, **b.registries}
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


def _diff_registry(label: str, old: dict[str, object], new: dict[str, object]) -> list[str]:
    """Diff one ``# @contract-surface`` registry dict, recursing into nested dict values.

    A removed top-level/nested KEY, or a removed SET/LIST MEMBER, is breaking — mirrors
    the manifest ``schema_version`` precedent (a data registry's literal contents are the
    contract, not just its Python type annotation). Additive changes (new key, new
    member) and non-collection VALUE mutations (e.g. a ``VENUE_DATA_TYPE_CAPABILITIES``
    inner date string changing) are intentionally NOT flagged — matches the "additive
    stays non-breaking" rule and the todo's stated scope. See
    breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md.
    """
    reasons: list[str] = []
    removed_keys = sorted(set(old) - set(new))
    if removed_keys:
        reasons.append(f"removed registry key(s) {label}: {removed_keys}")
    for key in sorted(set(old) & set(new)):
        old_v, new_v = old[key], new[key]
        if isinstance(old_v, frozenset) and isinstance(new_v, frozenset):
            removed_members = sorted(old_v - new_v)
            if removed_members:
                reasons.append(f"removed registry member(s) {label}[{key!r}]: {removed_members}")
        elif isinstance(old_v, dict) and isinstance(new_v, dict):
            reasons.extend(_diff_registry(f"{label}[{key!r}]", old_v, new_v))
        # type-changed (set<->dict<->opaque) or opaque-on-either-side: not tracked here.
    return reasons


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

    # 5) `# @contract-surface`-tagged registry data-dicts (the UAC INSTRUMENT_TYPES_BY_VENUE
    #    case). A whole tagged registry disappearing is breaking too (strictly worse than
    #    losing one key inside it).
    removed_registries = sorted(set(old.registries) - set(new.registries))
    if removed_registries:
        noun = "registry" if len(removed_registries) == 1 else "registries"
        reasons.append(f"removed contract-surface {noun}: {removed_registries}")
    for name in sorted(set(old.registries) & set(new.registries)):
        reasons.extend(_diff_registry(name, old.registries[name], new.registries[name]))

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
    return 0


if __name__ == "__main__":
    sys.exit(main())
