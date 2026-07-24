# Closed-loop QC orchestration

This package adds sensing and decision support around deterministic Opentrons
protocols. A normal `run()` is planned before execution and cannot branch on a
live measurement, so the plate-reader, camera, and run-control components operate
outside the protocol.

```text
protocols/*.py              deterministic liquid handling
       |
       v
orchestration/
  instruments/plate_reader.py   fluorescence result -> concentration
  vision/pellet_detector.py     camera frame -> bead state
  decisions.py                  measurement -> action
  flex_link.py                  resume or pause a run
```

## Modules

| File | Purpose | State |
|---|---|---|
| `decisions.py` | Concentration thresholds, cycle top-ups, and retention decisions | Implemented |
| `instruments/plate_reader.py` | CSV fluorescence result to `{well: ng/uL}` | CSV adapter implemented |
| `flex_link.py` | External run-control link | Resume and pause implemented |
| `vision/pellet_detector.py` | Camera interface for bead clearance and dryness | Interface and baseline scaffold |
| `run_qc_loop.py` | TIP-seq pre-cleanup QC example | Runnable in dry-run mode |

## Try it

```bash
python -m orchestration.run_qc_loop --dry-run
```

The example reads the bundled CSV, evaluates each well, and prints the robot
calls it would make.

## Development tracks

1. Complete the CSV plate-reader path, including well mapping and partial-file
   protection.
2. Train and validate the bead-pellet classifier with a fixed camera mount and
   controlled lighting.
3. Split PCR and cleanup stages into launchable segments so the orchestrator can
   request a cycle top-up.

Keep image-based and fluorescence-based control advisory until it agrees with a
validated manual reference. A false clearance call can irreversibly remove beads
and sample.

Optional dependencies are listed in `requirements.txt`.
