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
import transaction
import messages
import event
import utils
import settings
import log



class Payer(event.Handler):
	states = utils.Enum([
		"initial", "hasReceipt", "confirmed", "cancelled", "completed"
		])

	def __init__(self, context, routingContext, URL):
		event.Handler.__init__(self, context)
		self.routingContext = routingContext

		URL = urlparse(URL)
		self.remoteHost = URL.hostname
		self.remotePort = settings.defaultPort if URL.port == None else URL.port
		self.ID = URL.path[1:] #remove initial slash

		self.amount  = None #unknown
		self.receipt = None #unknown
		self.hash    = None #unknown
		self.token   = None #unknown

		self.__meetingPoint = None #unknown
		self.__transaction = None

		# Will be set when receipt message is received from payee
		self.__receiptReceived = threading.Event()

		self.connection = network.Connection(self.context,
			(self.remoteHost, self.remotePort))

		self.connect(self.connection, event.signals.message,
			self.__messageHandler)
		self.connect(self.connection, event.signals.closed,
			self.close)

		self.connection.sendMessage(messages.Pay(self.ID))

		self.state = self.states.initial


	def close(self):
		log.log("Payer side closing")
		self.state = self.states.cancelled #TODO: it depends, actually
		#Important: disconnect BEFORE connection.close, since this method is
		#a signal handler for the connection closed event.
		#Otherwise, it could give an infinite recursion.
		self.disconnectAll()
		self.connection.close()
		self.context.sendSignal(self, event.signals.closed)


	def waitForReceipt(self):
		#TODO: timeout mechanism
		self.__receiptReceived.wait()


	def confirmPayment(self, payerAgrees):
		if self.state != self.states.hasReceipt:
			raise Exception(
				"confirmPayment should not be called in state %s" % \
					self.state
				)

		if payerAgrees:
			self.connection.sendMessage(
				messages.String("OK:" + self.__meetingPoint))

			#This will start the transaction routing
			self.__transaction = transaction.Transaction(
				self.context, self.routingContext,
				self.amount, self.hash, self.__meetingPoint,
				payerLink=self)

			self.state = self.states.confirmed
		else:
			self.connection.sendMessage(messages.String("NOK"))
			self.close()
			self.state = self.states.cancelled


	def __messageHandler(self, message):
		situation = (self.state, message.__class__)

		if situation == (self.states.initial, messages.Receipt):

			self.amount = message.amount
			self.receipt = message.receipt
			self.hash = message.hash

			# for now, always select the first suggested meeting point.
			# Will automatically give an exception if 0 meeting points are given
			self.__meetingPoint = message.meetingPoints[0]

			self.state = self.states.hasReceipt
			self.__receiptReceived.set()

		else:
			log.log("Payer received unsupported message for state %s: %s" % \
				(self.state, message))
			self.close()



class Payee(event.Handler):
	states = utils.Enum([
		"initial", "confirmed", "cancelled", "completed"
		])

	def __init__(self, context, routingContext, ID, amount, receipt, token):
		event.Handler.__init__(self, context)
		self.routingContext = routingContext

		self.ID = ID
		self.amount = amount
		self.receipt = receipt
		self.token = token
		self.hash = settings.hashAlgorithm(self.token)

		self.__meetingPoint = None #unknown
		self.__transaction = None

		self.connection = None

		self.state = self.states.initial


	def list(self):
		return \
		{
		"ID": self.ID,
		"amount": self.amount,
		"receipt": self.receipt,
		"hash": self.hash,
		"meetingPoint": self.__meetingPoint,
		"isConnected": self.isConnected(),
		"state": self.state
		}


	def close(self):
		log.log("Payee side closing")
		self.state = self.states.cancelled #TODO: it depends, actually
		#Important: disconnect BEFORE connection.close, since this method is
		#a signal handler for the connection closed event.
		#Otherwise, it could give an infinite recursion.
		self.disconnectAll()
		if self.isConnected():
			self.connection.close()
			self.connection = None
		self.context.sendSignal(self, event.signals.closed)


	def connect(self, connection):
		if self.isConnected():
			log.log("Payee: Received a duplicate connection; closing it")
			connection.close()
			return

		log.log("Payee: Connection established")
		self.connection = connection

		event.Handler.connect(self, self.connection, event.signals.message,
			self.__messageHandler)
		event.Handler.connect(self, self.connection, event.signals.closed,
			self.close)

		meetingPoints = [mp.ID for mp in self.routingContext.meetingPoints]
		#TODO: add accepted external meeting points

		# Send amount, receipt and meeting points to payer:
		connection.sendMessage(messages.Receipt(
			self.amount, self.receipt, self.hash, meetingPoints))


	def isConnected(self):
		return self.connection != None


	def __messageHandler(self, message):
		situation = (self.state, message.__class__)

		if situation == (self.states.initial, messages.String):
			if message.value == "NOK":
				log.log("Payee received NOK")
				self.close()
				self.state = self.states.cancelled
			elif message.value[:3] == "OK:":
				self.__meetingPoint = message.value[3:]
				#TODO: check that meeting point is in self.meetingPoints

				#This will start the transaction routing
				self.__transaction = transaction.Transaction(
					self.context, self.routingContext,
					self.amount, self.hash, self.__meetingPoint,
					payeeLink=self)

				self.state = self.states.confirmed
				log.log("Payee received OK: " + self.__meetingPoint)

			else:
				log.log("Payee received invalid confirmation string")
				self.close()

		else:
			log.log("Payee received unsupported message for state %s: %s" % \
				(self.state, message))
			self.close()


