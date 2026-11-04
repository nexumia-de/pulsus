"""Amazfish's database as Pulsus sees it: found, copied into a private
snapshot, and copied again shortly after Amazfish has written to it, so
the pages follow every sync without Pulsus talking to Amazfish
(docs/amazfish-data.md#reading-safely)."""
import logging

from gi.repository import Gio, GLib, GObject

from pulsus import settings, store

log = logging.getLogger("pulsus.source")

# Amazfish writes a sync in many small transactions: wait until it has
# been quiet this long before taking a new snapshot.
SETTLE_MS = 3000


class Source(GObject.Object):
    """`store` is a pulsus.store.Store on the newest snapshot, or None if
    no database was found. "changed" is emitted after a new snapshot."""

    __gsignals__ = {"changed": (GObject.SignalFlags.RUN_FIRST, None, ())}

    def __init__(self, path=None, watch=True):
        super().__init__()
        self.path = path or store.find_database()
        self.store = None
        self.error = None
        self._monitors = []
        self._timeout = 0
        self._stamp = None
        self.reload()
        if watch and self.path is not None:
            self._watch()

    @property
    def found(self):
        return self.store is not None

    def _file_stamp(self):
        stamps = []
        for suffix in ("", "-journal", "-wal"):
            try:
                st = self.path.with_name(self.path.name + suffix).stat()
                stamps.append((st.st_mtime_ns, st.st_size))
            except OSError:
                stamps.append(None)
        return tuple(stamps)

    def reload(self):
        """Take a new snapshot if the database changed since the last
        one. Returns True if the store is new."""
        if self.path is None:
            return False
        stamp = self._file_stamp()
        if stamp == self._stamp and self.store is not None:
            return False
        try:
            target = store.snapshot(self.path, settings.cache_dir() / "amazfish-snapshot.sqlite")
            new = store.Store(target)
        except Exception as e:   # sqlite3.Error, OSError: keep the old one
            log.warning("can't read %s: %s", self.path, e)
            self.error = str(e)
            return False
        if self.store is not None:
            self.store.close()
        self.store = new
        self.error = None
        self._stamp = stamp
        log.debug("snapshot of %s", self.path)
        return True

    def _watch(self):
        # The directory, so journals and a replaced file are seen too.
        directory = Gio.File.new_for_path(str(self.path.parent))
        try:
            monitor = directory.monitor_directory(Gio.FileMonitorFlags.NONE, None)
        except GLib.Error as e:
            log.info("no file monitor: %s", e.message)
            return
        monitor.connect("changed", self._on_changed)
        self._monitors.append(monitor)

    def _on_changed(self, monitor, file, other, event):
        if not file.get_basename().startswith(self.path.name):
            return
        if self._timeout:
            GLib.source_remove(self._timeout)
        self._timeout = GLib.timeout_add(SETTLE_MS, self._on_settled)

    def _on_settled(self):
        self._timeout = 0
        if self.reload():
            self.emit("changed")
        return GLib.SOURCE_REMOVE

    def refresh(self):
        """Check now (the window came back to the front)."""
        if self.reload():
            self.emit("changed")
