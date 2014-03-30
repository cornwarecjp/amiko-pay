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
import finlink
import event



minProtocolVersion = 1
maxProtocolVersion = 1



class Amiko(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)

		self.context = event.Context()

		self.listener = network.Listener(self.context, 4321)
		self.finLinks = []
		self.finLinks.append(finlink.FinLink(self.context, "A", "B"))
		self.finLinks.append(finlink.FinLink(self.context, "B", "A"))

		self.__stop = False

		self.__signalLock = threading.Lock()
		self.__signal = None
		self.__signalProcessed = threading.Event()

		self.context.connect(None, event.signals.link, self.__handleLinkSignal)


	def stop(self):
		self.__stop = True
		self.join()


	def sendSignal(self, signal, *args, **kwargs):
		with self.__signalLock:
			self.__signal = (signal, args, kwargs)
			self.__signalProcessed.clear()
		self.__signalProcessed.wait()


	def run(self):
		self.__stop = False
		while not self.__stop:
			self.context.dispatchNetworkEvents()
			self.context.dispatchTimerEvents()
			with self.__signalLock:
				s = self.__signal
				if s != None:
					self.context.sendSignal(s[0], *s[1], **s[2])
				self.__signalProcessed.set()
				self.__signal = None


	def __handleLinkSignal(self, connection, message):
		for f in self.finLinks:
			if f.localID == message.yourID:
				f.connect(connection)
				return

		print "Received link message with unknown ID"
		connection.close()

