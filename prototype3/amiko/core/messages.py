#    messages.py
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



#Note: local link IDs and payee IDs should never be made equal to this!
#TODO: enforce the above rule
payerLocalID = "__payer__"



################################################################################
# Non-serializable messages, for immediate, internal use only:
################################################################################

#Abstract base class
class NonserializableMessage:
	def __init__(self, **kwargs):
		attributes = self.__class__.attributes
		for name in attributes.keys():
			setattr(self, name, copy.deepcopy(
					kwargs[name]
				if name in kwargs else
					attributes[name] #default value
				))


class BitcoinCommand(NonserializableMessage):
	attributes = {
		#Function accepts a bitcoind object as argument. The return value will
		#be emitted, wrapped in a BitcoinReturnValue message.
		'function': (lambda bitcoind: (None, None)),
		'returnID': '',
		'returnChannelIndex': 0}


class BitcoinReturnValue(NonserializableMessage):
	attributes = {'value': None, 'ID': '', 'channelIndex': 0}


class Confirmation(NonserializableMessage):
	attributes = {'localID': '', 'index':0}


class PayerLink_Confirm(NonserializableMessage):
	attributes = {'agreement':False}


class MakePayer(NonserializableMessage):
	attributes = {'host':'', 'port':0, 'payeeLinkID': ''}


class MakeLink(NonserializableMessage):
	attributes = {
		'localHost': None,
		'localPort': None,
		'localID': '',
		'remoteHost': None,
		'remotePort': None,
		'remoteID': None}


class Link_Deposit(NonserializableMessage):
	attributes = {'ID': '', 'channel': None}


class Link_Withdraw(NonserializableMessage):
	attributes = {'ID': '', 'channelIndex': 0}


class ReturnValue(NonserializableMessage):
	attributes = {'value':''}


class PaymentRequest(NonserializableMessage):
	attributes = {'amount':0, 'receipt':'', 'meetingPoints':[]}



################################################################################
# Serializable messages, for external communication and/or time-outs:
################################################################################

class Connect(serializable.Serializable):
	"""
	This is a base class for messages that indicate a connection ID
	(Link and Pay).
	"""
	serializableAttributes = {'ID': '', 'dice': 0}


class Pay(Connect):
	pass
serializable.registerClass(Pay)


class ConnectLink(Connect):
	serializableAttributes = {
		'ID': '',
		'dice': 0,
		'callbackHost': None,
		'callbackPort': None,
		'callbackID': None
		}
serializable.registerClass(ConnectLink)


class OutboundMessage(serializable.Serializable):
	serializableAttributes = {'localID': '', 'message': None}
serializable.registerClass(OutboundMessage)


class Timeout(serializable.Serializable):
	serializableAttributes = {'state':''}
serializable.registerClass(Timeout)


class ChannelMessage(serializable.Serializable):
	serializableAttributes = {'ID': '', 'channelIndex': 0, 'message': None}
serializable.registerClass(ChannelMessage)


class Receipt(serializable.Serializable):
	serializableAttributes = {'amount':0, 'receipt':'', 'transactionID':'', 'meetingPoints':[]}
serializable.registerClass(Receipt)


class Confirm(serializable.Serializable):
	serializableAttributes = {"ID": None, "meetingPointID": ""}
serializable.registerClass(Confirm)


class Cancel(serializable.Serializable):
	serializableAttributes = {"ID": None}
serializable.registerClass(Cancel)


class MakeRoute(serializable.Serializable):
	serializableAttributes = \
	{
		'amount': 0,
		'transactionID': '',
		'startTime': None,
		'endTime': None,
		'meetingPointID': '',
		'ID': '',
		'channelIndex': 0,
		'isPayerSide': False
	}
serializable.registerClass(MakeRoute)


class CancelRoute(serializable.Serializable):
	serializableAttributes = {'transactionID': '', 'payerSide': None}
serializable.registerClass(CancelRoute)


class HavePayerRoute(serializable.Serializable):
	serializableAttributes = {'ID': '', 'transactionID': ''}
serializable.registerClass(HavePayerRoute)


class HavePayeeRoute(serializable.Serializable):
	serializableAttributes = {'ID': '', 'transactionID': ''}
serializable.registerClass(HavePayeeRoute)


class HaveNoRoute(serializable.Serializable):
	serializableAttributes = {'ID': '', 'transactionID': ''}
serializable.registerClass(HaveNoRoute)


class Deposit(serializable.Serializable):
	serializableAttributes = {'ID': '', 'channelIndex': 0, 'channelClass': ''} #TODO: add payload?
serializable.registerClass(Deposit)


class Lock(serializable.Serializable):
	serializableAttributes = {'transactionID': ''} #TODO: add payload
serializable.registerClass(Lock)


class Commit(serializable.Serializable):
	serializableAttributes = {'token': ''}
serializable.registerClass(Commit)


class SettleCommit(serializable.Serializable):
	serializableAttributes = {'ID': '', 'token': ''} #TODO: add payload
serializable.registerClass(SettleCommit)


class TimeoutMessage(serializable.Serializable):
	serializableAttributes = {'timestamp': 0.0, 'message': None}
serializable.registerClass(TimeoutMessage)

