import ctypes
from typing import Tuple, Any, Union, Optional

import cv2
import gi
import numpy as np

__all__ = ["CameraReader", "num_cams"]

from cv2 import Mat
from numpy import ndarray, dtype

gi.require_version("Aravis", "0.8")
from gi.repository import Aravis

_FMT_MAP = {  # Pixel‑format → NumPy/OpenCV conversion map
    Aravis.PIXEL_FORMAT_MONO_8: dict(dtype=np.uint8, ch=1, cv_code=None),
    Aravis.PIXEL_FORMAT_MONO_16: dict(dtype=np.uint16, ch=1, cv_code=None),
    Aravis.PIXEL_FORMAT_BAYER_RG_8: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_RG2BGR),
    Aravis.PIXEL_FORMAT_BAYER_GR_8: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_GR2BGR),
    Aravis.PIXEL_FORMAT_BAYER_BG_8: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_BG2BGR),
    Aravis.PIXEL_FORMAT_BAYER_GB_8: dict(dtype=np.uint8, ch=1, cv_code=cv2.COLOR_BAYER_GB2BGR),
    Aravis.PIXEL_FORMAT_RGB_8_PACKED: dict(dtype=np.uint8, ch=3, cv_code=None),
    Aravis.PIXEL_FORMAT_BGR_8_PACKED: dict(dtype=np.uint8, ch=3, cv_code=None),
}


def num_cams():
    return Aravis.get_n_interfaces()


def _numpy_from_buffer(ptr: ctypes.POINTER(ctypes.c_uint8),
                       h: int, w: int, info: dict) -> np.ndarray:  # Helper: safe NumPy view from DMA buffer
    if info["ch"] == 1:
        arr = np.ctypeslib.as_array(ptr, (h, w)).view(info["dtype"])
    else:
        arr = (
            np.ctypeslib.as_array(ptr, (h, w * info["ch"]))
            .view(info["dtype"])
            .reshape(h, w, info["ch"])
        )
    return arr


class CameraReader:
    def __init__(self,
                 cam_id: int | str | None = None,
                 *, n_buffers: int = 12):

        Aravis.update_device_list()  # refresh hot-plug list :contentReference[oaicite:0]{index=0}
        n_dev = Aravis.get_n_devices()
        if n_dev == 0:
            raise RuntimeError("No GenICam camera detected")

        # ---------- resolve cam_id → device-id string ---------- #
        if cam_id is None:
            if n_dev == 1:  # auto-select the only camera
                device_id = Aravis.get_device_id(0)
            else:
                raise RuntimeError("Multiple cameras connected – pass an index or serial substring")
        elif isinstance(cam_id, int):
            if not (0 <= cam_id < n_dev):
                raise RuntimeError(f"Invalid camera index {cam_id}")
            device_id = Aravis.get_device_id(cam_id)
        else:  # cam_id is str  →  match by (sub)string
            cam_id_lc = cam_id.lower()
            # 1) exact & case-insensitive match
            exact = [i for i in range(n_dev)
                     if Aravis.get_device_id(i).lower() == cam_id_lc]
            # 2) fallback: substring match anywhere in the ID
            sub = [i for i in range(n_dev)
                   if cam_id_lc in Aravis.get_device_id(i).lower()]
            hits = exact or sub
            if len(hits) == 1:
                device_id = Aravis.get_device_id(hits[0])
            elif len(hits) == 0:
                raise RuntimeError(f"No camera contains id '{cam_id}'")
            else:
                raise RuntimeError(
                    f"Serial '{cam_id}' matches several cameras: "
                    + ", ".join(Aravis.get_device_id(i) for i in hits))

        # ---------- open device ---------- #
        self._cam: Aravis.Camera = Aravis.Camera.new(device_id)
        self._n_buf = n_buffers
        self._stream: Optional[Aravis.Stream] = None
        self._info = _FMT_MAP.get(self._cam.get_pixel_format())
        if self._info is None:
            raise RuntimeError(
                f"Unsupported pixel format 0x{self._cam.get_pixel_format():08X}"
            )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()

    def start(self):
        try:
            payload = self._cam.get_payload()
            self._stream = self._cam.create_stream(None, None)
            if self._stream is None:
                raise RuntimeError("Failed to create camera stream")

            for _ in range(self._n_buf):
                buffer = Aravis.Buffer.new_allocate(payload)
                if buffer is None:
                    raise RuntimeError("Failed to allocate buffer")
                self._stream.push_buffer(buffer)

            self._cam.start_acquisition()
        except Exception as e:
            self.stop()  # Clean up if there's an error
            raise RuntimeError(f"Failed to start camera: {str(e)}")

    def stop(self):
        if self._cam:
            self._cam.stop_acquisition()
        if self._stream:
            self._stream.pop_buffer()
        self._stream = None

    def get_feature(self, name: str) -> Any:
        """Generic GenICam getter (string → best‑fit python type)."""
        return self._cam.get_feature(name)

    def set_feature(self, name: str, value: Any) -> None:
        """Generic GenICam setter (string, value)."""
        self._cam.set_feature(name, value)

    @property
    def exposure_time(self) -> float:
        """Exposure in *microseconds*."""
        return self._cam.get_exposure_time()

    @exposure_time.setter
    def exposure_time(self, value: float):
        self._cam.set_exposure_time(value)

    @property
    def exposure_auto(self) -> bool:
        return bool(self._cam.get_exposure_time_auto())

    @exposure_auto.setter
    def exposure_auto(self, enable: bool):
        self._cam.set_exposure_time_auto(enable)

    @property
    def gain(self) -> float:
        return self._cam.get_gain()

    @gain.setter
    def gain(self, value: float):
        self._cam.set_gain(value)

    @property
    def gain_auto(self) -> bool:
        return bool(self._cam.get_gain_auto())

    @gain_auto.setter
    def gain_auto(self, enable: bool):
        self._cam.set_gain_auto(enable)

    @property
    def frame_rate(self) -> float:
        return self._cam.get_frame_rate()

    @frame_rate.setter
    def frame_rate(self, hz: float):
        self._cam.set_frame_rate(hz)

    @property
    def pixel_format(self) -> int:
        return self._cam.get_pixel_format()

    @pixel_format.setter
    def pixel_format(self, pix: int):
        self._cam.set_pixel_format(pix)
        # Update conversion map information
        self._info = _FMT_MAP.get(pix) or self._info

    @property
    def region(self) -> Tuple[int, int, int, int]:
        """(x, y, width, height) in sensor pixels."""
        return self._cam.get_region()

    def set_region(self, x: int, y: int, w: int, h: int):
        self._cam.set_region(x, y, w, h)

    @property
    def acquisition_mode(self) -> Aravis.AcquisitionMode:
        return self._cam.get_acquisition_mode()

    @acquisition_mode.setter
    def acquisition_mode(self, mode: Union[Aravis.AcquisitionMode, str]):
        if isinstance(mode, str):
            self._cam.set_acquisition_mode_from_string(mode)
        else:
            self._cam.set_acquisition_mode(mode)

    @property
    def binning(self) -> Tuple[int, int]:
        dx, dy = ctypes.c_int(), ctypes.c_int()
        self._cam.get_binning(ctypes.byref(dx), ctypes.byref(dy))
        return dx.value, dy.value

    def set_binning(self, dx: int = 1, dy: int = 1):
        self._cam.set_binning(dx, dy)

    def read(self, *, jpeg: bool = False, quality: int = 95, timeout_ms = 50) -> bytes | None | ndarray | Mat | ndarray[Any, dtype[Any]]:
        """Retrieve a single frame.

        Parameters
        ----------
        jpeg : bool
            If *True*, returns JPEG‑compressed bytes; otherwise returns a NumPy
            array.
        quality : int
            JPEG quality (1‑100) when *jpeg* is True.
        """
        if self._stream is None:
            raise RuntimeError("Stream not initialized. Call start() before read().")

        buf = self._stream.timeout_pop_buffer(timeout_ms)
        if buf is None or buf.get_status() != Aravis.BufferStatus.SUCCESS:
            return None

        h, w = buf.get_image_height(), buf.get_image_width()
        addr = buf.get_data()
        ptr = ctypes.cast(addr, ctypes.POINTER(ctypes.c_uint8))

        frame = _numpy_from_buffer(ptr, h, w, self._info).copy()
        self._stream.push_buffer(buf)

        if self._info["cv_code"] is not None:
            frame = cv2.cvtColor(frame, self._info["cv_code"])

        if self._info["dtype"] == np.uint16:
            frame = (frame / 256).astype(np.uint8)

        if not jpeg:
            return frame

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        ok, enc = cv2.imencode(
            ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        )
        return enc.tobytes() if ok else None
