"""WGA distributes, then gripper-move the plate to a "plate reader" (Studio45).

The closed-loop QC choreography in miniature: distribute reagents into the
sample plate, then have the Flex Gripper carry the plate from B2 to D1 (which
we're pretending is the plate reader). This is the move that, in the real
orchestration loop, hands the plate off for a Qubit-replacement read before
deciding whether to proceed.

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
        name="WGA Distributes + Gripper Move to Reader (Studio45)",
        description="Distribute water reagents, then gripper-move sample plate B2 -> D1 (pretend reader).",
        num_samples=num_samples,
        labware=[
            Labware("tips", "tiprack_1000", "A2", "1000 uL tips"),
            Labware("trash", "trash", "A3"),
            Labware(S, "pcr_plate_96", "B2", "Sample Plate"),
            Labware(SRC, "reservoir_12", "D2", "A1=lysis A2=reaction (water)"),
        ],
        liquids=[Liquid("lysis", f"{SRC}:A1"), Liquid("reaction", f"{SRC}:A2")],
        steps=[
            Transfer(f"{SRC}:A1", S, 5.0, comment="Distribute Lysis Mix (water)"),
            Transfer(f"{SRC}:A2", S, 6.0, comment="Distribute Reaction Mix (water)"),
            MoveLabware(S, "D1", use_gripper=True,
                        comment="Gripper: carry sample plate B2 -> D1 (pretend plate reader)"),
        ],
    )
