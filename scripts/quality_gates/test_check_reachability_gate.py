# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_reachability_gate.py.

Covers both covered-set derivation modes (census / registry), the reachability predicate
(aliased imports, docstring-mention non-matches, own-module/tests exclusion), the name-set
ratchet baseline, and — the "done when" bar from
`plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md` — a synthetic fixture repo
reproducing the exact defect class: a class built, exported, and never called in production.
"""

from __future__ import annotations

from pathlib import Path

from check_reachability_gate import (  # type: ignore[import-not-found]
    Baseline,
    ReachabilityTarget,
    census_classes,
    class_is_reachable,
    load_baseline,
    main,
    registry_classes,
    registry_uses_dynamic_dispatch,
    resolve_import_aliases,
    source_instantiates_any,
    unreachable_classes,
    write_baseline,
)

# ── census_classes ───────────────────────────────────────────────────────────


def test_census_classes_finds_direct_subclasses(tmp_path: Path) -> None:
    protocols = tmp_path / "protocols"
    protocols.mkdir()
    (protocols / "aave.py").write_text("class AAVEConnector(BaseConnector):\n    pass\n")
    (protocols / "base.py").write_text("class BaseConnector:\n    pass\n")

    target = ReachabilityTarget(
        key="t",
        repo="r",
        mode="census",
        census_dir="protocols",
        base_class_names=("BaseConnector",),
        exclude_class_names=frozenset({"BaseConnector"}),
        search_root="",
    )
    assert census_classes(tmp_path, target) == {"AAVEConnector": "protocols/aave.py"}


def test_census_classes_excludes_the_base_itself(tmp_path: Path) -> None:
    """The base class itself must never appear as a covered entry -- proves the
    exclude_class_names filter isn't vacuous (it would false-flag every ABC as
    'unreachable' otherwise, since abstract bases are never directly instantiated)."""
    protocols = tmp_path / "protocols"
    protocols.mkdir()
    (protocols / "base.py").write_text("class BaseConnector:\n    pass\n")
    target = ReachabilityTarget(
        key="t",
        repo="r",
        mode="census",
        census_dir="protocols",
        base_class_names=("BaseConnector",),
        exclude_class_names=frozenset({"BaseConnector"}),
        search_root="",
    )
    assert "BaseConnector" not in census_classes(tmp_path, target)


def test_census_classes_ignores_indirect_subclasses(tmp_path: Path) -> None:
    """Only DIRECT bases count (matches the real fleet shape: `class X(BaseConnector):`,
    never multi-level DeFi connector inheritance) -- a class two levels down must not be
    silently picked up as if it were a leaf connector."""
    protocols = tmp_path / "protocols"
    protocols.mkdir()
    (protocols / "mid.py").write_text(
        "class BaseConnector:\n    pass\nclass MidConnector(BaseConnector):\n    pass\nclass "
        "LeafConnector(MidConnector):\n    pass\n"
    )
    target = ReachabilityTarget(
        key="t",
        repo="r",
        mode="census",
        census_dir="protocols",
        base_class_names=("BaseConnector",),
        exclude_class_names=frozenset({"BaseConnector"}),
        search_root="",
    )
    assert census_classes(tmp_path, target) == {"MidConnector": "protocols/mid.py"}


# ── registry_classes ─────────────────────────────────────────────────────────


def test_registry_classes_bare_name_values(tmp_path: Path) -> None:
    (tmp_path / "factory.py").write_text(
        "from x import BinanceAdapter, DeribitAdapter\nADAPTER_MAP = {\n"
        '    "binance": BinanceAdapter,\n    "deribit": DeribitAdapter,\n}\n'
    )
    target = ReachabilityTarget(
        key="t", repo="r", mode="registry", registry_file="factory.py", registry_var="ADAPTER_MAP", search_root=""
    )
    assert registry_classes(tmp_path, target) == {
        "BinanceAdapter": "factory.py",
        "DeribitAdapter": "factory.py",
    }


def test_registry_classes_tuple_values() -> None:
    """MTDS's real VENUE_REGISTRY shape: `{"binance": ("cefi", BinanceAdapter)}` -- the
    class is inside a tuple value, not the bare value itself."""
    import ast

    from check_reachability_gate import _collect_dict_value_names  # type: ignore[import-not-found]

    node = ast.parse('("cefi", BinanceAdapter)').body[0].value  # type: ignore[attr-defined]
    assert _collect_dict_value_names(node) == {"BinanceAdapter"}


def test_registry_classes_ignores_other_dict_vars(tmp_path: Path) -> None:
    (tmp_path / "factory.py").write_text('OTHER_MAP = {"x": SomeClass}\nADAPTER_MAP = {"y": RealClass}\n')
    target = ReachabilityTarget(
        key="t", repo="r", mode="registry", registry_file="factory.py", registry_var="ADAPTER_MAP", search_root=""
    )
    assert registry_classes(tmp_path, target) == {"RealClass": "factory.py"}


# ── registry_uses_dynamic_dispatch ───────────────────────────────────────────


def test_registry_uses_dynamic_dispatch_subscript_call(tmp_path: Path) -> None:
    """The real MTDS shape: `category, adapter_class = REGISTRY[key]` then
    `adapter_class(...)` -- a bare subscript is enough evidence, no need to prove the
    unpacked variable is later called (that dataflow is a much harder, unnecessary proof)."""
    (tmp_path / "factory.py").write_text(
        "def get_adapter(key):\n    _, cls = VENUE_REGISTRY[key]\n    return cls(config={})\n"
    )
    target = ReachabilityTarget(
        key="t", repo="r", mode="registry", registry_file="factory.py", registry_var="VENUE_REGISTRY", search_root=""
    )
    assert registry_uses_dynamic_dispatch(tmp_path, target)


def test_registry_uses_dynamic_dispatch_get_call(tmp_path: Path) -> None:
    """The real strategy-service shape: `ARCHETYPE_ENGINE_REGISTRY.get(archetype)` in a
    DIFFERENT file than the registry's own definition."""
    (tmp_path / "factory.py").write_text("ARCHETYPE_ENGINE_REGISTRY = {}\n")
    (tmp_path / "coverage.py").write_text(
        "from factory import ARCHETYPE_ENGINE_REGISTRY\n\ndef f(a):\n    return ARCHETYPE_ENGINE_REGISTRY.get(a)\n"
    )
    target = ReachabilityTarget(
        key="t",
        repo="r",
        mode="registry",
        registry_file="factory.py",
        registry_var="ARCHETYPE_ENGINE_REGISTRY",
        search_root="",
    )
    assert registry_uses_dynamic_dispatch(tmp_path, target)


def test_registry_uses_dynamic_dispatch_negative_control_no_subscript_or_get(tmp_path: Path) -> None:
    """The real STRATEGY_CLOSE_ALL_REGISTRY shape: defined, never subscripted/`.get()`-ed
    anywhere -- a genuinely static (or dead) registry, not a dynamic-dispatch false-positive
    trap. Proves the detector isn't vacuously true on every registry."""
    (tmp_path / "close_all.py").write_text(
        'STRATEGY_CLOSE_ALL_REGISTRY = {"X": SomeCloseAll}\n__all__ = ["STRATEGY_CLOSE_ALL_REGISTRY"]\n'
    )
    target = ReachabilityTarget(
        key="t",
        repo="r",
        mode="registry",
        registry_file="close_all.py",
        registry_var="STRATEGY_CLOSE_ALL_REGISTRY",
        search_root="",
    )
    assert not registry_uses_dynamic_dispatch(tmp_path, target)


def test_registry_uses_dynamic_dispatch_ignores_unrelated_dict_subscript(tmp_path: Path) -> None:
    """Subscripting a DIFFERENT dict must not false-positive -- proves the name check is
    real, not "any subscript anywhere counts"."""
    (tmp_path / "factory.py").write_text("def f(k):\n    return OTHER_DICT[k]\n")
    target = ReachabilityTarget(
        key="t", repo="r", mode="registry", registry_file="factory.py", registry_var="VENUE_REGISTRY", search_root=""
    )
    assert not registry_uses_dynamic_dispatch(tmp_path, target)


def test_unreachable_classes_returns_none_for_dynamic_dispatch_registry(tmp_path: Path) -> None:
    (tmp_path / "factory.py").write_text(
        'class Foo:\n    pass\nVENUE_REGISTRY = {"x": Foo}\n\ndef get(k):\n    return VENUE_REGISTRY[k](config={})\n'
    )
    target = ReachabilityTarget(
        key="t", repo="r", mode="registry", registry_file="factory.py", registry_var="VENUE_REGISTRY", search_root=""
    )
    assert unreachable_classes(tmp_path, target) is None


# ── resolve_import_aliases / source_instantiates_any ────────────────────────


def test_resolve_import_aliases_includes_alias_and_original() -> None:
    import ast

    tree = ast.parse("from x.y import FooConnector as Bar\n")
    assert resolve_import_aliases(tree, "FooConnector") == {"FooConnector", "Bar"}


def test_source_instantiates_any_negative_control_import_only() -> None:
    """An import with no call must NOT count -- proves the scan isn't vacuous."""
    import ast

    tree = ast.parse("from x.y import FooConnector\n\ndef f() -> None:\n    pass\n")
    assert not source_instantiates_any(tree, resolve_import_aliases(tree, "FooConnector"))


def test_source_instantiates_any_negative_control_docstring_mention() -> None:
    import ast

    tree = ast.parse('"""Uses FooConnector eventually."""\n# TODO: call FooConnector here\n')
    assert not source_instantiates_any(tree, resolve_import_aliases(tree, "FooConnector"))


def test_source_instantiates_any_positive_control_via_alias() -> None:
    """A real instantiation via an import alias must be detected -- the real
    AAVEConnector-as-UDEIAAVEConnector case."""
    import ast

    tree = ast.parse("from x.y import FooConnector as Bar\n\ndef f():\n    return Bar(config={})\n")
    assert source_instantiates_any(tree, resolve_import_aliases(tree, "FooConnector"))


# ── class_is_reachable ────────────────────────────────────────────────────────


def test_class_is_reachable_finds_a_real_caller(tmp_path: Path) -> None:
    (tmp_path / "protocols").mkdir()
    (tmp_path / "protocols" / "aave.py").write_text("class AAVEConnector:\n    pass\n")
    (tmp_path / "cli").mkdir()
    (tmp_path / "cli" / "handler.py").write_text(
        "from protocols.aave import AAVEConnector\n\ndef build():\n    return AAVEConnector(config={})\n"
    )

    assert class_is_reachable(tmp_path, "AAVEConnector", "", ("protocols",))


def test_class_is_reachable_false_when_only_own_module_and_tests_reference_it(tmp_path: Path) -> None:
    """The exact MarinadeConnector shape: defined + tested, zero production callers."""
    (tmp_path / "protocols").mkdir()
    (tmp_path / "protocols" / "marinade.py").write_text(
        "class MarinadeConnector:\n    pass\n\ndef _self_check():\n    return MarinadeConnector(config={})\n"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_marinade.py").write_text(
        "from protocols.marinade import MarinadeConnector\n\ndef test_x():\n    MarinadeConnector(config={})\n"
    )

    assert not class_is_reachable(tmp_path, "MarinadeConnector", "", ("protocols",))


def test_class_is_reachable_excludes_test_files_at_search_root(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "test_thing.py").write_text(
        "from x import FooConnector\n\ndef test_x():\n    FooConnector(config={})\n"
    )
    assert not class_is_reachable(tmp_path, "FooConnector", "src", ())


# ── unreachable_classes — the "done when" proof ──────────────────────────────


def test_unreachable_classes_reproduces_the_defect_class(tmp_path: Path) -> None:
    """Synthetic fixture repo: 3 connectors under census_dir, one wired into a real
    production handler, two never called outside their own module/tests -- the exact
    Marinade/Kamino/Jupiter shape from e2e_wiring_reachability_audit_2026_08_15.md."""
    repo = tmp_path / "svc"
    protocols = repo / "svc" / "protocols"
    protocols.mkdir(parents=True)
    (protocols / "base.py").write_text("class BaseConnector:\n    pass\n")
    (protocols / "aave.py").write_text("class AAVEConnector(BaseConnector):\n    pass\n")
    (protocols / "marinade.py").write_text("class MarinadeConnector(BaseConnector):\n    pass\n")
    (protocols / "kamino.py").write_text("class KaminoConnector(BaseConnector):\n    pass\n")
    handlers = repo / "svc" / "handlers"
    handlers.mkdir(parents=True)
    (handlers / "live.py").write_text(
        "from svc.protocols.aave import AAVEConnector\n\ndef build():\n    return AAVEConnector()\n"
    )

    target = ReachabilityTarget(
        key="svc:protocols",
        repo="svc",
        mode="census",
        census_dir="svc/protocols",
        base_class_names=("BaseConnector",),
        exclude_class_names=frozenset({"BaseConnector"}),
        search_root="svc",
        exclude_prefixes=("svc/protocols",),
    )
    assert unreachable_classes(repo, target) == {"MarinadeConnector", "KaminoConnector"}


# ── Baseline round-trip ──────────────────────────────────────────────────────


def test_baseline_round_trip(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.json"
    write_baseline({"demo:target": {"Foo", "Bar"}}, Baseline(), path=baseline_file)

    loaded = load_baseline(baseline_file)

    assert loaded.allowed("demo:target") == {"Foo", "Bar"}
    assert loaded.allowed("unscanned:target") == set()


def test_baseline_preserves_unscanned_targets(tmp_path: Path) -> None:
    baseline_file = tmp_path / "baseline.json"
    existing = Baseline(tolerated={"a:t": {"X"}, "b:t": {"Y"}})
    write_baseline({"a:t": {"X", "NEW"}}, existing, path=baseline_file)

    loaded = load_baseline(baseline_file)

    assert loaded.allowed("a:t") == {"X", "NEW"}  # deliberate --update-baseline: written verbatim
    assert loaded.allowed("b:t") == {"Y"}  # unobserved this run -- carried forward verbatim


# ── main(): synthetic new-unreachable-class case ─────────────────────────────


def _write_target_fixture(workspace_root: Path, repo: str, wired: bool) -> None:
    repo_root = workspace_root / repo
    protocols = repo_root / "svc" / "protocols"
    protocols.mkdir(parents=True)
    (protocols / "base.py").write_text("class BaseConnector:\n    pass\n")
    (protocols / "marinade.py").write_text("class MarinadeConnector(BaseConnector):\n    pass\n")
    if wired:
        handlers = repo_root / "svc" / "handlers"
        handlers.mkdir(parents=True)
        (handlers / "live.py").write_text(
            "from svc.protocols.marinade import MarinadeConnector\n\ndef build():\n    return MarinadeConnector()\n"
        )


def test_main_flags_new_unreachable_class_beyond_empty_baseline(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import check_reachability_gate  # type: ignore[import-not-found]

    _write_target_fixture(tmp_path, "svc", wired=False)
    fixture_target = ReachabilityTarget(
        key="svc:protocols",
        repo="svc",
        mode="census",
        census_dir="svc/protocols",
        base_class_names=("BaseConnector",),
        exclude_class_names=frozenset({"BaseConnector"}),
        search_root="svc",
        exclude_prefixes=("svc/protocols",),
    )
    monkeypatch.setattr(check_reachability_gate, "TARGETS", (fixture_target,))
    baseline_file = tmp_path / "baseline.json"
    write_baseline({}, Baseline(), path=baseline_file)

    exit_code = main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline_file)])

    assert exit_code == 1


def test_main_passes_when_baselined(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import check_reachability_gate  # type: ignore[import-not-found]

    _write_target_fixture(tmp_path, "svc", wired=False)
    fixture_target = ReachabilityTarget(
        key="svc:protocols",
        repo="svc",
        mode="census",
        census_dir="svc/protocols",
        base_class_names=("BaseConnector",),
        exclude_class_names=frozenset({"BaseConnector"}),
        search_root="svc",
        exclude_prefixes=("svc/protocols",),
    )
    monkeypatch.setattr(check_reachability_gate, "TARGETS", (fixture_target,))
    baseline_file = tmp_path / "baseline.json"
    write_baseline({"svc:protocols": {"MarinadeConnector"}}, Baseline(), path=baseline_file)

    exit_code = main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline_file)])

    assert exit_code == 0


def test_main_flags_stale_baseline_entry_once_wired(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """A baselined class that becomes reachable must fail until removed from the baseline
    -- proves the ratchet only shrinks, it doesn't silently tolerate forever."""
    import check_reachability_gate  # type: ignore[import-not-found]

    _write_target_fixture(tmp_path, "svc", wired=True)  # now wired -- baseline is stale
    fixture_target = ReachabilityTarget(
        key="svc:protocols",
        repo="svc",
        mode="census",
        census_dir="svc/protocols",
        base_class_names=("BaseConnector",),
        exclude_class_names=frozenset({"BaseConnector"}),
        search_root="svc",
        exclude_prefixes=("svc/protocols",),
    )
    monkeypatch.setattr(check_reachability_gate, "TARGETS", (fixture_target,))
    baseline_file = tmp_path / "baseline.json"
    write_baseline({"svc:protocols": {"MarinadeConnector"}}, Baseline(), path=baseline_file)

    exit_code = main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline_file)])

    assert exit_code == 1


def test_main_skips_repo_not_present(tmp_path: Path) -> None:
    exit_code = main(["--workspace-root", str(tmp_path)])
    assert exit_code == 0
