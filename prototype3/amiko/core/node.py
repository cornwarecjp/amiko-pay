#    node.py
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

import randomsource

import link
import payeelink
import meetingpoint
import transaction

import serializable



class Node_PaymentRequest(serializable.Serializable):
	serializableAttributes = {'amount':0, 'receipt':''}
serializable.registerClass(Node_PaymentRequest)



class Node(serializable.Serializable):
	serializableAttributes = {'links':{}, 'payeeLinks':{}, 'meetingPoints':{}, 'transactions':{}}


	def handleMessage(self, msg):
		return \
		{
		Node_PaymentRequest: self.msg_request
		}[msg.__class__](msg)


	def msg_request(self, msg):
		#ID can be nonsecure random:
		#It only needs to be semi-unique, not secret.
		requestID = randomsource.getNonSecureRandom(8).encode("hex")

		#Token must be secure random
		token = randomsource.getSecureRandom(32)

		newPayeeLink = payeelink.PayeeLink(
			receipt=msg.receipt, token=token)
		newTransaction = transaction.Transaction(
			payeeLinkID=requestID,
			amount=msg.amount
			)

		self.payeeLinks[requestID] = newPayeeLink
		#The link has calculated transactionID, based on the token
		self.transactions[newPayeeLink.transactionID] = newTransaction

		#Returned messages:
		return []
		#TODO:
		# - URL to give to payer
		# - Receipt message to be sent to payer, on connect
		#return "amikopay://%s/%s" % \
		#	(self.settings.getAdvertizedNetworkLocation(), requestID)



serializable.registerClass(Node)

