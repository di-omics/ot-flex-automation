"""Synthetic WGS-preparation motion profile as a portable ProtocolSpec.

This example captures generic WGS-preparation choreography without publishing a
biological method. Every liquid is water, every transfer volume is deliberately
uniform, and every off-deck message defers to an operator-supplied local
profile. It is suitable for rendering, simulation, and deck-motion testing only.
"""

from ..spec import ProtocolSpec, Labware, Liquid, Transfer, Handoff


STAGE_TRANSFER_UL = 10.0
CLEANUP_TRANSFER_UL = 20.0
ELUTION_TRANSFER_UL = 10.0


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    source = "profile_stages"
    cleanup = "cleanup_res"
    sample = "sample_plate"
    output = "output_plate"
    return ProtocolSpec(
        name="Whole-Genome Sequencing Preparation - Synthetic Motion Profile",
        description=(
            "Water-only WGS-preparation choreography; no biological method "
            "parameters or QC thresholds."
        ),
        num_samples=num_samples,
        labware=[
            Labware("tips_a", "tiprack_1000", "A1", "1000 uL tips"),
            Labware("tips_b", "tiprack_1000", "A2", "1000 uL tips"),
            Labware("trash", "trash", "A3"),
            Labware(sample, "pcr_plate_96", "B2", "Synthetic-motion plate"),
            Labware(source, "reservoir_12", "B3", "Water stages A1-A4"),
            Labware("magnet", "magnet", "C2"),
            Labware(output, "pcr_plate_96", "C3", "Output plate"),
            Labware(
                cleanup,
                "reservoir_12",
                "D2",
                "Water cleanup A1, wash A2, elution A3, waste A12",
            ),
        ],
        liquids=[
            Liquid("input_preparation", f"{source}:A1", "water"),
            Liquid("genome_amplification", f"{source}:A2", "water"),
            Liquid("library_construction", f"{source}:A3", "water"),
            Liquid("pcr_enrichment", f"{source}:A4", "water"),
            Liquid("cleanup_medium", f"{cleanup}:A1", "water"),
            Liquid("wash_solution", f"{cleanup}:A2", "water"),
            Liquid("elution_solution", f"{cleanup}:A3", "water"),
            Liquid("waste", f"{cleanup}:A12"),
        ],
        steps=[
            Handoff(
                "PUBLIC MOTION PROFILE - WATER ONLY. Confirm water in stage "
                "and cleanup wells; no biological samples or reagents."
            ),
            Transfer(
                f"{source}:A1",
                sample,
                STAGE_TRANSFER_UL,
                comment="Synthetic input-preparation stage",
            ),
            Handoff(
                "Input-preparation checkpoint. No incubation program is included."
            ),
            Transfer(
                f"{source}:A2",
                sample,
                STAGE_TRANSFER_UL,
                comment="Synthetic genome-amplification stage",
            ),
            Handoff(
                "Genome-amplification checkpoint. No thermal program or QC "
                "threshold is included."
            ),
            Transfer(
                f"{source}:A3",
                sample,
                STAGE_TRANSFER_UL,
                comment="Synthetic library-construction stage",
            ),
            Handoff(
                "Library-construction checkpoint. No method program is included."
            ),
            Transfer(
                f"{source}:A4",
                sample,
                STAGE_TRANSFER_UL,
                comment="Synthetic PCR-enrichment stage",
            ),
            Handoff(
                "PCR-enrichment checkpoint. No cycle program is included."
            ),
            Transfer(
                f"{cleanup}:A1",
                sample,
                CLEANUP_TRANSFER_UL,
                mix_after=(3, 10.0),
                comment="Synthetic cleanup addition",
            ),
            Handoff(
                "Complete the synthetic separation handoff; no hold time is prescribed."
            ),
            Transfer(
                sample,
                f"{cleanup}:A12",
                CLEANUP_TRANSFER_UL,
                comment="Synthetic supernatant removal",
            ),
            Transfer(
                f"{cleanup}:A2",
                sample,
                CLEANUP_TRANSFER_UL,
                comment="Synthetic wash addition",
            ),
            Handoff(
                "Confirm the synthetic wash state; no hold time is prescribed."
            ),
            Transfer(
                sample,
                f"{cleanup}:A12",
                CLEANUP_TRANSFER_UL,
                comment="Synthetic wash removal",
            ),
            Handoff(
                "Complete the synthetic drying and off-magnet handoff; no "
                "timing criterion is prescribed."
            ),
            Transfer(
                f"{cleanup}:A3",
                sample,
                ELUTION_TRANSFER_UL,
                mix_after=(3, ELUTION_TRANSFER_UL),
                comment="Synthetic elution addition",
            ),
            Handoff(
                "Complete the synthetic elution handoff; no hold time is prescribed."
            ),
            Transfer(
                sample,
                output,
                ELUTION_TRANSFER_UL,
                comment="Synthetic output transfer",
            ),
            Handoff(
                "Motion profile complete. Apply no biological interpretation "
                "or public QC threshold."
            ),
        ],
    )
