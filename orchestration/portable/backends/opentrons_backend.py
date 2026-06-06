"""Compile a ProtocolSpec -> an Opentrons Flex protocol (runs on the Flex today).

Emits a standalone `.py` protocol file using the same API idioms as the
hand-written protocols in `protocols/` (api 2.21, 8-channel 1000 uL on the right
mount running 200 uL filter tips, per-column pick_up/aspirate/dispense/drop
loops, pauses for off-deck handoffs). The emitted file imports into the
Opentrons App and runs / simulates with `opentrons_simulate`.
"""
from __future__ import annotations

from ..spec import ProtocolSpec, Transfer, Handoff, split_loc

# vendor-neutral kind -> Opentrons catalog load name
_LOADNAME = {
    "pcr_plate_96": "nest_96_wellplate_100ul_pcr_full_skirt",
    "reservoir_12": "nest_12_reservoir_15ml",
    "tiprack_200":  "opentrons_flex_96_filtertiprack_200ul",
}


def render(spec: ProtocolSpec, mount: str = "right") -> str:
    if mount not in ("left", "right"):
        raise ValueError(f"mount must be 'left' or 'right', got {mount!r}")
    L: list[str] = []
    w = L.append

    w('"""AUTO-GENERATED from a portable ProtocolSpec — do not edit by hand.')
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
        elif lw.kind == "tiprack_200":
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
            _emit_handoff(w, step)
        elif isinstance(step, Transfer):
            _emit_transfer(w, step)
        else:
            raise TypeError(f"unknown step type {type(step).__name__}")

    return "\n".join(L) + "\n"


def _emit_handoff(w, step: Handoff):
    w(f"    protocol.pause({step.message!r})")
    w("")


def _emit_transfer(w, step: Transfer):
    src_lw, src_well = split_loc(step.source)
    if step.comment:
        w(f"    # {step.comment}")
    w(f"    _cols = [{step.dest}.columns()[i] for i in range(NUM_COLUMNS)]")
    w("    for _col in _cols:")
    w("        pipette.pick_up_tip()")
    w(f'        pipette.aspirate({step.volume_ul}, {src_lw}["{src_well}"].bottom(z={step.aspirate_z}))')
    w(f"        pipette.dispense({step.volume_ul}, _col[0].bottom(z={step.dispense_z}))")
    if step.mix_after:
        reps, vol = step.mix_after
        w(f"        pipette.mix({reps}, {vol}, _col[0].bottom(z={step.dispense_z}))")
    w("        pipette.drop_tip()")
    w("")
