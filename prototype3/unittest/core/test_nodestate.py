#!/usr/bin/env python
#    test_node.py
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

from amiko.core import node
from amiko.core import payeelink, transaction



class Test(unittest.TestCase):
	def setUp(self):
		self.node = node.Node(token="foo")


	def test_defaultAttributes(self):
		"Test default attributes"

		self.assertEqual(self.node.links, {})
		self.assertEqual(self.node.payeeLinks, {})
		self.assertEqual(self.node.meetingPoints, {})
		self.assertEqual(self.node.transactions, {})


	def test_msg_request(self):
		"Test msg_request"
		request = node.Node_PaymentRequest(amount=1234, receipt="foobar")

		ret = self.node.handleMessage(request)

		self.assertEqual(len(self.node.payeeLinks), 1)
		linkID = self.node.payeeLinks.keys()[0]
		newLink = self.node.payeeLinks[linkID]
		self.assertEqual(newLink.__class__, payeelink.PayeeLink)
		self.assertEqual(newLink.receipt, "foobar")
		txID = newLink.transactionID
		self.assertEqual(txID, RIPEMD160(SHA256(newLink.token)))

		#TODO: test ret



if __name__ == "__main__":
	unittest.main(verbosity=2)

