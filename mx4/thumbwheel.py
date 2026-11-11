"""Thumb wheel steps: turn diverted thumb-wheel rotation into whole actions
(one workspace per step) instead of sideways scrolling.

Pure logic (no GLib, no devices) so it can be tested on recorded rotation.
The daemon diverts the wheel (feature 0x2150), feeds every rotation event
here and runs the next / prev action once per step returned.

The first step of a turn comes after half a step of rotation, so a flick of
the thumb answers at once; later steps need a whole step each, so a long
turn walks through the workspaces at a steady rate. A pause or a fresh touch
starts a new turn and drops what was left over.
"""

from __future__ import annotations

from dataclasses import dataclass

# rotationStatus of a 0x2150 event
INACTIVE, START, ACTIVE, STOP = 0, 1, 2, 3


@dataclass
class WheelConfig:
    step: int = 60  # rotation units per action
    first: int = 30  # rotation units before the first action of a turn
    idle_ms: float = 400  # a pause this long starts a fresh turn


class WheelSteps:
    """State of the thumb wheel between events."""

    def __init__(self, cfg: WheelConfig | None = None):
        self.cfg = cfg or WheelConfig()
        self.acc = 0
        self.stepped = False  # this turn has already fired
        self.last = None

    def feed(self, t: float, rotation: int, status: int = ACTIVE) -> int:
        """Feed one rotation event at time t (seconds). Returns the actions
        to run: positive for next, negative for prev, 0 for none yet."""
        if status == START or self.last is None or (t - self.last) * 1000 >= self.cfg.idle_ms:
            self.acc = 0
            self.stepped = False
        self.last = t
        self.acc += rotation
        steps = 0
        need = self.cfg.step if self.stepped else self.cfg.first
        while abs(self.acc) >= need:
            sign = 1 if self.acc > 0 else -1
            steps += sign
            self.acc -= sign * need
            self.stepped = True
            need = self.cfg.step
        return steps
