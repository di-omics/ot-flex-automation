"""Method-neutral methylation-sequencing choreography for Opentrons Flex.

The committed profile is a synthetic, water-only motion test. It deliberately
does not choose a specific methylation chemistry or publish biological volumes,
thermal programs, cycle counts, or QC gates.

For biological use, create a private copy and populate
``OPERATOR_METHOD_PROFILE`` from a controlled, validated method.
"""

from opentrons import protocol_api


requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "Methylation Sequencing - Public Motion Profile",
    "author": "Di Hu",
    "description": (
        "Water-only Flex choreography for methylation-sequencing preparation. "
        "Draft and motion-test ready; no biological method parameters included."
    ),
}


NUM_SAMPLES = 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8

RIGHT_PIPETTE = "flex_8channel_1000"

SLOT_TIPS_1 = "A1"
SLOT_TIPS_2 = "A2"
SLOT_TIPS_3 = "A3"
SLOT_PLATE_A = "B2"
SLOT_SOURCE = "B3"
SLOT_MAG_BLOCK = "C2"
SLOT_PLATE_B = "C3"
SLOT_CLEANUP = "D2"
SLOT_TRASH = "D1"


# These uniform values are synthetic water transfers for visible motion only.
# They are not derived from a methylation-sequencing method.
PUBLIC_MOTION_PROFILE = {
    "name": "synthetic-water-motion-test",
    "water_only": True,
    "stages": [
        {
            "id": "library_construction",
            "source_well": "A1",
            "transfer_ul": 10.0,
            "cleanup": True,
            "handoff": (
                "Synthetic library-construction checkpoint. No biological "
                "incubation program is included; confirm the water-motion state "
                "and resume."
            ),
        },
        {
            "id": "methylation_processing",
            "source_well": "A2",
            "transfer_ul": 10.0,
            "cleanup": True,
            "handoff": (
                "Synthetic methylation-processing checkpoint. The public "
                "profile does not select a specific chemistry; confirm the "
                "water-motion state and resume."
            ),
        },
        {
            "id": "pcr_enrichment",
            "source_well": "A3",
            "transfer_ul": 10.0,
            "cleanup": True,
            "handoff": (
                "Synthetic PCR-enrichment checkpoint. No cycle program is "
                "included; confirm the water-motion state and resume."
            ),
        },
    ],
    "cleanup_add_ul": 20.0,
    "supernatant_remove_ul": 20.0,
    "wash_add_ul": 20.0,
    "wash_remove_ul": 20.0,
    "elution_add_ul": 10.0,
    "eluate_transfer_ul": 10.0,
    "cleanup_handoff": (
        "Synthetic cleanup checkpoint. Complete the locally validated "
        "separation handoff, or confirm the water-motion state, then resume."
    ),
    "elution_handoff": (
        "Synthetic elution checkpoint. Complete the locally validated "
        "separation handoff, or confirm the water-motion state, then resume."
    ),
    "final_qc_handoff": (
        "Apply the operator profile's validated methylation-library QC criteria. "
        "This public motion profile intentionally defines no biological threshold."
    ),
}


# Populate only in a private, controlled copy. The public repository supplies no
# biological fallback values.
OPERATOR_METHOD_PROFILE = None


def _active_profile(protocol):
    profile = OPERATOR_METHOD_PROFILE or PUBLIC_MOTION_PROFILE
    required = {
        "stages",
        "cleanup_add_ul",
        "supernatant_remove_ul",
        "wash_add_ul",
        "wash_remove_ul",
        "elution_add_ul",
        "eluate_transfer_ul",
        "cleanup_handoff",
        "elution_handoff",
        "final_qc_handoff",
    }
    missing = required - set(profile)
    if missing:
        raise ValueError(f"Operator profile is incomplete: {sorted(missing)}")
    if not profile["stages"]:
        raise ValueError("Operator profile must define at least one stage.")

    allowed_wells = {f"A{index}" for index in range(1, 12)}
    volumes = [
        profile["cleanup_add_ul"],
        profile["supernatant_remove_ul"],
        profile["wash_add_ul"],
        profile["wash_remove_ul"],
        profile["elution_add_ul"],
        profile["eluate_transfer_ul"],
    ]
    for stage in profile["stages"]:
        stage_missing = {"id", "source_well", "transfer_ul", "cleanup", "handoff"} - set(stage)
        if stage_missing:
            raise ValueError(
                f"Stage {stage.get('id', '<unnamed>')} is incomplete: "
                f"{sorted(stage_missing)}"
            )
        if stage["source_well"] not in allowed_wells:
            raise ValueError(f"Unsupported source well: {stage['source_well']}")
        volumes.append(stage["transfer_ul"])
    if any(not isinstance(value, (int, float)) or value <= 0 or value > 200 for value in volumes):
        raise ValueError("All profile transfer volumes must be numeric and in (0, 200] uL.")

    if profile.get("water_only", False):
        protocol.pause(
            "PUBLIC MOTION PROFILE ACTIVE - WATER ONLY.\n"
            "Load water in B3:A1-A3 and D2:A1-A3. Do not load biological "
            "samples or reagents. A biological run requires a private validated "
            "OPERATOR_METHOD_PROFILE."
        )
    else:
        protocol.comment(
            f"Controlled operator profile active: {profile.get('name', 'unnamed')}"
        )
    return profile


def run(protocol: protocol_api.ProtocolContext):
    if NUM_SAMPLES != 8:
        raise ValueError(
            "The committed public choreography is a one-column motion profile "
            "(NUM_SAMPLES=8). Scale only in a private validated profile."
        )

    profile = _active_profile(protocol)

    protocol.load_module("magneticBlockV1", SLOT_MAG_BLOCK)
    tips_1 = protocol.load_labware(
        "opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_1
    )
    tips_2 = protocol.load_labware(
        "opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_2
    )
    tips_3 = protocol.load_labware(
        "opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_3
    )
    plate_a = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt",
        SLOT_PLATE_A,
        label="Working plate A",
    )
    plate_b = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt",
        SLOT_PLATE_B,
        label="Working plate B",
    )
    source = protocol.load_labware(
        "nest_12_reservoir_15ml",
        SLOT_SOURCE,
        label="Operator-profile stages; public profile uses water in A1-A3",
    )
    cleanup = protocol.load_labware(
        "nest_12_reservoir_15ml",
        SLOT_CLEANUP,
        label="Profile cleanup: A1 cleanup, A2 wash, A3 elution, A12 waste",
    )
    protocol.load_trash_bin(SLOT_TRASH)

    pipette = protocol.load_instrument(
        RIGHT_PIPETTE, mount="right", tip_racks=[tips_1, tips_2, tips_3]
    )

    def columns(plate):
        return plate.columns()[:NUM_COLUMNS]

    def distribute(plate, source_well, volume, label, mix_after=None):
        protocol.comment(label)
        for column in columns(plate):
            pipette.pick_up_tip()
            pipette.aspirate(volume, source_well.bottom(z=2))
            pipette.dispense(volume, column[0].bottom(z=2))
            if mix_after is not None:
                pipette.mix(3, mix_after, column[0].bottom(z=2))
            pipette.drop_tip()

    def plate_to_waste(plate, volume, label):
        protocol.comment(label)
        for column in columns(plate):
            pipette.pick_up_tip()
            pipette.aspirate(volume, column[0].bottom(z=1))
            pipette.dispense(volume, cleanup["A12"].top())
            pipette.drop_tip()

    def cleanup_to_plate(work, destination, stage_id):
        distribute(
            work,
            cleanup["A1"],
            profile["cleanup_add_ul"],
            f"{stage_id}: profile-defined cleanup addition",
            mix_after=min(profile["cleanup_add_ul"], 20.0),
        )
        protocol.pause(profile["cleanup_handoff"])
        plate_to_waste(
            work,
            profile["supernatant_remove_ul"],
            f"{stage_id}: profile-defined supernatant removal",
        )
        distribute(
            work,
            cleanup["A2"],
            profile["wash_add_ul"],
            f"{stage_id}: profile-defined wash addition",
        )
        protocol.pause(
            "Complete the operator profile's wash handoff. "
            "No public hold time is defined."
        )
        plate_to_waste(
            work,
            profile["wash_remove_ul"],
            f"{stage_id}: profile-defined wash removal",
        )
        protocol.pause(
            "Complete the operator profile's drying and off-magnet handoff. "
            "No public timing criterion is defined."
        )
        distribute(
            work,
            cleanup["A3"],
            profile["elution_add_ul"],
            f"{stage_id}: profile-defined elution addition",
            mix_after=min(profile["elution_add_ul"], 10.0),
        )
        protocol.pause(profile["elution_handoff"])
        for source_column, destination_column in zip(
            columns(work), columns(destination)
        ):
            pipette.pick_up_tip()
            pipette.aspirate(
                profile["eluate_transfer_ul"], source_column[0].bottom(z=1)
            )
            pipette.dispense(
                profile["eluate_transfer_ul"],
                destination_column[0].bottom(z=2),
            )
            pipette.drop_tip()

    work, destination = plate_a, plate_b
    for stage in profile["stages"]:
        distribute(
            work,
            source[stage["source_well"]],
            stage["transfer_ul"],
            f"Profile stage: {stage['id'].replace('_', ' ')}",
        )
        protocol.pause(stage["handoff"])
        if stage["cleanup"]:
            cleanup_to_plate(work, destination, stage["id"])
            work, destination = destination, work

    protocol.pause(profile["final_qc_handoff"])
