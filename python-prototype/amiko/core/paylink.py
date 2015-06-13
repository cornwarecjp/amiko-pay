#    paylink.py
#    Copyright (C) 2014-2015 by CJP
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

from urlparse import urlparse
import threading

from ..utils import utils

import network
import transaction
import messages
import event
import settings
import log



class Payer(event.Handler):
	states = utils.Enum([
		"initial", "hasReceipt", "confirmed", "hasRoute",
		"locked", "cancelled", "committed"
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

		# Will be set when transaction is committed or cancelled
		self.__finished = threading.Event()

		self.state = self.states.initial

		self.connection = network.Connection(self.context,
			(self.remoteHost, self.remotePort))

		self.connect(self.connection, event.signals.message,
			self.__handleMessage)
		self.connect(self.connection, event.signals.closed,
			self.close)

		self.connection.sendMessage(messages.Pay(self.ID))


	def close(self):
		log.log("Payer side closing")

		#1: adjust own state
		#If locked, it can still become committed
		if self.state not in [self.states.locked, self.states.committed]:
			self.state = self.states.cancelled

		#Important: disconnect BEFORE connection.close, since this method is
		#a signal handler for the connection closed event.
		#Otherwise, it could give an infinite recursion.
		self.disconnectAll()

		#2: network traffic
		self.connection.close()
		self.context.sendSignal(self, event.signals.closed)

		#3: internal messaging
		#TODO

		#Inform waiting thread(s) that the transaction is finished (cancelled)
		self.__finished.set()


	def waitForReceipt(self):
		#TODO: timeout mechanism
		self.__receiptReceived.wait()


	def waitForFinished(self):
		#TODO: timeout mechanism
		self.__finished.wait()


	def confirmPayment(self, payerAgrees):
		if self.state != self.states.hasReceipt:
			raise Exception(
				"confirmPayment should not be called in state %s" % \
					self.state
				)

		if payerAgrees:
			#1: adjust own state
			self.state = self.states.confirmed

			#2: network traffic
			self.connection.sendMessage(
				messages.Confirm(self.__meetingPoint))

			#3: internal messaging
			#Note: we don't fill in timestamp values - they will be received
			#from the payee side.
			self.__transaction = transaction.Transaction(
				self.context, self.routingContext, self.__meetingPoint,
				self.amount, self.hash,
				payerLink=self)

			#This will start the transaction routing
			self.__transaction.msg_makeRoute()

		else:
			#1: adjust own state
			self.state = self.states.cancelled

			#2: network traffic
			self.connection.sendMessage(messages.Cancel())
			self.close()


	def msg_haveRoute(self, transaction):
		log.log("Payer: haveRoute")
		#1: adjust own state
		self.state = self.states.hasRoute
		#2: network traffic
		self.connection.sendMessage(messages.HaveRoute())


	def msg_cancel(self, transaction):
		log.log("Payer: cancel")
		#1: adjust own state
		self.state = self.states.cancelled
		#2: network traffic
		self.connection.sendMessage(messages.Cancel())
		#Inform waiting thread(s) that the transaction is finished (cancelled)
		self.__finished.set()


	def msg_requestCommit(self, transaction):
		log.log("Payer: requestCommit")

		#TODO: maybe check validity of payment token
		#TODO: do we need to do anything else here?
		self.token = transaction.token


	def __handleMessage(self, message):
		situation = (self.state, message.__class__)

		if situation == (self.states.initial, messages.Receipt):

			#1: adjust own state
			self.amount = message.amount
			self.receipt = message.receipt
			self.hash = message.hash

			# for now, always select the first suggested meeting point.
			# Will automatically give an exception if 0 meeting points are given
			self.__meetingPoint = message.meetingPoints[0]

			self.state = self.states.hasReceipt

			#Inform waiting thread(s) that the receipt is received
			self.__receiptReceived.set()

		elif situation == (self.states.hasRoute, messages.HaveRoute):
			log.log("Payer: both routes exist")
			#1: adjust own state
			self.state = self.states.locked
			#3: internal messaging
			self.__transaction.msg_lock()

		elif situation == (self.states.locked, messages.Commit):
			#TODO: check that token matches hash (IMPORTANT)
			log.log("Payer: commit")
			#1: adjust own state
			self.token = message.token
			self.state = self.states.committed
			#2: network traffic
			#close connection
			self.close()
			#3: internal messaging
			self.__transaction.msg_commit(self.token)
			#Inform waiting thread(s) that the transaction is finished (committed)
			self.__finished.set()

		else:
			log.log("Payer received unsupported message for state %s: %s" % \
				(self.state, message))
			self.close()



class Payee(event.Handler):
	states = utils.Enum([
		"initial", "confirmed", "hasRoutes", "sentCommit", "cancelled", "committed"
		])

	def __init__(self, context, routingContext, ID, amount, receipt, token, suggestedMeetingPoints):
		event.Handler.__init__(self, context)
		self.routingContext = routingContext

		self.ID = ID
		self.amount = amount
		self.receipt = receipt
		self.token = token
		self.hash = settings.hashAlgorithm(self.token)
		self.suggestedMeetingPoints = suggestedMeetingPoints

		self.__meetingPoint = None #unknown
		self.__transaction = None

		self.connection = None

		self.state = self.states.initial
		self.__payerHasRoute = False
		self.__payeeHasRoute = False


	def getState(self, forDisplay=False):
		ret = \
		{
		"ID": self.ID,
		"amount": self.amount,
		"receipt": self.receipt,
		"hash": self.hash.encode("hex"),
		"state": self.state
		}
		if forDisplay:
			ret["meetingPoint"] =  self.__meetingPoint
			ret["isConnected"] = self.isConnected()

		return ret


	def close(self):
		log.log("Payee side closing")

		#1: adjust own state
		#If sent commit, it can still become committed
		if self.state not in [self.states.sentCommit, self.states.committed]:
			self.state = self.states.cancelled

		#Important: disconnect BEFORE connection.close, since this method is
		#a signal handler for the connection closed event.
		#Otherwise, it could give an infinite recursion.
		self.disconnectAll()

		#2: network traffic
		if self.isConnected():
			self.connection.close()
			self.connection = None

		#3: internal messaging
		#TODO

		self.context.sendSignal(self, event.signals.closed)


	def connect(self, connection):
		if self.isConnected():
			log.log("Payee: Received a duplicate connection; closing it")
			connection.close()
			return

		log.log("Payee: Connection established")

		#1: adjust own state
		self.connection = connection

		event.Handler.connect(self, self.connection, event.signals.message,
			self.__handleMessage)
		event.Handler.connect(self, self.connection, event.signals.closed,
			self.close)

		#2: network traffic
		# Send amount, receipt and meeting points to payer:
		connection.sendMessage(messages.Receipt(
			self.amount, self.receipt, self.hash, self.suggestedMeetingPoints))


	def isConnected(self):
		return self.connection != None


	def msg_haveRoute(self, transaction):
		log.log("Payee: haveRoute")
		#1: adjust own state
		self.__payeeHasRoute = True
		#2: network traffic
		self.__checkRoutesAndConfirmToPayer()


	def msg_lock(self, transaction):
		log.log("Payee: locked; committing the transaction")
		#1: adjust own state
		self.state = self.states.sentCommit
		#2: network traffic
		self.connection.sendMessage(messages.Commit(token=self.token))
		#3: internal messaging
		transaction.msg_requestCommit(self.token)


	def msg_commit(self, transaction):
		log.log("Payee: commit")
		#1: adjust own state
		self.state = self.states.committed
		# Hooray, we've committed the transaction!
		#TODO: close connection


	def __handleMessage(self, message):
		situation = (self.state, message.__class__)

		if situation == (self.states.initial, messages.Confirm):
			self.__meetingPoint = message.value
			log.log("Payee received confirm: " + self.__meetingPoint)

			#TODO: check that meeting point is in self.meetingPoints

			#1: adjust own state
			self.state = self.states.confirmed

			#3: internal messaging
			#TODO: timestamp values
			self.__transaction = transaction.Transaction(
				self.context, self.routingContext, self.__meetingPoint,
				self.amount, self.hash, 0, 0,
				payeeLink=self)

			#This will start the transaction routing
			self.__transaction.msg_makeRoute()

		elif situation == (self.states.initial, messages.Cancel):
			log.log("Payee received cancel")
			#1: adjust own state
			self.state = self.states.cancelled
			#2: network traffic
			self.close()

		elif situation == (self.states.confirmed, messages.HaveRoute):
			#1: adjust own state
			self.__payerHasRoute = True
			#2: network traffic
			self.__checkRoutesAndConfirmToPayer()

		elif situation == (self.states.confirmed, messages.Cancel):
			log.log("Payee received cancel after confirm")
			#1: adjust own state
			self.state = self.states.cancelled
			#2: network traffic
			self.close()
			#3: internal messaging
			self.__transaction.msg_endRoute()

		else:
			log.log("Payee received unsupported message for state %s: %s" % \
				(self.state, message))
			self.close()


	def __checkRoutesAndConfirmToPayer(self):
		if self.__payeeHasRoute and self.__payerHasRoute:
			log.log("Payee: both routes exist")
			#1: adjust own state
			self.state = self.states.hasRoutes
			#2: network traffic
			self.connection.sendMessage(messages.HaveRoute())


