import os
import platform
from importlib import resources


def _load_native():
    sysname = platform.system().lower()
    arch = platform.machine().lower()
    key_map = {
        ("linux", "x86_64"): "linux_x86_64",
        ("linux", "aarch64"): "linux_arm64",
        ("darwin", "x86_64"): "macosx_x86_64",
        ("darwin", "arm64"): "macosx_arm64",
        ("windows", "amd64"): "win_amd64",
        ("windows", "arm64"): "win_arm64",
    }
    key = key_map.get((sysname, arch))
    if not key:
        raise OSError(f"Unsupported platform {sysname}/{arch}")

    vendor_dir = resources.files("camera_reader") / "_vendor" / key
    path = str(vendor_dir)

    if sysname == "linux":
        os.environ["LD_LIBRARY_PATH"] = f"{path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
    elif sysname == "darwin":
        os.environ["DYLD_LIBRARY_PATH"] = f"{path}:{os.environ.get('DYLD_LIBRARY_PATH', '')}"
    elif sysname == "windows":
        os.environ["PATH"] = f"{path};{os.environ.get('PATH', '')}"

    os.environ["GI_TYPELIB_PATH"] = f"{path}:{os.environ.get('GI_TYPELIB_PATH', '')}"


_load_native()

from .reader import CameraReader, num_cams
