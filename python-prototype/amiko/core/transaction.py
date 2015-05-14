#    transaction.py
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



class Transaction:
	"""
	A Transaction object.

	Performs the passing of the messages of a single transaction between
	links, paylinks and routing contexts. The routing algorithm is implemented
	in this class.
	"""

	def __init__(self, context, routingContext,
		amount, hash, meetingPoint,
		payerLink=None, payeeLink=None):
		"""
		Constructor.
		All arguments are stored as attributes with the same name.
		In addition, the attribute "token" is initialized as None.
		A list of to-be-tried routes is initialized, based on routingContext.

		Arguments:
		context: Context; event context
		routingContext: RoutingContext; routing context
		amount: int; the amount (in Satoshi) to be sent from payer to payee
		hash: str; the SHA256- and RIPEMD160-hashed commit token
		meetingPoint: str; the ID of the meeting point
		payerLink: Link/Payer/MeetingPoint; the payer-side link (default: None)
		payeeLink: Link/Payee/MeetingPoint; the payee-side link (default: None)

		Note: before msg_haveRoute is received, one of the two links is None,
		and the other one is non-None. After msg_haveRoute is received, both are
		non-None.
		"""

		self.context = context
		self.routingContext = routingContext
		self.amount = amount
		self.hash = hash
		self.token = None #unknown
		self.meetingPoint = meetingPoint
		self.payerLink = payerLink
		self.payeeLink = payeeLink

		#Initialize routing possibilities:
		#Note: just list the IDs here, not references to actual link objects.
		#This allows other code to remove links while we're routing.
		self.__remainingRoutes = \
			[lnk.localID for lnk in self.routingContext.links]
		self.__currentRoute = None


	def isPayerSide(self):
		"""
		When called while we do not have a route yet, indicates whether we are
		on the payer side (searching for a route towards the payee) or on the
		payee side (searching for a route towards the payer).

		Return value:
		bool; indicates whether we are on the payer side (True) or not (False).

		Exceptions:
		Exception: function is called while we already have a route
		           (both links are non-None).
		"""

		if self.payeeLink == None:
			return True
		if self.payerLink == None:
			return False
		raise Exception(
			"isPayerSide should only be called when routing is unfinished")


	def msg_makeRoute(self):
		"""
		This method is typically called by the already-existing link to
		initiate the routing for the non-existing link.

		Choose a link or a meeting point from the routing context, and call
		msg_makeRoute to that link or meeting point.
		If no suitable link or meeting point exists, call msg_haveNoRoute on the
		already attached link (either payerLink or payeeLink, whichever is
		non-None).

		Exceptions:
		Exception: function is called while we already have a route
		           (both links are non-None).
		"""

		#If we are the meeting point, we're finished:
		if self.__tryMeetingPoint():
			return #found -> finished

		#Note: this will just try the first route.
		#However, if that fails we'll be notified about it, and then
		#we'll try the next, and so on.
		self.__tryNextRoute()


	def msg_haveRoute(self, link):
		"""
		This method is typically called by a link that has previously received
		a msg_makeRoute from this object; it passes itself as argument.

		Replace the missing (None-valued) link (either payerLink or payeeLink)
		with the given link object. Call msg_haveRoute on the link that was
		already known.

		Arguments:
		link: Link/MeetingPoint; the link on which a route is found.

		Exceptions:
		Exception: function is called while we already have a route
		           (both links are non-None).
		"""

		log.log("Transaction: haveRoute")
		if self.isPayerSide():
			self.payeeLink = link
			self.payerLink.msg_haveRoute(self)
		else:
			self.payerLink = link
			self.payeeLink.msg_haveRoute(self)


	def msg_haveNoRoute(self):
		"""
		This method is typically called by a link that has previously received
		a msg_makeRoute from this object.

		Choose a new link from the routing context, and call msg_makeRoute to
		that link.
		If no suitable link exists, call msg_haveNoRoute on the already attached link
		(either payerLink or payeeLink, whichever is non-None).

		Exceptions:
		Exception: function is called while we already have a route
		           (both links are non-None).
		"""

		log.log("Transaction: haveNoRoute")
		#Immediately try next route, or send cancel back if there is none:
		self.__tryNextRoute()


	#TODO: msg_cancelRoute


	def msg_endRoute(self):
		"""
		This method is typically called by the already-existing link to
		end the routing that was previously started with a msg_makeRoute call.

		Call msg_endRoute to the link or meeting point to which the last
		msg_makeRoute was sent. If no such routing attempt was made or if the
		last routing attempt was already cancelled or ended, nothing is done.
		"""

		log.log("Transaction: endRoute")
		if self.__currentRoute != None:
			self.__currentRoute.msg_endRoute(self)
			self.__currentRoute = None


	def msg_lock(self):
		"""
		This method is typically called by the payer link.

		Call msg_lock to the payee link.
		"""

		log.log("Transaction: lock")
		self.payeeLink.msg_lock(self)


	def msg_commit(self, token):
		"""
		This method is typically called by the payer link.

		Set the attribute "token" to the given value. After that, call
		msg_commit to the payee link.

		Note: the token is NOT checked against the hash.

		Arguments:
		token: str; the commit token of the transaction.
		"""

		#TODO: split up into token distribution and commit, and make bi-directional
		log.log("Transaction: commit")
		self.token = token
		self.payeeLink.msg_commit(self)


	def __tryMeetingPoint(self):
		"""
		Check if one of our own meeting points matches the meeting point ID
		of this transaction, and if that is the case, call msg_makeRoute to
		that meeting point.

		Return value:
		bool; indicates whether a matching meeting point was found (True) or
              not (False).
		"""

		for mp in self.routingContext.meetingPoints:
			if mp.ID == self.meetingPoint:
				self.__currentRoute = mp
				mp.msg_makeRoute(self)
				return True #found

		return False #not found


	def __tryNextRoute(self):
		"""
		Choose a new link from the routing context, and call msg_makeRoute to
		that link.
		If no suitable link exists, call msg_haveNoRoute on the already attached link
		(either payerLink or payeeLink, whichever is non-None).

		Exceptions:
		Exception: function is called while we already have a route
		           (both links are non-None).
		"""

		while len(self.__remainingRoutes) > 0:
			nextRoute = self.__remainingRoutes.pop(0)

			for lnk in self.routingContext.links:
				if lnk.localID == nextRoute:
					log.log("Transaction: try next route")
					self.__currentRoute = lnk
					lnk.msg_makeRoute(self)
					return

		log.log("Transaction: no more route")
		#No more route: send cancel back to source
		self.__currentRoute = None
		del self.__remainingRoutes
		if self.isPayerSide():
			self.payerLink.msg_haveNoRoute(self)
		else:
			self.payeeLink.msg_haveNoRoute(self)



