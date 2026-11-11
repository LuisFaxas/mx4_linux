"""Thumb wheel steps.

    python3 -m unittest discover tests
"""

import unittest

from mx4.thumbwheel import ACTIVE, START, WheelConfig, WheelSteps

EVENT_S = 0.010


def turn(rotations, cfg=None, t0=0.0):
    """Feed rotation events 10 ms apart, the first marked as a fresh touch."""
    w = WheelSteps(cfg or WheelConfig())
    out = [w.feed(t0 + i * EVENT_S, r, START if i == 0 else ACTIVE) for i, r in enumerate(rotations)]
    return w, out


class Steps(unittest.TestCase):
    def test_small_nudge_does_nothing(self):
        _, out = turn([5, 5, 5])
        self.assertEqual(sum(out), 0)

    def test_first_step_comes_after_half_a_step(self):
        _, out = turn([10, 10, 10])
        self.assertEqual(out, [0, 0, 1])

    def test_long_turn_steps_steadily(self):
        cfg = WheelConfig()
        _, out = turn([10] * 33, cfg)  # 330 units: 30 for the first, then 60 each
        self.assertEqual(sum(out), 1 + (330 - cfg.first) // cfg.step)

    def test_backwards_is_prev(self):
        _, out = turn([-15, -15, -15])
        self.assertEqual(sum(out), -1)

    def test_fast_flick_can_fire_several(self):
        _, out = turn([150])
        self.assertEqual(out, [3])  # 30 + 60 + 60

    def test_pause_starts_a_fresh_turn(self):
        w, _ = turn([20])
        self.assertEqual(w.feed(0.5, 20), 0)  # leftover 20 dropped: 20 < 30
        self.assertEqual(w.feed(0.51, 15), 1)

    def test_reversing_mid_turn(self):
        _, out = turn([30, -10, -10, -10, -10, -10, -10, -10, -10, -10])
        self.assertEqual(out[0], 1)
        self.assertEqual(sum(out[1:]), -1)


if __name__ == "__main__":
    unittest.main()
