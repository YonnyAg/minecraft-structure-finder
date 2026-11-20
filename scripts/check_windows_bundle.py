"""Extract the release ZIP and test its EXE with Python removed from PATH."""

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pefile

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    archives = sorted((ROOT / "dist").glob("MinecraftStructureFinder-v*-windows-x64.zip"))
    if len(archives) != 1:
        raise SystemExit("Expected one versioned ZIP in dist/.")
    archive = archives[0]
    checksum = archive.with_suffix(".sha256").read_text(encoding="ascii").split()[0]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == checksum
    destination = ROOT / ".qa" / "prueba portable sin Python"
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        bundle.extractall(destination)
    application = destination / "MinecraftStructureFinder"
    executable = application / "MinecraftStructureFinder.exe"
    with pefile.PE(str(executable)) as binary:
        assert binary.FILE_HEADER.Machine == 0x8664, "Not a Windows x64 executable"
        assert binary.OPTIONAL_HEADER.Subsystem == 2, "Executable would open a console"
    assert (application / "_internal" / "python311.dll").is_file()
    engine = application / "_internal" / "mc_finder" / "_native"
    manifest = json.loads((engine / "manifest.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((engine / "finder.dll").read_bytes()).hexdigest() == manifest["binary_sha256"]
    assert (application / "LICENSES" / "Qt-LGPL-3.0.txt").is_file()
    report_path = ROOT / ".qa" / "windows-frozen-smoke.json"
    report_path.unlink(missing_ok=True)
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    system_root = next((value for key, value in env.items() if key.lower() == "systemroot"), r"C:\Windows")
    env["PATH"] = str(Path(system_root) / "System32")
    env["QT_QPA_PLATFORM"] = "windows"
    result = subprocess.run([str(executable), "--self-test-report", str(report_path)],
                            cwd=destination, env=env, timeout=90, capture_output=True)
    if not report_path.exists():
        raise SystemExit(f"EXE did not produce a report (exit {result.returncode}).")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert result.returncode == 0 and report["ok"] and report["frozen"], report
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
