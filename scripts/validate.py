#!/usr/bin/env python3
"""Validate this repository's CA metadata and Docker configuration offline."""

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/agrestisdavid/unraid-paperclip"
RAW = "https://raw.githubusercontent.com/agrestisdavid/unraid-paperclip/main"


def validate():
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    xml_files = sorted(ROOT.rglob("*.xml"))
    expected = {ROOT / "ca_profile.xml", ROOT / "templates/paperclip.xml"}
    check(set(xml_files) == expected, "Keep only the CA profile and the intended app XML in the repository.")
    parsed = {}
    for path in xml_files:
        raw = path.read_text(encoding="utf-8")
        check("<!DOCTYPE" not in raw and "<!ENTITY" not in raw, f"{path.name}: XML entities are not allowed.")
        check(not re.search(r"YOUR_|CHANGEME|REPLACE_ME", raw), f"{path.name}: unresolved publishing placeholder.")
        try:
            parsed[path.name] = ET.fromstring(raw)
        except ET.ParseError as exc:
            errors.append(f"{path.name}: {exc}")

    app = parsed.get("paperclip.xml")
    profile = parsed.get("ca_profile.xml")
    if app is not None:
        check(app.tag == "Container" and app.get("version") == "2", "Expected Container version 2.")
        for tag in ("Name", "Repository", "Support", "Project", "Overview", "Category", "WebUI", "Icon", "TemplateURL"):
            check(bool((app.findtext(tag) or "").strip()), f"Missing app field: {tag}")
        check(app.findtext("Repository") == "ghcr.io/paperclipai/paperclip:latest", "Unexpected upstream image.")
        check(app.findtext("TemplateURL") == RAW + "/templates/paperclip.xml", "TemplateURL must match the public file.")
        check(app.findtext("Icon") == RAW + "/assets/paperclip.svg", "Icon URL must match the bundled asset.")
        check(app.findtext("Support") == REPO + "/issues", "Support URL must resolve to this repository.")
        check(app.findtext("Network") == "bridge", "Bridge networking is required.")
        check(app.findtext("Privileged") == "false", "Privileged mode must be disabled.")
        extra = app.findtext("ExtraParams", "")
        check(extra == "--pids-limit=2048 --stop-timeout=60", "Review unexpected Docker arguments.")
        configs = app.findall("Config")
        keys = [(c.get("Type"), c.get("Target")) for c in configs]
        check(len(keys) == len(set(keys)), "Duplicate Docker configuration target.")
        variables = {c.get("Target"): c for c in configs if c.get("Type") == "Variable"}
        for c in configs:
            for attr in ("Name", "Target", "Default", "Mode", "Description", "Type", "Display", "Required", "Mask"):
                check(attr in c.attrib, f"{c.get('Name')}: missing {attr} attribute.")
            check(c.get("Type") in {"Variable", "Path", "Port"}, "Unsupported configuration type.")
            check(c.get("Display") in {"always", "advanced", "hidden"}, "Invalid display setting.")
        for key in ("BETTER_AUTH_SECRET", "PAPERCLIP_TOOL_ACTION_SIGNING_SECRET"):
            c = variables.get(key)
            check(c is not None, f"Missing {key}.")
            if c is not None:
                check(c.get("Mask") == "true" and c.get("Required") == "true", f"{key} must be required and masked.")
                check(not (c.text or "").strip() and not c.get("Default"), f"Never publish a default {key}.")
        for key, value in {"HOST": "0.0.0.0", "PORT": "3100", "USER_UID": "1000", "USER_GID": "1000", "PAPERCLIP_HOME": "/paperclip", "PAPERCLIP_DEPLOYMENT_MODE": "authenticated", "PAPERCLIP_DEPLOYMENT_EXPOSURE": "private"}.items():
            c = variables.get(key)
            check(c is not None and c.text == value, f"Unexpected {key} default.")
        public = variables.get("PAPERCLIP_PUBLIC_URL")
        check(public is not None and public.get("Required") == "true" and not (public.text or "").strip(), "Public URL must be filled by the installer.")
        ports = [c for c in configs if c.get("Type") == "Port"]
        check(len(ports) == 1 and ports[0].get("Target") == "3100" and ports[0].get("Mode") == "tcp", "Publish only the application TCP port.")
        paths = [c for c in configs if c.get("Type") == "Path"]
        check(len(paths) == 1 and paths[0].get("Target") == "/paperclip" and paths[0].text == "/mnt/user/appdata/paperclip", "Persist the complete Paperclip home only.")
        check(app.findtext("WebUI") == "http://[IP]:[PORT:3100]", "WebUI must use the mapped application port.")
    if profile is not None:
        check(profile.tag == "CommunityApplications", "Invalid CA profile root.")
        check(bool((profile.findtext("Profile") or "").strip()), "CA Profile must not be empty.")
        check(profile.findtext("WebPage") == REPO, "Wrong profile repository URL.")
    for name in ("README.md", "LICENSE", "LICENSES/Paperclip-MIT.txt", "THIRD-PARTY-NOTICES.md", "assets/paperclip.svg", "docs/CA-SUBMISSION.md", "docs/VALIDATION.md"):
        check((ROOT / name).is_file(), f"Missing required repository file: {name}")
    if (ROOT / "LICENSE").is_file():
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        check("MIT License" in license_text and "agrestisdavid" in license_text, "Missing attributed MIT license.")
    for error in errors:
        print("ERROR:", error, file=sys.stderr)
    if errors:
        return 1
    print("PASS: CA metadata, template URLs, persistent storage, port mapping and secret defaults.")
    print("The official CA portal Validate/Scan and Unraid UI acceptance test remain separate checks.")
    return 0


if __name__ == "__main__":
    sys.exit(validate())
