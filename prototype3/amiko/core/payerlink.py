#    payerlink.py
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

import messages
import log
import linkbase

from ..utils import serializable



class PayerLink(linkbase.LinkBase, serializable.Serializable):
	states = utils.Enum([
		"initial", "hasReceipt", "confirmed",
		"hasPayerRoute", "hasPayeeRoute",
		"locked", "cancelled", "receivedRequestCommit", "committed"
		])

	serializableAttributes = \
	{
		'payeeHost':      None,
		'payeePort':      None,
		'payeeLinkID':    None,

		'amount' :        None,
		'receipt':        None,
		'transactionID':  None,
		'token'  :        None,

		'routingContext': None,
		'meetingPointID': None,

		'state': states.initial
	}


	def getTimeoutMessage(self):
		return messages.PayerTimeout(state=self.state)


	def handleMessage(self, msg):
		return \
		{
		messages.PayerTimeout     : self.msg_timeout,
		messages.Receipt          : self.msg_receipt,
		messages.PayerLink_Confirm: self.msg_confirm,
		messages.Cancel           : self.msg_cancel,
		}[msg.__class__](msg)


	def msg_timeout(self, msg):
		if self.state == self.states.initial and msg.state == self.states.initial:
			#Receipt time-out
			log.log("Payer: receipt time-out -> cancelled")
			self.state = self.states.cancelled
			return self.__removeTimeouts() + \
			[
				messages.SetEvent(event=messages.SetEvent.events.receiptReceived)
			]

		elif self.state == self.states.receivedRequestCommit and msg.state == self.states.receivedRequestCommit:
			#settleCommit time-out: assume settled anyway, since we've received the commit token
			log.log("Payer: settleCommit time-out -> committed")
			self.state = self.states.committed
			return self.__removeTimeouts() + \
			[
				messages.SetEvent(event=messages.SetEvent.events.paymentFinished)
			]

		log.log("Payer: time-out of state %s no longer applicable: we are now in state %s" % \
			(msg.state, self.state))

		return []


	def msg_receipt(self, msg):
		log.log("PayerLink: Received payment receipt")

		self.amount = msg.amount
		self.receipt = msg.receipt
		self.transactionID = msg.transactionID
		self.meetingPointID = msg.meetingPoints[0] #TODO: more intelligent choice
		self.state = self.states.hasReceipt

		return [messages.SetEvent(event=messages.SetEvent.events.receiptReceived)]


	def msg_confirm(self, msg):
		log.log("PayerLink: Received confirm: %s" % str(msg.agreement))

		if self.state != self.states.hasReceipt:
			raise Exception(
				"msg_confirm should not be called in state %s" % \
					self.state
				)

		ret = []

		if msg.agreement:
			self.state = self.states.confirmed

			ret = \
			[
			messages.OutboundMessage(localID = messages.payerLocalID, message = \
				messages.Confirm(meetingPointID=self.meetingPointID)
			),
			messages.MakeRoute( #This will start the transaction routing
				ID=messages.payerLocalID,
				routingContext=self.routingContext,
				amount=self.amount,
				transactionID=self.transactionID,
				startTime=None, #Will be received from the payee side
				endTime=None, #Will be received from the payee side
				meetingPointID=self.meetingPointID,
				isPayerSide=True
				)
			]

		else:
			self.state = self.states.cancelled

			ret = self.__removeTimeouts() + \
			[
			messages.OutboundMessage(localID = messages.payerLocalID, message = \
				messages.Cancel()
			),
			messages.SetEvent(event=messages.SetEvent.events.paymentFinished)
			]

		return ret


	def msg_cancel(self, msg):
		log.log("Payer: Cancel received")
		if self.state not in (self.states.confirmed, self.states.hasPayerRoute):
			raise Exception(
				"msg_cancel should not be called in state %s" % \
					self.state
				)

		self.state = self.states.cancelled

		return self.__removeTimeouts() + \
		[
			messages.CancelRoute(transactionID=self.transactionID, isPayerSide=True),
			messages.SetEvent(event=messages.SetEvent.events.paymentFinished)
		]


	def haveNoRouteOutgoing(self, transactionID, isPayerSide):
		self.state = self.states.cancelled

		return self.__removeTimeouts() + \
		[
		messages.OutboundMessage(localID = messages.payerLocalID, message = \
			messages.Cancel()
		),
		messages.SetEvent(event=messages.SetEvent.events.paymentFinished)
		]


	def cancelOutgoing(self, msg):
		if self.state not in \
			(
			self.states.confirmed,
			self.states.hasPayerRoute,
			self.states.hasPayeeRoute,
			self.states.cancelled
			):
			raise Exception(
				"cancelOutgoing should not be called in state %s" % \
					self.state
				)

		return []


	def haveRouteOutgoing(self, msg):
		log.log("Payer: HaveRoute received (payer side)")

		self.state = \
		{
		self.states.confirmed    : self.states.hasPayerRoute,
		self.states.hasPayeeRoute: self.states.locked
		}[self.state]

		return self.__getHaveRouteResponse()


	def haveRouteIncoming(self, msg):
		log.log("Payer: HaveRoute received (payee side)")

		self.state = \
		{
		self.states.confirmed    : self.states.hasPayeeRoute,
		self.states.hasPayerRoute: self.states.locked
		}[self.state]

		return self.__getHaveRouteResponse()


	def __getHaveRouteResponse(self):
		#If both routes are present, start locking
		if self.state == self.states.locked:
			return [
				messages.Lock(
					ID=messages.payerLocalID,
					transactionID=self.transactionID,
					isPayerSide=True,
					amount=self.amount,
					startTime=None, #TODO
					endTime=None,   #TODO
					channelIndex=None #To be filled in by an outgoing link
					)
				]

		return []


	def requestCommitOutgoing(self, msg):
		if self.state != self.states.locked:
			raise Exception(
				"requestCommitOutgoing should not be called in state %s" % \
					self.state
				)
		self.state = self.states.receivedRequestCommit
		self.token = msg.token #TODO: maybe check?

		return \
		[
		messages.TimeoutMessage(timestamp=time.time()+1.0, message=\
			self.getTimeoutMessage()  #Add time-out to go to commit
		)
		]


	def settleCommitIncoming(self, msg):
		#TODO: receive token, and check it!

		log.log("Payer: received settleCommit -> committed")
		self.state = self.states.committed

		return self.__removeTimeouts() + \
		[
			messages.SetEvent(event=messages.SetEvent.events.paymentFinished)
		]


	def settleRollbackOutgoing(self, msg):
		if self.state != self.states.locked:
			raise Exception(
				"settleRollbackOutgoing should not be called in state %s" % \
					self.state
				)

		log.log("Payer: received settleRollback -> cancelled")
		self.state = self.states.cancelled

		return self.__removeTimeouts() + \
		[
		messages.OutboundMessage(localID = messages.payerLocalID, message = \
			messages.Cancel()
		),
		messages.SetEvent(event=messages.SetEvent.events.paymentFinished)
		]


	def __removeTimeouts(self):
		return [messages.FilterTimeouts(function = lambda message:
			not isinstance(message, messages.PayerTimeout)
			)]

serializable.registerClass(PayerLink)

