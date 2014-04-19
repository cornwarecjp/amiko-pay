#    link.py
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

import random
from urlparse import urlparse

import network
import messages
import event
import settings
import log
import transaction
import paymentchannel



class Link(event.Handler):
	def __init__(self, context, routingContext, settingsArg, state):
		event.Handler.__init__(self, context)
		self.routingContext = routingContext

		self.localID  = str(state["localID"])
		self.remoteID = str(state["remoteID"])

		self.localURL = "amikolink://%s/%s" % \
			(settingsArg.getAdvertizedNetworkLocation(), self.localID)
		self.remoteURL = str(state["remoteURL"])

		self.openTransactions = {} #hash->transaction

		self.paymentChannel = paymentchannel.PaymentChannel(state["channel"])

		self.__registerReconnectTimeoutHandler()

		self.connection = None


	def list(self):
		return \
		{
		"localID": self.localID,
		"localURL": self.localURL,
		"remoteID": self.remoteID,
		"remoteURL": self.remoteURL,
		"isConnected": self.isConnected(),
		"channel": self.paymentChannel.list()
		}


	def getBalance(self):
		return self.paymentChannel.amountLocal


	def connect(self, connection):
		if self.isConnected():
			log.log("Link: Received a duplicate connection; closing it")
			connection.close()

		log.log("Link: Connection established (received)")
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
		log.log("Link: Connection is closed")
		self.connection = None

		# Try to reconnect in the future:
		self.__registerReconnectTimeoutHandler()


	def __handleReconnectTimeout(self):
		# Timeout was pointless if we're already connected:
		if self.isConnected():
			return

		log.log("Link reconnect timeout: connecting")

		URL = urlparse(self.remoteURL)
		remoteHost = URL.hostname
		remotePort = settings.defaultPort if URL.port == None else URL.port
		#TODO: maybe read and check remoteID in URL?
		#Or maybe remove redundancy between remoteID and remoteURL.

		try:
			self.connection = network.Connection(self.context,
				(remoteHost, remotePort))
			self.__registerConnectionHandlers()
			log.log("Link: Connection established (created)")

			# Send a link establishment message:
			self.connection.sendMessage(messages.Link(self.remoteID))

			# Send URLs
			self.connection.sendMessage(messages.MyURLs([self.localURL]))
		except:
			#TODO: log entire exception
			log.log("Link: Connection creation failed")

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

		self.setTimer(timeout, self.__handleReconnectTimeout)


	def msg_makeRoute(self, transaction):
		log.log("Link: makeRoute")

		try:

			if not self.isConnected():
				raise paymentchannel.CheckFail("Not connected")

			#TODO: do all sorts of checks to see if it makes sense to perform
			#the transaction over this link.
			#For instance, check the responsiveness of the other side, etc. etc.

			#This will check whether enough funds are availbale
			self.paymentChannel.reserve(
				transaction.isPayerSide(), transaction.hash, transaction.amount)

			#Remember link to transaction object:
			self.openTransactions[transaction.hash] = transaction

			#Send message:
			self.connection.sendMessage(messages.MakeRoute(
				transaction.amount,
				transaction.isPayerSide(),
				transaction.hash,
				transaction.meetingPoint))

		except paymentchannel.CheckFail as f:
			log.log("Route refused by link: " + str(f))

			#Send back a cancel immediately
			transaction.msg_cancelRoute()


	def msg_haveRoute(self, transaction):
		log.log("Link: haveRoute")
		#TODO: check whether we're still connected
		self.connection.sendMessage(messages.HaveRoute(transaction.hash))


	def msg_lock(self, transaction):
		log.log("Link: lock")
		#TODO: check whether we're still connected
		self.paymentChannel.lockOutgoing(transaction.hash)
		#TODO: get new Bitcoin transaction from paymentChannel and
		# include it in the lock message
		self.connection.sendMessage(messages.Lock(transaction.hash))


	def msg_commit(self, transaction):
		log.log("Link: commit")
		#TODO: check whether we're still connected
		self.paymentChannel.commitOutgoing(transaction.hash)
		#TODO: get new Bitcoin transaction from paymentChannel and
		# include it in the lock message
		self.connection.sendMessage(messages.Commit(transaction.token))


	def __handleMessage(self, message):
		#log.log("Link received message: " + repr(str()))

		if message.__class__ == messages.MyURLs:
			#TODO: check URLs for validity etc.
			#TODO: support multiple remote URLs (for now, just pick the first)
			self.remoteURL = message.getURLs()[0]

		elif message.__class__ == messages.MakeRoute:
			log.log("Link received MakeRoute")

			try:
				#TODO: do all sorts of checks to see if it makes sense to perform
				#the transaction over this link.
				#For instance, check the responsiveness of the other side, etc. etc.

				#This will check whether enough funds are availbale
				#Note: if we're on the PAYER side of the meeting point,
				#then we're on the PAYEE side of this link, for this transaction.
				self.paymentChannel.reserve(
					not message.isPayerSide, message.hash, message.amount)

				#TODO: exception handling for the above

			except paymentchannel.CheckFail as f:
				log.log("Route refused by link: " + str(f))

				#Send back a cancel immediately
				#TODO

				return

			#This will start the transaction routing
			if message.isPayerSide:
				self.openTransactions[message.hash] = transaction.Transaction(
					self.context, self.routingContext,
					message.amount, message.hash, message.meetingPoint,
					payerLink=self)
			else:
				self.openTransactions[message.hash] = transaction.Transaction(
					self.context, self.routingContext,
					message.amount, message.hash, message.meetingPoint,
					payeeLink=self)

		elif message.__class__ == messages.HaveRoute:
			log.log("Link received HaveRoute")
			self.openTransactions[message.value].msg_haveRoute(self)

		elif message.__class__ == messages.Lock:
			log.log("Link received Lock")

			#TODO: get new Bitcoin transaction from message and
			# pass it to paymentChannel
			self.paymentChannel.lockIncoming(message.value)
			#TODO: exception handling for the above

			self.openTransactions[message.value].msg_lock()

		elif message.__class__ == messages.Commit:
			log.log("Link received Commit")
			token = message.value
			hash = settings.hashAlgorithm(token)

			#TODO: get new Bitcoin transaction from message and
			# pass it to paymentChannel
			self.paymentChannel.commitIncoming(hash)
			#TODO: exception handling for the above

			self.openTransactions[hash].msg_commit(token)

		else:
			log.log("Link received unsupported message: %s" % str(message))


