#!/usr/bin/env python
#    test_tcd.py
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

from amiko.channels import tcd



class Test(unittest.TestCase):

	def test_TCD(self):
		"Test the TCD class and its serialization"

		doc = tcd.TCD(0x0123456789abcdef, 0xfedcba9876543210,
			'20-character string.',
			'other 20-len string.',
			'Twenty bytes length.')
		self.assertEqual(doc.startTime, 0x0123456789abcdef)
		self.assertEqual(doc.endTime, 0xfedcba9876543210)
		self.assertEqual(doc.tokenHash, '20-character string.')
		self.assertEqual(doc.commitAddress, 'other 20-len string.')
		self.assertEqual(doc.rollbackAddress, 'Twenty bytes length.')

		data = doc.serialize()
		self.assertEqual(data,
			'\x01\x23\x45\x67\x89\xab\xcd\xef'
			'\xfe\xdc\xba\x98\x76\x54\x32\x10'
			'20-character string.'
			'other 20-len string.'
			'Twenty bytes length.')

		doc2 = tcd.TCD.deserialize(data)
		self.assertEqual(doc2.startTime, 0x0123456789abcdef)
		self.assertEqual(doc2.endTime, 0xfedcba9876543210)
		self.assertEqual(doc2.tokenHash, '20-character string.')
		self.assertEqual(doc2.commitAddress, 'other 20-len string.')
		self.assertEqual(doc2.rollbackAddress, 'Twenty bytes length.')

		self.assertRaises(Exception, tcd.TCD.deserialize, data[:-1])
		self.assertRaises(Exception, tcd.TCD.deserialize, data + '\x00')


	def test_TCDList(self):
		"Test the TCD list serialization"

		TCDlist = \
		[
		tcd.TCD(1, 2, 'a'*20, 'b'*20, 'c'*20),
		tcd.TCD(3, 4, 'd'*20, 'e'*20, 'f'*20),
		tcd.TCD(5, 6, 'g'*20, 'h'*20, 'i'*20)
		]

		data = tcd.serializeList(TCDlist)
		self.assertEqual(data,
			TCDlist[0].serialize() +
			TCDlist[1].serialize() +
			TCDlist[2].serialize()
			)

		TCDlist2 = tcd.deserializeList(data)
		self.assertEqual(len(TCDlist2), 3)
		for i in range(3):
			self.assertEqual(TCDlist2[i].startTime, TCDlist[i].startTime)
			self.assertEqual(TCDlist2[i].endTime, TCDlist[i].endTime)
			self.assertEqual(TCDlist2[i].tokenHash, TCDlist[i].tokenHash)
			self.assertEqual(TCDlist2[i].commitAddress, TCDlist[i].commitAddress)
			self.assertEqual(TCDlist2[i].rollbackAddress, TCDlist[i].rollbackAddress)

		self.assertRaises(Exception, tcd.deserializeList, data[:-1])
		self.assertRaises(Exception, tcd.deserializeList, data + '\x00')



if __name__ == "__main__":
	unittest.main(verbosity=2)

