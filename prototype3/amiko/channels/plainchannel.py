#    plainchannel.py
#    Copyright (C) 2015-2016 by CJP
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
from ..utils import serializable

from ..core import messages



class PlainChannel_Deposit(serializable.Serializable):
	serializableAttributes = {'amount': 0}
serializable.registerClass(PlainChannel_Deposit)



class PlainChannel_Withdraw(serializable.Serializable):
	serializableAttributes = {}
serializable.registerClass(PlainChannel_Withdraw)



class PlainChannel_Transaction(serializable.Serializable):
	serializableAttributes = {'startTime': None, 'endTime': None, 'amount': 0}
serializable.registerClass(PlainChannel_Transaction)



class PlainChannel(serializable.Serializable):
	"""
	Payment channel without any protection.
	This can be used as a base class for other channel types.
	"""

	states = utils.Enum([
		'opening',
		'open',
		'closing',
		'closed'
		])

	serializableAttributes = \
	{
	'state': states.opening,

	'amountLocal': 0,
	'amountRemote': 0,

	#routeID -> amount
	#routeID is hash of the commit token, prefixed by a single character
	'transactionsIncomingReserved': {},
	'transactionsOutgoingReserved': {},
	'transactionsIncomingLocked':   {},
	'transactionsOutgoingLocked':   {}
	}


	@staticmethod
	def makeForOwnDeposit(amount):
		return PlainChannel(
			state=PlainChannel.states.opening, amountLocal=amount, amountRemote=0)


	def handleMessage(self, msg):
		"""
		Return value:
			tuple(list, list)
		"""

		if (self.state, msg) == (self.states.opening, None):
			self.state = self.states.open
			return [PlainChannel_Deposit(amount=self.amountLocal)], []

		elif (self.state, msg.__class__) == (self.states.opening, PlainChannel_Deposit):
			self.state = self.states.open
			self.amountRemote = msg.amount
			return [], []

		elif msg.__class__ == PlainChannel_Withdraw:
			if self.state in (self.states.closing, self.states.closed):
				#Ignore if already in progress/done
				return [], []
			else:
				return self.startWithdraw()

		raise Exception("Received unexpected channel message")


	def startWithdraw(self):
		"""
		Return value:
			tuple(list, list)
		"""

		if self.state in (self.states.closing, self.states.closed):
			raise Exception("Channel is already %s." % self.state)

		if self.state != self.states.open:
			raise Exception("Can not withdraw from a channel in state %s." % self.state)

		self.state = self.states.closing

		#Tell peer to do withdrawal
		ret = self.tryToClose()
		return [PlainChannel_Withdraw()] + ret[0], ret[1]


	def reserve(self, isOutgoing, routeID, startTime, endTime, amount):
		if self.state != self.states.open:
			raise Exception("Channel will not start transactions in state %s." % self.state)

		if isOutgoing:
			if self.amountLocal < amount:
				raise Exception("Insufficient funds")

			if routeID in self.transactionsOutgoingReserved:
				raise Exception("Attempt to let a route run twice through the same channel")

			self.amountLocal -= amount
			self.transactionsOutgoingReserved[routeID] = \
				PlainChannel_Transaction(
					startTime=startTime, endTime=endTime, amount=amount)
		else:
			if self.amountRemote < amount:
				raise Exception("Insufficient funds")

			if routeID in self.transactionsOutgoingReserved:
				raise Exception("Attempt to let a route run twice through the same channel")

			self.amountRemote -= amount
			self.transactionsIncomingReserved[routeID] = \
				PlainChannel_Transaction(
					startTime=startTime, endTime=endTime, amount=amount)


	def updateReservation(self, isOutgoing, routeID, startTime, endTime):
		if isOutgoing:
			tx = self.transactionsOutgoingReserved[routeID]
		else:
			tx = self.transactionsIncomingReserved[routeID]

		#Updating startTime and endTime is only allowed if they were previously
		#unknown, or if they were already the same as the new values.
		if not(tx.startTime is None) and tx.startTime != startTime:
			raise Exception(
				'Error: startTime was previously agreed to be %d, but now we receive %d' % \
				(tx.startTime, startTime))
		if not(tx.endTime is None) and tx.endTime != endTime:
			raise Exception(
				'Error: endTime was previously agreed to be %d, but now we receive %d' % \
				(tx.endTime, endTime))

		tx.startTime = startTime
		tx.endTime = endTime


	def unreserve(self, isOutgoing, routeID):
		"""
		Return value:
			tuple(list, list)
		"""

		if isOutgoing:
			self.amountLocal += self.transactionsOutgoingReserved[routeID].amount
			del self.transactionsOutgoingReserved[routeID]
		else:
			self.amountRemote += self.transactionsIncomingReserved[routeID].amount
			del self.transactionsIncomingReserved[routeID]

		return self.tryToClose()


	def lockOutgoing(self, routeID):
		self.transactionsOutgoingLocked[routeID] = \
			self.transactionsOutgoingReserved[routeID]
		del self.transactionsOutgoingReserved[routeID]


	def lockIncoming(self, routeID):
		self.transactionsIncomingLocked[routeID] = \
			self.transactionsIncomingReserved[routeID]
		del self.transactionsIncomingReserved[routeID]


	def getOutgoingCommitTimeout(self, routeID):
		return self.transactionsOutgoingLocked[routeID].endTime


	def doCommitTimeout(self, routeID):
		"""
		Return value:
			tuple(list, list)
		"""
		return [], [messages.NodeState_TimeoutRollback(transactionID=routeID)]


	def settleCommitOutgoing(self, routeID, token):
		"""
		Return value:
			tuple(list, list)
		"""

		self.amountRemote += self.transactionsOutgoingLocked[routeID].amount
		del self.transactionsOutgoingLocked[routeID]
		return self.tryToClose()


	def settleCommitIncoming(self, routeID):
		"""
		Return value:
			tuple(list, list)
		"""

		self.amountLocal += self.transactionsIncomingLocked[routeID].amount
		del self.transactionsIncomingLocked[routeID]
		return self.tryToClose()


	def settleRollbackOutgoing(self, routeID):
		"""
		Return value:
			tuple(list, list)
		"""

		self.amountRemote += self.transactionsIncomingLocked[routeID].amount
		del self.transactionsIncomingLocked[routeID]
		return self.tryToClose()


	def settleRollbackIncoming(self, routeID):
		"""
		Return value:
			tuple(list, list)
		"""

		self.amountLocal += self.transactionsOutgoingLocked[routeID].amount
		del self.transactionsOutgoingLocked[routeID]
		return self.tryToClose()


	def tryToClose(self):
		"""
		Return value:
			tuple(list, list)
		"""

		if self.state != self.states.closing:
			return [], []

		if len(self.transactionsIncomingReserved) != 0:
			return [], []
		if len(self.transactionsOutgoingReserved) != 0:
			return [], []
		if len(self.transactionsIncomingLocked) != 0:
			return [], []
		if len(self.transactionsOutgoingLocked) != 0:
			return [], []

		#we're closing, and there are no more ongoing transactions,
		#so it's OK to close the channel now.
		return self.doClose()


	def doClose(self):
		"""
		Return value:
			tuple(list, list)
		"""

		self.state = self.states.closed

		return [], []


	def hasRoute(self, routeID):
		return \
			routeID in self.transactionsIncomingReserved or \
			routeID in self.transactionsOutgoingReserved or \
			routeID in self.transactionsIncomingLocked or \
			routeID in self.transactionsOutgoingLocked


serializable.registerClass(PlainChannel)

