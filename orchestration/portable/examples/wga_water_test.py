"""WGA reagent distributes - live water test (Studio45).

Section 1 of whole-genome sequencing, the choreography only: distribute "lysis" from
reservoir A1 and "reaction" from reservoir A2 to the sample plate. Two reagents
from two different wells - the multi-well sourcing - with water, no pauses, so
it runs continuously as a motion test.

Reservoir kept at D2 (where it already sits from the hello-water run) to minimize
deck changes. The full protocol uses B3 for reagents; we'll lay out the full deck
when we run the whole thing.

Deck:
  A2  1000 uL tips      A3  trash
  B2  empty sample plate
  D2  reservoir: A1 = water ("lysis"), A2 = water ("reaction")  - dye to see it
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    SRC, S = "reservoir", "sample_plate"
    return ProtocolSpec(
        name="WGA Distributes - Water Test (Studio45)",
        description="Distribute water from reservoir A1 + A2 to sample plate. No pauses.",
        num_samples=num_samples,
        labware=[
            Labware("tips", "tiprack_1000", "A2", "1000 uL tips"),
            Labware("trash", "trash", "A3"),
            Labware(S, "pcr_plate_96", "B2", "Sample Plate (empty)"),
            Labware(SRC, "reservoir_12", "D2", "A1=lysis A2=reaction (water)"),
        ],
        liquids=[Liquid("lysis", f"{SRC}:A1"), Liquid("reaction", f"{SRC}:A2")],
        steps=[
            Transfer(f"{SRC}:A1", S, 5.0, comment="Distribute Lysis Mix (water)"),
            Transfer(f"{SRC}:A2", S, 6.0, comment="Distribute Reaction Mix (water)"),
        ],
    )
