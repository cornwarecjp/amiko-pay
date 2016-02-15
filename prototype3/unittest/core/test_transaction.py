#!/usr/bin/env python
#    test_transaction.py
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

from dummy_interfaces import DummyNetwork

from amiko.core import transaction



class Test(unittest.TestCase):
	def setUp(self):
		self.transaction = transaction.Transaction()


	def test_constructor(self):
		"Test constructor"

		self.assertEqual(self.transaction.isPayerSide, None)
		self.assertEqual(self.transaction.payeeID, None)
		self.assertEqual(self.transaction.payerID, None)
		self.assertEqual(self.transaction.remainingLinkIDs, [])
		self.assertEqual(self.transaction.meetingPointID, None)
		self.assertEqual(self.transaction.amount, 0)
		self.assertEqual(self.transaction.startTime, 0)
		self.assertEqual(self.transaction.endTime, 0)


	def test_tryNextRoute(self):
		"Test tryNextRoute"

		self.transaction.remainingLinkIDs = ['a', 'b', 'c']
		self.transaction.isPayerSide = True
		self.transaction.payerID = 'old'

		self.assertEqual(self.transaction.tryNextRoute(), 'a')
		self.assertEqual(self.transaction.payerID, 'old')
		self.assertEqual(self.transaction.payeeID, 'a')
		self.assertEqual(self.transaction.remainingLinkIDs, ['b', 'c'])

		self.assertEqual(self.transaction.tryNextRoute(), 'b')
		self.assertEqual(self.transaction.payeeID, 'b')
		self.assertEqual(self.transaction.remainingLinkIDs, ['c'])

		self.assertEqual(self.transaction.tryNextRoute(), 'c')
		self.assertEqual(self.transaction.payeeID, 'c')
		self.assertEqual(self.transaction.remainingLinkIDs, [])

		self.assertEqual(self.transaction.tryNextRoute(), None)
		self.assertEqual(self.transaction.payeeID, None)
		self.assertEqual(self.transaction.remainingLinkIDs, [])

		self.transaction.remainingLinkIDs = ['a', 'b', 'c']
		self.transaction.isPayerSide = False
		self.transaction.payeeID = 'old'

		self.assertEqual(self.transaction.tryNextRoute(), 'a')
		self.assertEqual(self.transaction.payeeID, 'old')
		self.assertEqual(self.transaction.payerID, 'a')
		self.assertEqual(self.transaction.remainingLinkIDs, ['b', 'c'])



if __name__ == "__main__":
	unittest.main(verbosity=2)

