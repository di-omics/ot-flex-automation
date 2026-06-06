"""Vendor-neutral liquid-handling protocol spec (the portable asset).

The whole point of this module: capture *what the protocol does* - volumes,
source -> destination maps, step order, off-deck handoffs - with **zero**
dependence on any vendor's API. Opentrons Python, Hamilton Venus, and Agilent
Bravo VWorks share none of their code, but they share this intent. Encode the
protocol once here; compile it to each platform with a backend.

A spec is plain data: it serializes to/from a dict (JSON/YAML), so the protocol
is a file you can diff, review, and hand to the next platform - not code locked
to one robot.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from math import ceil
from typing import Optional


# ── Labware ───────────────────────────────────────────────────────────
# `kind` is a vendor-neutral type; each backend maps it to its own catalog
# name (e.g. opentrons "nest_12_reservoir_15ml"). `slot` is the nominal deck
# position - advisory, a backend may remap it to its own deck geometry.
LABWARE_KINDS = {
    "pcr_plate_96",   # 96-well PCR plate
    "reservoir_12",   # 12-well reagent reservoir / trough
    "tiprack_200",    # 200 uL filter tips
    "tiprack_1000",   # 1000 uL tips (Studio45's loaded tips)
    "magnet",         # magnetic block/module
    "trash",          # waste / trash bin
}


@dataclass
class Labware:
    id: str            # logical handle used by steps, e.g. "sample_plate"
    kind: str          # one of LABWARE_KINDS
    slot: str          # nominal deck slot, e.g. "B2"
    label: str = ""

    def __post_init__(self):
        if self.kind not in LABWARE_KINDS:
            raise ValueError(f"unknown labware kind {self.kind!r}; pick from {sorted(LABWARE_KINDS)}")


@dataclass
class Liquid:
    id: str            # e.g. "lysis_mix"
    location: str      # "<labware_id>:<well>", e.g. "source_plate:A1"
    description: str = ""


# ── Steps ─────────────────────────────────────────────────────────────
@dataclass
class Transfer:
    """Move `volume_ul` between a source and a destination, 8-channel column-wise.

    Source and dest are each either a single well ("<labware>:<well>", e.g. a
    reservoir trough or a waste well) or a whole plate ("<labware>"). The mode is
    inferred from which is which - this covers every motif in the kit protocols:

      well  -> plate : distribute a master mix to each sample column (reagent add)
      plate -> well  : pool each column into one well (remove supernatant / EtOH)
      plate -> plate : column i -> column i (transfer eluate to the output plate)
      well  -> well  : a single trough-to-trough move

    Backends expand it to their own primitive (Opentrons column loop; worklist
    rows for STAR/Bravo).
    """
    source: str                       # "<labware>" or "<labware>:<well>"
    dest: str                         # "<labware>" or "<labware>:<well>"
    volume_ul: float
    new_tip: str = "each"             # "each" | "once" | "none"
    aspirate_z: float = 5.0           # mm above well bottom
    dispense_z: float = 5.0
    mix_after: Optional[tuple] = None  # (reps, volume_ul) or None
    comment: str = ""


@dataclass
class Handoff:
    """An off-deck operator step the liquid handler can't do - thermal cycling,
    magnet moves, a QC checkpoint. Compiles to a pause on every platform."""
    message: str


@dataclass
class Delay:
    """An on-deck timed wait (e.g. an EtOH soak). Unlike a Handoff it needs no
    operator - the robot just waits. Compiles to protocol.delay()."""
    seconds: int
    message: str = ""


@dataclass
class MoveLabware:
    """Relocate a plate to another deck slot - by the Flex Gripper
    (use_gripper=True) or a manual operator move. Models "take the plate to the
    reader / onto the magnet / off the magnet." Destination slot must be empty."""
    labware: str          # labware id to move
    to_slot: str          # destination deck slot, e.g. "D1"
    use_gripper: bool = True
    comment: str = ""


Step = object  # Transfer | Handoff | Delay | MoveLabware (backends isinstance-dispatch)


# ── Protocol ──────────────────────────────────────────────────────────
@dataclass
class ProtocolSpec:
    name: str
    num_samples: int                  # multiple of 8
    labware: list[Labware]
    liquids: list[Liquid] = field(default_factory=list)
    steps: list = field(default_factory=list)
    description: str = ""

    @property
    def num_columns(self) -> int:
        return ceil(self.num_samples / 8)

    def labware_by_id(self, lid: str) -> Labware:
        for lw in self.labware:
            if lw.id == lid:
                return lw
        raise KeyError(f"no labware with id {lid!r}")

    # serialization - the spec as a portable file
    def to_dict(self) -> dict:
        d = asdict(self)
        d["steps"] = [{"_type": type(s).__name__, **asdict(s)} for s in self.steps]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ProtocolSpec":
        steps = []
        for s in d.get("steps", []):
            t = s.pop("_type")
            steps.append({"Transfer": Transfer, "Handoff": Handoff, "Delay": Delay,
                          "MoveLabware": MoveLabware}[t](**s))
        return cls(
            name=d["name"],
            num_samples=d["num_samples"],
            labware=[Labware(**lw) for lw in d["labware"]],
            liquids=[Liquid(**lq) for lq in d.get("liquids", [])],
            steps=steps,
            description=d.get("description", ""),
        )


def split_loc(loc: str) -> tuple[str, str]:
    """'source_plate:A1' -> ('source_plate', 'A1')."""
    lid, _, well = loc.partition(":")
    return lid, well
