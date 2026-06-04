"""
Example orchestrator: TIP-seq pre-SPRI Qubit loop, closed.

Flow:
  protocol pauses at the pre-SPRI Qubit checkpoint
    -> aliquot + dye into a read plate, read it
    -> CsvPlateReader parses the export -> {well: ng/uL}
    -> decisions.tipseq_pre_spri per well
    -> all PROCEED: FlexLink.resume_run(); else report cycle top-ups

Dry run (no hardware, uses the bundled example export):
    python -m orchestration.run_qc_loop --dry-run

Reference wiring the other tracks (CV gating, live reader, cycle re-queue)
extend. See the issues/ folder.
"""
from __future__ import annotations
import argparse
from pathlib import Path

from orchestration import decisions
from orchestration.instruments.plate_reader import CsvPlateReader, StandardCurve
from orchestration.flex_link import FlexLink


def run(export_csv: Path, run_id: str, dry_run: bool = True) -> dict:
    curve = StandardCurve.from_points([(0, 50), (1, 1050), (5, 5050), (10, 10050)])
    reader = CsvPlateReader(export_csv, curve, layout="long", blank_rfu=0.0)
    readings = reader.read_plate()

    verdicts = decisions.decide_batch(decisions.tipseq_pre_spri, readings)
    for well, d in verdicts.items():
        print(f"  {well}: {readings[well]:.2f} ng/uL -> {d}")

    all_proceed = all(d.action is decisions.Action.PROCEED for d in verdicts.values())
    link = FlexLink(dry_run=dry_run)
    if all_proceed:
        print("All wells pass -> resuming run for the 0.8x cleanup.")
        link.resume_run(run_id)
    else:
        topups = {w: d.params.get("extra_cycles") for w, d in verdicts.items()
                  if d.action is decisions.Action.ADD_CYCLES}
        print(f"HOLD -- re-PCR needed before cleanup. Cycle top-ups: {topups}")
    return {"readings": readings,
            "verdicts": {w: str(d) for w, d in verdicts.items()},
            "resumed": all_proceed}


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="TIP-seq pre-SPRI Qubit QC loop")
    ap.add_argument("--export", type=Path,
                    default=here / "examples" / "sample_plate_read.csv",
                    help="CSV exported by the plate reader")
    ap.add_argument("--run-id", default="example-run-id", help="Opentrons run id")
    ap.add_argument("--dry-run", action="store_true", help="print robot calls, don't send")
    args = ap.parse_args()
    run(args.export, args.run_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
