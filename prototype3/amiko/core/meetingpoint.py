#    meetingpoint.py
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

import copy

from ..utils import serializable

import log

import messages
import linkbase



class MeetingPoint(linkbase.LinkBase, serializable.Serializable):
	serializableAttributes = {'ID': '', 'unmatchedRoutes': {}}

	def makeRouteOutgoing(self, msg):
		if msg.meetingPointID != self.ID:
			log.log('Meeting point: MakeRoute has a different destination')
			#This is not the meeting point mentioned in the message, so
			#this meeting point will not be part of the route.
			return \
			[
			messages.HaveNoRoute(
				ID=self.ID, transactionID=msg.transactionID, isPayerSide=msg.isPayerSide)
			]

		reverseRouteID = self.__makeRouteID(msg.transactionID, not msg.isPayerSide)
		if reverseRouteID in self.unmatchedRoutes:
			log.log('Meeting point: matched MakeRoute; sending HaveRoute')

			if msg.isPayerSide:
				startTime, endTime = self.unmatchedRoutes[reverseRouteID]
			else:
				startTime, endTime = msg.startTime, msg.endTime

			del self.unmatchedRoutes[reverseRouteID]

			return \
			[
			messages.HaveRoute(
				ID=self.ID, transactionID=msg.transactionID, isPayerSide=True,
					startTime=startTime, endTime=endTime),
			messages.HaveRoute(
				ID=self.ID, transactionID=msg.transactionID, isPayerSide=False,
					startTime=startTime, endTime=endTime)
			]

		#else: it is not yet matched
		log.log('Meeting point: MakeRoute is not (yet) matched')
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		self.unmatchedRoutes[routeID] = (msg.startTime, msg.endTime)
		return []


	def cancelOutgoing(self, msg):
		routeID = self.__makeRouteID(msg.transactionID, msg.isPayerSide)
		if routeID in self.unmatchedRoutes:
			#Just remove the unmatched item
			del self.unmatchedRoutes[routeID]
			return []

		#TODO: maybe send HaveNoRoute to the other side?
		#That would just be an optimization, since the other side can decide
		#to time-out on its own.
		return []


	def lockOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.ID
		msg.isPayerSide = False
		return [msg]


	def requestCommitOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.ID
		msg.isPayerSide = True
		return [msg]


	def settleCommitOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.ID
		msg.isPayerSide = False
		return [msg]


	def settleRollbackOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.ID
		msg.isPayerSide = True
		return [msg]


	def __makeRouteID(self, transactionID, isPayerSide):
		return ('1' if isPayerSide else '0') + transactionID


serializable.registerClass(MeetingPoint)

