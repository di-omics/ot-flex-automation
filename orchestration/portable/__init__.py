"""Portable protocol layer: write the protocol once, run it on every platform.

See README.md. The protocol lives as a vendor-neutral `ProtocolSpec` (spec.py);
backends compile it to a specific liquid handler (Opentrons today; a STAR/Bravo
worklist for the port; native Hamilton Venus later).
"""
