"""AUTO-GENERATED from a portable ProtocolSpec — do not edit by hand.
Edit the spec and re-render. Source protocol: Hello Water (Phase-0 motion test)."""
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.21"}
metadata = {
    "protocolName": 'Hello Water (Phase-0 motion test)',
    "description": 'Move water reservoir A1 -> every sample column. No pauses.',
    "author": "portable-backend",
}

NUM_SAMPLES = 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8


def run(protocol: protocol_api.ProtocolContext):
    sample_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 'B2', label='Sample Plate (empty)')
    source_plate = protocol.load_labware('nest_12_reservoir_15ml', 'B3', label='Reservoir (A1 = water)')
    tips_a = protocol.load_labware('opentrons_flex_96_filtertiprack_200ul', 'A1')
    tips_b = protocol.load_labware('opentrons_flex_96_filtertiprack_200ul', 'A2')
    trash = protocol.load_trash_bin('D1')

    # 8-channel 1000 uL on the left mount, running 200 uL filter tips
    pipette = protocol.load_instrument("flex_8channel_1000", mount="left", tip_racks=[tips_a, tips_b])

    # Move 20 uL water to each column
    _cols = [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]
    for _col in _cols:
        pipette.pick_up_tip()
        pipette.aspirate(20.0, source_plate["A1"].bottom(z=5.0))
        pipette.dispense(20.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

