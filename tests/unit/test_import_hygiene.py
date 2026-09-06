"""Architectural guard rail.

The pipeline is one-directional:

    video -> perception -> tracking -> features -> events -> behaviours
          -> risk -> incidents -> db -> api -> web

The CV core must stay importable without any web or database machinery, because
three people are building these layers in parallel and the cheapest way for the
architecture to rot is for someone to reach "just one import" upward.

This test is deliberately blunt: it reads source text rather than importing, so
it works even while modules are still stubs.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "handleguard"

#: Layers that form the CV core. Nothing here may import from FORBIDDEN.
CORE_MODULES = [
    "types.py",
    "config.py",
    "video",
    "perception",
    "tracking",
    "features",
    "events",
    "behaviours",
    "risk",
]

#: Things the CV core must never depend on.
FORBIDDEN_TOP_LEVEL = {
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "sqlite3",
    "starlette",
    "pydantic",
}
FORBIDDEN_INTERNAL = {
    "handleguard.db",
    "handleguard.incidents",
    "handleguard.assistant",
    "apps",
}


def _python_files() -> list[Path]:
    out: list[Path] = []
    for entry in CORE_MODULES:
        p = PKG / entry
        if p.is_file():
            out.append(p)
        elif p.is_dir():
            out.extend(sorted(p.rglob("*.py")))
    return out


def _imports(path: Path) -> set[str]:
    """Every module name imported by `path`, as dotted strings."""
    tree = ast.parse(path.read_text(), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import — stays inside the package
                continue
            if node.module:
                names.add(node.module)
    return names


@pytest.mark.parametrize("path", _python_files(), ids=lambda p: str(p.relative_to(PKG)))
def test_cv_core_does_not_import_web_or_db(path: Path):
    found = _imports(path)
    for name in found:
        top = name.split(".")[0]
        assert top not in FORBIDDEN_TOP_LEVEL, (
            f"{path.relative_to(ROOT)} imports {name!r}. The CV core must stay "
            f"free of web/DB dependencies — move this logic into "
            f"handleguard/incidents/ or apps/api/ instead."
        )
        for bad in FORBIDDEN_INTERNAL:
            assert not (name == bad or name.startswith(bad + ".")), (
                f"{path.relative_to(ROOT)} imports {name!r}, which points back "
                f"up the pipeline. Data flows one way: the CV core emits "
                f"dataclasses and never reads persistence."
            )


def test_types_module_stays_dependency_free():
    """types.py is imported by everything, so it may only use stdlib + numpy."""
    found = _imports(PKG / "types.py")
    allowed = {"numpy", "dataclasses", "typing", "__future__", "enum", "datetime"}
    extra = {n.split(".")[0] for n in found} - allowed
    assert not extra, (
        f"types.py gained dependencies: {sorted(extra)}. Keep it importable "
        f"with nothing installed but numpy — every other module depends on it."
    )


def test_core_modules_exist():
    """Guards against the parametrized test silently passing on an empty list."""
    assert len(_python_files()) >= 3, "expected core modules to exist by now"
