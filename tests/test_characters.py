import unittest
from characters import ACTIONS, draw_rival


class RecordedRenderer:
    def __init__(self, frame=42):
        self.frame_count = frame
        self.calls = []

    def __getattr__(self, name):
        def record(*args):
            self.calls.append((name, args))
        return record


class CharacterTests(unittest.TestCase):
    def test_every_pose_fits_its_stage_space_at_all_animation_phases(self):
        for species in ("rabbit", "red_panda"):
            for action in ACTIONS:
                for frame in range(0, 240, 7):
                    g = RecordedRenderer(frame)
                    draw_rival(g, 0, 0, species, action)
                    for name, args in g.calls:
                        self.assertIn(args[-1], range(16))
                        if name in {"rect", "elli"}:
                            x, y, w, h, _ = args
                            bounds = (x, y, x + w - 1, y + h - 1)
                        elif name == "circ":
                            x, y, radius, _ = args
                            bounds = (x - radius, y - radius, x + radius, y + radius)
                        else:
                            coords = args[:-1]
                            bounds = (min(coords[::2]), min(coords[1::2]),
                                      max(coords[::2]), max(coords[1::2]))
                        x1, y1, x2, y2 = bounds
                        self.assertGreaterEqual(x1, -4)
                        self.assertGreaterEqual(y1, -14)
                        self.assertLessEqual(x2, 70)
                        self.assertLessEqual(y2, 60)

    def test_rivals_and_emotions_have_distinct_drawings(self):
        poses = []
        for species in ("rabbit", "red_panda"):
            for action in ACTIONS:
                g = RecordedRenderer()
                draw_rival(g, 0, 0, species, action)
                poses.append(tuple(g.calls))
        self.assertEqual(len(set(poses)), 12)

    def test_idle_motion_is_not_a_static_image(self):
        for species in ("rabbit", "red_panda"):
            poses = []
            for frame in (0, 32, 72):
                g = RecordedRenderer(frame)
                draw_rival(g, 0, 0, species, "idle")
                poses.append(tuple(g.calls))
            self.assertEqual(len(set(poses)), 3)

    def test_reduced_motion_freezes_every_pose(self):
        for species in ("rabbit", "red_panda"):
            for action in ACTIONS:
                poses = []
                for frame in (0, 32, 72, 223):
                    g = RecordedRenderer(frame)
                    draw_rival(g, 0, 0, species, action, motion=False)
                    poses.append(tuple(g.calls))
                self.assertEqual(len(set(poses)), 1)


if __name__ == "__main__":
    unittest.main()
