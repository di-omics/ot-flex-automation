"""AUTO-GENERATED from a portable ProtocolSpec - Hamilton STAR via PyLabRobot.
Same protocol as the Flex build, retargeted to the STAR. Source: whole-genome sequencing - Full (portable, Studio45).
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
    tip_carrier[0] = tips_a = hamilton_96_tiprack_1000uL(name='tips_a')
    tip_carrier[1] = tips_b = hamilton_96_tiprack_1000uL(name='tips_b')
    deck.assign_child_resource(tip_carrier, rails=1)
    plate_carrier = PLT_CAR_L5MD_A00(name="plate_carrier")
    plate_carrier[0] = sample_plate = Cor_96_wellplate_360ul_Fb(name='sample_plate')
    plate_carrier[1] = reagent_res = CellTreat_12_troughplate_15000ul_Vb(name='reagent_res')
    plate_carrier[2] = output_plate = Cor_96_wellplate_360ul_Fb(name='output_plate')
    plate_carrier[3] = bead_res = CellTreat_12_troughplate_15000ul_Vb(name='bead_res')
    deck.assign_child_resource(plate_carrier, rails=9)
    _READER_SITE = plate_carrier[4]   # free site used as gripper/move target
    # ========================================================================

    await lh.setup()

    _TIP_RACKS = [tips_a, tips_b]
    _tip = {'i': 0}

    async def _grab_tips():
        n = _tip['i']; _tip['i'] += 1
        rack = _TIP_RACKS[(n // 12) % len(_TIP_RACKS)]
        col = (n % 12) + 1
        await lh.pick_up_tips(rack[f'A{col}:H{col}'])

    # ===== PROTOCOL (generated) =====
    input('LYSIS MIX in reagent reservoir A1 (water for motion test).' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'LYSIS MIX in reagent reservoir A1 (water for motion test).')
    # Distribute Lysis Mix
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reagent_res["A1"] * 8, vols=[5.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[5.0] * 8)
        await lh.return_tips()
    input('Seal. Incubate RT on ice 20 min. Resume.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Seal. Incubate RT on ice 20 min. Resume.')
    input('REACTION MIX in reagent reservoir A2.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'REACTION MIX in reagent reservoir A2.')
    # Distribute Reaction Mix
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reagent_res["A2"] * 8, vols=[6.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[6.0] * 8)
        await lh.return_tips()
    input('Seal/flick/spin. THERMAL CYCLER DNA Amplification (lid 70C): 30C 2.5h -> 65C 3min -> 4C. Return plate.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Seal/flick/spin. THERMAL CYCLER DNA Amplification (lid 70C): 30C 2.5h -> 65C 3min -> 4C. Return plate.')
    input('QC: Qubit HS >800 ng avg; Tapestation ~1275 bp. Prepare 2 ng/uL normalized plate. Return to B2.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'QC: Qubit HS >800 ng avg; Tapestation ~1275 bp. Prepare 2 ng/uL normalized plate. Return to B2.')
    input('DNA PREP MIX in reagent reservoir A3.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'DNA PREP MIX in reagent reservoir A3.')
    # Distribute DNA Prep
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reagent_res["A3"] * 8, vols=[5.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[5.0] * 8)
        await lh.return_tips()
    input('THERMAL CYCLER DNAPREP (lid 105C): 37C 10min -> 4C. Return on ice.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'THERMAL CYCLER DNAPREP (lid 105C): 37C 10min -> 4C. Return on ice.')
    input('FERAT MIX in reagent reservoir A4.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'FERAT MIX in reagent reservoir A4.')
    # Distribute FERAT + mix
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reagent_res["A4"] * 8, vols=[5.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[5.0] * 8)
        for _ in range(5):  # mix
            await lh.aspirate(sample_plate[f"A{c}:H{c}"], vols=[5] * 8)
            await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[5] * 8)
        await lh.return_tips()
    input('THERMAL CYCLER FERAT (lid 105C): 4C 30s -> 30C 5min -> 65C 30min -> 4C.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'THERMAL CYCLER FERAT (lid 105C): 4C 30s -> 30C 5min -> 65C 30min -> 4C.')
    input('Vortex adapter plate briefly. Spin down.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Vortex adapter plate briefly. Spin down.')
    # Distribute Adapters
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reagent_res["A6"] * 8, vols=[5.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[5.0] * 8)
        await lh.return_tips()
    # Distribute LP2L
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reagent_res["A5"] * 8, vols=[5.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[5.0] * 8)
        await lh.return_tips()
    input('Seal. Vortex medium. Spin. Incubate RT 15 min. Proceed.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Seal. Vortex medium. Spin. Incubate RT 15 min. Proceed.')
    input('AMP MIX in reagent reservoir A7. Start LIB-AMP, pause at 98C.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'AMP MIX in reagent reservoir A7. Start LIB-AMP, pause at 98C.')
    # Distribute Amp Mix + mix
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(reagent_res["A7"] * 8, vols=[20.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[20.0] * 8)
        for _ in range(5):  # mix
            await lh.aspirate(sample_plate[f"A{c}:H{c}"], vols=[20] * 8)
            await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[20] * 8)
        await lh.return_tips()
    input('THERMAL CYCLER LIB-AMP (lid 105C): 98C 45s -> [98C 15s/60C 30s/72C 45s]x8 -> 72C 60s -> 4C. Return on ice.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'THERMAL CYCLER LIB-AMP (lid 105C): 98C 45s -> [98C 15s/60C 30s/72C 45s]x8 -> 72C 60s -> 4C. Return on ice.')
    input('Vortex Resolve Beads 10s. Fresh 80% EtOH in bead reservoir A2.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Vortex Resolve Beads 10s. Fresh 80% EtOH in bead reservoir A2.')
    # Add Resolve Beads
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(bead_res["A1"] * 8, vols=[30.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[30.0] * 8)
        await lh.return_tips()
    input('Seal. Vortex 10s. Incubate RT 5 min. Spin. Place plate ON Magnetic Block (C2). Wait 3 min until clear.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Seal. Vortex 10s. Incubate RT 5 min. Spin. Place plate ON Magnetic Block (C2). Wait 3 min until clear.')
    # Remove supernatant to waste
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(sample_plate[f"A{c}:H{c}"], vols=[70.0] * 8)
        await lh.dispense(bead_res["A12"] * 8, vols=[70.0] * 8)
        await lh.return_tips()
    # EtOH wash 1 add
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(bead_res["A2"] * 8, vols=[180.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[180.0] * 8)
        await lh.return_tips()
    await asyncio.sleep(30 if not USE_CHATTERBOX else 0)  # EtOH wash 1 soak
    # EtOH wash 1 remove
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(sample_plate[f"A{c}:H{c}"], vols=[180.0] * 8)
        await lh.dispense(bead_res["A12"] * 8, vols=[180.0] * 8)
        await lh.return_tips()
    # EtOH wash 2 add
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(bead_res["A2"] * 8, vols=[180.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[180.0] * 8)
        await lh.return_tips()
    await asyncio.sleep(30 if not USE_CHATTERBOX else 0)  # EtOH wash 2 soak
    # EtOH wash 2 remove
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(sample_plate[f"A{c}:H{c}"], vols=[180.0] * 8)
        await lh.dispense(bead_res["A12"] * 8, vols=[180.0] * 8)
        await lh.return_tips()
    input('Remove residual EtOH with P20. Air dry 3 min - do NOT over-dry.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Remove residual EtOH with P20. Air dry 3 min - do NOT over-dry.')
    input('Remove plate FROM magnet.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Remove plate FROM magnet.')
    # Add Elution Buffer + mix
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(bead_res["A3"] * 8, vols=[42.0] * 8)
        await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[42.0] * 8)
        for _ in range(10):  # mix
            await lh.aspirate(sample_plate[f"A{c}:H{c}"], vols=[35] * 8)
            await lh.dispense(sample_plate[f"A{c}:H{c}"], vols=[35] * 8)
        await lh.return_tips()
    input('Incubate RT 2 min. Return to magnet. Wait 2 min until clear.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'Incubate RT 2 min. Return to magnet. Wait 2 min until clear.')
    # Transfer eluate -> output plate
    for c in range(1, NUM_COLUMNS + 1):
        await _grab_tips()
        await lh.aspirate(sample_plate[f"A{c}:H{c}"], vols=[40.0] * 8)
        await lh.dispense(output_plate[f"A{c}:H{c}"], vols=[40.0] * 8)
        await lh.return_tips()
    input('DONE. POST-QC: Qubit HS + Tapestation HS D1000. Pool + final 0.75x cleanup before sequencing.' + ' [Enter]') if not USE_CHATTERBOX else print('PAUSE:', 'DONE. POST-QC: Qubit HS + Tapestation HS D1000. Pool + final 0.75x cleanup before sequencing.')

    await lh.stop()


if __name__ == "__main__":
    asyncio.run(main())
