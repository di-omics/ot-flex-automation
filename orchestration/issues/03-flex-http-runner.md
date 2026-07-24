## Flex HTTP orchestration runner

Extend `orchestration/flex_link.py` + `run_qc_loop.py` so the decision engine actually advances the robot over the HTTP API (outside the deterministic protocol).

### Scope
- [ ] Run management: find/track the active `run_id`; verify `resume_run` (play) against a live paused run.
- [ ] Cycle top-up / segment re-queue: make each PCR/cleanup stage a launchable segment so "PCR +N cycles" can run on demand (the decision engine already emits `extra_cycles` / `target_total_cycles`).
- [ ] Wire the full TIP-seq pre-SPRI loop live: checkpoint pause -> read plate -> decide -> resume or re-PCR.
- [ ] Auth headers / timeouts; surface robot errors cleanly.

### Reference
HTTP API: docs.opentrons.com -> Flex -> Additional Documentation. Interactive option: Flex Jupyter / SSH.

### Done when
`run_qc_loop` runs against a real paused protocol and either resumes it or triggers a re-PCR from a live plate read; `--dry-run` still works with example data.
