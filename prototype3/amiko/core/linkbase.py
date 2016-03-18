#    linkbase.py
#    Copyright (C) 2016 by CJP
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


class LinkBase:
	"""
	This is a base-class for all link-like objects.
	The base class defines a common interface, consisting of a couple of
	methods. The default behavior of each method is to return an empty list of
	messages. Derived classes can override these methods to implement other
	behavior.
	"""


	def makeRouteOutgoing(self, msg):
		return []


	def makeRouteIncoming(self, msg):
		return []


	def haveNoRouteOutgoing(self, transactionID, isPayerSide):
		return []


	def haveNoRouteIncoming(self, msg):
		return []


	def cancelOutgoing(self, msg):
		return []


	def cancelIncoming(self, msg):
		return []


	def lockOutgoing(self, msg):
		return []


	def lockIncoming(self, msg):
		return []


	def requestCommitOutgoing(self, msg):
		return []


	def requestCommitIncoming(self, msg):
		return []


	def settleCommitOutgoing(self, msg):
		return []


	def settleCommitIncoming(self, msg):
		return []


	def settleRollbackOutgoing(self, msg):
		return []


	def settleRollbackIncoming(self, msg):
		return []

