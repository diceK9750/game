"""Queued picture taps must refer to the card and round actually rendered."""
import json
import random
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from modern_ui import ModernUI
from shiritori import ShiritoriRound


class Root:
    def __init__(self):
        self.attributes = {"data-modern-ready": "true", "data-modern-commands": "[]"}
    def getAttribute(self, key):
        return self.attributes.get(key)
    def setAttribute(self, key, value):
        self.attributes[key] = value


class StalePictureInputTests(unittest.TestCase):
    def setUp(self):
        self.now = [0.0]
        self.game = ShiritoriRound(mode="solo", total=48, rng=random.Random(0), clock=lambda: self.now[0])
        self.game.start()
        self.root = Root()
        self.bridge = ModernUI(SimpleNamespace(documentElement=self.root))
        self.app = SimpleNamespace(screen="shiritori", shiritori=self.game, play_sfx=Mock())
        self.serial = 0

    def command(self, index, card_id, deal_id=None):
        return {"action": "sh_card", "value": index, "card_id": card_id,
                "deal_id": self.game.deal_id if deal_id is None else deal_id}

    def send(self, *commands):
        entries = []
        for command in commands:
            self.serial += 1
            entries.append({"id": self.serial, **command})
        self.root.attributes["data-modern-commands"] = json.dumps(entries)
        self.bridge.consume(self.app)

    def test_two_taps_on_old_picture_do_not_select_unseen_refill(self):
        move, _ = self.game.chain_advice()
        index = move[0]
        picture = self.game.cards[index][0]
        self.send(self.command(index, picture), self.command(index, picture))
        self.assertNotEqual(self.game.cards[index][0], picture)
        self.assertEqual(len(self.game.history), 1)
        self.assertEqual(self.game.mistakes, 0)
        self.assertEqual(self.bridge.ack, 2)
        self.app.play_sfx.assert_called_once()

    def test_two_distinct_visible_pictures_are_accepted_in_one_batch(self):
        move, plan = self.game.chain_advice()
        first, second = plan["route"][:2]
        self.assertNotEqual(first[0], second[0])
        first_id = self.game.cards[first[0]][0]
        second_id = self.game.cards[second[0]][0]
        self.send(self.command(first[0], first_id), self.command(second[0], second_id))
        self.assertEqual([row["id"] for row in self.game.history], [first_id, second_id])
        self.assertEqual(self.game.mistakes, 0)

    def test_newly_rendered_refill_can_be_selected_immediately(self):
        self.game = ShiritoriRound(mode="solo", total=48, rng=random.Random(70), clock=lambda: self.now[0])
        self.game.start()
        self.app.shiritori = self.game
        first, _ = self.game.chain_advice()
        index = first[0]
        old_id = self.game.cards[index][0]
        self.send(self.command(index, old_id))
        new_id = self.game.cards[index][0]
        self.assertNotEqual(old_id, new_id)
        self.assertIn(index, {i for i, _ in self.game.moves()})
        self.send(self.command(index, new_id))
        self.assertEqual([row["id"] for row in self.game.history], [old_id, new_id])
        self.assertEqual(self.game.mistakes, 0)

    def test_missing_partial_invalid_and_forged_metadata_is_rejected(self):
        index, _ = self.game.chain_advice()[0]
        picture = self.game.cards[index][0]
        for command in (
            {"action": "sh_card", "value": index, "card_id": picture},
            {"action": "sh_card", "value": index, "deal_id": self.game.deal_id},
            self.command(index, "forged"), self.command(index, picture, True),
            self.command(index, picture, self.game.deal_id + 1),
            self.command(True, picture), self.command(999, picture),
        ):
            with self.subTest(command=command):
                self.send(command)
                self.assertFalse(self.game.history)
                self.assertEqual(self.game.mistakes, 0)
        self.app.play_sfx.assert_not_called()

    def test_prior_round_is_rejected_even_if_same_picture_is_in_same_slot(self):
        move, _ = self.game.chain_advice()
        index = move[0]
        picture, old_deal = self.game.cards[index][0], self.game.deal_id
        self.game.rng.seed(0)
        self.game.start()
        self.assertEqual(self.game.cards[index][0], picture)
        self.assertNotEqual(self.game.deal_id, old_deal)
        self.send(self.command(index, picture, old_deal))
        self.assertFalse(self.game.history)
        self.send(self.command(index, picture))
        self.assertEqual(len(self.game.history), 1)

    def test_legacy_integer_only_command_remains_supported(self):
        move, _ = self.game.chain_advice()
        self.send({"action": "sh_card", "value": move[0]})
        self.assertEqual(len(self.game.history), 1)
        self.assertEqual(self.game.mistakes, 0)

    def test_cpu_move_before_queued_tap_rejects_replaced_picture(self):
        game = ShiritoriRound(mode="battle", total=48, rng=random.Random(0), clock=lambda: self.now[0])
        game.start()
        game.rng.random = lambda: 1.0  # hand off after the first CPU answer
        self.app.shiritori = self.game = game
        player, _ = game.chain_advice()
        game.command("card", player[0])
        self.now[0] += 4.6
        game.update()
        self.assertEqual(game.turn, "cpu")
        index = game.cpu_move[0]
        old_id = game.cards[index][0]
        self.now[0] = game.cpu_due
        self.send(self.command(index, old_id))
        self.assertEqual(game.history[-1]["owner"], "cpu")
        self.assertNotEqual(game.cards[index][0], old_id)
        self.assertEqual(game.turn, "you")
        self.assertEqual(game.mistakes, 0)
        self.assertEqual(len(game.history), 2)


if __name__ == "__main__":
    unittest.main()
