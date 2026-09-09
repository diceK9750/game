import random
import unittest
from timed_chain import TimedChain
from shiritori import ShiritoriRound
from game_logic import NumberTapRound, BattleRound


class TimedChainTests(unittest.TestCase):
    def test_windows_boundary_bonus_and_tiers(self):
        chain = TimedChain()
        for n in range(1, 12):
            self.assertEqual(chain.hit('you', n * .1), n)
            self.assertAlmostEqual(chain.players['you']['window'], max(1.2, 4.5-.45*(n-1)))
        self.assertEqual(chain.snapshot(1.1)['you']['tier'], 3)
        self.assertEqual(chain.players['you']['bonus'], 5500)
        chain.hit('you', 2.3)
        self.assertEqual(chain.players['you']['count'], 1)
        self.assertEqual(chain.players['you']['best'], 11)

    def test_turn_wait_and_pause_are_not_play_time(self):
        c = TimedChain()
        c.hit('you', 0)
        c.sync(1, ('cpu',))
        c.sync(100, ())
        c.sync(200, ('you',))
        self.assertAlmostEqual(c.players['you']['remaining'], 3.5)
        c.hit('you', 201)
        self.assertEqual(c.players['you']['count'], 2)
        c.miss('you')
        self.assertEqual(c.players['you']['count'], 0)

    def test_numbers_all_ranges_and_orders_pause_and_reset(self):
        for total in (10,20,30,40):
            for mode in ('ordered','random'):
                now = [0.]
                g = NumberTapRound(max_number=total,clock=lambda:now[0])
                g.start(mode)
                g.tap(g.current_target)
                now[0] = 1
                g.pause()
                now[0] = 100
                g.resume()
                g.tap(g.current_target)
                self.assertEqual(g.chain.players['you']['count'], 2)
                g.tap(None)
                self.assertEqual(g.chain.players['you']['count'], 2)
                now[0] += 5
                g.tap(g.current_target)
                self.assertEqual(g.chain.players['you']['count'], 1)
                g.tap(-1)
                self.assertEqual(g.chain.players['you']['count'], 0)
                g.start(mode)
                self.assertEqual(g.chain.players['you']['best'], 0)

    def test_number_cpu_uses_same_rules_and_steals_break_chains(self):
        now = [0.]
        g = BattleRound(clock=lambda:now[0],difficulty='hard')
        g.start()
        g.tap(g.current_target)
        now[0]=g.cpu_at
        g.update_cpu()
        self.assertEqual(g.chain.players['you']['count'], 0)
        now[0]=g.cpu_at
        g.update_cpu()
        self.assertEqual(g.chain.players['cpu']['count'], 2)
        g.tap(g.current_target)
        self.assertEqual(g.chain.players['cpu']['count'], 0)
        self.assertEqual(g.player_points+g.cpu_points,g.completed_count)

    def test_shiritori_all_counts_modes_keep_routes_and_award_immediately(self):
        for total in (12,24,36,48):
            for mode in ('solo','battle'):
                now=[0.]
                g=ShiritoriRound(total=total,mode=mode,clock=lambda:now[0],rng=random.Random(7))
                g.start()
                for _ in range(total):
                    move=g.chain_advice()[0]
                    now[0]+=.1
                    g.take(*move)
                self.assertEqual(g.phase,'finished')
                self.assertEqual(g.chain.players['you']['best'],total if mode=='solo' else total//2)
                if mode=='battle':
                    self.assertEqual(g.chain.players['cpu']['best'],total//2)
                self.assertEqual(len(g.discoveries),total if mode=='solo' else total//2)

    def test_shiritori_real_cpu_turn_pause_and_wrong_input(self):
        now=[0.]
        g=ShiritoriRound(mode='battle',clock=lambda:now[0],rng=random.Random(7))
        g.start()
        for _ in range(3):
            now[0]+=.1
            g.command('card',g.chain_advice()[0][0])
            now[0]+=2.21
            g.update()
        self.assertEqual(g.chain.players['cpu']['count'],3)
        self.assertEqual(g.chain.players['you']['count'],3)
        g.command('pause')
        remaining=g.snapshot()['chain']['you']['remaining']
        now[0]+=100
        self.assertEqual(g.snapshot()['chain']['you']['remaining'],remaining)
        g.command('resume')
        legal={i for i,_ in g.moves()}
        wrong=next(i for i in range(len(g.cards)) if i not in g.used and i not in legal)
        g.command('card',wrong)
        self.assertEqual(g.chain.players['you']['count'],0)
        g.command('pause')
        g.command('restart')
        self.assertEqual(g.chain.players['cpu']['best'],0)
