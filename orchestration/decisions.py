"""
QC decision engine for the ot-flex-automation orchestration layer.

Pure, hardware-free functions that encode the SAME accept/branch rules already
written into the protocol pause() messages -- so a plate reader (or any
concentration source) can drive them automatically instead of a human reading
a Qubit value off a screen.

Nothing here touches a robot or an instrument; it just maps numbers to a
Decision. That keeps it unit-testable and lets the vision / instrument / Flex
layers stay swappable behind it.

Rules transcribed from the protocols (keep in sync with the pause text):

  TIP-seq, Day3 Step6 PRE-SPRI Qubit (tipseq_epigenome_flex.py):
    >= 1 ng/uL     -> proceed to 0.8x cleanup
    0.3 - 1 ng/uL  -> +5 cycles top-up, re-PCR, re-Qubit
    < 0.3 ng/uL    -> +6 cycles
  TIP-seq POST-SPRI Qubit:
    >= 50% of pre-SPRI -> ship to TapeStation HS D1000 + sequencing
    <  50%             -> SPRI loss; re-amp eluate to 15 total cycles

  WGS, post-WGA QC checkpoint (whole_genome_seq_flex.py):
    Qubit HS dsDNA expect > 800 ng avg; TapeStation D5000 ~1275 bp
    -> normalize to 2 ng/uL plate, proceed (flag if well below expected yield)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Action(str, Enum):
    PROCEED = "proceed"
    ADD_CYCLES = "add_cycles"
    REAMP = "reamp"
    NORMALIZE = "normalize"
    FLAG = "flag"


@dataclass
class Decision:
    action: Action
    reason: str
    params: dict = field(default_factory=dict)

    def __str__(self) -> str:
        extra = f" {self.params}" if self.params else ""
        return f"[{self.action.value}] {self.reason}{extra}"


# ---- TIP-seq -------------------------------------------------------------
PRE_SPRI_PROCEED = 1.0       # ng/uL
PRE_SPRI_LOW = 0.3           # ng/uL
POST_SPRI_RETENTION = 0.50   # fraction of pre-SPRI to keep


def tipseq_pre_spri(conc_ng_ul: float) -> Decision:
    """Pre-0.8x-cleanup Qubit gate for TIP-seq PCR product."""
    if conc_ng_ul >= PRE_SPRI_PROCEED:
        return Decision(Action.PROCEED,
                        f"{conc_ng_ul:.2f} ng/uL >= {PRE_SPRI_PROCEED} -> 0.8x cleanup")
    if conc_ng_ul >= PRE_SPRI_LOW:
        return Decision(Action.ADD_CYCLES,
                        f"{conc_ng_ul:.2f} ng/uL in [{PRE_SPRI_LOW}, {PRE_SPRI_PROCEED}) -> +5 cycles",
                        {"extra_cycles": 5})
    return Decision(Action.ADD_CYCLES,
                    f"{conc_ng_ul:.2f} ng/uL < {PRE_SPRI_LOW} -> +6 cycles",
                    {"extra_cycles": 6})


def tipseq_post_spri(pre_ng_ul: float, post_ng_ul: float) -> Decision:
    """Post-cleanup retention check. Re-amp to 15 total cycles on heavy loss."""
    if pre_ng_ul <= 0:
        return Decision(Action.FLAG, "pre-SPRI concentration <= 0; cannot compute retention")
    retention = post_ng_ul / pre_ng_ul
    if retention >= POST_SPRI_RETENTION:
        return Decision(Action.PROCEED,
                        f"retention {retention:.0%} >= {POST_SPRI_RETENTION:.0%} -> TapeStation + sequencing",
                        {"retention": round(retention, 3)})
    return Decision(Action.REAMP,
                    f"retention {retention:.0%} < {POST_SPRI_RETENTION:.0%} -> re-amp to 15 total cycles",
                    {"retention": round(retention, 3), "target_total_cycles": 15})


# ---- WGS -----------------------------------------------------------------
WGS_MIN_YIELD_NG = 800.0     # expected Qubit HS dsDNA average
WGS_NORMALIZE_NG_UL = 2.0    # target normalized plate


def wgs_wga_qc(total_ng: float, size_bp: float | None = None) -> Decision:
    """Post-WGA checkpoint: normalize to 2 ng/uL or flag a low/failed amp."""
    if total_ng < 0.5 * WGS_MIN_YIELD_NG:
        return Decision(Action.FLAG,
                        f"{total_ng:.0f} ng << {WGS_MIN_YIELD_NG:.0f} expected -> review WGA before prep",
                        {"total_ng": total_ng, "size_bp": size_bp})
    note = "" if total_ng >= WGS_MIN_YIELD_NG else " (below typical, proceeding with caution)"
    return Decision(Action.NORMALIZE,
                    f"{total_ng:.0f} ng -> normalize to {WGS_NORMALIZE_NG_UL} ng/uL{note}",
                    {"target_ng_ul": WGS_NORMALIZE_NG_UL, "total_ng": total_ng, "size_bp": size_bp})


# ---- batch helper --------------------------------------------------------
def decide_batch(decider, readings: dict) -> dict:
    """Apply a per-well decider to {well: value}. Returns {well: Decision}."""
    return {well: decider(val) for well, val in readings.items()}


if __name__ == "__main__":
    for c in (2.4, 0.6, 0.1):
        print(f"pre-SPRI {c:>4} ng/uL -> {tipseq_pre_spri(c)}")
    print("post-SPRI 2.0 -> 1.3 :", tipseq_post_spri(2.0, 1.3))
    print("post-SPRI 2.0 -> 0.6 :", tipseq_post_spri(2.0, 0.6))
    print("WGS 1100 ng          :", wgs_wga_qc(1100, 1275))
    print("WGS 250 ng           :", wgs_wga_qc(250))
