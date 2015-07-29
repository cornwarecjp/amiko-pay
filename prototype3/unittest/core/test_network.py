#!/usr/bin/env python
#    test_network.py
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

from amiko.core import messages

from amiko.core import network



class Test(unittest.TestCase):
	def setUp(self):
		self.network = network.Network('localhost', 4321, self)

		self.messages = []


	def tearDown(self):
		#Clean up the listener, so we can run other tests:
		self.network.listener.close()


	def test_connectionSession(self):
		"Test connection session"

		#Opening the connection:
		c1 = self.network.makeConnection(
			('localhost', 4321), 'localID', messages.Pay(ID='remoteID'))

		self.assertEqual(c1.localID, 'localID')
		self.assertEqual(len(self.network.connections), 1)
		self.assertEqual(self.network.connections[0], c1)
		self.assertEqual(self.network.getInterface('localID'), c1)
		self.assertTrue(self.network.interfaceExists('localID'))

		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(len(self.network.connections), 2)
		c2 = self.network.connections[1]
		self.assertEqual(c2.localID, None)

		self.assertEqual(len(self.messages), 0)

		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(c2.localID, 'remoteID')
		self.assertTrue(self.network.interfaceExists('remoteID'))
		self.assertEqual(len(self.messages), 1)
		self.assertEqual(self.messages[0].__class__, messages.Pay)

		#Sending another connect message (illegal):
		self.messages = []
		self.network.sendOutboundMessage(0, messages.OutboundMessage(
			localID='localID',
			message=messages.Pay(ID='remoteID2')))

		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(c2.localID, 'remoteID') #unchanged
		self.assertEqual(len(self.messages), 0) #nothing received

		#Sending another message back:
		self.network.sendOutboundMessage(42, messages.OutboundMessage(
			localID='remoteID',
			message=messages.Cancel(ID=None)))

		self.network.processNetworkEvents(timeout=0.01) #sends the confirmation

		self.assertEqual(len(self.messages), 1)
		self.assertEqual(self.messages[0].__class__, messages.Cancel)

		self.messages = []
		self.network.processNetworkEvents(timeout=0.01) #receives the confirmation

		self.assertEqual(len(self.messages), 1)
		self.assertEqual(self.messages[0].__class__, messages.Confirmation)
		self.assertEqual(self.messages[0].localID, 'remoteID')
		self.assertEqual(self.messages[0].index, 42)

		#Sending an invalid message:
		self.messages = []
		c2.send('{"data": "Invalid"}\n')

		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(len(self.messages), 0)

		#Try to make an already open connection (should be ignored):
		self.network.makeConnection(
			('localhost', 4321), 'localID', messages.Pay(ID='remoteID'))
		self.assertEqual(len(self.network.connections), 2)

		#Closing the connection:
		self.network.closeInterface('remoteID')

		self.assertEqual(len(self.network.connections), 1)
		self.assertEqual(self.network.connections[0], c1)
		self.assertFalse(self.network.interfaceExists('remoteID'))
		self.assertTrue(self.network.interfaceExists('localID'))

		self.network.processNetworkEvents(timeout=0.01)

		self.assertFalse(self.network.interfaceExists('localID'))
		self.assertEqual(len(self.network.connections), 0)

		#Closing a no-longer-existing connection (should be fine):
		self.network.closeInterface('localID')

		self.assertEqual(len(self.messages), 0)


	def test_duplicateConnection(self):
		"Test duplicate connection scenario"

		c1 = self.network.makeConnection(
			('localhost', 4321), 'localID', messages.Pay(ID='remoteID'))
		c2 = self.network.makeConnection(
			('localhost', 4321), 'remoteID', messages.Pay(ID='localID'))

		self.assertEqual(len(self.network.connections), 2)
		self.assertTrue(c1 in self.network.connections)
		self.assertTrue(c2 in self.network.connections)
		self.assertTrue(self.network.interfaceExists('localID'))
		self.assertTrue(self.network.interfaceExists('remoteID'))

		self.network.processNetworkEvents(timeout=0.01)
		self.network.processNetworkEvents(timeout=0.01)
		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(len(self.network.connections), 2)
		stillOpen = [c for c in (c1,c2) if c in self.network.connections]
		self.assertEqual(len(stillOpen), 1) #exactly one of the original connections is still open
		self.assertTrue(self.network.interfaceExists('localID'))
		self.assertTrue(self.network.interfaceExists('remoteID'))


	def test_acceptError(self):
		"Test accept error"

		def acceptWithException():
			raise Exception("Unit test exception")
		self.network.listener.accept = acceptWithException

		#Opening a connection:
		c1 = self.network.makeConnection(
			('localhost', 4321), 'localID', messages.Pay(ID='remoteID'))

		#This triggers the handle_accept to be called for the above connection:
		self.network.processNetworkEvents(timeout=0.01)


	def handleMessage(self, msg):
		self.messages.append(msg)



if __name__ == "__main__":
	unittest.main(verbosity=2)

