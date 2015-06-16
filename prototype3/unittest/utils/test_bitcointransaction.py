#!/usr/bin/env python
#    test_bitcointransaction.py
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
import struct

import testenvironment

from amiko.utils import crypto

from amiko.utils import bitcointransaction
from amiko.utils.bitcointransaction import OP


class Test(unittest.TestCase):

	def test_packVarInt(self):
		"Test the packVarInt function"
		self.assertEqual(bitcointransaction.packVarInt(0x00), '\x00')
		self.assertEqual(bitcointransaction.packVarInt(0xfc), '\xfc')
		self.assertEqual(bitcointransaction.packVarInt(0xfd), '\xfd\xfd\x00')
		self.assertEqual(bitcointransaction.packVarInt(0xfe), '\xfd\xfe\x00')
		self.assertEqual(bitcointransaction.packVarInt(0xfffe), '\xfd\xfe\xff')
		self.assertEqual(bitcointransaction.packVarInt(0xffff), '\xfd\xff\xff')
		self.assertEqual(bitcointransaction.packVarInt(0x010000), '\xfe\x00\x00\x01\x00')
		self.assertEqual(bitcointransaction.packVarInt(0x12345678), '\xfe\x78\x56\x34\x12')
		self.assertEqual(bitcointransaction.packVarInt(0xffffffff), '\xfe\xff\xff\xff\xff')
		self.assertEqual(bitcointransaction.packVarInt(0x0100000000), '\xff\x00\x00\x00\x00\x01\x00\x00\x00')
		self.assertEqual(bitcointransaction.packVarInt(0x0102030405060708), '\xff\x08\x07\x06\x05\x04\x03\x02\x01')


	def test_unpackVarInt(self):
		"Test the unpackVarInt function"
		self.assertEqual(bitcointransaction.unpackVarInt('\x00'), (0x00, 1))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfc'), (0xfc, 1))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfd\xfd\x00'), (0xfd, 3))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfd\xfe\x00'), (0xfe, 3))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfd\xfe\xff'), (0xfffe, 3))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfd\xff\xff'), (0xffff, 3))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfe\x00\x00\x01\x00'), (0x010000, 5))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfe\x78\x56\x34\x12'), (0x12345678, 5))
		self.assertEqual(bitcointransaction.unpackVarInt('\xfe\xff\xff\xff\xff'), (0xffffffff, 5))
		self.assertEqual(bitcointransaction.unpackVarInt('\xff\x00\x00\x00\x00\x01\x00\x00\x00'), (0x0100000000, 9))
		self.assertEqual(bitcointransaction.unpackVarInt('\xff\x08\x07\x06\x05\x04\x03\x02\x01'), (0x0102030405060708, 9))

		old_unpack = struct.unpack
		try:
			struct.unpack = lambda x, y: (0x100,) #Outside normally possible range
			self.assertRaises(Exception, bitcointransaction.unpackVarInt, '\x00')
		finally:
			struct.unpack = old_unpack


	def test_OPCodes(self):
		"Test the OPCode values"

		self.assertEqual(OP.ZERO, 0x00)
		self.assertEqual(OP.TWO, 0x52)
		self.assertEqual(OP.RETURN, 0x6a)
		self.assertEqual(OP.DUP, 0x76)
		self.assertEqual(OP.EQUAL, 0x87)
		self.assertEqual(OP.EQUALVERIFY, 0x88)
		self.assertEqual(OP.SHA256, 0xa8)
		self.assertEqual(OP.HASH160, 0xa9)
		self.assertEqual(OP.CHECKSIG, 0xac)
		self.assertEqual(OP.CHECKSIGVERIFY, 0xad)
		self.assertEqual(OP.CHECKMULTISIG, 0xae)


	def test_standardPubKey(self):
		"Test the Script.standardPubKey method"

		script = bitcointransaction.Script.standardPubKey("foo")
		self.assertTrue(isinstance(script, bitcointransaction.Script))
		self.assertEqual(script.elements,
			(OP.DUP, OP.HASH160, "foo", OP.EQUALVERIFY, OP.CHECKSIG))


	def test_multiSigPubKey(self):
		"Test the Script.multiSigPubKey method"

		script = bitcointransaction.Script.multiSigPubKey(["foo", "bar"])
		self.assertTrue(isinstance(script, bitcointransaction.Script))
		self.assertEqual(script.elements,
			[OP.TWO, "foo", "bar", OP.TWO, OP.CHECKMULTISIG])

		script = bitcointransaction.Script.multiSigPubKey(["foo", "bar", "baz"])
		self.assertTrue(isinstance(script, bitcointransaction.Script))
		self.assertEqual(script.elements,
			[OP.TWO, "foo", "bar", "baz", OP.TWO+1, OP.CHECKMULTISIG])

		self.assertRaises(Exception, bitcointransaction.Script.multiSigPubKey,
			["foo"]*17)

		self.assertRaises(Exception, bitcointransaction.Script.multiSigPubKey,
			["foo"])


	def test_dataPubKey(self):
		"Test the Script.dataPubKey method"

		script = bitcointransaction.Script.dataPubKey("foobar")
		self.assertTrue(isinstance(script, bitcointransaction.Script))
		self.assertEqual(script.elements,
			(OP.RETURN, "foobar"))


	def test_script_deserialize(self):
		"Test the Script.deserialize method"

		script = bitcointransaction.Script.deserialize(
			"\x00"
			"\x03foo"
			"\x4c\x50" + 0x50*'a' + \
			"\x4d\x02\x01" + 0x0102*'a' + \
			"\x4e\x04\x03\x02\x01" + 0x01020304*'a' + \
			"\x76"
			)
		self.assertTrue(isinstance(script, bitcointransaction.Script))
		self.assertEqual(script.elements,
			["", "foo", 0x50*'a', 0x0102*'a', 0x01020304*'a', OP.DUP]
			)


	def test_script_constructor(self):
		"Test the Script constructor"

		script = bitcointransaction.Script(["foo", "bar"])
		self.assertEqual(script.elements, ["foo", "bar"])


	def test_script_serialize(self):
		"Test the Script.serialize method"

		script = bitcointransaction.Script(
			["", "foo", 0x50*'a', 0x0102*'a', 0x01020304*'a', OP.DUP]
			)
		self.assertEqual(script.serialize(),
			"\x00"
			"\x03foo"
			"\x4c\x50" + 0x50*'a' + \
			"\x4d\x02\x01" + 0x0102*'a' + \
			"\x4e\x04\x03\x02\x01" + 0x01020304*'a' + \
			"\x76"
			)

		self.assertRaises(Exception,
			bitcointransaction.Script([None]).serialize)

		class fakeLongString(str):
			def __len__(self):
				return 0x0100000000 #too long to be accepted
		self.assertRaises(Exception,
			bitcointransaction.Script([fakeLongString()]).serialize)


	def test_txin_deserialize(self):
		"Test the TxIn.deserialize method"

		txin, numBytes = bitcointransaction.TxIn.deserialize(
			"abcdefghijklmnopqrstuvwxyz789012" #prev hash
			"\x04\x03\x02\x01" #prev index
			"\x04" #script length
			"\x03foo" #script
			"\x14\x13\x12\x11" #sequence number
			"foobar" #extra, non-read bytes
			)
		self.assertTrue(isinstance(txin, bitcointransaction.TxIn))
		self.assertEqual(txin.previousOutputHash, "abcdefghijklmnopqrstuvwxyz789012")
		self.assertEqual(txin.previousOutputIndex, 0x01020304)
		self.assertTrue(isinstance(txin.scriptSig, bitcointransaction.Script))
		self.assertEqual(txin.scriptSig.elements, ["foo"])
		self.assertEqual(numBytes, 32+4+1+4+4)


	def test_txin_constructor(self):
		"Test the TxIn constructor"

		txin = bitcointransaction.TxIn("foo", 42)
		self.assertEqual(txin.previousOutputHash, "foo")
		self.assertEqual(txin.previousOutputIndex, 42)
		self.assertTrue(isinstance(txin.scriptSig, bitcointransaction.Script))
		self.assertEqual(txin.scriptSig.elements, tuple())


	def test_txin_serialize(self):
		"Test the TxIn.serialize method"

		txin = bitcointransaction.TxIn(
			"abcdefghijklmnopqrstuvwxyz789012", 0x01020304)
		txin.scriptSig = bitcointransaction.Script(["foo"])
		self.assertEqual(txin.serialize(),
			"abcdefghijklmnopqrstuvwxyz789012" #prev hash
			"\x04\x03\x02\x01" #prev index
			"\x04" #script length
			"\x03foo" #script
			"\xff\xff\xff\xff" #sequence number
			)


	def test_txout_deserialize(self):
		"Test the TxOut.deserialize method"

		txout, numBytes = bitcointransaction.TxOut.deserialize(
			"\x08\x07\x06\x05\x04\x03\x02\x01" #amount
			"\x04" #script length
			"\x03foo" #script
			"foobar" #extra, non-read bytes
			)
		self.assertTrue(isinstance(txout, bitcointransaction.TxOut))
		self.assertEqual(txout.amount, 0x0102030405060708)
		self.assertTrue(isinstance(txout.scriptPubKey, bitcointransaction.Script))
		self.assertEqual(txout.scriptPubKey.elements, ["foo"])
		self.assertEqual(numBytes, 8+1+4)


	def test_txout_constructor(self):
		"Test the TxOut constructor"

		txout = bitcointransaction.TxOut(42, bitcointransaction.Script(["foo"]))
		self.assertEqual(txout.amount, 42)
		self.assertTrue(isinstance(txout.scriptPubKey, bitcointransaction.Script))
		self.assertEqual(txout.scriptPubKey.elements, ["foo"])


	def test_txout_serialize(self):
		"Test the TxOut.serialize method"

		txout = bitcointransaction.TxOut(
			0x0102030405060708, bitcointransaction.Script(["foo"]))
		self.assertEqual(txout.serialize(),
			"\x08\x07\x06\x05\x04\x03\x02\x01" #amount
			"\x04" #script length
			"\x03foo" #script
			)


	def test_transaction_deserialize(self):
		"Test the Transaction.deserialize method"

		tx = bitcointransaction.Transaction.deserialize(
			#Example taken from https://en.bitcoin.it/wiki/Protocol_documentation#tx

			#Transaction:
			"\x01\x00\x00\x00"                                 #version

			#Inputs:
			"\x01"                                             #number of transaction inputs

			#Input 1:
			"\x6D\xBD\xDB\x08\x5B\x1D\x8A\xF7\x51\x84\xF0\xBC\x01\xFA\xD5\x8D" #previous output (outpoint)
			"\x12\x66\xE9\xB6\x3B\x50\x88\x19\x90\xE4\xB4\x0D\x6A\xEE\x36\x29"
			"\x00\x00\x00\x00"

			"\x8B"                                             #script is 139 bytes long

			"\x48\x30\x45\x02\x21\x00\xF3\x58\x1E\x19\x72\xAE\x8A\xC7\xC7\x36" #signature script (scriptSig)
			"\x7A\x7A\x25\x3B\xC1\x13\x52\x23\xAD\xB9\xA4\x68\xBB\x3A\x59\x23"
			"\x3F\x45\xBC\x57\x83\x80\x02\x20\x59\xAF\x01\xCA\x17\xD0\x0E\x41"
			"\x83\x7A\x1D\x58\xE9\x7A\xA3\x1B\xAE\x58\x4E\xDE\xC2\x8D\x35\xBD"
			"\x96\x92\x36\x90\x91\x3B\xAE\x9A\x01\x41\x04\x9C\x02\xBF\xC9\x7E"
			"\xF2\x36\xCE\x6D\x8F\xE5\xD9\x40\x13\xC7\x21\xE9\x15\x98\x2A\xCD"
			"\x2B\x12\xB6\x5D\x9B\x7D\x59\xE2\x0A\x84\x20\x05\xF8\xFC\x4E\x02"
			"\x53\x2E\x87\x3D\x37\xB9\x6F\x09\xD6\xD4\x51\x1A\xDA\x8F\x14\x04"
			"\x2F\x46\x61\x4A\x4C\x70\xC0\xF1\x4B\xEF\xF5"

			"\xFF\xFF\xFF\xFF"                                 #sequence

			#Outputs:
			"\x02"                                             #2 Output Transactions

			#Output 1:
			"\x40\x4B\x4C\x00\x00\x00\x00\x00"                 #0.05 BTC (5000000)
			"\x19"                                             #pk_script is 25 bytes long

			"\x76\xA9\x14\x1A\xA0\xCD\x1C\xBE\xA6\xE7\x45\x8A\x7A\xBA\xD5\x12" #pk_script
			"\xA9\xD9\xEA\x1A\xFB\x22\x5E\x88\xAC"

			#Output 2:
			"\x80\xFA\xE9\xC7\x00\x00\x00\x00"                 #33.54 BTC (3354000000)
			"\x19"                                             #pk_script is 25 bytes long

			"\x76\xA9\x14\x0E\xAB\x5B\xEA\x43\x6A\x04\x84\xCF\xAB\x12\x48\x5E" #pk_script
			"\xFD\xA0\xB7\x8B\x4E\xCC\x52\x88\xAC"

			#Locktime:
			"\x00\x00\x00\x00"                                 #lock time
			)
		self.assertTrue(isinstance(tx, bitcointransaction.Transaction))
		self.assertEqual(tx.lockTime, 0)
		self.assertEqual(len(tx.tx_in), 1)
		self.assertTrue(isinstance(tx.tx_in[0], bitcointransaction.TxIn))
		self.assertEqual(len(tx.tx_out), 2)
		self.assertTrue(isinstance(tx.tx_out[0], bitcointransaction.TxOut))
		self.assertTrue(isinstance(tx.tx_out[1], bitcointransaction.TxOut))
		self.assertEqual(tx.tx_in[0].previousOutputHash,
			"\x6D\xBD\xDB\x08\x5B\x1D\x8A\xF7\x51\x84\xF0\xBC\x01\xFA\xD5\x8D"
			"\x12\x66\xE9\xB6\x3B\x50\x88\x19\x90\xE4\xB4\x0D\x6A\xEE\x36\x29"
			)
		self.assertEqual(tx.tx_in[0].previousOutputIndex, 0)
		self.assertEqual(tx.tx_in[0].scriptSig.elements,[
			'0E\x02!\x00\xf3X\x1e\x19r\xae\x8a\xc7\xc76zz%;\xc1\x13R#\xad\xb9\xa4h\xbb:Y#?E\xbcW\x83\x80\x02 Y\xaf\x01\xca\x17\xd0\x0eA\x83z\x1dX\xe9z\xa3\x1b\xaeXN\xde\xc2\x8d5\xbd\x96\x926\x90\x91;\xae\x9a\x01',
			'\x04\x9c\x02\xbf\xc9~\xf26\xcem\x8f\xe5\xd9@\x13\xc7!\xe9\x15\x98*\xcd+\x12\xb6]\x9b}Y\xe2\n\x84 \x05\xf8\xfcN\x02S.\x87=7\xb9o\t\xd6\xd4Q\x1a\xda\x8f\x14\x04/FaJLp\xc0\xf1K\xef\xf5'
			])
		self.assertEqual(tx.tx_out[0].amount, 5000000)
		self.assertEqual(tx.tx_out[0].scriptPubKey.elements, [
			OP.DUP, OP.HASH160,
			'\x1a\xa0\xcd\x1c\xbe\xa6\xe7E\x8az\xba\xd5\x12\xa9\xd9\xea\x1a\xfb"^',
			OP.EQUALVERIFY, OP.CHECKSIG
			])
		self.assertEqual(tx.tx_out[1].amount, 3354000000)
		self.assertEqual(tx.tx_out[1].scriptPubKey.elements, [
			OP.DUP, OP.HASH160,
			'\x0e\xab[\xeaCj\x04\x84\xcf\xab\x12H^\xfd\xa0\xb7\x8bN\xccR',
			OP.EQUALVERIFY, OP.CHECKSIG
			])

		self.assertRaises(Exception, bitcointransaction.Transaction.deserialize,
			"\x02\x00\x00\x00"
			)

		self.assertRaises(Exception, bitcointransaction.Transaction.deserialize,
			"\x01\x00\x00\x00"                                 #version

			#Inputs:
			"\x00"                                             #number of transaction inputs

			#Outputs:
			"\x00"                                             #2 Output Transactions

			#Locktime:
			"\x00\x00\x00\x00"                                 #lock time

			#Unused data (triggers the exception):
			"foobar"
			)


	def test_transaction_constructor(self):
		"Test the Transaction constructor"

		tx = bitcointransaction.Transaction("tx_in", "tx_out", 12345)
		self.assertEqual(tx.tx_in, "tx_in")
		self.assertEqual(tx.tx_out, "tx_out")
		self.assertEqual(tx.lockTime, 12345)


	def test_transaction_serialize(self):
		"Test the Transaction.serialize method"

		tx = bitcointransaction.Transaction(
			[
			bitcointransaction.TxIn(
				"\x6D\xBD\xDB\x08\x5B\x1D\x8A\xF7\x51\x84\xF0\xBC\x01\xFA\xD5\x8D"
				"\x12\x66\xE9\xB6\x3B\x50\x88\x19\x90\xE4\xB4\x0D\x6A\xEE\x36\x29",
				0
				)
			],
			[
			bitcointransaction.TxOut(5000000, bitcointransaction.Script([
				OP.DUP, OP.HASH160,
				'\x1a\xa0\xcd\x1c\xbe\xa6\xe7E\x8az\xba\xd5\x12\xa9\xd9\xea\x1a\xfb"^',
				OP.EQUALVERIFY, OP.CHECKSIG
				])),
			bitcointransaction.TxOut(3354000000, bitcointransaction.Script([
				OP.DUP, OP.HASH160,
				'\x0e\xab[\xeaCj\x04\x84\xcf\xab\x12H^\xfd\xa0\xb7\x8bN\xccR',
				OP.EQUALVERIFY, OP.CHECKSIG
				]))
			],
			0)
		tx.tx_in[0].scriptSig = bitcointransaction.Script([
			'0E\x02!\x00\xf3X\x1e\x19r\xae\x8a\xc7\xc76zz%;\xc1\x13R#\xad\xb9\xa4h\xbb:Y#?E\xbcW\x83\x80\x02 Y\xaf\x01\xca\x17\xd0\x0eA\x83z\x1dX\xe9z\xa3\x1b\xaeXN\xde\xc2\x8d5\xbd\x96\x926\x90\x91;\xae\x9a\x01',
			'\x04\x9c\x02\xbf\xc9~\xf26\xcem\x8f\xe5\xd9@\x13\xc7!\xe9\x15\x98*\xcd+\x12\xb6]\x9b}Y\xe2\n\x84 \x05\xf8\xfcN\x02S.\x87=7\xb9o\t\xd6\xd4Q\x1a\xda\x8f\x14\x04/FaJLp\xc0\xf1K\xef\xf5'
			])

		self.assertEqual(tx.serialize(),
			#Example taken from https://en.bitcoin.it/wiki/Protocol_documentation#tx

			#Transaction:
			"\x01\x00\x00\x00"                                 #version

			#Inputs:
			"\x01"                                             #number of transaction inputs

			#Input 1:
			"\x6D\xBD\xDB\x08\x5B\x1D\x8A\xF7\x51\x84\xF0\xBC\x01\xFA\xD5\x8D" #previous output (outpoint)
			"\x12\x66\xE9\xB6\x3B\x50\x88\x19\x90\xE4\xB4\x0D\x6A\xEE\x36\x29"
			"\x00\x00\x00\x00"

			"\x8B"                                             #script is 139 bytes long

			"\x48\x30\x45\x02\x21\x00\xF3\x58\x1E\x19\x72\xAE\x8A\xC7\xC7\x36" #signature script (scriptSig)
			"\x7A\x7A\x25\x3B\xC1\x13\x52\x23\xAD\xB9\xA4\x68\xBB\x3A\x59\x23"
			"\x3F\x45\xBC\x57\x83\x80\x02\x20\x59\xAF\x01\xCA\x17\xD0\x0E\x41"
			"\x83\x7A\x1D\x58\xE9\x7A\xA3\x1B\xAE\x58\x4E\xDE\xC2\x8D\x35\xBD"
			"\x96\x92\x36\x90\x91\x3B\xAE\x9A\x01\x41\x04\x9C\x02\xBF\xC9\x7E"
			"\xF2\x36\xCE\x6D\x8F\xE5\xD9\x40\x13\xC7\x21\xE9\x15\x98\x2A\xCD"
			"\x2B\x12\xB6\x5D\x9B\x7D\x59\xE2\x0A\x84\x20\x05\xF8\xFC\x4E\x02"
			"\x53\x2E\x87\x3D\x37\xB9\x6F\x09\xD6\xD4\x51\x1A\xDA\x8F\x14\x04"
			"\x2F\x46\x61\x4A\x4C\x70\xC0\xF1\x4B\xEF\xF5"

			"\xFF\xFF\xFF\xFF"                                 #sequence

			#Outputs:
			"\x02"                                             #2 Output Transactions

			#Output 1:
			"\x40\x4B\x4C\x00\x00\x00\x00\x00"                 #0.05 BTC (5000000)
			"\x19"                                             #pk_script is 25 bytes long

			"\x76\xA9\x14\x1A\xA0\xCD\x1C\xBE\xA6\xE7\x45\x8A\x7A\xBA\xD5\x12" #pk_script
			"\xA9\xD9\xEA\x1A\xFB\x22\x5E\x88\xAC"

			#Output 2:
			"\x80\xFA\xE9\xC7\x00\x00\x00\x00"                 #33.54 BTC (3354000000)
			"\x19"                                             #pk_script is 25 bytes long

			"\x76\xA9\x14\x0E\xAB\x5B\xEA\x43\x6A\x04\x84\xCF\xAB\x12\x48\x5E" #pk_script
			"\xFD\xA0\xB7\x8B\x4E\xCC\x52\x88\xAC"

			#Locktime:
			"\x00\x00\x00\x00"                                 #lock time
			)

	def test_getSignatureBodyHash(self):
		"Test the Transaction.getSignatureBodyHash method"

		tx = bitcointransaction.Transaction(
			[
				bitcointransaction.TxIn("fooofooofooofooofooofooofooofooo", 1),
				bitcointransaction.TxIn("barrbarrbarrbarrbarrbarrbarrbarr", 2)
			],
			[
			bitcointransaction.TxOut(
				5000000, bitcointransaction.Script(["a"])),
			],
			4)
		tx.tx_in[0].scriptSig = bitcointransaction.Script(["b"])
		tx.tx_in[1].scriptSig = bitcointransaction.Script(["c"])

		bodyHash = tx.getSignatureBodyHash(
			0, bitcointransaction.Script(["foobar"]), hashType=1)

		self.assertEqual(bodyHash,
			crypto.SHA256(crypto.SHA256(
			#Transaction:
			"\x01\x00\x00\x00"                 #version

			#Inputs:
			"\x02"                             #number of transaction inputs

			#Input 1:
			"fooofooofooofooofooofooofooofooo" #previous output (outpoint)
			"\x01\x00\x00\x00"

			"\x07"                             #script is 7 bytes long (replaced)
			"\x06foobar"

			"\xFF\xFF\xFF\xFF"                 #sequence

			#Input 2:
			"barrbarrbarrbarrbarrbarrbarrbarr" #previous output (outpoint)
			"\x02\x00\x00\x00"

			"\x00"                             #script is 0 bytes long (emptied)

			"\xFF\xFF\xFF\xFF"                 #sequence

			#Outputs:
			"\x01"                             #1 Output Transaction

			#Output 1:
			"\x40\x4B\x4C\x00\x00\x00\x00\x00" #0.05 BTC (5000000)
			"\x02"                             #pk_script is 2 bytes long

			"\x01a"                            #pk_script

			#Locktime:
			"\x04\x00\x00\x00"                 #lock time

			#Hash type:
			"\x01\x00\x00\x00"
			)))


	def test_signInputWithSignatures(self):
		"Test the Transaction.signInputWithSignatures method"

		tx = bitcointransaction.Transaction(
			[
				bitcointransaction.TxIn("foo", 1),
				bitcointransaction.TxIn("bar", 2)
			],
			[
			bitcointransaction.TxOut(
				5000000, bitcointransaction.Script(["a"])),
			],
			4)

		tx.signInputWithSignatures(1, ["x", None, "y", None, "z"], ["sig1", "sig2"])

		self.assertTrue(isinstance(tx.tx_in[1].scriptSig, bitcointransaction.Script))
		self.assertEqual(tx.tx_in[1].scriptSig.elements,
			["x", "sig1", "y", "sig2", "z"]
			)


	def test_signInput(self):
		"Test the Transaction.signInput method"

		tx = bitcointransaction.Transaction(
			[
				bitcointransaction.TxIn("foo", 1),
				bitcointransaction.TxIn("bar", 2)
			],
			[
			bitcointransaction.TxOut(
				5000000, bitcointransaction.Script(["a"])),
			],
			4)

		keys = [crypto.Key(), crypto.Key()]
		for k in keys:
			k.makeNewKey()

		scriptPubKey = bitcointransaction.Script(["foobar"])
		bodyHash = tx.getSignatureBodyHash(1, scriptPubKey, 1)
		tx.signInput(1, scriptPubKey, ["x", None, "y", None, "z"], keys)

		self.assertTrue(isinstance(tx.tx_in[1].scriptSig, bitcointransaction.Script))
		e = tx.tx_in[1].scriptSig.elements

		self.assertEqual(len(e), 5)
		self.assertEqual(e[0], "x")
		self.assertEqual(e[2], "y")
		self.assertEqual(e[4], "z")
		sigs = [e[1], e[3]]
		for i in range(2):
			s = sigs[i]
			k = keys[i]
			self.assertEqual(s[-1], "\x01")
			self.assertTrue(k.verify(bodyHash, s[:-1]))


	def test_getTransactionID(self):
		"Test the Transaction.getTransactionID method"

		tx = bitcointransaction.Transaction(
			[
				bitcointransaction.TxIn("foo", 1),
				bitcointransaction.TxIn("bar", 2)
			],
			[
			bitcointransaction.TxOut(
				5000000, bitcointransaction.Script(["a"])),
			],
			4)

		#This hash number was generated by the code itself, so it is
		#only a regression test.
		self.assertEqual(tx.getTransactionID().encode("hex"),
			"4455a9149e1e6ab19c7647dbf58378468e80ca8d1d3bb1713ba1da3825194ff4")



if __name__ == "__main__":
	unittest.main(verbosity=2)

