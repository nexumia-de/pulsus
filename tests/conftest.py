"""Shared fixtures: private XDG directories and the demo database
(pulsus.demo), made once per test session."""
import sys
from pathlib import Path

import pytest

# The shared package from the sibling checkout (CI checks it out at the
# commit the Flatpak manifest pins and sets PYTHONPATH).
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "phosh-toolkit" / "lib"))

from pulsus import demo  # noqa: E402


@pytest.fixture(autouse=True)
def xdg(tmp_path, monkeypatch):
    for name in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(name, str(tmp_path / name.lower()))
    monkeypatch.delenv("PULSUS_DATABASE", raising=False)
    monkeypatch.delenv("PULSUS_DEMO", raising=False)


@pytest.fixture(scope="session")
def demo_db(tmp_path_factory):
    return demo.create(tmp_path_factory.mktemp("demo") / "amazfish.kexi")
