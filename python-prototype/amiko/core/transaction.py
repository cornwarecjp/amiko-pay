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

	Attributes:
	meetingPoint: str; the ID of the meeting point
	amount: int; the amount (in Satoshi) to be sent from payer to payee
	hash: str; the SHA256- and RIPEMD160-hashed commit token
	startTime: int; start of the time range when the transaction token must
		       be published (UNIX time) (default: None)
	endTime: int; end of the time range when the transaction token must
		     be published (UNIX time) (default: None)
	isPayerSide: bool; indicates whether we are on the payer side (True) or
	             not (False).
	"""

	def __init__(self, context, routingContext, meetingPoint,
		amount, hash, startTime=0, endTime=0,
		payerLink=None, payeeLink=None):
		"""
		Constructor.
		All arguments are stored as attributes with the same name.
		In addition, the attribute "token" is initialized as None.
		A list of to-be-tried routes is initialized, based on routingContext.

		Arguments:
		context: Context; event context
		routingContext: RoutingContext; routing context
		meetingPoint: str; the ID of the meeting point
		amount: int; the amount (in Satoshi) to be sent from payer to payee
		hash: str; the SHA256- and RIPEMD160-hashed commit token
		startTime: int; start of the time range when the transaction token must
			       be published (UNIX time) (default: None)
		endTime: int; end of the time range when the transaction token must
			     be published (UNIX time) (default: None)
		payerLink: Link/Payer/MeetingPoint; the payer-side link (default: None)
		payeeLink: Link/Payee/MeetingPoint; the payee-side link (default: None)

		Note: exactly one of the two links must be None.

		Exceptions:
		KeyError: Either both links are None, or neither link is.
		"""

		self.context = context
		self.routingContext = routingContext
		self.amount = amount
		self.hash = hash
		self.startTime = startTime
		self.endTime = endTime
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

		#Note: this will give an exception if both payer and payee link are None,
		#or if neither is None.
		self.isPayerSide = \
		{
		(True, False): True, #payee link is None -> payer side
		(False, True): False #payer link is None -> payee side
		} [(payeeLink == None, payerLink == None)]


	def msg_makeRoute(self, sourceLinkID=None):
		"""
		This method is typically called by the already-existing link to
		initiate the routing for the non-existing link.

		Choose a link or a meeting point from the routing context, and call
		msg_makeRoute to that link or meeting point.
		If no suitable link or meeting point exists, call msg_haveNoRoute on the
		already attached link (either payerLink or payeeLink, whichever is
		non-None).

		Arguments:
		sourceLinkID: str; the ID of the source link (if any).
		              This ID will be skipped in routing attempts.
		"""

		#If we are the meeting point, we're finished:
		if self.__tryMeetingPoint():
			return #found -> finished

		#Remove sourceLinkID from the to-be-tried routes:
		while sourceLinkID in self.__remainingRoutes:
			self.__remainingRoutes.remove(sourceLinkID)

		#Note: this will just try the first route.
		#However, if that fails we'll be notified about it, and then
		#we'll try the next, and so on.
		self.__tryNextRoute()


	def msg_haveRoute(self, link, startTime, endTime):
		"""
		This method is typically called by a link that has previously received
		a msg_makeRoute from this object; it passes itself as argument.

		Replace the missing (None-valued) link (either payerLink or payeeLink)
		with the given link object. Call msg_haveRoute on the link that was
		already known.

		Arguments:
		link: Link/MeetingPoint; the link on which a route is found.
		startTime: int; start of the time range when the transaction token must
			       be published (UNIX time)
		endTime: int; end of the time range when the transaction token must
			     be published (UNIX time)
		"""

		log.log("Transaction: haveRoute")

		#On the payee side, this should overwrite values with the same values.
		#On the payer side, this should overwrite zero with the actual values.
		#It's important to do this BEFORE calling msg_haveRoute on the other end,
		#since that other end will read these attributes.
		self.startTime = startTime
		self.endTime = endTime

		if self.isPayerSide:
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


	def msg_requestCommit(self, token):
		"""
		This method is typically called by the payee link.

		Set the attribute "token" to the given value. After that, call
		msg_requestCommit to the payer link.

		Note: the token is NOT checked against the hash.

		Arguments:
		token: str; the commit token of the transaction.
		"""

		log.log("Transaction: requestCommit")
		self.token = token
		self.payerLink.msg_requestCommit(self)


	def msg_commit(self, token):
		"""
		This method is typically called by the payer link.

		If the token was not already known (self.token is None), set the
		attribute "token" to the given value, and call msg_commit to the payee link.

		Note: the token is NOT checked against the hash.

		Arguments:
		token: str; the commit token of the transaction.
		"""

		log.log("Transaction: commit")
		if self.token is None:
			self.token = token
			self.payeeLink.msg_commit(self)
		else:
			#TODO: maybe check whether both tokens are the same
			log.log("Transaction: token was already known; not transmitting the commit")


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
		if self.isPayerSide:
			self.payerLink.msg_haveNoRoute(self)
		else:
			self.payeeLink.msg_haveNoRoute(self)



