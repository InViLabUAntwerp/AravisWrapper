#!/usr/bin/env python3
"""
Copy the shared libraries and typelibs collected in camera_reader/_vendor/…
into backend/toolbox/GenICam/aravis_runtime.
On Windows the GLib DLLs are renamed to the ABI-encoded names Aravis expects.
"""

from __future__ import annotations
import platform, shutil, sys
from pathlib import Path

_DEST_DIR = Path("backend/toolbox/GenICam/aravis_runtime")

_WIN_RENAMES = {
    "glib-2.0.dll":    "libglib-2.0-0.dll",
    "gobject-2.0.dll": "libgobject-2.0-0.dll",
    "gthread-2.0.dll": "libgthread-2.0-0.dll",
    "gmodule-2.0.dll": "libgmodule-2.0-0.dll",
    "gio-2.0.dll":     "libgio-2.0-0.dll",
}

_EXTS = {
    "Windows": {".dll", ".typelib"},
    "Darwin":  {".dylib", ".typelib"},
    "Linux":   {".so", ".typelib"},
}

def _vendor_root() -> Path:
    sysname = platform.system()
    arch = platform.machine()
    if sysname == "Windows":
        return Path(f"camera_reader/_vendor/win_{'arm64' if arch.startswith(('arm64', 'aarch64')) else 'amd64'}")
    if sysname == "Darwin":
        return Path(f"camera_reader/_vendor/macosx_{'arm64' if arch == 'arm64' else 'x86_64'}")
    if sysname == "Linux":
        return Path(f"camera_reader/_vendor/linux_{'aarch64' if arch.startswith(('arm64', 'aarch64')) else 'x86_64'}")
    sys.exit(f"Unsupported OS: {sysname}")

def _wanted(p: Path, exts: set[str], sysname: str) -> bool:
    if p.suffix.lower() in exts:
        return True
    return sysname == "Linux" and ".so." in p.name

def main() -> None:
    sysname = platform.system()
    src_root = _vendor_root()
    if not src_root.exists():
        sys.exit(f"Vendor directory {src_root} not found – run the GitHub Actions seed job or vendor manually")

    _DEST_DIR.mkdir(parents=True, exist_ok=True)
    exts = _EXTS[sysname]
    copied = 0

    for lib in src_root.rglob("*"):
        if not _wanted(lib, exts, sysname):
            continue
        dest_name = _WIN_RENAMES.get(lib.name.lower(), lib.name) if sysname == "Windows" else lib.name
        shutil.copy2(lib, _DEST_DIR / dest_name, follow_symlinks=(sysname == "Windows"))
        copied += 1

    print(f"✅  Copied {copied} shared libraries for {sysname} → {_DEST_DIR.resolve()}")

if __name__ == "__main__":
    main()
