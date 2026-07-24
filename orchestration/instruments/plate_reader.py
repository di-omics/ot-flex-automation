"""
Plate-reader adapters for the orchestration layer.

Job: turn whatever a fluorescence microplate reader produces into
{well: ng_per_uL}, so the decision engine can run on it.

v1 = CsvPlateReader (watch a file the reader exports + apply a dsDNA standard
curve). Live SDK / SiLA backends are stubbed -- the CSV path is robust and
vendor-agnostic, so it's the right first step.

Assay: a fluorometric dsDNA assay in a compatible black microplate. The reader
gives RFU; the standard curve maps RFU to ng/uL.
"""
from __future__ import annotations
import csv
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StandardCurve:
    """Linear fit RFU = slope * (ng/uL) + intercept, applied in reverse.
    Fit from per-run standards (DNA mass standards -> RFU)."""
    slope: float
    intercept: float = 0.0

    def rfu_to_ng_ul(self, rfu: float) -> float:
        if self.slope == 0:
            raise ValueError("standard-curve slope is 0; refit standards")
        return max((rfu - self.intercept) / self.slope, 0.0)

    @classmethod
    def from_points(cls, points: list[tuple[float, float]]) -> "StandardCurve":
        """Least-squares fit from [(ng_ul, rfu), ...]."""
        n = len(points)
        if n < 2:
            raise ValueError("need >= 2 standard points")
        sx = sum(x for x, _ in points)
        sy = sum(y for _, y in points)
        sxx = sum(x * x for x, _ in points)
        sxy = sum(x * y for x, y in points)
        denom = n * sxx - sx * sx
        if denom == 0:
            raise ValueError("degenerate standards (all same concentration)")
        slope = (n * sxy - sx * sy) / denom
        intercept = (sy - slope * sx) / n
        return cls(slope=slope, intercept=intercept)


class PlateReader(ABC):
    """A source of per-well dsDNA concentrations."""

    @abstractmethod
    def read_plate(self) -> dict[str, float]:
        """Return {well_id: ng_per_uL}, e.g. {'A1': 2.4, ...}."""
        raise NotImplementedError


class CsvPlateReader(PlateReader):
    """Parse a CSV the reader exports. Two layouts:

      'long' : columns  well,rfu          (one row per well)
      'grid' : 8x12 block of RFU values, row labels A-H, col labels 1-12

    `blank_rfu` is subtracted before the curve (buffer-only well); set to 0 if
    the curve intercept already encodes the baseline.
    """

    def __init__(self, path: str | Path, curve: StandardCurve,
                 layout: str = "long", blank_rfu: float = 0.0):
        self.path = Path(path)
        self.curve = curve
        self.layout = layout
        self.blank_rfu = blank_rfu

    def read_plate(self) -> dict[str, float]:
        if not self.path.exists():
            raise FileNotFoundError(f"reader export not found: {self.path}")
        rfu = self._parse_long() if self.layout == "long" else self._parse_grid()
        return {w: self.curve.rfu_to_ng_ul(v - self.blank_rfu) for w, v in rfu.items()}

    def wait_for_export(self, timeout_s: float = 600, poll_s: float = 2.0) -> dict[str, float]:
        """Block until the export file appears (non-empty), then read it.
        TODO: guard against partial writes (size stable across 2 polls)."""
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self.path.exists() and self.path.stat().st_size > 0:
                return self.read_plate()
            time.sleep(poll_s)
        raise TimeoutError(f"no reader export at {self.path} within {timeout_s}s")

    def _parse_long(self) -> dict[str, float]:
        out: dict[str, float] = {}
        with self.path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            cols = {c.lower(): c for c in (reader.fieldnames or [])}
            wkey = cols.get("well")
            rkey = cols.get("rfu") or cols.get("value") or cols.get("fluorescence")
            if not wkey or not rkey:
                raise ValueError(f"expected 'well' and 'rfu' columns, got {reader.fieldnames}")
            for row in reader:
                out[row[wkey].strip().upper()] = float(row[rkey])
        return out

    def _parse_grid(self) -> dict[str, float]:
        out: dict[str, float] = {}
        with self.path.open(newline="") as fh:
            rows = [r for r in csv.reader(fh) if any(c.strip() for c in r)]
        for r in rows:
            label = r[0].strip().upper()
            if len(label) == 1 and label in "ABCDEFGH":
                for j, cell in enumerate(r[1:], start=1):
                    cell = cell.strip()
                    if cell:
                        out[f"{label}{j}"] = float(cell)
        if not out:
            raise ValueError("no A-H row labels found; is this a grid export?")
        return out


# ---- live backends (STUB -- see issue: plate-reader CSV adapter) ----------
class SerialPlateReader(PlateReader):  # pragma: no cover
    """TODO: drive a reader over serial/USB or a vendor SDK. SiLA2 is a
    cross-platform option. Implement
    only after the CSV path is proven on a real run."""
    def read_plate(self) -> dict[str, float]:
        raise NotImplementedError("live reader backend not implemented yet")


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    example = here.parent / "examples" / "sample_plate_read.csv"
    curve = StandardCurve.from_points([(0, 50), (1, 1050), (5, 5050), (10, 10050)])
    rr = CsvPlateReader(example, curve, layout="long", blank_rfu=0.0)
    if example.exists():
        for well, ng in rr.read_plate().items():
            print(f"{well}: {ng:.2f} ng/uL")
    else:
        print(f"(no example file at {example})")
