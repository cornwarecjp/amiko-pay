#!/usr/bin/env python
#    test_channel.py
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

import messages

import channel



class Dummy:
	pass



class Test(unittest.TestCase):
	def setUp(self):
		s = \
		{
		"ID": 3,
		"amountLocal": 1234,
		"amountRemote": 4321,
		}

		self.channel = channel.Channel(s)


	def test_constructor(self):
		"Test channel constructor"

		self.assertEqual(self.channel.ID, 3)
		self.assertEqual(self.channel.amountLocal, 1234)
		self.assertEqual(self.channel.amountRemote, 4321)

		#TODO: test initialization of these once supported:
		self.assertEqual(self.channel.transactionsIncomingReserved, {})
		self.assertEqual(self.channel.transactionsOutgoingReserved, {})
		self.assertEqual(self.channel.transactionsIncomingLocked, {})
		self.assertEqual(self.channel.transactionsOutgoingLocked, {})


	def test_getType(self):
		"Test getType method"

		self.assertEqual(self.channel.getType(), "plain")


	def test_getState(self):
		"Test the getState method"

		for forDisplay in [False, True]:
			s = self.channel.getState(forDisplay)

			self.assertEqual(len(s), 8)
			self.assertEqual(s["type"], "plain")
			self.assertEqual(s["ID"], 3)
			self.assertEqual(s["amountLocal"], 1234)
			self.assertEqual(s["amountRemote"], 4321)

			self.assertEqual(s["transactionsIncomingReserved"], {})
			self.assertEqual(s["transactionsOutgoingReserved"], {})
			self.assertEqual(s["transactionsIncomingLocked"], {})
			self.assertEqual(s["transactionsOutgoingLocked"], {})

		self.channel.transactionsIncomingReserved = \
			{binascii.unhexlify("abcd"): 12, binascii.unhexlify("1234"): 34}
		self.channel.transactionsOutgoingReserved = \
			{binascii.unhexlify("0000"): 56}
		self.channel.transactionsIncomingLocked = \
			{binascii.unhexlify("12"): 78}
		self.channel.transactionsOutgoingLocked = \
			{binascii.unhexlify("f000"): 90}
		s = self.channel.getState()
		self.assertEqual(s["transactionsIncomingReserved"],
			{"abcd": 12, "1234": 34})
		self.assertEqual(s["transactionsOutgoingReserved"],
			{"0000": 56})
		self.assertEqual(s["transactionsIncomingLocked"],
			{"12": 78})
		self.assertEqual(s["transactionsOutgoingLocked"],
			{"f000": 90})


	def test_reserve(self):
		"Test the reserve method"

		self.channel.amountLocal = 100
		self.channel.amountRemote = 102
		self.assertRaises(channel.CheckFail, self.channel.reserve,
			True, "foo", 101
			)

		self.channel.amountLocal = 102
		self.channel.amountRemote = 100
		self.assertRaises(channel.CheckFail, self.channel.reserve,
			False, "foo", 101
			)

		self.channel.amountLocal = 100
		self.channel.amountRemote = 200
		self.channel.reserve(True, "foo", 25)
		self.assertEqual(self.channel.amountLocal, 75)
		self.assertEqual(self.channel.amountRemote, 200)
		self.assertEqual(self.channel.transactionsIncomingReserved, {})
		self.assertEqual(self.channel.transactionsOutgoingReserved, {"foo": 25})
		self.assertEqual(self.channel.transactionsIncomingLocked, {})
		self.assertEqual(self.channel.transactionsOutgoingLocked, {})

		self.channel.transactionsOutgoingReserved = {}
		self.channel.amountLocal = 100
		self.channel.amountRemote = 200
		self.channel.reserve(False, "foo", 25)
		self.assertEqual(self.channel.amountLocal, 100)
		self.assertEqual(self.channel.amountRemote, 175)
		self.assertEqual(self.channel.transactionsIncomingReserved, {"foo": 25})
		self.assertEqual(self.channel.transactionsOutgoingReserved, {})
		self.assertEqual(self.channel.transactionsIncomingLocked, {})
		self.assertEqual(self.channel.transactionsOutgoingLocked, {})


	def test_lockIncoming(self):
		"Test the lockIncoming method"

		message = Dummy()
		message.hash = "foo"
		self.channel.transactionsIncomingReserved = {"foo": 25}
		self.channel.lockIncoming(message)
		self.assertEqual(self.channel.transactionsIncomingReserved, {})
		self.assertEqual(self.channel.transactionsOutgoingReserved, {})
		self.assertEqual(self.channel.transactionsIncomingLocked, {"foo": 25})
		self.assertEqual(self.channel.transactionsOutgoingLocked, {})


	def test_lockOutgoing(self):
		"Test the lockOutgoing method"

		self.channel.transactionsOutgoingReserved = {"foo": 25}
		message = self.channel.lockOutgoing("foo")
		self.assertEqual(self.channel.transactionsIncomingReserved, {})
		self.assertEqual(self.channel.transactionsOutgoingReserved, {})
		self.assertEqual(self.channel.transactionsIncomingLocked, {})
		self.assertEqual(self.channel.transactionsOutgoingLocked, {"foo": 25})

		self.assertTrue(isinstance(message, messages.Lock))
		self.assertEqual(message.channelID, 3)
		self.assertEqual(message.hash, "foo")


	def test_commitIncoming(self):
		"Test the commitIncoming method"

		message = Dummy()
		self.channel.transactionsIncomingLocked = {"foo": 25}
		self.channel.amountLocal = 100
		self.channel.commitIncoming("foo", message)
		self.assertEqual(self.channel.amountLocal, 125)
		self.assertEqual(self.channel.transactionsIncomingReserved, {})
		self.assertEqual(self.channel.transactionsOutgoingReserved, {})
		self.assertEqual(self.channel.transactionsIncomingLocked, {})
		self.assertEqual(self.channel.transactionsOutgoingLocked, {})


	def test_commitOutgoing(self):
		"Test the commitOutgoing method"

		self.channel.transactionsOutgoingLocked = {"foo": 25}
		self.channel.amountRemote = 100
		message = self.channel.commitOutgoing("foo", "bar")
		self.assertEqual(self.channel.amountRemote, 125)
		self.assertEqual(self.channel.transactionsIncomingReserved, {})
		self.assertEqual(self.channel.transactionsOutgoingReserved, {})
		self.assertEqual(self.channel.transactionsIncomingLocked, {})
		self.assertEqual(self.channel.transactionsOutgoingLocked, {})

		self.assertTrue(isinstance(message, messages.Commit))
		self.assertEqual(message.channelID, 3)
		self.assertEqual(message.token, "bar")



if __name__ == "__main__":
	unittest.main(verbosity=2)

