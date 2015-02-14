#    meetingpoint.py
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

import log



class MeetingPoint:
	"""
	A meeting point object.

	A transaction is routed from both payer and payee side towards a meeting
	point. A meeting point has an ID which is supposed to be globally unique
	in the Amiko network. A meeting point object represents a meeting point
	which is operated by this node. It contains functionality like matching
	routing attempts received from both sides.
	"""

	def __init__(self, ID):
		"""
		Constructor.

		Arguments:
		ID: str; the ID of the meeting point
		"""
		self.ID = ID

		# Each element is a transaction list [payer, payee]
		self.transactionPairs = {}


	def getState(self, forDisplay=False):
		"""
		Return a data structure that contains state information of the meeting
		point.

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
		"ID": self.ID,
		"openTransactions":
			[k.encode("hex") for k in self.transactionPairs.keys()]
		}


	def msg_makeRoute(self, transaction):
		"""
		This method is typically called by a transaction object to initiate the
		routing to this meeting point.

		If a matching msg_makeRoute was not yet received from the other
		(payer/payee) side, remember the transaction.

		If a matching msg_makeRoute was previously received from the other
		(payer/payee) side, call msg_haveRoute on the transaction objects on
		both sides. In case of a hash match but any other mismatch (e.g.
		amount), call msg_cancelRoute on the transaction objects on both sides,
		and forget the transaction.

		Arguments:
		transaction: Transaction; the transaction object that called this
                     method.
		"""

		try:
			pair = self.transactionPairs[transaction.hash]

			if transaction.isPayerSide() and pair[0] == None:
				pair[0] = transaction
			elif not transaction.isPayerSide() and pair[1] == None:
				pair[1] = transaction
			else:
				#Apparently, we received the transaction twice from the same
				#side. This can be an outside error.
				#For now, respond to it by sending msg_cancelRoute to both:
				#TODO: send a message that won't confuse the routing algorithms
				#of peers.
				log.log("Received twice from the same side: " + str(pair))

				#We don't need this anymore:
				del self.transactionPairs[transaction.hash]

				otherSide = pair[1]
				if transaction.isPayerSide():
					otherSide = pair[0]
				transaction.msg_cancelRoute()
				otherSide.msg_cancelRoute()
				return

			#Check whether transaction amounts match:
			if pair[0].amount != pair[1].amount:
				log.log("Transaction amounts don't match: %s; %d; %d" % \
					(str(pair), pair[0].amount, pair[1].amount))
				#For now, respond to it by sending msg_cancelRoute to both:
				#TODO: send a message that won't confuse the routing algorithms
				#of peers.
				del self.transactionPairs[transaction.hash]
				pair[0].msg_cancelRoute()
				pair[1].msg_cancelRoute()
				return

			self.transactionPairs[transaction.hash] = pair

			log.log("Matched transactions: " + str(pair))

			pair[0].msg_haveRoute(self)
			pair[1].msg_haveRoute(self)

		except KeyError as e:

			pair = [None, transaction]
			if transaction.isPayerSide():
				pair = [transaction, None]

			self.transactionPairs[transaction.hash] = pair


	def msg_endRoute(self, transaction):
		"""
		This method is typically called by a transaction object that has
		previously called msg_makeRoute.

		If the other side has already connected with msg_makeRoute, call
		msg_cancelRoute on the transaction object on that side, and forget
		the transaction.

		Arguments:
		transaction: Transaction; the transaction object that called this
                     method.
		"""

		log.log("Meeting point: endRoute")

		pair = self.transactionPairs[transaction.hash]

		#We don't need this anymore:
		del self.transactionPairs[transaction.hash]

		otherSide = pair[0]
		if transaction.isPayerSide():
			otherSide = pair[1]

		if otherSide != None:
			otherSide.msg_cancelRoute()


	def msg_lock(self, transaction):
		"""
		This method is typically called by the payer side transaction.

		Call msg_lock to the payee side transaction.

		Arguments:
		transaction: Transaction; the transaction object that called this
                     method.
		"""

		log.log("Meeting point: lock")
		pair = self.transactionPairs[transaction.hash]
		pair[1].msg_lock()


	def msg_commit(self, transaction):
		"""
		This method is typically called by the payer side transaction.

		Call msg_commit to the payee side transaction, and forget the
		transaction.

		Arguments:
		transaction: Transaction; the transaction object that called this
                     method.
		"""

		#TODO: split up into token distribution and commit, and make bi-directional
		log.log("Meeting point: commit")
		pair = self.transactionPairs[transaction.hash]
		pair[1].msg_commit(transaction.token)

		#We don't need this anymore:
		del self.transactionPairs[transaction.hash]


