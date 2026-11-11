import unittest
from decimal import Decimal as D
from qis_spot_perp.data.orderbook import Book
from tests.fixtures.market import event


class OrderBookTests(unittest.TestCase):
    def test_book_absolute_delete_and_gap_recovery(self):
        b=Book();b.apply(event(0,size='2'))
        b.apply(event(1,size='3',action='update',seq=8,prev=1))
        self.assertEqual(b.bids[D(100)],3)
        b.apply(dict(ts='2',bids=[['100','0']],asks=[],action='update',seqId=9,prevSeqId=8))
        self.assertFalse(b.bids)
        self.assertEqual(b.apply(event(3,action='update',seq=11,prev=10)),'sequence_gap')
        self.assertFalse(b.valid)
        b.apply(event(4));self.assertTrue(b.valid)

    def test_heartbeat_duplicate_and_reset(self):
        b=Book();snap=event(0);b.apply(snap)
        self.assertEqual(b.apply(snap),'duplicate')
        b.apply(dict(ts='1',bids=[],asks=[],action='update',seqId=1,prevSeqId=1))
        b.apply(event(2,action='update',seq=0,prev=1))
        self.assertTrue(b.valid);self.assertEqual(b.seq,0)

    def test_missing_sequence_not_verified(self):
        e=event(0);e.pop('seqId');e.pop('prevSeqId')
        b=Book();b.apply(e);self.assertFalse(b.valid)
        b=Book(allow_unsequenced=True);b.apply(e)
        self.assertTrue(b.valid);self.assertFalse(b.sequence_verified)

    def test_out_of_order_message_invalidates_until_snapshot(self):
        b=Book();b.apply(event(10,seq=20))
        self.assertEqual(b.apply(event(9,action='update',seq=21,prev=20)),'out_of_order')
        self.assertFalse(b.valid)
        self.assertEqual(b.apply(event(11,action='update',seq=21,prev=20)),'awaiting_snapshot')
        self.assertEqual(b.apply(event(12,seq=50)),'ok')
        self.assertTrue(b.valid)
        self.assertEqual(b.seq,50)

    def test_healthy_checks_staleness_and_age_boundaries(self):
        b=Book();b.apply(event(100))
        self.assertTrue(b.healthy(100,50))
        self.assertTrue(b.healthy(150,50))
        self.assertFalse(b.healthy(151,50))
        self.assertFalse(b.healthy(99,50))
        self.assertEqual(b.apply(dict(ts='151',bids=[],asks=[],action='update',
                                      seqId=1,prevSeqId=1)),'ok')
        self.assertTrue(b.healthy(151,0))

    def test_healthy_is_false_for_empty_or_crossed_books(self):
        empty=Book()
        empty.apply(dict(ts='0',bids=[],asks=[['101','1']],action='snapshot',
                         seqId=1,prevSeqId=-1))
        self.assertIs(empty.healthy(0,100),False)
        crossed=Book();crossed.apply(event(0,bid='102',ask='101'))
        self.assertIs(crossed.healthy(0,100),False)
