#    paylink.py
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

from urlparse import urlparse
import threading

import network
import messages
import event



class Payer(event.Handler):
	def __init__(self, context, URL):
		event.Handler.__init__(self, context)

		URL = urlparse(URL)
		self.remoteHost = URL.hostname
		self.remotePort = 4321 if URL.port == None else URL.port
		self.ID = URL.path[1:] #remove initial slash

		print self.remoteHost
		print self.remotePort
		print self.ID

		self.amount = None #unknown
		self.receipt = None #unknown

		# Will be set when receipt message is received from payee
		self.__receiptReceived = threading.Event()

		self.connection = network.Connection(self.context,
			(self.remoteHost, self.remotePort))

		self.connect(self.connection, event.signals.message,
			self.__messageHandler)
		# TODO: register other event handlers
		# TODO: find some way to un-register on close

		self.connection.sendMessage(messages.Pay(self.ID))


	def waitForReceipt(self):
		#TODO: timeout mechanism
		self.__receiptReceived.wait()


	def __messageHandler(self, message):
		if isinstance(message, messages.Receipt):
			if self.amount != None or self.receipt != None:
				raise Exception(
					"Received receipt, while receipt data was already present")
				# TODO: handle protocol error situation

			self.amount = message.amount
			self.receipt = message.receipt
			#TODO: hash
			self.__receiptReceived.set()

		else:
			print "Payer received unknown message: ", message


class Payee(event.Handler):
	def __init__(self, context, ID, amount, receipt):
		event.Handler.__init__(self, context)

		self.ID = ID
		self.amount = amount
		self.receipt = receipt

		self.connection = None


	def connect(self, connection):
		if self.isConnected():
			print "Payee: Received a duplicate connection; closing it"
			connection.close()

		print "Payee: Connection established"
		self.connection = connection
		# TODO: register event handlers

		# Send amount and receipt to payer:
		connection.sendMessage(messages.Receipt(self.amount, self.receipt))


	def isConnected(self):
		return self.connection != None


