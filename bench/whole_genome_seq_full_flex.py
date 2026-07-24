"""AUTO-GENERATED from a portable ProtocolSpec - do not edit by hand.
Edit the spec and re-render. Source protocol: Whole-Genome Sequencing Preparation - Synthetic Motion Profile."""
from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.21"}
metadata = {
    "protocolName": 'Whole-Genome Sequencing Preparation - Synthetic Motion Profile',
    "description": 'Water-only WGS-preparation choreography; no biological method parameters or QC thresholds.',
    "author": "portable-backend",
}

NUM_SAMPLES = 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8


def run(protocol: protocol_api.ProtocolContext):
    tips_a = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A1')
    tips_b = protocol.load_labware('opentrons_flex_96_tiprack_1000ul', 'A2')
    trash = protocol.load_trash_bin('A3')
    sample_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 'B2', label='Synthetic-motion plate')
    profile_stages = protocol.load_labware('nest_12_reservoir_15ml', 'B3', label='Water stages A1-A4')
    magnet = protocol.load_module("magneticBlockV1", 'C2')
    output_plate = protocol.load_labware('nest_96_wellplate_100ul_pcr_full_skirt', 'C3', label='Output plate')
    cleanup_res = protocol.load_labware('nest_12_reservoir_15ml', 'D2', label='Water cleanup A1, wash A2, elution A3, waste A12')

    # 8-channel 1000 uL on the left mount, running 200 uL filter tips
    pipette = protocol.load_instrument("flex_8channel_1000", mount="left", tip_racks=[tips_a, tips_b])

    protocol.pause('PUBLIC MOTION PROFILE - WATER ONLY. Confirm water in stage and cleanup wells; no biological samples or reagents.')

    # Synthetic input-preparation stage
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(10.0, profile_stages["A1"].bottom(z=5.0))
        pipette.dispense(10.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Input-preparation checkpoint. No incubation program is included.')

    # Synthetic genome-amplification stage
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(10.0, profile_stages["A2"].bottom(z=5.0))
        pipette.dispense(10.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Genome-amplification checkpoint. No thermal program or QC threshold is included.')

    # Synthetic library-construction stage
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(10.0, profile_stages["A3"].bottom(z=5.0))
        pipette.dispense(10.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Library-construction checkpoint. No method program is included.')

    # Synthetic PCR-enrichment stage
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(10.0, profile_stages["A4"].bottom(z=5.0))
        pipette.dispense(10.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('PCR-enrichment checkpoint. No cycle program is included.')

    # Synthetic cleanup addition
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(20.0, cleanup_res["A1"].bottom(z=5.0))
        pipette.dispense(20.0, _col[0].bottom(z=5.0))
        pipette.mix(3, 10.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Complete the synthetic separation handoff; no hold time is prescribed.')

    # Synthetic supernatant removal
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(20.0, _col[0].bottom(z=5.0))
        pipette.dispense(20.0, cleanup_res["A12"].bottom(z=5.0))
        pipette.drop_tip()

    # Synthetic wash addition
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(20.0, cleanup_res["A2"].bottom(z=5.0))
        pipette.dispense(20.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Confirm the synthetic wash state; no hold time is prescribed.')

    # Synthetic wash removal
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(20.0, _col[0].bottom(z=5.0))
        pipette.dispense(20.0, cleanup_res["A12"].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Complete the synthetic drying and off-magnet handoff; no timing criterion is prescribed.')

    # Synthetic elution addition
    for _col in [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]:
        pipette.pick_up_tip()
        pipette.aspirate(10.0, cleanup_res["A3"].bottom(z=5.0))
        pipette.dispense(10.0, _col[0].bottom(z=5.0))
        pipette.mix(3, 10.0, _col[0].bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Complete the synthetic elution handoff; no hold time is prescribed.')

    # Synthetic output transfer
    for i in range(NUM_COLUMNS):
        _s = sample_plate.columns()[i][0]
        _d = output_plate.columns()[i][0]
        pipette.pick_up_tip()
        pipette.aspirate(10.0, _s.bottom(z=5.0))
        pipette.dispense(10.0, _d.bottom(z=5.0))
        pipette.drop_tip()

    protocol.pause('Motion profile complete. Apply no biological interpretation or public QC threshold.')

