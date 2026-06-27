from opentrons import protocol_api

requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "whole-genome sequencing Full - Studio45 Flex Lower Source",
    "author": "Di Hu / ChatGPT",
    "description": (
        "Full whole-genome sequencing dry-run protocol remapped to Studio45-style Flex deck: "
        "left 8-channel 1000 uL, tips A2+A1, trash A3, sample B2, reagents B3, "
        "magnet C2, output C3, bead/wash reservoir D2."
    ),
}

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
NUM_SAMPLES = 8  # must be a multiple of 8
NUM_COLUMNS = (NUM_SAMPLES + 7) // 8

# This file is meant to import cleanly into the Opentrons App tomorrow.
# Default = motion/water-safe. Flip to False only after choosing real cleanup
# labware that can tolerate the actual ethanol wash volume.
MOTION_TEST_SAFE_VOLUMES = True
ETOH_VOL = 80.0 if MOTION_TEST_SAFE_VOLUMES else 180.0

# Manual moves are safest for first full-protocol app load. Set True only if
# the Flex Gripper + C2 magnetic block move has been validated on this setup.
USE_GRIPPER_FOR_MAGNET_MOVES = False

PIPETTE_MOUNT = "left"
PIPETTE_NAME = "flex_8channel_1000"

# Lower reservoir aspiration height for B3 reagent reservoir and D2 bead/wash reservoir.
# Prior source pulls used bottom(z=5); for the current reservoir fill, z=2.0 sits lower
# while avoiding scraping the reservoir bottom. Plate aspirates/dispenses are unchanged.
RESERVOIR_SOURCE_Z = 2.0
PLATE_Z = 5.0

# Studio45 deck layout. This keeps the toy demo's A2 tips / A3 trash / B2
# sample / D2 reservoir convention, and adds the full protocol positions.
SLOT_TIPS_PRIMARY = "A2"    # same as toy demo
SLOT_TIPS_SECONDARY = "A1"  # full protocol needs >1 rack for fresh tips
SLOT_TRASH = "A3"           # Studio45 movable trash
SLOT_SAMPLE_PLATE = "B2"
SLOT_REAGENT_RES = "B3"
SLOT_MAG_BLOCK = "C2"
SLOT_OUTPUT_PLATE = "C3"
SLOT_BEAD_RES = "D2"

# Labware names
TIPRACK_1000 = "opentrons_flex_96_tiprack_1000ul"
PCR_PLATE = "nest_96_wellplate_100ul_pcr_full_skirt"
RESERVOIR_12 = "nest_12_reservoir_15ml"
MAG_BLOCK = "magneticBlockV1"

# External thermal cycler programs:
# DNA Amplification, lid 70C: 30C 2.5h -> 65C 3min -> 4C hold
# DNAPREP, lid 105C: 37C 10min -> 4C hold
# FERAT, lid 105C: 4C 30s -> 30C 5min -> 65C 30min -> 4C hold
# LIB-AMP, lid 105C: 98C 45s -> [98/60/72C]x8 -> 72C 60s -> 4C hold


def lysis_vols(n):
    s = n * 1.30
    return {"L1": round(1.68 * s, 1), "L2": round(0.12 * s, 1), "L3": round(1.20 * s, 1)}


def reaction_vols(n):
    s = n * 1.30
    return {"R1": round(5.4 * s, 1), "R2": round(0.6 * s, 1)}


def dna_prep_vols(n):
    return {"LP0B": round(4.0 * n * 1.33, 1), "LP0E": round(0.5 * (1 if n < 48 else 2), 2)}


def ferat_vols(n):
    s = n * 1.20
    return {"LP1B": round(0.8 * s, 1), "LP1E": round(1.2 * s, 1), "ELUTION": round(2.0 * s, 1)}


def amp_vols(n):
    s = n * 1.10
    return {"LP3A": round(18.0 * s, 1), "LP3P": round(2.0 * s, 1)}


def run(protocol: protocol_api.ProtocolContext):
    if NUM_SAMPLES % 8 != 0:
        raise ValueError("NUM_SAMPLES must be a multiple of 8 for this 8-channel protocol.")

    protocol.comment(f"whole-genome sequencing full Studio45 Flex | {NUM_SAMPLES} samples | {NUM_COLUMNS} columns")
    protocol.comment("Deck: A2 primary tips, A1 secondary tips, A3 trash, B2 sample, B3 reagents, C2 magnet, C3 output, D2 bead/wash reservoir.")
    protocol.comment(f"Reservoir source aspiration height: bottom(z={RESERVOIR_SOURCE_Z}) for B3/D2 source wells.")

    # Module
    mag_block = protocol.load_module(MAG_BLOCK, SLOT_MAG_BLOCK)

    # Labware
    tips_primary = protocol.load_labware(TIPRACK_1000, SLOT_TIPS_PRIMARY, label="Primary 1000 uL tips")
    tips_secondary = protocol.load_labware(TIPRACK_1000, SLOT_TIPS_SECONDARY, label="Secondary 1000 uL tips")
    trash = protocol.load_trash_bin(SLOT_TRASH)

    sample_plate = protocol.load_labware(PCR_PLATE, SLOT_SAMPLE_PLATE, label="Sample Plate")
    reagent_res = protocol.load_labware(
        RESERVOIR_12,
        SLOT_REAGENT_RES,
        label="Reagent Reservoir: A1 lysis, A2 reaction, A3 DNAprep, A4 FERAT, A5 LP2L, A6 adapters, A7 amp",
    )
    output_plate = protocol.load_labware(PCR_PLATE, SLOT_OUTPUT_PLATE, label="Output Plate")
    bead_res = protocol.load_labware(
        RESERVOIR_12,
        SLOT_BEAD_RES,
        label="Bead Reservoir: A1 beads, A2 EtOH/water, A3 elution, A12 waste",
    )

    # Pipette: Studio45 has the P1000 8-channel on the LEFT mount.
    p8 = protocol.load_instrument(PIPETTE_NAME, mount=PIPETTE_MOUNT, tip_racks=[tips_primary, tips_secondary])

    # Reagent reservoir B3
    lysis_src = reagent_res["A1"]
    rxn_src = reagent_res["A2"]
    dna_prep_src = reagent_res["A3"]
    ferat_src = reagent_res["A4"]
    lp2l_src = reagent_res["A5"]
    adapter_src = reagent_res["A6"]
    amp_src = reagent_res["A7"]

    # Bead/wash reservoir D2
    beads = bead_res["A1"]
    etoh = bead_res["A2"]
    elut = bead_res["A3"]
    waste = bead_res["A12"]

    cols = [sample_plate.columns()[i] for i in range(NUM_COLUMNS)]
    out_cols = [output_plate.columns()[i] for i in range(NUM_COLUMNS)]

    def add_to_sample(source, volume, comment=None, mix_after=None):
        if comment:
            protocol.comment(comment)
        for col in cols:
            p8.pick_up_tip()
            p8.aspirate(volume, source.bottom(z=RESERVOIR_SOURCE_Z))
            p8.dispense(volume, col[0].bottom(z=PLATE_Z))
            if mix_after is not None:
                reps, mix_vol = mix_after
                p8.mix(reps, mix_vol, col[0].bottom(z=PLATE_Z))
            p8.drop_tip()

    def sample_to_waste(volume, comment=None):
        if comment:
            protocol.comment(comment)
        for col in cols:
            p8.pick_up_tip()
            p8.aspirate(volume, col[0].bottom(z=PLATE_Z))
            p8.dispense(volume, waste.bottom(z=5))
            p8.drop_tip()

    def sample_to_output(volume, comment=None):
        if comment:
            protocol.comment(comment)
        for i, col in enumerate(cols):
            p8.pick_up_tip()
            p8.aspirate(volume, col[0].bottom(z=PLATE_Z))
            p8.dispense(volume, out_cols[i][0].bottom(z=PLATE_Z))
            p8.drop_tip()

    def move_sample_to_magnet():
        protocol.comment("Move Sample Plate from B2 to Magnetic Block at C2. Robot state will follow the move.")
        protocol.move_labware(sample_plate, mag_block, use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES)

    def move_sample_to_b2():
        protocol.comment("Move Sample Plate from Magnetic Block C2 back to B2. Robot state will follow the move.")
        protocol.move_labware(sample_plate, SLOT_SAMPLE_PLATE, use_gripper=USE_GRIPPER_FOR_MAGNET_MOVES)

    # ------------------------------------------------------------------
    # SECTION 1 - WGA
    # ------------------------------------------------------------------
    lv = lysis_vols(NUM_SAMPLES)
    protocol.pause(
        "PRE-FLIGHT / LYSIS MIX\n"
        "Load deck exactly as shown in comments. For water test, fill B3:A1-A7 and D2:A1-A3 with water.\n"
        f"If using real lysis mix in B3:A1: L1 {lv['L1']} uL, L2 {lv['L2']} uL, L3 {lv['L3']} uL.\n"
        "Resume to distribute lysis mix."
    )
    add_to_sample(lysis_src, 5.0, "Distribute Lysis Mix from B3:A1 to sample columns.")

    protocol.pause("Seal plate. Incubate RT/on ice 20 min. Spin if needed. Resume for Reaction Mix.")

    rv = reaction_vols(NUM_SAMPLES)
    protocol.pause(
        "REACTION MIX\n"
        f"If using real reaction mix in B3:A2: R1 {rv['R1']} uL, R2 {rv['R2']} uL.\n"
        "Resume to distribute reaction mix."
    )
    add_to_sample(rxn_src, 6.0, "Distribute Reaction Mix from B3:A2 to sample columns.")

    protocol.pause(
        "Seal/flick/spin. Keep on ice. Run external thermal cycler DNA Amplification:\n"
        "lid 70C: 30C 2.5h -> 65C 3min -> 4C hold. Return plate to B2 when complete."
    )
    protocol.pause(
        "WGA QC checkpoint: Qubit HS dsDNA and TapeStation D5000. "
        "Normalize to 2 ng/uL in the same sample plate position B2 before continuing."
    )

    # ------------------------------------------------------------------
    # SECTION 2 - LIBRARY PREP
    # ------------------------------------------------------------------
    dp = dna_prep_vols(NUM_SAMPLES)
    protocol.pause(
        "DNA PREP MIX in B3:A3. "
        f"For real mix: LP0B {dp['LP0B']} uL, LP0E {dp['LP0E']} uL. Resume to distribute."
    )
    add_to_sample(dna_prep_src, 5.0, "Distribute DNA Prep Mix from B3:A3.")

    protocol.pause("External thermal cycler DNAPREP, lid 105C: 37C 10min -> 4C hold. Return plate to B2 on ice.")

    fv = ferat_vols(NUM_SAMPLES)
    protocol.pause(
        "FERAT MIX in B3:A4. "
        f"For real mix: LP1B {fv['LP1B']} uL, LP1E {fv['LP1E']} uL, Elution Buffer {fv['ELUTION']} uL. Resume to distribute."
    )
    add_to_sample(ferat_src, 5.0, "Distribute FERAT Mix from B3:A4 and mix.", mix_after=(5, 5))

    protocol.pause("External thermal cycler FERAT, lid 105C: 4C 30s -> 30C 5min -> 65C 30min -> 4C hold. Return plate to B2 on ice.")

    protocol.pause("Vortex adapter plate briefly and spin down. Put adapter/water source at B3:A6. Resume to distribute adapters.")
    add_to_sample(adapter_src, 5.0, "Distribute adapters from B3:A6.")

    protocol.pause("LP2L / ligation reagent in B3:A5. Resume to distribute LP2L.")
    add_to_sample(lp2l_src, 5.0, "Distribute LP2L from B3:A5.")

    protocol.pause("Seal. Vortex medium. Spin. Incubate room temp 15 min. Proceed immediately to amp mix.")

    av = amp_vols(NUM_SAMPLES)
    protocol.pause(
        "AMP MIX in B3:A7. Start external LIB-AMP program and pause at 98C. "
        f"For real mix: LP3A {av['LP3A']} uL, LP3P {av['LP3P']} uL. Resume to distribute."
    )
    add_to_sample(amp_src, 20.0, "Distribute Amp Mix from B3:A7 and mix.", mix_after=(5, 20))

    protocol.pause(
        "External thermal cycler LIB-AMP, lid 105C:\n"
        "98C 45s -> [98C 15s / 60C 30s / 72C 45s] x8 -> 72C 60s -> 4C hold. Return plate to B2 on ice."
    )

    # ------------------------------------------------------------------
    # SECTION 3 - BEAD CLEANUP
    # ------------------------------------------------------------------
    protocol.pause(
        "BEAD CLEANUP\n"
        f"Vortex Resolve Beads/water in D2:A1. Fresh 80% EtOH/water in D2:A2. Elution in D2:A3.\n"
        f"This file is using ETOH_VOL={ETOH_VOL} uL. MOTION_TEST_SAFE_VOLUMES={MOTION_TEST_SAFE_VOLUMES}. Resume to add beads."
    )
    add_to_sample(beads, 30.0, "Add Resolve Beads from D2:A1.")

    protocol.pause("Seal. Vortex high 10s. Incubate RT 5 min. Spin briefly. Resume to move plate to magnetic block C2.")
    move_sample_to_magnet()
    protocol.delay(minutes=3, msg="On magnetic block: wait 3 min or until liquid is clear.")

    sample_to_waste(70.0, "Remove supernatant to D2:A12 waste while plate is on magnetic block.")

    add_to_sample(etoh, ETOH_VOL, "EtOH wash 1: add wash from D2:A2 while plate is on magnetic block.")
    protocol.delay(seconds=30, msg="EtOH wash 1 soak.")
    sample_to_waste(ETOH_VOL, "EtOH wash 1: remove to D2:A12 waste.")

    add_to_sample(etoh, ETOH_VOL, "EtOH wash 2: add wash from D2:A2 while plate is on magnetic block.")
    protocol.delay(seconds=30, msg="EtOH wash 2 soak.")
    sample_to_waste(ETOH_VOL, "EtOH wash 2: remove to D2:A12 waste.")

    protocol.pause("Remove residual EtOH manually with P20 if needed. Air dry 3 min; do NOT over-dry. Resume to move plate back to B2.")
    move_sample_to_b2()

    add_to_sample(elut, 42.0, "Add Elution Buffer from D2:A3 and mix off magnet at B2.", mix_after=(10, 35))

    protocol.pause("Incubate RT 2 min. Resume to move plate back to magnetic block C2 for elution separation.")
    move_sample_to_magnet()
    protocol.delay(minutes=2, msg="On magnetic block: wait 2 min or until eluate clears.")

    sample_to_output(40.0, "Transfer cleared eluate from sample plate to output plate C3.")

    protocol.comment("DONE - libraries/water-demo output in C3.")
    protocol.pause("POST-QC: Qubit HS dsDNA + TapeStation HS D1000. Pool + final 0.75x cleanup before sequencing if this was a real run.")
