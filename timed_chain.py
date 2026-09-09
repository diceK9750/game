"""Shared, clock-injected automatic chains. No rendering or win-score changes."""


class TimedChain:
    def __init__(self, now=0.0, active=('you',)):
        self.at = now
        self.active = tuple(active)
        self.players = {owner: dict(count=0, best=0, bonus=0, remaining=0.0,
                                   window=4.5, event=0) for owner in ('you', 'cpu')}

    @staticmethod
    def window(count):
        return max(1.2, 4.5 - .45 * (count - 1))

    def sync(self, now, active=None):
        dt = max(0.0, now - self.at)
        for owner in self.active:
            row = self.players[owner]
            row['remaining'] = max(0.0, row['remaining'] - dt)
            if row['remaining'] <= 1e-9:
                row['count'] = 0
                row['remaining'] = 0.0
        self.at = max(self.at, now)
        if active is not None:
            self.active = tuple(active)

    def miss(self, owner):
        self.players[owner]['count'] = 0
        self.players[owner]['remaining'] = 0.0

    def hit(self, owner, now, break_other=False):
        self.sync(now)
        if break_other:
            self.miss('cpu' if owner == 'you' else 'you')
        row = self.players[owner]
        row['count'] += 1
        row['event'] += 1
        row['best'] = max(row['best'], row['count'])
        row['window'] = row['remaining'] = self.window(row['count'])
        row['bonus'] += 100 * (row['count'] - 1)
        return row['count']

    def snapshot(self, now, active=None):
        self.sync(now, active)
        return {owner: {**row, 'remaining': round(row['remaining'], 2),
                        'tier': 3 if row['count'] >= 7 else 2 if row['count'] >= 4 else 1 if row['count'] >= 2 else 0,
                        'waiting': owner not in self.active}
                for owner, row in self.players.items()}

    def sound(self, owner):
        count = self.players[owner]['count']
        return 3 if count >= 7 else 2 if count >= 4 else 4 if count >= 2 else 5 if owner == 'cpu' else 0
