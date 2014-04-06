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



class Transaction:
	def __init__(self, context, routingContext,
		amount, hash, meetingPoint,
		payerLink=None, payeeLink=None):

		self.context = context
		self.routingContext = routingContext
		self.amount = amount
		self.hash = hash
		self.meetingPoint = meetingPoint
		self.payerLink = payerLink
		self.payeeLink = payeeLink

		if self.__tryMeetingPoint():
			return #found -> finished

		#TODO: start routing if we're not the meeting point


	def __tryMeetingPoint(self):
		for mp in self.routingContext.meetingPoints:
			if mp.ID == self.meetingPoint:
				mp.addTransaction(self)
				return True #found

		return False #not found


