"""Alternate-deck WGS choreography with fresh tips and a private-profile seam.

The committed configuration is a synthetic water-only motion profile. A
biological run requires a private ``OPERATOR_METHOD_PROFILE`` that supplies
every transfer volume and handoff; this public file includes no method recipe.
"""

from opentrons import protocol_api


requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "WGS Preparation - Alternate-Deck Public Motion Profile",
    "author": "Di Hu",
    "description": (
        "Fresh-tip alternate-deck Flex choreography with lower reservoir "
        "aspiration. Public default is water only; no biological parameters."
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


PUBLIC_MOTION_PROFILE = {
    "name": "synthetic-water-motion-test",
    "water_only": True,
    "stage_transfers_ul": {
        "input_preparation": 10.0,
        "genome_amplification": 10.0,
        "library_construction": 10.0,
        "pcr_enrichment": 10.0,
    },
    "cleanup_add_ul": 20.0,
    "supernatant_remove_ul": 20.0,
    "wash_add_ul": 20.0,
    "wash_remove_ul": 20.0,
    "elution_add_ul": 10.0,
    "output_transfer_ul": 10.0,
    "handoffs": {
        "input_preparation": "Complete the operator profile's input-preparation handoff.",
        "genome_amplification": "Complete the operator profile's genome-amplification handoff.",
        "library_construction": "Complete the operator profile's library-construction handoff.",
        "pcr_enrichment": "Complete the operator profile's PCR-enrichment handoff.",
        "cleanup_bind": "Complete the operator profile's separation handoff.",
        "cleanup_elute": "Complete the operator profile's elution handoff.",
        "final_qc": "Apply the operator profile's validated QC criteria.",
    },
}


# Populate only in a private controlled copy.
OPERATOR_METHOD_PROFILE = None

STAGE_WELLS = {
    "input_preparation": "A1",
    "genome_amplification": "A2",
    "library_construction": "A3",
    "pcr_enrichment": "A4",
}


def _active_profile(protocol):
    profile = OPERATOR_METHOD_PROFILE or PUBLIC_MOTION_PROFILE
    required_volume_keys = {
        "cleanup_add_ul",
        "supernatant_remove_ul",
        "wash_add_ul",
        "wash_remove_ul",
        "elution_add_ul",
        "output_transfer_ul",
    }
    missing = required_volume_keys - set(profile)
    missing_stages = set(STAGE_WELLS) - set(profile.get("stage_transfers_ul", {}))
    missing_handoffs = (
        set(STAGE_WELLS)
        | {"cleanup_bind", "cleanup_elute", "final_qc"}
    ) - set(profile.get("handoffs", {}))
    if missing or missing_stages or missing_handoffs:
        raise ValueError(
            "Operator profile is incomplete: "
            f"volume keys={sorted(missing)}, "
            f"stages={sorted(missing_stages)}, "
            f"handoffs={sorted(missing_handoffs)}"
        )
    values = list(profile["stage_transfers_ul"].values())
    values.extend(profile[key] for key in required_volume_keys)
    if any(not isinstance(value, (int, float)) or value <= 0 or value > 200 for value in values):
        raise ValueError("All profile transfer volumes must be numeric and in (0, 200] uL.")

    if profile.get("water_only", False):
        protocol.pause(
            "PUBLIC MOTION PROFILE ACTIVE - WATER ONLY.\n"
            "Load water in B3:A1-A4 and D2:A1-A3. Do not load samples or "
            "reagents. Biological use requires a private validated profile."
        )
    else:
        protocol.comment(
            f"Controlled operator profile active: {profile.get('name', 'unnamed')}"
        )
    return profile


def run(protocol: protocol_api.ProtocolContext):
    if NUM_SAMPLES != 8 or NUM_COLUMNS != 1:
        raise ValueError(
            "The committed alternate-deck choreography is a one-column profile. "
            "Scale only in a private validated copy with tip-capacity planning."
        )

    profile = _active_profile(protocol)

    mag_block = protocol.load_module(MAG_BLOCK, SLOT_MAG_BLOCK)
    tips_primary = protocol.load_labware(
        TIPRACK_1000, SLOT_TIPS_PRIMARY, label="Primary tips"
    )
    tips_secondary = protocol.load_labware(
        TIPRACK_1000, SLOT_TIPS_SECONDARY, label="Secondary tips"
    )
    protocol.load_trash_bin(SLOT_TRASH)
    sample_plate = protocol.load_labware(
        PCR_PLATE, SLOT_SAMPLE_PLATE, label="Working plate"
    )
    reagent_res = protocol.load_labware(
        RESERVOIR_12,
        SLOT_REAGENT_RES,
        label=(
            "Profile stages: A1 input, A2 genome amplification, "
            "A3 library construction, A4 PCR enrichment"
        ),
    )
    output_plate = protocol.load_labware(
        PCR_PLATE, SLOT_OUTPUT_PLATE, label="Output plate"
    )
    cleanup_res = protocol.load_labware(
        RESERVOIR_12,
        SLOT_CLEANUP_RES,
        label="Profile cleanup A1, wash A2, elution A3, waste A12",
    )
    pipette = protocol.load_instrument(
        PIPETTE_NAME,
        mount=PIPETTE_MOUNT,
        tip_racks=[tips_primary, tips_secondary],
    )

    sample_columns = sample_plate.columns()[:NUM_COLUMNS]
    output_columns = output_plate.columns()[:NUM_COLUMNS]

    def distribute(source_well, volume, label, mix_after=None):
        protocol.comment(label)
        for column in sample_columns:
            pipette.pick_up_tip()
            pipette.aspirate(volume, source_well.bottom(z=RESERVOIR_SOURCE_Z))
            pipette.dispense(volume, column[0].bottom(z=PLATE_Z))
            if mix_after is not None:
                pipette.mix(3, mix_after, column[0].bottom(z=PLATE_Z))
            pipette.drop_tip()

    def sample_to_waste(volume, label):
        protocol.comment(label)
        for column in sample_columns:
            pipette.pick_up_tip()
            pipette.aspirate(volume, column[0].bottom(z=PLATE_Z))
            pipette.dispense(volume, cleanup_res["A12"].top())
            pipette.drop_tip()

    for stage, source_well in STAGE_WELLS.items():
        distribute(
            reagent_res[source_well],
            profile["stage_transfers_ul"][stage],
            f"Profile stage: {stage.replace('_', ' ')}",
        )
        protocol.pause(profile["handoffs"][stage])

    distribute(
        cleanup_res["A1"],
        profile["cleanup_add_ul"],
        "Profile-defined cleanup addition",
        mix_after=min(profile["cleanup_add_ul"], 20.0),
    )
    protocol.pause(profile["handoffs"]["cleanup_bind"])
    protocol.move_labware(
        sample_plate, mag_block, use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES
    )
    sample_to_waste(
        profile["supernatant_remove_ul"], "Profile-defined supernatant removal"
    )
    distribute(
        cleanup_res["A2"],
        profile["wash_add_ul"],
        "Profile-defined wash addition",
    )
    protocol.pause(
        "Complete the operator profile's wash handoff; no public hold time is defined."
    )
    sample_to_waste(profile["wash_remove_ul"], "Profile-defined wash removal")
    protocol.pause(
        "Complete the operator profile's drying handoff; no public timing "
        "criterion is defined."
    )
    protocol.move_labware(
        sample_plate,
        SLOT_SAMPLE_PLATE,
        use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES,
    )
    distribute(
        cleanup_res["A3"],
        profile["elution_add_ul"],
        "Profile-defined elution addition",
        mix_after=min(profile["elution_add_ul"], 10.0),
    )
    protocol.pause(profile["handoffs"]["cleanup_elute"])
    protocol.move_labware(
        sample_plate, mag_block, use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES
    )
    protocol.pause(
        "Complete the operator profile's post-elution separation handoff; no "
        "public hold time is defined."
    )

    for source_column, output_column in zip(sample_columns, output_columns):
        pipette.pick_up_tip()
        pipette.aspirate(
            profile["output_transfer_ul"], source_column[0].bottom(z=PLATE_Z)
        )
        pipette.dispense(
            profile["output_transfer_ul"], output_column[0].bottom(z=PLATE_Z)
        )
        pipette.drop_tip()

    protocol.pause(profile["handoffs"]["final_qc"])
