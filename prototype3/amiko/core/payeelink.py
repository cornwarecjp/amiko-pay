#    payeelink.py
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

import time

from ..utils import utils

import log
import settings
import messages
import linkbase

from ..utils import serializable



class PayeeLink(linkbase.LinkBase, serializable.Serializable):
	states = utils.Enum([
		"initial", "confirmed",
		"sentRequestCommit", "cancelled", "committed"
		])

	serializableAttributes = \
	{
		'state': states.initial,

		'ID': '',
		'amount': 0,
		'receipt': None,
		'token': None,

		'routingContext': None,
		'meetingPoints': [],
		'meetingPointID': ''
	}

	def __init__(self, **kwargs):
		serializable.Serializable.__init__(self, **kwargs)

		#This will fail if token is not set (is None).
		#So, token must always be set for successful construction.
		self.transactionID = settings.hashAlgorithm(self.token)


	def handleMessage(self, msg):
		return \
		{
		messages.Pay      : self.msg_pay,
		messages.Confirm  : self.msg_confirm,
		messages.Cancel   : self.msg_cancel,
		messages.HaveRoute: self.msg_haveRoute
		}[msg.__class__](msg)


	def msg_pay(self, msg):
		if self.state != self.states.initial:
			raise Exception(
				"msg_pay should not be called in state %s" % \
					self.state
				)

		return [messages.OutboundMessage(localID = msg.ID, message = \
			messages.Receipt(
				amount=self.amount,
				receipt=self.receipt,
				transactionID=self.transactionID,
				meetingPoints=self.meetingPoints
			))]


	def msg_confirm(self, msg):
		if self.state != self.states.initial:
			raise Exception(
				"msg_confirm should not be called in state %s" % \
					self.state
				)

		if msg.meetingPointID not in self.meetingPoints:
			raise Exception(
				"The meeting point selected by the payer is not in our meeting point list"
				)

		self.state = self.states.confirmed
		self.meetingPointID = msg.meetingPointID

		#End time is the same as start time:
		#this time-out is NOT exceeded on this link, since we already have the
		#token from the beginning.
		startTime = int(time.time())
		endTime = startTime

		return \
		[
			messages.MakeRoute( #This will start the transaction routing
				amount=self.amount,
				transactionID=self.transactionID,
				startTime=startTime,
				endTime=endTime,
				meetingPointID=self.meetingPointID,
				ID=msg.ID,
				routingContext=self.routingContext,
				isPayerSide=False
				)
		]


	def msg_cancel(self, msg):
		if self.state not in (self.states.initial, self.states.confirmed):
			raise Exception(
				"msg_cancel should not be called in state %s" % \
					self.state
				)

		ret = []

		if self.state == self.states.confirmed:
			ret = [messages.CancelRoute(transactionID=self.transactionID, isPayerSide=False)]

		self.state = self.states.cancelled

		return ret


	def msg_haveRoute(self, msg):
		#Simply pass it to the payer, who keeps track of whether the route is complete
		return \
		[
		messages.OutboundMessage(localID = msg.ID, message = \
			messages.HaveRoute(transactionID=None, isPayerSide=False)
			)
		]


	def haveNoRouteOutgoing(self, transactionID, isPayerSide):
		if self.state != self.states.confirmed:
			raise Exception(
				"haveNoRouteOutgoing should not be called in state %s" % \
					self.state
				)

		self.state = self.states.cancelled

		return \
		[
		messages.OutboundMessage(localID = self.ID, message = \
			messages.Cancel()
			)
		]


	def cancelOutgoing(self, msg):
		if self.state not in (self.states.confirmed, self.states.cancelled):
			raise Exception(
				"cancelOutgoing should not be called in state %s" % \
					self.state
				)

		return []


	def lockOutgoing(self, msg):
		log.log("Payee: locked; committing")

		self.state = self.states.sentRequestCommit

		return \
		[
		messages.RequestCommit(ID=self.ID, token=self.token, isPayerSide=False),
		messages.OutboundMessage(localID = self.ID, message = \
			messages.SettleCommit(token=self.token)
			)
		]


	def settleCommitOutgoing(self, msg):
		log.log("Payee: committed")
		self.state = self.states.committed
		return []


serializable.registerClass(PayeeLink)

