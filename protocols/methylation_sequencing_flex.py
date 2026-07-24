from opentrons import protocol_api

# ──────────────────────────────────────────────────────────────────────
# Methylation Sequencing - Library Preparation (Opentrons Flex)
#
# Automates a conversion-based methylation-sequencing workflow on the
# Flex. Produces genome-wide methylation libraries for downstream analysis.
#
# STATUS: DRAFT - first implementation, motion-test ready, NOT yet
# bench-validated. The whole-genome sequencing protocol in this repo has been run
# end-to-end; this one has not. Treat volumes/timing as the starting
# point for a validation run, not a finished method.
#
# What the Flex does: every enzymatic / master-mix / bead addition.
# Operator handoffs via protocol.pause(): off-deck DNA fragmentation,
# every thermal-cycler
# program, vortex/spin, and moving the plate on/off the Magnetic Block.
#
# Enzyme reservoir (12-well, slot B3):
#   A1 = End Prep MM      A2 = Adapter          A3 = Ligation MM
#   A4 = Protection MM    A5 = Cofactor         A6 = Stop Reagent
#   A7 = Denaturation     A8 = Conversion MM    A9 = Index Primers
#   A10 = PCR Master Mix
# Bead / wash reservoir (12-well, slot D2):
#   A1 = Sample Purification Beads   A2 = 80% EtOH
#   A3 = Elution Buffer              A12 = liquid waste
#
# Two PCR plates (B2, C3) ping-pong through the 3 cleanups; the operator
# swaps a fresh plate into the spent-beads slot when prompted.
#
# TIPS: 200 uL FILTER tips only (opentrons_flex_96_filtertiprack_200ul),
#   run on the 8-channel 1000 uL pipette - the only Flex pipette
#   compatible with 200 uL tips. Every transfer is <=200 uL. Three racks
#   (A1/A2/A3) cover the ~34 tip pickups one column needs across the 3
#   SPRI cleanups (a single column would exhaust 2 racks mid-run).
#
# CAVEATS for a real run (see repo roadmap):
#   - 2.5 uL adaptor and 1 uL Stop are below the pipette's reliable range
#     even on 200 uL tips - use an 8-channel 50 uL for those adds.
#   - liquid waste (A12) will overflow a 15 mL trough past ~1 column;
#     route to the waste chute or empty between cleanups for full plates.
#   - in-place cleanups + manual magnet moves are the simplification
#     carried over from the WGS protocol; production wants gripper-driven
#     plate shuttling on a magnetic module.
# ──────────────────────────────────────────────────────────────────────

requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "Methylation Sequencing - Library Preparation",
    "author": "Di Hu",
    "description": (
        "Conversion-based methylation sequencing on Opentrons Flex. Genome-wide "
        "methylation libraries for downstream methylation analysis. "
        "200 uL filter tips. DRAFT - not yet bench-validated."
    ),
}

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════
NUM_SAMPLES = 8     # must be a multiple of 8
OVERAGE     = 1.15  # master-mix overage factor
PCR_CYCLES  = 8     # by input: 200ng 4-5 / 50ng 5-6 / 10ng 8 / 1ng 11 / 0.1ng 14

RIGHT_PIPETTE = "flex_8channel_1000"  # all liquid handling (runs 200 uL filter tips)
LEFT_PIPETTE  = "flex_1channel_50"    # not used - see CAVEATS (small-volume adds)

SLOT_PLATE_A   = "B2"   # starts holding fragmented DNA
SLOT_PLATE_B   = "C3"
SLOT_SOURCE    = "B3"   # enzyme reservoir (A1-A10)
SLOT_RESERVOIR = "D2"   # bead/wash reservoir (A1-A3, waste A12)
SLOT_TIPS_1    = "A1"   # 200 uL filter
SLOT_TIPS_2    = "A2"   # 200 uL filter
SLOT_TIPS_3    = "A3"   # 200 uL filter (3 racks: 3 SPRIs => ~34 tip pickups/column)
SLOT_MAG_BLOCK = "C2"   # Opentrons Magnetic Block GEN1 (manual plate moves)
SLOT_TRASH     = "D1"

# Per-reaction add volumes (uL)
END_PREP_MM_VOL = 10.0
ADAPTER_VOL     = 2.5    # small - 50 uL pipette for real run
LIG_MM_VOL      = 31.0
PROTECTION_MM_VOL = 17.0
COFACTOR_VOL    = 5.0
STOP_VOL        = 1.0    # small - 50 uL pipette for real run
DENATURATION_VOL = 4.0
CONVERSION_MM_VOL = 20.0
PRIMER_VOL      = 5.0
PCR_MM_VOL      = 45.0

# Bead cleanups - (bead_vol, pre-bead reaction vol, elute vol, transfer vol)
BEADS_LIG,  RXN_LIG,  ELUTE_LIG,  XFER_LIG  = 93.0, 93.5, 29.0, 28.0   # 1.0X
BEADS_PROT, RXN_PROT, ELUTE_PROT, XFER_PROT = 50.0, 51.0, 17.0, 16.0   # 1.0X
BEADS_PCR,  RXN_PCR,  ELUTE_PCR,  XFER_PCR  = 72.0, 90.0, 21.0, 20.0   # 0.8X

ETOH_VOL = 180.0   # 80% EtOH wash (capped under the 200 uL tip)

NUM_COLUMNS = (NUM_SAMPLES + 7) // 8

# Thermal-cycler programs (external bench cycler):
# End Prep      (lid >=75C):  20C 15min -> 65C 15min -> 4C
# Ligation      (lid OFF):    20C 15min -> 4C
# Protection    (lid >=45C):  37C 1h -> 4C
# Stop          (lid >=45C):  37C 30min -> 4C
# Denaturation  (lid >=105C): 85C 10min -> snap-cool on ice
# Conversion    (lid >=45C):  37C 3h -> 4C
# PCR           (lid 105C):   98C 30s -> [98C 10s / 62C 30s / 65C 60s]xN -> 65C 5min -> 4C


def end_prep_mm(n):
    s = n * OVERAGE
    return {"EndPrepBuffer": round(7*s, 1), "EndPrepEnzyme": round(3*s, 1)}

def ligation_mm(n):
    s = n * OVERAGE
    return {"LigationEnhancer": round(1*s, 1), "LigationMasterMix": round(30*s, 1)}

def protection_mm(n):
    s = n * OVERAGE
    return {"ProtectionBuffer": round(10*s, 1), "Cofactor": round(1*s, 1),
            "ReducingAgent": round(1*s, 1), "EnzymeA": round(1*s, 1),
            "EnzymeB": round(4*s, 1)}

def conversion_mm(n):
    s = n * OVERAGE
    return {"Water": round(14*s, 1), "ConversionBuffer": round(4*s, 1),
            "CarrierProtein": round(1*s, 1), "ConversionEnzyme": round(1*s, 1)}

def pcr_mm(n):
    s = n * OVERAGE
    return {"PCRMasterMix": round(45*s, 1)}


def first_cols(plate, n):
    return plate.columns()[:n]


def add_reagent(pip, src_well, vol, dst_cols):
    """Add `vol` of one reagent from a single reservoir well to each column."""
    for col in dst_cols:
        pip.pick_up_tip()
        pip.aspirate(vol, src_well.bottom(z=2))
        pip.dispense(vol, col[0].bottom(z=2))
        pip.blow_out(col[0].top())
        pip.drop_tip()


def bead_cleanup(protocol, pip, src_plate, dst_plate, ncols,
                 beads, etoh, elution, waste,
                 bead_vol, rxn_vol, elute_vol, transfer_vol, label):
    """SPRI cleanup: bind -> magnet -> 2x 80% EtOH -> dry -> elute -> transfer.
    Plate moves on/off the magnet are operator handoffs (pauses)."""
    src = first_cols(src_plate, ncols)
    dst = first_cols(dst_plate, ncols)
    sup_vol = min(round((rxn_vol + bead_vol) * 1.05, 1), 190.0)   # cap under 200 uL tip
    mix_vol = min(round((rxn_vol + bead_vol) * 0.7, 1), 150)

    protocol.pause(f"{label} - vortex Sample Purification Beads (A1). Fresh 80% EtOH in A2.")

    # Bind
    for col in src:
        pip.pick_up_tip()
        pip.aspirate(bead_vol, beads.bottom(z=2))
        pip.dispense(bead_vol, col[0].bottom(z=2))
        pip.mix(10, mix_vol, col[0].bottom(z=2))
        pip.blow_out(col[0].top())
        pip.drop_tip()

    protocol.pause("Incubate RT 5 min. Move plate ONTO the Magnetic Block. Wait ~5 min until clear.")

    # Remove supernatant
    for col in src:
        pip.pick_up_tip()
        pip.aspirate(sup_vol, col[0].bottom(z=1))
        pip.dispense(sup_vol, waste.top())
        pip.drop_tip()

    # 2x 80% EtOH wash (plate stays on magnet)
    for wash in range(2):
        for col in src:
            pip.pick_up_tip()
            pip.aspirate(ETOH_VOL, etoh.bottom(z=2))
            pip.dispense(ETOH_VOL, col[0].top(z=-2))   # down the side, don't disturb beads
            pip.drop_tip()
        protocol.delay(seconds=30, msg=f"{label}: EtOH wash {wash+1}/2 (30 s)")
        for col in src:
            pip.pick_up_tip()
            pip.aspirate(ETOH_VOL, col[0].bottom(z=1))
            pip.dispense(ETOH_VOL, waste.top())
            pip.drop_tip()

    protocol.pause(
        "Remove residual EtOH (P20). Air-dry 1-2 min - do NOT over-dry "
        "(elute while beads are dark/glossy). Then move plate OFF the magnet."
    )

    # Elute
    for col in src:
        pip.pick_up_tip()
        pip.aspirate(elute_vol, elution.bottom(z=2))
        pip.dispense(elute_vol, col[0].bottom(z=2))
        pip.mix(10, min(round(elute_vol*0.8, 1), 20), col[0].bottom(z=2))
        pip.blow_out(col[0].top())
        pip.drop_tip()

    protocol.pause("Incubate RT 1 min. Move plate ONTO the magnet. Wait ~3 min until clear.")

    # Transfer eluate to destination plate (leaves beads behind)
    for s, d in zip(src, dst):
        pip.pick_up_tip()
        pip.aspirate(transfer_vol, s[0].bottom(z=1))
        pip.dispense(transfer_vol, d[0].bottom(z=2))
        pip.blow_out(d[0].top())
        pip.drop_tip()


def run(protocol: protocol_api.ProtocolContext):

    protocol.comment(f"Methylation sequencing | {NUM_SAMPLES} samples | {NUM_COLUMNS} column(s) | DRAFT")

    # Modules
    mag = protocol.load_module("magneticBlockV1", SLOT_MAG_BLOCK)

    # Labware
    plate_a = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", SLOT_PLATE_A, label="Plate A")
    plate_b = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", SLOT_PLATE_B, label="Plate B")
    source = protocol.load_labware(
        "nest_12_reservoir_15ml", SLOT_SOURCE,
        label="Reagents (A1 EndPrep A2 Adapter A3 LigMM A4 Protection A5 Cofactor "
              "A6 Stop A7 Denaturation A8 Conversion A9 Index A10 PCR)")
    reservoir = protocol.load_labware(
        "nest_12_reservoir_15ml", SLOT_RESERVOIR,
        label="Bead/wash (A1 beads A2 EtOH A3 elution A12 waste)")

    tips_1 = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_1)
    tips_2 = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_2)
    tips_3 = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_3)
    trash  = protocol.load_trash_bin(SLOT_TRASH)

    pip = protocol.load_instrument(RIGHT_PIPETTE, mount="right",
                                   tip_racks=[tips_1, tips_2, tips_3])

    # Reagent wells
    endprep   = source["A1"]
    adaptor   = source["A2"]
    ligmm     = source["A3"]
    protection_source = source["A4"]
    cofactor  = source["A5"]
    stop      = source["A6"]
    denaturation = source["A7"]
    conversion_source = source["A8"]
    index_primers = source["A9"]
    pcr_source = source["A10"]

    beads   = reservoir["A1"]
    etoh    = reservoir["A2"]
    elution = reservoir["A3"]
    waste   = reservoir["A12"]

    work, dest = plate_a, plate_b

    # Pre-flight
    protocol.pause(
        "INPUT: Plate A (B2) holds 50 uL fragmented DNA per well\n"
        "(sample + unmethylated and methylated spike-in controls,\n"
        "fragmented to the locally validated target size off-instrument).\n"
        "MOTION TEST: load water in enzyme A1-A10 and bead reservoir A1-A3 instead."
    )

    # ── SECTION 1 - End Prep ──────────────────────────────────────────
    ep = end_prep_mm(NUM_SAMPLES)
    protocol.pause(
        f"END PREP MM (premix off-deck -> A1):\n"
        f"  End Prep Buffer {ep['EndPrepBuffer']} uL + End Prep Enzyme {ep['EndPrepEnzyme']} uL"
    )
    add_reagent(pip, endprep, END_PREP_MM_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause(
        "Seal, vortex, spin. THERMAL CYCLER - End Prep (lid >=75C):\n"
        "  20C 15min -> 65C 15min -> 4C hold. Return plate."
    )

    # ── SECTION 2 - Adaptor Ligation ──────────────────────────────────
    lg = ligation_mm(NUM_SAMPLES)
    protocol.pause(
        f"LIGATION MM (premix enhancer + ligation master mix -> A3):\n"
        f"  Ligation Enhancer {lg['LigationEnhancer']} uL + Ligation MM {lg['LigationMasterMix']} uL\n"
        f"Adapter (neat) -> A2. Do NOT premix adapter into the ligation MM."
    )
    add_reagent(pip, adaptor, ADAPTER_VOL, first_cols(work, NUM_COLUMNS))   # 2.5 uL - small
    add_reagent(pip, ligmm,   LIG_MM_VOL,  first_cols(work, NUM_COLUMNS))
    protocol.pause(
        "Seal, vortex (MM is viscous - mix well), spin. THERMAL CYCLER - Ligation (lid OFF):\n"
        "  20C 15min -> 4C hold. Return plate."
    )

    # ── SECTION 3 - Post-Ligation Cleanup (1.0X) ──────────────────────
    bead_cleanup(protocol, pip, work, dest, NUM_COLUMNS,
                 beads, etoh, elution, waste,
                 BEADS_LIG, RXN_LIG, ELUTE_LIG, XFER_LIG, "POST-LIGATION CLEANUP (1.0X)")
    work, dest = dest, work   # clean DNA now in `work`

    # ── SECTION 4 - Base protection ───────────────────────────────────
    protection = protection_mm(NUM_SAMPLES)
    protocol.pause(
        f"PROTECTION MM (premix -> A4):\n"
        f"  Protection buffer {protection['ProtectionBuffer']} + cofactor {protection['Cofactor']}"
        f" + reducing agent {protection['ReducingAgent']} + enzyme A {protection['EnzymeA']}"
        f" + enzyme B {protection['EnzymeB']} uL"
    )
    add_reagent(pip, protection_source, PROTECTION_MM_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause("Prepare the protection cofactor per the locally validated SOP -> A5.")
    add_reagent(pip, cofactor, COFACTOR_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause(
        "Seal, vortex, spin. THERMAL CYCLER - Protection (lid >=45C):\n"
        "  37C 1h -> 4C hold. Return plate ON ICE."
    )
    add_reagent(pip, stop, STOP_VOL, first_cols(work, NUM_COLUMNS))   # 1 uL - small
    protocol.pause(
        "Seal, vortex, spin. THERMAL CYCLER - Stop (lid >=45C):\n"
        "  37C 30min -> 4C hold. Return plate."
    )

    # ── SECTION 5 - Post-Protection Cleanup (1.0X) ────────────────────
    fresh_slot = SLOT_PLATE_A if dest is plate_a else SLOT_PLATE_B
    protocol.pause(f"Place a FRESH 96-well PCR plate in slot {fresh_slot} (eluate destination).")
    bead_cleanup(protocol, pip, work, dest, NUM_COLUMNS,
                 beads, etoh, elution, waste,
                 BEADS_PROT, RXN_PROT, ELUTE_PROT, XFER_PROT, "POST-PROTECTION CLEANUP (1.0X)")
    work, dest = dest, work

    # ── SECTION 6 - Denaturation ──────────────────────────────────────
    protocol.pause("Denaturation reagent -> A7. Preheat cycler to 85C (lid >=105C).")
    add_reagent(pip, denaturation, DENATURATION_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause(
        "Seal, vortex, spin. THERMAL CYCLER - Denaturation:\n"
        "  85C 10min, then snap-cool on ice ~2 min. Return plate ON ICE."
    )

    # ── SECTION 7 - Conversion ────────────────────────────────────────
    conversion = conversion_mm(NUM_SAMPLES)
    protocol.pause(
        f"CONVERSION MM (premix -> A8):\n"
        f"  Nuclease-free water {conversion['Water']} + conversion buffer "
        f"{conversion['ConversionBuffer']} + carrier protein {conversion['CarrierProtein']}"
        f" + conversion enzyme {conversion['ConversionEnzyme']} uL"
    )
    add_reagent(pip, conversion_source, CONVERSION_MM_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause(
        "Seal, vortex, spin. THERMAL CYCLER - Conversion (lid >=45C):\n"
        "  37C 3h -> 4C hold. NO cleanup - straight to PCR. Return plate."
    )

    # ── SECTION 8 - PCR Amplification ─────────────────────────────────
    pc = pcr_mm(NUM_SAMPLES)
    protocol.pause(
        f"PCR master mix -> A10: {pc['PCRMasterMix']} uL.\n"
        f"Index primer pairs -> A9 (one unique pair per sample/well for a real run;\n"
        f"single well OK for a motion test)."
    )
    add_reagent(pip, index_primers, PRIMER_VOL, first_cols(work, NUM_COLUMNS))
    add_reagent(pip, pcr_source, PCR_MM_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause(
        f"Seal, vortex, spin. THERMAL CYCLER - PCR (lid 105C):\n"
        f"  98C 30s -> [98C 10s / 62C 30s / 65C 60s] x{PCR_CYCLES} -> 65C 5min -> 4C hold.\n"
        f"  Cycles by input: 200ng 4-5 / 50ng 5-6 / 10ng 8 / 1ng 11 / 0.1ng 14. Return plate."
    )

    # ── SECTION 9 - Post-PCR Cleanup (0.8X) -> final libraries ────────
    fresh_slot = SLOT_PLATE_A if dest is plate_a else SLOT_PLATE_B
    protocol.pause(f"Place a FRESH 96-well PCR plate in slot {fresh_slot} (final library plate).")
    bead_cleanup(protocol, pip, work, dest, NUM_COLUMNS,
                 beads, etoh, elution, waste,
                 BEADS_PCR, RXN_PCR, ELUTE_PCR, XFER_PCR, "POST-PCR CLEANUP (0.8X)")
    work, dest = dest, work

    final_slot = SLOT_PLATE_A if work is plate_a else SLOT_PLATE_B
    protocol.comment(f"DONE - methylation-sequencing libraries in slot {final_slot}.")
    protocol.pause(
        "POST-QC: fragment analysis (size + concentration).\n"
        "Pool, sequence on the selected platform, then run methylation calling and downstream analysis."
    )
