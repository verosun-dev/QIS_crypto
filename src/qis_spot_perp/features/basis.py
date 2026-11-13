"""Trailing basis median and momentum, excluding the current point from history.

Momentum requires an observation exactly 60 seconds earlier, independently of
the median window. A missing exact lag produces missing momentum.
"""
from collections import deque
from bisect import bisect_left, insort


class Features:
    def __init__(self, window_ms, step_ms=1000):
        self.window = window_ms
        self.step = step_ms
        self.history = deque()
        self.sorted_basis = []
        self.momentum_history = deque()

    def update(self, t, spot_mid, perp_mid):
        b = 10000 * (float(perp_mid)/float(spot_mid)-1)
        while self.history and self.history[0][0] < t-self.window:
            _, old = self.history.popleft()
            self.sorted_basis.pop(bisect_left(self.sorted_basis, old))
        n = len(self.sorted_basis)
        complete = n == self.window // self.step and self.history[0][0] == t-self.window if n else False
        median = ((self.sorted_basis[(n-1)//2]+self.sorted_basis[n//2])/2) if complete else None
        while self.momentum_history and self.momentum_history[0][0] < t-60000:
            self.momentum_history.popleft()
        lag = self.momentum_history[0][1] if self.momentum_history and self.momentum_history[0][0] == t-60000 else None
        result = {"ts":t, "spot_mid":str(spot_mid), "perp_mid":str(perp_mid), "basis_bps":b,
                  "excess_bps":None if median is None else b-median,
                  "momentum_60s_bps":None if lag is None else b-lag, "warm":complete}
        self.history.append((t,b)); insort(self.sorted_basis,b)
        self.momentum_history.append((t,b))
        return result
