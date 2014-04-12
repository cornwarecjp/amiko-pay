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
from urlparse import urlparse

import network
import messages
import event
import settings
import log



class FinLink(event.Handler):
	def __init__(self, context, settingsArg, state):
		event.Handler.__init__(self, context)

		self.localID  = str(state["localID"])
		self.remoteID = str(state["remoteID"])

		self.localURL = "amikolink://%s/%s" % \
			(settingsArg.getAdvertizedNetworkLocation(), self.localID)
		self.remoteURL = str(state["remoteURL"])

		self.__registerReconnectTimeoutHandler()

		self.connection = None


	def list(self):
		return \
		{
		"localID": self.localID,
		"localURL": self.localURL,
		"remoteID": self.remoteID,
		"remoteURL": self.remoteURL,
		"isConnected": self.isConnected()
		}


	def connect(self, connection):
		if self.isConnected():
			log.log("Finlink: Received a duplicate connection; closing it")
			connection.close()

		log.log("Finlink: Connection established (received)")
		self.connection = connection
		self.__registerConnectionHandlers()

		# Send URLs
		self.connection.sendMessage(messages.MyURLs([self.localURL]))


	def isConnected(self):
		return self.connection != None


	def __registerConnectionHandlers(self):
		event.Handler.connect(self,
			self.connection, event.signals.closed,
			self.__handleConnectionClosed)
		event.Handler.connect(self,
			self.connection, event.signals.message,
			self.__handleMessage)


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

		URL = urlparse(self.remoteURL)
		remoteHost = URL.hostname
		remotePort = settings.defaultPort if URL.port == None else URL.port
		#TODO: maybe read and check remoteID in URL?
		#Or maybe remove redundancy between remoteID and remoteURL.

		try:
			self.connection = network.Connection(self.context,
				(remoteHost, remotePort))
			self.__registerConnectionHandlers()
			log.log("Finlink: Connection established (created)")

			# Send a link establishment message:
			self.connection.sendMessage(messages.Link(self.remoteID))

			# Send URLs
			self.connection.sendMessage(messages.MyURLs([self.localURL]))
		except:
			#TODO: log entire exception
			log.log("Finlink: Connection creation failed")

			if self.connection != None:
				self.connection.close()
				self.connection = None

			# Register again, to retry in the future:
			self.__registerReconnectTimeoutHandler()


	def __registerReconnectTimeoutHandler(self):

		#Reconnect doesn't make sense if we don't know where to connect to
		if self.remoteURL == "":
			return

		# Use random time-out to prevent repeating connect collisions.
		# This is especially important for the (not so important)
		# loop-back connections.
		timeout = random.uniform(1.0, 2.0)

		self.setTimer(time.time() + timeout, self.__handleReconnectTimeout)


	def __handleMessage(self, message):
		#log.log("FinLink received message: " + repr(str()))

		if message.__class__ == messages.MyURLs:
			#TODO: check URLs for validity etc.
			#TODO: support multiple remote URLs (for now, just pick the first)
			self.remoteURL = message.getURLs()[0]


