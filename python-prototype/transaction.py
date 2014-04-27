#    transaction.py
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



class Transaction:
	def __init__(self, context, routingContext,
		amount, hash, meetingPoint,
		payerLink=None, payeeLink=None):

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
		if self.payeeLink == None:
			return True
		if self.payerLink == None:
			return False
		raise Exception(
			"isPayerSide should only be called when routing is unfinished")


	def msg_makeRoute(self):

		#If we are the meeting point, we're finished:
		if self.__tryMeetingPoint():
			return #found -> finished

		#Note: this will just try the first route.
		#However, if that fails we'll be notified about it, and then
		#we'll try the next, and so on.
		self.__tryNextRoute()


	def msg_haveRoute(self, link):
		log.log("Transaction: haveRoute")
		if self.payeeLink == None:
			self.payeeLink = link
			self.payerLink.msg_haveRoute(self)
		elif self.payerLink == None:
			self.payerLink = link
			self.payeeLink.msg_haveRoute(self)
		else:
			raise Exception(
				"msg_haveRoute should only be called when routing is unfinished")


	def msg_cancelRoute(self):
		log.log("Transaction: cancelRoute")
		#Immediately try next route, or send cancel back if there is none:
		self.__tryNextRoute()


	def msg_endRoute(self):
		log.log("Transaction: endRoute")
		self.__currentRoute.msg_endRoute(self)


	def msg_lock(self):
		log.log("Transaction: lock")
		self.payeeLink.msg_lock(self)


	def msg_commit(self, token):
		log.log("Transaction: commit")
		self.token = token
		self.payeeLink.msg_commit(self)


	def __tryMeetingPoint(self):
		for mp in self.routingContext.meetingPoints:
			if mp.ID == self.meetingPoint:
				self.__currentRoute = mp
				mp.msg_makeRoute(self)
				return True #found

		return False #not found


	def __tryNextRoute(self):
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
			self.payerLink.msg_cancel(self)
		else:
			self.payeeLink.msg_cancel(self)



