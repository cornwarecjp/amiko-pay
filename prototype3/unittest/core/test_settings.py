#!/usr/bin/env python
#    test_settings.py
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

import testenvironment

from amiko.utils.crypto import RIPEMD160, SHA256

from amiko.core import settings



class Test(unittest.TestCase):
	def test_globalConstants(self):
		"Test global constants"
		self.assertEqual(settings.defaultPort, 4321)


	def test_hashAlgorithm(self):
		"Test hashAlgorithm function"
		self.assertEqual(settings.hashAlgorithm("foobar"),
			RIPEMD160(SHA256("foobar")))


	def test_construct_without_file(self):
		"Test constion without file"

		s = settings.Settings()
		self.checkDefaultValues(s)


	def test_construct_with_file(self):
		"Test constion with file"

		s = settings.Settings('test_settings.conf')
		self.checkLoadedValues(s)


	def checkDefaultValues(self, s):
		self.assertEqual(s.listenHost, '')
		self.assertEqual(s.listenPort, 4321)
		self.assertEqual(s.advertizedHost, '')
		self.assertEqual(s.advertizedPort, 4321)
		self.assertEqual(s.stateFile, 'amikopay.dat')
		self.assertEqual(s.payLogFile, 'payments.log')
		self.assertEqual(s.acceptedEscrowKeys, [])
		self.assertEqual(s.externalMeetingPoints, [])
		self.assertEqual(s.bitcoinRPCURL, '')

		self.assertEqual(s.getAdvertizedNetworkLocation(), '')

	def checkLoadedValues(self, s):
		self.assertEqual(s.listenHost, 'test_listen_host')
		self.assertEqual(s.listenPort, 12345)
		self.assertEqual(s.advertizedHost, 'test_advertized_host')
		self.assertEqual(s.advertizedPort, 2468)
		self.assertEqual(s.stateFile, 'test_state_file')
		self.assertEqual(s.payLogFile, 'test_log_file')
		self.assertEqual(s.acceptedEscrowKeys, ['\xde\xad\xbe\xef', '\x01\x23\x45\x67'])
		self.assertEqual(s.externalMeetingPoints, ['MP1', 'MP2'])
		self.assertEqual(s.bitcoinRPCURL, 'test_rpc_url')

		self.assertEqual(s.getAdvertizedNetworkLocation(), 'test_advertized_host:2468')



if __name__ == "__main__":
	unittest.main(verbosity=2)

