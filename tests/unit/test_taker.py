import unittest
from decimal import Decimal as D

from qis_spot_perp.data.orderbook import Book
from qis_spot_perp.execution.taker import sweep


def book(leg):
    sizes = ('2', '3') if leg == 'perp' else ('.02', '.03')
    result = Book('.01' if leg == 'perp' else '1')
    result.apply(dict(
        ts='0', action='snapshot', seqId=1, prevSeqId=-1,
        bids=[['98', sizes[1]], ['99', sizes[0]]],
        asks=[['102', sizes[1]], ['101', sizes[0]]],
    ))
    return result


class TakerTests(unittest.TestCase):
    directions = (('spot', 'buy'), ('spot', 'sell'),
                  ('perp', 'sell'), ('perp', 'buy'))

    def test_four_directions_consume_best_prices_in_btc(self):
        for leg, side in self.directions:
            with self.subTest(leg=leg, side=side):
                b = book(leg)
                opposite = dict(b.bids if side == 'buy' else b.asks)
                best, next_price = (D(101), D(102)) if side == 'buy' else (D(99), D(98))
                fills, remaining = sweep(b, side, '.04')
                self.assertEqual(fills, [(best, D('.02')), (next_price, D('.02'))])
                self.assertEqual(remaining, 0)
                self.assertEqual(sum(q for _, q in fills) + remaining, D('.04'))
                self.assertEqual(b.asks if side == 'buy' else b.bids, {next_price: D('.01')})
                self.assertEqual(b.bids if side == 'buy' else b.asks, opposite)
                for price, quantity in fills:
                    self.assertIsInstance(price, D)
                    self.assertIsInstance(quantity, D)
                self.assertIsInstance(remaining, D)

    def test_small_exact_and_insufficient_depth(self):
        cases = (
            ('.01', ('.01',), '0', ('.01', '.03')),
            ('.05', ('.02', '.03'), '0', ('0', '0')),
            ('.06', ('.02', '.03'), '.01', ('0', '0')),
        )
        for leg, side in self.directions:
            for quantity, sizes, unfilled, residual in cases:
                with self.subTest(leg=leg, side=side, quantity=quantity):
                    b = book(leg)
                    opposite = dict(b.bids if side == 'buy' else b.asks)
                    prices = (D(101), D(102)) if side == 'buy' else (D(99), D(98))
                    fills, remaining = sweep(b, side, quantity)
                    self.assertEqual(fills, list(zip(prices, map(D, sizes))))
                    self.assertEqual(remaining, D(unfilled))
                    self.assertEqual(sum(q for _, q in fills) + remaining, D(quantity))
                    expected = {p: D(q) for p, q in zip(prices, residual) if D(q)}
                    self.assertEqual(b.asks if side == 'buy' else b.bids, expected)
                    self.assertEqual(b.bids if side == 'buy' else b.asks, opposite)

    def test_repeated_orders_cannot_reuse_consumed_depth(self):
        for leg, side in self.directions:
            with self.subTest(leg=leg, side=side):
                b = book(leg)
                next_price = D(102) if side == 'buy' else D(98)
                first, first_remaining = sweep(b, side, '.03')
                second, second_remaining = sweep(b, side, '.03')
                self.assertEqual(first_remaining, 0)
                self.assertEqual(sum(q for _, q in first), D('.03'))
                self.assertEqual(second, [(next_price, D('.02'))])
                self.assertEqual(second_remaining, D('.01'))
                self.assertEqual(b.asks if side == 'buy' else b.bids, {})
                self.assertEqual(sum(q for _, q in first + second), D('.05'))

    def test_empty_requested_side_leaves_order_unfilled(self):
        for leg, side in self.directions:
            with self.subTest(leg=leg, side=side):
                b = book(leg)
                (b.asks if side == 'buy' else b.bids).clear()
                opposite = dict(b.bids if side == 'buy' else b.asks)
                fills, remaining = sweep(b, side, '.01')
                self.assertEqual(fills, [])
                self.assertEqual(remaining, D('.01'))
                self.assertEqual(b.bids if side == 'buy' else b.asks, opposite)
