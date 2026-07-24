# ot-flex-automation

Opentrons Flex automation for genomics library preparation. The repository
contains whole-genome sequencing, methylation sequencing, and TIP-seq workflows
plus a small orchestration layer for closed-loop quality control.

Each protocol keeps liquid-handling actions on the robot and presents thermal
cycling, fragmentation, magnet moves, and instrument-based QC as explicit
operator handoffs.

The public WGS and methylation files are **water-only motion profiles**. Their
uniform synthetic volumes exist solely to exercise deck choreography and are
not wet-lab instructions. Biological execution requires an uncommitted
`OPERATOR_METHOD_PROFILE` containing locally validated volumes, programs,
cleanup rules, and QC criteria.

## Protocols

| File | Workflow | Output | Status |
|---|---|---|---|
| `protocols/whole_genome_seq_flex.py` | Whole-genome sequencing preparation | Whole-genome libraries | Deck choreography run end to end on the Flex; public profile is water only |
| `protocols/methylation_sequencing_flex.py` | Methylation sequencing | Genome-wide methylation libraries | Draft; motion-test ready |
| `protocols/tipseq_epigenome_flex.py` | TIP-seq epigenomic profiling | Histone-mark and transcription-factor libraries | Draft; motion-test ready |

All protocols use `protocol.pause()` for off-deck steps. WGS and methylation
expose a private-profile seam near the top of the file; their committed fallback
contains water-only stage labels and no biological parameter defaults.

## Whole-genome sequencing

The WGS choreography models these functional boundaries:

1. Input preparation and genome amplification.
2. Library construction and PCR enrichment.
3. Profile-defined cleanup, elution, and output transfer.

The public profile maps those boundaries to equal water transfers. It does not
publish reagent composition, stage-specific volume, thermal program, cleanup
ratio, or QC threshold.

Default deck:

- Sample plate: B2
- Reagent reservoir: B3
- Magnetic block: C2
- Output plate: C3
- Bead and wash reservoir: D2
- Tip racks: A2 and A3
- Trash: D1

The public B3 map uses A1 input preparation, A2 genome amplification, A3 library
construction, and A4 PCR enrichment. D2 uses A1 cleanup water, A2 wash water,
A3 elution water, and A12 waste.

## Methylation sequencing

The methylation choreography provides configurable library-construction,
methylation-processing, PCR-enrichment, cleanup, and QC boundaries. It does not
select a specific methylation chemistry. Two plates alternate through the
synthetic cleanup motion so the deck behavior remains testable.

The public B3 map uses water in A1-A3 for the three synthetic stages. A private
operator profile may define different stage wells and cleanup choices.

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

The committed WGS and methylation profiles are one-column motion tests
(`NUM_SAMPLES = 8`).

- Load water only in the mapped stage and cleanup wells.
- Import the protocol into the Opentrons App and complete Labware Position Check.
- For biological work, create a private copy and populate
  `OPERATOR_METHOD_PROFILE`; the public fallback must not be used with samples
  or reagents.

Each profile is validated for required keys and safe pipette-volume bounds before
movement. Off-deck timing, thermal programs, chemistry, and acceptance criteria
remain operator-supplied.

## Portable orchestration

`orchestration/portable/` represents transfer intent independently of a robot
API. Public examples render synthetic water choreography; a controlled local
spec is required for biological method values.

`orchestration/` also includes:

- A concentration-based QC decision engine
- A CSV fluorescence-plate-reader adapter
- A Flex HTTP link
- A camera-based bead-pellet QC interface

These components are scaffolding for supervised, closed-loop runs. WGS decision
logic requires a caller-supplied `WgsQcProfile`; the repository defines no
default yield, fragment, or normalization target.

## Alternate-deck WGS variants

The alternate-deck WGS files use the Flex 8-channel 1000 µL pipette on the left
mount and lower source aspiration in B3 and D2:

| File | Use |
|---|---|
| `protocols/whole_genome_seq_full_8ch_returntip_lower_source_demo.py` | Water-only demo that returns one reused tip column |
| `protocols/whole_genome_seq_full_flex_v2_lower_source.py` | Fresh-tip motion profile with a private-profile seam |

The return-tip file is hard-limited to water. The fresh-tip file still defaults
to water and requires an uncommitted validated profile for biological work.

## References

- Bartlett et al. (2021), TIP-seq
- Kaya-Okur et al. (2019), CUT&Tag
- [Opentrons Python Protocol API](https://docs.opentrons.com/)
