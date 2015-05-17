#    channel.py
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

import messages



class CheckFail(Exception):
	pass



class Transaction:
	"""
	Information about a micro-transaction in a payment channel.

	Attributes:
	startTime: int; start of the time range when the transaction token must
	           be published (UNIX time)
	endTime: int; end of the time range when the transaction token must
	         be published (UNIX time)
	amount: int; the amount (in Satoshi) locked for the transaction
	"""

	@staticmethod
	def makeFromState(state):
		"""
		Make a Transaction, based on the given state object.
		This is a static method: it can be called without having an instance,
		as an alternative to calling the constructor directly.

		Arguments:
		state: A data structure, consisting of only standard Python types like
		       dict, list, str, bool, int.

		Return value:
		Transaction; the created transaction structure.

		Exceptions:
		Exception: loading from the state object failed
		"""
		return Transaction(state["startTime"], state["endTime"], state["amount"])


	def __init__(self, startTime, endTime, amount):
		"""
		Constructor.

		Arguments:
		startTime: int; start of the time range when the transaction token must
		           be published (UNIX time)
		endTime: int; end of the time range when the transaction token must
		         be published (UNIX time)
		amount: int; the amount (in Satoshi) locked for the transaction
		"""
		self.startTime = startTime
		self.endTime = endTime
		self.amount = amount


	def getState(self, forDisplay=False):
		"""
		Return a data structure that contains state information of the transaction.

		Arguments:
		forDisplay: bool; indicates whether the returned state is for user
		            interface display purposes (True) or for state saving
		            purposes (False). For user interface display purposes, a
		            summary may be returned instead of the complete state.

		Return value:
		A data structure, consisting of only standard Python types like dict,
		list, str, bool, int.
		"""

		return \
		{
			"startTime": self.startTime,
			"endTime": self.endTime,
			"amount": self.amount
		}



class Channel:
	"""
	Payment channel without any protection.
	This implements a pure Ripple-style system, with full trust between
	neighbors.
	"""

	def __init__(self, state):
		"""
		Constructor.

		Arguments:
		state: a data structure, consisting of only standard Python types like
		dict, list, str, bool, int.
		"""

		self.ID = state["ID"]

		#Current balances:
		self.amountLocal             = state["amountLocal"]
		self.amountRemote            = state["amountRemote"]

		#hash -> amount
		self.transactionsIncomingReserved  = {} #TODO state["transactionsIncomingReserved"]
		self.transactionsOutgoingReserved  = {} #TODO state["transactionsOutgoingReserved"]
		self.transactionsIncomingLocked    = {} #TODO state["transactionsIncomingLocked"]
		self.transactionsOutgoingLocked    = {} #TODO state["transactionsOutgoingLocked"]


	def getType(self):
		"""
		Return the type of channel.
		This method should be overridden by Channel-derived classes.

		Return value:
		str; the type of channel.
		"""

		return "plain"


	def getState(self, forDisplay=False):
		"""
		Return a data structure that contains state information of the channel.

		Arguments:
		forDisplay: bool; indicates whether the returned state is for user
		            interface display purposes (True) or for state saving
		            purposes (False). For user interface display purposes, a
		            summary may be returned instead of the complete state.

		Return value:
		A data structure, consisting of only standard Python types like dict,
		list, str, bool, int.
		"""

		return \
		{
		"ID"                    : self.ID,
		"type"                  : self.getType(),
		"amountLocal"           : self.amountLocal,
		"amountRemote"          : self.amountRemote,

		"transactionsIncomingReserved":
			self.__encodeTxes(self.transactionsIncomingReserved),
		"transactionsOutgoingReserved":
			self.__encodeTxes(self.transactionsOutgoingReserved),
		"transactionsIncomingLocked"  :
			self.__encodeTxes(self.transactionsIncomingLocked),
		"transactionsOutgoingLocked"  :
			self.__encodeTxes(self.transactionsOutgoingLocked)
		}


	def __encodeTxes(self, txes):
		"""
		Returns the state object for a dict of transactions.
		The dict keys are transformed to a hex encoding; the getState method
		of each value is called to determine its state.

		Arguments:
		txes: dict of (str, Transaction); the dict of transactions

		Return value:
		A data structure, consisting of only standard Python types like dict,
		list, str, bool, int.
		"""

		ret = {}
		for k,v in txes.iteritems():
			ret[k.encode("hex")] = v.getState()
		return ret


	def reserve(self, isPayerSide, hash, startTime, endTime, amount):
		"""
		Reserves the given amount of funds for an incoming or outgoing payment.

		Arguments:
		isPayerSide: bool; indicates whether we are on the payer side (True) or
		             not (False). Note that the payer side corresponds to an
		             outgoing transaction and payee side to an incoming one.
		hash: str; the SHA256- and RIPEMD160-hashed commit token.
		startTime: int; start of the time range when the transaction token must
		           be published (UNIX time)
		endTime: int; end of the time range when the transaction token must
		         be published (UNIX time)
		amount: int; the amount (in Satoshi) to be sent from payer to payee.

		Exceptions:
		CheckFail: A check has failed, and the reservation was not performed.
		"""

		if isPayerSide:
			if self.amountLocal < amount:
				raise CheckFail("Insufficient funds")

			self.amountLocal -= amount
			self.transactionsOutgoingReserved[hash] = \
				Transaction(startTime, endTime, amount)
		else:
			if self.amountRemote < amount:
				raise CheckFail("Insufficient funds")

			self.amountRemote -= amount
			self.transactionsIncomingReserved[hash] = \
				Transaction(startTime, endTime, amount)


	def unreserve(self, isPayerSide, hash):
		"""
		Un-reserves the funds for an incoming or outgoing payment.

		Arguments:
		isPayerSide: bool; indicates whether we are on the payer side (True) or
		             not (False). Note that the payer side corresponds to an
		             outgoing transaction and payee side to an incoming one.
		hash: str; the SHA256- and RIPEMD160-hashed commit token.

		Exceptions:
		Exception: the hash does not correspond to any reserved funds.
		"""

		if isPayerSide:
			self.amountLocal += self.transactionsOutgoingReserved[hash].amount
			del self.transactionsOutgoingReserved[hash]
		else:
			self.amountRemote += self.transactionsIncomingReserved[hash].amount
			del self.transactionsIncomingReserved[hash]


	def lockIncoming(self, message):
		"""
		Lock previously reserved funds for an incoming transaction.

		Arguments:
		message: Lock; the lock message.

		Exceptions:
		KeyError: the hash in the message did not match any reserved funds.
		CheckFail: A check has failed, and the locking was not performed.
		"""

		hash = message.hash
		self.transactionsIncomingLocked[hash] = \
			self.transactionsIncomingReserved[hash]
		del self.transactionsIncomingReserved[hash]


	def lockOutgoing(self, hash):
		"""
		Lock previously reserved funds for an outgoing transaction.

		Arguments:
		hash: str; the SHA256- and RIPEMD160-hashed commit token.

		Return value:
		Lock; the lock message.

		Exceptions:
		KeyError: the hash did not match any reserved funds.
		"""

		self.transactionsOutgoingLocked[hash] = \
			self.transactionsOutgoingReserved[hash]
		del self.transactionsOutgoingReserved[hash]
		return messages.Lock(self.ID, hash=hash)


	def commitIncoming(self, hash, message):
		"""
		Commit previously locked funds for an incoming transaction.

		Arguments:
		hash: str; the SHA256- and RIPEMD160-hashed commit token.
		message: Commit; the commit message.

		Exceptions:
		KeyError: the hash in the message did not match any locked funds.
		CheckFail: A check has failed, and the committing was not performed.
		"""

		self.amountLocal += self.transactionsIncomingLocked[hash].amount
		del self.transactionsIncomingLocked[hash]


	def commitOutgoing(self, hash, token):
		"""
		Commit previously locked funds for an outgoing transaction.

		Arguments:
		hash: str; the SHA256- and RIPEMD160-hashed commit token.
		token: str; the commit token.

		Return value:
		Commit; the commit message.

		Exceptions:
		KeyError: the hash did not match any locked funds.
		"""

		self.amountRemote += self.transactionsOutgoingLocked[hash].amount
		del self.transactionsOutgoingLocked[hash]
		return messages.Commit(self.ID, token=token)

