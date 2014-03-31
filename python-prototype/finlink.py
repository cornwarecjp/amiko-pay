#    finlink.py
#    Copyright (C) 2014 by CJP
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

import time

import network
import messages



class FinLink:
	def __init__(self, context, localID, remoteID):
		self.context = context

		self.localID = localID

		self.remoteHost = "localhost" #TODO
		self.remotePort = 4321 #TODO
		self.remoteID = remoteID

		self.context.setTimer(time.time() + 1.0, self.handleReconnectTimeout)

		self.connection = None


	def connect(self, connection):
		if self.isConnected():
			print "Received a duplicate connection; closing it"
			connection.close()

		print "Connection established"
		self.connection = connection
		#TODO: connect signals


	def isConnected(self):
		return self.connection != None


	def handleReconnectTimeout(self):
		# Timeout was pointless if we're already connected:
		if self.isConnected():
			return

		print "Finlink reconnect timeout: connecting"

		self.connection = network.Connection(self.context,
			(self.remoteHost, self.remotePort))

		# Send a link establishment message:
		self.connection.sendMessage(messages.Link(self.remoteID))

		# Register again, in case the above connection fails:
		self.context.setTimer(time.time() + 1.0, self.handleReconnectTimeout)


