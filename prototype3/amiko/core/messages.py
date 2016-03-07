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
from ..utils import utils



#Note: local link IDs and payee IDs should never be made equal to this!
#TODO: enforce the above rule
payerLocalID = "__payer__"



################################################################################
# Non-serializable messages, for immediate, internal use only:
################################################################################

#Abstract base class
class Message:
	def __init__(self, **kwargs):
		attributes = self.__class__.attributes
		for name in attributes.keys():
			setattr(self, name, copy.deepcopy(
					kwargs[name]
				if name in kwargs else
					attributes[name] #default value
				))


class BitcoinCommand(Message):
	attributes = {
		#Function accepts a bitcoind object as argument. The return value will
		#be emitted, wrapped in a BitcoinReturnValue message.
		'function': (lambda bitcoind: (None, None)),
		'returnID': '',
		'returnChannelIndex': 0}


class BitcoinReturnValue(Message):
	attributes = {'value': None, 'ID': '', 'channelIndex': 0}


class Confirmation(Message):
	attributes = {'localID': '', 'index':0}


class PayerLink_Confirm(Message):
	attributes = {'agreement':False}


class MakePayer(Message):
	attributes = {'host':'', 'port':0, 'payeeLinkID': '', 'routingContext': None}


class MakeLink(Message):
	attributes = {
		'localHost': None,
		'localPort': None,
		'localID': '',
		'remoteHost': None,
		'remotePort': None,
		'remoteID': None}


class MakeMeetingPoint(Message):
	attributes = {'name': ''}


class Link_Deposit(Message):
	attributes = {'ID': '', 'channel': None}


class Link_Withdraw(Message):
	attributes = {'ID': '', 'channelIndex': 0}


class PaymentRequest(Message):
	attributes = {'amount':0, 'receipt':'', 'meetingPoints':[], 'routingContext': None}


class ReturnValue(Message):
	attributes = {'value':''}


class SetEvent(Message):
	events = utils.Enum(['receiptReceived', 'paymentFinished'])
	attributes = {'event': None}



################################################################################
# Serializable messages, for external communication:
################################################################################


#Abstract base class
class ProtocolMessage(serializable.Serializable, Message):
	def __init__(self, **kwargs):
		Message.__init__(self, **kwargs)
		serializable.Serializable.__init__(self, **kwargs)


class Pay(ProtocolMessage):
	attributes = {}
	serializableAttributes = {'ID': ''}
serializable.registerClass(Pay)


class ConnectLink(ProtocolMessage):
	attributes = {}
	serializableAttributes = {
		'ID': '',
		'dice': 0,
		'callbackHost': None,
		'callbackPort': None,
		'callbackID': None
		}
serializable.registerClass(ConnectLink)


class ChannelMessage(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'channelIndex': 0, 'message': None}
serializable.registerClass(ChannelMessage)


class Deposit(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'channelIndex': 0, 'channelClass': ''} #TODO: add payload?
serializable.registerClass(Deposit)


class Receipt(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'amount':0, 'receipt':'', 'transactionID':'', 'meetingPoints':[]}
serializable.registerClass(Receipt)


class Confirm(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'meetingPointID': ''}
serializable.registerClass(Confirm)


class Cancel(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {}
serializable.registerClass(Cancel)


class MakeRoute(ProtocolMessage):
	attributes = {'ID': None, 'routingContext': None}
	serializableAttributes = \
	{
		'amount': 0,
		'transactionID': '',
		'startTime': None,
		'endTime': None,
		'meetingPointID': '',
		'channelIndex': 0,
		'isPayerSide': False
	}
serializable.registerClass(MakeRoute)


class CancelRoute(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'transactionID': '', 'isPayerSide': None}
serializable.registerClass(CancelRoute)


class HaveNoRoute(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'transactionID': '', 'isPayerSide': None}
serializable.registerClass(HaveNoRoute)


class HaveRoute(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'transactionID': '', 'isPayerSide': None}
serializable.registerClass(HaveRoute)


class Lock(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'transactionID': '', 'isPayerSide': None} #TODO: add payload
serializable.registerClass(Lock)


class RequestCommit(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'token': '', 'isPayerSide': None}
serializable.registerClass(RequestCommit)


class SettleCommit(ProtocolMessage):
	attributes = {'ID': None}
	serializableAttributes = {'token': '', 'isPayerSide': None} #TODO: add payload
serializable.registerClass(SettleCommit)


################################################################################
# Serializable messages, for internal use (e.g. time-outs):
################################################################################


class OutboundMessage(serializable.Serializable):
	serializableAttributes = {'localID': '', 'message': None}
serializable.registerClass(OutboundMessage)


class TimeoutMessage(serializable.Serializable):
	serializableAttributes = {'timestamp': 0.0, 'message': None}
serializable.registerClass(TimeoutMessage)


class PayerTimeout(serializable.Serializable):
	serializableAttributes = {'state':''}
serializable.registerClass(PayerTimeout)


class NodeStateTimeout_Route(serializable.Serializable):
	serializableAttributes = {'transactionID': '', 'isPayerSide': None, 'payerID': ''}
serializable.registerClass(NodeStateTimeout_Route)

