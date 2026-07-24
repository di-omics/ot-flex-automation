"""WGS-preparation distributes, then moves the plate to a reader position.

The closed-loop QC choreography in miniature: distribute reagents into the
sample plate, then have the Flex Gripper carry the plate from B2 to D1 (which
represents the plate-reader handoff). The external orchestration loop can then
evaluate a fluorometric DNA-quantification result before continuing.

Deck:
  A2  1000 uL tips      A3  trash
  B2  sample plate (starts here)
  D1  EMPTY  <- gripper drops the plate here ("plate reader")
  D2  reservoir: A1 = water ("lysis"), A2 = water ("reaction")
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer, MoveLabware


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    SRC, S = "reservoir", "sample_plate"
    return ProtocolSpec(
        name="WGS Preparation + Gripper Move to Reader",
        description="Distribute water reagents, then gripper-move sample plate B2 -> D1 (pretend reader).",
        num_samples=num_samples,
        labware=[
            Labware("tips", "tiprack_1000", "A2", "1000 uL tips"),
            Labware("trash", "trash", "A3"),
            Labware(S, "pcr_plate_96", "B2", "Sample Plate"),
            Labware(SRC, "reservoir_12", "D2", "A1=lysis A2=amplification (water)"),
        ],
        liquids=[Liquid("lysis", f"{SRC}:A1"), Liquid("amplification", f"{SRC}:A2")],
        steps=[
            Transfer(f"{SRC}:A1", S, 5.0, comment="Distribute Lysis Mix (water)"),
            Transfer(f"{SRC}:A2", S, 6.0, comment="Distribute Amplification Mix (water)"),
            MoveLabware(S, "D1", use_gripper=True,
                        comment="Gripper: carry sample plate B2 -> D1 (pretend plate reader)"),
        ],
    )
