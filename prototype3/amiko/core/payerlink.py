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

from ..utils import utils

import network
import payeelink
import log

import serializable



class Timeout(serializable.Serializable):
	serializableAttributes = {'state':''}
serializable.registerClass(Timeout)



class Receipt(serializable.Serializable):
	serializableAttributes = {'amount':0, 'receipt':'', 'transactionID':'', 'meetingPoints':[]}
serializable.registerClass(Receipt)


class PayerLink_Confirm(serializable.Serializable):
	serializableAttributes = {'agreement':False}
serializable.registerClass(PayerLink_Confirm)



class PayerLink(serializable.Serializable):
	states = utils.Enum([
		"initial", "hasReceipt", "confirmed", "hasRoute",
		"locked", "cancelled", "committed"
		])

	serializableAttributes = \
	{
		'amount' :        None, #unknown
		'receipt':        None, #unknown
		'transactionID':  None, #unknown
		'token'  :        None, #unknown
		'meetingPointID': None, #unknown
		'state': states.initial
	}


	def __init__(self, **kwargs):
		serializable.Serializable.__init__(self, **kwargs)

		# Will be set when receipt message is received from payee
		self.__receiptReceived = threading.Event()

		# Will be set when transaction is committed or cancelled
		self.__finished = threading.Event()

		#TODO: recover from a state where one of the above events can be set,
		#but the user interface is not waiting for it anymore after a re-start.


	def __deepcopy__(self, memo):
		#This is called indirectly from serializable.py.
		#It overrides default deepcopy behavior to work around a problem with
		#threading.Event objects
		return PayerLink(
			amount         = self.amount,
			receipt        = self.receipt,
			transactionID  = self.transactionID,
			token          = self.token,
			meetingPointID = self.meetingPointID,
			state          = self.state
		)


	def getTimeoutMessage(self):
		return Timeout(state=self.state)


	def waitForReceipt(self):
		self.__receiptReceived.wait()


	def waitForFinished(self):
		#TODO: timeout mechanism
		self.__finished.wait()


	def handleMessage(self, msg):
		return \
		{
		Timeout          : self.msg_timeout,
		Receipt          : self.msg_receipt,
		PayerLink_Confirm: self.msg_confirm
		}[msg.__class__](msg)


	def msg_timeout(self, msg):
		if self.state == self.states.initial and msg.state == self.states.initial:
			#Receipt time-out
			self.state = self.states.cancelled
			self.__receiptReceived.set()

		return []


	def msg_receipt(self, msg):
		log.log("PayerLink: Received payment receipt")

		self.amount = msg.amount
		self.receipt = msg.receipt
		self.transactionID = msg.transactionID
		#self.meetingPointID = msg.meetingPoints[0] #TODO
		self.state = self.states.hasReceipt #TODO
		self.__receiptReceived.set()

		return []


	def msg_confirm(self, msg):
		log.log("PayerLink: Received confirm: %s" % str(msg.agreement))

		if self.state != self.states.hasReceipt:
			raise Exception(
				"confirmPaymentmsg_confirm should not be called in state %s" % \
					self.state
				)

		ret = []

		if msg.agreement:
			self.state = self.states.confirmed

			ret = \
			[
			(None, network.OutboundMessage(localID = network.payerLocalID, message = \
				payeelink.Confirm(meetingPointID=self.meetingPointID)
			))
			]

			#Note: we don't fill in timestamp values - they will be received
			#from the payee side.
			#TODO
			#self.__transaction = transaction.Transaction(
			#	self.context, self.routingContext, self.__meetingPoint,
			#	self.amount, self.hash,
			#	payerLink=self)

			#This will start the transaction routing
			#self.__transaction.msg_makeRoute()

		else:
			self.state = self.states.cancelled

			ret = \
			[
			(None, network.OutboundMessage(localID = network.payerLocalID, message = \
				payeelink.Cancel()
			))
			]

		return ret


serializable.registerClass(PayerLink)

