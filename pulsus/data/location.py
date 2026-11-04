"""Where Amazfish keeps its database, and the read-only snapshot Pulsus
takes of it (docs/amazfish-data.md#reading-safely). No GTK."""
import os
import sqlite3
from pathlib import Path

# Where Amazfish keeps its database: QStandardPaths::AppDataLocation with
# organisation and application "harbour-amazfish", file "amazfish.kexi".
_RELATIVE = Path("harbour-amazfish") / "harbour-amazfish" / "amazfish.kexi"
LOCATIONS = (
    # Installed as a system package (postmarketOS, Alpine, distributions).
    Path(".local/share") / _RELATIVE,
    # Installed from Flathub (uk.co.piggz.amazfish).
    Path(".var/app/uk.co.piggz.amazfish/data") / _RELATIVE,
)

def find_database(home=None, environ=None):
    """The Amazfish database, or None. PULSUS_DATABASE overrides the
    search. Inside the Flatpak the home directory is the real one, so
    the same paths work there (docs/amazfish-data.md#flatpak)."""
    environ = os.environ if environ is None else environ
    if environ.get("PULSUS_DATABASE"):
        path = Path(environ["PULSUS_DATABASE"]).expanduser()
        return path if path.is_file() else None
    home = Path(home or Path.home())
    for relative in LOCATIONS:
        path = home / relative
        if path.is_file():
            return path
    return None


def searched_paths(home=None):
    home = Path(home or Path.home())
    return [home / relative for relative in LOCATIONS]


def snapshot(source, target):
    """Copy the database `source` to `target` without writing to the
    source: SQLite's backup API on a read-only connection, so the copy is
    consistent even while Amazfish writes. Returns `target`."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    src = sqlite3.connect(f"{Path(source).resolve().as_uri()}?mode=ro", uri=True)
    try:
        dst = sqlite3.connect(tmp)
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()
    tmp.replace(target)
    return target
