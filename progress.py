"""Small, validated browser save; unavailable storage never stops a game."""
import json
import math

KEY = "number-rush-progress-v1"


def decode(raw):
    result = {"best_times": {}, "battle_records": {}, "bonus_bank": 0,
              "bgm_on": True, "sfx_on": True, "reduced_motion": False}
    try:
        data = json.loads(raw or "{}")
    except (ValueError, TypeError):
        return result
    if not isinstance(data, dict) or data.get("version") != 1:
        return result
    for field, size in (("best_times", 2), ("battle_records", 3)):
        records = data.get(field, [])
        if not isinstance(records, list):
            continue
        for entry in records[:100]:
            if not isinstance(entry, list) or len(entry) != size + 1:
                continue
            count, mode, *rest = entry
            value = rest[-1]
            if type(count) is not int or count not in (10, 20, 30, 40):
                continue
            if mode not in ("ordered", "random"):
                continue
            if size == 3 and rest[0] not in ("easy", "normal", "hard"):
                continue
            if type(value) not in (float, int) or not math.isfinite(value) or value < 0:
                continue
            if size == 3 and (type(value) is not int or value > count):
                continue
            result[field][tuple(entry[:-1])] = value
    bonus = data.get("bonus_bank")
    if type(bonus) is int and 0 <= bonus <= 10**12:
        result["bonus_bank"] = bonus
    for field in ("bgm_on", "sfx_on", "reduced_motion"):
        if type(data.get(field)) is bool:
            result[field] = data[field]
    return result


def encode(app):
    return json.dumps({"version": 1,
        "best_times": [list(k) + [v] for k, v in app.best_times.items()],
        "battle_records": [list(k) + [v] for k, v in app.battle_records.items()],
        "bonus_bank": app.bonus_bank, "bgm_on": app.bgm_on,
        "sfx_on": app.sfx_on, "reduced_motion": app.reduced_motion},
        allow_nan=False)


def load():
    try:
        from js import localStorage
        return decode(localStorage.getItem(KEY))
    except Exception:
        return decode(None)


def save(app):
    try:
        from js import localStorage
        localStorage.setItem(KEY, encode(app))
        return True
    except Exception:
        return False
