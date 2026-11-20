"""Download a pinned source revision and build the Windows x64 engine locally.

Requires: python -m pip install ziglang==0.16.0
Run from any directory: python scripts/build_engine.py
"""

import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "d3290a8f421863b737ae7c31ad3d800b4fc584c7"
URL = f"https://codeload.github.com/xpple/cubiomes/zip/{COMMIT}"


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("El binario de esta primera etapa requiere Windows x64.")
    build = ROOT / ".qa" / "engine-build"
    build.mkdir(parents=True, exist_ok=True)
    source = build / f"cubiomes-{COMMIT}"
    if not source.exists():
        archive = build / "source.zip"
        urllib.request.urlretrieve(URL, archive)
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(build)
    cmake = (source / "CMakeLists.txt").read_text(encoding="utf-8")
    source_block = cmake.split("set(SOURCES", 1)[1].split(")", 1)[0]
    sources = [str(source / path) for path in re.findall(r"[\w/]+\.c", source_block)]
    output = ROOT / "mc_finder" / "_native"
    output.mkdir(parents=True, exist_ok=True)
    target = output / "finder.dll"
    command = [
        sys.executable, "-m", "ziglang", "cc", "-target", "x86_64-windows-gnu",
        "-shared", "-O2", "-fwrapv", "-fno-strict-aliasing", "-D_WIN32",
        "-I", str(source), str(ROOT / "native" / "bridge.c"), *sources,
        "-o", str(target),
    ]
    subprocess.run(command, check=True, cwd=build)
    cjson_source = (source / "loot" / "cjson" / "cJSON.c").read_text(encoding="utf-8")
    (output / "LICENSE_cJSON.txt").write_text(cjson_source.split("*/", 1)[0] + "*/\n", encoding="utf-8")
    for license_path in source.rglob("*"):
        if license_path.is_file() and "license" in license_path.name.lower():
            relative = license_path.relative_to(source).as_posix().replace("/", "_")
            shutil.copyfile(license_path, output / relative)
    manifest = {
        "repository": "https://github.com/xpple/cubiomes", "commit": COMMIT,
        "source_archive_sha256": hashlib.sha256((build / "source.zip").read_bytes()).hexdigest(),
        "minecraft": "26.3", "abi": 1, "platform": "windows-x64",
        "binary_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        "compiler": "ziglang 0.16.0 (zig cc)",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Motor compilado: {target}")


if __name__ == "__main__":
    main()
