"""Build a portable, windowed Windows-x64 ZIP. Run in the build environment."""

import hashlib
import json
import platform
import shutil
import struct
import subprocess
import sys
import tomllib
import zipfile
from importlib.metadata import distribution
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "MinecraftStructureFinder"


def main() -> None:
    if sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64") or struct.calcsize("P") != 8:
        raise SystemExit("Build with Windows and Python x64.")
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    native = ROOT / "mc_finder" / "_native"
    manifest = json.loads((native / "manifest.json").read_text(encoding="utf-8"))
    if hashlib.sha256((native / "finder.dll").read_bytes()).hexdigest() != manifest["binary_sha256"]:
        raise SystemExit("The native engine hash does not match its manifest.")
    # Both output trees are fixed children of the workspace. PyInstaller replaces
    # only its own generated bundle, never source or user-selected directories.
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm",
                    "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
                    str(ROOT / "packaging" / "windows.spec")], check=True, cwd=ROOT)
    bundle = ROOT / "dist" / NAME
    licenses = bundle / "LICENSES"
    licenses.mkdir(exist_ok=True)
    shutil.copyfile(Path(sys.base_prefix) / "LICENSE.txt", licenses / "Python-LICENSE.txt")
    for license_file in (ROOT / "packaging" / "licenses").iterdir():
        shutil.copyfile(license_file, licenses / license_file.name)
    for name in ("PySide6", "PySide6_Essentials", "shiboken6"):
        dist = distribution(name)
        for path in dist.files or []:
            if "license" in path.name.lower() or "copying" in path.name.lower():
                shutil.copyfile(dist.locate_file(path), licenses / f"{name}-{path.name}")
    for path in native.iterdir():
        if "license" in path.name.lower():
            shutil.copyfile(path, licenses / f"Cubiomes-{path.name}")
    versions = {name: distribution(name).version for name in ("PySide6", "shiboken6", "pyinstaller")}
    (bundle / "LEEME.txt").write_text(
        f"Minecraft Structure Finder {version} — Windows x64\n\n"
        "1. Extrae TODO el ZIP en una carpeta.\n"
        "2. Abre MinecraftStructureFinder.exe con doble clic.\n"
        "No necesitas instalar Python, abrir una consola ni instalar mods.\n"
        "Conserva la carpeta _internal junto al EXE; contiene las dependencias.\n\n"
        "Prueba: Cargar ejemplo > Buscar estructuras. Cabaña esperada: X -2368, Z 656.\n"
        "Grupos: cantidad 2, radio 200; con el área del ejemplo aparecen 3 grupos.\n"
        "Compatible con generación estándar de Minecraft Java 26.3, cabañas de brujas del Overworld.\n"
        "Los centros y perímetros son referencias; no certifican un punto AFK ni rendimiento máximo.\n\n"
        "Proyecto e instrucciones: https://github.com/YonnyAg/minecraft-structure-finder\n"
        "Licencias y componentes: LICENSES y THIRD_PARTY_NOTICES.txt.\n",
        encoding="utf-8-sig")
    (bundle / "THIRD_PARTY_NOTICES.txt").write_text(
        "This application includes unmodified third-party components.\n"
        f"Python {platform.python_version()} — PSF license (LICENSES/Python-LICENSE.txt).\n"
        f"PySide6 / Shiboken {versions['PySide6']} and Qt 6.8.3 — LGPLv3 distribution option.\n"
        "License texts are in LICENSES; shared Qt/PySide libraries remain separate in _internal.\n"
        "These libraries may be replaced with compatible modified builds under their licenses.\n"
        "Qt and Python-for-Qt sources for this version:\n"
        "https://download.qt.io/archive/qt/6.8/6.8.3/single/\n"
        "https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.8.3-src/\n"
        "Cubiomes by Cubitect, fork maintained by xpple — MIT; includes cJSON and loot notices.\n"
        f"Engine source: https://github.com/xpple/cubiomes/tree/{manifest['commit']}\n"
        f"Bundled using PyInstaller {versions['pyinstaller']} (bootloader distribution exception).\n",
        encoding="utf-8")
    (bundle / "build-info.json").write_text(json.dumps({"version": version, "platform": "windows-x64",
        "python": platform.python_version(), "dependencies": versions, "engine": manifest["commit"],
        "format": "portable-folder", "console": False}, indent=2), encoding="utf-8")
    archive = ROOT / "dist" / f"{NAME}-v{version}-windows-x64.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                output.write(path, path.relative_to(bundle.parent))
    checksum = archive.with_suffix(".sha256")
    checksum.write_text(f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n", encoding="ascii")
    print(f"ZIP: {archive}\nSHA256: {checksum}")


if __name__ == "__main__":
    main()
