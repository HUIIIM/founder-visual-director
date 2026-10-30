#!/usr/bin/env python3
"""Write a CycloneDX 1.5 SBOM for a release of this skill. Zero dependencies.

The skill has no runtime dependencies (demo and checkers use the Python standard library only).
The SBOM therefore lists the skill itself plus the hash-pinned dev tools from requirements-dev.txt,
marked as excluded from the runtime.

Usage: python3 scripts/make_sbom.py VERSION OUTPUT.json
"""

import json
import os
import re
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "founder-visual-director"
REPO_URL = "https://github.com/HUIIIM/founder-visual-director"


def parse_requirements(path):
    """Return [(name, version, [sha256, ...])] from a pip --require-hashes file."""
    with open(path, encoding="utf-8") as f:
        text = f.read().replace("\\\n", " ")
    out = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip() if not line.lstrip().startswith("--") else line.strip()
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;]+)(.*)$", line)
        if m:
            out.append((m.group(1).lower(), m.group(2), re.findall(r"--hash=sha256:([0-9a-f]{64})", m.group(3))))
    return out


def build(version, requirements_path):
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ValueError(f"version must be MAJOR.MINOR.PATCH, got {version!r}")
    components = []
    for name, ver, hashes in parse_requirements(requirements_path):
        components.append(
            {
                "type": "application",
                "name": name,
                "version": ver,
                "purl": f"pkg:pypi/{name}@{ver}",
                "scope": "excluded",
                "description": "Dev tool used in CI only; not shipped or needed at runtime.",
                "hashes": [{"alg": "SHA-256", "content": h} for h in hashes],
            }
        )
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "component": {
                "type": "application",
                "bom-ref": f"{NAME}@{version}",
                "name": NAME,
                "version": version,
                "licenses": [{"license": {"id": "MIT"}}],
                "purl": f"pkg:github/HUIIIM/{NAME}@v{version}",
                "externalReferences": [{"type": "vcs", "url": REPO_URL}],
            },
        },
        "components": components,
    }


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip().splitlines()[-1])
        return 2
    sbom = build(argv[1], os.path.join(ROOT, "requirements-dev.txt"))
    with open(argv[2], "w", encoding="utf-8") as f:
        json.dump(sbom, f, indent=2)
        f.write("\n")
    print(f"SBOM written: {argv[2]} ({len(sbom['components'])} dev components, 0 runtime dependencies)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
