# orchestration – closed-loop QC for ot-flex-automation

Scaffolding for sensing-in-the-loop on top of the deterministic protocols. This is where computer vision (bead-pellet QC) and a fluorescence plate reader (Qubit-replacement QC) plug in.

## The key idea

A normal `run()` protocol – every file in `protocols/` – is planned and simulated up front, then executed deterministically. It **can't branch on a live sensor reading**. So anything that reacts to "what does the camera see" or "what did the plate reader measure" runs from *outside* that flow: over the Flex **HTTP API**, or in the robot's **Jupyter / SSH** session.

```
  protocols/*.py          deterministic "muscle" – the liquid handling
        |                  pauses at QC checkpoints
        v
  orchestration/          the "brain" – runs outside the protocol
    plate reader / camera   --> reading
    decisions.py            --> proceed? add cycles? re-amp?
    flex_link.py            --> resume the run / queue next segment  (HTTP API)
```

The QC rules aren't new – they're already written into the protocol `pause()` text (TIP-seq's pre/post-SPRI Qubit gates, WGS's post-WGA checkpoint). `decisions.py` just makes them executable.

## Modules

| File | What | State |
|------|------|-------|
| `decisions.py` | QC rule engine (ng/uL thresholds, cycle top-ups, retention). Pure, no hardware. | Implemented |
| `instruments/plate_reader.py` | Reader -> `{well: ng/uL}`. `CsvPlateReader` = watch export + standard curve. | CSV path done; live SDK stubbed |
| `flex_link.py` | HTTP API wrapper: resume run, (later) queue segments. `dry_run` prints calls. | Resume done; segment re-queue TODO |
| `vision/pellet_detector.py` | Camera -> pellet cleared? / dryness. ABC + GoPro skeleton + baseline. | Stub (Hunter) |
| `run_qc_loop.py` | Reference orchestrator: TIP-seq pre-SPRI Qubit loop, wired end to end. | Runnable (dry-run) |

## Try it (no hardware)

```bash
python -m orchestration.run_qc_loop --dry-run
```

Reads the bundled example export, runs the decision engine per well, and (dry-run) prints the robot calls it *would* send.

## Two tracks, easiest first

1. **Plate reader -> Qubit QC.** Highest ROI, lowest risk. Swap the manual Qubit at the SPRI checkpoints for a dsDNA fluorescence read; the decision engine drives proceed / +cycles / re-amp. Start by parsing the reader's CSV export (`CsvPlateReader`); add a live SDK later.
2. **GoPro CV -> pellet & dryness QC.** Gate the "wait until clear" and "do NOT over-dry" pauses. **Start advisory** (log/alert, human confirms); only let it gate an aspirate once it's trusted – a wrong "cleared" call vacuums up the beads.

## For Hunter

Three scoped issues in `issues/` – fire them from the repo root:

```bash
gh issue create --title "Plate-reader CSV adapter (Qubit-replacement QC)" \
  --body-file orchestration/issues/01-plate-reader-csv-adapter.md --assignee spacexengineer
gh issue create --title "CV bead-pellet detector (SPRI QC from video)" \
  --body-file orchestration/issues/02-cv-pellet-detector.md --assignee spacexengineer
gh issue create --title "Flex HTTP orchestration runner" \
  --body-file orchestration/issues/03-flex-http-runner.md --assignee spacexengineer
```

## Honest status

This is scaffolding: clean interfaces + a working decision engine + a runnable dry-run path. The vision backend and live robot/reader calls are stubs behind stable boundaries, ready to build against. Validate any sensor-gated *control* against the manual method before trusting it to make irreversible pipetting calls.

Optional deps per backend in `requirements.txt`: `opencv-python` + `numpy` (vision), `requests` (live Flex calls).
