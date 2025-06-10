import cv2
import numpy as np
from typing import Union


class OpenCVCamera:
    def __init__(self, _ignored: str | None = None, *, cam_id: Union[int, str, None] = None, n_buffers: int = 1):
        self._cam_id = cam_id
        self._n_buf = n_buffers
        self._capture: cv2.VideoCapture | None = None
        self._running: bool = False

    def _create_capture(self, src: Union[int, str]):
        cap = cv2.VideoCapture(src)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera/device: {src!r}")
        return cap

    def Open(self, address: Union[int, str, None] = None) -> None:
        if self._capture is not None:
            return
        chosen_id = address if address is not None else self._cam_id
        if isinstance(chosen_id, str) and chosen_id.isdigit():
            chosen_id = int(chosen_id)
        if chosen_id is None:
            chosen_id = 0
        self._capture = self._create_capture(chosen_id)
        self._running = True

    def Start(self) -> None:
        if self._capture is None:
            self.Open()
        self._running = True

    def Stop(self) -> None:
        self._running = False

    def GetFrame(self) -> np.ndarray:
        if self._capture is None:
            raise RuntimeError("Camera not opened")
        if not self._running:
            raise RuntimeError("Camera not started")
        while True:
            ret, frame_bgr = self._capture.read()
            if not ret or frame_bgr is None:
                continue
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            return frame_rgb

    def SetParameterDouble(self, name: str, value: float) -> None:
        if self._capture is None:
            raise RuntimeError("Camera not opened")
        key = name.lower()
        if key in {"exposuretime", "exposure"}:
            self._capture.set(cv2.CAP_PROP_EXPOSURE, float(value))
        elif key == "gain":
            self._capture.set(cv2.CAP_PROP_GAIN, float(value))
        else:
            prop_id = getattr(cv2, f"CAP_PROP_{name.upper()}", None)
            if prop_id is None:
                raise ValueError(f"Unsupported parameter: {name}")
            self._capture.set(prop_id, float(value))

    def Close(self) -> None:
        self.Stop()
        if self._capture is not None:
            self._capture.release()
        self._capture = None

    def __del__(self):
        try:
            self.Close()
        except Exception:
            pass
