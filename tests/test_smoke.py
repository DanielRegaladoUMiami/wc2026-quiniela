"""Smoke test — verifies the package import surface is intact during scaffolding."""

import importlib


def test_package_imports():
    for mod in (
        "src",
        "src.data",
        "src.features",
        "src.models",
        "src.sims",
        "src.strategy",
        "src.eval",
        "src.live",
    ):
        importlib.import_module(mod)
