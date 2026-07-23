# PRD - Autonomous Single-Cell WGS Liquid Handling

> Status: draft v0.2 · Owners: Hunter Casbeer (automation/orchestration), Di Hu (protocols/wet-lab) · Last updated: 2026-06-06

## 1. Why this exists

To know whether a gene edit is **safe**, you have to know it's clean in *every*
cell. The workflow: edit an embryo at the **1-cell stage**, grow it to a
**~300-cell blastocyst** (the point at which it would be implanted), and at that
stage verify - across every cell - that the edit didn't introduce off-target
damage. The readout is **single-cell whole-genome sequencing (scWGS)**:
copy-number variants, SNVs, structural variants, aneuploidy, per cell.

The problem is scale and cost:
- A batch is ~**300 cells × ~20 embryos ≈ 6,000 single-cell libraries**. No human
  pipettes that by hand.
- The whole-genome sequencing preparation chemistry is **expensive** per cell.
- The downstream analysis is **compute-heavy**.

So: automate the liquid handling, **scale reagent volumes down** to cut per-cell
cost, **continuously screen for cheaper/better conditions**, and keep the analysis
affordable.

## 2. Platform strategy ⟵ read this first

This is a **two-platform** plan, and conflating them is the main trap:

- **Opentrons Flex = the prototype / development rig.** Goal: a *decent* protocol
  that runs the **actions** autonomously and reliably. Precision is **not** the bar
  here - the available pipettes can't hit it and there's no direct way to measure
  volume yet. The Flex is where we get the choreography right cheaply.
- **Hamilton STAR + Agilent Bravo = the precision / production rigs.** Goal: port
  the working protocol over and hit **1-3% CV across the protocol**. That is where
  the accuracy target lives - not on the Flex.

**Design implication (important):** write the Flex protocol to be **portable** -
keep the liquid-handling *intent* (volumes, source->destination maps, step order,
QC gates) separated from Flex-specific deck/API details, so moving to STAR/Bravo
is a **re-targeting, not a rewrite**.

## 3. One-line vision

*Prototype a fully autonomous scWGS liquid-handling protocol on the Flex, then
port it to precision platforms (STAR/Bravo) to hit 1-3% CV at scale - turning
sparse single cells into sequencing-ready libraries that flag edit safety per cell.*

## 4. Goals / non-goals

**Goals**
- G1. **State-aware autonomous execution on the Flex:** the system knows its
  calibration, tips, columns, source, and destination, runs the protocol, and
  **continues on its own** without babysitting.
- G2. A **reality-grounded, portable** protocol that replaces the assumed baseline.
- G3. **Port to STAR/Bravo** and achieve **1-3% CV** across the protocol.
- G4. **Volume scale-down** to cut per-cell cost (validated on the precision rig).
- G5. **Closed-loop condition screening** (the `orchestration/` layer).
- G6. **Efficient scWGS analysis** (CNV / SNV / SV / aneuploidy) at lower compute.

**Non-goals (for now)**
- **Not** hitting 1-3% CV *on the Flex* - that's the precision platforms' job.
- Not automating off-deck steps the Flex can't do (thermal cycling, fragmentation,
  magnet moves) - operator handoffs via `pause()`.
- Not clinical deployment (kits are Research Use Only).
- Not the upstream biology (embryo culture, editing, single-cell isolation).

## 5. Current state - honest baseline

**Hardware (on-bench, 2026-06-06)**
- **8-channel 1000 µL** (right mount) - primary, but calibration reads **"No data."**
  Not yet calibrated; **Di is on it.**
- **1-channel 50 µL** - owned, but **slow** (single channel = 8× the moves).
- **96-channel head** - available (exciting, heavy); deferred for later.
- **8-channel 50 µL** - **not owned.** Di classifies it as **Phase 2**.
- **No direct volume measurement** available right now (possibly a balance/scale).
  -> We cannot validate CV on the Flex yet; near-term success = *the actions run*.
- Deck loaded; tip racks appear ~A2/A3 while the protocol expects **A1 + A2** - a
  likely Labware Position Check mismatch (matches the observed "expecting a channel
  at the other location"). Verify, don't assume.
- Not yet connected to the app/HTTP for programmatic control.

**Software (`ot-flex-automation` repo)**
- `protocols/whole_genome_seq_flex.py` - scWGS prep coded end-to-end, but an
  **assumed baseline** (written to the API, not calibrated to this machine). A
  starting hypothesis, not ground truth.
- `orchestration/` - working decision engine, CSV plate-reader QC, Flex HTTP runner
  (resume done), CV pellet detector (stub). Runs `--dry-run` with no hardware.

**Honest framing:** we don't yet have *one* confirmed, autonomous, failure-free
run of the actions on this machine. That - not precision - is the Flex value gate.

## 6. Core near-term objective (Hunter's bar, on the Flex)

> "If it can just move liquid from here to there \[autonomously, without me\], that's my entire job."

Make the pipetting **real and autonomous**. Definition of done:
1. **State-aware:** before/while running, the system knows calibration is good,
   tips are present and sufficient, labware/columns are at the expected slots, and
   source + destination are defined - and **proceeds on its own**.
2. **Autonomous & robust:** runs **≥2 iterations without failure** (no crashes,
   aborts, or mid-run operator rescue of the pipetting).
3. Precision (CV) is explicitly **deferred to the STAR/Bravo port** - not measured
   or chased on the Flex yet.

"Better than the existing protocol" = *runs autonomously and failure-free on the
real machine, state-aware* - not elegance, and not (yet) accuracy.

## 7. Workstreams & milestones

### Phase 0 - Instrument bring-up  ⟵ current blocker
- [~] Calibrate the 8-channel 1000 µL (clear "No data"). **Di is on this.**
- [ ] Labware Position Check; fix the tip-rack slot mismatch (align deck to
      `SLOT_TIPS_200A/B`, or update the constants to match the deck).
- [ ] Smallest **water transfer** (one column, A->B) running clean from the app -
      "hello world" for the instrument.

### Phase 1 - State-aware autonomous execution (the Flex value gate)
- [ ] **Pre-flight state check:** query the robot (calibration present? tips loaded
      & sufficient? labware at expected slots? source/dest defined?) and refuse to
      start - with a clear reason - if anything's missing.
- [ ] **Autonomous runner:** start the run and let it proceed through the protocol
      on its own; surface progress; only pause at the genuine off-deck handoffs.
- [ ] Pass the **≥2-iterations-without-failure** gate on a representative sequence.

### Phase 2 - Faithful whole-genome sequencing preparation, end-to-end on Flex
- [ ] Reconcile `whole_genome_seq_flex.py` with reality (deck, tips, volumes, pauses).
- [ ] Dry run end-to-end with **water**; then a small real-reagent run.
- [ ] Small reagent adds (~1-6 µL): use the slow **1-channel 50 µL** as fallback,
      or fold in the **8-channel 50 µL** (Di's Phase 2) when available.

### Phase 3 - Port to precision platforms (where accuracy lives)
- [ ] Port the protocol to **Hamilton STAR** and **Agilent Bravo**.
- [ ] Achieve **1-3% CV across the protocol** (these rigs + proper measurement).
- [ ] Confirm the portable-intent abstraction held (re-target, not rewrite).

### Phase 4 - Volume scale-down (cost) on the precision rig
- [ ] Titrate reagent volumes down; gate each cut on measured CV **and** library QC
      (yield/uniformity) so cost drops without losing data quality.

### Phase 5 - Closed-loop condition screening
- [ ] Wire `orchestration/` (decision engine + plate-reader/CV QC) to score
      conditions and pick the next experiment automatically. **Advisory-first** for
      any sensor that gates an irreversible aspirate.

### Phase 6 - Analysis efficiency (parallel track)
- [ ] Profile the scWGS pipeline; cut compute for sparse-input CNV/SNV/SV/aneuploidy
      calling. Quantify accuracy traded per dollar saved.

## 8. Success metrics
- **M0 (gate):** ≥1 autonomous, failure-free run of the actions on the Flex.
- **M1:** state-aware pre-flight catches a missing tip/labware/calibration and
  refuses to start, with a clear reason.
- **M2:** ≥2 consecutive autonomous iterations, zero failures, on the Flex.
- **M3 (precision):** **CV 1-3% across the protocol on STAR/Bravo** (the accuracy bar).
- **M4 (cost):** $/usable-library reduced X% vs. full-volume manual baseline.
- **M5:** closed loop completes ≥1 cheaper-condition discovery end-to-end.
- **M6:** analysis $/cell reduced Y% at equal call concordance.

## 9. Risks
- **Irreversible pipetting on precious samples.** Embryo-derived single cells are
  *not* re-runnable; a bad aspirate destroys unregenerable data. -> validate every
  sensor-gated control against the manual method first.
- **Measurement gap.** No direct volume measurement on the Flex now -> can't quantify
  accuracy until a balance is in place or the protocol reaches STAR/Bravo.
- **Portability risk.** Flex-specific code that doesn't cleanly port to STAR/Bravo
  would force a rewrite - mitigate by separating intent from platform up front.
- **Throughput on small volumes.** The 1-channel 50 µL is slow (8× moves); heavy
  reliance on it bottlenecks runs until the 8-channel 50 µL (Phase 2) arrives.
- **Sparse-input dropout.** scWGS from one cell is dropout-prone; volume scale-down
  can worsen it - gate cost cuts on library QC, not just "it ran."
- **Bead loss** (over-drying / false "cleared" from CV) - advisory-first guardrail.

## 10. Open questions
- **ANSWERED - accuracy:** 1-3% CV, and it's a **STAR/Bravo** target, not a Flex one.
- **ANSWERED - calibration:** Di owns it. **8-ch 50 µL:** not owned, Phase 2.
- **Measurement:** is a balance/scale actually available, and at what resolution?
  (Determines whether we can do *any* Flex-side accuracy check before the port.)
- **Port timing:** when do STAR/Bravo become available to develop against?
- **Scale-down floor:** how low before dropout/quality breaks?
- **Closed-loop objective:** cost at fixed quality, or a quality/cost ratio?

## 11. Proposed single-cell-WGS skill (separate artifact)
A `single-cell-wgs` skill: deep-dive reference for **executing scWGS from very
sparse samples** (WGS/WGA handling, dropout mitigation, low-input QC) and
**analyzing** it (CNV, SNV, SV, aneuploidy) with an eye to compute efficiency.
Scope and build after Phase 1, grounded in real runs.
