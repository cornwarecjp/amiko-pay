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

import bitcointransaction
from bitcointransaction import OP


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

		script = bitcointransaction.Script.multiSigPubKey("foo", "bar")
		self.assertTrue(isinstance(script, bitcointransaction.Script))
		self.assertEqual(script.elements,
			(OP.TWO, "foo", "bar", OP.TWO, OP.CHECKMULTISIG))


	def test_secretPubKey(self):
		"Test the Script.secretPubKey method"

		script = bitcointransaction.Script.secretPubKey("foo", "bar")
		self.assertTrue(isinstance(script, bitcointransaction.Script))
		self.assertEqual(script.elements,
			("foo", OP.CHECKSIGVERIFY, OP.SHA256, "bar", OP.EQUAL))


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

		self.assertRaises(Exception, bitcointransaction.Script([None]).serialize)



if __name__ == "__main__":
	unittest.main(verbosity=2)

