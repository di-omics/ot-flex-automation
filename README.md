# ot-flex-automation

Opentrons Flex automation for genomics library prep. Each protocol turns a single-cell or methylation kit into a reproducible, walkaway liquid-handling run, with the steps the Flex can't do (thermal cycling, fragmentation, magnet moves) surfaced as operator handoffs.

## Objective

Sequencing-ready libraries for **clinical disease-risk profiling**, **gene-therapy safety profiling**, and **epigenetic-aging-clock** analysis - built on the Flex for tight well-to-well consistency and minimal hands-on time.

> **Intended use note:** The kits below are labeled Research Use Only by their vendors. The "clinical" framing describes the research aim - flagged here so the regulatory context is explicit for anyone building on this. Adjust as needed.

## Protocols

| File | Kit | Output | Status |
|------|-----|--------|--------|
| `protocols/resolvedna_wgs_flex.py` | the vendor whole-genome sequencing (the kit user guide) | Single-cell whole-genome libraries | **Run end-to-end** on the Flex |
| `protocols/emseq_epigenetic_clock_flex.py` | NEBNext EM-seq v2 (NEB #E8015) | Genome-wide methylation libraries (aging-clock input) | **Draft** - motion-test ready, not yet bench-validated |

Both share the same conventions: a `CONFIG` block up top, off-deck steps driven by `protocol.pause()`, and an 8-channel 1000 µL pipette on the right mount.

---

## whole-genome sequencing

whole-genome amplification-based whole-genome amplification -> library prep -> bead cleanup, from single cells / nuclei. The Flex handles stages 2-3 of the 5-stage pipeline (isolation -> **WGA -> library prep** -> sequencing -> analysis); everything else is off-instrument.

**Section 1 - WGA:** Lysis Mix (L1/L2/L3) -> RT incubation -> Reaction Mix (R1/R2) -> cycler 30 °C 2.5 h -> 65 °C 3 min
**Section 2 - Library Prep:** DNAPREP (LP0B/LP0E) -> FERAT (LP1B/LP1E) -> ligation (adapters + LP2L) -> LIB-AMP (LP3A/LP3P)
**Section 3 - Bead Cleanup:** Resolve Beads 0.75× -> 2× 80 % EtOH -> elute -> transfer

Deck: sample plate **B2**, source reservoir **B3**, mag block **C2**, output plate **C3**, bead/wash reservoir **D2**, tips **A2/A3**, trash **D1**.
Source reservoir (B3): A1 Lysis · A2 Reaction · A3 DNA Prep · A4 FERAT · A5 LP2L · A6 Adapters · A7 Amp Mix.

## EM-seq Epigenetic Clock

Enzymatic methyl-seq (TET2 + APOBEC, no bisulfite) producing genome-wide 5mC/5hmC libraries - the input for epigenetic-aging-clock models. **Fragmentation is off-instrument** (Covaris/UltraShear) before the protocol starts.

**Flow:** End Prep -> adaptor ligation -> cleanup (1.0×) -> TET2 oxidation + Stop -> cleanup (1.0×) -> Formamide denaturation -> APOBEC deamination -> PCR -> cleanup (0.8×).
Seven thermal-cycler programs and all three SPRI cleanups are in the file. The three cleanups share one reusable `bead_cleanup()` function; two PCR plates (B2, C3) ping-pong through them, with the operator swapping a fresh plate into the spent-beads slot when prompted.

Enzyme reservoir (B3): A1 End Prep MM · A2 Adaptor · A3 Ligation MM · A4 TET2 MM · A5 Fe(II) · A6 Stop · A7 Formamide · A8 Deamination MM · A9 UDI primers · A10 Q5U MM.

Known simplifications for a real run are listed in the file header (small-volume adds want a 50 µL pipette; liquid waste routing; gripper-driven plate moves).

---

## Hardware & consumables

- Opentrons Flex + 8-channel 1000 µL pipette (right mount)
- Opentrons Magnetic Block GEN1
- 12-well reservoirs, 96-well PCR plates, Flex 1000 µL tip racks
- External: bench thermal cycler, Qubit (HS dsDNA), Agilent TapeStation; **Covaris/UltraShear** for EM-seq fragmentation

## Running a protocol

`NUM_SAMPLES` (multiple of 8) is at the top of each file.

- **Dry motion/volume check:** load water in the source + bead/wash reservoir wells and run as-is.
- **Real run:** prepare master mixes off-deck per the kit guide, load them into the mapped reservoir wells, and follow each `pause()` prompt for thermal-cycler and magnet handoffs.

Import the file into the Opentrons App and complete Labware Position Check before running.

## Repository structure

```
protocols/
  resolvedna_wgs_flex.py          WGS - run end-to-end on the Flex.
  emseq_epigenetic_clock_flex.py  EM-seq methylation - draft, motion-test ready.
README.md
```

## Roadmap

- [x] Repo + collaborator setup
- [x] whole-genome sequencing - full end-to-end protocol
- [x] EM-seq epigenetic-clock protocol (draft)
- [ ] Bench-validate the EM-seq protocol
- [ ] Add 8-channel 50 µL for accurate small-volume reagent adds (both protocols)
- [ ] Gripper-driven plate moves on/off the Mag Block (replace manual handoffs)
- [ ] Parameterize via Opentrons Runtime Parameters (sample count, volumes, PCR cycles)

## References

- whole-genome Single-Cell Core Kit - User Guide the kit user guide (the vendor)
- NEBNext Enzymatic Methyl-seq v2 - Instruction Manual, NEB #E8015 (New England Biolabs)
- Opentrons Flex + Python Protocol API - https://docs.opentrons.com
