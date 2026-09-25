#!/usr/bin/env python3
"""Exercise the actual template using an isolated Linux Docker container and volume."""

from datetime import datetime, timezone
import http.client
import http.cookiejar
import json
from pathlib import Path
import re
import secrets
import shlex
import socket
import subprocess
import time
import urllib.error
import urllib.request
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "test-results/smoke.json"


class LoopbackConnection(http.client.HTTPConnection):
    """Route the reserved test hostname locally without changing system DNS."""

    def connect(self):
        self.sock = socket.create_connection(("127.0.0.1", self.port), self.timeout)


class LoopbackHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(LoopbackConnection, req)


def docker(*args, timeout=120):
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        # Do not print the command: docker run arguments contain generated test secrets.
        raise RuntimeError(f"docker {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def main():
    if docker("info", "--format", "{{.OSType}}") != "linux":
        raise RuntimeError("The smoke test requires a Linux Docker engine.")
    app = ET.parse(ROOT / "templates/paperclip.xml").getroot()
    image = app.findtext("Repository")
    name = "unraid-paperclip-smoke-" + uuid.uuid4().hex[:12]
    volume = name + "-data"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    # Exercise a LAN-style origin: upstream rewrites localhost URL ports to
    # its internal listen port, which is unsuitable for a remapped Docker port.
    base = f"http://paperclip-smoke.test:{port}"
    environment = {c.get("Target"): (c.text or c.get("Default", "")) for c in app.findall("Config") if c.get("Type") == "Variable"}
    environment.update(PAPERCLIP_PUBLIC_URL=base, BETTER_AUTH_SECRET=secrets.token_hex(32), PAPERCLIP_TOOL_ACTION_SIGNING_SECRET=secrets.token_hex(32))
    password = secrets.token_urlsafe(32)
    email = "smoke-test@example.com"
    cookies = http.cookiejar.CookieJar()
    client = urllib.request.build_opener(LoopbackHandler(), urllib.request.HTTPCookieProcessor(cookies), urllib.request.ProxyHandler({}))
    anonymous = urllib.request.build_opener(LoopbackHandler(), urllib.request.ProxyHandler({}))
    report = {"startedAt": datetime.now(timezone.utc).isoformat(), "image": image, "checks": [], "success": False}
    volume_created = False

    def request(path, data=None, authenticated=True):
        headers = {"Origin": base, "Accept": "application/json"}
        payload = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(data).encode()
        req = urllib.request.Request(base + path, data=payload, headers=headers)
        try:
            response = (client if authenticated else anonymous).open(req, timeout=15)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            raw = response.read().decode()
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = raw
            return response.code, body

    def check(condition, label):
        if not condition:
            raise AssertionError(label)
        report["checks"].append(label)
        print("PASS:", label, flush=True)

    def ready():
        deadline = time.monotonic() + 300
        last = "not yet reachable"
        while time.monotonic() < deadline:
            try:
                status, health = request("/api/health", authenticated=False)
                if status == 200 and isinstance(health, dict):
                    return health
                last = f"HTTP {status}"
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                last = type(exc).__name__
            if docker("inspect", "--format", "{{.State.Running}}", name) != "true":
                raise RuntimeError("Container exited before the API became ready.")
            time.sleep(2)
        raise RuntimeError("API did not become ready: " + last)

    def start():
        command = ["run", "-d", "--name", name, "--label", "io.github.agrestisdavid.unraid-paperclip.smoke=true", "--network", app.findtext("Network")]
        command += shlex.split(app.findtext("ExtraParams", ""))
        for key, value in environment.items():
            command += ["-e", f"{key}={value}"]
        command += ["-p", f"127.0.0.1:{port}:3100", "--mount", f"type=volume,src={volume},dst=/paperclip", report["imageId"]]
        docker(*command)
        return ready()

    def company_present(company_id):
        status, companies = request("/api/companies")
        return status == 200 and isinstance(companies, list) and any(c.get("id") == company_id for c in companies)

    try:
        print("Pulling", image, flush=True)
        docker("pull", image, timeout=600)
        metadata = json.loads(docker("image", "inspect", image))[0]
        report.update(imageId=metadata["Id"], repoDigests=metadata.get("RepoDigests", []), architecture=metadata.get("Architecture"), sourceRevision=metadata.get("Config", {}).get("Labels", {}).get("org.opencontainers.image.revision"))
        print("Image:", json.dumps({k: report[k] for k in ("repoDigests", "architecture", "sourceRevision")}), flush=True)
        docker("volume", "create", "--label", "io.github.agrestisdavid.unraid-paperclip.smoke=true", volume)
        volume_created = True
        health = start()
        check(health.get("deploymentMode") == "authenticated", "Authenticated startup using the XML settings")
        status, body = request("/", authenticated=False)
        check(status == 200 and isinstance(body, str) and "<html" in body.lower(), "Dashboard HTML is served")
        status, _ = request("/api/companies", authenticated=False)
        check(status in (401, 403), "Anonymous access to company data is denied")
        ownership = docker("exec", name, "node", "-e", "const s=require('fs').statSync('/paperclip');console.log(s.uid+':'+s.gid)")
        check(ownership == environment["USER_UID"] + ":" + environment["USER_GID"], "Fresh persistent storage receives the configured UID/GID")
        process_uid = docker("exec", name, "node", "-e", r"const fs=require('fs');for(const p of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))){try{const a=fs.readFileSync('/proc/'+p+'/cmdline','utf8').split('\0');if(a[0].split('/').pop()==='node' && a.includes('server/dist/index.js')){const s=fs.readFileSync('/proc/'+p+'/status','utf8');console.log(s.match(/^Uid:\s+(\d+)/m)[1]);}}catch{}}")
        check(process_uid.strip() == environment["USER_UID"], "Application process runs as the configured non-root user")
        status, signup = request("/api/auth/sign-up/email", {"name": "Template Smoke Test", "email": email, "password": password})
        if status not in (200, 201):
            raise RuntimeError(f"Sign-up HTTP {status}: {signup}")
        check(True, "First account can sign up")
        status, claim = request("/api/bootstrap/claim", {})
        check(status == 200 and isinstance(claim, dict) and claim.get("claimed") is True, "Private deployment supports browser first-admin claim")
        status, company = request("/api/companies", {"name": "Unraid template smoke test"})
        check(status in (200, 201) and isinstance(company, dict) and bool(company.get("id")), "Authenticated administrator can create a company")
        company_id = company["id"]
        docker("restart", "--time", "60", name)
        ready()
        check(company_present(company_id), "Account session and company persist across restart")
        docker("stop", "--time", "60", name)
        docker("rm", name)
        start()
        check(company_present(company_id), "Account session and company persist across container recreation")
        cookies.clear()
        status, _ = request("/api/auth/sign-in/email", {"email": email, "password": password})
        check(status == 200 and company_present(company_id), "Fresh login works against the persisted database")
        report["success"] = True
    except Exception as exc:
        report["error"] = str(exc)
        try:
            logs = docker("logs", "--tail", "100", name)
            for secret in (password, environment["BETTER_AUTH_SECRET"], environment["PAPERCLIP_TOOL_ACTION_SIGNING_SECRET"]):
                logs = logs.replace(secret, "[redacted]")
            logs = re.sub(r"https?://\S*(?:invite|claim)\S*", "[redacted setup URL]", logs)
            print(logs, flush=True)
        except Exception:
            pass
        raise
    finally:
        cleanup_errors = []
        # Names are generated here; no pre-existing container or data path is targeted.
        try:
            exists = docker("ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.Names}}")
            if exists == name:
                docker("rm", "-f", name)
        except Exception as exc:
            cleanup_errors.append(str(exc))
        if volume_created:
            try:
                docker("volume", "rm", volume)
            except Exception as exc:
                cleanup_errors.append(str(exc))
        report["cleanupErrors"] = cleanup_errors
        report["finishedAt"] = datetime.now(timezone.utc).isoformat()
        if cleanup_errors:
            report["success"] = False
        RESULT.parent.mkdir(exist_ok=True)
        RESULT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if cleanup_errors:
            raise RuntimeError("Could not clean up test resources: " + "; ".join(cleanup_errors))
    print("PASS: isolated smoke test complete; test container and data volume removed.", flush=True)


if __name__ == "__main__":
    main()
