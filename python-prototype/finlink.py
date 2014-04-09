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
import random

import network
import messages
import event
import settings
import log



class FinLink(event.Handler):
	def __init__(self, context, settingsArg, localID, remoteID):
		event.Handler.__init__(self, context)

		self.localID = localID

		self.localURL = "amikolink://%s/%s" % \
			(settingsArg.getAdvertizedNetworkLocation(), localID)

		self.remoteHost = "localhost" #TODO
		self.remotePort = settings.defaultPort #TODO
		self.remoteID = remoteID

		self.__registerReconnectTimeoutHandler()

		self.connection = None


	def list(self):
		return \
		{
		"localID": self.localID,
		"localURL": self.localURL,
		"remoteID": self.remoteID,
		"isConnected": self.isConnected()
		}


	def connect(self, connection):
		if self.isConnected():
			log.log("Finlink: Received a duplicate connection; closing it")
			connection.close()

		log.log("Finlink: Connection established (received)")
		self.connection = connection
		self.__registerConnectionHandlers()


	def isConnected(self):
		return self.connection != None


	def __registerConnectionHandlers(self):
		event.Handler.connect(self,
			self.connection, event.signals.closed,
			self.__handleConnectionClosed)
		#TODO: other handlers (esp. message available event)


	def __handleConnectionClosed(self):
		log.log("Finlink: Connection is closed")
		self.connection = None

		# Try to reconnect in the future:
		self.__registerReconnectTimeoutHandler()


	def __handleReconnectTimeout(self):
		# Timeout was pointless if we're already connected:
		if self.isConnected():
			return

		log.log("Finlink reconnect timeout: connecting")

		self.connection = network.Connection(self.context,
			(self.remoteHost, self.remotePort))
		self.__registerConnectionHandlers()
		log.log("Finlink: Connection established (created)")

		# Send a link establishment message:
		self.connection.sendMessage(messages.Link(self.remoteID))

		# Register again, in case the above connection fails:
		self.__registerReconnectTimeoutHandler()


	def __registerReconnectTimeoutHandler(self):
		# Use random time-out to prevent repeating connect collisions.
		# This is especially important for the (not so important)
		# loop-back connections.
		timeout = random.uniform(1.0, 2.0)

		self.setTimer(time.time() + timeout, self.__handleReconnectTimeout)


