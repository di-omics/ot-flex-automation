# Portable protocol representation

The protocol's reusable value is its intent: ordered transfers, mixes, delays,
and off-deck handoffs. Robot APIs represent those actions differently, so this
package captures the intent once and renders it through platform backends.
Committed examples contain synthetic water values only; biological parameters
belong in a controlled local spec.

`ProtocolSpec` is plain serializable data defined in `spec.py`. Backends compile
the same spec into an Opentrons protocol or a neutral worklist. Precision is
validated independently on the selected execution platform.

```
                    ┌─────────────────────────┐
   examples/*.py ─▶ │   ProtocolSpec (spec.py) │ ─┐  the portable asset
                    │ synthetic motion · handoffs│  │  (also JSON: --target spec)
                    └─────────────────────────┘  │
                                                  ├─▶ opentrons_backend  -> Flex .py
                                                  ├─▶ worklist_backend   -> neutral CSV
                                                  └─▶ hamilton_backend   -> Hamilton worklist
```

## Try it

```bash
# Water-only Flex protocol (imports into the Opentrons App; simulates clean):
python -m orchestration.portable.render --target opentrons --out flex_wgs_preparation.py
opentrons_simulate flex_wgs_preparation.py

# Neutral transfer worklist:
python -m orchestration.portable.render --target worklist --out wgs_preparation_worklist.csv

# the portable spec itself, as JSON:
python -m orchestration.portable.render --target spec
```

## What ports, concretely

| Layer | Portable? | How |
|---|---|---|
| Synthetic protocol intent (source-to-destination map, order, handoffs) | Yes | `ProtocolSpec` |
| Biological method values and QC gates | Controlled local input | Not committed |
| Neutral execution list | Yes | `worklist` CSV |
| Platform method and liquid-class tuning | Backend-specific | Platform backend |
| Opentrons Python | Regenerated | `opentrons_backend` |
| QC decision engine | Yes | Operates on measurements rather than pipette APIs |

## Status

- `spec.py` - vendor-neutral model + JSON round-trip. **Done.**
- `backends/opentrons_backend.py` - renders a Flex protocol; **simulates clean.**
- `backends/worklist_backend.py` - renders a transfer worklist CSV. **Done.**
- `backends/hamilton_backend.py` - native Venus = **stub** (Phase 3); interim
  worklist path works today.
- `examples/whole_genome_seq_preparation.py` - uniform water transfers across
  generic WGS-preparation stage boundaries.

## Extending

- **More steps:** add to a controlled local spec. `Transfer` (per-column
  distribute) and `Handoff` (operator pause) cover the WGS-preparation motif;
  keep biological values outside the public examples.
- **Full whole-genome sequencing preparation:** use the committed synthetic
  full-flow example to test backend coverage, then supply validated method
  values through a controlled local profile.
- **Native Hamilton:** fill in `hamilton_backend.render()` with a Venus method
  template for labware mapping, tip types, and liquid classes.
