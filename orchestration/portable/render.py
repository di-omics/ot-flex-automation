"""Render the portable example spec to a target platform.

    python -m orchestration.portable.render --target opentrons        # Flex .py
    python -m orchestration.portable.render --target worklist          # STAR/Bravo CSV
    python -m orchestration.portable.render --target spec              # the portable JSON
    python -m orchestration.portable.render --target opentrons --out flex_wga.py

One spec in; the platform-specific artifact out. The spec is the asset that
survives the move from Flex to Hamilton/Bravo.
"""
from __future__ import annotations

import argparse
import json
import sys

from .examples import (resolvedna_wga, hello_water, resolvedna_full,
                       wga_water_test, wga_move_to_reader)
from .backends import opentrons_backend, worklist_backend, hamilton_backend

EXAMPLES = {
    "wga": resolvedna_wga.build_spec,
    "hello": hello_water.build_spec,
    "resolvedna": resolvedna_full.build_spec,
    "wga_test": wga_water_test.build_spec,
    "wga_move": wga_move_to_reader.build_spec,
}


def render(target: str, num_samples: int, example: str = "wga",
           mount: str = "right", return_tips: bool = False) -> str:
    spec = EXAMPLES[example](num_samples=num_samples)
    if target == "opentrons":
        return opentrons_backend.render(spec, mount=mount, return_tips=return_tips)
    if target == "worklist":
        return worklist_backend.render(spec)
    if target == "hamilton":
        return hamilton_backend.render_worklist(spec)  # interim worklist path
    if target == "spec":
        return json.dumps(spec.to_dict(), indent=2)
    raise SystemExit(f"unknown target {target!r}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", required=True,
                   choices=["opentrons", "worklist", "hamilton", "spec"])
    p.add_argument("--example", default="wga", choices=list(EXAMPLES),
                   help="which portable spec to render (default: wga)")
    p.add_argument("--mount", default="right", choices=["left", "right"],
                   help="Opentrons pipette mount (Studio45's p1000 is on the LEFT)")
    p.add_argument("--return-tips", action="store_true",
                   help="return tips to the rack instead of trashing (water testing)")
    p.add_argument("--num-samples", type=int, default=8)
    p.add_argument("--out", help="write to file instead of stdout")
    a = p.parse_args(argv)

    text = render(a.target, a.num_samples, a.example, a.mount, a.return_tips)
    if a.out:
        with open(a.out, "w") as f:
            f.write(text)
        print(f"wrote {a.out} ({len(text)} bytes)", file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
