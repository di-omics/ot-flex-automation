## CV bead-pellet detector (SPRI QC from video)

Build `orchestration/vision/pellet_detector.py`: a camera that tells us when a bead pellet has cleared on the magnet and when it's dried to the right point.

### Maps to these protocol pauses
- "Move plate ONTO the Magnetic Block. Wait until clear" -> `is_pellet_cleared`
- "Air-dry ... do NOT over-dry (glossy/dark)" -> `dryness` (wet / glossy / matte / cracked)

### Scope
- [ ] `FrameSource`: a UVC camera via `cv2.VideoCapture`, with a fixed industrial-camera option for long runs.
- [ ] ROI calibration: map each well to a pixel box on a fixed-mount frame (helper + saved config).
- [ ] Detector: replace the `OpenCVHeuristicDetector` baseline with a trained classifier (collect labeled frames: cleared/not, dry states). Return state + confidence.
- [ ] Document the fixed mount + controlled-lighting rig (repeatability is half the problem).

### Guardrail
**Advisory first.** Emit state + confidence; the runner logs/alerts, a human confirms. Do NOT wire it to gate an aspirate until validated - a false "cleared" loses the beads/sample.

### Done when
From a fixed-mount feed it emits per-well `WellObservation` (cleared bool + dryness + confidence) at the magnet and dry steps, logged with the run.
