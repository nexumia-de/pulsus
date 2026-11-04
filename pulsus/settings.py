"""Pulsus's own preferences on disk: style and the daily step goal. Pulsus
keeps no health data of its own; the snapshot of Amazfish's database is
a cache. No GTK."""
from dataclasses import dataclass

from phosh_toolkit.settings import JsonStore, app_dir

VERSION = 1
STEP_GOALS = (4000, 6000, 8000, 10000, 12000, 15000)


@dataclass
class Settings:
    style: str = "system"
    step_goal: int = 8000


def config_dir():
    return app_dir("config", "pulsus")


def cache_dir():
    return app_dir("cache", "pulsus")


class Store(JsonStore):
    def __init__(self, path=None):
        super().__init__(path or config_dir() / "settings.json", Settings, VERSION)
