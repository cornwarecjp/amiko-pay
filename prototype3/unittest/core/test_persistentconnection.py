#!/usr/bin/env python
#    test_persistentconnection.py
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

from amiko.core import messages

from amiko.core import persistentconnection



class Test(unittest.TestCase):
	def setUp(self):
		self.connection = persistentconnection.PersistentConnection()


	def test_constructor(self):
		"Test constructor"
		self.assertEqual(self.connection.host, None)
		self.assertEqual(self.connection.port, None)
		self.assertEqual(self.connection.connectMessage, None)
		self.assertEqual(self.connection.messages, [])
		self.assertEqual(self.connection.lastIndex, -1)
		self.assertEqual(self.connection.notYetTransmitted, 0)
		self.assertEqual(self.connection.closing, False)


	def test_addMessage_fullOutbox(self):
		"Test addMessage (full outbox)"

		msgIn = messages.OutboundMessage(
			localID="localID",
			message=messages.Cancel()
			)
		msgInState = msgIn.getState()

		for i in range(32768):
			self.connection.handleMessage(msgIn)

			self.assertEqual(self.connection.lastIndex, i)
			self.assertEqual(self.connection.notYetTransmitted, i+1)
			self.assertEqual(len(self.connection.messages), i+1)
			msg = self.connection.messages[-1]
			self.assertEqual(msg.index, i)
			self.assertEqual(msg.message.getState(), msgInState)

		self.assertRaises(Exception, self.connection.handleMessage, msgIn)

		self.assertEqual(self.connection.lastIndex, 32767)
		self.assertEqual(self.connection.notYetTransmitted, 32768)
		self.assertEqual(len(self.connection.messages), 32768)


	def test_addMessage_wrapAround(self):
		"Test addMessage (wrap-around)"

		msgIn = messages.OutboundMessage(
			localID="localID",
			message=messages.Cancel()
			)
		msgInState = msgIn.getState()

		for i in range(65536):
			self.connection.handleMessage(msgIn)

			self.assertEqual(self.connection.lastIndex, i)
			self.assertEqual(self.connection.notYetTransmitted, 1)
			self.assertEqual(len(self.connection.messages), 1)
			msg = self.connection.messages[-1]
			self.assertEqual(msg.index, i)
			self.assertEqual(msg.message.getState(), msgInState)

			self.connection.messages = []
			self.connection.notYetTransmitted = 0

		self.connection.handleMessage(msgIn)

		self.assertEqual(self.connection.lastIndex, 0)
		self.assertEqual(self.connection.notYetTransmitted, 1)
		self.assertEqual(len(self.connection.messages), 1)
		msg = self.connection.messages[-1]
		self.assertEqual(msg.index, 0)
		self.assertEqual(msg.message.getState(), msgInState)


	def test_processConfirmation(self):
		"Test processConfirmation"

		self.connection.messages = \
		[
		persistentconnection.PersistentConnectionMessage(index=1000),
		persistentconnection.PersistentConnectionMessage(index=1001),
		persistentconnection.PersistentConnectionMessage(index=1002),
		persistentconnection.PersistentConnectionMessage(index=1),
		persistentconnection.PersistentConnectionMessage(index=2),
		persistentconnection.PersistentConnectionMessage(index=3),
		persistentconnection.PersistentConnectionMessage(index=4),
		persistentconnection.PersistentConnectionMessage(index=0)
		]

		self.connection.handleMessage(messages.Confirmation(index=2))

		self.assertEqual(len(self.connection.messages), 3)
		self.assertEqual(self.connection.messages[0].index, 3)
		self.assertEqual(self.connection.messages[1].index, 4)
		self.assertEqual(self.connection.messages[2].index, 0)

		self.connection.handleMessage(messages.Confirmation(index=1))

		self.assertEqual(len(self.connection.messages), 3)
		self.assertEqual(self.connection.messages[0].index, 3)
		self.assertEqual(self.connection.messages[1].index, 4)
		self.assertEqual(self.connection.messages[2].index, 0)


	def test_transmit_noMessages(self):
		"Test transmit (no messages)"
		network = DummyNetwork()

		self.assertFalse(self.connection.transmit(network))

		self.assertEqual(network.trace, [])


	def test_transmit_closedConnection(self):
		"Test transmit (closed connection)"
		network = DummyNetwork()
		network.interfaceExistsReturnValue = False

		self.connection.messages = \
		[
		persistentconnection.PersistentConnectionMessage(
			index=1,
			message=messages.OutboundMessage(localID="localID")
			),
		persistentconnection.PersistentConnectionMessage(
			index=2,
			message=messages.OutboundMessage(localID="localID")
			),
		persistentconnection.PersistentConnectionMessage(
			index=3,
			message=messages.OutboundMessage(localID="localID")
			)
		]

		self.connection.closing = False
		self.connection.notYetTransmitted = 1

		self.assertTrue(self.connection.transmit(network))

		self.assertEqual(network.trace, [('interfaceExists', ('localID',), {})])
		self.assertEqual(len(self.connection.messages), 3)
		self.assertEqual(self.connection.notYetTransmitted, 3)

		network.trace = []

		self.assertFalse(self.connection.transmit(network))

		self.assertEqual(network.trace, [('interfaceExists', ('localID',), {})])
		self.assertEqual(len(self.connection.messages), 3)
		self.assertEqual(self.connection.notYetTransmitted, 3)

		network.trace = []
		self.connection.closing = True

		self.assertTrue(self.connection.transmit(network))

		self.assertEqual(network.trace, [('interfaceExists', ('localID',), {})])
		self.assertEqual(len(self.connection.messages), 0)
		self.assertEqual(self.connection.notYetTransmitted, 0)


	def test_transmit_openConnection(self):
		"Test transmit (open connection)"
		network = DummyNetwork()
		network.interfaceExistsReturnValue = True

		self.connection.messages = \
		[
		persistentconnection.PersistentConnectionMessage(
			index=1,
			message=messages.OutboundMessage(localID="localID")
			),
		persistentconnection.PersistentConnectionMessage(
			index=2,
			message=messages.OutboundMessage(localID="localID")
			),
		persistentconnection.PersistentConnectionMessage(
			index=3,
			message=messages.OutboundMessage(localID="localID")
			)
		]

		self.connection.notYetTransmitted = 0

		self.assertFalse(self.connection.transmit(network))

		self.assertEqual(network.trace, [('interfaceExists', ('localID',), {})])
		self.assertEqual(len(self.connection.messages), 3)
		self.assertEqual(self.connection.notYetTransmitted, 0)

		network.trace = []
		self.connection.notYetTransmitted = 2

		self.assertTrue(self.connection.transmit(network))

		self.assertEqual(network.trace,
			[
			('interfaceExists', ('localID',), {}),
			('sendOutboundMessage', (2, self.connection.messages[1].message), {}),
			('sendOutboundMessage', (3, self.connection.messages[2].message), {})
			])
		self.assertEqual(len(self.connection.messages), 3)
		self.assertEqual(self.connection.notYetTransmitted, 0)



if __name__ == "__main__":
	unittest.main(verbosity=2)

