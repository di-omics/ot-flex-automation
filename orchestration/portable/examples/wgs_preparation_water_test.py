"""WGS-preparation stage distribution as a live water test.

The choreography only: distribute two equal water stages from two reservoir
wells to the sample plate. Equal synthetic volumes keep this a motion-only
example rather than a wet-lab method.

The reservoir stays at D2 to minimize deck changes. The full protocol uses B3
for reagents.

Deck:
  A2  1000 uL tips      A3  trash
  B2  empty sample plate
  D2  reservoir: A1 = water ("stage 1"), A2 = water ("stage 2")
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    SRC, S = "reservoir", "sample_plate"
    return ProtocolSpec(
        name="WGS Preparation - Water Test",
        description="Distribute water from reservoir A1 + A2 to sample plate. No pauses.",
        num_samples=num_samples,
        labware=[
            Labware("tips", "tiprack_1000", "A2", "1000 uL tips"),
            Labware("trash", "trash", "A3"),
            Labware(S, "pcr_plate_96", "B2", "Sample Plate (empty)"),
            Labware(SRC, "reservoir_12", "D2", "A1=stage 1 A2=stage 2 (water)"),
        ],
        liquids=[Liquid("stage_1", f"{SRC}:A1"), Liquid("stage_2", f"{SRC}:A2")],
        steps=[
            Transfer(f"{SRC}:A1", S, 10.0, comment="Distribute synthetic stage 1 (water)"),
            Transfer(f"{SRC}:A2", S, 10.0, comment="Distribute synthetic stage 2 (water)"),
        ],
    )
