"""AUTO-GENERATED from a portable ProtocolSpec - Hamilton STAR via PyLabRobot.
Same protocol as the Flex build, retargeted to the STAR. Source: WGA Distributes + Gripper Move to Reader (Studio45).
Dry run: USE_CHATTERBOX=True (default). Real STAR: set it False.
EDIT the DECK SETUP block (rails/carriers/labware) for your physical STAR."""
import asyncio
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import (
    STARBackend, LiquidHandlerChatterboxBackend)
from pylabrobot.resources import (
    STARLetDeck, TIP_CAR_288_A00, PLT_CAR_L5MD_A00,
    CellTreat_12_troughplate_15000ul_Vb, Cor_96_wellplate_360ul_Fb, hamilton_96_tiprack_1000uL)

USE_CHATTERBOX = True   # False -> real Hamilton STAR
NUM_SAMPLES = 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8


async def main():
    deck = STARLetDeck()
    backend = LiquidHandlerChatterboxBackend(num_channels=8) if USE_CHATTERBOX else STARBackend()
    lh = LiquidHandler(backend=backend, deck=deck)

    # ===== DECK SETUP - EDIT FOR YOUR STAR (rails / carriers / labware) =====
    tip_carrier = TIP_CAR_288_A00(name="tip_carrier")
    tip_carrier[0] = tips = hamilton_96_tiprack_1000uL(name='tips')
    deck.assign_child_resource(tip_carrier, rails=1)
    plate_carrier = PLT_CAR_L5MD_A00(name="plate_carrier")
    plate_carrier[0] = sample_plate = Cor_96_wellplate_360ul_Fb(name='sample_plate')
    plate_carrier[1] = reservoir = CellTreat_12_troughplate_15000ul_Vb(name='reservoir')
    deck.assign_child_resource(plate_carrier, rails=9)
    _READER_SITE = plate_carrier[2]   # free site used as gripper/move target
    # ========================================================================

    await lh.setup()

    _TIP_RACKS = [tips]
    _tip = {'i': 0}

    async def _grab_tips():
        n = _tip['i']; _tip['i'] += 1
        rack = _TIP_RACKS[(n // 12) % len(_TIP_RACKS)]
        col = (n % 12) + 1
        await lh.pick_up_tips(rack[f'A{col}:H{col}'])

    # ===== PROTOCOL (generated) =====
    # Distribute Lysis Mix (water)
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reservoir["A1"] * 8, vols=[5.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[5.0] * 8)
        await lh.return_tips()
    # Distribute Reaction Mix (water)
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reservoir["A2"] * 8, vols=[6.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[6.0] * 8)
        await lh.return_tips()
    await lh.move_plate(sample_plate, _READER_SITE)  # Gripper: carry sample plate B2 -> D1 (pretend plate reader)

    await lh.stop()


if __name__ == "__main__":
    asyncio.run(main())
