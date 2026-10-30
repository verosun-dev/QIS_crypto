"""Trailing basis median and momentum, excluding the current point from history."""
from collections import deque
from bisect import bisect_left, insort


class Features:
    def __init__(self, window_ms, step_ms=1000):
        self.window = window_ms
        self.step = step_ms
        self.history = deque()
        self.sorted_basis = []

    def update(self, t, spot_mid, perp_mid):
        b = 10000 * (float(perp_mid)/float(spot_mid)-1)
        while self.history and self.history[0][0] < t-self.window:
            _, old = self.history.popleft()
            self.sorted_basis.pop(bisect_left(self.sorted_basis, old))
        n = len(self.sorted_basis)
        complete = n == self.window // self.step and self.history[0][0] == t-self.window if n else False
        median = ((self.sorted_basis[(n-1)//2]+self.sorted_basis[n//2])/2) if complete else None
        lag = next((v for ts,v in reversed(self.history) if ts <= t-60000), None)
        result = {"ts":t, "spot_mid":str(spot_mid), "perp_mid":str(perp_mid), "basis_bps":b,
                  "excess_bps":None if median is None else b-median,
                  "momentum_60s_bps":None if lag is None else b-lag, "warm":complete}
        self.history.append((t,b)); insort(self.sorted_basis,b)
        return result
