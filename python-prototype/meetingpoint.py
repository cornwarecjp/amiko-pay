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
	def __init__(self, ID):
		self.ID = ID

		# Each element is a transaction list [payer, payee]
		self.transactionPairs = {}


	def getState(self, forDisplay=False):
		return \
		{
		"ID": self.ID,
		"openTransactions":
			[k.encode("hex") for k in self.transactionPairs.keys()]
		}


	def msg_makeRoute(self, transaction):
		try:
			pair = self.transactionPairs[transaction.hash]

			if transaction.isPayerSide() and pair[0] == None:
				pair[0] = transaction
			elif not transaction.isPayerSide() and pair[1] == None:
				pair[1] = transaction
			else:
				raise Exception("Bug in meeting point matching")

			#TODO: check whether amount equals (IMPORTANT)

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
		log.log("Meeting point: lock")
		pair = self.transactionPairs[transaction.hash]
		pair[1].msg_lock()


	def msg_commit(self, transaction):
		log.log("Meeting point: commit")
		pair = self.transactionPairs[transaction.hash]
		pair[1].msg_commit(transaction.token)

		#We don't need this anymore:
		del self.transactionPairs[transaction.hash]


