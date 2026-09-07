"""Small, optional browser presentation bridge; Python remains the game engine.

The DOM carries JSON data only. Commands are validated, acknowledged once, and
sent through the same game methods as native input. No browser-only scoring or
CPU timing exists, so the desktop Pyxel renderer remains a complete fallback.
"""

import json
import math

from game_logic import BattleRound
from shiritori import ShiritoriRound


class ModernUI:
    MAX_COMMANDS = 128
    MAX_BYTES = 65_536
    MAX_ID = 9_007_199_254_740_991

    def __init__(self, document=None):
        try:
            self.root = document.documentElement if document is not None else None
        except Exception:
            self.root = None
        self.last_state = None
        self.ack = 0

    @property
    def ready(self):
        try:
            return self.root is not None and self.root.getAttribute("data-modern-ready") == "true"
        except Exception:
            return False

    def consume(self, app):
        """Drain a bounded queue once, before the CPU's update for this frame."""
        if not self.ready:
            return
        try:
            raw = self.root.getAttribute("data-modern-commands")
            if not raw or raw == "[]":
                return
            # Never execute if draining failed: this avoids replaying input.
            self.root.setAttribute("data-modern-commands", "[]")
            if not isinstance(raw, str) or len(raw) > self.MAX_BYTES:
                return
            if len(raw.encode("utf-8")) > self.MAX_BYTES:
                return
            commands = json.loads(raw)
        except Exception:
            return
        if not isinstance(commands, list) or len(commands) > self.MAX_COMMANDS:
            return
        for command in commands:
            if not isinstance(command, dict):
                continue
            command_id = command.get("id")
            if type(command_id) is not int or not self.ack < command_id <= self.MAX_ID:
                continue
            # Invalid or stale-screen actions are acknowledged too; retries must
            # not unexpectedly fire after the player moves to another screen.
            self.ack = command_id
            self.dispatch(app, command)

    @staticmethod
    def dispatch(app, command):
        action = command.get("action")
        value = command.get("value")
        if not isinstance(action, str):
            return
        screen = app.screen
        if action == "bgm":
            app.toggle_bgm()
        elif action == "sfx":
            app.toggle_sfx()
        elif action == "motion":
            app.toggle_motion()
        elif screen == "shiritori":
            if action == "sh_exit" and app.shiritori.phase in ("intro", "paused", "finished"):
                app.screen = "ready"
                app.game_selected = False
            elif action.startswith("sh_"):
                before = (len(app.shiritori.history), app.shiritori.mistakes)
                app.shiritori.command(action[3:], value)
                if app.shiritori.mistakes > before[1]:
                    app.play_sfx(1)
                elif len(app.shiritori.history) > before[0]:
                    app.play_sfx(0)
        elif screen == "ready":
            if action == "home":
                app.game_selected = False
            elif action == "numbers":
                app.game_selected = True
            elif action == "shiritori":
                if not hasattr(app, "shiritori"):
                    app.shiritori = ShiritoriRound(app.difficulty, mode="solo")
                else:
                    app.shiritori.phase = "intro"
                app.screen = "shiritori"
            elif not getattr(app, "game_selected", False):
                return
            elif action == "kind" and value in ("battle", "practice"):
                app.play_kind = value
            elif action == "range" and type(value) is int and value in (10, 20, 30, 40):
                app.selected_max_number = value
            elif action == "difficulty" and value in ("easy", "normal", "hard"):
                app.difficulty = value
            elif action == "start" and value in ("ordered", "random"):
                app.begin_countdown(value)
            elif action == "help":
                app.screen = "help"
        elif screen == "playing":
            if action == "cell":
                index = command.get("index")
                if type(index) is int and 0 <= index < len(app.round.board_cells):
                    app.keyboard_cursor = False
                    app.cursor_cell = index
                    app.handle_tap(index)
            elif action in ("pause", "retry", "title"):
                app.open_confirmation(action)
            elif action == "hint":
                app.show_hint()
        elif screen == "countdown" and action == "title":
            app.clear_feedback()
            app.screen = "ready"
        elif screen == "confirm":
            if action == "yes":
                if app.confirm_action == "pause":
                    app.cancel_confirmation()
                else:
                    app.accept_confirmation()
            elif action == "no":
                app.cancel_confirmation()
            elif action in ("title", "retry"):
                app.confirm_action = action
        elif screen == "finished":
            if action == "retry":
                app.begin_countdown(app.selected_mode)
            elif action == "title":
                app.clear_feedback()
                app.screen = "ready"
            elif action == "review" and isinstance(app.round, BattleRound):
                app.screen = "review"
        elif screen == "help" and action == "back":
            app.screen = "ready"
        elif screen == "review" and action == "back":
            app.screen = "finished"

    def snapshot(self, app, frame_count=0):
        """Return presentation state without revealing hidden boards or targets."""
        screen = "home" if app.screen == "ready" and not getattr(app, "game_selected", False) else app.screen
        round_ = app.round
        uses_round = screen not in ("home", "ready", "help", "countdown")
        battle = uses_round and isinstance(round_, BattleRound)
        count = round_.max_number if uses_round else app.selected_max_number
        mode = round_.mode if uses_round else app.selected_mode
        kind = ("battle" if battle else "practice") if uses_round else app.play_kind
        difficulty = round_.difficulty if battle else app.difficulty
        board_visible = screen in ("playing", "finished", "review")
        elapsed = round_.elapsed() if uses_round else 0.0
        effects = {index: (effect, started) for effect, index, started in app.cell_effects}
        cells = []
        if board_visible:
            for index, number in enumerate(round_.board_cells):
                effect, started = effects.get(index, (None, None))
                owner = round_.owners.get(number) if battle else "you" if number in round_.found_numbers else None
                cells.append({"n": number, "owner": owner, "effect": effect,
                              "effect_id": f"{effect}:{started}" if effect else None})
        cpu_remaining = max(0.0, round_.cpu_at - elapsed) if battle and round_.is_playing else 0.0
        cpu_progress = (min(1.0, max(0.0, (elapsed - round_.ready_at) /
                        max(0.01, round_.cpu_at - round_.ready_at)))
                        if battle and round_.is_playing else 0.0)
        hint_index = None
        if (screen == "playing" and not battle and frame_count < app.hint_until
                and round_.current_target in round_.board_cells):
            hint_index = round_.board_cells.index(round_.current_target)
        countdown = 0
        if screen in ("countdown", "resuming"):
            end = app.countdown_end_frame if screen == "countdown" else app.resume_end_frame
            countdown = max(1, math.ceil((end - frame_count) / 60))
        left, right = app.character_actions()
        history = []
        if battle and screen in ("finished", "review"):
            history = [{**entry, "seconds": round(entry["seconds"], 2)} for entry in round_.history]
        return {
            "v": 1, "screen": screen, "kind": kind, "difficulty": difficulty,
            "max_number": count, "mode": mode, "bgm": bool(app.bgm_on),
            "sfx": bool(app.sfx_on), "reduced": bool(app.reduced_motion),
            "elapsed": round(elapsed, 2 if screen in ("finished", "review") else 1),
            "target": round_.current_target if screen == "playing" else None,
            "completed": round_.completed_count if uses_round else 0,
            "mistakes": round_.mistakes if uses_round else 0,
            "score": app.score if uses_round else 0,
            "streak": app.streak if uses_round else 0,
            "max_streak": app.max_streak if uses_round else 0,
            "player_points": round_.player_points if battle else 0,
            "cpu_points": round_.cpu_points if battle else 0,
            "goal": round_.goal if battle else (count * 3 + 4) // 5,
            "cpu_remaining": round(cpu_remaining, 1), "cpu_progress": round(cpu_progress, 2),
            "won": round_.won if battle else round_.is_finished if uses_round else False,
            "perfect": round_.is_perfect if battle else False,
            "bonus": round_.special_bonus if battle else 0,
            "bonus_bank": app.bonus_bank, "is_new_best": bool(app.is_new_best) if uses_round else False,
            "best_time": app.best_times.get((count, mode)),
            "best_points": app.battle_records.get((count, mode, difficulty)),
            "hint_used": bool(app.hint_used) if uses_round else False,
            "hint_index": hint_index, "countdown": countdown,
            "confirm_action": app.confirm_action if screen == "confirm" else None,
            "cells": cells, "left": left, "right": right, "history": history, "ack": self.ack,
            "shiritori": app.shiritori.snapshot() if screen == "shiritori" else None,
        }

    def sync(self, app, frame_count=0):
        if self.root is None:
            return
        try:
            state = json.dumps(self.snapshot(app, frame_count), ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False)
            if state == self.last_state:
                return
            self.root.setAttribute("data-modern-state", state)
            self.last_state = state
        except Exception:
            # Release the renderer/input ownership as well as swallowing DOM
            # failures, so the native game can remain usable after a failure.
            try:
                self.root.setAttribute("data-modern-ready", "false")
            except Exception:
                pass
