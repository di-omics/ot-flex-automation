"""Hamilton STAR (Venus) backend - the seam, deliberately a stub.

A native Venus method is generated/edited in Hamilton's tooling, not emitted as
text the way an Opentrons `.py` is. So the realistic port path has two tiers:

  1. NOW (works today): drive the STAR from the **worklist CSV**
     (`worklist_backend`). Venus's worklist/sequence import consumes
     `source -> dest, volume` rows directly. The same spec that runs on the Flex
     produces that worklist - that's the portability win, available immediately.

  2. LATER (native): a Venus method template parameterized by the spec
     (labware mapping to the STAR deck, tip types, liquid classes for the
     1-3% CV target). That's where platform-specific accuracy tuning lives.

This module marks tier 2 explicitly so the port is a known fill-in-the-blanks,
not a surprise rewrite. For now it points callers at the worklist.
"""
from __future__ import annotations

from ..spec import ProtocolSpec
from . import worklist_backend


def render(spec: ProtocolSpec) -> str:
    raise NotImplementedError(
        "Native Venus method generation is Phase 3 (port + 1-3% CV tuning).\n"
        "Interim path available today: use the worklist backend -\n"
        "  python -m orchestration.portable.render --target worklist\n"
        "and import the CSV into Venus. See this module's docstring for the plan."
    )


def render_worklist(spec: ProtocolSpec) -> str:
    """Interim Hamilton path: the vendor-neutral worklist Venus can import now."""
    return worklist_backend.render(spec)
