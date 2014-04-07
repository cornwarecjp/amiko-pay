#    meetingpoint.py
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

import log



class MeetingPoint:
	def __init__(self, ID):
		self.ID = ID

		# Each element is a transaction list [payer, payee]
		self.__transactionPairs = {}


	def list(self):
		return \
		{
		"ID": self.ID
		}


	def msg_makeRoute(self, transaction):
		try:
			pair = self.__transactionPairs[transaction.hash]

			if transaction.isPayerSide() and pair[0] == None:
				pair[0] = transaction
			elif not transaction.isPayerSide() and pair[1] == None:
				pair[1] = transaction
			else:
				raise Exception("Bug in meeting point matching")

			#TODO: check whether amount equals

			self.__transactionPairs[transaction.hash] = pair

			log.log("Matched transactions: " + str(pair))

			pair[0].msg_haveRoute(fromPayerSide=False)
			pair[1].msg_haveRoute(fromPayerSide=True)

		except KeyError as e:

			pair = [None, transaction]
			if transaction.isPayerSide():
				pair = [transaction, None]

			self.__transactionPairs[transaction.hash] = pair


	def msg_lock(self, transaction):
		log.log("Meeting point: lock")
		pair = self.__transactionPairs[transaction.hash]
		pair[1].msg_lock()


