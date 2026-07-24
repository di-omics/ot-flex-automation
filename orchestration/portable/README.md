# Portable protocol representation

The protocol's reusable value is its intent: ordered transfers, mixes, delays,
and off-deck handoffs. Robot APIs represent those actions differently, so this
package captures the intent once and renders it through platform backends.

`ProtocolSpec` is plain serializable data defined in `spec.py`. Backends compile
the same spec into an Opentrons protocol or a neutral worklist. Precision is
validated independently on the selected execution platform.

```
                    ┌─────────────────────────┐
   examples/*.py ─▶ │   ProtocolSpec (spec.py) │ ─┐  the portable asset
                    │   volumes · src->dst · QC │  │  (also JSON: --target spec)
                    └─────────────────────────┘  │
                                                  ├─▶ opentrons_backend  -> Flex .py
                                                  ├─▶ worklist_backend   -> neutral CSV
                                                  └─▶ hamilton_backend   -> Hamilton worklist
```

## Try it

```bash
# Flex protocol (imports into the Opentrons App; simulates clean):
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
| Protocol intent (volumes, source-to-destination map, order, handoffs) | Yes | `ProtocolSpec` |
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
- `examples/whole_genome_seq_preparation.py` - the genome-amplification section
  represented with functional reagent names.

## Extending

- **More steps:** add to an example's `steps=[...]`. `Transfer` (per-column
  distribute) and `Handoff` (operator pause) cover the WGS-preparation motif; add step types
  (plate->plate, SPRI cleanup) as the encoded protocol grows.
- **Full whole-genome sequencing preparation:** transcribe Sections 2-3 (library prep, bead cleanup) into
  the spec, then the same spec can drive multiple backends.
- **Native Hamilton:** fill in `hamilton_backend.render()` with a Venus method
  template for labware mapping, tip types, and liquid classes.
