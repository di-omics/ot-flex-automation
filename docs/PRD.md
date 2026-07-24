# PRD - Portable Genomics Liquid Handling

> Status: draft

## 1. Purpose

Build reliable, reusable liquid-handling workflows for whole-genome sequencing,
methylation sequencing, and epigenomic library preparation. The Opentrons Flex
is the development platform; the protocol model should remain portable to other
liquid handlers.

## 2. Product principles

- **Assay-level naming:** public interfaces use functional names such as WGS
  preparation, methylation sequencing, PCR enrichment, and DNA cleanup.
- **Portable intent:** source-to-destination maps, step order, and handoff types
  are separate from robot-specific API calls. Public examples use synthetic
  water volumes; biological volumes and QC gates stay in controlled local
  profiles.
- **Explicit handoffs:** thermal cycling, fragmentation, magnet moves, and
  instrument-based QC are represented as visible checkpoints.
- **State-aware operation:** a run verifies calibration, tips, labware, sources,
  destinations, and sample count before liquid movement begins.
- **Research use:** the workflows are development and research assets, not
  validated diagnostic methods.

## 3. Goals

1. Execute representative genomics-preparation runs without liquid-handling
   failures.
2. Detect missing calibration, tips, labware, or source definitions before a run.
3. Keep protocol intent renderable for both Opentrons and worklist-driven
   platforms.
4. Validate liquid-handling precision on the selected production platform.
5. Support volume scale-down only after yield, uniformity, and reproducibility
   gates pass.
6. Add supervised closed-loop decisions from plate-reader and camera QC.

## 4. Non-goals

- Automating upstream sample generation or single-cell isolation.
- Automating physical steps the configured robot cannot perform.
- Treating a motion-tested protocol as a validated wet-lab method.
- Allowing an unvalidated sensor result to trigger an irreversible sample move.

## 5. Architecture

The repository separates three layers:

1. `protocols/` contains runnable water-motion profiles plus private-profile
   seams for controlled biological parameters.
2. `orchestration/portable/` contains platform-neutral synthetic protocol
   intent and renderers.
3. `orchestration/` contains external QC adapters and run-control scaffolding.

The portable representation is the source of truth for transferable actions.
Platform backends translate those actions into robot-specific instructions.

## 6. Delivery phases

### Phase 1 - Instrument bring-up

- Calibrate the installed pipettes.
- Complete labware position checks.
- Run a one-column water transfer.
- Confirm tips, source wells, destination wells, and waste routing.

### Phase 2 - Autonomous execution

- Add a preflight state check.
- Run representative sequences without mid-run pipetting intervention.
- Surface progress and genuine off-deck handoffs clearly.

### Phase 3 - Workflow validation

- Reconcile deck layouts with controlled local WGS, methylation-sequencing, and
  TIP-seq profiles without committing method volumes, timings, or thresholds.
- Complete water runs before small wet-reagent runs.
- Use an appropriately sized pipette for low-volume additions.

### Phase 4 - Portability and precision

- Render the same transfer intent for a second liquid-handling platform.
- Measure well-to-well precision with a suitable assay.
- Confirm that porting requires backend mapping rather than protocol rewriting.

### Phase 5 - Closed-loop QC

- Parse fluorescence plate-reader exports.
- Add camera-based bead-pellet and dryness observations.
- Keep sensor decisions advisory until they agree with the validated manual
  method.

## 7. Success metrics

- At least two consecutive representative runs without liquid-handling failure.
- Preflight checks reject missing calibration, tips, labware, or source data with
  an actionable explanation.
- Portable examples render successfully for every supported backend.
- Wet-lab precision and library-quality thresholds are documented in the
  controlled operator profile before production use.
- Closed-loop QC completes at least one supervised decision cycle end to end.

## 8. Risks

- Low-volume transfers can fall outside a pipette's reliable operating range.
- A false bead-clearance result can cause irreversible sample loss.
- Over-dried cleanup beads can reduce recovery.
- Platform-specific assumptions can leak into portable protocol intent.
- Sparse-input workflows can lose coverage when volumes are reduced too far.

Each risk should have a water-test or manual-reference gate before it affects a
real sample.
