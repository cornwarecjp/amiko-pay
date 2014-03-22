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

import select



class Enum(set):
	def __getattr__(self, name):
		if name in self:
			return name
		raise AttributeError



signals = Enum([
	"readyForRead",
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


	def __init__(self):
		# Each element is an EventConnection
		self.__eventConnections = []


	def connect(self, sender, signal, handler):
		self.__eventConnections.append(
			Context.EventConnection(sender, signal, handler))


	def removeEventConnectionsBySender(self, sender):
		self.__eventConnections = filter(lambda c: c.sender != sender,
			self.__eventConnections)


	def dispatchNetworkEvents(self):
		rlist = set([c.sender for c in self.__eventConnections
			if c.signal == signals.readyForRead])

		# wait for network events, with 0.01 s timeout:
		rlist, wlist, xlist = select.select(rlist, [], [], 0.01)

		for r in rlist:
			handlers = [c.handler for c in self.__eventConnections
				if c.sender == r and c.signal == signals.readyForRead]
			for h in handlers:
				h()


	def sendSignal(self, signal, *args, **kwargs):
		handlers = [c.handler for c in self.__eventConnections
			if c.sender == None and c.signal == signal]
		for h in handlers:
			h(*args, **kwargs)



class Amiko:
	pass


