#    event.py
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

import select
import time

import network
import utils



signals = utils.Enum([
	"readyForRead",
	"readyForWrite",
	"closed",
	"link",
	"pay",
	"message",
	"quit"
	])



class Context:

	class EventConnection:
		# For network signals, sender must be the socket object
		# sender == None: common place-holder
		def __init__(self, sender, signal, handler):
			self.sender = sender
			self.signal = signal
			self.handler = handler

	class Timer:
		def __init__(self, timestamp, handler):
			self.timestamp = timestamp
			self.handler = handler


	def __init__(self):
		# Each element is an EventConnection
		self.__eventConnections = []

		# Each element is a Timer
		self.__timers = []


	def connect(self, sender, signal, handler):
		self.__eventConnections.append(
			Context.EventConnection(sender, signal, handler))


	def setTimer(self, dt, handler):
		self.__timers.append(Context.Timer(time.time() + dt, handler))


	def removeConnectionsBySender(self, sender):
		self.__eventConnections = filter(lambda c: c.sender != sender,
			self.__eventConnections)


	def removeConnectionsByHandler(self, handler):
		self.__eventConnections = filter(lambda c: c.handler != handler,
			self.__eventConnections)
		self.__timers = filter(lambda c: c.handler != handler,
			self.__timers)


	def dispatchNetworkEvents(self):
		rlist = set([c.sender for c in self.__eventConnections
			if c.signal == signals.readyForRead])
		wlist = set([c.sender for c in self.__eventConnections
			if c.signal == signals.readyForWrite])

		# wait for network events, with 0.01 s timeout:
		#print "select.select(%s, %s, [], 0.01)" % (str(rlist), str(wlist))
		rlist, wlist, xlist = select.select(rlist, wlist, [], 0.01)
		#print " = %s, %s, %s" % (rlist, wlist, xlist)

		#Call write handlers:
		for w in wlist:
			self.sendSignal(w, signals.readyForWrite)

		#Call read handlers:
		for r in rlist:
			self.sendSignal(r, signals.readyForRead)


	def dispatchTimerEvents(self):
		now = time.time()
		for t in self.__timers:
			if not (t.timestamp > now):
				t.handler()
		self.__timers = filter(lambda t: t.timestamp > now, self.__timers)


	def sendSignal(self, sender, signal, *args, **kwargs):
		handlers = [c.handler for c in self.__eventConnections
			if c.sender == sender and c.signal == signal]
		for h in handlers:
			h(*args, **kwargs)



class Handler:
	def __init__(self, context):
		self.context = context
		self.__handlers = set([])


	def disconnectAll(self):
		for h in self.__handlers:
			self.context.removeConnectionsByHandler(h)
		self.context.removeConnectionsBySender(self)


	def connect(self, sender, signal, handler):
		self.context.connect(sender, signal, handler)
		self.__handlers.add(handler)


	def setTimer(self, dt, handler):
		self.context.setTimer(dt, handler)
		self.__handlers.add(handler)


