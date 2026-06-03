from opentrons import protocol_api

# ──────────────────────────────────────────────────────────────────────
# ResolveDNA WGS on Opentrons Flex — BAREBONES STARTER
#
# This is a minimal, runnable skeleton — NOT the full protocol yet.
# Goal: load the deck correctly and run a simple liquid-handling smoke
# test (water from reservoir -> plate columns) so we can verify labware
# definitions, the pipette, and motion/calibration on the Flex before
# building out the real ResolveDNA steps.
#
# Hardware assumed (matches what we have today):
#   Flex + 8-channel 1000 uL pipette on the RIGHT mount,
#   one 12-well reservoir, one 96-well PCR plate, one 1000 uL tip rack.
#
# To expand into the real run (ResolveDNA TAS-068.5), we'll add:
#   - an 8-channel 50 uL on the LEFT mount for the 3-6 uL reagent adds
#     (the 1000 uL is at the bottom of its range there and won't be accurate)
#   - a Magnetic Block + move_labware(..., use_gripper=True) for cleanup
#   - an output plate (e.g. slot C3)
# ──────────────────────────────────────────────────────────────────────

requirements = {"robotType": "Flex", "apiLevel": "2.21"}

metadata = {
    "protocolName": "ResolveDNA WGS Flex — Barebones Starter",
    "author": "Di Hu",
    "description": "Deck setup + liquid-handling smoke test. Build out from here.",
}

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════
NUM_SAMPLES = 8          # must be a multiple of 8
TEST_VOLUME = 100        # uL of water to move per column in the smoke test

# Deck slots
SLOT_PLATE     = "D1"
SLOT_RESERVOIR = "C1"
SLOT_TIPS      = "B2"
SLOT_TRASH     = "A3"

assert NUM_SAMPLES % 8 == 0, "NUM_SAMPLES must be a multiple of 8 (8-channel pipette)"
NUM_COLUMNS = NUM_SAMPLES // 8


def run(protocol: protocol_api.ProtocolContext):

    protocol.comment(
        f"Barebones smoke test | {NUM_SAMPLES} samples | {NUM_COLUMNS} column(s)"
    )

    # ── Labware ───────────────────────────────────────────────────────
    plate = protocol.load_labware(
        "nest_96_wellplate_100ul_pcr_full_skirt", SLOT_PLATE, label="Working Plate"
    )
    reservoir = protocol.load_labware(
        "nest_12_reservoir_15ml", SLOT_RESERVOIR, label="Reagent Reservoir"
    )
    tips = protocol.load_labware("opentrons_flex_96_tiprack_1000ul", SLOT_TIPS)
    trash = protocol.load_trash_bin(SLOT_TRASH)

    # ── Pipette ───────────────────────────────────────────────────────
    p8 = protocol.load_instrument(
        "flex_8channel_1000", mount="right", tip_racks=[tips]
    )

    # ── Smoke test ────────────────────────────────────────────────────
    # Fill reservoir well A1 with water before running:
    #   need >= TEST_VOLUME * 8 * NUM_COLUMNS uL (e.g. ~800 uL for 1 column).
    water = reservoir["A1"]
    columns = plate.columns()[:NUM_COLUMNS]

    for column in columns:
        p8.pick_up_tip()
        p8.aspirate(TEST_VOLUME, water.bottom(z=2))
        p8.dispense(TEST_VOLUME, column[0].bottom(z=2))   # 8-ch -> fills whole column
        p8.blow_out(column[0].top())
        p8.drop_tip()

    protocol.comment("Smoke test complete.")

    # ══════════════════════════════════════════════════════════════════
    # TODO — SECTION 1: WGA
    #   Lysis Mix (L1/L2/L3) add -> RT incubation -> Reaction Mix (R1/R2)
    #   -> off-deck DNA Amplification thermal cycler (30C 2.5h -> 65C 3min)
    # ══════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════
    # TODO — SECTION 2: LIBRARY PREP
    #   DNAPREP (LP0B/LP0E) -> FERAT (LP1B/LP1E) -> ligation (adapters/LP2L)
    #   -> LIB-AMP (LP3A/LP3P)   [each followed by off-deck thermal cycling]
    # ══════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════
    # TODO — SECTION 3: BEAD CLEANUP
    #   Resolve Beads 0.75x -> magnet -> 2x 80% EtOH wash -> dry
    #   -> elute 42 uL -> magnet -> transfer 40 uL to output plate
    # ══════════════════════════════════════════════════════════════════
