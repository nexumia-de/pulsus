"""Pulsus: the health data of your watch, from Amazfish, on Phosh phones."""

try:
    from pulsus.config import APP_ID, BUILD_LABEL
except ImportError:  # run from the source tree, config.py is not built
    APP_ID = "de.nexumia.Pulsus"
    BUILD_LABEL = ""
VERSION = "0.1.1"
# The nightly app is built from every push to main.
NIGHTLY = APP_ID.endswith(".Devel")
NAME = "Watch Health (Nightly)" if NIGHTLY else "Watch Health"
# About dialog, e.g. "0.1.0 (main · 8534d2c)" for a nightly build.
VERSION_LABEL = f"{VERSION} ({BUILD_LABEL})" if BUILD_LABEL else VERSION
REPO_URL = "https://github.com/nexumia-de/pulsus"
# Voluntary support for development (phosh-toolkit docs/support.md).
SUPPORT_URL = "https://liberapay.com/suitably"
