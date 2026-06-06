"""Compile a ProtocolSpec -> a PyLabRobot script for the Hamilton STAR.

PyLabRobot (PLR) is a hardware-agnostic Python liquid-handling framework with a
real Hamilton STAR backend - a far better Hamilton target than a raw worklist
CSV. This backend emits a runnable PLR script: the SAME portable protocol that
drives the Opentrons Flex, retargeted to the STAR.

The emitted script:
  * defaults to PLR's LiquidHandlerChatterboxBackend (hardware-free dry run) so
    it runs and prints every command immediately; flip USE_CHATTERBOX=False for
    the real STAR (STARBackend).
  * has a clearly marked DECK SETUP section - rails, carriers, and exact labware
    depend on YOUR physical STAR, so edit that block. The protocol body below it
    is generated and faithful to the spec.

Operation patterns are validated against PLR 0.2.x under the chatterbox backend.
"""
from __future__ import annotations

from ..spec import ProtocolSpec, Transfer, Handoff, Delay, MoveLabware, split_loc

# vendor-neutral kind -> (PLR resource class, kind-group)
_RESOURCE = {
    "tiprack_1000": "hamilton_96_tiprack_1000uL",
    "tiprack_200":  "hamilton_96_tiprack_1000uL",  # nearest STAR tip; adjust to your rack
    "pcr_plate_96": "Cor_96_wellplate_360ul_Fb",
    "reservoir_12": "CellTreat_12_troughplate_15000ul_Vb",
}


def render(spec: ProtocolSpec) -> str:
    tipracks = [lw for lw in spec.labware if lw.kind.startswith("tiprack")]
    plates = [lw for lw in spec.labware if lw.kind in ("pcr_plate_96", "reservoir_12")]
    classes = sorted({_RESOURCE[lw.kind] for lw in tipracks + plates})

    L: list[str] = []
    w = L.append
    w('"""AUTO-GENERATED from a portable ProtocolSpec - Hamilton STAR via PyLabRobot.')
    w(f'Same protocol as the Flex build, retargeted to the STAR. Source: {spec.name}.')
    w('Dry run: USE_CHATTERBOX=True (default). Real STAR: set it False.')
    w('EDIT the DECK SETUP block (rails/carriers/labware) for your physical STAR."""')
    w("import asyncio")
    w("from pylabrobot.liquid_handling import LiquidHandler")
    w("from pylabrobot.liquid_handling.backends import (")
    w("    STARBackend, LiquidHandlerChatterboxBackend)")
    w("from pylabrobot.resources import (")
    w("    STARLetDeck, TIP_CAR_288_A00, PLT_CAR_L5MD_A00,")
    w(f"    {', '.join(classes)})")
    w("")
    w("USE_CHATTERBOX = True   # False -> real Hamilton STAR")
    w(f"NUM_SAMPLES = {spec.num_samples}")
    w("NUM_COLUMNS = (NUM_SAMPLES + 7) // 8")
    w("")
    w("")
    w("async def main():")
    w("    deck = STARLetDeck()")
    w("    backend = LiquidHandlerChatterboxBackend(num_channels=8) if USE_CHATTERBOX else STARBackend()")
    w("    lh = LiquidHandler(backend=backend, deck=deck)")
    w("")
    w("    # ===== DECK SETUP - EDIT FOR YOUR STAR (rails / carriers / labware) =====")
    w('    tip_carrier = TIP_CAR_288_A00(name="tip_carrier")')
    for i, lw in enumerate(tipracks):
        w(f'    tip_carrier[{i}] = {lw.id} = {_RESOURCE[lw.kind]}(name={lw.id!r})')
    w("    deck.assign_child_resource(tip_carrier, rails=1)")
    w('    plate_carrier = PLT_CAR_L5MD_A00(name="plate_carrier")')
    for j, lw in enumerate(plates):
        w(f'    plate_carrier[{j}] = {lw.id} = {_RESOURCE[lw.kind]}(name={lw.id!r})')
    free_site = len(plates)
    w("    deck.assign_child_resource(plate_carrier, rails=9)")
    w(f"    _READER_SITE = plate_carrier[{free_site}]   # free site used as gripper/move target")
    w("    # ========================================================================")
    w("")
    w("    await lh.setup()")
    w("")
    w(f"    _TIP_RACKS = [{', '.join(lw.id for lw in tipracks)}]")
    w("    _tip = {'i': 0}")
    w("")
    w("    async def _grab_tips():")
    w("        n = _tip['i']; _tip['i'] += 1")
    w("        rack = _TIP_RACKS[(n // 12) % len(_TIP_RACKS)]")
    w("        col = (n % 12) + 1")
    w("        await lh.pick_up_tips(rack[f'A{col}:H{col}'])")
    w("")
    w("    # ===== PROTOCOL (generated) =====")

    for step in spec.steps:
        if isinstance(step, Handoff):
            w(f"    input({_oneline(step.message)!r} + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', {_oneline(step.message)!r})")
        elif isinstance(step, Delay):
            w(f"    await asyncio.sleep({step.seconds} if not USE_CHATTERBOX else 0)  # {step.message}")
        elif isinstance(step, MoveLabware):
            w(f"    await lh.move_plate({step.labware}, _READER_SITE)  # {step.comment or 'gripper move'}")
        elif isinstance(step, Transfer):
            _emit_transfer(w, step)
        else:
            raise TypeError(f"unknown step {type(step).__name__}")
    w("")
    w("    await lh.stop()")
    w("")
    w("")
    w('if __name__ == "__main__":')
    w("    asyncio.run(main())")
    return "\n".join(L) + "\n"


def _oneline(msg: str) -> str:
    return " ".join(msg.split())


def _col(lw: str) -> str:
    return f'{lw}[f"A{{c}}:H{{c}}"]'


def _emit_transfer(w, step: Transfer):
    src_lw, src_well = split_loc(step.source)
    dst_lw, dst_well = split_loc(step.dest)
    v = step.volume_ul
    if step.comment:
        w(f"    # {step.comment}")
    w("    for c in range(1, NUM_COLUMNS + 1):")
    w("        await _grab_tips()")
    if src_well and not dst_well:        # well -> plate
        w(f'        await lh.aspirate({src_lw}["{src_well}"] * 8, vols=[{v}] * 8)')
        w(f"        await lh.dispense({_col(dst_lw)}, vols=[{v}] * 8)")
        mix_target = _col(dst_lw)
    elif not src_well and dst_well:      # plate -> well
        w(f"        await lh.aspirate({_col(src_lw)}, vols=[{v}] * 8)")
        w(f'        await lh.dispense({dst_lw}["{dst_well}"] * 8, vols=[{v}] * 8)')
        mix_target = None
    else:                                # plate -> plate
        w(f"        await lh.aspirate({_col(src_lw)}, vols=[{v}] * 8)")
        w(f"        await lh.dispense({_col(dst_lw)}, vols=[{v}] * 8)")
        mix_target = _col(dst_lw)
    if step.mix_after and mix_target:
        reps, mv = step.mix_after
        w(f"        for _ in range({reps}):  # mix")
        w(f"            await lh.aspirate({mix_target}, vols=[{mv}] * 8)")
        w(f"            await lh.dispense({mix_target}, vols=[{mv}] * 8)")
    w("        await lh.return_tips()")
