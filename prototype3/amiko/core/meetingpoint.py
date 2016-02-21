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

import messages



class MeetingPoint(serializable.Serializable):
	serializableAttributes = {'ID': ''}

	def makeRouteOutgoing(self, msg):
		if msg.meetingPointID != self.ID:
			#This is not the meeting point mentioned in the message, so
			#this meeting point will not be part of the route.
			return \
			[
			messages.HaveNoRoute(
				ID=self.ID, transactionID=msg.transactionID, isPayerSide=msg.isPayerSide)
			]

		return \
		[
		messages.HaveRoute(ID=self.ID, transactionID=msg.transactionID, isPayerSide=msg.isPayerSide)
		]


	def haveNoRouteIncoming(self, msg):
		return [] #This is called when our own HaveNoRoute message is processed -> NOP


	def lockOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.ID
		msg.isPayerSide = False
		return [msg]


	def lockIncoming(self, msg):
		return [] #This is called when our own lock message is processed -> NOP


	def requestCommitOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.ID
		msg.isPayerSide = True
		return [msg]


	def requestCommitIncoming(self, msg):
		return [] #This is called when our own request commit message is processed -> NOP


	def settleCommitOutgoing(self, msg):
		msg = copy.deepcopy(msg)
		msg.ID = self.ID
		msg.isPayerSide = False
		return [msg]


	def settleCommitIncoming(self, msg):
		return [] #This is called when our own settle commit message is processed -> NOP


serializable.registerClass(MeetingPoint)

