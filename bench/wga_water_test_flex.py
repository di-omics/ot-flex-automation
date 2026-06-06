"""AUTO-GENERATED from a portable ProtocolSpec — do not edit by hand.
Edit the spec and re-render. Source protocol: WGA Distributes - Water Test (Studio45)."""
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.21"}
metadata = {
    "protocolName": 'WGA Distributes - Water Test (Studio45)',
    "description": 'Distribute water from reservoir A1 + A2 to sample plate. No pauses.',
    "author": "portable-backend",
}

NUM_SAMPLES = 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8


def run(protocol: protocol_api.ProtocolContext):
    tips = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A2')
    trash = protocol.load_trash_bin('A3')
    sample_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 'B2', label='Sample Plate (empty)')
    reservoir = protocol.load_labware('nest_12_reservoir_15ml', 'D2', label='A1=lysis A2=reaction (water)')

    # 8-channel 1000 uL on the left mount, running 200 uL filter tips
    pipette = protocol.load_instrument("flex_8channel_1000", mount="left", tip_racks=[tips])

    # Distribute Lysis Mix (water)
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(5.0, reservoir["A1"].bottom(z=5.0))
        pipette.dispense(5.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

    # Distribute Reaction Mix (water)
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(6.0, reservoir["A2"].bottom(z=5.0))
        pipette.dispense(6.0, _col[0].bottom(z=5.0))
        pipette.return_tip()

