"""
Thin link to the Flex for the orchestration layer.

Why this exists: a normal run() protocol is planned + simulated up front and
can't branch on a live sensor reading. To act on a plate read or a camera call
you drive the robot from OUTSIDE that flow -- over the HTTP API, or by running
commands in the Flex's Jupyter / SSH session. This wraps the moves the QC loop
needs:
  * resume a run paused at a Qubit checkpoint
  * (later) add PCR cycles / re-queue a cleanup segment

dry_run=True prints intended calls instead of hitting the robot, so the loop is
testable with no hardware. Live calls need `requests` + the robot IP.
HTTP reference: docs.opentrons.com -> Flex -> Additional Documentation.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class FlexLink:
    host: str = "169.254.1.1"   # robot IP on the wired/Wi-Fi link
    port: int = 31950           # default Opentrons HTTP port
    dry_run: bool = True

    @property
    def base(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _post(self, path: str, **kwargs):
        if self.dry_run:
            print(f"[dry-run] POST {self.base}{path} {kwargs or ''}")
            return {"dry_run": True, "path": path, **kwargs}
        import requests  # live only
        headers = {"Opentrons-Version": "*"}
        r = requests.post(f"{self.base}{path}", headers=headers, timeout=30, **kwargs)
        r.raise_for_status()
        return r.json()

    def resume_run(self, run_id: str):
        """Advance a run paused at a checkpoint (play action)."""
        return self._post(f"/runs/{run_id}/actions", json={"data": {"actionType": "play"}})

    def pause_run(self, run_id: str):
        return self._post(f"/runs/{run_id}/actions", json={"data": {"actionType": "pause"}})

    # TODO(hunter): cycle top-up / segment re-queue. Cleanest path is to make
    # each PCR/cleanup stage its own launchable segment so the orchestrator can
    # run "PCR +N cycles" on demand. See the runner issue.


if __name__ == "__main__":
    FlexLink(dry_run=True).resume_run("example-run-id")
