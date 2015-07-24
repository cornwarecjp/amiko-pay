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


	def test_connectionSession(self):
		"Test connection session"

		#Opening the connection:
		c1 = self.network.makeConnection(('localhost', 4321), 'localID')

		self.assertEqual(c1.localID, 'localID')
		self.assertEqual(len(self.network.connections), 1)
		self.assertEqual(self.network.connections[0], c1)
		self.assertEqual(self.network.getInterface('localID'), c1)
		self.assertTrue(self.network.interfaceExists('localID'))

		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(len(self.network.connections), 2)
		c2 = self.network.connections[1]
		self.assertEqual(c2.localID, None)

		#Sending a connect message:
		self.network.sendOutboundMessage(0, messages.OutboundMessage(
			localID='localID',
			message=messages.Pay(ID='remoteID')))

		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(c2.localID, 'remoteID')
		self.assertTrue(self.network.interfaceExists('remoteID'))

		#Sending another connect message (illegal):
		self.network.sendOutboundMessage(0, messages.OutboundMessage(
			localID='localID',
			message=messages.Pay(ID='remoteID2')))

		self.network.processNetworkEvents(timeout=0.01)

		self.assertEqual(c2.localID, 'remoteID') #unchanged

		#Sending another message back:
		self.network.sendOutboundMessage(0, messages.OutboundMessage(
			localID='remoteID',
			message=messages.Cancel(ID=None)))

		self.network.processNetworkEvents(timeout=0.01) #sends the confirmation
		self.network.processNetworkEvents(timeout=0.01) #receives the confirmation

		#Sending an invalid message:
		c2.send('{"data": "Invalid"}\n')

		self.network.processNetworkEvents(timeout=0.01)

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


	def handleMessage(self, msg):
		pass #TODO



if __name__ == "__main__":
	unittest.main(verbosity=2)

