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

import random
from urlparse import urlparse

import network
import messages
import event
import settings
import log
import transaction
import channel
from ..channels import multisigchannel



class Link(event.Handler):
	def __init__(self, context, routingContext, bitcoind, settingsArg, state):
		event.Handler.__init__(self, context)
		self.routingContext = routingContext
		self.bitcoind = bitcoind

		self.acceptedEscrowKeys = settingsArg.acceptedEscrowKeys

		self.name  = str(state["name"])
		self.localID  = str(state["localID"])
		self.remoteID = str(state["remoteID"])

		self.localURL = "amikolink://%s/%s" % \
			(settingsArg.getAdvertizedNetworkLocation(), self.localID)
		self.remoteURL = str(state["remoteURL"])

		self.openTransactions = {} #hash->transaction

		self.channels = []
		for c in state["channels"]:
			if c["type"] == "plain":
				self.channels.append(
					channel.Channel(c)
					)
			elif c["type"] == "multisig":
				self.channels.append(
					multisigchannel.MultiSigChannel(self.bitcoind, c)
					)
			else:
				raise Exception("Unrecognized channel type \"%s\"" % \
					c["type"])

		self.connection = None
		self.dice = random.randint(0, 0xffffffff) #for connect collision decision

		#After the time-out, we'll try to establish a connection.
		#The reason for not connecting immediately is that, in the case of a
		#link to self (useful for testing), the listener may still be inactive.
		self.__registerReconnectTimeoutHandler(timeout=0.1)


	def getState(self, forDisplay=False):
		ret = \
		{
		"name": self.name,
		"localID": self.localID,
		"remoteID": self.remoteID,
		"remoteURL": self.remoteURL,
		"channels": [c.getState(forDisplay) for c in self.channels],
		"openTransactions":
			[k.encode("hex") for k in self.openTransactions.keys()]
		}
		if forDisplay:
			ret["isConnected"] = self.isConnected()
			ret["localURL"] = self.localURL
		return ret


	def getBalance(self):
		return \
		{
			"availableForSpending": sum(c.amountLocal for c in self.channels),
			"availableForReceiving": sum(c.amountRemote for c in self.channels)
		}


	def deposit(self, amount, escrowKey):
		if not self.isConnected():
			raise Exception("Not connected")

		try:
			newID = 1 + max(c.ID for c in self.channels)
		except ValueError:
			newID = 0

		newChannel = multisigchannel.constructFromDeposit(
			self.bitcoind, newID, amount, escrowKey)
		self.channels.append(newChannel)
		self.connection.sendMessage(newChannel.makeDepositMessage(None))
		self.context.sendSignal(None, event.signals.save)


	def withdraw(self, channelID):
		if not self.isConnected():
			raise Exception("Not connected")

		existingIDs = [c.ID for c in self.channels]
		if channelID not in existingIDs:
			raise Exception("Channel ID does not exist")

		channel = self.channels[existingIDs.index(channelID)]
		msg = channel.makeWithdrawMessage(None)
		if msg != None:
			self.connection.sendMessage(msg)
		self.context.sendSignal(None, event.signals.save)


	def connect(self, connection, message):
		if self.isConnected():
			if message.dice > self.dice:
				log.log("Link: Received a duplicate connection with larger dice value; closing own connection")
				self.connection.close()
				#Fall-through: accept the new connection
			elif message.dice < self.dice:
				log.log("Link: Received a duplicate connection with smaller dice value; closing it")
				connection.close()
				return
			else:
				#Note: this is very unlikely (1 in every 2**32 times)
				log.log("Link: Received a duplicate connection with equal dice value; closing it")
				#Choose new dice value:
				self.dice = random.randint(0, 0xffffffff)
				connection.close()
				return

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
			self.connection.sendMessage(messages.Link(self.remoteID, self.dice))

			# Send URLs
			self.connection.sendMessage(messages.MyURLs([self.localURL]))
		except:
			log.log("Link: Connection creation failed:")
			log.logException()

			if self.connection != None:
				self.connection.close()
				self.connection = None

			# Register again, to retry in the future:
			self.__registerReconnectTimeoutHandler()


	def __registerReconnectTimeoutHandler(self, timeout=10.0):

		#Reconnect doesn't make sense if we don't know where to connect to
		if self.remoteURL == "":
			return

		self.setTimer(timeout, self.__handleReconnectTimeout)
		log.log("Link: set reconnect timeout to %f s" % timeout)


	def msg_makeRoute(self, transaction):
		log.log("Link: makeRoute")

		try:

			if not self.isConnected():
				raise channel.CheckFail("Not connected")

			#TODO: do all sorts of checks to see if it makes sense to perform
			#the transaction over this link.
			#For instance, check the responsiveness of the other side, etc. etc.

			#This will check whether enough funds are availbale
			#TODO: use multiple channels
			self.channels[0].reserve(
				transaction.isPayerSide(), transaction.hash, transaction.amount)

			#Remember link to transaction object:
			self.openTransactions[transaction.hash] = transaction

			#Send message:
			self.connection.sendMessage(messages.MakeRoute(
				transaction.amount,
				transaction.isPayerSide(),
				transaction.hash,
				transaction.meetingPoint))

		except channel.CheckFail as f:
			log.log("Route refused by link: " + str(f))

			#Send back a cancel immediately
			transaction.msg_cancelRoute()


	#TODO: msg_cancelRoute handling


	def msg_haveRoute(self, transaction):
		log.log("Link: haveRoute")
		#TODO: check whether we're still connected
		self.connection.sendMessage(messages.HaveRoute(transaction.hash))


	def msg_lock(self, transaction):
		log.log("Link: lock")
		#TODO: check whether we're still connected
		#TODO: use multiple channels
		message = self.channels[0].lockOutgoing(transaction.hash)

		self.context.sendSignal(None, event.signals.save)

		self.connection.sendMessage(message)


	def msg_commit(self, transaction):
		log.log("Link: commit")
		#TODO: check whether we're still connected
		#TODO: use multiple channels
		message = self.channels[0].commitOutgoing(transaction.hash, transaction.token)

		self.context.sendSignal(None, event.signals.save)

		self.connection.sendMessage(message)

		#We don't need this anymore:
		del self.openTransactions[transaction.hash]


	def __handleMessage(self, message):
		#log.log("Link received message: " + repr(str()))

		if message.__class__ == messages.MyURLs:
			#TODO: check URLs for validity etc.
			#TODO: support multiple remote URLs (for now, just pick the first)
			remoteURL = message.getURLs()[0]
			URL = urlparse(remoteURL)

			oldRemoteID = self.remoteID
			oldRemoteURL = self.remoteURL

			self.remoteID = URL.path[1:]
			self.remoteURL = remoteURL

			if oldRemoteID != self.remoteID or oldRemoteURL != self.remoteURL:
				self.context.sendSignal(None, event.signals.save)

		elif message.__class__ == messages.MakeRoute:
			log.log("Link received MakeRoute")

			try:
				#TODO: do all sorts of checks to see if it makes sense to perform
				#the transaction over this link.
				#For instance, check the responsiveness of the other side, etc. etc.

				#This will check whether enough funds are availbale
				#Note: if we're on the PAYER side of the meeting point,
				#then we're on the PAYEE side of this link, for this transaction.
				#TODO: use multiple channels
				self.channels[0].reserve(
					not message.isPayerSide, message.hash, message.amount)

				#TODO: exception handling for the above

			except channel.CheckFail as f:
				log.log("Route refused by link: " + str(f))

				#Send back a cancel immediately
				#TODO

				return

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

			#This will start the transaction routing
			self.openTransactions[message.hash].msg_makeRoute()

		elif message.__class__ == messages.HaveRoute:
			log.log("Link received HaveRoute")
			self.openTransactions[message.value].msg_haveRoute(self)

		elif message.__class__ == messages.Lock:
			log.log("Link received Lock")

			#TODO: use multiple channels
			self.channels[0].lockIncoming(message)
			#TODO: exception handling for the above

			self.context.sendSignal(None, event.signals.save)

			self.openTransactions[message.hash].msg_lock()

		elif message.__class__ == messages.Commit:
			log.log("Link received Commit")
			token = message.token
			hash = settings.hashAlgorithm(token)

			#TODO: use multiple channels
			self.channels[0].commitIncoming(hash, message)
			#TODO: exception handling for the above

			self.context.sendSignal(None, event.signals.save)

			self.openTransactions[hash].msg_commit(token)

			#We don't need this anymore:
			del self.openTransactions[hash]

		elif message.__class__ == messages.Deposit:
			log.log("Link received Deposit")

			existingIDs = [c.ID for c in self.channels]

			if message.isInitial:
				if message.channelID in existingIDs:
					log.log("Initial deposit message contains already existing channel ID")
					#TODO: send refusal reply?
				elif message.type not in ["multisig"]:
					log.log("Initial deposit message with unsupported channel type")
					#TODO: send refusal reply?
				else:
					newChannel = multisigchannel.constructFromDepositMessage(
						self.bitcoind, message)
					self.channels.append(newChannel)
					reply = newChannel.makeDepositMessage(message)
					if reply != None:
						self.connection.sendMessage(reply)
					self.context.sendSignal(None, event.signals.save)
			else:
				try:
					channel = self.channels[existingIDs.index(message.channelID)]
					reply = channel.makeDepositMessage(message)
					if reply != None:
						self.connection.sendMessage(reply)
					self.context.sendSignal(None, event.signals.save)
				except ValueError:
					log.log("Follow-up deposit message contains non-existing channel ID")
					#TODO: send refusal reply?

		elif message.__class__ == messages.Withdraw:
			log.log("Link received Withdraw")

			existingIDs = [c.ID for c in self.channels]

			try:
				channel = self.channels[existingIDs.index(message.channelID)]
				reply = channel.makeWithdrawMessage(message)
				if reply != None:
					self.connection.sendMessage(reply)
				self.context.sendSignal(None, event.signals.save)
			except ValueError:
				log.log("Withdraw message contains non-existing channel ID")
				#TODO: send refusal reply?

		else:
			log.log("Link received unsupported message: %s" % str(message))


