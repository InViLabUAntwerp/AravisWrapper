from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__.replace('_', '-'))
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

from .reader import num_cams, CameraReader
from .genicam_camera import GenICamCamera
from .opencv_camera import OpenCVCamera

__all__ = ["num_cams", "CameraReader", "GenICamCamera", "OpenCVCamera"]
