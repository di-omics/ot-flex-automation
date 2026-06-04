# ot-flex-automation

Opentrons Flex automation for genomics library prep. Each protocol turns a single-cell, methylation, or chromatin kit into a reproducible, walkaway liquid-handling run, with the steps the Flex can't do (thermal cycling, fragmentation, magnet moves) surfaced as operator handoffs.

## TL;DR – the why

Three Flex protocols, three questions on the road from genome to intervention:

1. **WGS** (ResolveDNA) – **gene-editing safety.** Single-cell whole-genome sequencing to catch off-target edits and confirm an edit or gene therapy is clean.
2. **Epigenetic clock** (EM-seq) – **a longevity readout.** Genome-wide methylation as a quantitative measure of biological age – the gauge for whether a longevity intervention actually moves the needle.
3. **TIP-seq** – **disease risk to target.** Low-input epigenomic profiling that follows non-coding GWAS risk variants to the regulatory elements they act through, turning a statistical hit into a druggable target.

One bench engine, taking human-health questions from variant to validated intervention.

## Objective

Sequencing-ready libraries for **clinical disease-risk profiling**, **gene-therapy safety profiling**, **epigenetic-aging-clock** analysis, and **low-input epigenomic profiling that maps human disease risk from GWAS loci to target** – built on the Flex for tight well-to-well consistency and minimal hands-on time.

> **Intended use note:** The kits below are labeled Research Use Only by their vendors. The "clinical" framing describes the research aim – flagged here so the regulatory context is explicit for anyone building on this. Adjust as needed.

## Protocols

| File | Method / Kit | Output | Status |
|------|--------------|--------|--------|
| `protocols/resolvedna_wgs_flex.py` | BioSkryb ResolveDNA WGS (TAS-068.5) | Single-cell whole-genome libraries | **Run end-to-end** on the Flex |
| `protocols/emseq_epigenetic_clock_flex.py` | NEBNext EM-seq v2 (NEB #E8015) | Genome-wide methylation libraries (aging-clock input) | **Draft** – motion-test ready, not yet bench-validated |
| `protocols/tipseq_epigenome_flex.py` | TIP-seq (Tn5 + IVT, low-input CUT&Tag) | Histone-mark / TF epigenomic libraries | **Draft** – adaptation, not yet bench-validated |

All three share the same conventions: a `CONFIG` block up top, off-deck steps driven by `protocol.pause()`, and an 8-channel 1000 µL pipette on the right mount, running **200 µL filter tips** (`opentrons_flex_96_filtertiprack_200ul`) – the only Flex pipette that takes 200 µL tips, and every transfer here is ≤200 µL.

---

## ResolveDNA WGS

PTA-based whole-genome amplification → library prep → bead cleanup, from single cells / nuclei. The Flex handles stages 2–3 of the 5-stage pipeline (isolation → **WGA → library prep** → sequencing → analysis); everything else is off-instrument.

**Section 1 – WGA:** Lysis Mix (L1/L2/L3) → RT incubation → Reaction Mix (R1/R2) → cycler 30 °C 2.5 h → 65 °C 3 min
**Section 2 – Library Prep:** DNAPREP (LP0B/LP0E) → FERAT (LP1B/LP1E) → ligation (adapters + LP2L) → LIB-AMP (LP3A/LP3P)
**Section 3 – Bead Cleanup:** Resolve Beads 0.75× → 2× 80 % EtOH → elute → transfer

Deck: sample plate **B2**, source reservoir **B3**, mag block **C2**, output plate **C3**, bead/wash reservoir **D2**, tips **A2/A3**, trash **D1**.
Source reservoir (B3): A1 Lysis · A2 Reaction · A3 DNA Prep · A4 FERAT · A5 LP2L · A6 Adapters · A7 Amp Mix.

## EM-seq Epigenetic Clock

Enzymatic methyl-seq (TET2 + APOBEC, no bisulfite) producing genome-wide 5mC/5hmC libraries – the input for epigenetic-aging-clock models. **Fragmentation is off-instrument** (Covaris/UltraShear) before the protocol starts.

**Flow:** End Prep → adaptor ligation → cleanup (1.0×) → TET2 oxidation + Stop → cleanup (1.0×) → Formamide denaturation → APOBEC deamination → PCR → cleanup (0.8×). Seven thermal-cycler programs and all three SPRI cleanups are in the file. The three cleanups share one reusable `bead_cleanup()` function; two PCR plates (B2, C3) ping-pong through them, with the operator swapping a fresh plate into the spent-beads slot when prompted.

Enzyme reservoir (B3): A1 End Prep MM · A2 Adaptor · A3 Ligation MM · A4 TET2 MM · A5 Fe(II) · A6 Stop · A7 Formamide · A8 Deamination MM · A9 UDI primers · A10 Q5U MM.

## TIP-seq Epigenomic Profiling

Tn5-based CUT&Tag with T7 in-vitro transcription to amplify genome coverage from **low-input / single-cell chromatin** – mapping histone marks (e.g. H3K27me3) and transcription-factor occupancy (e.g. Pol2S5p) in non-coding regulatory regions, the path from **GWAS disease-risk loci to function and target**.

TIP-seq is predominantly manual single-cell work, so the automation boundary is **tagmentation → PCR**: the robot does every enzymatic / master-mix addition and all five SPRI cleanups; the upstream ConA binding, antibody steps, and pA-Tn5 washes stay manual (pre-flight). The signature TIP-seq **bead carry-through** (AMPure beads added at the first cleanup are retained through gap fill → IVT → RNA SPRI → 2nd-strand SPRI, discarded only at the fragmentation SPRI) is encoded via a `keep_beads` flag on the `spri()` helper. Pre- and post-SPRI Qubit checkpoints are built in as pauses.

**Tips:** like the other protocols it runs 200 µL filter tips, but TIP-seq is the most tip-hungry – 3 racks + one mid-run refill (`reset_tipracks`) cover a single column across all the carry-through SPRIs.

Enzyme reservoir (B3): A1 Tag · A2 ProtK · A3 Taq · A4 IVT · A5 Hexamer · A6 RT · A7 RNase H · A8 sss · A9 frag-Tn5 · A10 GuHCl · A11 PCR · A12 EDTA.

Known simplifications for real runs are listed in each file header (small-volume adds want a 50 µL pipette; liquid-waste routing; gripper-driven plate moves; per-arm tag buffers for multi-arm TIP-seq runs).

---

## Hardware & consumables

- Opentrons Flex + 8-channel 1000 µL pipette (right mount)
- Opentrons Magnetic Block GEN1
- 12-well reservoirs, 96-well PCR plates, 200 µL filter tip racks (all protocols; 2 racks for WGS, 3 for EM-seq and TIP-seq)
- External: bench thermal cycler, Qubit (HS dsDNA), Agilent TapeStation; Covaris/UltraShear for EM-seq fragmentation

## Running a protocol

`NUM_SAMPLES` (multiple of 8) is at the top of each file.

- **Dry motion/volume check:** load water in the source + bead/wash reservoir wells and run as-is.
- **Real run:** prepare master mixes off-deck per the kit guide, load them into the mapped reservoir wells, and follow each `pause()` prompt for thermal-cycler and magnet handoffs.

Import the file into the Opentrons App and complete Labware Position Check before running.

## Repository structure

```
protocols/
  resolvedna_wgs_flex.py          WGS – run end-to-end on the Flex.
  emseq_epigenetic_clock_flex.py  EM-seq methylation – draft, motion-test ready.
  tipseq_epigenome_flex.py        TIP-seq epigenomic – draft (200 uL filter tips).
README.md
```

## Roadmap

- [x] Repo + collaborator setup
- [x] ResolveDNA WGS – full end-to-end protocol
- [x] EM-seq epigenetic-clock protocol (draft)
- [x] TIP-seq epigenomic protocol (draft)
- [ ] Bench-validate the EM-seq and TIP-seq protocols
- [ ] Add 8-channel 50 µL for accurate small-volume reagent adds
- [ ] Gripper-driven plate moves on/off the Mag Block (replace manual handoffs)
- [ ] Parameterize via Opentrons Runtime Parameters (sample count, volumes, PCR cycles)

## References

- ResolveDNA Whole Genome Single-Cell Core Kit – User Guide TAS-068.5 (BioSkryb)
- NEBNext Enzymatic Methyl-seq v2 – Instruction Manual, NEB #E8015 (New England Biolabs)
- TIP-seq – Bartlett et al. (2021) J Cell Biol; Kaya-Okur et al. (2019) Nat Commun
- Opentrons Flex + Python Protocol API – https://docs.opentrons.com
