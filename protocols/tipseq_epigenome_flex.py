from opentrons import protocol_api

# ──────────────────────────────────────────────────────────────────────
# TIP-seq Epigenomic Profiling - Library Construction (Opentrons Flex)
#
# Adapts the TIP-seq protocol (Di Hu v4.9, embryo D7 blastocyst pilot;
# Bartlett 2021 / Kaya-Okur 2019) for the Flex. TIP-seq amplifies genome
# coverage from low-input / single-cell chromatin to map disease-risk
# variants in non-coding regulatory regions to function.
#
# STATUS: DRAFT - adaptation of a manual, tube-based single-cell method
# to a plate-based robot. Automates the enzymatic LIBRARY-CONSTRUCTION
# steps (Day 2 tagmentation -> Day 3 PCR) + the SPRI cleanups. NOT yet
# bench-validated. The whole-genome sequencing protocol in this repo is the only
# bench-run one; this and the EM-seq protocol are scaffolds.
#
# AUTOMATION BOUNDARY - what the Flex does vs. the operator:
#   MANUAL (pre-flight, off-robot): ConA bead activation, cell thaw +
#   binding, primary/secondary antibody, pA-Tn5 binding, the bead washes
#   (1 mL magnetic-capture washes in tubes), and the low-salt rinse for
#   CUTAC arms. These are delicate single-cell steps - done by hand.
#   ROBOT (this protocol): from tagmentation onward - every enzymatic /
#   master-mix addition and all SPRI cleanups. Thermal-cycler programs,
#   incubations, magnet moves, and Qubit checkpoints are pauses.
#
# ⚠️ BEAD CARRY-THROUGH (TIP-seq's defining gotcha): AMPure XP beads added
#   at Day 2 Step 4 are RETAINED in-well through gap fill -> IVT -> RNA
#   SPRI -> RT -> 2nd-strand SPRI -> fragmentation. Only the Day 3
#   fragmentation SPRI transfers eluate to a fresh plate and discards
#   beads. The post-PCR SPRI uses a SEPARATE fresh bead batch.
#   The spri() helper encodes this via keep_beads=True/False.
#
# TIPS: 200 uL FILTER tips only (opentrons_flex_96_filtertiprack_200ul),
#   run on the 8-channel 1000 uL pipette - the only Flex pipette
#   compatible with 200 uL tips. All transfers are <=200 uL.
#   3 racks + one mid-run refill (reset_tipracks) cover one column.
#
# CAVEATS for a real run (repo roadmap):
#   - several adds are 1-2.5 uL (EDTA, RNase H, ProtK mix, primers) -
#     below the pipette's reliable range; premix or use a 50 uL pipette.
#   - multi-arm runs (A standard vs B/C/IgG CUTAC) need DIFFERENT tag
#     buffers per well - one reservoir well can't serve both; split by
#     column or add manually. Single tag-buffer well here for the demo.
#   - SPRI volumes are estimates to tune during validation.
# ──────────────────────────────────────────────────────────────────────

requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "TIP-seq Epigenomic Profiling - Library Construction",
    "author": "Di Hu",
    "description": (
        "TIP-seq library construction on Opentrons Flex (tagmentation -> PCR). "
        "Low-input / single-cell epigenomic profiling for non-coding regulatory "
        "disease-risk mapping. 200 uL filter tips. DRAFT - not bench-validated."
    ),
}

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════
NUM_SAMPLES = 8     # must be a multiple of 8 (arms A / B / C / IgG map to wells)
PCR_CYCLES  = 9     # v4.9 default; Pol2S5p arm may need 10

RIGHT_PIPETTE = "flex_8channel_1000"   # 200 uL tips run on the 1000 uL pipette
LEFT_PIPETTE  = "flex_1channel_50"     # not used - see CAVEATS (small-volume adds)

SLOT_PLATE_A   = "B2"   # working plate (carry-through happens here)
SLOT_PLATE_B   = "C3"   # transfer / final-library plate
SLOT_SOURCE    = "B3"   # enzyme reservoir (A1-A12)
SLOT_RESERVOIR = "D2"   # bead/wash reservoir
SLOT_TIPS_1    = "A1"   # 200 uL filter
SLOT_TIPS_2    = "A2"   # 200 uL filter
SLOT_TIPS_3    = "A3"   # 200 uL filter
SLOT_MAG_BLOCK = "C2"   # Opentrons Magnetic Block GEN1 (manual plate moves)
SLOT_TRASH     = "D1"

# Per-reaction enzymatic add volumes (uL) - master mixes premixed off-deck
TAG_VOL      = 20.0   # Tag buffer (Buffer 8A standard OR 8B CUTAC - per arm)
EDTA_VOL     = 1.0    # 0.5M EDTA, stop tagmentation        (small)
PROTK_VOL    = 2.5    # ProtK 2 + 10% SDS 0.5               (small)
GAPFILL_VOL  = 2.0    # Taq 5x Master Mix                   (small)
IVT_VOL      = 10.0   # NTP set 2 + T7 buf 2 + T7 pol 2 + RNase-inh 0.3 + water 3.7
HEXAMER_VOL  = 2.5    # random hexamer 20 uM                (small)
RT_VOL       = 8.5    # 5x FS buf 4 + dNTP 2 + DTT 2 + MMLV RT 0.5
RNASEH_VOL   = 1.0    # RNase H (1:10)                      (small)
SSS_VOL      = 2.5    # sss_bulk-nXT 20 uM                  (small)
SS_TAQ_VOL   = 5.9    # Taq 5x Master Mix (second strand)
FRAG_VOL     = 4.0    # 10 mM TAPS 2 + 0.7 uM Tn5-ME-B 2
GUHCL_VOL    = 11.0   # 8M GuHCl -> 4M final
PCR_VOL      = 24.0   # NEBNext HiFi 2x 20 + i5 2 + i7 2

# SPRI cleanups - (bind reagent vol, supernatant vol, elute vol, transfer vol)
# Step 4 / Step 1 / Step 3 keep beads; Step 5 / Step 6 transfer + discard beads.
SPRI_DNA   = (47.0, 75.0,  8.0, None)   # Day2 S4: FRESH beads 2x, keep
SPRI_RNA   = (40.0, 65.0,  9.0, None)   # Day3 S1: rebind 2x, keep
SPRI_SS    = (60.0, 95.0,  7.0, None)   # Day3 S3: rebind 2x, keep
SPRI_FRAG  = (44.0, 70.0, 16.0, 16.0)   # Day3 S5: rebind 2x, TRANSFER (discard beads)
SPRI_PCR   = (32.0, 78.0, 30.0, 30.0)   # Day3 S6: FRESH beads 0.8x left-side, TRANSFER

ETOH_VOL = 180.0   # 80% EtOH wash (capped under the 200 uL tip)

NUM_COLUMNS = (NUM_SAMPLES + 7) // 8

# Thermal-cycler / incubation programs (external bench cycler / heat block):
# Tagmentation (37C):  Arm A 10 min · Arms B/C/IgG 20 min
# ProtK        (50C):  30 min
# Gap fill     (72C):  3 min
# IVT          (37C):  21 h
# 1st strand        :  70C 3min (hexamer) -> 22C 10min / 42C 60min / 70C 10min -> RNaseH 37C 20min
# 2nd strand        :  65C 2min -> 72C 8min
# Fragmentation(55C):  8 min
# PCR (lid 105C)    :  72C 5min -> 98C 30s -> [98C 10s / 63C 30s] xN -> 72C 1min -> 4C


def first_cols(plate, n):
    return plate.columns()[:n]


def add_reagent(pip, src_well, vol, dst_cols):
    """Add one reagent from a single reservoir well to each column (fresh tips)."""
    for col in dst_cols:
        pip.pick_up_tip()
        pip.aspirate(vol, src_well.bottom(z=2))
        pip.dispense(vol, col[0].bottom(z=2))
        pip.blow_out(col[0].top())
        pip.drop_tip()


def spri(protocol, pip, work, dst, ncols, bind_well, params,
         etoh, elution, waste, keep_beads, label):
    """SPRI cleanup.
    keep_beads=True  -> rebind/bind, wash, elute IN PLACE; beads + eluate
                        stay in the well for the next step (carry-through).
    keep_beads=False -> wash, elute, then transfer eluate to dst and leave
                        beads behind (discard).
    bind_well is FRESH beads (initial / post-PCR) or SPRI binding buffer
    (carry-through rebind) - caller decides."""
    bind_vol, sup_vol, elute_vol, transfer_vol = params
    src = first_cols(work, ncols)
    mix_vol = min(round(sup_vol * 0.6, 1), 150)

    protocol.pause(f"{label} - vortex bead / binding-buffer source. Fresh 80% EtOH in A2.")

    # Bind (add fresh beads, or add binding buffer to existing beads)
    for col in src:
        pip.pick_up_tip()
        pip.aspirate(bind_vol, bind_well.bottom(z=2))
        pip.dispense(bind_vol, col[0].bottom(z=2))
        pip.mix(10, mix_vol, col[0].bottom(z=2))
        pip.blow_out(col[0].top())
        pip.drop_tip()

    protocol.pause("Incubate RT 5 min. Move plate ONTO the Magnetic Block. Wait until clear.")

    # Remove supernatant -> waste
    for col in src:
        pip.pick_up_tip()
        pip.aspirate(sup_vol, col[0].bottom(z=1))
        pip.dispense(sup_vol, waste.top())
        pip.drop_tip()

    # 2x 80% EtOH wash (on magnet)
    for w in range(2):
        for col in src:
            pip.pick_up_tip()
            pip.aspirate(ETOH_VOL, etoh.bottom(z=2))
            pip.dispense(ETOH_VOL, col[0].top(z=-2))   # down the side, don't disturb beads
            pip.drop_tip()
        protocol.delay(seconds=30, msg=f"{label}: EtOH wash {w+1}/2 (30 s)")
        for col in src:
            pip.pick_up_tip()
            pip.aspirate(ETOH_VOL, col[0].bottom(z=1))
            pip.dispense(ETOH_VOL, waste.top())
            pip.drop_tip()

    protocol.pause(
        "Pull residual EtOH with a fine tip. Air-dry 3 min MAX - matte, not "
        "cracked (over-drying = library loss). Then move plate OFF the magnet."
    )

    # Elute
    for col in src:
        pip.pick_up_tip()
        pip.aspirate(elute_vol, elution.bottom(z=2))
        pip.dispense(elute_vol, col[0].bottom(z=2))
        pip.mix(10, min(round(elute_vol * 0.8, 1), 20), col[0].bottom(z=2))
        pip.blow_out(col[0].top())
        pip.drop_tip()

    if keep_beads:
        protocol.comment(f"{label}: beads RETAINED in well (carry-through).")
        return work   # sample stays in same plate; beads carried forward

    # Transfer eluate to fresh plate, leaving beads behind
    protocol.pause("Incubate RT 5 min. Move plate ONTO the magnet. Wait until clear.")
    dcols = first_cols(dst, ncols)
    for s, d in zip(src, dcols):
        pip.pick_up_tip()
        pip.aspirate(transfer_vol, s[0].bottom(z=1))
        pip.dispense(transfer_vol, d[0].bottom(z=2))
        pip.blow_out(d[0].top())
        pip.drop_tip()
    protocol.comment(f"{label}: eluate transferred; old beads discarded.")
    return dst    # sample now in dst plate


def run(protocol: protocol_api.ProtocolContext):

    protocol.comment(f"TIP-seq library construction | {NUM_SAMPLES} samples | "
                     f"{NUM_COLUMNS} column(s) | DRAFT")

    # Modules
    mag = protocol.load_module("magneticBlockV1", SLOT_MAG_BLOCK)

    # Labware
    plate_a = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", SLOT_PLATE_A, label="Plate A (working)")
    plate_b = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", SLOT_PLATE_B, label="Plate B (transfer)")
    source = protocol.load_labware(
        "nest_12_reservoir_15ml", SLOT_SOURCE,
        label="Enzymes (A1 Tag A2 ProtK A3 Taq A4 IVT A5 Hexamer A6 RT A7 RNaseH "
              "A8 sss A9 frag-Tn5 A10 GuHCl A11 PCR A12 EDTA)")
    reservoir = protocol.load_labware(
        "nest_12_reservoir_15ml", SLOT_RESERVOIR,
        label="Bead/wash (A1 AMPure A2 EtOH A3 binding A4 elution A5 AMPure-PCR A12 waste)")

    tips_1 = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_1)
    tips_2 = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_2)
    tips_3 = protocol.load_labware("opentrons_flex_96_filtertiprack_200ul", SLOT_TIPS_3)
    trash  = protocol.load_trash_bin(SLOT_TRASH)

    pip = protocol.load_instrument(RIGHT_PIPETTE, mount="right",
                                   tip_racks=[tips_1, tips_2, tips_3])

    # Enzyme wells
    tag      = source["A1"]
    protk    = source["A2"]
    taq      = source["A3"]
    ivt      = source["A4"]
    hexamer  = source["A5"]
    rt_mix   = source["A6"]
    rnaseh   = source["A7"]
    sss      = source["A8"]
    frag_tn5 = source["A9"]
    guhcl    = source["A10"]
    pcr_mix  = source["A11"]
    edta     = source["A12"]

    ampure      = reservoir["A1"]    # carry-through beads (Day2 S4 onward)
    etoh        = reservoir["A2"]
    binding     = reservoir["A3"]    # SPRI binding buffer (PEG/NaCl) for rebinds
    elution     = reservoir["A4"]    # nuclease-free water / Tris
    ampure_pcr  = reservoir["A5"]    # SEPARATE fresh beads for post-PCR left-side
    waste       = reservoir["A12"]

    work, dest = plate_a, plate_b

    # ── Pre-flight ────────────────────────────────────────────────────
    protocol.pause(
        "INPUT: Plate A (B2) holds ConA-bound, antibody-labeled, pA-Tn5-bound\n"
        "cells in their final wash state - one arm per well/column\n"
        "(A H3K27me3-standard / B Pol2S5p-CUTAC / C combined / IgG).\n"
        "All upstream steps (ConA, cell binding, primary+secondary Ab, pA-Tn5\n"
        "binding, washes, CUTAC low-salt rinse) are done MANUALLY before this.\n"
        "MOTION TEST: load water in enzyme A1-A12 and bead reservoir A1-A5."
    )

    # ══════════════════════════════════════════════════════════════════
    # DAY 2 STEP 3 - Tagmentation
    # ══════════════════════════════════════════════════════════════════
    protocol.pause(
        "TAG BUFFER -> A1 (make fresh): Arm A = Buffer 8A (Dig-300 + 10 mM MgCl2); "
        "Arms B/C/IgG = Buffer 8B (CUTAC, 10 mM TAPS + 5 mM MgCl2).\n"
        "NOTE: one well = one buffer. For mixed arms, split by column or add 8A/8B by hand."
    )
    add_reagent(pip, tag, TAG_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause(
        "Seal. HEAT BLOCK 37C - Arm A 10 min, Arms B/C/IgG 20 min. Then ice."
    )
    add_reagent(pip, edta, EDTA_VOL, first_cols(work, NUM_COLUMNS))   # 1 uL - small

    # ══════════════════════════════════════════════════════════════════
    # DAY 2 STEP 4 - DNA purification  (beads ENTER and are RETAINED)
    # ══════════════════════════════════════════════════════════════════
    protocol.pause(
        "ProtK mix -> A2 (ProteinaseK 20 mg/mL + 10% SDS). AMPure XP (carry-through) -> A1.\n"
        "SPRI binding buffer -> A3, elution water -> A4."
    )
    add_reagent(pip, protk, PROTK_VOL, first_cols(work, NUM_COLUMNS))  # 2.5 uL - small
    protocol.pause("Seal. 50C 30 min (ProteinaseK release). Then ice. Resume for SPRI.")
    work = spri(protocol, pip, work, dest, NUM_COLUMNS, ampure, SPRI_DNA,
                etoh, elution, waste, keep_beads=True, label="DAY2 S4 DNA SPRI (2x, KEEP beads)")

    # ══════════════════════════════════════════════════════════════════
    # DAY 2 STEP 5 - Gap fill
    # ══════════════════════════════════════════════════════════════════
    add_reagent(pip, taq, GAPFILL_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause("Flick to mix. 72C 3 min -> cool to RT. (Beads stay in tube.)")

    # ══════════════════════════════════════════════════════════════════
    # DAY 2 STEP 6 - IVT (overnight)
    # ══════════════════════════════════════════════════════════════════
    protocol.pause(
        "IVT mix -> A4 (NTP set 2 + 10x T7 buf 2 + T7 pol 2 + RNase-inh 0.3 + water 3.7).\n"
        "Reminder: NTP set is 25 mM each (Phase 0D pre-mix), NOT 100 mM each."
    )
    add_reagent(pip, ivt, IVT_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause("Mix gently. 37C 21 h IVT (beads present). Resume Day 3. RNase-ZAP the bench.")

    # ══════════════════════════════════════════════════════════════════
    # DAY 3 STEP 1 - RNA purification  (rebind to carried beads, KEEP)
    # ══════════════════════════════════════════════════════════════════
    work = spri(protocol, pip, work, dest, NUM_COLUMNS, binding, SPRI_RNA,
                etoh, elution, waste, keep_beads=True, label="DAY3 S1 RNA SPRI (2x, KEEP beads)")

    # ══════════════════════════════════════════════════════════════════
    # DAY 3 STEP 2 - First-strand synthesis
    # ══════════════════════════════════════════════════════════════════
    add_reagent(pip, hexamer, HEXAMER_VOL, first_cols(work, NUM_COLUMNS))  # 2.5 uL - small
    protocol.pause("70C 3 min, then IMMEDIATELY ice. RT mix -> A6.")
    add_reagent(pip, rt_mix, RT_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause("22C 10min -> 42C 60min -> 70C 10min -> 4C. RNase H (1:10) -> A7.")
    add_reagent(pip, rnaseh, RNASEH_VOL, first_cols(work, NUM_COLUMNS))    # 1 uL - small
    protocol.pause("37C 20 min (RNase H).")

    # ══════════════════════════════════════════════════════════════════
    # DAY 3 STEP 3 - Second-strand synthesis  (rebind, KEEP)
    # ══════════════════════════════════════════════════════════════════
    protocol.pause("sss_bulk-nXT (TCGTCGGCAGCGTC, 20 uM) -> A8.  NOT sss_sci-nXTv2.")
    add_reagent(pip, sss, SSS_VOL, first_cols(work, NUM_COLUMNS))          # 2.5 uL - small
    protocol.pause("65C 2 min -> ice. Taq 5x Master Mix -> A3.")
    add_reagent(pip, taq, SS_TAQ_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause("72C 8 min -> ice. Resume for SPRI.")
    work = spri(protocol, pip, work, dest, NUM_COLUMNS, binding, SPRI_SS,
                etoh, elution, waste, keep_beads=True, label="DAY3 S3 2nd-strand SPRI (2x, KEEP beads)")

    # ── Tip refill (3 racks are ~spent; carry-through portion done) ────
    protocol.pause(
        "TIP REFILL: replace all three 200 uL filter-tip racks (A1/A2/A3) with "
        "fresh racks, then resume. (Spent tips from the carry-through steps.)"
    )
    pip.reset_tipracks()

    # ══════════════════════════════════════════════════════════════════
    # DAY 3 STEP 5 - cDNA fragmentation + FINAL carry-through SPRI (TRANSFER)
    # ══════════════════════════════════════════════════════════════════
    protocol.pause("Fragmentation mix -> A9 (10 mM TAPS 2 + 0.7 uM Tn5-ME-B 2). GuHCl -> A10.")
    add_reagent(pip, frag_tn5, FRAG_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause("55C 8 min -> ice.")
    add_reagent(pip, guhcl, GUHCL_VOL, first_cols(work, NUM_COLUMNS))   # 4M GuHCl final
    fresh_slot = SLOT_PLATE_A if dest is plate_a else SLOT_PLATE_B
    protocol.pause(f"Place a FRESH PCR plate in slot {fresh_slot} (fragmentation eluate). "
                   f"This SPRI DISCARDS the carry-through beads.")
    work = spri(protocol, pip, work, dest, NUM_COLUMNS, binding, SPRI_FRAG,
                etoh, elution, waste, keep_beads=False, label="DAY3 S5 frag SPRI (2x, TRANSFER)")
    dest = plate_a if work is plate_b else plate_b

    # ══════════════════════════════════════════════════════════════════
    # DAY 3 STEP 6 - PCR indexing  (+ pre/post-SPRI Qubit, left-side SPRI)
    # ══════════════════════════════════════════════════════════════════
    protocol.pause("PCR mix -> A11 (NEBNext HiFi 2x 20 + i5 2 + i7 2). Fresh AMPure XP -> A5.")
    add_reagent(pip, pcr_mix, PCR_VOL, first_cols(work, NUM_COLUMNS))
    protocol.pause(
        f"Seal. THERMAL CYCLER - PCR (lid 105C):\n"
        f"  72C 5min -> 98C 30s -> [98C 10s / 63C 30s] x{PCR_CYCLES} -> 72C 1min -> 4C.\n"
        f"  Pol2S5p arm may need 10 cycles. Return plate."
    )
    protocol.pause(
        "PRE-SPRI QUBIT (mandatory): pull 1 uL from each well, Qubit HS dsDNA.\n"
        "  >=1 ng/uL -> proceed.  0.3-1 -> +5 cyc top-up.  <0.3 -> +6 cyc.\n"
        "  Catches SPRI-loss vs PCR-failure. Resume when ready for 0.8x cleanup."
    )
    fresh_slot = SLOT_PLATE_A if dest is plate_a else SLOT_PLATE_B
    protocol.pause(f"Place a FRESH PCR plate in slot {fresh_slot} (final library plate).")
    work = spri(protocol, pip, work, dest, NUM_COLUMNS, ampure_pcr, SPRI_PCR,
                etoh, elution, waste, keep_beads=False,
                label="DAY3 S6 post-PCR SPRI (0.8x left-side, TRANSFER)")

    final_slot = SLOT_PLATE_A if work is plate_a else SLOT_PLATE_B
    protocol.comment(f"DONE - TIP-seq libraries in slot {final_slot}.")
    protocol.pause(
        "POST-SPRI QUBIT (mandatory): re-Qubit final eluate.\n"
        "  >=50% of pre-SPRI -> ship to TapeStation HS D1000 + sequencing.\n"
        "  <50% -> SPRI loss; re-amp eluate (15 total cycles) to rescue."
    )
