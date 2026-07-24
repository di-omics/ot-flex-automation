# bench - ready-to-run protocols for the Opentrons App

Rendered-from-`orchestration/portable` specs, committed here so they can be
**downloaded and imported into the Opentrons App directly** (no terminal,
no Python). Regenerate with, e.g.:

```bash
python -m orchestration.portable.render --target opentrons --example hello --out bench/hello_water_flex.py
```

## hello_water_flex.py - Phase-0 motion test

The smallest real test: pick up tips, move 20 µL water from reservoir A1 into
column 1 of the sample plate, drop tips. No reagents, no pauses. Simulates clean.

**Deck:**
| Slot | Labware |
|------|---------|
| A1, A2 | Opentrons Flex 200 µL filter tip racks |
| B2 | NEST 96-well PCR plate, full skirt (empty destination) |
| B3 | NEST 12-well reservoir - **water in A1** (use dyed water to see it) |
| D1 | trash |

**Pipette mount:** this artifact is rendered for the **left mount**. Re-render
for a different mount with `--mount right`.

**Run:** import in the App -> Labware Position Check -> Run. Success = it completes
and water visibly lands in the 8 wells of column 1.

> Labware is NEST (`nest_96_wellplate_100ul_pcr_full_skirt`,
> `nest_12_reservoir_15ml`). If your physical plate/reservoir differ, the import
> will mismatch - swap the load names in the spec and re-render.

## whole_genome_seq_full_flex.py - synthetic WGS choreography

This generated artifact uses water only and uniform synthetic transfers. It
exercises generic input-preparation, genome-amplification,
library-construction, PCR-enrichment, cleanup, and output-transfer boundaries.
It contains no biological method volume, thermal program, cleanup ratio, or QC
threshold. Render a controlled local spec instead of modifying this artifact
for biological work.
