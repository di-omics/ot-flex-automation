"""Whole-genome sequencing preparation choreography for an Opentrons Flex.

The committed configuration is a synthetic, water-only motion profile. It
exercises source selection, column-wise transfers, cleanup choreography, and
operator handoffs without embedding a commercial or laboratory method.

To run biological material, make a private copy and populate
``OPERATOR_METHOD_PROFILE`` from a locally controlled and validated method. Do
not treat the synthetic values below as wet-lab instructions.
"""

from opentrons import protocol_api


requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "Whole-Genome Sequencing Preparation - Public Motion Profile",
    "author": "Di Hu",
    "description": (
        "Water-only Flex choreography for whole-genome sequencing preparation. "
        "The deck workflow has been run end to end on the Flex; no biological "
        "method parameters are included in this public file."
    ),
}


NUM_SAMPLES = 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8

RIGHT_PIPETTE = "flex_8channel_1000"

SLOT_TIPS_1 = "A1"
SLOT_TIPS_2 = "A2"
SLOT_SAMPLE_PLATE = "B2"
SLOT_SOURCE = "B3"
SLOT_MAG_BLOCK = "C2"
SLOT_OUTPUT_PLATE = "C3"
SLOT_CLEANUP = "D2"
SLOT_TRASH = "D1"


# Public values are deliberately uniform synthetic water transfers. They are
# chosen only to make the motion path visible and stay within the loaded
# labware. They do not encode a sequencing method.
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
        "input_preparation": (
            "Synthetic input-preparation checkpoint. No incubation program is "
            "included; confirm the water-motion state and resume."
        ),
        "genome_amplification": (
            "Synthetic genome-amplification checkpoint. No thermal program or "
            "acceptance threshold is included; confirm the water-motion state "
            "and resume."
        ),
        "library_construction": (
            "Synthetic library-construction checkpoint. No method-specific "
            "program is included; confirm the water-motion state and resume."
        ),
        "pcr_enrichment": (
            "Synthetic PCR-enrichment checkpoint. No cycle program is included; "
            "confirm the water-motion state and resume."
        ),
        "cleanup_bind": (
            "Synthetic cleanup checkpoint. Move the plate through the locally "
            "validated separation handoff, or simply confirm the motion-test "
            "state, then resume."
        ),
        "cleanup_elute": (
            "Synthetic elution checkpoint. Complete the locally validated "
            "separation handoff, or confirm the motion-test state, then resume."
        ),
        "final_qc": (
            "Apply the operator profile's validated QC criteria. This public "
            "motion profile intentionally defines no biological threshold."
        ),
    },
}


# Populate only in a private, controlled copy. Required keys are validated
# below; no biological defaults are supplied by this repository.
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
            "Load water in B3:A1-A4 and D2:A1-A3. Do not load biological "
            "samples or reagents. A biological run requires a private validated "
            "OPERATOR_METHOD_PROFILE."
        )
    else:
        protocol.comment(
            f"Controlled operator profile active: {profile.get('name', 'unnamed')}"
        )
    return profile


def run(protocol: protocol_api.ProtocolContext):
    if NUM_SAMPLES != 8 or NUM_COLUMNS != 1:
        raise ValueError(
            "The committed public choreography is a one-column profile. "
            "Scale only in a private validated copy with tip-capacity planning."
        )

    profile = _active_profile(protocol)

    protocol.load_module("magneticBlockV1", SLOT_MAG_BLOCK)
    tips_1 = protocol.load_labware(
        "opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_1
    )
    tips_2 = protocol.load_labware(
        "opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_2
    )
    sample_plate = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt",
        SLOT_SAMPLE_PLATE,
        label="Sample or synthetic-motion plate",
    )
    source = protocol.load_labware(
        "nest_12_reservoir_15ml",
        SLOT_SOURCE,
        label=(
            "Profile stages: A1 input, A2 genome amplification, "
            "A3 library construction, A4 PCR enrichment"
        ),
    )
    output_plate = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt",
        SLOT_OUTPUT_PLATE,
        label="Output plate",
    )
    cleanup = protocol.load_labware(
        "nest_12_reservoir_15ml",
        SLOT_CLEANUP,
        label="Profile cleanup: A1 cleanup, A2 wash, A3 elution, A12 waste",
    )
    protocol.load_trash_bin(SLOT_TRASH)

    pipette = protocol.load_instrument(
        RIGHT_PIPETTE, mount="right", tip_racks=[tips_1, tips_2]
    )
    sample_columns = sample_plate.columns()[:NUM_COLUMNS]
    output_columns = output_plate.columns()[:NUM_COLUMNS]

    def distribute(source_well, volume, label, mix_after=None):
        protocol.comment(label)
        for column in sample_columns:
            pipette.pick_up_tip()
            pipette.aspirate(volume, source_well.bottom(z=2))
            pipette.dispense(volume, column[0].bottom(z=2))
            if mix_after is not None:
                pipette.mix(3, mix_after, column[0].bottom(z=2))
            pipette.drop_tip()

    def sample_to_waste(volume, label):
        protocol.comment(label)
        for column in sample_columns:
            pipette.pick_up_tip()
            pipette.aspirate(volume, column[0].bottom(z=1))
            pipette.dispense(volume, cleanup["A12"].top())
            pipette.drop_tip()

    for stage, source_well in STAGE_WELLS.items():
        distribute(
            source[source_well],
            profile["stage_transfers_ul"][stage],
            f"Profile stage: {stage.replace('_', ' ')}",
        )
        protocol.pause(profile["handoffs"][stage])

    distribute(
        cleanup["A1"],
        profile["cleanup_add_ul"],
        "Profile-defined cleanup addition",
        mix_after=min(profile["cleanup_add_ul"], 20.0),
    )
    protocol.pause(profile["handoffs"]["cleanup_bind"])
    sample_to_waste(
        profile["supernatant_remove_ul"],
        "Profile-defined supernatant removal",
    )
    distribute(
        cleanup["A2"],
        profile["wash_add_ul"],
        "Profile-defined wash addition",
    )
    protocol.pause(
        "Complete the operator profile's wash handoff. No public hold time is defined."
    )
    sample_to_waste(profile["wash_remove_ul"], "Profile-defined wash removal")
    protocol.pause(
        "Complete the operator profile's drying and off-magnet handoff. "
        "No public timing criterion is defined."
    )
    distribute(
        cleanup["A3"],
        profile["elution_add_ul"],
        "Profile-defined elution addition",
        mix_after=min(profile["elution_add_ul"], 10.0),
    )
    protocol.pause(profile["handoffs"]["cleanup_elute"])

    for source_column, output_column in zip(sample_columns, output_columns):
        pipette.pick_up_tip()
        pipette.aspirate(
            profile["output_transfer_ul"], source_column[0].bottom(z=1)
        )
        pipette.dispense(
            profile["output_transfer_ul"], output_column[0].bottom(z=2)
        )
        pipette.drop_tip()

    protocol.pause(profile["handoffs"]["final_qc"])
