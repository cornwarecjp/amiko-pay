#!/usr/bin/env python
#    test_base58.py
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
import sys
sys.path.append('../..')

import testenvironment

from amiko.core import base58



class Test(unittest.TestCase):
	def setUp(self):
		#I just took some random keys from the block chain
		#(thanks to blockexplorer.com for the service).
		#I have no idea whose keys they are.
		self.testSet = \
		[
		#Just some address (without leading zeroes):
		("66750c10f3f64d0e4b8d6d80fa3d9f08cb59cdd3", "1ALk99MqTNc9ifW1DhbUa8g39FTiHuyr3L"),

		#This one is included to test leading zeroes:
		("0000a21b7e708c3816f18be8cfce5f6740f94c2b", "111kzsNZ1w27kSGXwyov1ZvUGVLJMvLmJ")
		]

		self.testSet = [
			(binascii.unhexlify(hash160), address)
			for hash160, address in self.testSet
			]


	def test_encodeBase58Check(self):
		"Test the encodeBase58Check function"

		for hash160, address in self.testSet:
			self.assertEqual(base58.encodeBase58Check(hash160, 0), address)


	def test_decodeBase58Check(self):
		"Test the decodeBase58Check function"

		for hash160, address in self.testSet:
			self.assertEqual(base58.decodeBase58Check(address, 0), hash160)


	def test_versionMismatch(self):
		"Test what happens if decode finds an incorrect version number"

		for hash160, address in self.testSet:
			wrongAddress = base58.encodeBase58Check(hash160, 1)

			#Make sure it still works if we use the same version number:
			self.assertEqual(base58.decodeBase58Check(wrongAddress, 1), hash160)

			#But it will fail with a different version number:
			self.assertRaises(Exception, base58.decodeBase58Check,
				wrongAddress, 0
				)


	def test_checksumFailure(self):
		"Test what happens if a single character is changed"

		for hash160, address in self.testSet:
			def change(c):
				return 'b' if c=='a' else 'a'

			wrongAddress = address[:5] + change(address[5]) + address[6:]

			self.assertRaises(Exception, base58.decodeBase58Check,
				wrongAddress, 0
				)


	def test_encodeEmptyString(self):
		"Test encoding the empty string"

		self.assertEqual(base58.encodeBase58(""), "")


	def test_encodeDecodeZeroes(self):
		"Test encoding and decoding zeroes"

		original = '\0'*4
		encoded = base58.encodeBase58(original)
		decoded = base58.decodeBase58(encoded)
		#print repr(original), repr(encoded), repr(decoded)
		self.assertEqual(original, decoded)



if __name__ == "__main__":
	unittest.main(verbosity=2)

