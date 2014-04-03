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

import network
import event
import finlink
import paylink



version = "0.1.0 (unstable,development)"
lastCopyrightYear = "2014"


minProtocolVersion = 1
maxProtocolVersion = 1



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
	def __init__(self):
		threading.Thread.__init__(self)

		self.context = event.Context()

		self.listener = network.Listener(self.context, 4321)
		self.finLinks = []
		self.finLinks.append(finlink.FinLink(self.context, "A", "B"))
		self.finLinks.append(finlink.FinLink(self.context, "B", "A"))
		self.payees = []

		self.__stop = False

		self._commandFunctionLock = threading.Lock()
		self._commandFunction = None
		self._commandProcessed = threading.Event()
		self._commandReturnValue = None

		self.context.connect(None, event.signals.link, self.__handleLinkSignal)
		self.context.connect(None, event.signals.pay, self.__handlePaySignal)


	def stop(self):
		self.__stop = True
		self.join()


	@runInAmikoThread
	def sendSignal(self, sender, signal, *args, **kwargs):
		self.context.sendSignal(sender, signal, *args, **kwargs)


	@runInAmikoThread
	def request(self, amount, receipt):
		print amount
		print receipt
		ID = "42" #TODO: large random ID
		newPayee = paylink.Payee(self.context, ID, amount, receipt)
		self.payees.append(newPayee)

		#TODO: get this from newPayee:
		return "amikopay://localhost/" + ID


	@runInAmikoThread
	def pay(self, URL):
		newPayer = paylink.Payer(self.context, URL)
		return newPayer


	def run(self):
		self.__stop = False
		while not self.__stop:

			self.context.dispatchNetworkEvents()
			self.context.dispatchTimerEvents()

			with self._commandFunctionLock:
				s = self._commandFunction
				if s != None:
					try:
						self._commandReturnValue = s[0](self, *s[1], **s[2])
					except Exception as e:
						self._commandReturnValue = e
					self._commandProcessed.set()
					self._commandFunction = None


	def __handleLinkSignal(self, connection, message):
		for f in self.finLinks:
			if f.localID == message.yourID:
				f.connect(connection)
				return

		print "Received link message with unknown ID"
		connection.close()


	def __handlePaySignal(self, connection, message):
		for p in self.payees:
			if p.ID == message.ID:
				p.connect(connection)
				return

		print "Received pay message with unknown ID"
		connection.close()

