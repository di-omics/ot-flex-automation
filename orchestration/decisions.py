"""
QC decision engine for the ot-flex-automation orchestration layer.

Pure, hardware-free functions that apply an explicitly supplied decision
profile, so a plate reader (or any concentration source) can drive a supervised
branch instead of a manual fluorometric DNA-quantification result.

Nothing here touches a robot or an instrument; it just maps numbers to a
Decision. That keeps it unit-testable and lets the vision / instrument / Flex
layers stay swappable behind it.

TIP-seq rules remain part of the user-owned assay implementation. WGS thresholds
are not committed: callers must supply a controlled ``WgsQcProfile`` at runtime.

  TIP-seq, Day3 Step6 PRE-SPRI DNA quantification (tipseq_epigenome_flex.py):
    >= 1 ng/uL     -> proceed to 0.8x cleanup
    0.3 - 1 ng/uL  -> +5 cycles top-up, re-PCR, and remeasure
    < 0.3 ng/uL    -> +6 cycles
  TIP-seq POST-SPRI DNA quantification:
    >= 50% of pre-SPRI -> fragment analysis + sequencing
    <  50%             -> SPRI loss; re-amp eluate to 15 total cycles
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
    """Pre-0.8x-cleanup DNA-quantification gate for TIP-seq PCR product."""
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
                        f"retention {retention:.0%} >= {POST_SPRI_RETENTION:.0%} -> fragment analysis + sequencing",
                        {"retention": round(retention, 3)})
    return Decision(Action.REAMP,
                    f"retention {retention:.0%} < {POST_SPRI_RETENTION:.0%} -> re-amp to 15 total cycles",
                    {"retention": round(retention, 3), "target_total_cycles": 15})


# ---- WGS -----------------------------------------------------------------
@dataclass(frozen=True)
class WgsQcProfile:
    """Operator-supplied WGS acceptance criteria.

    No defaults are provided because yield, normalization, and fragment-size
    criteria belong to the locally validated method rather than this public
    orchestration package.
    """

    minimum_yield_ng: float
    flag_below_yield_ng: float
    normalize_to_ng_ul: float
    minimum_fragment_bp: float | None
    maximum_fragment_bp: float | None

    def validate(self) -> None:
        numeric = (
            self.minimum_yield_ng,
            self.flag_below_yield_ng,
            self.normalize_to_ng_ul,
        )
        if any(value <= 0 for value in numeric):
            raise ValueError("WGS QC yield and normalization values must be positive.")
        if self.flag_below_yield_ng > self.minimum_yield_ng:
            raise ValueError("flag_below_yield_ng cannot exceed minimum_yield_ng.")
        if (self.minimum_fragment_bp is None) != (self.maximum_fragment_bp is None):
            raise ValueError("Supply both fragment bounds or neither.")
        if (
            self.minimum_fragment_bp is not None
            and self.minimum_fragment_bp >= self.maximum_fragment_bp
        ):
            raise ValueError("minimum_fragment_bp must be below maximum_fragment_bp.")


def wgs_amplification_qc(
    total_ng: float,
    profile: WgsQcProfile,
    size_bp: float | None = None,
) -> Decision:
    """Apply a controlled WGS QC profile; no public method defaults are used."""
    profile.validate()
    if total_ng < profile.flag_below_yield_ng:
        return Decision(
            Action.FLAG,
            "yield is below the operator profile's stop threshold",
            {"total_ng": total_ng, "size_bp": size_bp},
        )
    if total_ng < profile.minimum_yield_ng:
        return Decision(
            Action.FLAG,
            "yield is below the operator profile's proceed threshold",
            {"total_ng": total_ng, "size_bp": size_bp},
        )
    if (
        size_bp is not None
        and profile.minimum_fragment_bp is not None
        and not (profile.minimum_fragment_bp <= size_bp <= profile.maximum_fragment_bp)
    ):
        return Decision(
            Action.FLAG,
            "fragment measurement is outside the operator profile's accepted range",
            {"total_ng": total_ng, "size_bp": size_bp},
        )
    return Decision(
        Action.NORMALIZE,
        "WGS checkpoint passed the supplied operator profile",
        {
            "target_ng_ul": profile.normalize_to_ng_ul,
            "total_ng": total_ng,
            "size_bp": size_bp,
        },
    )


# ---- batch helper --------------------------------------------------------
def decide_batch(decider, readings: dict) -> dict:
    """Apply a per-well decider to {well: value}. Returns {well: Decision}."""
    return {well: decider(val) for well, val in readings.items()}


if __name__ == "__main__":
    for c in (2.4, 0.6, 0.1):
        print(f"pre-SPRI {c:>4} ng/uL -> {tipseq_pre_spri(c)}")
    print("post-SPRI 2.0 -> 1.3 :", tipseq_post_spri(2.0, 1.3))
    print("post-SPRI 2.0 -> 0.6 :", tipseq_post_spri(2.0, 0.6))
