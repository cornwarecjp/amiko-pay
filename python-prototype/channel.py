#    channel.py
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



class CheckFail(Exception):
	pass



class Channel:
	"""
	Payment channel without any protection.
	This implements a pure Ripple-style system, with full trust between
	neighbors.
	"""

	def __init__(self, state):

		#Current balances:
		self.amountLocal             = state["amountLocal"]
		self.amountRemote            = state["amountRemote"]

		#hash -> amount
		self.transactionsIncomingReserved  = {} #TODO state["transactionsIncomingReserved"]
		self.transactionsOutgoingReserved  = {} #TODO state["transactionsOutgoingReserved"]
		self.transactionsIncomingLocked    = {} #TODO state["transactionsIncomingLocked"]
		self.transactionsOutgoingLocked    = {} #TODO state["transactionsOutgoingLocked"]


	def getType(self):
		return "plain"


	def getState(self, verbose=False):
		return \
		{
		"type"                  : self.getType(),
		"amountLocal"           : self.amountLocal,
		"amountRemote"          : self.amountRemote,

		"transactionsIncomingReserved":
			self.__encodeDict(self.transactionsIncomingReserved),
		"transactionsOutgoingReserved": 
			self.__encodeDict(self.transactionsOutgoingReserved),
		"transactionsIncomingLocked"  : 
			self.__encodeDict(self.transactionsIncomingLocked),
		"transactionsOutgoingLocked"  : 
			self.__encodeDict(self.transactionsOutgoingLocked)
		}


	def __encodeDict(self, d):
		ret = {}
		for k,v in d.iteritems():
			ret[k.encode("hex")] = v
		return ret


	def reserve(self, isPayerSide, hash, amount):
		if isPayerSide:
			if self.amountLocal < amount:
				raise CheckFail("Insufficient funds")

			self.amountLocal -= amount
			self.transactionsOutgoingReserved[hash] = amount
		else:
			if self.amountRemote < amount:
				raise CheckFail("Insufficient funds")

			self.amountRemote -= amount
			self.transactionsIncomingReserved[hash] = amount


	def lockIncoming(self, hash):
		self.transactionsIncomingLocked[hash] = \
			self.transactionsIncomingReserved[hash]
		del self.transactionsIncomingReserved[hash]


	def lockOutgoing(self, hash):
		self.transactionsOutgoingLocked[hash] = \
			self.transactionsOutgoingReserved[hash]
		del self.transactionsOutgoingReserved[hash]


	def commitIncoming(self, hash):
		self.amountLocal += self.transactionsIncomingLocked[hash]
		del self.transactionsIncomingLocked[hash]


	def commitOutgoing(self, hash):
		self.amountRemote += self.transactionsOutgoingLocked[hash]
		del self.transactionsOutgoingLocked[hash]


