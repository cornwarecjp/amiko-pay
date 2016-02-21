#!/usr/bin/env python
#    test_meetingpoint.py
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

from amiko.core import messages

from amiko.core import meetingpoint



class Test(unittest.TestCase):
	def setUp(self):
		self.meetingPoint = meetingpoint.MeetingPoint(ID='MPID')

	def test_makeRouteOutgoing(self):
		'Test makeRouteOutgoing'

		#Different ID:
		ret = self.meetingPoint.makeRouteOutgoing(messages.MakeRoute(
			meetingPointID='OtherMP',
			transactionID='foo',
			isPayerSide=True
			))

		self.assertEqual(len(ret), 1)

		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.HaveNoRoute))
		self.assertEqual(msg.ID, 'MPID')
		self.assertEqual(msg.transactionID, 'foo')
		self.assertEqual(msg.isPayerSide, True)

		#Same ID:
		ret = self.meetingPoint.makeRouteOutgoing(messages.MakeRoute(
			meetingPointID='MPID',
			transactionID='foo',
			isPayerSide=True
			))

		self.assertEqual(len(ret), 1)

		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.HaveRoute))
		self.assertEqual(msg.ID, 'MPID')
		self.assertEqual(msg.transactionID, 'foo')
		self.assertEqual(msg.isPayerSide, True)


	def test_lockOutgoing(self):
		'Test lockOutgoing'

		ret = self.meetingPoint.lockOutgoing(messages.Lock(
			ID='foo',
			transactionID='bar',
			isPayerSide=True
			))

		self.assertEqual(len(ret), 1)

		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.Lock))
		self.assertEqual(msg.ID, 'MPID')
		self.assertEqual(msg.transactionID, 'bar')
		self.assertEqual(msg.isPayerSide, False)


	def test_requestCommitOutgoing(self):
		'Test requestCommitOutgoing'

		ret = self.meetingPoint.requestCommitOutgoing(messages.RequestCommit(
			ID='foo',
			token='bar',
			isPayerSide=False
			))

		self.assertEqual(len(ret), 1)

		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.RequestCommit))
		self.assertEqual(msg.ID, 'MPID')
		self.assertEqual(msg.token, 'bar')
		self.assertEqual(msg.isPayerSide, True)


	def test_settleCommitOutgoing(self):
		'Test settleCommitOutgoing'

		ret = self.meetingPoint.settleCommitOutgoing(messages.SettleCommit(
			ID='foo',
			token='bar',
			isPayerSide=True
			))

		self.assertEqual(len(ret), 1)

		msg = ret[0]
		self.assertTrue(isinstance(msg, messages.SettleCommit))
		self.assertEqual(msg.ID, 'MPID')
		self.assertEqual(msg.token, 'bar')
		self.assertEqual(msg.isPayerSide, False)



if __name__ == '__main__':
	unittest.main(verbosity=2)

