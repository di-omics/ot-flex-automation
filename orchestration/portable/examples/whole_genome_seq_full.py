"""Whole-genome sequencing preparation as a portable ProtocolSpec.

The workflow covers genome amplification, library preparation, and bead cleanup.
Each functional reagent comes from its own reservoir well.

Deck:
  A1, A2  1000 uL tip racks        A3  trash
  B2      sample plate             B3  reagent reservoir (A1-A7, see below)
  C2      magnet (manual moves)    C3  output plate
  D2      bead/wash reservoir (A1 beads, A2 EtOH, A3 elution, A12 waste)

Reagent reservoir B3:  A1 Lysis · A2 Amplification · A3 End preparation
                       A4 Repair · A5 Ligation · A6 Adapters
                       A7 Library amplification

KNOWN REALISM GAPS (inherited from the assumed baseline - fix before a real run):
  * Sample plate is a 100 uL PCR plate but the bead cleanup adds 180 uL EtOH -
    physically overflows. Real bead cleanup needs a deeper plate or smaller wash.
  * Magnet steps are manual pauses; with the Flex Gripper these could become
    automated moveLabware to C2.
  * Small additions on a 1000 uL pipette are suitable for motion testing but
    require an appropriately sized pipette for validated wet-lab runs.
"""
from ..spec import ProtocolSpec, Labware, Liquid, Transfer, Handoff, Delay

ETOH_VOL = 180.0  # see realism note above


def build_spec(num_samples: int = 8) -> ProtocolSpec:
    SRC, BEAD, S, OUT = "reagent_res", "bead_res", "sample_plate", "output_plate"
    return ProtocolSpec(
        name="Whole-Genome Sequencing Preparation",
        description="Genome amplification, library preparation, and bead cleanup.",
        num_samples=num_samples,
        labware=[
            Labware("tips_a", "tiprack_1000", "A1", "1000 uL tips"),
            Labware("tips_b", "tiprack_1000", "A2", "1000 uL tips"),
            Labware("trash", "trash", "A3"),
            Labware(S, "pcr_plate_96", "B2", "Sample Plate"),
            Labware(SRC, "reservoir_12", "B3", "Reagents A1-A7"),
            Labware("magnet", "magnet", "C2"),
            Labware(OUT, "pcr_plate_96", "C3", "Output Plate"),
            Labware(BEAD, "reservoir_12", "D2", "Beads/EtOH/Elution/Waste"),
        ],
        liquids=[
            Liquid("lysis", f"{SRC}:A1"), Liquid("amplification", f"{SRC}:A2"),
            Liquid("end_preparation", f"{SRC}:A3"), Liquid("repair", f"{SRC}:A4"),
            Liquid("ligation", f"{SRC}:A5"), Liquid("adapters", f"{SRC}:A6"),
            Liquid("library_amplification", f"{SRC}:A7"),
            Liquid("beads", f"{BEAD}:A1"), Liquid("etoh", f"{BEAD}:A2"),
            Liquid("elution", f"{BEAD}:A3"), Liquid("waste", f"{BEAD}:A12"),
        ],
        steps=[
            # ── Section 1: Genome amplification ──
            Handoff("LYSIS MIX in reagent reservoir A1 (water for motion test)."),
            Transfer(f"{SRC}:A1", S, 5.0, comment="Distribute Lysis Mix"),
            Handoff("Seal. Incubate RT on ice 20 min. Resume."),
            Handoff("AMPLIFICATION MIX in reagent reservoir A2."),
            Transfer(f"{SRC}:A2", S, 6.0, comment="Distribute Amplification Mix"),
            Handoff("Seal/flick/spin. THERMAL CYCLER DNA Amplification (lid 70C): "
                    "30C 2.5h -> 65C 3min -> 4C. Return plate."),
            Handoff("QC: fluorometric DNA yield >800 ng average; fragment size ~1275 bp. "
                    "Prepare 2 ng/uL normalized plate. Return to B2."),
            # ── Section 2: Library Prep ──
            Handoff("END-PREPARATION MIX in reagent reservoir A3."),
            Transfer(f"{SRC}:A3", S, 5.0, comment="Distribute end-preparation mix"),
            Handoff("THERMAL CYCLER END PREPARATION (lid 105C): 37C 10min -> 4C. Return on ice."),
            Handoff("REPAIR MIX in reagent reservoir A4."),
            Transfer(f"{SRC}:A4", S, 5.0, mix_after=(5, 5), comment="Distribute repair mix"),
            Handoff("THERMAL CYCLER REPAIR (lid 105C): 4C 30s -> 30C 5min -> 65C 30min -> 4C."),
            Handoff("Vortex adapter plate briefly. Spin down."),
            Transfer(f"{SRC}:A6", S, 5.0, comment="Distribute Adapters"),
            Transfer(f"{SRC}:A5", S, 5.0, comment="Distribute ligation reagent"),
            Handoff("Seal. Vortex medium. Spin. Incubate RT 15 min. Proceed."),
            Handoff("LIBRARY-AMPLIFICATION MIX in reagent reservoir A7. Start the program and pause at 98C."),
            Transfer(f"{SRC}:A7", S, 20.0, mix_after=(5, 20), comment="Distribute library-amplification mix"),
            Handoff("THERMAL CYCLER LIBRARY AMPLIFICATION (lid 105C): 98C 45s -> "
                    "[98C 15s/60C 30s/72C 45s]x8 -> 72C 60s -> 4C. Return on ice."),
            # ── Section 3: Bead Cleanup ──
            Handoff("Vortex SPRI beads 10s. Fresh 80% EtOH in bead reservoir A2."),
            Transfer(f"{BEAD}:A1", S, 30.0, comment="Add SPRI beads"),
            Handoff("Seal. Vortex 10s. Incubate RT 5 min. Spin. "
                    "Place plate ON Magnetic Block (C2). Wait 3 min until clear."),
            Transfer(S, f"{BEAD}:A12", 70.0, comment="Remove supernatant to waste"),
            # EtOH wash 1
            Transfer(f"{BEAD}:A2", S, ETOH_VOL, comment="EtOH wash 1 add"),
            Delay(30, "EtOH wash 1 soak"),
            Transfer(S, f"{BEAD}:A12", ETOH_VOL, comment="EtOH wash 1 remove"),
            # EtOH wash 2
            Transfer(f"{BEAD}:A2", S, ETOH_VOL, comment="EtOH wash 2 add"),
            Delay(30, "EtOH wash 2 soak"),
            Transfer(S, f"{BEAD}:A12", ETOH_VOL, comment="EtOH wash 2 remove"),
            Handoff("Remove residual EtOH with P20. Air dry 3 min - do NOT over-dry."),
            Handoff("Remove plate FROM magnet."),
            Transfer(f"{BEAD}:A3", S, 42.0, mix_after=(10, 35), comment="Add Elution Buffer + mix"),
            Handoff("Incubate RT 2 min. Return to magnet. Wait 2 min until clear."),
            Transfer(S, OUT, 40.0, comment="Transfer eluate -> output plate"),
            Handoff("DONE. POST-QC: fluorometric DNA quantification and fragment analysis. "
                    "Pool + final 0.75x cleanup before sequencing."),
        ],
    )
