"""Phase-0 "hello world": the smallest real motion test.

Pick up tips, move water from reservoir A1 into every active sample column,
drop tips. No reagents, no pauses, no off-deck handoffs - just the one thing
that matters: *does it move liquid from here to there.* Run this first once the
pipette is calibrated; watch it on the deck.

Deck (matches the protocol's expectations - verify with Labware Position Check):
  A1, A2  200 µL filter tip racks
  B2      empty 96-well PCR plate (destination)
  B3      12-well reservoir, water in A1 (source)
  D1      trash
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    return ProtocolSpec(
        name="Hello Water (Phase-0 motion test)",
        description="Move water reservoir A1 -> every sample column. No pauses.",
        num_samples=num_samples,
        labware=[
            Labware("sample_plate", "pcr_plate_96", "B2", "Sample Plate (empty)"),
            Labware("source_plate", "reservoir_12", "B3", "Reservoir (A1 = water)"),
            Labware("tips_a", "tiprack_200", "A1"),
            Labware("tips_b", "tiprack_200", "A2"),
            Labware("trash", "trash", "D1"),
        ],
        liquids=[Liquid("water", "source_plate:A1", "plain water")],
        steps=[
            Transfer("source_plate:A1", "sample_plate", 20.0,
                     comment="Move 20 uL water to each column"),
        ],
    )
