"""Phase-0 "hello world": the smallest real motion test.

Pick up a tip, move water from the reservoir into the sample plate, drop the
tip. No reagents, no pauses — just the one thing that matters: *does it move
liquid from here to there.*

Deck matches the configuration that already ran successfully on Studio45
(verified via the robot's run history): 1000 uL tips at A2, NEST PCR plate at
B2, NEST 12-well reservoir at D2 (water in A1), trash at D1, 8-channel 1000 uL
on the LEFT mount.
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    return ProtocolSpec(
        name="Hello Water (Phase-0 motion test)",
        description="Move water reservoir D2:A1 -> sample plate B2. No pauses.",
        num_samples=num_samples,
        labware=[
            Labware("sample_plate", "pcr_plate_96", "B2", "Sample Plate (empty)"),
            Labware("source_plate", "reservoir_12", "D2", "Reservoir (A1 = water)"),
            Labware("tips", "tiprack_1000", "A2", "1000 uL tips"),
            Labware("trash", "trash", "A3"),  # Studio45's movable trash is physically at A3
        ],
        liquids=[Liquid("water", "source_plate:A1", "plain water (dyed to see it)")],
        steps=[
            Transfer("source_plate:A1", "sample_plate", 50.0,
                     comment="Move 50 uL water to each column"),
        ],
    )
