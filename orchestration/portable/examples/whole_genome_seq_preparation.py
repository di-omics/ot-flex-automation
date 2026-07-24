"""Example: the genome-amplification stage of WGS preparation.

Distribute lysis mix, then amplification mix, to every sample column, with
incubation and thermal-cycler handoffs between them.
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer, Handoff


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    return ProtocolSpec(
        name="WGS preparation - genome amplification",
        description="Genome-amplification reagent distribution and off-deck handoffs.",
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
            Liquid("lysis_mix", "source_plate:A1", "functional lysis master mix"),
            Liquid("amplification_mix", "source_plate:A2", "functional amplification master mix"),
        ],
        steps=[
            Handoff("LYSIS MIX in source A1 (water for motion test). Resume to distribute."),
            Transfer("source_plate:A1", "sample_plate", 5.0, comment="Distribute Lysis Mix"),
            Handoff("Seal plate. Incubate RT on ice 20 min. Resume when done."),
            Handoff("AMPLIFICATION MIX in source A2 (water for motion test). Resume to distribute."),
            Transfer("source_plate:A2", "sample_plate", 6.0, comment="Distribute Amplification Mix"),
            Handoff(
                "Seal/flick/spin, keep on ice. THERMAL CYCLER DNA Amplification "
                "(lid 70C): 30C 2.5h -> 65C 3min -> 4C hold. Return plate when done."
            ),
        ],
    )
