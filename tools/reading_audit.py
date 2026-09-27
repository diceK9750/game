"""Read-only catalog graph and random-card chain comparison.

Usage: .venv/Scripts/python.exe -B tools/reading_audit.py \
       --baseline-dir PATH --step25-dir PATH --seeds 800
Both baselines are external pre-edit copies. No repository history is rewritten
and no diagnostic file is written into the game tree.
"""
import argparse
import importlib.util
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shiritori as current


def load_baseline(directory):
    spec = importlib.util.spec_from_file_location('shiritori_baseline', Path(directory) / 'shiritori.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def graph_report(module):
    graph = current.reading_connections(module.CARDS)
    common = [(identity, word, count) for (identity, word), count in graph.items()
              if word not in current.SPECIAL_READINGS]
    heads = {identity: {current.head(word) for word in words if current.tail(word) != 'ん'}
             for identity, _, words in module.CARDS}
    weak = [{'card': identity, 'reading': word,
             'normalized': current.normalize_reading(word), 'tail': current.tail(word),
             'candidates': [other for other, sounds in heads.items()
                            if other != identity and current.tail(word) in sounds],
             'count': count}
            for identity, word, count in common if count <= 1]
    return {
        'cards': len(module.CARDS),
        'readings': sum(len(card[2]) for card in module.CARDS),
        'common': sum(word not in current.SPECIAL_READINGS for card in module.CARDS for word in card[2]),
        'special': sum(word in current.SPECIAL_READINGS for card in module.CARDS for word in card[2]),
        'common_dead': [(i, w) for i, w, n in common if n == 0],
        'common_one': [(i, w) for i, w, n in common if n == 1],
        'common_two_plus': sum(n >= 2 for _, _, n in common),
        'weak_common': weak,
    }


def sample(module, total, mode, seed, improved):
    game = module.ShiritoriRound(total=total, mode=mode, rng=random.Random(seed), clock=lambda: 0)
    game.start()
    card_rng = random.Random(seed ^ 0x5A17)
    cards, stock = tuple(game.cards), tuple(game.stock)
    required, seen = game.required, frozenset(game.seen)
    consumed = 0
    while consumed < total:
        moves = module.chain_moves(cards, required, seen)
        if not moves:
            break
        index = card_rng.choice(sorted({index for index, _ in moves}))
        if improved:
            game.cards, game.stock, game.required, game.seen = list(cards), list(stock), required, set(seen)
            game.used = {}
            move = game.choose_move_for_card(index)
        else:
            move = next(move for move in moves if move[0] == index)
        cards, stock, required, seen = module.chain_step(cards, stock, seen, move)
        consumed += 1
    return consumed


def simulation(module, improved, seeds):
    results = {}
    for total in (12, 24, 36, 48):
        for mode in ('solo', 'battle'):
            counts = [sample(module, total, mode, seed, improved) for seed in range(seeds)]
            results[f'{total}-{mode}'] = {
                'seeds': seeds,
                'full_clear_pct': round(100 * sum(n == total for n in counts) / seeds, 1),
                'average_consumed': round(sum(counts) / seeds, 2),
                'early_dead_pct': round(100 * sum(n < total / 2 for n in counts) / seeds, 1),
                'reading_shortage_pct': round(100 * sum(n < total for n in counts) / seeds, 1),
            }
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline-dir', type=Path)
    parser.add_argument('--step25-dir', type=Path)
    parser.add_argument('--seeds', type=int, default=100)
    args = parser.parse_args()
    report = {'current_graph': graph_report(current)}
    if args.baseline_dir:
        baseline = load_baseline(args.baseline_dir)
        report['baseline_graph'] = graph_report(baseline)
        report['baseline_random'] = simulation(baseline, False, args.seeds)
    if args.step25_dir:
        step25 = load_baseline(args.step25_dir)
        report['step25_graph'] = graph_report(step25)
        report['step25_random'] = simulation(step25, True, args.seeds)
    if args.baseline_dir or args.step25_dir:
        report['current_random'] = simulation(current, True, args.seeds)
        report['comparison_note'] = ('Same seeds and random-card policy; catalog changes may alter initial board '
                                     'composition. Battle label tests shared chain/refill rules, not CPU timing.')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
