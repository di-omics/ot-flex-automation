# ot-flex-automation

Opentrons Flex automation for genomics library preparation. The repository
contains whole-genome sequencing, methylation sequencing, and TIP-seq workflows
plus a small orchestration layer for closed-loop quality control.

Each protocol keeps liquid-handling actions on the robot and presents thermal
cycling, fragmentation, magnet moves, and instrument-based QC as explicit
operator handoffs.

## Protocols

| File | Workflow | Output | Status |
|---|---|---|---|
| `protocols/whole_genome_seq_flex.py` | Whole-genome sequencing preparation | Whole-genome libraries | Run end to end on the Flex |
| `protocols/methylation_sequencing_flex.py` | Methylation sequencing | Genome-wide methylation libraries | Draft; motion-test ready |
| `protocols/tipseq_epigenome_flex.py` | TIP-seq epigenomic profiling | Histone-mark and transcription-factor libraries | Draft; motion-test ready |

All protocols expose a configuration block near the top of the file, use
`protocol.pause()` for off-deck steps, and keep reagent names functional rather
than tied to a particular commercial kit.

## Whole-genome sequencing

The WGS workflow prepares libraries from low-input DNA:

1. Genome amplification: lysis, amplification mix, and thermal incubation.
2. Library preparation: end preparation, repair, adapter ligation, and library
   amplification.
3. Cleanup: SPRI binding, ethanol washes, elution, and transfer.

Default deck:

- Sample plate: B2
- Reagent reservoir: B3
- Magnetic block: C2
- Output plate: C3
- Bead and wash reservoir: D2
- Tip racks: A2 and A3
- Trash: D1

The B3 reservoir uses A1 lysis, A2 amplification, A3 end preparation, A4 repair,
A5 ligation, A6 adapters, and A7 library amplification.

## Methylation sequencing

The methylation workflow performs end preparation, adapter ligation, bead
cleanup, base protection, denaturation, conversion, PCR enrichment, and final
cleanup. Fragmentation is an off-instrument preflight step. Two PCR plates
alternate through the cleanup stages.

The B3 reservoir uses A1 end preparation, A2 adapter, A3 ligation, A4 protection,
A5 cofactor, A6 stop reagent, A7 denaturation, A8 conversion, A9 index primers,
and A10 PCR enrichment.

## TIP-seq

The TIP-seq workflow preserves the published Tn5, in-vitro transcription, and
bead carry-through structure of the assay. Upstream cell binding, antibody
incubation, transposase binding, and washes remain manual. The robot handles
tagmentation onward, including master-mix additions and SPRI cleanups.

Pre- and post-cleanup DNA-quantification checkpoints are represented as pauses.
TIP-seq uses three tip racks plus one mid-run refill for a single column.

## Hardware and consumables

- Opentrons Flex with an 8-channel 1000 µL pipette
- Opentrons Magnetic Block GEN1
- 12-well reservoirs
- 96-well PCR plates
- 200 µL filter-tip racks
- External thermal cycler
- Fluorometric DNA quantification and fragment-analysis instruments
- Off-deck fragmentation equipment where required

## Running a protocol

Set `NUM_SAMPLES` to a multiple of eight near the top of the selected protocol.

- For a motion and volume check, load water in the mapped reagent and bead wells.
- For a real run, prepare functional master mixes from a locally validated SOP
  and follow each operator handoff.

Import the protocol into the Opentrons App and complete Labware Position Check
before running.

## Portable orchestration

`orchestration/portable/` represents transfer intent independently of a robot
API. It can render an Opentrons protocol or a neutral worklist for another liquid
handler.

`orchestration/` also includes:

- A concentration-based QC decision engine
- A CSV fluorescence-plate-reader adapter
- A Flex HTTP link
- A camera-based bead-pellet QC interface

These components are scaffolding for supervised, closed-loop runs. Validate any
sensor-gated action before using it on irreplaceable samples.

## References

- Locally validated whole-genome sequencing SOP
- Locally validated methylation-sequencing SOP
- Bartlett et al. (2021), TIP-seq
- Kaya-Okur et al. (2019), CUT&Tag
- [Opentrons Python Protocol API](https://docs.opentrons.com/)
