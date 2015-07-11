#    node.py
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


import threading
from urlparse import urlparse
import asyncore
import socket
import os
import time

from core import log
from core import network
from core import nodestate
from core import outbox
from core import payerlink
from core import payeelink
from core import paylog
from core import serializable
from core import settings



#Somehow it is hard to replace the above copyright information with a more
#sensible doc string...
__doc__ = """
Top-level Application Programming Interface for the Amiko payment system
"""

version = "0.1.0 (unstable,development)"
lastCopyrightYear = "2015"



def runInNodeThread(implementationFunc):
	"""
	Function decorator, which can be used by Node methods to have them
	called by an external thread, but have them run inside the internal thread
	of the Node object.

	Intended for internal use by Node.
	Not intended to be part of the API.
	"""

	def remoteCaller(self, *args, **kwargs):
		with self._commandFunctionLock:
			self._commandFunction = (implementationFunc, args, kwargs)
			self._commandProcessed.clear()
		self._commandProcessed.wait()

		if isinstance(self._commandReturnValue, Exception):
			raise self._commandReturnValue
		return self._commandReturnValue

	remoteCaller.__doc__ = implementationFunc.__doc__

	return remoteCaller



class Node(threading.Thread):
	"""
	A single Amiko node.

	A process can run multiple Amiko nodes by making multiple instances of
	this class. Each instance can have its own configuration, and runs in its
	own thread.

	After creating an instance, it can be started with the start() method.

	To stop the node, the stop() method must be called. This should always be
	done before program termination.
	"""

	def __init__(self, conf="amikopay.conf"):
		"""
		Constructor.

		Arguments:
		conf: Name of the configuration file to be loaded, or a
		      settings.Settings instance
		"""

		threading.Thread.__init__(self)

		if isinstance(conf, settings.Settings):
			self.settings = conf
		else:
			self.settings = settings.Settings(conf)

		self.networkEventDispatcher = network.EventDispatcher(
			self.settings.listenHost, self.settings.listenPort, callback=self)

		#self.bitcoind = bitcoind.Bitcoind(self.settings)

		self.payLog = paylog.PayLog(self.settings)

		self.__stop = False

		self._commandFunctionLock = threading.Lock()
		self._commandFunction = None
		self._commandProcessed = threading.Event()
		self._commandReturnValue = None

		self.__loadState()


	def __loadState(self):

		oldFile = self.settings.stateFile + ".old"
		if os.access(oldFile, os.F_OK):
			if os.access(self.settings.stateFile, os.F_OK):
				#Remove old file if normal state file exists:
				os.remove(oldFile)
			else:
				#Use old file if state file does not exist:
				os.rename(oldFile, self.settings.stateFile)

		try:
			with open(self.settings.stateFile, 'rb') as fp:
				stateData = fp.read()

			self.setState(serializable.deserializeState(stateData))

		except IOError:
			log.log("Failed to load from %s" % self.settings.stateFile)
			log.log("Starting with empty state")

			#Create a new, empty state:
			self.__node = nodestate.NodeState()
			self.__timeoutMessages = []
			self.__outBox = outbox.OutBox()

			#Store the newly created state
			self.__saveState()


	def __saveState(self):
		stateData = serializable.serializeState(self.getState())

		newFile = self.settings.stateFile + ".new"
		log.log("Saving in " + newFile)
		with open(newFile, 'wb') as fp:
			fp.write(stateData)

		oldFile = self.settings.stateFile + ".old"

		#Replace old data with new data
		try:
			os.rename(self.settings.stateFile, oldFile)
		except OSError:
			log.log("Got OSError on renaming old state file; probably it didn't exist yet, which is OK in a fresh installation.")
		os.rename(newFile, self.settings.stateFile)
		try:
			os.remove(oldFile)
		except OSError:
			log.log("Got OSError on removing old state file; probably it didn't exist, which is OK in a fresh installation.")


	def getState(self):
		return serializable.object2State(
			{
			"Node": self.__node,
			"TimeoutMessages": self.__timeoutMessages,
			"OutBox": self.__outBox
			})


	def setState(self, s):
		s = serializable.state2Object(s)
		self.__node            = s["Node"]
		self.__timeoutMessages = s["TimeoutMessages"]
		self.__outBox          = s["OutBox"]


	def __addTimeoutMessage(self, msg):
		"""
		Note: you should call __saveState afterwards!
		"""

		self.__timeoutMessages.append(msg)
		self.__timeoutMessages.sort(
			cmp = lambda a, b: a.timestamp - b.timestamp
			)


	def handleMessage(self, msg):
		returnValue = None

		oldState = self.getState()
		try:

			messages = [msg]
			while len(messages) > 0:
				msg = messages.pop(0)
				newMessages = []

				log.log("Processing message %s" % str(msg.__class__))

				#Messages for the node:
				if msg.__class__ in [
					nodestate.PaymentRequest,
					nodestate.MakePayer,
					nodestate.MakeRoute,
					nodestate.HavePayerRoute,
					nodestate.HavePayeeRoute,
					nodestate.Lock,
					payeelink.Pay,
					payeelink.Confirm,
					payeelink.Cancel,
					payerlink.Timeout,
					payerlink.Receipt,
					payerlink.PayerLink_Confirm
					]:
					newMessages = self.__node.handleMessage(msg)

				#Messages for the API:
				elif msg.__class__ == nodestate.ReturnValue:
					#Should happen only once per call of this function.
					#Otherwise, some return values will be forgotten.
					returnValue = msg.value

				#Messages for the outbox:
				elif msg.__class__ == network.OutboundMessage:
					self.__outBox.addMessage(msg)
				elif msg.__class__ == network.Confirmation:
					self.__outBox.processConfirmation(msg)

				else:
					raise Exception("Unsupported message type: " + str(msg.__class__))

				#Put new messages in the right places:
				for msg in newMessages:
					if msg.__class__ == nodestate.TimeoutMessage:
						#Add to the list of time-out messages:
						self.__addTimeoutMessage(msg)
					else:
						#Process in another iteration of the loop we're in:
						messages.append(msg)

			self.__saveState()
		except Exception as e:
			log.logException()
			#In case of exception, recover the old state:
			self.setState(oldState)
			raise

		return returnValue


	def stop(self):
		"""
		Stops the Node object.

		This method blocks until the Node object is stopped completely.
		"""

		self.__stop = True
		self.join()


	@runInNodeThread
	def request(self, amount, receipt):
		"""
		Request a payment.

		Arguments:
		amount : The amount (integer, in Satoshi) to be paid
		receipt: A receipt for the payment

		Return value:
		The URL of the payment request
		"""

		ID = self.handleMessage(nodestate.PaymentRequest(
			amount=amount, receipt=receipt))

		return "amikopay://%s/%s" % \
			(self.settings.getAdvertizedNetworkLocation(), ID)


	def pay(self, URL, linkname=None):
		"""
		Start paying a payment.

		Arguments:
		URL     : The URL of the payment request
		linkname: If not equal to None, payment routing is restricted to the
		          link with the given name.

		Return value:
		A tuple, containing:
			amount : The amount (integer, in Satoshi) to be paid
			receipt: A receipt for the payment
		"""

		self.__pay(URL, linkname) #implemented in Node thread
		payer = self.__node.payerLink

		payer.waitForReceipt() #Must be done in this thread

		if payer.amount is None or payer.receipt is None:
			raise Exception("Connecting to payee failed")

		return payer.amount, payer.receipt


	@runInNodeThread
	def __pay(self, URL, linkname=None):
		#TODO: make routing context, based on linkname

		URL = urlparse(URL)
		host = URL.hostname
		port = settings.defaultPort if URL.port == None else URL.port
		payeeLinkID = URL.path[1:] #remove initial slash

		self.handleMessage(nodestate.MakePayer(payeeLinkID=payeeLinkID))

		connection = self.networkEventDispatcher.makeConnection((host, port), callback=self)
		connection.localID = network.payerLocalID

		self.__outBox.addMessage(network.OutboundMessage(localID=connection.localID,
			message=payeelink.Pay(ID=payeeLinkID)))


	def confirmPayment(self, payerAgrees):
		"""
		Finish or cancel paying a payment.

		Arguments:
		payerAgrees: Boolean, indicating whether or not the user agrees to pay

		Return value:
		str, indicating the final payment state
		"""
		self.__confirmPayment(payerAgrees) #implemented in Node thread
		payer = self.__node.payerLink

		#TODO:
		#payer.waitForFinished() #Must be done in this thread
		#self.payLog.writePayer(payer)

		return payer.state


	@runInNodeThread
	def __confirmPayment(self, payerAgrees):
		self.handleMessage(payerlink.PayerLink_Confirm(agreement=payerAgrees))


	@runInNodeThread
	def list(self):
		"""
		Return value:
		A data structure, containing a summary of objects present in this
		Amiko node.
		"""

		return self.getState()


	@runInNodeThread
	def getBalance(self):
		"""
		Return value:
		Dictionary, containing different balances
		(integer, in Satoshi).
		"""

		raise Exception("NYI")


	@runInNodeThread
	def makeLink(self, localName, remoteURL=""):
		raise Exception("NYI")


	@runInNodeThread
	def deposit(self, linkname, amount):
		"""
		Deposit into a link.

		Arguments:
		linkname: the name of the link
		amount: the amount (integer, Satoshi) to be deposited
		"""

		raise Exception("NYI")



	@runInNodeThread
	def withdraw(self, linkname, channelID):
		"""
		Withdraw from a link.

		Arguments:
		linkname: the name of the link
		channelID: the channel ID of the channel to be withdrawn
		"""

		raise Exception("NYI")


	def run(self):
		"""
		The thread function.

		Intended for internal use by Node.
		Not intended to be part of the API.
		"""

		log.log("\n\nNode thread started")

		#TODO: (re-)enable creation of new transactions

		self.__stop = False
		while True:

			#Network events:
			asyncore.loop(timeout=0.01, count=1)

			#API events:
			with self._commandFunctionLock:
				s = self._commandFunction
				if s != None:
					try:
						self._commandReturnValue = s[0](self, *s[1], **s[2])
					except Exception as e:
						self._commandReturnValue = e
						log.logException()
					self._commandProcessed.set()
					self._commandFunction = None

			#Time-out events:
			while len(self.__timeoutMessages) > 0 and self.__timeoutMessages[0].timestamp < time.time():
				msg = self.__timeoutMessages.pop(0)
				self.handleMessage(msg.message)

			#New attempt to send the outbox:
			self.__outBox.transmit(self.networkEventDispatcher)

			if self.__stop:
				#TODO: stop creation of new transactions
				#TODO: only break once there are no more open transactions
				break

		log.log("Node thread terminated\n\n")

