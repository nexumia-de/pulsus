"""Metadata, build files and manifest agree with each other."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pulsus

ROOT = Path(__file__).resolve().parent.parent
APP_ID = "de.nexumia.Pulsus"


def test_version_matches_meson_and_metainfo():
    meson = (ROOT / "meson.build").read_text()
    assert re.search(r"version: '([^']+)'", meson).group(1) == pulsus.VERSION
    metainfo = ET.parse(ROOT / "data" / f"{APP_ID}.metainfo.xml")
    assert metainfo.find("releases/release").get("version") == pulsus.VERSION


def test_every_module_is_installed():
    meson = (ROOT / "meson.build").read_text()
    for path in (ROOT / "pulsus").rglob("*.py"):
        name = path.relative_to(ROOT).as_posix()
        assert f"'{name}'" in meson, name


def test_phone_metadata():
    desktop = (ROOT / "data" / f"{APP_ID}.desktop").read_text()
    # Phosh matches the substring "mobile;" case-insensitively.
    assert re.search(r"^X-Purism-FormFactor=.*mobile;", desktop,
                     re.IGNORECASE | re.MULTILINE)
    root = ET.parse(ROOT / "data" / f"{APP_ID}.metainfo.xml").getroot()
    length = root.find("recommends/display_length")
    assert length.get("compare") == "ge" and length.text == "360"
    assert {"touch", "pointing", "keyboard"} <= {
        c.text for c in root.findall("supports/control")}
    assert root.find("url[@type='donation']").text == pulsus.SUPPORT_URL


def test_manifest_reads_amazfish_read_only_and_has_no_network():
    manifest = (ROOT / f"{APP_ID}.yml").read_text()
    args = [line.strip()[2:] for line in manifest.splitlines()
            if line.strip().startswith("- --")]
    reads = [a for a in args if a.startswith("--filesystem=")]
    assert reads and all(a.endswith(":ro") for a in reads)
    assert "--share=network" not in args
    commit = re.search(r"- name: phosh-toolkit.*?commit: (\w+)", manifest, re.S)
    assert commit and len(commit.group(1)) == 40


def test_screenshot_actions_exist():
    release = (ROOT / "release.toml").read_text()
    main = (ROOT / "pulsus" / "main.py").read_text()
    for action in re.findall(r'"app\.([a-z-]+)', release):
        assert f'"{action}"' in main, action


def test_stable_build_from_source_tree():
    assert pulsus.APP_ID == APP_ID and not pulsus.NIGHTLY
    assert pulsus.VERSION_LABEL == pulsus.VERSION


def test_own_icons_exist():
    icons = {p.stem for p in (ROOT / "data" / "icons").rglob("*.svg")}
    used = set()
    for path in (ROOT / "pulsus").rglob("*.py"):
        used |= set(re.findall(r'"(pulsus-[a-z0-9-]+-symbolic)"', path.read_text()))
    assert used and used <= icons, used - icons
    meson = (ROOT / "meson.build").read_text()
    assert "symbolic/apps" in meson
