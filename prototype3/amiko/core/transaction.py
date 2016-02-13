#    transaction.py
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

from ..utils import serializable


side_payer = 1
side_payee = -1


class Transaction(serializable.Serializable):
	serializableAttributes = \
	{
	'side':None, 'payeeID':None, 'payerID':None, 'remainingLinkIDs':[],
	'meetingPointID':None, 'amount':0,
	'transactionID':'', 'startTime':0, 'endTime':0,
	}


	def tryNextRoute(self):
		try:
			nextRoute = self.remainingLinkIDs.pop(0)
		except IndexError:
			#None in case there is no more route
			nextRoute = None

		if self.side == side_payer:
			self.payeeID = nextRoute
		else: #side_payee
			self.payerID = nextRoute

		return nextRoute


serializable.registerClass(Transaction)

