"""Example: the whole-genome amplification section, as a portable ProtocolSpec.

Transcribed from `protocols/whole_genome_seq_flex.py` Section 1 (WGA): distribute
Lysis Mix, then Reaction Mix, to every sample column, with the incubation /
thermal-cycler handoffs in between. This is the vendor-neutral source of truth -
render it to the Flex today, to a STAR/Bravo worklist for the port.
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer, Handoff


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    return ProtocolSpec(
        name="Whole-genome amplification (portable)",
        description="WGA reagent distribution + off-deck handoffs, platform-neutral.",
        num_samples=num_samples,
        labware=[
            Labware("sample_plate", "pcr_plate_96", "B2", "Sample Plate"),
            Labware("source_plate", "reservoir_12", "B3",
                    "Source 12-well (A1=lysis A2=reaction)"),
            Labware("tips_a", "tiprack_200", "A1"),
            Labware("tips_b", "tiprack_200", "A2"),
            Labware("trash", "trash", "D1"),
        ],
        liquids=[
            Liquid("lysis_mix", "source_plate:A1", "L1/L2/L3 master mix"),
            Liquid("reaction_mix", "source_plate:A2", "R1/R2 master mix"),
        ],
        steps=[
            Handoff("LYSIS MIX in source A1 (water for motion test). Resume to distribute."),
            Transfer("source_plate:A1", "sample_plate", 5.0, comment="Distribute Lysis Mix"),
            Handoff("Seal plate. Incubate RT on ice 20 min. Resume when done."),
            Handoff("REACTION MIX in source A2 (water for motion test). Resume to distribute."),
            Transfer("source_plate:A2", "sample_plate", 6.0, comment="Distribute Reaction Mix"),
            Handoff(
                "Seal/flick/spin, keep on ice. THERMAL CYCLER DNA Amplification "
                "(lid 70C): 30C 2.5h -> 65C 3min -> 4C hold. Return plate when done."
            ),
        ],
    )
