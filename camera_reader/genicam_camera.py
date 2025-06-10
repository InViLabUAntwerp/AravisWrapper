import numpy as np

from .reader import CameraReader


class GenICamCamera:
    """Adapter exposing Open / Start / GetFrame / SetParameterDouble / Stop / Close."""

    def __init__(self,
                 _ignored: str | None = None,
                 *, cam_id: int | str | None = None,
                 n_buffers: int = 12):
        self._cam_id = cam_id
        self._n_buf = n_buffers
        self._reader = None
        self._running = False

    def Open(self, address: str | None = None) -> None:
        if self._reader:
            return
        # prefer explicit address passed at runtime,
        # fall back to the ctor-level cam_id
        chosen_id = address if address is not None else self._cam_id
        self._reader = CameraReader(chosen_id, n_buffers=self._n_buf)
        self._reader.start()
        self._running = True

    def Start(self) -> None:
        if not self._reader:
            self.Open()
        if not self._running:
            self._reader.start()
            self._running = True

    def Stop(self) -> None:
        if self._reader and self._running:
            self._reader.stop()
            self._running = False

    def GetFrame(self) -> np.ndarray:
        if not self._reader:
            raise RuntimeError("Camera not opened")
        if not self._running:
            raise RuntimeError("Camera not started")

        while True:  # Keep trying until we get a frame
            try:
                frame = self._reader.read()
                if frame is not None:
                    return np.array(frame)
                # If frame is None, continue the loop to try again
            except Exception as e:
                if "Stream not initialized" in str(e):
                    # Try to restart the stream
                    self.Stop()
                    self._reader.start()
                    self._running = True
                    frame = self._reader.read()
                    if frame is not None:
                        return np.array(frame)
                    # If still None after restart, continue the loop
                else:
                    # Re-raise any non-timeout errors
                    raise

    def SetParameterDouble(self, name: str, value: float) -> None:
        if not self._reader:
            raise RuntimeError("Camera not opened")
        if name == "ExposureTime":
            self._reader.exposure_time = value
        elif name == "Gain":
            self._reader.gain = value
        else:
            self._reader.set_feature(name, value)

    def Close(self) -> None:
        self.Stop()
        self._reader = None
