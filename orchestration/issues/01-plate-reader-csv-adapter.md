## Plate-reader CSV adapter (Qubit-replacement QC)

Finish `orchestration/instruments/plate_reader.py` so a fluorescence microplate reader's export drives the SPRI-checkpoint QC instead of a manual Qubit.

### Context
The protocols pause at Qubit checkpoints with the accept/branch rules already encoded in `decisions.py`. Goal: reader -> `{well: ng/uL}` -> `decisions.py`.

### Scope (v1 = CSV, vendor-agnostic)
- [ ] Confirm our reader's export format (long vs grid) and lock `CsvPlateReader` to it.
- [ ] Standard curve from per-run standards (`StandardCurve.from_points`); document where blanks/standards sit on the plate.
- [ ] Map read-plate wells to sample wells (QC aliquot layout may differ from the prep plate).
- [ ] `wait_for_export()` robust to partial writes (size stable across two polls).
- [ ] Unit tests against a couple of anonymized real exports in `examples/`.

### Out of scope (later)
Live SDK / SiLA control (`SerialPlateReader` stub) – only after the CSV path is proven on a real run.

### Done when
`python -m orchestration.run_qc_loop --dry-run --export <real_export.csv>` gives correct per-well ng/uL and decisions.

Assay: dsDNA fluorometric kit (PicoGreen / Quant-iT / AccuClear), black 96-well.
cc @spacexengineer
