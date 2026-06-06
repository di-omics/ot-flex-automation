"""Vendor-neutral liquid-handling protocol spec (the portable asset).

The whole point of this module: capture *what the protocol does* — volumes,
source -> destination maps, step order, off-deck handoffs — with **zero**
dependence on any vendor's API. Opentrons Python, Hamilton Venus, and Agilent
Bravo VWorks share none of their code, but they share this intent. Encode the
protocol once here; compile it to each platform with a backend.

A spec is plain data: it serializes to/from a dict (JSON/YAML), so the protocol
is a file you can diff, review, and hand to the next platform — not code locked
to one robot.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from math import ceil
from typing import Optional


# ── Labware ───────────────────────────────────────────────────────────
# `kind` is a vendor-neutral type; each backend maps it to its own catalog
# name (e.g. opentrons "nest_12_reservoir_15ml"). `slot` is the nominal deck
# position — advisory, a backend may remap it to its own deck geometry.
LABWARE_KINDS = {
    "pcr_plate_96",   # 96-well PCR plate
    "reservoir_12",   # 12-well reagent reservoir / trough
    "tiprack_200",    # 200 uL filter tips
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
    """Move `volume_ul` from one source well to a destination plate.

    mode="per_column" models an 8-channel distribute: aspirate from a single
    reservoir well, dispense into each column of the destination plate. This is
    the dominant motif in the kit protocols (distribute a master mix to all
    sample columns). Backends expand it to their own primitive (Opentrons
    column loop; a worklist row per destination well for STAR/Bravo).
    """
    source: str                       # "<labware_id>:<well>"
    dest: str                         # "<labware_id>" (all active columns)
    volume_ul: float
    mode: str = "per_column"
    new_tip: str = "each"             # "each" | "once" | "none"
    aspirate_z: float = 5.0           # mm above well bottom
    dispense_z: float = 5.0
    mix_after: Optional[tuple] = None  # (reps, volume_ul) or None
    comment: str = ""


@dataclass
class Handoff:
    """An off-deck operator step the liquid handler can't do — thermal cycling,
    magnet moves, a QC checkpoint. Compiles to a pause on every platform."""
    message: str


Step = object  # Transfer | Handoff (kept loose; backends isinstance-dispatch)


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

    # serialization — the spec as a portable file
    def to_dict(self) -> dict:
        d = asdict(self)
        d["steps"] = [{"_type": type(s).__name__, **asdict(s)} for s in self.steps]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ProtocolSpec":
        steps = []
        for s in d.get("steps", []):
            t = s.pop("_type")
            steps.append({"Transfer": Transfer, "Handoff": Handoff}[t](**s))
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
