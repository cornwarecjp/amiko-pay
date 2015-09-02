#    plainchannel.py
#    Copyright (C) 2015 by CJP
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

from ..utils import utils

#TODO: should serializable be moved to utils?
from ..core import serializable



class PlainChannel_Deposit(serializable.Serializable):
	serializableAttributes = {'amount': 0}
serializable.registerClass(PlainChannel_Deposit)



class PlainChannel_Transaction(serializable.Serializable):
	serializableAttributes = {'startTime': None, 'endTime': None, 'amount': 0}
serializable.registerClass(PlainChannel_Transaction)



class PlainChannel(serializable.Serializable):
	"""
	Payment channel without any protection.
	This implements a pure Ripple-style system, with full trust between
	neighbors.
	"""

	states = utils.Enum([
		"initial", "depositing",
		"ready"
		])

	serializableAttributes = \
	{
	'state': states.initial,

	'amountLocal': 0,
	'amountRemote': 0,

	#hash -> amount
	'transactionsIncomingReserved': {},
	'transactionsOutgoingReserved': {},
	'transactionsIncomingLocked':   {},
	'transactionsOutgoingLocked':   {}
	}


	@staticmethod
	def makeForOwnDeposit(amount):
		return PlainChannel(
			state=PlainChannel.states.depositing, amountLocal=amount, amountRemote=0)


	def handleMessage(self, msg):
		if (self.state, msg) == (self.states.depositing, None):
			self.state = self.states.ready
			return PlainChannel_Deposit(amount=self.amountLocal)
		elif (self.state, msg.__class__) == (self.states.initial, PlainChannel_Deposit):
			self.state = self.states.ready
			self.amountRemote = msg.amount
			return None

		return None


	def reserve(self, isPayerSide, transactionID, startTime, endTime, amount):
		if isPayerSide:
			if self.amountLocal < amount:
				raise Exception("Insufficient funds")

			self.amountLocal -= amount
			self.transactionsOutgoingReserved[transactionID] = \
				PlainChannel_Transaction(
					startTime=startTime, endTime=endTime, amount=amount)
		else:
			if self.amountRemote < amount:
				raise Exception("Insufficient funds")

			self.amountRemote -= amount
			self.transactionsIncomingReserved[transactionID] = \
				PlainChannel_Transaction(
					startTime=startTime, endTime=endTime, amount=amount)


	def lockOutgoing(self, transactionID):
		self.transactionsOutgoingLocked[transactionID] = \
			self.transactionsOutgoingReserved[transactionID]
		del self.transactionsOutgoingReserved[transactionID]


	def lockIncoming(self, transactionID):
		self.transactionsIncomingLocked[transactionID] = \
			self.transactionsIncomingReserved[transactionID]
		del self.transactionsIncomingReserved[transactionID]


	def settleCommitOutgoing(self, transactionID, token):
		self.amountRemote += self.transactionsOutgoingLocked[transactionID].amount
		del self.transactionsOutgoingLocked[transactionID]


	def settleCommitIncoming(self, transactionID):
		self.amountLocal += self.transactionsIncomingLocked[transactionID].amount
		del self.transactionsIncomingLocked[transactionID]


	def hasTransaction(self, transactionID):
		return \
			transactionID in self.transactionsIncomingReserved or \
			transactionID in self.transactionsOutgoingReserved or \
			transactionID in self.transactionsIncomingLocked or \
			transactionID in self.transactionsOutgoingLocked


serializable.registerClass(PlainChannel)

