"""Thumb-button swipe detection: when does held-button mouse motion become a
touchpad swipe, and which way does it go?

Pure logic (no GLib, no devices) so it can be tested on recorded motion.
The daemon feeds it press / motion / release with timestamps and forwards
the answers to the virtual touchpad.

Why it is careful about the start: GNOME fixes a swipe's orientation —
workspaces (horizontal) or overview (vertical) — from the first ~0.4 mm of
finger motion, so the first motion handed to the fingers decides the whole
gesture. The thumb press can nudge the mouse, and hands often start a swipe
on a slight curve, so the direction is taken from where the hand is heading
once the motion is clearly one way, not from everything since the press.

Why it ignores the start of the press: a thumb tap is often made on the
move — the hand is heading for something and taps on the way. Recorded taps
like that (2026-11-11) carry all their motion in the first ~30 ms, often
hundreds of counts, and then the mouse stops dead: at most ~40 counts follow.
A quick swipe keeps moving: 54+ counts by 100 ms, 200+ by 150 ms. So motion
inside the settle window never decides anything, and what follows it does:
enough of it begins the swipe at once, carrying all of it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SwipeConfig:
    start: int = 80  # travel after the settle window that makes a swipe (or, released early, a flick)
    gain: float = 1.5  # touchpad units per sensor count
    axis_lock: bool = True  # once begun, drop motion across the swipe's axis
    settle_ms: float = 30  # motion this soon after the press is the press nudge
    recent_ms: float = 60  # window of motion that decides the direction
    recent_min: int = 50  # counts that window needs before it can decide
    dominance: float = 1.4  # dominant axis must beat the other by this (~35 degrees)
    rolling_min: int = 30  # travel inside the settle window that means the mouse was already moving (logged only)


class ThumbSwipe:
    """State of one thumb-button hold."""

    def __init__(self, cfg: SwipeConfig | None = None):
        self.cfg = cfg or SwipeConfig()
        self.reset()

    def press(self, t: float) -> None:
        """A fresh press: forget the previous hold."""
        self.reset()
        self.t0 = t

    def reset(self) -> None:
        self.t0 = 0.0
        self.active = False
        self.axis = ""  # "x", "y", or "" (free) once active
        self.total = [0, 0]  # everything since the press, nudge included
        self.path = 0  # travel after the settle window
        self.after = [0, 0]  # motion after the settle window, which a swipe carries
        self.recent: list[tuple[float, int, int]] = []
        self.settled = 0  # travel inside the settle window
        self.rolling = False  # the mouse was moving when the button went down

    def motion(self, t: float, dx: int, dy: int) -> tuple[str, float, float] | None:
        """Feed raw sensor motion while the button is held.

        Returns ("begin", x, y) when the swipe starts (put the fingers down
        and move them by x, y touchpad units), ("move", x, y) while it runs,
        or None while it is still undecided.
        """
        self.total[0] += dx
        self.total[1] += dy
        g = self.cfg.gain
        if self.active:
            if self.axis == "x":
                dy = 0
            elif self.axis == "y":
                dx = 0
            return ("move", dx * g, dy * g) if dx or dy else None
        held_ms = (t - self.t0) * 1000
        if held_ms < self.cfg.settle_ms:
            self.settled += abs(dx) + abs(dy)
            if self.settled >= self.cfg.rolling_min:
                self.rolling = True
            return None
        self.path += abs(dx) + abs(dy)
        self.after[0] += dx
        self.after[1] += dy
        self.recent.append((t, dx, dy))
        horizon = t - self.cfg.recent_ms / 1000
        self.recent = [r for r in self.recent if r[0] >= horizon]
        if self.path < self.cfg.start:
            return None
        rx = sum(r[1] for r in self.recent)
        ry = sum(r[2] for r in self.recent)
        if abs(rx) + abs(ry) < self.cfg.recent_min:
            return None
        return self._begin(rx, ry)

    def release(self, t: float) -> tuple[str, float, float]:
        """The button came up. Returns ("end", 0, 0) for a running swipe,
        ("flick", x, y) for a quick swipe that ended before it began (play it
        out now), or ("tap", 0, 0) for a press that never became a swipe."""
        if self.active:
            return ("end", 0.0, 0.0)
        if self.path >= self.cfg.start:
            # the mouse kept moving after the press: never a tap; no more motion
            # is coming to settle the direction, so a diagonal goes with its
            # stronger axis
            _, x, y = self._begin(*self.after, decided=True)
            return ("flick", x, y)
        return ("tap", 0.0, 0.0)

    def _begin(self, vx: float, vy: float, decided: bool = False) -> tuple[str, float, float] | None:
        """Start the swipe in the direction (vx, vy), carrying all the motion
        since the settle window so none of the hand's travel is lost."""
        horizontal = abs(vx) >= abs(vy)
        major, minor = (abs(vx), abs(vy)) if horizontal else (abs(vy), abs(vx))
        if not decided and major < self.cfg.dominance * minor:
            return None  # no clear direction yet
        self.active = True
        # carry the travel along the chosen way, unless the hand first went the other way
        ax, ay = self.after
        if horizontal and ax * vx > 0:
            vx = ax
        elif not horizontal and ay * vy > 0:
            vy = ay
        if self.cfg.axis_lock:
            self.axis = "x" if horizontal else "y"
            if horizontal:
                vy = 0
            else:
                vx = 0
        g = self.cfg.gain
        return ("begin", vx * g, vy * g)
