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
import finlink
import meetingpoint
import paylink
import settings
import randomsource
import log
import paylog



version = "0.1.0 (unstable,development)"
lastCopyrightYear = "2014"


minProtocolVersion = 1
maxProtocolVersion = 1



class RoutingContext:
	def __init__(self):
		self.finLinks = []
		self.meetingPoints = []

	def list(self):
		return \
		{
			"finLinks":
			[fl.list() for fl in self.finLinks],

			"meetingPoints":
			[mp.list() for mp in self.meetingPoints]
		}


def runInAmikoThread(implementationFunc):
	"""
	Function decorator, which can be used by Amiko methods to have them
	called by an external thread, but have them run inside the internal thread
	of the Amiko object.
	"""

	def remoteCaller(self, *args, **kwargs):
		with self._commandFunctionLock:
			self._commandFunction = (implementationFunc, args, kwargs)
			self._commandProcessed.clear()
		self._commandProcessed.wait()

		if isinstance(self._commandReturnValue, Exception):
			raise self._commandReturnValue
		return self._commandReturnValue

	return remoteCaller



class Amiko(threading.Thread):
	def __init__(self, conffile="amikopay.conf"):
		threading.Thread.__init__(self)

		self.settings = settings.Settings(conffile)

		self.context = event.Context()

		self.routingContext = RoutingContext()
		self.payees = []

		self.payLog = paylog.PayLog(self.settings)

		self.__stop = False

		self._commandFunctionLock = threading.Lock()
		self._commandFunction = None
		self._commandProcessed = threading.Event()
		self._commandReturnValue = None

		self.context.connect(None, event.signals.link, self.__handleLinkSignal)
		self.context.connect(None, event.signals.pay, self.__handlePaySignal)

		self.__loadState()


	def stop(self):
		self.__stop = True
		self.join()


	@runInAmikoThread
	def request(self, amount, receipt):
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


	def pay(self, URL):
		newPayer = self.__pay(URL) #implemented in Amiko thread
		newPayer.waitForReceipt() #Must be done in this thread
		return newPayer


	@runInAmikoThread
	def __pay(self, URL):
		newPayer = paylink.Payer(self.context, self.routingContext, URL)
		return newPayer


	def confirmPayment(self, payer, payerAgrees):
		self.__confirmPayment(payer, payerAgrees) #implemented in Amiko thread
		payer.waitForFinished() #Must be done in this thread
		self.payLog.writePayer(payer)


	@runInAmikoThread
	def __confirmPayment(self, payer, payerAgrees):
		payer.confirmPayment(payerAgrees)


	@runInAmikoThread
	def list(self):
		ret = self.routingContext.list()
		ret["requests"] = [p.list() for p in self.payees]
		return ret


	def run(self):
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


	def __loadState(self):
		with open(self.settings.stateFile, 'rb') as fp:
			state = json.load(fp)
			#print state

		for fl in state["finLinks"]:
			self.routingContext.finLinks.append(finlink.FinLink(
				self.context, self.routingContext,
				self.settings, fl))

		for mp in state["meetingPoints"]:
			self.routingContext.meetingPoints.append(
				meetingpoint.MeetingPoint(str(mp["ID"])))


	def __movePayeesToPayLog(self):
		"Writes finished payee objects to pay log and then removes them"

		for p in self.payees[:]: #copy of list, since the list will be modified
			if p.state in [p.states.cancelled, p.states.committed]:
				self.payLog.writePayee(p)
				self.payees.remove(p)


	def __handleLinkSignal(self, connection, message):
		for f in self.routingContext.finLinks:
			if f.localID == message.value:
				f.connect(connection)
				return

		print "Received link message with unknown ID"
		connection.close()


	def __handlePaySignal(self, connection, message):
		for p in self.payees:
			if p.ID == message.value:
				p.connect(connection)
				return

		print "Received pay message with unknown ID"
		connection.close()

