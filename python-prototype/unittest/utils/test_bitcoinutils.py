#!/usr/bin/env python
#    test_bitcoinutils.py
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
import sys
sys.path.append('../..')
sys.path.append('..')

import testenvironment
import dummy_interfaces

from amiko.utils import bitcointransaction
from amiko.utils.bitcointransaction import OP
from amiko.utils import crypto

from amiko.utils import bitcoinutils



class DummyTransaction:
	def __init__(self):
		self.instances = []


	def __enter__(self):
		self.oldTransaction = bitcoinutils.Transaction
		self.oldTxIn = bitcoinutils.TxIn
		self.oldTxOut = bitcoinutils.TxOut
		bitcoinutils.Transaction = self
		bitcoinutils.TxIn = self
		bitcoinutils.TxOut = self
		return self


	def __exit__(self, exc_type, exc_val, exc_tb):
		bitcoinutils.Transaction = self.oldTransaction
		bitcoinutils.TxIn = self.oldTxIn
		bitcoinutils.TxOut = self.oldTxOut


	def __call__(self, *args, **kwargs):
		tx = dummy_interfaces.Tracer()
		tx.trace.append(("__init__", args, kwargs))
		self.instances.append(tx)
		return tx



class Test(unittest.TestCase):
	def setUp(self):
		self.bitcoind = dummy_interfaces.DummyBitcoind()


	def test_getInputsForAmount(self):
		"Test the getInputsForAmount function"

		total, inputs = bitcoinutils.getInputsForAmount(self.bitcoind, 45)
		self.assertEqual(total, 50)
		self.assertEqual(inputs,
			[
				("foobar_tx", 1, "foobar_pub", "foobar")
			])

		total, inputs = bitcoinutils.getInputsForAmount(self.bitcoind, 55)
		self.assertEqual(total, 70)
		self.assertEqual(inputs,
			[
				("foobar_tx", 1, "foobar_pub", "foobar"),
				("bar_tx"   , 2, "bar_pub"   , "bar"   )
			])

		self.assertRaises(Exception, bitcoinutils.getInputsForAmount,
			self.bitcoind, 95)


	def test_sendToStandardPubKey(self):
		"Test the sendToStandardPubKey function"

		with DummyTransaction():
			tx = bitcoinutils.sendToStandardPubKey(
				self.bitcoind, 40, "toHash", "changeHash", 3)

			self.assertEqual(len(tx.trace), 2)

			#Constructor, with tx_in and tx_out:
			self.assertEqual(tx.trace[0][0], "__init__")
			self.assertEqual(tx.trace[0][1], tuple())
			self.assertEqual(len(tx.trace[0][2]), 2)
			self.assertEqual(len(tx.trace[0][2]["tx_in"]), 1)
			self.assertEqual(len(tx.trace[0][2]["tx_out"]), 2)

			tx_in = tx.trace[0][2]["tx_in"][0]
			self.assertEqual(tx_in.trace,
				[('__init__', ('foobar_tx', 1), {})])

			for i, destHash, amount in ((0, "toHash", 40), (1, "changeHash", 7)):
				tx_out = tx.trace[0][2]["tx_out"][i]
				self.assertEqual(len(tx_out.trace), 1)
				self.assertEqual(tx_out.trace[0][0], "__init__")
				self.assertEqual(len(tx_out.trace[0][1]), 2)
				self.assertEqual(tx_out.trace[0][1][0], amount)
				script = tx_out.trace[0][1][1]
				self.assertEqual(script.elements,
					(OP.DUP, OP.HASH160, destHash, OP.EQUALVERIFY, OP.CHECKSIG))

			#Transaction signing:
			self.assertEqual(tx.trace[1][0], "signInput")
			self.assertEqual(len(tx.trace[1][1]), 4)
			self.assertEqual(tx.trace[1][1][0], 0)
			scriptPubKey = tx.trace[1][1][1]
			self.assertEqual(scriptPubKey.serialize(), "foobar_pub")

			key = crypto.Key()
			key.setPrivateKey("foobar")
			self.assertEqual(tx.trace[1][1][2], [None, key.getPublicKey()])
			self.assertEqual(len(tx.trace[1][1][3]), 1)
			self.assertEqual(tx.trace[1][1][3][0].getPrivateKey(), key.getPrivateKey())


	def test_sendToMultiSigPubKey(self):
		"Test the sendToMultiSigPubKey function"

		with DummyTransaction():
			tx = bitcoinutils.sendToMultiSigPubKey(
				self.bitcoind, 40, "toPK1", "toPK2", "changeHash", 3)

			self.assertEqual(len(tx.trace), 2)

			#Constructor, with tx_in and tx_out:
			self.assertEqual(tx.trace[0][0], "__init__")
			self.assertEqual(tx.trace[0][1], tuple())
			self.assertEqual(len(tx.trace[0][2]), 2)
			self.assertEqual(len(tx.trace[0][2]["tx_in"]), 1)
			self.assertEqual(len(tx.trace[0][2]["tx_out"]), 2)

			tx_in = tx.trace[0][2]["tx_in"][0]
			self.assertEqual(tx_in.trace,
				[('__init__', ('foobar_tx', 1), {})])

			tx_out = tx.trace[0][2]["tx_out"][0]
			self.assertEqual(len(tx_out.trace), 1)
			self.assertEqual(tx_out.trace[0][0], "__init__")
			self.assertEqual(len(tx_out.trace[0][1]), 2)
			self.assertEqual(tx_out.trace[0][1][0], 40)
			script = tx_out.trace[0][1][1]
			self.assertEqual(script.elements,
				[OP.TWO, "toPK1", "toPK2", OP.TWO, OP.CHECKMULTISIG])

			tx_out = tx.trace[0][2]["tx_out"][1]
			self.assertEqual(len(tx_out.trace), 1)
			self.assertEqual(tx_out.trace[0][0], "__init__")
			self.assertEqual(len(tx_out.trace[0][1]), 2)
			self.assertEqual(tx_out.trace[0][1][0], 7)
			script = tx_out.trace[0][1][1]
			self.assertEqual(script.elements,
				(OP.DUP, OP.HASH160, "changeHash", OP.EQUALVERIFY, OP.CHECKSIG))

			#Transaction signing:
			self.assertEqual(tx.trace[1][0], "signInput")
			self.assertEqual(len(tx.trace[1][1]), 4)
			self.assertEqual(tx.trace[1][1][0], 0)
			scriptPubKey = tx.trace[1][1][1]
			self.assertEqual(scriptPubKey.serialize(), "foobar_pub")

			key = crypto.Key()
			key.setPrivateKey("foobar")
			self.assertEqual(tx.trace[1][1][2], [None, key.getPublicKey()])
			self.assertEqual(len(tx.trace[1][1][3]), 1)
			self.assertEqual(tx.trace[1][1][3][0].getPrivateKey(), key.getPrivateKey())


	def test_makeSpendMultiSigTransaction(self):
		"Test the makeSpendMultiSigTransaction function"

		with DummyTransaction():
			tx = bitcoinutils.makeSpendMultiSigTransaction(
				"txid", 4, 40, "toHash", 3)

			self.assertEqual(len(tx.trace), 1)

			#Constructor, with tx_in and tx_out:
			self.assertEqual(tx.trace[0][0], "__init__")
			self.assertEqual(tx.trace[0][1], tuple())
			self.assertEqual(len(tx.trace[0][2]), 2)
			self.assertEqual(len(tx.trace[0][2]["tx_in"]), 1)
			self.assertEqual(len(tx.trace[0][2]["tx_out"]), 1)

			tx_in = tx.trace[0][2]["tx_in"][0]
			self.assertEqual(tx_in.trace,
				[('__init__', ('txid', 4), {})])

			tx_out = tx.trace[0][2]["tx_out"][0]
			self.assertEqual(len(tx_out.trace), 1)
			self.assertEqual(tx_out.trace[0][0], "__init__")
			self.assertEqual(len(tx_out.trace[0][1]), 2)
			self.assertEqual(tx_out.trace[0][1][0], 37)
			script = tx_out.trace[0][1][1]
			self.assertEqual(script.elements,
				(OP.DUP, OP.HASH160, "toHash", OP.EQUALVERIFY, OP.CHECKSIG))


	def test_signMultiSigTransaction(self):
		"Test the signMultiSigTransaction function"

		tx = dummy_interfaces.Tracer()
		def getSignatureBodyHash(*args, **kwargs):
			tx.trace.append(("getSignatureBodyHash", args, kwargs))
			return "bodyHash"
		tx.getSignatureBodyHash = getSignatureBodyHash

		key = crypto.Key()
		key.makeNewKey()

		signature = bitcoinutils.signMultiSigTransaction(
			tx, 3, "toPubKey1", "toPubKey2", key)
		
		self.assertEqual(len(tx.trace), 1)
		self.assertEqual(tx.trace[0][0], "getSignatureBodyHash")
		self.assertEqual(tx.trace[0][1][0], 3)
		script = tx.trace[0][1][1]
		self.assertEqual(tx.trace[0][1][2], 1)
		self.assertEqual(script.elements,
			[OP.TWO, "toPubKey1", "toPubKey2", OP.TWO, OP.CHECKMULTISIG])

		self.assertEqual(signature[-1], "\x01")
		signature = signature[:-1]
		self.assertTrue(key.verify("bodyHash", signature))


	def test_verifyMultiSigSignature(self):
		"Test the verifyMultiSigSignature function"

		tx = dummy_interfaces.Tracer()
		def getSignatureBodyHash(*args, **kwargs):
			tx.trace.append(("getSignatureBodyHash", args, kwargs))
			return "bodyHash"
		tx.getSignatureBodyHash = getSignatureBodyHash

		key = crypto.Key()
		key.makeNewKey()

		signature = bitcoinutils.signMultiSigTransaction(
			tx, 3, "toPubKey1", "toPubKey2", key)

		self.assertTrue(bitcoinutils.verifyMultiSigSignature(
			tx, 3, "toPubKey1", "toPubKey2", key, signature)
			)

		key2 = crypto.Key()
		key2.makeNewKey()
		self.assertFalse(bitcoinutils.verifyMultiSigSignature(
			tx, 3, "toPubKey1", "toPubKey2", key2, signature)
			)

		self.assertFalse(bitcoinutils.verifyMultiSigSignature(
			tx, 3, "toPubKey1", "toPubKey2", key, signature[:-1] + "\x02")
			)


	def test_applyMultiSigSignatures(self):
		"Test the applyMultiSigSignatures function"

		tx = dummy_interfaces.Tracer()
		bitcoinutils.applyMultiSigSignatures(tx, "sig1", "sig2")
		self.assertTrue(tx.trace, [(
			"signInputWithSignatures",
			(0, [OP.ZERO, None, None], ["sig1", "sig2"]),
			{}
			)])



if __name__ == "__main__":
	unittest.main(verbosity=2)

