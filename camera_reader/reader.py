import ctypes
import os
import platform
import sys
from ctypes import POINTER
from ctypes.util import find_library
from pathlib import Path
from typing import Any, Tuple, Union, Optional

import cv2
import numpy as np

print(f"[DEBUG] Imported aravis-wrapper module (platform={platform.platform()}, cwd={Path().resolve()})", file=sys.stderr)

_SYSTEM = platform.system().lower()
print(f"[DEBUG] Detected platform.system().lower() = {_SYSTEM!r}", file=sys.stderr)

if _SYSTEM == "windows":
    dll_dir = Path(__file__).with_name("aravis_runtime")
    if not dll_dir.is_dir():
        raise RuntimeError(f"Missing DLL folder: {dll_dir}")
    os.add_dll_directory(str(dll_dir))

_SUBDIR = "aravis_runtime"

c_uint = ctypes.c_uint
c_int = ctypes.c_int
c_char_p = ctypes.c_char_p
c_void_p = ctypes.c_void_p


def _candidate_names() -> list[str]:
    if _SYSTEM == "linux":
        return ["libaravis-0.8.so.0", "libaravis-0.8.so", "libaravis.so"]
    if _SYSTEM == "darwin":
        return ["libaravis-0.8.dylib", "libaravis.dylib"]
    if _SYSTEM == "windows":
        return ["libaravis-0.8-0.dll", "aravis-0.8.dll", "aravis-0.dll"]
    raise RuntimeError(f"Unsupported OS {_SYSTEM!r}")


def _find_lib() -> str:
    here = Path(__file__).resolve().parent
    subdir = here / _SUBDIR
    for name in _candidate_names():
        for base in (subdir, here):
            cand = base / name
            if cand.exists():
                return str(cand)
    wildcard = "libaravis*" if _SYSTEM != "windows" else "*aravis*.dll"
    try:
        cand = next(subdir.glob(wildcard))
        return str(cand)
    except StopIteration:
        pass
    found = find_library("aravis-0.8") or find_library("aravis")
    if found:
        return found
    raise RuntimeError(
        "Aravis 0.8 library not found.\n"
        "Expected it in 'aravis_runtime' beside reader.py, or on the system library path."
    )


_lib_path = _find_lib()
print(f"[DEBUG] Loading C library from: {_lib_path}", file=sys.stderr)
_LIB = ctypes.CDLL(_lib_path)

_LIB.arv_update_device_list.restype = None
_LIB.arv_get_n_devices.restype = c_uint
_LIB.arv_get_device_id.restype = c_char_p
ArvCamera = c_void_p
ArvBuffer = c_void_p
ArvStream = c_void_p
_LIB.arv_camera_new.restype = ArvCamera
_LIB.arv_camera_new.argtypes = [c_char_p, c_void_p]
_LIB.arv_camera_get_pixel_format.restype = c_uint
_LIB.arv_camera_set_pixel_format.argtypes = [ArvCamera, c_uint]
_LIB.arv_camera_get_payload.restype = c_uint
_LIB.arv_camera_create_stream.restype = ArvStream
_LIB.arv_camera_create_stream.argtypes = [ArvCamera, c_void_p, c_void_p]
_LIB.arv_camera_start_acquisition.argtypes = [ArvCamera]
_LIB.arv_camera_stop_acquisition.argtypes = [ArvCamera]
_LIB.arv_camera_get_exposure_time.restype = ctypes.c_double
_LIB.arv_camera_set_exposure_time.argtypes = [ArvCamera, ctypes.c_double]
_LIB.arv_camera_get_gain.restype = ctypes.c_double
_LIB.arv_camera_set_gain.argtypes = [ArvCamera, ctypes.c_double]
_LIB.arv_camera_get_frame_rate.restype = ctypes.c_double
_LIB.arv_camera_set_frame_rate.argtypes = [ArvCamera, ctypes.c_double]
_LIB.arv_stream_push_buffer.argtypes = [ArvStream, ArvBuffer]
_LIB.arv_stream_timeout_pop_buffer.restype = ArvBuffer
_LIB.arv_stream_timeout_pop_buffer.argtypes = [ArvStream, c_uint]
_LIB.arv_stream_pop_buffer.restype = ArvBuffer
_LIB.arv_stream_pop_buffer.argtypes = [ArvStream]
_LIB.arv_buffer_new_allocate.restype = ArvBuffer
_LIB.arv_buffer_new_allocate.argtypes = [c_uint]
_LIB.arv_camera_get_pixel_format.argtypes = [ArvCamera]
_LIB.arv_camera_get_payload.argtypes = [ArvCamera]
_LIB.arv_buffer_get_status.argtypes = [ArvBuffer]
_LIB.arv_buffer_get_image_width.argtypes = [ArvBuffer]
_LIB.arv_buffer_get_image_height.argtypes = [ArvBuffer]
_LIB.arv_buffer_get_data.argtypes = [ArvBuffer]
_LIB.arv_buffer_get_status.restype = c_int
_LIB.arv_buffer_get_image_width.restype = c_int
_LIB.arv_buffer_get_image_height.restype = c_int
_LIB.arv_buffer_get_data.restype = c_void_p

PF = {
    "MONO_8": 0x01080001,
    "MONO_16": 0x01100007,
    "BAYER_RG_8": 0x01080009,
    "BAYER_GR_8": 0x0108000A,
    "BAYER_BG_8": 0x0108000B,
    "BAYER_GB_8": 0x0108000C,
    "RGB_8_PACKED": 0x02180014,
    "BGR_8_PACKED": 0x02180015,
}
_FMT_MAP = {
    PF["MONO_8"]: dict(dtype=np.uint8, ch=1, cv_code=None),
    PF["MONO_16"]: dict(dtype=np.uint16, ch=1, cv_code=None),
    PF["BAYER_RG_8"]: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_RG2BGR),
    PF["BAYER_GR_8"]: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_GR2BGR),
    PF["BAYER_BG_8"]: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_BG2BGR),
    PF["BAYER_GB_8"]: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_GB2BGR),
    PF["RGB_8_PACKED"]: dict(dtype=np.uint8, ch=3, cv_code=None),
    PF["BGR_8_PACKED"]: dict(dtype=np.uint8, ch=3, cv_code=None),
}


def num_cams() -> int:
    _LIB.arv_update_device_list()
    return _LIB.arv_get_n_devices()


def _numpy_from_buffer(ptr: POINTER(ctypes.c_uint8), h: int, w: int, info: dict) -> np.ndarray:
    if info["ch"] == 1:
        arr = np.ctypeslib.as_array(ptr, shape=(h, w)).view(info["dtype"])
    else:
        arr = np.ctypeslib.as_array(ptr, shape=(h, w * info["ch"])).view(info["dtype"]).reshape(h, w, info["ch"])
    return arr


class CameraReader:
    def __init__(self, cam_id: Union[int, str, None] = None, *, n_buffers: int = 3):
        _LIB.arv_update_device_list()
        n_dev = _LIB.arv_get_n_devices()
        if n_dev == 0:
            raise RuntimeError("No GenICam camera detected")
        if cam_id is None:
            if n_dev == 1:
                raw_id = _LIB.arv_get_device_id(0)
                device_id = raw_id.decode("utf-8")
            else:
                raise RuntimeError("Multiple cameras connected – pass an index or serial substring")
        elif isinstance(cam_id, int):
            if not (0 <= cam_id < n_dev):
                raise RuntimeError(f"Invalid camera index {cam_id}")
            raw_id = _LIB.arv_get_device_id(cam_id)
            device_id = raw_id.decode("utf-8")
        else:
            cam_id_lc = cam_id.lower()
            exact_hits = []
            substr_hits = []
            for i in range(n_dev):
                raw = _LIB.arv_get_device_id(i)
                text = raw.decode("utf-8")
                if text.lower() == cam_id_lc:
                    exact_hits.append((i, text))
                elif cam_id_lc in text.lower():
                    substr_hits.append((i, text))
            hits = exact_hits if exact_hits else substr_hits
            if len(hits) == 1:
                device_id = hits[0][1]
            elif len(hits) == 0:
                raise RuntimeError(f"No camera contains id '{cam_id}'")
            else:
                multiples = ", ".join(t for (_, t) in hits)
                raise RuntimeError(f"Serial '{cam_id}' matches several cameras: {multiples}")
        device_id_bytes = device_id.encode("utf-8")
        self._cam: ArvCamera = _LIB.arv_camera_new(device_id_bytes, None)
        if not self._cam:
            raise RuntimeError(f"Failed to open camera with ID '{device_id}'")
        self._n_buf = n_buffers
        self._stream: Optional[ArvStream] = None
        pix = _LIB.arv_camera_get_pixel_format(self._cam)
        self._info = _FMT_MAP.get(pix)
        if self._info is None:
            raise RuntimeError(f"Unsupported pixel format 0x{pix:08X}")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

    def start(self):
        payload = _LIB.arv_camera_get_payload(self._cam)
        self._stream = _LIB.arv_camera_create_stream(self._cam, None, None)
        if not self._stream:
            raise RuntimeError("Failed to create camera stream")
        for _ in range(self._n_buf):
            buf = _LIB.arv_buffer_new_allocate(payload)
            _LIB.arv_stream_push_buffer(self._stream, buf)
        _LIB.arv_camera_start_acquisition(self._cam)

    def stop(self):
        if hasattr(self, "_cam") and self._cam:
            _LIB.arv_camera_stop_acquisition(self._cam)
        if hasattr(self, "_stream") and self._stream:
            _LIB.arv_stream_pop_buffer(self._stream)
        self._stream = None
        self._cam = None

    def read(self, *, jpeg: bool = False, quality: int = 95, timeout_ms: int = 100) -> Union[bytes, None, np.ndarray]:
        if not self._stream:
            raise RuntimeError("Stream not initialized. Call start() before read().")
        buf = _LIB.arv_stream_timeout_pop_buffer(self._stream, c_uint(timeout_ms))
        if not buf:
            return None
        status = _LIB.arv_buffer_get_status(buf)
        if status != 0:
            _LIB.arv_stream_push_buffer(self._stream, buf)
            return None
        h = _LIB.arv_buffer_get_image_height(buf)
        w = _LIB.arv_buffer_get_image_width(buf)
        addr = _LIB.arv_buffer_get_data(buf)
        ptr = ctypes.cast(addr, POINTER(ctypes.c_uint8))
        frame = _numpy_from_buffer(ptr, h, w, self._info)
        _LIB.arv_stream_push_buffer(self._stream, buf)
        if self._info["cv_code"] is not None:
            frame = cv2.cvtColor(frame, self._info["cv_code"])
        if self._info["dtype"] == np.uint16:
            frame = (frame // 256).astype(np.uint8)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        if not jpeg:
            return frame
        ok, enc = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return enc.tobytes() if ok else None
