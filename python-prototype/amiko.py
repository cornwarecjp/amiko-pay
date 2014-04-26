#    amiko.py
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

import threading
import json

import network
import event
import link
import meetingpoint
import paylink
import settings
import randomsource
import log
import paylog

#Somehow it is hard to replace the above copyright information with a more
#sensible doc string...
__doc__ = """
Top-level Application Programming Interface for the Amiko payment system
"""

version = "0.1.0 (unstable,development)"
lastCopyrightYear = "2014"


minProtocolVersion = 1
maxProtocolVersion = 1



class RoutingContext:
	"""
	The context in which transaction routing takes place.

	Contains all objects relevant to routing, such as links and meeting points.

	Intended for internal use by Amiko.
	Not intended to be part of the API.
	"""

	def __init__(self):
		self.links = []
		self.meetingPoints = []

	def getState(self):
		return \
		{
			"links":
			[lnk.getState() for lnk in self.links],

			"meetingPoints":
			[mp.getState() for mp in self.meetingPoints]
		}


def runInAmikoThread(implementationFunc):
	"""
	Function decorator, which can be used by Amiko methods to have them
	called by an external thread, but have them run inside the internal thread
	of the Amiko object.

	Intended for internal use by Amiko.
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



class Amiko(threading.Thread):
	"""
	A single Amiko node.

	A process can run multiple Amiko nodes by making multiple instances of
	this class. Each instance can have its own configuration, and runs in its
	own thread.

	After creating an instance, it can be started with the start() method.

	To stop the node, the stop() method must be called. This should always be
	done before program termination.
	"""

	def __init__(self, conffile="amikopay.conf"):
		"""
		Constructor.

		Arguments:
		conffile: Name of the configuration file to be loaded.
		"""

		threading.Thread.__init__(self)

		self.settings = settings.Settings(conffile)

		self.context = event.Context()

		self.routingContext = RoutingContext()
		self.payees = []

		self.payLog = paylog.PayLog(self.settings)

		self.__stop = False
		self.__doSave = False

		self._commandFunctionLock = threading.Lock()
		self._commandFunction = None
		self._commandProcessed = threading.Event()
		self._commandReturnValue = None

		self.context.connect(None, event.signals.link,
			self.__handleLinkSignal)
		self.context.connect(None, event.signals.pay,
			self.__handlePaySignal)
		self.context.connect(None, event.signals.save,
			self.__handleSaveSignal)
		self.context.connectPost(event.signals.message,
			self.__postHandleMessageSignal)

		self.__loadState()


	def stop(self):
		"""
		Stops the Amiko object.

		This method blocks until the Amiko object is stopped completely.
		"""

		self.__stop = True
		self.join()


	@runInAmikoThread
	def request(self, amount, receipt):
		"""
		Request a payment.

		Arguments:
		amount : The amount (integer, in Satoshi) to be paid
		receipt: A receipt for the payment

		Return value:
		The URL of the payment request
		"""

		#ID can be nonsecure random:
		#It only needs to be semi-unique, not secret.
		ID = randomsource.getNonSecureRandom(8).encode("hex")

		#Token must be secure random
		token = randomsource.getSecureRandom(32)

		newPayee = paylink.Payee(
			self.context, self.routingContext, ID, amount, receipt, token)
		self.payees.append(newPayee)

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
		A "payer" object, with the following attributes:
			amount : The amount (integer, in Satoshi) to be paid
			receipt: A receipt for the payment
		"""

		newPayer = self.__pay(URL, linkname) #implemented in Amiko thread
		newPayer.waitForReceipt() #Must be done in this thread
		return newPayer


	@runInAmikoThread
	def __pay(self, URL, linkname=None):
		rc = self.routingContext
		if linkname != None:
			rc = RoutingContext()
			rc.links = \
				[lnk for lnk in self.routingContext.links if lnk.name == linkname]
			if len(rc.links) == 0:
				raise Exception("There is no link with that name")

		newPayer = paylink.Payer(self.context, rc, URL)
		return newPayer


	def confirmPayment(self, payer, payerAgrees):
		"""
		Finish or cancel paying a payment.

		Arguments:
		payer      : A "payer" object as returned by the pay() method
		payerAgrees: Boolean, indicating whether or not the user agrees to pay
		"""

		self.__confirmPayment(payer, payerAgrees) #implemented in Amiko thread
		payer.waitForFinished() #Must be done in this thread
		self.payLog.writePayer(payer)


	@runInAmikoThread
	def __confirmPayment(self, payer, payerAgrees):
		payer.confirmPayment(payerAgrees)


	@runInAmikoThread
	def list(self):
		"""
		Return value:
		A data structure, containing a summary of objects present in this
		Amiko node.
		"""

		ret = self.routingContext.getState()
		ret["requests"] = [p.getState() for p in self.payees]
		return ret


	@runInAmikoThread
	def getBalance(self):
		"""
		Return value:
		The sum of all funds directly available for spending
		(integer, in Satoshi).
		"""

		ret = 0
		for lnk in self.routingContext.links:
			ret += lnk.getBalance()
		return ret


	def run(self):
		"""
		The thread function.

		Intended for internal use by Amiko.
		Not intended to be part of the API.
		"""

		log.log("\n\nAmiko thread started")

		#Start listening
		listener = network.Listener(self.context,
			self.settings.listenHost, self.settings.listenPort)

		#TODO: (re-)enable creation of new transactions

		self.__stop = False
		while True:

			self.context.dispatchNetworkEvents()
			self.context.dispatchTimerEvents()

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

			self.__movePayeesToPayLog()

			if self.__stop:
				#TODO: stop creation of new transactions
				#TODO: only break once there are no more open transactions
				break

		#This closes all network connections etc.
		self.context.sendSignal(None, event.signals.quit)

		log.log("Amiko thread terminated\n\n")


	def __loadState(self):
		with open(self.settings.stateFile, 'rb') as fp:
			state = json.load(fp)
			#print state

		for lnk in state["links"]:
			self.routingContext.links.append(link.Link(
				self.context, self.routingContext,
				self.settings, lnk))

		for mp in state["meetingPoints"]:
			self.routingContext.meetingPoints.append(
				meetingpoint.MeetingPoint(str(mp["ID"])))


	def __saveState(self):
		log.log("STATE SAVE NOT YET IMPLEMENTED")


	def __movePayeesToPayLog(self):
		"Writes finished payee objects to pay log and then removes them"

		for p in self.payees[:]: #copy of list, since the list will be modified
			if p.state in [p.states.cancelled, p.states.committed]:
				self.payLog.writePayee(p)
				self.payees.remove(p)


	def __handleLinkSignal(self, connection, message):
		for lnk in self.routingContext.links:
			if lnk.localID == message.value:
				lnk.connect(connection)
				return

		log.log("Received link message with unknown ID")
		connection.close()


	def __handlePaySignal(self, connection, message):
		for p in self.payees:
			if p.ID == message.value:
				p.connect(connection)
				return

		log.log("Received pay message with unknown ID")
		connection.close()


	def __handleSaveSignal(self):
		log.log("Save handler called")
		self.__doSave = True


	def __postHandleMessageSignal(self, message):
		log.log("Message post-handler called: " + str(message))

		if self.__doSave:
			self.__saveState()
			self.__doSave = False


