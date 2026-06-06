"""Compile a ProtocolSpec -> a vendor-neutral transfer worklist (CSV).

A flat transfer list - `source -> destination, volume` per row - is the lingua
franca that Hamilton Venus (STAR) and Agilent Bravo (VWorks) worklist importers
both consume. This is the **interim port path**: the same spec that drives the
Flex emits a worklist a STAR/Bravo method can execute.

Column-wise (8-channel) transfers expand to one row per destination well (rows
A-H of each active column). Handoffs and delays become commented marker rows.
"""
from __future__ import annotations

import csv
import io

from ..spec import ProtocolSpec, Transfer, Handoff, Delay, split_loc

_ROWS = "ABCDEFGH"
HEADER = ["step", "source_labware", "source_well",
          "dest_labware", "dest_well", "volume_ul", "comment"]


def render(spec: ProtocolSpec) -> str:
    buf = io.StringIO()
    out = csv.writer(buf)
    out.writerow(HEADER)

    for n, step in enumerate(spec.steps, 1):
        if isinstance(step, Handoff):
            first = step.message.splitlines()[0] if step.message else "handoff"
            out.writerow([n, "", "", "", "", "", f"HANDOFF: {first}"])
        elif isinstance(step, Delay):
            out.writerow([n, "", "", "", "", "", f"DELAY {step.seconds}s: {step.message}"])
        elif isinstance(step, Transfer):
            for row in _expand(spec, step):
                out.writerow([n] + row)
        else:
            raise TypeError(f"unknown step type {type(step).__name__}")
    return buf.getvalue()


def _expand(spec, step: Transfer):
    """One CSV row per physical well-to-well move."""
    s_lw, s_well = split_loc(step.source)
    d_lw, d_well = split_loc(step.dest)
    v, c = step.volume_ul, step.comment
    cols = range(1, spec.num_columns + 1)

    if s_well and not d_well:          # well -> plate
        return [[s_lw, s_well, d_lw, f"{r}{col}", v, c] for col in cols for r in _ROWS]
    if not s_well and d_well:          # plate -> well
        return [[s_lw, f"{r}{col}", d_lw, d_well, v, c] for col in cols for r in _ROWS]
    if not s_well and not d_well:      # plate -> plate (column i -> i)
        return [[s_lw, f"{r}{col}", d_lw, f"{r}{col}", v, c] for col in cols for r in _ROWS]
    return [[s_lw, s_well, d_lw, d_well, v, c]]  # well -> well
