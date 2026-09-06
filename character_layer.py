"""Optional HD presentation bridge. The game always owns input and timing."""
import json


class CharacterLayer:
    def __init__(self, document=None):
        self.root = document.documentElement if document is not None else None
        self.last_state = None

    @property
    def ready(self):
        if self.root is None:
            return False
        try:
            return self.root.getAttribute("data-character-ready") == "true"
        except Exception:
            return False

    def sync(self, screen, left, right, reduced_motion, perfect=False):
        if self.root is None:
            return
        state = json.dumps({"screen": screen, "left": left, "right": right,
                            "reduced": bool(reduced_motion), "perfect": bool(perfect)})
        if state != self.last_state:
            try:
                self.root.setAttribute("data-character-state", state)
                self.last_state = state
            except Exception:
                # A failed presentation layer must never stop a round.
                pass
