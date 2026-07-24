## Plate-reader CSV adapter

Complete `orchestration/instruments/plate_reader.py` so a fluorescence
microplate-reader export drives the SPRI-checkpoint QC.

### Scope

- Confirm the export layout and configure `CsvPlateReader`.
- Fit a standard curve from per-run DNA standards.
- Map read-plate wells to preparation-plate wells.
- Make `wait_for_export()` robust to partial files.
- Add tests against anonymized exports.

### Later

Add a live SDK or SiLA backend after the CSV path is validated.

### Done when

`python -m orchestration.run_qc_loop --dry-run --export <export.csv>` produces
the expected per-well concentrations and decisions.

Use a fluorometric dsDNA assay in a compatible black microplate.
