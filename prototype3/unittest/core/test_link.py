#!/usr/bin/env python
#    test_link.py
#    Copyright (C) 2016 by CJP
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

import unittest

import testenvironment

from amiko.utils import serializable

from amiko.core import messages
from amiko.core import settings

from amiko.core import link


class DummyChannel(serializable.Serializable):
	serializableAttributes = {'state': [], 'hasRouteReturn': False}

	def handleMessage(self, msg):
		if msg is None:
			self.state.append(['handleMessage', None])
		else:
			self.state.append(['handleMessage', msg.ID, msg.channelIndex, msg.message])

		return ['handleMessage'], None


	def hasRoute(self, routeID):
		self.state.append(routeID)
		return self.hasRouteReturn
 

	def __getattr__(self, name):
		if name.startswith('__'):
			raise AttributeError(name)

		def generic_method(*args, **kwargs):
			#print self, (name, args, kwargs)
			self.state.append((name, args, kwargs))
			return [name], None

		return generic_method


serializable.registerClass(DummyChannel)



class Test(unittest.TestCase):
	def setUp(self):
		self.link = link.Link(remoteID='remote', localID='local', channels=[])


	def test_defaultAttributes(self):
		'Test default attributes'

		self.assertEqual(self.link.remoteID, 'remote')
		self.assertEqual(self.link.localID, 'local')
		self.assertEqual(self.link.channels, [])


	def test_msg_ownDeposit(self):
		'test msg_ownDeposit'

		channel = DummyChannel(state=['initial'])

		ret = self.link.handleMessage(messages.Link_Deposit(
			ID=None, channel=channel))

		self.assertEqual(len(ret), 2)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.Deposit))
		self.assertEqual(msg.channelIndex, 0)
		self.assertEqual(msg.channelClass, 'DummyChannel')
		msg = ret[1]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 0)
		self.assertEqual(msg.message, 'handleMessage')

		self.assertEqual(len(self.link.channels), 1)
		channel = self.link.channels[0]
		self.assertTrue(isinstance(channel, DummyChannel))
		self.assertEqual(channel.state, ['initial', ['handleMessage', None]])

		#Attempt to deposit when remoteID is None:
		self.link = link.Link(remoteID=None, localID='local', channels=[])
		channel = DummyChannel(state=['initial'])
		self.assertRaises(Exception, self.link.handleMessage,
			messages.Link_Deposit(ID=None, channel=channel))


	def test_msg_peerDeposit(self):
		'test msg_peerDeposit'

		ret = self.link.handleMessage(messages.Deposit(
			ID=None, channelIndex=0, channelClass='DummyChannel'))

		self.assertEqual(ret, [])

		self.assertEqual(len(self.link.channels), 1)
		channel = self.link.channels[0]
		self.assertTrue(isinstance(channel, DummyChannel))
		self.assertEqual(channel.state, [])

		#Invalid channel index (should be 1 after the above):
		self.assertRaises(Exception, self.link.handleMessage, messages.Deposit(
			ID=None, channelIndex=0, channelClass='DummyChannel'))
		self.assertRaises(Exception, self.link.handleMessage, messages.Deposit(
			ID=None, channelIndex=2, channelClass='DummyChannel'))


	def test_msg_ownWithdraw(self):
		'test msg_ownWithdraw'

		self.link.channels.append(DummyChannel())

		ret = self.link.handleMessage(messages.Link_Withdraw(
			ID=None, channelIndex=0))

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 0)
		self.assertEqual(msg.message, 'startWithdraw')

		channel = self.link.channels[0]
		self.assertEqual(channel.state, [('startWithdraw', (), {})])

		self.assertRaises(Exception, self.link.handleMessage,
			messages.Link_Withdraw(ID=None, channelIndex=-1))
		self.assertRaises(Exception, self.link.handleMessage,
			messages.Link_Withdraw(ID=None, channelIndex=1))


	def test_msg_haveRoute(self):
		'test msg_haveRoute'

		msg_in = messages.HaveRoute(
			ID=None,
			transactionID='foobar',
			isPayerSide=True,
			startTime=123,
			endTime=456
			)

		ret = self.link.handleMessage(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertFalse(msg is msg_in)
		self.assertTrue(isinstance(msg, messages.HaveRoute))
		self.assertEqual(msg.ID, 'remote')
		self.assertEqual(msg.transactionID, msg_in.transactionID)
		self.assertEqual(msg.isPayerSide, msg_in.isPayerSide)
		self.assertEqual(msg.startTime, msg_in.startTime)
		self.assertEqual(msg.endTime, msg_in.endTime)


	def test_msg_bitcoinReturnValue(self):
		'test msg_bitcoinReturnValue'

		ret = self.link.handleMessage(messages.BitcoinReturnValue(
			ID=None, value=(['foobar'], None), channelIndex=3))

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 3)
		self.assertEqual(msg.message, 'foobar')


	def test_makeRouteOutgoing(self):
		'test makeRouteOutgoing'

		msg_in = messages.MakeRoute(
			amount=42,
			transactionID='foobar',
			startTime=123,
			endTime=456,
			meetingPointID='meetingPoint',
			channelIndex=None,
			isPayerSide=True
			)

		ret = self.link.makeRouteOutgoing(msg_in)
		self.assertEqual(len(ret), 0)

		self.link.channels.append(DummyChannel())
		self.link.channels[0].reserve = lambda x: None
		self.link.channels.append(DummyChannel())

		ret = self.link.makeRouteOutgoing(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertFalse(msg is msg_in)
		self.assertTrue(isinstance(msg, messages.MakeRoute))
		self.assertEqual(msg.amount, msg_in.amount)
		self.assertEqual(msg.transactionID, msg_in.transactionID)
		self.assertEqual(msg.startTime, msg_in.startTime)
		self.assertEqual(msg.endTime, msg_in.endTime)
		self.assertEqual(msg.meetingPointID, msg_in.meetingPointID)
		self.assertEqual(msg.isPayerSide, msg_in.isPayerSide)
		self.assertEqual(msg.channelIndex, 1)

		#TODO: check that the state of the first channel is restored

		self.assertEqual(self.link.channels[1].state,
			[('reserve', (True, '1foobar', 123, 456, 42), {})])


	def test_makeRouteIncoming(self):
		'test makeRouteIncoming'

		msg_in = messages.MakeRoute(
			amount=42,
			transactionID='foobar',
			startTime=123,
			endTime=456,
			meetingPointID='meetingPoint',
			channelIndex=1,
			isPayerSide=True
			)

		self.assertRaises(Exception, self.link.makeRouteIncoming, msg_in)

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		ret = self.link.makeRouteIncoming(msg_in)

		self.assertEqual(len(ret), 0)

		self.assertEqual(self.link.channels[0].state, [])
		self.assertEqual(self.link.channels[1].state, [('reserve', (False, '1foobar', 123, 456, 42), {})])


	def test_haveNoRouteOutgoing(self):
		'test haveNoRouteOutgoing'

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.haveNoRouteOutgoing, 'foobar', True)
		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.haveNoRouteOutgoing('foobar', True)

		self.assertEqual(len(ret), 2)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'unreserve')
		msg = ret[1]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.HaveNoRoute))
		self.assertEqual(msg.transactionID, 'foobar')
		self.assertEqual(msg.isPayerSide, True)

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])

		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('unreserve', (False, '1foobar'), {})])


	def test_haveNoRouteIncoming(self):
		'test haveNoRouteIncoming'

		msg_in = messages.HaveNoRoute(
			transactionID='foobar',
			isPayerSide=True
			)

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.haveNoRouteIncoming, msg_in)
		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.haveNoRouteIncoming(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'unreserve')

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])

		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('unreserve', (True, '1foobar'), {})])


	def test_cancelOutgoing(self):
		'test cancelOutgoing'

		msg_in = messages.CancelRoute(
			transactionID='foobar',
			isPayerSide=True
			)

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.cancelOutgoing, msg_in)
		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.cancelOutgoing(msg_in)

		self.assertEqual(len(ret), 2)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'unreserve')
		msg = ret[1]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertFalse(msg is msg_in)
		self.assertTrue(isinstance(msg, messages.CancelRoute))
		self.assertEqual(msg.transactionID, msg_in.transactionID)
		self.assertEqual(msg.isPayerSide, msg_in.isPayerSide)

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])

		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('unreserve', (True, '1foobar'), {})])


	def test_cancelIncoming(self):
		'test cancelIncoming'

		msg_in = messages.CancelRoute(
			transactionID='foobar',
			isPayerSide=True
			)

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.cancelIncoming, msg_in)
		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.cancelIncoming(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'unreserve')

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])

		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('unreserve', (False, '1foobar'), {})])


	def test_lockOutgoing(self):
		'test lockOutgoing'

		msg_in = messages.Lock(
			amount=42,
			transactionID='foobar',
			startTime=123,
			endTime=456,
			channelIndex=None,
			isPayerSide=True
			)

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.lockOutgoing, msg_in)
		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.lockOutgoing(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertFalse(msg is msg_in)
		self.assertTrue(isinstance(msg, messages.Lock))
		self.assertEqual(msg.amount, msg_in.amount)
		self.assertEqual(msg.transactionID, msg_in.transactionID)
		self.assertEqual(msg.startTime, msg_in.startTime)
		self.assertEqual(msg.endTime, msg_in.endTime)
		self.assertEqual(msg.isPayerSide, msg_in.isPayerSide)
		self.assertEqual(msg.channelIndex, 1)
		#TODO: payload

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])

		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('lockOutgoing', ('1foobar',), {})])


	def test_lockIncoming(self):
		'test lockIncoming'

		msg_in = messages.Lock(
			amount=42,
			transactionID='foobar',
			startTime=123,
			endTime=456,
			channelIndex=None,
			isPayerSide=True
			)
		#TODO: payload

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.lockIncoming, msg_in)
		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.lockIncoming(msg_in)

		self.assertEqual(len(ret), 0)

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])

		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('lockIncoming', ('1foobar',), {})])


	def test_requestCommitOutgoing(self):
		'test requestCommitOutgoing'

		msg_in = messages.RequestCommit(
			token='foobar',
			isPayerSide=True
			)

		ret = self.link.requestCommitOutgoing(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertFalse(msg is msg_in)
		self.assertTrue(isinstance(msg, messages.RequestCommit))
		self.assertEqual(msg.token, msg_in.token)
		self.assertEqual(msg.isPayerSide, msg_in.isPayerSide)


	def test_requestCommitIncoming(self):
		'test requestCommitIncoming'

		#TODO: hash check

		msg_in = messages.RequestCommit(
			token='foobar',
			isPayerSide=True
			)

		ret = self.link.requestCommitIncoming(msg_in)

		self.assertEqual(len(ret), 0)


	def test_settleCommitOutgoing(self):
		'test settleCommitOutgoing'

		msg_in = messages.SettleCommit(
			token='foobar',
			isPayerSide=True
			)
		expectedRouteID = '1' + settings.hashAlgorithm('foobar')

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		ret = self.link.settleCommitOutgoing(msg_in)

		self.assertEqual(len(ret), 0)

		self.assertEqual(self.link.channels[0].state,
			[expectedRouteID])
		self.assertEqual(self.link.channels[1].state,
			[expectedRouteID])

		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.settleCommitOutgoing(msg_in)

		self.assertEqual(len(ret), 2)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'settleCommitOutgoing')
		msg = ret[1]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertFalse(msg is msg_in)
		self.assertTrue(isinstance(msg, messages.SettleCommit))
		self.assertEqual(msg.token, msg_in.token)
		self.assertEqual(msg.isPayerSide, msg_in.isPayerSide)

		self.assertEqual(self.link.channels[0].state,
			[expectedRouteID])
		self.assertEqual(self.link.channels[1].state,
			[expectedRouteID, ('settleCommitOutgoing', (expectedRouteID, 'foobar'), {})])


	def test_settleCommitIncoming(self):
		'test settleCommitIncoming'

		msg_in = messages.SettleCommit(
			token='foobar',
			isPayerSide=True
			)
		expectedRouteID = '1' + settings.hashAlgorithm('foobar')

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.settleCommitIncoming, msg_in)

		self.assertEqual(self.link.channels[0].state,
			[expectedRouteID])
		self.assertEqual(self.link.channels[1].state,
			[expectedRouteID])

		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.settleCommitIncoming(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'settleCommitIncoming')

		self.assertEqual(self.link.channels[0].state,
			[expectedRouteID])
		self.assertEqual(self.link.channels[1].state,
			[expectedRouteID, ('settleCommitIncoming', (expectedRouteID,), {})])


	def test_settleRollbackOutgoing(self):
		'test settleRollbackOutgoing'

		msg_in = messages.SettleRollback(
			transactionID='foobar',
			isPayerSide=True
			)

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.settleRollbackOutgoing, msg_in)

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])
		self.assertEqual(self.link.channels[1].state,
			['1foobar'])

		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.settleRollbackOutgoing(msg_in)

		self.assertEqual(len(ret), 2)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'settleRollbackOutgoing')
		msg = ret[1]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertFalse(msg is msg_in)
		self.assertTrue(isinstance(msg, messages.SettleRollback))
		self.assertEqual(msg.transactionID, msg_in.transactionID)
		self.assertEqual(msg.isPayerSide, msg_in.isPayerSide)

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])
		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('settleRollbackOutgoing', ('1foobar',), {})])


	def test_settleRollbackIncoming(self):
		'test settleRollbackIncoming'

		msg_in = messages.SettleRollback(
			transactionID='foobar',
			isPayerSide=True
			)

		self.link.channels.append(DummyChannel())
		self.link.channels.append(DummyChannel())

		self.assertRaises(Exception, self.link.settleRollbackIncoming, msg_in)

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])
		self.assertEqual(self.link.channels[1].state,
			['1foobar'])

		self.link.channels[0].state = []
		self.link.channels[1].state = []

		self.link.channels[1].hasRouteReturn = True

		ret = self.link.settleRollbackIncoming(msg_in)

		self.assertEqual(len(ret), 1)
		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.OutboundMessage))
		self.assertEqual(msg.localID, 'local')
		msg = msg.message
		self.assertTrue(isinstance(msg, messages.ChannelMessage))
		self.assertEqual(msg.channelIndex, 1)
		self.assertEqual(msg.message, 'settleRollbackIncoming')

		self.assertEqual(self.link.channels[0].state,
			['1foobar'])
		self.assertEqual(self.link.channels[1].state,
			['1foobar', ('settleRollbackIncoming', ('1foobar',), {})])


	def test_handleChannelOutput(self):
		'test handleChannelOutput'

		ret = self.link.handleChannelOutput(42, (['x', 'y'], None))
		self.assertEqual(len(ret), 2)
		for i,m in enumerate(['x', 'y']):
			msg = ret[i]
			self.assertTrue(isinstance(msg, messages.OutboundMessage))
			self.assertEqual(msg.localID, 'local')
			msg = msg.message
			self.assertTrue(isinstance(msg, messages.ChannelMessage))
			self.assertEqual(msg.channelIndex, 42)
			self.assertEqual(msg.message, m)

		dummyFunc = lambda x: x

		ret = self.link.handleChannelOutput(42, (['x', 'y'], dummyFunc))
		self.assertEqual(len(ret), 3)
		for i,m in enumerate(['x', 'y']):
			msg = ret[i]
			self.assertTrue(isinstance(msg, messages.OutboundMessage))
			self.assertEqual(msg.localID, 'local')
			msg = msg.message
			self.assertTrue(isinstance(msg, messages.ChannelMessage))
			self.assertEqual(msg.channelIndex, 42)
			self.assertEqual(msg.message, m)

		msg = ret[2]
		self.assertTrue(isinstance(msg, messages.BitcoinCommand))
		self.assertEqual(msg.function, dummyFunc)
		self.assertEqual(msg.returnID, 'local')
		self.assertEqual(msg.returnChannelIndex, 42)



if __name__ == '__main__':
	unittest.main(verbosity=2)

