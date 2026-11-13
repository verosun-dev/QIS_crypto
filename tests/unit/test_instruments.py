import json
import unittest
from decimal import Decimal as D
from pathlib import Path

from qis_spot_perp.core.instruments import matched_units


class InstrumentSizingTests(unittest.TestCase):
    def setUp(self):
        self.spot = dict(baseCcy='BTC', quoteCcy='USDT',
                         minSz='.00001', lotSz='.00000001')
        self.perp = dict(ctType='linear', ctValCcy='BTC', settleCcy='USDT',
                         ctVal='.01', ctMult='1', minSz='.01', lotSz='.01')

    def test_saved_retrieval_time_metadata_matches_btc_exposure(self):
        root = Path(__file__).resolve().parents[2]
        spot = json.loads((root/'data/manifests/okx-spot-spec.json').read_text())['data'][0]
        perp = json.loads((root/'data/manifests/okx-swap-spec.json').read_text())['data'][0]
        # These saved responses do not establish historical effective-date equivalence.
        for quantity, contracts in (('.01', '1'), ('.0001', '.01'), ('.0003', '.03')):
            with self.subTest(quantity=quantity):
                actual = matched_units(quantity, spot, perp)
                self.assertEqual(actual, (D(quantity), D(contracts)))
                self.assertIsInstance(actual[0], D)
                self.assertIsInstance(actual[1], D)

    def test_decimal_quantity_and_fractional_contracts_remain_exact(self):
        self.assertEqual(matched_units('.01010000', self.spot, self.perp),
                         (D('.01010000'), D('1.01')))

    def test_nonunit_face_value_and_multiplier(self):
        self.perp.update(ctVal='.02', ctMult='2.5')
        self.assertEqual(matched_units('.125', self.spot, self.perp),
                         (D('.125'), D('2.5')))

    def test_empty_or_missing_multiplier_defaults_to_one(self):
        empty = dict(self.perp, ctMult='')
        missing = dict(self.perp)
        del missing['ctMult']
        for spec in (empty, missing):
            with self.subTest(spec=spec):
                self.assertEqual(matched_units('.01', self.spot, spec),
                                 (D('.01'), D(1)))

    def test_spot_minimum_is_checked_independently(self):
        self.spot['minSz'] = '.0002'
        with self.assertRaises(ValueError):
            matched_units('.0001', self.spot, self.perp)
        for quantity, contracts in (('.0002', '.02'), ('.0003', '.03')):
            with self.subTest(quantity=quantity):
                self.assertEqual(matched_units(quantity, self.spot, self.perp),
                                 (D(quantity), D(contracts)))

    def test_perpetual_minimum_is_checked_in_contracts(self):
        self.perp['minSz'] = '.02'
        with self.assertRaises(ValueError):
            matched_units('.0001', self.spot, self.perp)
        for quantity, contracts in (('.0002', '.02'), ('.0003', '.03')):
            with self.subTest(quantity=quantity):
                self.assertEqual(matched_units(quantity, self.spot, self.perp),
                                 (D(quantity), D(contracts)))

    def test_spot_lot_step_does_not_round_an_invalid_quantity(self):
        self.spot.update(minSz='.0002', lotSz='.0002')
        with self.assertRaises(ValueError):
            matched_units('.0003', self.spot, self.perp)
        self.assertEqual(matched_units('.0004', self.spot, self.perp),
                         (D('.0004'), D('.04')))

    def test_perpetual_lot_step_is_checked_in_contracts(self):
        self.perp.update(minSz='.02', lotSz='.02')
        with self.assertRaises(ValueError):
            matched_units('.0003', self.spot, self.perp)
        self.assertEqual(matched_units('.0004', self.spot, self.perp),
                         (D('.0004'), D('.04')))

    def test_zero_and_negative_quantities_are_below_minimum(self):
        for quantity in ('0', '-.01'):
            with self.subTest(quantity=quantity), self.assertRaises(ValueError):
                matched_units(quantity, self.spot, self.perp)

    def test_unsupported_exposure_and_settlement_are_rejected(self):
        for field, value in (('ctType', 'inverse'), ('ctValCcy', 'ETH'),
                             ('settleCcy', 'USD')):
            with self.subTest(field=field), self.assertRaises(ValueError):
                matched_units('.01', self.spot, dict(self.perp, **{field: value}))
