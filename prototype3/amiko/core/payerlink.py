#    payerlink.py
#    Copyright (C) 2015 by CJP
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

import threading
import copy
import time

from ..utils import utils

import messages
import log

import serializable



class PayerLink(serializable.Serializable):
	states = utils.Enum([
		"initial", "hasReceipt", "confirmed",
		"hasPayerRoute", "hasPayeeRoute",
		"locked", "cancelled", "receivedCommit", "committed"
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
		'meetingPointID': None,
		'state': states.initial
	}


	def __init__(self, **kwargs):
		serializable.Serializable.__init__(self, **kwargs)

		# Will be set when receipt message is received from payee, or in case of time-out
		self.__receiptReceived = threading.Event()

		# Will be set when transaction is committed or cancelled, or in case of time-out
		self.__finished = threading.Event()

		#TODO: recover from a state where one of the above events can be set,
		#but the user interface is not waiting for it anymore after a re-start.


	def __deepcopy__(self, memo):
		#This is called indirectly from serializable.py.
		#It overrides default deepcopy behavior to work around a problem with
		#threading.Event objects
		return PayerLink(
			payeeHost      = self.payeeHost,
			payeePort      = self.payeePort,
			payeeLinkID    = self.payeeLinkID,
			amount         = self.amount,
			receipt        = self.receipt,
			transactionID  = self.transactionID,
			token          = self.token,
			meetingPointID = self.meetingPointID,
			state          = self.state
		)


	def getTimeoutMessage(self):
		return messages.Timeout(state=self.state)


	def waitForReceipt(self):
		self.__receiptReceived.wait()


	def waitForFinished(self):
		#TODO: timeout mechanism
		self.__finished.wait()


	def handleMessage(self, msg):
		return \
		{
		messages.Timeout          : self.msg_timeout,
		messages.Receipt          : self.msg_receipt,
		messages.PayerLink_Confirm: self.msg_confirm,
		messages.HavePayerRoute   : self.msg_havePayerRoute,
		messages.HavePayeeRoute   : self.msg_havePayeeRoute
		}[msg.__class__](msg)


	def msg_timeout(self, msg):
		ret = []
		if self.state == self.states.initial and msg.state == self.states.initial:
			#Receipt time-out
			log.log("Payer: receipt time-out -> cancelled")
			self.state = self.states.cancelled
			self.__receiptReceived.set()
		elif self.state == self.states.receivedCommit and msg.state == self.states.receivedCommit:
			#settleCommit time-out: assume settled anyway, since we've received the commit token
			log.log("Payer: settleCommit time-out -> committed")
			self.state = self.states.committed
			self.__finished.set()
		elif self.state in (self.states.confirmed, self.states.hasPayerRoute, self.states.hasPayeeRoute) and msg.state == self.states.confirmed:
			log.log("Payer: routing time-out -> cancelled")
			self.state = self.states.cancelled
			ret += \
				[
				messages.CancelRoute(transactionID=self.transactionID, payerSide=True),
				messages.OutboundMessage(localID = messages.payerLocalID, message = \
					messages.Cancel(ID=self.payeeLinkID)
					)
				]
			self.__finished.set()
		else:
			log.log("Payer: time-out of state %s no longer applicable: we are now in state %s" % \
				(msg.state, self.state))

		return ret


	def msg_receipt(self, msg):
		log.log("PayerLink: Received payment receipt")

		self.amount = msg.amount
		self.receipt = msg.receipt
		self.transactionID = msg.transactionID
		self.meetingPointID = msg.meetingPoints[0] #TODO: more intelligent choice
		self.state = self.states.hasReceipt
		self.__receiptReceived.set()

		return []


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
				messages.Confirm(ID=self.payeeLinkID, meetingPointID=self.meetingPointID)
			),
			messages.MakeRoute( #This will start the transaction routing
				amount=self.amount,
				transactionID=self.transactionID,
				startTime=None, #Will be received from the payee side
				endTime=None, #Will be received from the payee side
				meetingPointID=self.meetingPointID,
				ID=messages.payerLocalID,
				isPayerSide=True
				),
			messages.TimeoutMessage(timestamp=time.time()+5.0, message=\
				self.getTimeoutMessage()  #Add time-out to routing
				)
			]

		else:
			self.state = self.states.cancelled

			self.__finished.set()

			ret = \
			[
			messages.OutboundMessage(localID = messages.payerLocalID, message = \
				messages.Cancel(ID=self.payeeLinkID)
			)
			]

		return ret


	def msg_havePayerRoute(self, msg):
		log.log("Payer: HavePayerRoute received")

		self.state = \
		{
		self.states.confirmed    : self.states.hasPayerRoute,
		self.states.hasPayeeRoute: self.states.locked
		}[self.state]

		ret = []

		#If both routes are present, start locking
		if self.state == self.states.locked:
			ret.append(
				messages.Lock(transactionID=self.transactionID, payload=[])
				)

		return ret


	def msg_havePayeeRoute(self, msg):
		log.log("Payer: HavePayeeRoute received")

		self.state = \
		{
		self.states.confirmed    : self.states.hasPayeeRoute,
		self.states.hasPayerRoute: self.states.locked
		}[self.state]

		ret = []

		#If both routes are present, start locking
		if self.state == self.states.locked:
			ret.append(
				messages.Lock(transactionID=self.transactionID, payload=[])
				)

		return ret


	def makeRouteIncoming(self, msg):
		return [] #NOP


	def haveNoRouteOutgoing(self, transactionID, payerID, isPayerSide):
		#TODO: go to state cancelled
		return [] #NOP


	def cancelIncoming(self, msg):
		return [] #NOP


	def cancelOutgoing(self, msg, payerID):
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


	def lockIncoming(self, msg):
		return [] #This is called when our own lock message is processed -> NOP


	def commitOutgoing(self, msg, payerID):
		if self.state != self.states.locked:
			raise Exception(
				"commitOutgoing should not be called in state %s" % \
					self.state
				)
		self.state = self.states.receivedCommit
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
		self.__finished.set()

		return []


serializable.registerClass(PayerLink)

