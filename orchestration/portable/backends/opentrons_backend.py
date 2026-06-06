"""Compile a ProtocolSpec -> an Opentrons Flex protocol (runs on the Flex today).

Emits a standalone `.py` protocol file using the same API idioms as the
hand-written protocols in `protocols/` (api 2.21, 8-channel 1000 uL, per-column
pick_up/aspirate/dispense loops, pauses for off-deck handoffs). The emitted file
imports into the Opentrons App and runs / simulates with `opentrons_simulate`.

  mount        : "left" or "right" (Studio45's p1000 is on the LEFT)
  return_tips  : for water testing - return tips to the rack instead of
                 trashing them, so a dry run doesn't consume the rack.
"""
from __future__ import annotations

from ..spec import ProtocolSpec, Transfer, Handoff, Delay, split_loc

# vendor-neutral kind -> Opentrons catalog load name
_LOADNAME = {
    "pcr_plate_96": "nest_96_wellplate_100ul_pcr_full_skirt",
    "reservoir_12": "nest_12_reservoir_15ml",
    "tiprack_200":  "opentrons_flex_96_filtertiprack_200ul",
    "tiprack_1000": "opentrons_flex_96_tiprack_1000ul",
}


def render(spec: ProtocolSpec, mount: str = "right", return_tips: bool = False) -> str:
    if mount not in ("left", "right"):
        raise ValueError(f"mount must be 'left' or 'right', got {mount!r}")
    drop = "pipette.return_tip()" if return_tips else "pipette.drop_tip()"

    L: list[str] = []
    w = L.append
    w('"""AUTO-GENERATED from a portable ProtocolSpec - do not edit by hand.')
    w(f'Edit the spec and re-render. Source protocol: {spec.name}."""')
    w("from opentrons import protocol_api")
    w("")
    w('requirements = {"robotType": "Flex", "apiLevel": "2.21"}')
    w("metadata = {")
    w(f'    "protocolName": {spec.name!r},')
    w(f'    "description": {spec.description!r},')
    w('    "author": "portable-backend",')
    w("}")
    w("")
    w(f"NUM_SAMPLES = {spec.num_samples}")
    w("NUM_COLUMNS = (NUM_SAMPLES + 7) // 8")
    w("")
    w("")
    w("def run(protocol: protocol_api.ProtocolContext):")

    tipracks = []
    for lw in spec.labware:
        if lw.kind == "trash":
            w(f'    {lw.id} = protocol.load_trash_bin({lw.slot!r})')
        elif lw.kind == "magnet":
            w(f'    {lw.id} = protocol.load_module("magneticBlockV1", {lw.slot!r})')
        elif lw.kind.startswith("tiprack"):
            w(f'    {lw.id} = protocol.load_labware({_LOADNAME[lw.kind]!r}, {lw.slot!r})')
            tipracks.append(lw.id)
        else:
            label = f", label={lw.label!r}" if lw.label else ""
            w(f'    {lw.id} = protocol.load_labware({_LOADNAME[lw.kind]!r}, {lw.slot!r}{label})')

    racks = ", ".join(tipracks)
    w("")
    w(f"    # 8-channel 1000 uL on the {mount} mount, running 200 uL filter tips")
    w(f'    pipette = protocol.load_instrument("flex_8channel_1000", mount="{mount}", tip_racks=[{racks}])')
    w("")

    for step in spec.steps:
        if isinstance(step, Handoff):
            w(f"    protocol.pause({step.message!r})")
            w("")
        elif isinstance(step, Delay):
            w(f"    protocol.delay(seconds={step.seconds}, msg={step.message!r})")
            w("")
        elif isinstance(step, Transfer):
            _emit_transfer(w, step, drop)
        else:
            raise TypeError(f"unknown step type {type(step).__name__}")

    return "\n".join(L) + "\n"


def _well(loc: str) -> str:
    """'reservoir:A1' -> 'reservoir[\"A1\"]'."""
    lw, well = split_loc(loc)
    return f'{lw}["{well}"]'


def _emit_transfer(w, step: Transfer, drop: str):
    src_lw, src_well = split_loc(step.source)
    dst_lw, dst_well = split_loc(step.dest)
    if step.comment:
        w(f"    # {step.comment}")

    if src_well and not dst_well:       # well -> plate : distribute
        src = f'{src_lw}["{src_well}"]'
        w(f"    for _col in [{dst_lw}.columns()[i] for i in range(NUM_COLUMNS)]:")
        _emit_cycle(w, step, src, "_col[0]", drop)
    elif not src_well and dst_well:     # plate -> well : pool / remove
        dst = f'{dst_lw}["{dst_well}"]'
        w(f"    for _col in [{src_lw}.columns()[i] for i in range(NUM_COLUMNS)]:")
        _emit_cycle(w, step, "_col[0]", dst, drop)
    elif not src_well and not dst_well:  # plate -> plate : column i -> column i
        w(f"    for i in range(NUM_COLUMNS):")
        w(f"        _s = {src_lw}.columns()[i][0]")
        w(f"        _d = {dst_lw}.columns()[i][0]")
        _emit_cycle(w, step, "_s", "_d", drop)
    else:                               # well -> well : single move
        w("    if True:")
        _emit_cycle(w, step, f'{src_lw}["{src_well}"]', f'{dst_lw}["{dst_well}"]', drop)
    w("")


def _emit_cycle(w, step: Transfer, src_expr: str, dst_expr: str, drop: str):
    v = step.volume_ul
    w("        pipette.pick_up_tip()")
    w(f"        pipette.aspirate({v}, {src_expr}.bottom(z={step.aspirate_z}))")
    w(f"        pipette.dispense({v}, {dst_expr}.bottom(z={step.dispense_z}))")
    if step.mix_after:
        reps, mv = step.mix_after
        w(f"        pipette.mix({reps}, {mv}, {dst_expr}.bottom(z={step.dispense_z}))")
    w(f"        {drop}")
