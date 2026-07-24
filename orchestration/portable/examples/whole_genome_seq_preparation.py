"""Synthetic WGS-preparation stage distribution.

Two uniform water transfers exercise multi-well sourcing and external handoffs.
No biological volume, incubation program, or QC threshold is included.
"""

from ..spec import ProtocolSpec, Labware, Liquid, Transfer, Handoff


MOTION_TRANSFER_UL = 10.0


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    return ProtocolSpec(
        name="WGS Preparation - Synthetic Stage Distribution",
        description="Uniform water transfers with method-neutral handoffs.",
        num_samples=num_samples,
        labware=[
            Labware("sample_plate", "pcr_plate_96", "B2", "Synthetic-motion plate"),
            Labware(
                "source_plate",
                "reservoir_12",
                "B3",
                "Water stages A1-A2",
            ),
            Labware("tips_a", "tiprack_200", "A1"),
            Labware("tips_b", "tiprack_200", "A2"),
            Labware("trash", "trash", "D1"),
        ],
        liquids=[
            Liquid("input_preparation", "source_plate:A1", "water"),
            Liquid("genome_amplification", "source_plate:A2", "water"),
        ],
        steps=[
            Handoff(
                "PUBLIC MOTION PROFILE - WATER ONLY. Confirm water in A1-A2."
            ),
            Transfer(
                "source_plate:A1",
                "sample_plate",
                MOTION_TRANSFER_UL,
                comment="Synthetic input-preparation stage",
            ),
            Handoff(
                "Input-preparation checkpoint. No incubation program is included."
            ),
            Transfer(
                "source_plate:A2",
                "sample_plate",
                MOTION_TRANSFER_UL,
                comment="Synthetic genome-amplification stage",
            ),
            Handoff(
                "Genome-amplification checkpoint. No thermal program or QC "
                "threshold is included."
            ),
        ],
    )
