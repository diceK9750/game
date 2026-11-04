"""Small, validated browser save; unavailable storage never stops a game."""
import json
import math

KEY = "number-rush-progress-v1"

_SETTING_DEFAULTS = {
    'bgm_on': True, 'sfx_on': True, 'reduced_motion': False,
    'selected_max_number': 40, 'selected_mode': 'ordered',
    'play_kind': 'battle', 'difficulty': 'normal',
}


def decode(raw):
    result = {"best_times": {}, "battle_records": {}, "bonus_bank": 0,
              "bgm_on": True, "sfx_on": True, "reduced_motion": False}
    try:
        data = json.loads(raw or "{}")
    except (ValueError, TypeError, RecursionError):
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
            if type(value) not in (float, int) or not 0 <= value <= 10**12 or not math.isfinite(value):
                continue
            if size == 3 and (type(value) is not int or value > count):
                continue
            key = tuple(entry[:-1])
            old = result[field].get(key)
            result[field][key] = value if old is None else (min(old, value) if size == 2 else max(old, value))
    bonus = data.get("bonus_bank")
    if type(bonus) is int and 0 <= bonus <= 10**12:
        result["bonus_bank"] = bonus
    for field in ("bgm_on", "sfx_on", "reduced_motion"):
        if type(data.get(field)) is bool:
            result[field] = data[field]
    # Optional additions to v1: old saves keep their existing defaults.
    for field, allowed in (("selected_max_number", (10, 20, 30, 40)),
                           ("selected_mode", ("ordered", "random")),
                           ("play_kind", ("battle", "practice")),
                           ("difficulty", ("easy", "normal", "hard"))):
        value = data.get(field)
        if type(value) is type(allowed[0]) and value in allowed:
            result[field] = value
    settings = data.get('shiritori_settings')
    if isinstance(settings, dict):
        clean = {}
        for key, allowed in (('mode', ('battle', 'solo')), ('total', (12, 24, 36, 48)),
                             ('difficulty', ('easy', 'normal', 'hard'))):
            value = settings.get(key)
            if type(value) is type(allowed[0]) and value in allowed:
                clean[key] = value
        if clean:
            style = settings.get('rival_style')
            clean['rival_style'] = style if type(style) is str and style in ('chain', 'speed', 'counter') else 'chain'
            result['shiritori_settings'] = clean
    return result


def encode(app):
    data = {"version": 1,
        "best_times": [list(k) + [v] for k, v in app.best_times.items()],
        "battle_records": [list(k) + [v] for k, v in app.battle_records.items()],
        "bonus_bank": app.bonus_bank, "bgm_on": app.bgm_on,
        "sfx_on": app.sfx_on, "reduced_motion": app.reduced_motion}
    if not getattr(app, "audio_available", True):
        # Changing modes/saving a score in a silent session must not save the
        # temporary forced-OFF flags over the user's actual sound preferences.
        for field in ("bgm_on", "sfx_on"):
            data[field] = getattr(app, "audio_preferences", {}).get(field, data[field])
    for field in ("selected_max_number", "selected_mode", "play_kind", "difficulty"):
        if hasattr(app, field):
            data[field] = getattr(app, field)
    if hasattr(app, 'shiritori'):
        data['shiritori_settings'] = {key: getattr(app.shiritori, key) for key in ('mode', 'total', 'difficulty')}
        data['shiritori_settings']['rival_style'] = getattr(app.shiritori, 'rival_style', 'chain')
    elif hasattr(app, 'shiritori_settings'):
        data['shiritori_settings'] = app.shiritori_settings
    return json.dumps(data, allow_nan=False)


def _read_envelope(raw):
    """Reject data we cannot safely merge instead of overwriting it."""
    if raw is None:
        return {}
    # Pyodide 314 represents JavaScript null with a distinct singleton;
    # older runtimes and Python tests may use None instead.
    try:
        from pyodide.ffi import jsnull
    except ImportError:
        jsnull = None
    if raw is jsnull:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('unsupported progress format')
    for field in ('best_times', 'battle_records'):
        if field in data and not isinstance(data[field], list):
            raise ValueError('unsupported record format')
        # decode intentionally limits itself to 100 entries. Do not save a
        # partial view over a larger legacy/future collection.
        if len(data.get(field, [])) > 100:
            raise ValueError('too many records to merge safely')
    if 'shiritori_settings' in data and not isinstance(data['shiritori_settings'], dict):
        raise ValueError('unsupported settings format')
    if 'bonus_bank' in data and (type(data['bonus_bank']) is not int or not 0 <= data['bonus_bank'] <= 10**12):
        raise ValueError('unsupported bonus format')
    return data


def _unrecognized_records(data, field):
    """Retain v1 records whose shape or options are unknown to this version."""
    unknown = []
    for entry in data.get(field, []):
        sample = json.dumps({'version': 1, field: [entry]})
        if not decode(sample)[field]:
            unknown.append(entry)
    return unknown


def _setting_baseline(state):
    settings = {key: state.get(key, default) for key, default in _SETTING_DEFAULTS.items()}
    settings['shiritori_settings'] = {
        'mode': 'solo', 'total': 24, 'difficulty': settings['difficulty'], 'rival_style': 'chain',
        **state.get('shiritori_settings', {}),
    }
    return settings


def load():
    try:
        from js import localStorage
        state = decode(localStorage.getItem(KEY))
    except Exception:
        state = decode(None)
    # Even if loading failed, the current session starts at its decoded
    # balance. Subsequent bonus increases are attributable to this session;
    # save still refuses to overwrite unreadable or unsupported data.
    state['_progress_base_bonus'] = state['bonus_bank']
    state['_progress_base_times'] = dict(state['best_times'])
    state['_progress_base_battles'] = dict(state['battle_records'])
    state['_progress_base_settings'] = _setting_baseline(state)
    state['_progress_shiritori_owned'] = 'shiritori_settings' in state
    return state


def save(app):
    try:
        encoded = encode(app)
        own = decode(encoded)
        data = json.loads(encoded)
        local_settings = {key: data[key] for key in _SETTING_DEFAULTS if key in data}
        if 'shiritori_settings' in data:
            local_settings['shiritori_settings'] = dict(data['shiritori_settings'])
        base_settings = getattr(app, '_progress_base_settings', {})
        has_previous_attempt = hasattr(app, '_progress_attempt_settings')
        previous_attempt = getattr(app, '_progress_attempt_settings', base_settings)
        dirty = set(getattr(app, '_progress_dirty_settings', ()))
        for key, value in local_settings.items():
            if key == 'shiritori_settings':
                continue
            if value != base_settings.get(key) or value != previous_attempt.get(key, base_settings.get(key)):
                dirty.add(key)
        base_shiritori = dict(base_settings.get('shiritori_settings', {}))
        previous_shiritori = dict(previous_attempt.get('shiritori_settings', base_shiritori))
        local_shiritori = local_settings.get('shiritori_settings')
        if local_shiritori is not None:
            # The first view inherits number difficulty, even if the prior
            # number-setting save failed; it is not itself a user change.
            if ('difficulty' in local_settings and not getattr(app, '_progress_shiritori_owned', False)
                    and local_shiritori.get('difficulty') == local_settings.get('difficulty')):
                base_shiritori['difficulty'] = local_settings['difficulty']
                if not has_previous_attempt or 'shiritori_settings' not in previous_attempt:
                    previous_shiritori['difficulty'] = local_settings['difficulty']
            for key, value in local_shiritori.items():
                if value != base_shiritori.get(key) or value != previous_shiritori.get(key, base_shiritori.get(key)):
                    dirty.add(('shiritori_settings', key))
        # Keep pending changes through both read and write failures; clear
        # them only after localStorage confirms a successful write.
        app._progress_dirty_settings = dirty
        # Record this attempt even if storage read/write later fails. A user
        # can explicitly change a setting back to its original value before
        # retrying; comparing only successful saves would miss that change.
        app._progress_attempt_settings = local_settings
        from js import localStorage
        raw = localStorage.getItem(KEY)
        existing = _read_envelope(raw)
        current = decode(raw)
        for key in _SETTING_DEFAULTS:
            if key in data and key in existing and key not in dirty:
                data[key] = existing[key]

        for field, better in (('best_times', min), ('battle_records', max)):
            combined = dict(current[field])
            for key, value in own[field].items():
                combined[key] = better(combined[key], value) if key in combined else value
            data[field] = [list(key) + [value] for key, value in combined.items()]
            data[field].extend(_unrecognized_records(existing, field))
            # Never create data that a later save would refuse to merge.
            if len(data[field]) > 100:
                return False

        base = getattr(app, '_progress_base_bonus', None)
        if type(base) is int and 0 <= base <= app.bonus_bank and current['bonus_bank'] >= base:
            bonus = current['bonus_bank'] + (app.bonus_bank - base)
        else:
            # When an initial read failed, the missing baseline prevents safe
            # attribution of earned increments. Never invent or erase bonus.
            bonus = max(current['bonus_bank'], app.bonus_bank)
        if not 0 <= bonus <= 10**12:
            return False
        data['bonus_bank'] = bonus
        if isinstance(data.get('shiritori_settings'), dict):
            old_settings = existing.get('shiritori_settings', {})
            merged_settings = dict(old_settings)
            for key, value in data['shiritori_settings'].items():
                if key not in old_settings or ('shiritori_settings', key) in dirty:
                    merged_settings[key] = value
            data['shiritori_settings'] = merged_settings
        payload = json.dumps({**existing, **data}, allow_nan=False)
        localStorage.setItem(KEY, payload)

        # Update the live session only after a successful write. This keeps a
        # failed retry from adding the same earned bonus a second time.
        saved = decode(payload)
        round_ = getattr(app, 'round', None)
        if getattr(app, 'is_new_best', False) and round_ is not None:
            count = getattr(round_, 'max_number', None)
            mode = getattr(app, 'selected_mode', None)
            if getattr(app, 'play_kind', None) == 'battle':
                field, baseline, key = ('battle_records', getattr(app, '_progress_base_battles', {}),
                                        (count, mode, getattr(app, 'difficulty', None)))
                better_or_equal = lambda a, b: a >= b
            else:
                field, baseline, key = 'best_times', getattr(app, '_progress_base_times', {}), (count, mode)
                better_or_equal = lambda a, b: a <= b
            latest, submitted = current[field].get(key), own[field].get(key)
            # A newly arrived record may already beat this round. Do not
            # erase the session's own prior successful new-record indicator.
            if (latest is not None and submitted is not None and latest != baseline.get(key)
                    and better_or_equal(latest, submitted)):
                app.is_new_best = False
        app.best_times = saved['best_times']
        app.battle_records = saved['battle_records']
        app.bonus_bank = bonus
        app._progress_base_bonus = bonus
        app._progress_base_times = dict(saved['best_times'])
        app._progress_base_battles = dict(saved['battle_records'])
        # The app is not switched to another tab's current settings during
        # play. Compare against this tab's own values again on its next save.
        next_settings = {**base_settings, **local_settings}
        if 'shiritori_settings' not in local_settings and not getattr(app, '_progress_shiritori_owned', False):
            # The first picture-game view inherits this tab's current number
            # difficulty. Merely opening it is not an explicit change.
            next_settings['shiritori_settings'] = {
                **base_settings.get('shiritori_settings', {}),
                'difficulty': local_settings.get('difficulty', _SETTING_DEFAULTS['difficulty']),
            }
        app._progress_base_settings = next_settings
        if 'shiritori_settings' in local_settings:
            app._progress_shiritori_owned = True
        app._progress_dirty_settings = set()
        return True
    except Exception:
        return False
