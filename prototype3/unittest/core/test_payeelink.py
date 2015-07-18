#!/usr/bin/env python
#    test_payeelink.py
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

from amiko.core import network, nodestate, payerlink

from amiko.core import payeelink



class Test(unittest.TestCase):
	def setUp(self):
		self.payeeLink = payeelink.PayeeLink(token="foo")


	def test_defaultAttributes(self):
		"Test default attributes"

		self.assertEqual(self.payeeLink.state, payeelink.PayeeLink.states.initial)
		self.assertEqual(self.payeeLink.amount, 0)
		self.assertEqual(self.payeeLink.receipt, None)
		self.assertEqual(self.payeeLink.token, "foo")
		self.assertEqual(self.payeeLink.transactionID, RIPEMD160(SHA256("foo")))
		self.assertEqual(self.payeeLink.meetingPointID, "")


	def test_msg_pay(self):
		"Test msg_pay"

		ret = self.payeeLink.handleMessage(payeelink.Pay(ID="foobar"))

		self.assertEqual(self.payeeLink.state, payeelink.PayeeLink.states.initial)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, network.OutboundMessage))
		self.assertEqual(msg.localID, "foobar")
		msg = msg.message
		self.assertTrue(isinstance(msg, payerlink.Receipt))
		self.assertEqual(msg.amount, self.payeeLink.amount)
		self.assertEqual(msg.receipt, self.payeeLink.receipt)
		self.assertEqual(msg.transactionID, self.payeeLink.transactionID)
		#self.assertEqual(msg.meetingPoints, []) #TODO

		self.payeeLink.state = payeelink.PayeeLink.states.confirmed
		self.assertRaises(Exception,
			self.payeeLink.handleMessage, payeelink.Pay(ID="foobar"))


	def test_msg_confirm(self):
		"Test msg_confirm"

		ret = self.payeeLink.handleMessage(payeelink.Confirm(ID="foobar", meetingPointID="MPID"))

		self.assertEqual(self.payeeLink.state, payeelink.PayeeLink.states.confirmed)
		self.assertEqual(self.payeeLink.meetingPointID, "MPID")

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, nodestate.MakeRoute))
		self.assertEqual(msg.amount, self.payeeLink.amount)
		self.assertEqual(msg.transactionID, self.payeeLink.transactionID)
		#self.assertEqual(msg.startTime, None) #TODO
		#self.assertEqual(msg.endTime, None) #TODO
		self.assertEqual(msg.meetingPointID, "MPID")
		self.assertEqual(msg.payerID, None)
		self.assertEqual(msg.payeeID, "foobar")

		self.assertRaises(Exception, self.payeeLink.handleMessage,
			payeelink.Confirm(ID="foobar", meetingPointID="MPID"))


	def test_msg_cancel(self):
		"Test msg_cancel"

		ret = self.payeeLink.handleMessage(payeelink.Cancel(ID="foobar"))

		self.assertEqual(self.payeeLink.state, payeelink.PayeeLink.states.cancelled)

		self.assertEqual(len(ret), 0)

		self.assertRaises(Exception, self.payeeLink.handleMessage,
			payeelink.Cancel(ID="foobar"))



if __name__ == "__main__":
	unittest.main(verbosity=2)

