#!/usr/bin/env python
#    test_multisigtransaction.py
#    Copyright (C) 2015 by CJP
#
#    This file is part of Amiko Pay.
#
#    Amiko Pay is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Amiko Pay is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.
#
#    Additional permission under GNU GPL version 3 section 7
#
#    If you modify this Program, or any covered work, by linking or combining it
#    with the OpenSSL library (or a modified version of that library),
#    containing parts covered by the terms of the OpenSSL License and the SSLeay
#    License, the licensors of this Program grant you additional permission to
#    convey the resulting work. Corresponding Source for a non-source form of
#    such a combination shall include the source code for the parts of the
#    OpenSSL library used as well as that of the covered work.

import unittest
import binascii

import testenvironment

from amiko.utils.bitcointransaction import OP
from amiko.utils import crypto

from amiko.channels import tcd
from amiko.channels import multisigtransaction



class Test(unittest.TestCase):

	def test_constructor(self):
		"Test the MultiSigTransaction constructor"

		tx = multisigtransaction.MultiSigTransaction("tx", ["a", "b"])
		self.assertEqual(tx.transaction, "tx")
		self.assertEqual(tx.TCDlist, ["a", "b"])


	def test_makeNew(self):
		"Test the makeNew method"

		ownKey = crypto.Key()
		ownKey.makeNewKey(compressed=True)
		ownKeyHash = crypto.RIPEMD160(crypto.SHA256(ownKey.getPublicKey()))

		tx = multisigtransaction.MultiSigTransaction.makeNew(
			ownKey, "depositTxID", 2000, 10, 1234)

		self.assertEqual(tx.TCDlist, [])
		tx = tx.transaction

		self.assertEqual(len(tx.tx_in), 1)
		self.assertEqual(len(tx.tx_out), 1)
		tx_in = tx.tx_in[0]
		tx_out = tx.tx_out[0]

		self.assertEqual(tx_in.previousOutputHash, "depositTxID")
		self.assertEqual(tx_in.previousOutputIndex, 0)
		self.assertEqual(tx_in.scriptSig.elements, tuple())

		self.assertEqual(tx_out.amount, 1990)
		self.assertEqual(tx_out.scriptPubKey.elements,
			(OP.DUP, OP.HASH160, ownKeyHash, OP.EQUALVERIFY, OP.CHECKSIG))


	def test_state(self):
		"Test state loading and saving"

		ownKey = crypto.Key()
		ownKey.makeNewKey(compressed=True)
		tx1 = multisigtransaction.MultiSigTransaction.makeNew(
			ownKey, "x"*32, 2000, 10, 1234)

		state = tx1.getState(forDisplay=True)
		self.assertEqual(state,
			{"ID": tx1.transaction.getTransactionID()[::-1].encode("hex")})

		state = tx1.getState(forDisplay=False)

		tx2 = multisigtransaction.MultiSigTransaction.makeFromState(state)

		self.assertEqual(
			tx1.transaction.serialize(),
			tx2.transaction.serialize()
			)
		self.assertEqual(
			tcd.serializeList(tx1.TCDlist),
			tcd.serializeList(tx2.TCDlist)
			)


	def test_serialization(self):
		"Test serialization and deserialization"

		ownKey = crypto.Key()
		ownKey.makeNewKey(compressed=True)
		tx1 = multisigtransaction.MultiSigTransaction.makeNew(
			ownKey, "x"*32, 2000, 10, 1234)

		data = tx1.serialize()

		tx2 = multisigtransaction.MultiSigTransaction.deserialize(data)

		self.assertEqual(
			tx1.transaction.serialize(),
			tx2.transaction.serialize()
			)
		self.assertEqual(
			tcd.serializeList(tx1.TCDlist),
			tcd.serializeList(tx2.TCDlist)
			)


	def test_TCDExists(self):
		"Test TCDExists method"

		tx = multisigtransaction.MultiSigTransaction("tx",
			[
			tcd.TCD(0, 0, 0, "foo", "", ""),
			tcd.TCD(0, 0, 0, "bar", "", "")
			])
		self.assertTrue(tx.TCDExists("foo"))
		self.assertTrue(tx.TCDExists("bar"))
		self.assertFalse(tx.TCDExists("foobar"))


	def test_addTCD(self):
		"Test addTCD method"

		TCD1 = tcd.TCD(0, 0, 0, "foo", "", "")
		TCD2 = tcd.TCD(0, 0, 0, "bar", "", "")
		TCD3 = tcd.TCD(0, 0, 0, "foobar", "", "")

		tx = multisigtransaction.MultiSigTransaction("tx", [TCD1, TCD2])
		tx.addTCD(TCD3)
		self.assertEqual(tx.TCDlist, [TCD1, TCD2, TCD3])

		TCD4 = tcd.TCD(1, 1, 1, "foobar", "x", "y") #same hash as TCD3
		self.assertRaises(Exception, tx.addTCD, TCD4)
		self.assertEqual(tx.TCDlist, [TCD1, TCD2, TCD3]) #it's not added


	def test_removeTCD(self):
		"Test removeTCD method"

		TCD1 = tcd.TCD(0, 0, 0, "foo", "", "")
		TCD2 = tcd.TCD(0, 0, 0, "bar", "", "")
		TCD3 = tcd.TCD(0, 0, 0, "foobar", "", "")

		tx = multisigtransaction.MultiSigTransaction("tx", [TCD1, TCD2, TCD3])

		tx.removeTCD("bar")
		self.assertEqual(tx.TCDlist, [TCD1, TCD3])

		self.assertRaises(Exception, tx.removeTCD, "bar") #it doesn't exist anymore
		self.assertEqual(tx.TCDlist, [TCD1, TCD3]) #no effect


	def test_setOutputs(self):
		"Test setOutputs method"

		ownKey = crypto.Key()
		ownKey.makeNewKey(compressed=True)
		txn = multisigtransaction.MultiSigTransaction.makeNew(
			ownKey, "x"*32, 2000, 10, 1234)

		txn.TCDlist = [
			tcd.TCD(1, 2, 3, 'a'*20, 'b'*20, 'c'*20),
			tcd.TCD(4, 5, 6, 'd'*20, 'e'*20, 'f'*20)
			]

		txn.setOutputs(
			"ownPubKey", "peerPubKey", "escrowPubKey",
			1234, 5678)

		tx = txn.transaction
		self.assertEqual(len(tx.tx_in), 1)
		self.assertEqual(len(tx.tx_out), 3) #TODO: 4

		tx_in = tx.tx_in[0]
		self.assertEqual(tx_in.previousOutputHash, "x"*32)
		self.assertEqual(tx_in.previousOutputIndex, 0)
		self.assertEqual(tx_in.scriptSig.elements, tuple())

		def testOwnOutput(tx_out):
			self.assertEqual(tx_out[0].amount, 1234)
			self.assertEqual(tx_out[0].scriptPubKey.elements,
				(OP.DUP, OP.HASH160, crypto.RIPEMD160(crypto.SHA256("ownPubKey")), OP.EQUALVERIFY, OP.CHECKSIG))
		def testPeerOutput(tx_out):
			self.assertEqual(tx_out[1].amount, 5678)
			self.assertEqual(tx_out[1].scriptPubKey.elements,
				(OP.DUP, OP.HASH160, crypto.RIPEMD160(crypto.SHA256("peerPubKey")), OP.EQUALVERIFY, OP.CHECKSIG))
		def testLockOutput(tx_out):
			self.assertEqual(tx_out[2].amount, 9)
			self.assertEqual(tx_out[2].scriptPubKey.elements,
				[OP.TWO, "ownPubKey", "peerPubKey", "escrowPubKey", OP.TWO+1, OP.CHECKMULTISIG])

		tx_out = tx.tx_out
		testOwnOutput(tx_out)
		testPeerOutput(tx_out)
		testLockOutput(tx_out)


		txn.TCDlist = []
		txn.setOutputs(
			"ownPubKey", "peerPubKey", "escrowPubKey",
			1234, 5678)
		tx = txn.transaction
		self.assertEqual(len(tx.tx_out), 2)
		tx_out = tx.tx_out
		testOwnOutput(tx_out)
		testPeerOutput(tx_out)

		txn.setOutputs(
			"ownPubKey", "peerPubKey", "escrowPubKey",
			1234, 0)
		tx = txn.transaction
		self.assertEqual(len(tx.tx_out), 1)
		tx_out = tx.tx_out
		testOwnOutput(tx_out)

		txn.setOutputs(
			"ownPubKey", "peerPubKey", "escrowPubKey",
			0, 0)
		tx = txn.transaction
		self.assertEqual(len(tx.tx_out), 0)



if __name__ == "__main__":
	unittest.main(verbosity=2)

