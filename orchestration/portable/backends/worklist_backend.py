"""Compile a ProtocolSpec -> a vendor-neutral transfer worklist (CSV).

A flat transfer list - `source -> destination, volume` per row - is the lingua
franca that Hamilton Venus (STAR) and Agilent Bravo (VWorks) worklist importers
both consume. This is the **interim port path**: the same spec that drives the
Flex emits a worklist a STAR/Bravo method can execute, so the protocol intent
moves platforms without a rewrite.

Per-column (8-channel) transfers are expanded to one row per destination well
(rows A-H of each active column), since single-/multi-channel platforms address
wells individually. Handoffs become commented marker rows.
"""
from __future__ import annotations

import csv
import io

from ..spec import ProtocolSpec, Transfer, Handoff, split_loc

_ROWS = "ABCDEFGH"
HEADER = ["step", "source_labware", "source_well",
          "dest_labware", "dest_well", "volume_ul", "comment"]


def render(spec: ProtocolSpec) -> str:
    buf = io.StringIO()
    out = csv.writer(buf)
    out.writerow(HEADER)

    step_no = 0
    for step in spec.steps:
        step_no += 1
        if isinstance(step, Handoff):
            first_line = step.message.splitlines()[0] if step.message else "handoff"
            out.writerow([step_no, "", "", "", "", "", f"HANDOFF: {first_line}"])
        elif isinstance(step, Transfer):
            src_lw, src_well = split_loc(step.source)
            for c in range(1, spec.num_columns + 1):
                for r in _ROWS:
                    out.writerow([step_no, src_lw, src_well,
                                  step.dest, f"{r}{c}", step.volume_ul, step.comment])
        else:
            raise TypeError(f"unknown step type {type(step).__name__}")

    return buf.getvalue()
