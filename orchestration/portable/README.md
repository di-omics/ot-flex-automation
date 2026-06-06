# portable — write the protocol once, run it on every platform

**The problem this solves:** the protocol's value is its *intent* — the ordered
list of "move X µL from source to destination, mix, hand off for thermal
cycling." But Opentrons Python, Hamilton Venus (STAR), and Agilent Bravo
(VWorks) share **none** of their code. Hand-write the protocol per platform and
you rewrite (and re-validate) it three times, and they drift apart.

**The fix:** capture the protocol once as a vendor-neutral **`ProtocolSpec`**
(plain, serializable data — `spec.py`). Compile it to each platform with a
**backend**. The Flex is our prototype rig; the Hamilton STAR / Bravo are where
the 1–3% CV target is hit. The spec is the asset that survives the move.

```
                    ┌─────────────────────────┐
   examples/*.py ─▶ │   ProtocolSpec (spec.py) │ ─┐  the portable asset
                    │   volumes · src→dst · QC │  │  (also JSON: --target spec)
                    └─────────────────────────┘  │
                                                  ├─▶ opentrons_backend  → Flex .py (runs today)
                                                  ├─▶ worklist_backend   → CSV (STAR/Bravo import, today)
                                                  └─▶ hamilton_backend   → native Venus method (Phase 3)
```

## Try it

```bash
# Flex protocol (imports into the Opentrons App; simulates clean):
python -m orchestration.portable.render --target opentrons --out flex_wga.py
opentrons_simulate flex_wga.py

# Hamilton STAR / Agilent Bravo worklist (vendor-neutral transfer list):
python -m orchestration.portable.render --target worklist --out wga_worklist.csv

# the portable spec itself, as JSON:
python -m orchestration.portable.render --target spec
```

## What ports, concretely

| Layer | Ports to STAR/Bravo? | How |
|---|---|---|
| Protocol intent (volumes, source→dest, order, handoffs) | ✅ 100% | the `ProtocolSpec` |
| Execution today | ✅ now | `worklist` CSV → Venus/VWorks worklist import |
| Native method + accuracy tuning (liquid classes for 1–3% CV) | ⏳ Phase 3 | `hamilton_backend` (the seam, stubbed) |
| Opentrons Python | ❌ | regenerated per platform from the spec — never hand-ported |
| `orchestration/` decision + QC engine | ✅ already | sits above the handler; talks ng/µL, not pipettes |

## Status

- `spec.py` — vendor-neutral model + JSON round-trip. **Done.**
- `backends/opentrons_backend.py` — renders a Flex protocol; **simulates clean.**
- `backends/worklist_backend.py` — renders a transfer worklist CSV. **Done.**
- `backends/hamilton_backend.py` — native Venus = **stub** (Phase 3); interim
  worklist path works today.
- `examples/resolvedna_wga.py` — the WGA section, transcribed from
  `protocols/resolvedna_wgs_flex.py`. Extend to the full protocol next.

## Extending

- **More steps:** add to an example's `steps=[...]`. `Transfer` (per-column
  distribute) and `Handoff` (operator pause) cover the WGA motif; add step types
  (plate→plate, SPRI cleanup) as the encoded protocol grows.
- **Full ResolveDNA:** transcribe Sections 2–3 (library prep, bead cleanup) into
  the spec, then the *same* spec drives Flex now and STAR/Bravo at port time.
- **Native Hamilton:** fill in `hamilton_backend.render()` with a Venus method
  template — labware→deck mapping, tip types, and liquid classes (the knobs that
  buy the 1–3% CV the Flex can't reach).
