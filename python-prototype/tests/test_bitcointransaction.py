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
			


if __name__ == "__main__":
	unittest.main(verbosity=2)

