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

from dummy_interfaces import Tracer, DummyRoutingContext, DummyMeetingPoint

from amiko.core import transaction



class Test(unittest.TestCase):
	def setUp(self):
		self.routingContext = DummyRoutingContext()
		self.makeNewTransaction(payerLink="payerLink")


	def makeNewTransaction(self, payerLink=None, payeeLink=None):
		self.transaction = transaction.Transaction(
			context="context", routingContext=self.routingContext,
			meetingPoint="meetingPoint",
			amount=42, hash="hash", startTime =123, endTime=456,
			payerLink=payerLink, payeeLink=payeeLink)


	def test_initialState(self):
		"Test the initial state of a transaction"
		self.assertEqual(self.transaction.context, "context")
		self.assertEqual(self.transaction.routingContext, self.routingContext)
		self.assertEqual(self.transaction.meetingPoint, "meetingPoint")
		self.assertEqual(self.transaction.amount, 42)
		self.assertEqual(self.transaction.hash, "hash")
		self.assertEqual(self.transaction.startTime, 123)
		self.assertEqual(self.transaction.endTime, 456)
		self.assertEqual(self.transaction.payerLink, "payerLink")
		self.assertEqual(self.transaction.payeeLink, None)

		self.makeNewTransaction(payeeLink="payeeLink")
		self.assertEqual(self.transaction.payerLink, None)
		self.assertEqual(self.transaction.payeeLink, "payeeLink")


	def test_constructorDefaultArguments(self):
		"Test the default arguments of the constructor"
		self.transaction = transaction.Transaction(
			"context", self.routingContext,
			"meetingPoint",
			42, "hash", payerLink="payerLink")
		self.assertEqual(self.transaction.context, "context")
		self.assertEqual(self.transaction.routingContext, self.routingContext)
		self.assertEqual(self.transaction.meetingPoint, "meetingPoint")
		self.assertEqual(self.transaction.amount, 42)
		self.assertEqual(self.transaction.hash, "hash")
		self.assertEqual(self.transaction.startTime, 0)
		self.assertEqual(self.transaction.endTime, 0)
		self.assertEqual(self.transaction.payerLink, "payerLink")
		self.assertEqual(self.transaction.payeeLink, None)

		self.transaction = transaction.Transaction(
			"context", self.routingContext,
			"meetingPoint",
			42, "hash", payeeLink="payeeLink")
		self.assertEqual(self.transaction.payerLink, None)
		self.assertEqual(self.transaction.payeeLink, "payeeLink")


	def test_constructorExceptions(self):
		#The constructor checks whether exactly one of the links is None
		self.assertRaises(KeyError, self.makeNewTransaction,
			None, None
			)
		self.assertRaises(KeyError, self.makeNewTransaction,
			"payerLink", "payeeLink"
			)


	def test_makeRoute(self):
		"Test the msg_makeRoute method"

		sourceLink = Tracer()

		for payerLink, payeeLink in ((None, sourceLink), (sourceLink, None)):

			self.routingContext.links[0].trace = []
			self.routingContext.links[1].trace = []
			sourceLink.trace = []
			self.routingContext.meetingPoints = \
				[DummyMeetingPoint("NoMeetingPoint"), DummyMeetingPoint("meetingPoint")]
			self.makeNewTransaction(payerLink=payerLink, payeeLink=payeeLink)

			#Routed to meeting point:
			self.transaction.msg_makeRoute()
			self.assertEqual(self.routingContext.meetingPoints[0].trace, [])
			self.assertEqual(self.routingContext.meetingPoints[1].trace,
				[('msg_makeRoute', (self.transaction,), {})]
				)
			self.assertEqual(self.routingContext.links[0].trace, [])
			self.assertEqual(self.routingContext.links[1].trace, [])
			self.assertEqual(sourceLink.trace, [])

			self.routingContext.meetingPoints = []
			self.makeNewTransaction(payerLink=payerLink, payeeLink=payeeLink)

			#Routed to first link:
			self.transaction.msg_makeRoute()
			self.assertEqual(self.routingContext.links[0].trace,
				[('msg_makeRoute', (self.transaction,), {})]
				)
			self.assertEqual(self.routingContext.links[1].trace, [])
			self.assertEqual(sourceLink.trace, [])

			self.routingContext.links[0].trace = []

			#Skip route to second link:
			self.transaction.msg_makeRoute(sourceLinkID="link2")
			self.assertEqual(self.routingContext.links[0].trace, [])
			self.assertEqual(self.routingContext.links[1].trace, [])
			self.assertEqual(self.routingContext.links[2].trace,
				[('msg_makeRoute', (self.transaction,), {})]
				)
			self.assertEqual(sourceLink.trace, [])

			self.routingContext.links[2].trace = []

			#Remove the last link:
			lastlink = self.routingContext.links[-1]
			del self.routingContext.links[-1]

			#No more route:
			self.transaction.msg_makeRoute()
			self.assertEqual(self.routingContext.links[0].trace, [])
			self.assertEqual(self.routingContext.links[1].trace, [])
			self.assertEqual(sourceLink.trace,
				[
				('msg_haveNoRoute', (self.transaction,), {})
				]
				)

			#Place the last Link back:
			self.routingContext.links.append(lastlink)


	def test_haveRoute(self):
		"Test the msg_haveRoute method"

		sourceLink = Tracer()
		destLink = Tracer()
		self.makeNewTransaction(payerLink=sourceLink, payeeLink=None)
		self.transaction.msg_haveRoute(destLink, 1000, 2000)
		self.assertEqual(self.transaction.startTime, 1000)
		self.assertEqual(self.transaction.endTime, 2000)
		self.assertEqual(self.transaction.payerLink, sourceLink)
		self.assertEqual(self.transaction.payeeLink, destLink)
		self.assertEqual(sourceLink.trace,
			[("msg_haveRoute", (self.transaction,), {})]
			)
		self.assertEqual(destLink.trace, [])

		sourceLink = Tracer()
		destLink = Tracer()
		self.makeNewTransaction(payerLink=None, payeeLink=sourceLink)
		self.transaction.msg_haveRoute(destLink, 1000, 2000)
		self.assertEqual(self.transaction.startTime, 1000)
		self.assertEqual(self.transaction.endTime, 2000)
		self.assertEqual(self.transaction.payerLink, destLink)
		self.assertEqual(self.transaction.payeeLink, sourceLink)
		self.assertEqual(sourceLink.trace,
			[("msg_haveRoute", (self.transaction,), {})]
			)
		self.assertEqual(destLink.trace, [])


	def test_haveNoRoute(self):
		"Test the msg_haveNoRoute method"

		sourceLink = Tracer()
		self.makeNewTransaction(payerLink=sourceLink, payeeLink=None)

		#First try the first route:
		self.transaction.msg_makeRoute()
		self.assertEqual(self.routingContext.links[0].trace,
			[('msg_makeRoute', (self.transaction,), {})]
			)
		self.assertEqual(self.routingContext.links[1].trace, [])
		self.assertEqual(sourceLink.trace, [])

		self.routingContext.links[0].trace = []

		#Then report 'no route', which should automatically try the next route:
		self.transaction.msg_haveNoRoute()
		self.assertEqual(self.routingContext.links[0].trace, [])
		self.assertEqual(self.routingContext.links[1].trace,
			[('msg_makeRoute', (self.transaction,), {})]
			)
		self.assertEqual(sourceLink.trace, [])


	def test_endRoute(self):
		"Test the msg_endRoute method"

		sourceLink = Tracer()

		for payerLink, payeeLink in ((None, sourceLink), (sourceLink, None)):
			self.makeNewTransaction(payerLink=payerLink, payeeLink=payeeLink)

			#First try a route:
			self.transaction.msg_makeRoute()

			#Then end it:
			self.routingContext.links[0].trace = []
			self.routingContext.links[1].trace = []
			sourceLink.trace = []
			self.transaction.msg_endRoute()
			self.assertEqual(self.routingContext.links[0].trace,
				[('msg_endRoute', (self.transaction,), {})]
				)
			self.assertEqual(self.routingContext.links[1].trace, [])
			self.assertEqual(sourceLink.trace, [])

			#Then end it again (should be a NOP):
			self.routingContext.links[0].trace = []
			self.transaction.msg_endRoute()
			self.assertEqual(self.routingContext.links[0].trace, [])
			self.assertEqual(self.routingContext.links[1].trace, [])
			self.assertEqual(sourceLink.trace, [])


	def test_lock(self):
		"Test the msg_lock method"

		payerLink = Tracer()
		payeeLink = Tracer()
		self.makeNewTransaction(payerLink=payerLink, payeeLink=None)
		self.transaction.msg_haveRoute(payeeLink, 123, 456)

		payerLink.trace = []
		payeeLink.trace = []
		self.transaction.msg_lock()
		self.assertEqual(payerLink.trace, [])
		self.assertEqual(payeeLink.trace,
			[('msg_lock', (self.transaction,), {})]
			)


	def test_commit(self):
		"Test the msg_commit method"

		payerLink = Tracer()
		payeeLink = Tracer()
		self.makeNewTransaction(payerLink=payerLink, payeeLink=None)
		self.transaction.msg_haveRoute(payeeLink, 123, 456)

		payerLink.trace = []
		payeeLink.trace = []

		payerLink.trace = []
		payeeLink.trace = []
		self.transaction.msg_commit("token")
		self.assertEqual(self.transaction.token, "token")
		self.assertEqual(payerLink.trace, [])
		self.assertEqual(payeeLink.trace,
			[('msg_commit', (self.transaction,), {})]
			)



if __name__ == "__main__":
	unittest.main(verbosity=2)

