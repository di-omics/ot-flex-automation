from opentrons import protocol_api

# ──────────────────────────────────────────────────────────────────────
# Whole-Genome Sequencing Preparation (Opentrons Flex)
#
# Automates genome amplification, library preparation, and bead cleanup to
# produce sequencing-ready whole-genome libraries from low-input DNA.
#
# Status: run end-to-end on the Flex. All liquid handling uses the
# 8-channel 1000 uL pipette running 200 uL FILTER tips (every transfer
# is <=200 uL). Steps the Flex can't do (thermal cycling, vortex/spin,
# moving the plate on/off the magnet) are operator handoffs via
# protocol.pause() - read each pause message before resuming.
#
# Reagent source map - 12-well reservoir in B3:
#   A1 = Lysis mix        A2 = Amplification mix   A3 = End-preparation mix
#   A4 = Repair mix       A5 = Ligation reagent    A6 = Adapters
#   A7 = Library-amplification mix
# Bead / wash reservoir - 12-well in D2:
#   A1 = SPRI beads A2 = 80% EtOH       A3 = Elution Buffer  A12 = waste
#
# Dry motion/volume check: load water in the source + bead wells and run
# as-is. Real run: prepare the master mixes off-deck per a locally validated SOP.
# ──────────────────────────────────────────────────────────────────────

requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "Whole-Genome Sequencing Preparation",
    "author": "Di Hu",
    "description": (
        "Genome amplification, library preparation, and bead cleanup on Opentrons Flex. "
        "Thermal cycling and plate moves are manual handoffs (pauses). "
        "Research-use whole-genome sequencing preparation workflow. "
        "Uses 200 uL filter tips."
    ),
}

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════
NUM_SAMPLES = 8   # must be multiple of 8

# 8-channel 1000 uL pipette runs 200 uL FILTER tips for all steps.
# (The 1000 uL pipette is the only Flex 8-channel that takes 200 uL tips;
#  every transfer here is <=200 uL, so 200 uL filter tips are the fit.)
LEFT_PIPETTE  = "flex_1channel_50"    # not used - kept for config completeness
RIGHT_PIPETTE = "flex_8channel_1000"  # primary pipette (running 200 uL filter tips)

SLOT_SAMPLE_PLATE = "B2"
SLOT_OUTPUT_PLATE = "C3"
SLOT_SOURCE_PLATE = "B3"   # 12-well reservoir - reagents in A1-A7
SLOT_RESERVOIR    = "D2"   # 12-well reservoir - beads/EtOH/elution in A1-A3, waste A12
SLOT_TIPS_200A    = "A1"   # 200 uL filter tips
SLOT_TIPS_200B    = "A2"   # 200 uL filter tips (8-channel uses many tips)
SLOT_MAG_BLOCK    = "C2"   # Opentrons Magnetic Block GEN1
SLOT_TRASH        = "D1"

USE_OPENTRONS_MAG_MODULE = True  # True = Opentrons Mag Block; False = passive rack (manual)

ETOH_VOL = 180.0   # 80% EtOH wash (capped under the 200 uL tip)

# Thermal cycler programs (external bench cycler):
# DNA Amplification (lid 70C):  30C 2.5h -> 65C 3min -> 4C hold
# END PREP       (lid 105C):     37C 10min -> 4C hold
# REPAIR         (lid 105C):     4C 30s -> 30C 5min -> 65C 30min -> 4C hold
# LIBRARY AMPLIFICATION       (lid 105C):     98C 45s -> [98/60/72C]x8 -> 72C 60s -> 4C hold

NUM_COLUMNS = (NUM_SAMPLES + 7) // 8


def lysis_vols(n):
    s = n * 1.30
    return {"LYSIS_COMPONENT_A": round(1.68*s,1), "LYSIS_COMPONENT_B": round(0.12*s,1), "LYSIS_COMPONENT_C": round(1.20*s,1)}

def amplification_vols(n):
    s = n * 1.30
    return {"AMPLIFICATION_COMPONENT_A": round(5.4*s,1), "AMPLIFICATION_COMPONENT_B": round(0.6*s,1)}

def end_prep_vols(n):
    return {"END_PREP_BUFFER": round(4.0*n*1.33,1), "END_PREP_ENZYME": round(0.5*(1 if n<48 else 2),2)}

def repair_vols(n):
    s = n * 1.20
    return {"REPAIR_BUFFER": round(0.8*s,1), "REPAIR_ENZYME": round(1.2*s,1), "ELUTION": round(2.0*s,1)}

def library_amplification_vols(n):
    s = n * 1.10
    return {"AMPLIFICATION_MIX": round(18.0*s,1), "AMPLIFICATION_ENZYME": round(2.0*s,1)}


def run(protocol: protocol_api.ProtocolContext):

    protocol.comment(f"whole-genome sequencing | {NUM_SAMPLES} samples | {NUM_COLUMNS} columns")

    # Modules
    if USE_OPENTRONS_MAG_MODULE:
        mag_mod = protocol.load_module("magneticBlockV1", SLOT_MAG_BLOCK)

    # Labware
    sample_plate = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", SLOT_SAMPLE_PLATE, label="Sample Plate")
    output_plate = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", SLOT_OUTPUT_PLATE, label="Output Plate")
    source_plate = protocol.load_labware(
        "nest_12_reservoir_15ml", SLOT_SOURCE_PLATE,
        label="Source: A1 lysis, A2 amplification, A3 end prep, A4 repair, "
              "A5 ligation, A6 adapters, A7 library amplification")
    reservoir = protocol.load_labware(
        "nest_12_reservoir_15ml", SLOT_RESERVOIR, label="Reservoir")

    tips_200a = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_200A)
    tips_200b = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_200B)
    trash     = protocol.load_trash_bin(SLOT_TRASH)

    # Pipettes
    # 8-channel 1000 uL pipette, running 200 uL filter tips for all steps
    p8_1000 = protocol.load_instrument(RIGHT_PIPETTE, mount="right", tip_racks=[tips_200a, tips_200b])

    # Source wells (water for motion test; real reagents for liquid test)
    lysis_src    = source_plate["A1"]
    amplification_src = source_plate["A2"]
    end_prep_src = source_plate["A3"]
    repair_src    = source_plate["A4"]
    ligation_src = source_plate["A5"]
    adapter_src  = source_plate["A6"]
    library_amp_src = source_plate["A7"]

    beads = reservoir["A1"]
    etoh  = reservoir["A2"]
    elut  = reservoir["A3"]
    waste = reservoir["A12"]

    cols     = [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]
    out_cols = [output_plate.columns()[i]  for i in range(NUM_COLUMNS)]

    # ══════════════════════════════════════════════════════════════════
    # SECTION 1 - GENOME AMPLIFICATION
    # ══════════════════════════════════════════════════════════════════

    lv = lysis_vols(NUM_SAMPLES)
    protocol.pause(
        f"LYSIS MIX - prepare off-deck if using real reagents:\n"
        f"  Component A: {lv['LYSIS_COMPONENT_A']} uL  "
        f"Component B: {lv['LYSIS_COMPONENT_B']} uL  "
        f"Component C: {lv['LYSIS_COMPONENT_C']} uL\n"
        f"For motion test: water already in source plate A1."
    )
    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(5, lysis_src.bottom(z=5))
        p8_1000.dispense(5, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause("Seal plate. Incubate RT on ice 20 min. Resume when done.")

    rv = amplification_vols(NUM_SAMPLES)
    protocol.pause(
        f"AMPLIFICATION MIX - prepare off-deck if using real reagents:\n"
        f"  Component A: {rv['AMPLIFICATION_COMPONENT_A']} uL  "
        f"Component B: {rv['AMPLIFICATION_COMPONENT_B']} uL\n"
        f"For motion test: water in source plate A2."
    )
    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(6, amplification_src.bottom(z=5))
        p8_1000.dispense(6, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause(
        "Seal plate. Flick to mix. Spin briefly. Keep on ice.\n"
        "THERMAL CYCLER - DNA Amplification (lid 70C):\n"
        "  30C 2.5h -> 65C 3min -> 4C hold\n"
        "Return plate when complete."
    )
    protocol.pause(
        "QC CHECKPOINT:\n"
        "  Fluorometric DNA yield: expect >800 ng average.\n"
        "  Fragment analysis: expect ~1275 bp.\n"
        "  Prepare 2 ng/uL normalized plate. Return to B2."
    )

    # ══════════════════════════════════════════════════════════════════
    # SECTION 2 - LIBRARY PREP
    # ══════════════════════════════════════════════════════════════════

    dp = end_prep_vols(NUM_SAMPLES)
    protocol.pause(
        f"END PREPARATION MIX:\n"
        f"  Buffer: {dp['END_PREP_BUFFER']} uL  "
        f"Enzyme: {dp['END_PREP_ENZYME']} uL (invert 10x, no vortex)\n"
        f"Source plate A3."
    )
    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(5, end_prep_src.bottom(z=5))
        p8_1000.dispense(5, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause(
        "THERMAL CYCLER - END PREP (lid 105C):\n"
        "  37C 10min -> 4C hold\n"
        "Return plate on ice."
    )

    fv = repair_vols(NUM_SAMPLES)
    protocol.pause(
        f"REPAIR MIX:\n"
        f"  Buffer: {fv['REPAIR_BUFFER']} uL  "
        f"Enzyme: {fv['REPAIR_ENZYME']} uL  Elution: {fv['ELUTION']} uL\n"
        f"Source plate A4."
    )
    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(5, repair_src.bottom(z=5))
        p8_1000.dispense(5, col[0].bottom(z=5))
        p8_1000.mix(5, 5, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause(
        "THERMAL CYCLER - REPAIR (lid 105C):\n"
        "  4C 30s -> 30C 5min -> 65C 30min -> 4C hold\n"
        "Return plate on ice."
    )

    # Ligation
    protocol.pause("Vortex adapter plate briefly. Spin down.")
    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(5, adapter_src.bottom(z=5))
        p8_1000.dispense(5, col[0].bottom(z=5))
        p8_1000.drop_tip()

    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(5, ligation_src.bottom(z=5))
        p8_1000.dispense(5, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause("Seal. Vortex medium. Spin. Incubate RT 15 min. Proceed immediately.")

    av = library_amplification_vols(NUM_SAMPLES)
    protocol.pause(
        f"LIBRARY-AMPLIFICATION MIX:\n"
        f"  Mix: {av['AMPLIFICATION_MIX']} uL (invert, no vortex)  "
        f"Enzyme: {av['AMPLIFICATION_ENZYME']} uL\n"
        f"Source plate A7. Start LIBRARY AMPLIFICATION on thermal cycler, pause at 98C."
    )
    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(20, library_amp_src.bottom(z=5))
        p8_1000.dispense(20, col[0].bottom(z=5))
        p8_1000.mix(5, 20, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause(
        "THERMAL CYCLER - LIBRARY AMPLIFICATION (lid 105C):\n"
        "  98C 45s -> [98C 15s / 60C 30s / 72C 45s]x8 -> 72C 60s -> 4C hold\n"
        "Return plate on ice."
    )

    # ══════════════════════════════════════════════════════════════════
    # SECTION 3 - BEAD CLEANUP
    # ══════════════════════════════════════════════════════════════════

    protocol.pause("Vortex SPRI beads 10s. Fresh 80% EtOH in reservoir A2.")

    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(30, beads.bottom(z=5))
        p8_1000.dispense(30, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause(
        "Seal. Vortex high 10s. Incubate RT 5 min. Spin briefly.\n"
        "Place plate on Magnetic Block. Wait 3 min until clear."
    )

    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(70, col[0].bottom(z=5))
        p8_1000.dispense(70, waste.bottom(z=5))
        p8_1000.drop_tip()

    for wash in range(2):
        for col in cols:
            p8_1000.pick_up_tip()
            p8_1000.aspirate(ETOH_VOL, etoh.bottom(z=5))
            p8_1000.dispense(ETOH_VOL, col[0].bottom(z=5))
            p8_1000.drop_tip()
        protocol.delay(seconds=30, msg=f"EtOH wash {wash+1}/2")
        for col in cols:
            p8_1000.pick_up_tip()
            p8_1000.aspirate(ETOH_VOL, col[0].bottom(z=5))
            p8_1000.dispense(ETOH_VOL, waste.bottom(z=5))
            p8_1000.drop_tip()

    protocol.pause("Remove residual EtOH with P20. Air dry 3 min - do NOT over-dry.")
    protocol.pause("Remove plate from magnet.")

    for col in cols:
        p8_1000.pick_up_tip()
        p8_1000.aspirate(42, elut.bottom(z=5))
        p8_1000.dispense(42, col[0].bottom(z=5))
        p8_1000.mix(10, 35, col[0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.pause("Incubate RT 2 min. Return to magnet. Wait 2 min until clear.")

    for i, col in enumerate(cols):
        p8_1000.pick_up_tip()
        p8_1000.aspirate(40, col[0].bottom(z=5))
        p8_1000.dispense(40, out_cols[i][0].bottom(z=5))
        p8_1000.drop_tip()

    protocol.comment("DONE - libraries in output plate (C3).")
    protocol.pause(
        "POST-QC: DNA quantification + fragment analysis.\n"
        "Pool + final 0.75x bead cleanup before sequencing."
    )
