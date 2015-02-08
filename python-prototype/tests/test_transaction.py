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

import transaction


class Tracer:
	def __init__(self):
		self.trace = []


	def __getattr__(self, name):
		def generic_method(*args, **kwargs):
			#print self, (name, args, kwargs)
			self.trace.append((name, args, kwargs))

		return generic_method


	def __eq__(self, x):
		#Exception: this doesn't get through __getattr__
		return id(x) == id(self)


	def __ne__(self, x):
		#Exception: this doesn't get through __getattr__
		return id(x) != id(self)



class DummyLink(Tracer):
	def __init__(self, ID):
		Tracer.__init__(self)
		self.localID = ID


	def __str__(self):
		return "DummyLink:" + self.localID


	def __repr__(self):
		return self.__str__()



class DummyMeetingPoint(Tracer):
	def __init__(self, ID):
		Tracer.__init__(self)
		self.ID = ID

	def __str__(self):
		return "DummyMeetingPoint:" + self.ID



class DummyRoutingContext:
	def __init__(self):
		self.links = [DummyLink("link1"), DummyLink("link2"), DummyLink("link3")]
		self.meetingPoints = []



class Test(unittest.TestCase):
	def setUp(self):
		self.routingContext = DummyRoutingContext()
		self.makeNewTransaction()


	def makeNewTransaction(self, payerLink="payerLink", payeeLink="payeeLink"):
		self.transaction = transaction.Transaction(
			context="context", routingContext=self.routingContext,
			amount=42, hash="hash", meetingPoint="meetingPoint",
			payerLink=payerLink, payeeLink=payeeLink)


	def test_initialState(self):
		"Test the initial state of a transaction"
		self.assertEqual(self.transaction.context, "context")
		self.assertEqual(self.transaction.routingContext, self.routingContext)
		self.assertEqual(self.transaction.amount, 42)
		self.assertEqual(self.transaction.hash, "hash")
		self.assertEqual(self.transaction.meetingPoint, "meetingPoint")
		self.assertEqual(self.transaction.payerLink, "payerLink")
		self.assertEqual(self.transaction.payeeLink, "payeeLink")


	def test_isPayerSide(self):
		"Test the isPayerSide method"
		self.transaction.payerLink = None
		self.transaction.payeeLink = "payeeLink"
		self.assertFalse(self.transaction.isPayerSide())

		self.transaction.payerLink = "payerLink"
		self.transaction.payeeLink = None
		self.assertTrue(self.transaction.isPayerSide())

		self.transaction.payerLink = "payerLink"
		self.transaction.payeeLink = "payeeLink"
		self.assertRaises(Exception, self.transaction.isPayerSide)


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

			#Routed to second link:
			self.transaction.msg_makeRoute()
			self.assertEqual(self.routingContext.links[0].trace, [])
			self.assertEqual(self.routingContext.links[1].trace,
				[('msg_makeRoute', (self.transaction,), {})]
				)

			self.routingContext.links[1].trace = []
			self.assertEqual(sourceLink.trace, [])

			#Remove the last link:
			lastlink = self.routingContext.links[-1]
			del self.routingContext.links[-1]

			#No more route:
			self.transaction.msg_makeRoute()
			self.assertEqual(self.routingContext.links[0].trace, [])
			self.assertEqual(self.routingContext.links[1].trace, [])
			self.assertEqual(sourceLink.trace,
				[
				('msg_cancel', (self.transaction,), {})
				]
				)

			#Place the last Link back:
			self.routingContext.links.append(lastlink)


	def test_haveRoute(self):
		"Test the msg_haveRoute method"

		sourceLink = Tracer()
		destLink = Tracer()
		self.makeNewTransaction(payerLink=sourceLink, payeeLink=None)
		self.transaction.msg_haveRoute(destLink)
		self.assertEqual(self.transaction.payerLink, sourceLink)
		self.assertEqual(self.transaction.payeeLink, destLink)
		self.assertEqual(sourceLink.trace,
			[("msg_haveRoute", (self.transaction,), {})]
			)
		self.assertEqual(destLink.trace, [])

		sourceLink = Tracer()
		destLink = Tracer()
		self.makeNewTransaction(payerLink=None, payeeLink=sourceLink)
		self.transaction.msg_haveRoute(destLink)
		self.assertEqual(self.transaction.payerLink, destLink)
		self.assertEqual(self.transaction.payeeLink, sourceLink)
		self.assertEqual(sourceLink.trace,
			[("msg_haveRoute", (self.transaction,), {})]
			)
		self.assertEqual(destLink.trace, [])

		link1 = Tracer()
		link2 = Tracer()
		destLink = Tracer()
		self.makeNewTransaction(payerLink=link1, payeeLink=link2)
		self.assertRaises(Exception, self.transaction.msg_haveRoute, destLink)
		self.assertEqual(self.transaction.payerLink, link1)
		self.assertEqual(self.transaction.payeeLink, link2)
		self.assertEqual(link1.trace, [])
		self.assertEqual(link2.trace, [])
		self.assertEqual(destLink.trace, [])


	def test_cancelRoute(self):
		"Test the msg_cancelRoute method"

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

		#Then cancel it, which should automatically try the next route:
		self.transaction.msg_cancelRoute()
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


	def test_lock(self):
		"Test the msg_lock method"

		payerLink = Tracer()
		payeeLink = Tracer()
		self.makeNewTransaction(payerLink=payerLink, payeeLink=None)
		self.transaction.msg_haveRoute(payeeLink)

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
		self.transaction.msg_haveRoute(payeeLink)

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

