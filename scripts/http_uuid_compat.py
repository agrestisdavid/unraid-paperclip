#!/usr/bin/env python3
"""Apply or restore a narrowly scoped workaround in a running Paperclip container.

The image is unchanged. Recreation or an image update removes this workaround.
HTTPS is the durable solution; this is only for the tested upstream revision.
"""

import argparse
import json
from pathlib import Path
import subprocess

REVISION = "d554c4789ed3930f8a53ac9fdf6503b3187097da"
MARKER = "paperclip-unraid-http-uuid-v1"

PATCHER = r"""
const fs = require('node:fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const file = '/app/ui/dist/index.html';
const backup = '/paperclip/compat-backups/http-uuid-' + input.revision + '.html';
const original = fs.readFileSync(file, 'utf8');
let result;
if (input.restore) {
  if (!original.includes(input.marker)) {
    console.log('No HTTP UUID workaround is installed.');
    process.exit(0);
  }
  result = fs.readFileSync(backup, 'utf8');
} else {
  if (original.includes(input.marker)) {
    console.log('HTTP UUID workaround is already installed.');
    process.exit(0);
  }
  if (!original.includes('<head>') || !original.includes('type="module"')) {
    throw new Error('Unrecognized Paperclip HTML; no changes made.');
  }
  fs.mkdirSync('/paperclip/compat-backups', {recursive: true, mode: 0o700});
  try { fs.writeFileSync(backup, original, {flag: 'wx', mode: 0o600}); }
  catch (error) {
    if (error.code !== 'EEXIST' || fs.readFileSync(backup, 'utf8') !== original) throw error;
  }
  const script = '<script id="' + input.marker + '">\n' + input.script + '\n</script>';
  result = original.replace('<head>', '<head>\n' + script);
}
const temporary = file + '.http-uuid-' + process.pid;
try {
  fs.writeFileSync(temporary, result, {flag: 'wx', mode: 0o644});
  fs.renameSync(temporary, file);
} finally {
  if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
}
console.log(input.restore ? 'Original HTML restored.' : 'HTTP UUID workaround installed. Reload the browser page.');
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", default="Paperclip-Upstream")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    container = json.loads(subprocess.check_output(["docker", "inspect", args.container], text=True))[0]
    image = json.loads(subprocess.check_output(["docker", "image", "inspect", container["Image"]], text=True))[0]
    revision = image["Config"].get("Labels", {}).get("org.opencontainers.image.revision")
    if revision != REVISION:
        raise SystemExit("Untested upstream revision; no changes made. Use HTTPS or review compatibility first.")
    if not container["State"]["Running"]:
        raise SystemExit("The target container must be running.")
    payload = {"revision": revision, "marker": MARKER, "restore": args.restore,
               "script": Path(__file__).with_name("http_uuid_fallback.js").read_text(encoding="utf-8")}
    subprocess.run(["docker", "exec", "--user", "1000:1000", "-i", args.container,
                    "node", "-e", PATCHER], input=json.dumps(payload), text=True, check=True)


if __name__ == "__main__":
    main()
