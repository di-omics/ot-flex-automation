"""Water-only alternate-deck WGS choreography with one returned tip column.

This file exists to exercise the Flex deck, lower reservoir aspiration, plate
moves, and return-tip behavior. It contains only uniform synthetic water
transfers and cannot be switched to biological chemistry.
"""

from opentrons import protocol_api


requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "WGS Preparation - Return-Tip Water Motion Test",
    "author": "Di Hu",
    "description": (
        "Water-only alternate-deck WGS choreography. One 8-channel tip column "
        "is reused and returned; no biological method parameters are included."
    ),
}


NUM_SAMPLES = 8
NUM_COLUMNS = 1

PIPETTE_MOUNT = "left"
PIPETTE_NAME = "flex_8channel_1000"
RESERVOIR_SOURCE_Z = 2.0
PLATE_Z = 5.0
USE_GRIPPER_FOR_MAGNET_MOVES = False

SLOT_TIPS_PRIMARY = "A2"
SLOT_TIPS_SECONDARY = "A1"
SLOT_TRASH = "A3"
SLOT_SAMPLE_PLATE = "B2"
SLOT_REAGENT_RES = "B3"
SLOT_MAG_BLOCK = "C2"
SLOT_OUTPUT_PLATE = "C3"
SLOT_CLEANUP_RES = "D2"

TIPRACK_1000 = "opentrons_flex_96_tiprack_1000ul"
PCR_PLATE = "nest_96_wellplate_100ul_pcr_full_skirt"
RESERVOIR_12 = "nest_12_reservoir_15ml"
MAG_BLOCK = "magneticBlockV1"


# Uniform synthetic volumes for water visibility only.
STAGE_TRANSFER_UL = 10.0
CLEANUP_ADD_UL = 20.0
SUPERNATANT_REMOVE_UL = 20.0
WASH_ADD_UL = 20.0
WASH_REMOVE_UL = 20.0
ELUTION_ADD_UL = 10.0
OUTPUT_TRANSFER_UL = 10.0

STAGES = (
    ("input preparation", "A1"),
    ("genome amplification", "A2"),
    ("library construction", "A3"),
    ("PCR enrichment", "A4"),
)


def run(protocol: protocol_api.ProtocolContext):
    if NUM_SAMPLES != 8 or NUM_COLUMNS != 1:
        raise ValueError("This committed return-tip demo is fixed to one 8-well column.")

    protocol.pause(
        "WATER-ONLY RETURN-TIP MOTION TEST.\n"
        "Load water in B3:A1-A4 and D2:A1-A3. Do not load samples or reagents."
    )

    mag_block = protocol.load_module(MAG_BLOCK, SLOT_MAG_BLOCK)
    tips_primary = protocol.load_labware(
        TIPRACK_1000, SLOT_TIPS_PRIMARY, label="Primary tips"
    )
    protocol.load_labware(
        TIPRACK_1000, SLOT_TIPS_SECONDARY, label="Reserved tips"
    )
    protocol.load_trash_bin(SLOT_TRASH)
    sample_plate = protocol.load_labware(
        PCR_PLATE, SLOT_SAMPLE_PLATE, label="Synthetic-motion plate"
    )
    reagent_res = protocol.load_labware(
        RESERVOIR_12,
        SLOT_REAGENT_RES,
        label="Water stages A1-A4",
    )
    output_plate = protocol.load_labware(
        PCR_PLATE, SLOT_OUTPUT_PLATE, label="Output plate"
    )
    cleanup_res = protocol.load_labware(
        RESERVOIR_12,
        SLOT_CLEANUP_RES,
        label="Water cleanup A1, wash A2, elution A3, waste A12",
    )
    pipette = protocol.load_instrument(
        PIPETTE_NAME, mount=PIPETTE_MOUNT, tip_racks=[tips_primary]
    )

    sample_columns = sample_plate.columns()[:NUM_COLUMNS]
    output_columns = output_plate.columns()[:NUM_COLUMNS]
    demo_tip = tips_primary.wells()[0]

    def ensure_tip():
        if not pipette.has_tip:
            pipette.pick_up_tip(demo_tip)

    def distribute(source_well, volume, label, mix_after=None):
        protocol.comment(label)
        ensure_tip()
        for column in sample_columns:
            pipette.aspirate(volume, source_well.bottom(z=RESERVOIR_SOURCE_Z))
            pipette.dispense(volume, column[0].bottom(z=PLATE_Z))
            if mix_after is not None:
                pipette.mix(3, mix_after, column[0].bottom(z=PLATE_Z))

    def sample_to_waste(volume, label):
        protocol.comment(label)
        ensure_tip()
        for column in sample_columns:
            pipette.aspirate(volume, column[0].bottom(z=PLATE_Z))
            pipette.dispense(volume, cleanup_res["A12"].top())

    for stage_name, source_well in STAGES:
        distribute(
            reagent_res[source_well],
            STAGE_TRANSFER_UL,
            f"Synthetic profile stage: {stage_name}",
        )
        protocol.pause(
            f"{stage_name.title()} checkpoint. No biological program is "
            "included; confirm the water-motion state and resume."
        )

    distribute(
        cleanup_res["A1"],
        CLEANUP_ADD_UL,
        "Synthetic cleanup addition",
        mix_after=10.0,
    )
    protocol.pause(
        "Move the plate through the synthetic separation handoff and resume."
    )
    protocol.move_labware(
        sample_plate, mag_block, use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES
    )
    sample_to_waste(SUPERNATANT_REMOVE_UL, "Synthetic supernatant removal")
    distribute(cleanup_res["A2"], WASH_ADD_UL, "Synthetic wash addition")
    protocol.pause("Confirm the synthetic wash state; no hold time is prescribed.")
    sample_to_waste(WASH_REMOVE_UL, "Synthetic wash removal")
    protocol.pause("Confirm the synthetic off-magnet handoff and resume.")
    protocol.move_labware(
        sample_plate,
        SLOT_SAMPLE_PLATE,
        use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES,
    )
    distribute(
        cleanup_res["A3"],
        ELUTION_ADD_UL,
        "Synthetic elution addition",
        mix_after=10.0,
    )
    protocol.pause("Confirm the synthetic elution handoff and resume.")
    protocol.move_labware(
        sample_plate, mag_block, use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES
    )
    protocol.pause(
        "Confirm the synthetic post-elution separation state; no hold time is "
        "prescribed."
    )

    ensure_tip()
    for source_column, output_column in zip(sample_columns, output_columns):
        pipette.aspirate(OUTPUT_TRANSFER_UL, source_column[0].bottom(z=PLATE_Z))
        pipette.dispense(OUTPUT_TRANSFER_UL, output_column[0].bottom(z=PLATE_Z))

    pipette.return_tip()
    protocol.pause(
        "Water-motion test complete. Apply no biological interpretation or QC "
        "threshold to this synthetic run."
    )
