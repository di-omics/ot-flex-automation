"""
Vision backend for SPRI bead-pellet QC.

Two questions the camera answers, mapped to existing protocol pauses:
  is_pellet_cleared(roi) -> bool   # 'wait until clear' on the magnet
  dryness(roi) -> Dryness          # 'air-dry, do NOT over-dry'

Design rules:
  * START ADVISORY. Return state + confidence; the runner logs/alerts and a
    human confirms. Do NOT let this gate an aspirate until it's trusted -- a
    wrong 'cleared' call on the magnet vacuums up the beads.
  * Capture is decoupled from analysis. A FrameSource yields frames; backends
    consume them. Any supported UVC camera can work; a fixed
    mount + controlled lighting matter more than the camera.

OpenCVHeuristicDetector is a deliberately dumb baseline placeholder so the
pipeline wires end to end -- replace it with a trained classifier
(see issue: CV pellet-clear detector).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class Dryness(str, Enum):
    WET = "wet"          # liquid still present
    GLOSSY = "glossy"    # ideal elution window
    MATTE = "matte"      # drying, act soon
    CRACKED = "cracked"  # over-dried -> library loss risk


@dataclass
class WellObservation:
    well: str
    cleared: bool
    dryness: Dryness
    confidence: float  # 0..1
    note: str = ""


@dataclass
class ROI:
    """Pixel box for one well in the fixed camera frame."""
    well: str
    x: int
    y: int
    w: int
    h: int


class FrameSource(ABC):
    @abstractmethod
    def grab(self):
        """Return one frame as an HxWx3 (BGR) array."""
        raise NotImplementedError


class VisionBackend(ABC):
    @abstractmethod
    def observe(self, frame, rois: list[ROI]) -> list[WellObservation]:
        raise NotImplementedError

    def is_pellet_cleared(self, frame, roi: ROI) -> WellObservation:
        return self.observe(frame, [roi])[0]


# ---- stub frame source ---------------------------------------------------
class UvcCamera(FrameSource):  # pragma: no cover
    """Open a supported UVC camera with ``cv2.VideoCapture(device_index)``."""
    def __init__(self, device_index: int = 0):
        self.device_index = device_index

    def grab(self):
        raise NotImplementedError("wire up cv2.VideoCapture(self.device_index)")


# ---- baseline detector (REPLACE with a trained model) --------------------
class OpenCVHeuristicDetector(VisionBackend):  # pragma: no cover
    """Placeholder. Intuition: a cleared well leaves the center brighter /
    lower-variance once beads pull to the magnet side; an over-dried pellet
    shows high edge density. Thresholds here are NOT validated -- they exist
    so the runner has something to call while the real classifier is built."""

    def __init__(self, cleared_var_thresh: float = 120.0,
                 cracked_edge_thresh: float = 0.18):
        self.cleared_var_thresh = cleared_var_thresh
        self.cracked_edge_thresh = cracked_edge_thresh

    def observe(self, frame, rois: list[ROI]) -> list[WellObservation]:
        try:
            import cv2  # noqa: F401
            import numpy as np  # noqa: F401
        except ImportError as e:
            raise ImportError("pip install opencv-python numpy for the vision backend") from e
        # TODO: crop ROI -> features -> trained classifier.
        raise NotImplementedError("baseline detector is a scaffold; see CV issue")


if __name__ == "__main__":
    print("vision scaffold loaded. Implement UvcCamera + a trained detector.")
    print("Dryness states:", [d.value for d in Dryness])
