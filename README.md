# ot-flex-automation

Automating the **BioSkryb ResolveDNA Whole Genome Single-Cell Core Kit** (TAS-068.5) on the **Opentrons Flex** liquid handler.

## Objective

Whole genome sequencing for **clinical disease-risk profiling** and **gene-therapy safety profiling**. The goal is a reproducible, walkaway liquid-handling workflow that takes single cells / nuclei through whole genome amplification and into sequencing-ready Illumina libraries with minimal hands-on time and tight well-to-well consistency.

> **Intended use note:** The ResolveDNA Core Kit is labeled Research Use Only by BioSkryb. The "clinical" objective above describes the research aim — flagging here so the regulatory framing is explicit for anyone building on this. Adjust as needed.

## Workflow overview

The full ResolveDNA pipeline has five stages; the Flex handles the wet-lab liquid handling in the middle (stages 2–3). Everything else is off-instrument.

| Stage | Step | Where |
|-------|------|-------|
| 1 | Single-cell isolation (FACS / FANS into Cell Buffer) | off-instrument |
| 2 | **Whole Genome Amplification (PTA)** | **Flex** + bench thermal cycler |
| 3 | **Library Preparation** | **Flex** + bench thermal cycler |
| 4 | Next-Generation Sequencing (Illumina) | off-instrument |
| 5 | BaseJumper analysis (QC → WGS variant calling) | off-instrument |

Thermal cycling is handled on an **external bench cycler** — the protocol pauses and prompts for the plate handoff. On-deck Thermocycler / Temperature modules are a possible future integration.

## What the Flex automates

`resolvedna_wgs_flex.py` runs the full kit end-to-end across three sections, with operator handoffs (thermal cycling, vortex/spin, moving the plate on/off the magnet) prompted via `protocol.pause()`.

**Section 1 — WGA**
- Add Lysis Mix (L1 / L2 / L3, 3 µL/rxn) → RT incubation
- Add Reaction Mix (R1 / R2, 6 µL/rxn)
- Handoff: DNA Amplification cycler — 30 °C 2.5 h → 65 °C 3 min → 4 °C (lid 70 °C)

**Section 2 — Library Prep**
- DNAPREP (LP0B / LP0E) → cycler 37 °C 10 min
- FERAT (LP1B / LP1E) → cycler 4 °C 30 s → 30 °C 5 min → 65 °C 30 min
- Ligation (unique adapters + LP2L) → 20 °C 15 min
- LIB-AMP (LP3A / LP3P) → 98 °C 45 s → [98/60/72 °C] ×8 → 72 °C 60 s

**Section 3 — Bead Cleanup**
- Resolve Beads at 0.75× → magnet
- 2× 80 % ethanol washes → dry
- Elute (42 µL) → magnet → transfer 40 µL to output plate

## Hardware & consumables

- Opentrons Flex
- 8-channel 1000 µL pipette (right mount) — all liquid handling
- Opentrons Magnetic Block GEN1 — bead cleanup
- 12-well reservoirs ×2, 96-well PCR plates ×2 (sample + output), Flex 1000 µL tip racks ×2
- External: bench thermal cycler, Qubit (HS dsDNA), Agilent TapeStation

## Deck layout

```
        col 1              col 2              col 3
  A   [Tips 50µL]      [Tips 1000]      [Tips 1000]
  B   [    .    ]      [ Sample  ]      [ Source  ]
                       [  Plate  ]      [Reservoir]
  C   [    .    ]      [Mag Block]      [ Output  ]
                                        [  Plate  ]
  D   [  Trash  ]      [Bead/Wash]      [    .    ]
                       [Reservoir]
```

**Source reservoir (B3):** A1 Lysis · A2 Reaction · A3 DNA Prep · A4 FERAT · A5 LP2L · A6 Adapters · A7 Amp Mix
**Bead/wash reservoir (D2):** A1 Resolve Beads · A2 80 % EtOH · A3 Elution Buffer · A12 waste

## Repository structure

```
resolvedna_wgs_flex.py    Full end-to-end protocol: WGA → library prep → bead cleanup.
                          Run end-to-end on the Flex.
README.md                 This file.
```

### Running it

`NUM_SAMPLES` (multiple of 8) is at the top of the file.

- **Dry motion/volume check:** load water in the source + bead/wash reservoir wells and run as-is.
- **Real run:** prepare the master mixes off-deck per the kit guide, load them into the mapped reservoir wells, and follow each `pause()` prompt for the thermal-cycler and magnet handoffs.

Import `resolvedna_wgs_flex.py` into the Opentrons App and follow the labware placement + Labware Position Check prompts before running.

## Roadmap

- [x] Repo + collaborator setup
- [x] Full end-to-end protocol (WGA → library prep → bead cleanup)
- [ ] Add 8-channel 50 µL for more accurate small-volume reagent adds
- [ ] Gripper-driven plate moves on/off the Mag Block (replace manual handoffs)
- [ ] Parameterize via Opentrons Runtime Parameters (sample count, volumes)
- [ ] EM-seq / epigenetic-clock protocol (methylation, separate file)

## References

- ResolveDNA Whole Genome Single-Cell Core Kit — User Guide TAS-068.5 (BioSkryb)
- Opentrons Flex + Python Protocol API — https://docs.opentrons.com
