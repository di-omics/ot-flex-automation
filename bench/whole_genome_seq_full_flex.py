"""AUTO-GENERATED from a portable ProtocolSpec - do not edit by hand.
Edit the spec and re-render. Source protocol: Whole-genome sequencing - Full (portable, Studio45)."""
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.21"}
metadata = {
    "protocolName": 'Whole-genome sequencing - Full (portable, Studio45)',
    "description": 'Full WGA + Library Prep + Bead Cleanup. Reagents per reservoir well.',
    "author": "portable-backend",
}

NUM_SAMPLES = 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8


def run(protocol: protocol_api.ProtocolContext):
    tips_a = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips_b = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A2')
    trash = protocol.load_trash_bin('A3')
    sample_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 'B2', label='Sample Plate')
    reagent_res = protocol.load_labware('nest_12_reservoir_15ml', 'B3', label='Reagents A1-A7')
    magnet = protocol.load_module("magneticBlockV1", 'C2')
    output_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 'C3', label='Output Plate')
    bead_res = protocol.load_labware('nest_12_reservoir_15ml', 'D2', label='Beads/EtOH/Elution/Waste')

    # 8-channel 1000 uL on the left mount, running 200 uL filter tips
    pipette = protocol.load_instrument("flex_8channel_1000", mount="left", tip_racks=[tips_a, tips_b])

    protocol.pause('LYSIS MIX in reagent reservoir A1 (water for motion test).')

    # Distribute Lysis Mix
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(5.0, reagent_res["A1"].bottom(z=5.0))
        pipette.dispense(5.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('Seal. Incubate RT on ice 20 min. Resume.')

    protocol.pause('REACTION MIX in reagent reservoir A2.')

    # Distribute Reaction Mix
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(6.0, reagent_res["A2"].bottom(z=5.0))
        pipette.dispense(6.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('Seal/flick/spin. THERMAL CYCLER DNA Amplification (lid 70C): 30C 2.5h -> 65C 3min -> 4C. Return plate.')

    protocol.pause('QC: Qubit HS >800 ng avg; Tapestation ~1275 bp. Prepare 2 ng/uL normalized plate. Return to B2.')

    protocol.pause('DNA PREP MIX in reagent reservoir A3.')

    # Distribute DNA Prep
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(5.0, reagent_res["A3"].bottom(z=5.0))
        pipette.dispense(5.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('THERMAL CYCLER DNAPREP (lid 105C): 37C 10min -> 4C. Return on ice.')

    protocol.pause('FERAT MIX in reagent reservoir A4.')

    # Distribute FERAT + mix
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(5.0, reagent_res["A4"].bottom(z=5.0))
        pipette.dispense(5.0, _col[0].bottom(z=5.0))
        pipette.mix(5, 5, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('THERMAL CYCLER FERAT (lid 105C): 4C 30s -> 30C 5min -> 65C 30min -> 4C.')

    protocol.pause('Vortex adapter plate briefly. Spin down.')

    # Distribute Adapters
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(5.0, reagent_res["A6"].bottom(z=5.0))
        pipette.dispense(5.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    # Distribute LP2L
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(5.0, reagent_res["A5"].bottom(z=5.0))
        pipette.dispense(5.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('Seal. Vortex medium. Spin. Incubate RT 15 min. Proceed.')

    protocol.pause('AMP MIX in reagent reservoir A7. Start LIB-AMP, pause at 98C.')

    # Distribute Amp Mix + mix
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(20.0, reagent_res["A7"].bottom(z=5.0))
        pipette.dispense(20.0, _col[0].bottom(z=5.0))
        pipette.mix(5, 20, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('THERMAL CYCLER LIB-AMP (lid 105C): 98C 45s -> [98C 15s/60C 30s/72C 45s]x8 -> 72C 60s -> 4C. Return on ice.')

    protocol.pause('Vortex SPRI magnetic cleanup beads 10s. Fresh 80% EtOH in bead reservoir A2.')

    # Add SPRI magnetic cleanup beads
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(30.0, bead_res["A1"].bottom(z=5.0))
        pipette.dispense(30.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('Seal. Vortex 10s. Incubate RT 5 min. Spin. Place plate ON Magnetic Block (C2). Wait 3 min until clear.')

    # Remove supernatant to waste
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(70.0, _col[0].bottom(z=5.0))
        pipette.dispense(70.0, bead_res["A12"].bottom(z=5.0))
        pipette.return_tip()

    # EtOH wash 1 add
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(180.0, bead_res["A2"].bottom(z=5.0))
        pipette.dispense(180.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.delay(seconds=30, msg='EtOH wash 1 soak')

    # EtOH wash 1 remove
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(180.0, _col[0].bottom(z=5.0))
        pipette.dispense(180.0, bead_res["A12"].bottom(z=5.0))
        pipette.return_tip()

    # EtOH wash 2 add
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(180.0, bead_res["A2"].bottom(z=5.0))
        pipette.dispense(180.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.delay(seconds=30, msg='EtOH wash 2 soak')

    # EtOH wash 2 remove
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(180.0, _col[0].bottom(z=5.0))
        pipette.dispense(180.0, bead_res["A12"].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('Remove residual EtOH with P20. Air dry 3 min - do NOT over-dry.')

    protocol.pause('Remove plate FROM magnet.')

    # Add Elution Buffer + mix
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(42.0, bead_res["A3"].bottom(z=5.0))
        pipette.dispense(42.0, _col[0].bottom(z=5.0))
        pipette.mix(10, 35, _col[0].bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('Incubate RT 2 min. Return to magnet. Wait 2 min until clear.')

    # Transfer eluate -> output plate
    for i in range(NUM_COLUMNS):
        _s = sample_plate.columns()[i][0]
        _d = output_plate.columns()[i][0]
        pipette.pick_up_tip()
        pipette.aspirate(40.0, _s.bottom(z=5.0))
        pipette.dispense(40.0, _d.bottom(z=5.0))
        pipette.return_tip()

    protocol.pause('DONE. POST-QC: Qubit HS + Tapestation HS D1000. Pool + final 0.75x cleanup before sequencing.')
