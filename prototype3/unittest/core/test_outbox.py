#!/usr/bin/env python
#    test_outbox.py
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

import unittest

import testenvironment

from amiko.core import serializable
from amiko.core import messages

from amiko.core import outbox


class OutBoxTestMessage(serializable.Serializable):
	serializableAttributes = {'payload': None}
serializable.registerClass(OutBoxTestMessage)



class Test(unittest.TestCase):
	def setUp(self):
		self.outBox = outbox.OutBox()


	def test_constructor(self):
		"Test constructor"

		self.assertEqual(self.outBox.lists, {})


	def test_addMessage(self):
		"Test addMessage"

		msg1 = messages.OutboundMessage(
			localID='foo',
			message=OutBoxTestMessage(payload='bar')
			)
		self.outBox.addMessage(msg1)

		self.assertEqual(self.outBox.lists.keys(), ['foo'])
		outBoxList = self.outBox.lists['foo']
		self.assertEqual(len(outBoxList.messages), 1)
		msg = outBoxList.messages[0]
		self.assertEqual(msg.message.getState(), msg1.getState())
		self.assertEqual(msg.index, 0)
		self.assertEqual(outBoxList.lastIndex, 0)
		self.assertEqual(outBoxList.notYetTransmitted, 1)
		self.assertEqual(outBoxList.closing, False)

		msg2 = messages.OutboundMessage(
			localID='foo',
			message=OutBoxTestMessage(payload='foobar')
			)
		self.outBox.addMessage(msg2)

		self.assertEqual(self.outBox.lists.keys(), ['foo'])
		outBoxList = self.outBox.lists['foo']
		self.assertEqual(len(outBoxList.messages), 2)
		msg = outBoxList.messages[0]
		self.assertEqual(msg.message.getState(), msg1.getState())
		self.assertEqual(msg.index, 0)
		msg = outBoxList.messages[1]
		self.assertEqual(msg.message.getState(), msg2.getState())
		self.assertEqual(msg.index, 1)
		self.assertEqual(outBoxList.lastIndex, 1)
		self.assertEqual(outBoxList.notYetTransmitted, 2)
		self.assertEqual(outBoxList.closing, False)

		msg3 = messages.OutboundMessage(
			localID='baz',
			message=OutBoxTestMessage(payload='foobar')
			)
		self.outBox.addMessage(msg3)

		self.assertEqual(set(self.outBox.lists.keys()), set(['foo', 'baz']))
		self.assertEqual(len(self.outBox.lists['foo'].messages), 2)
		self.assertEqual(len(self.outBox.lists['baz'].messages), 1)


	def test_addMessage_limit(self):
		"Test addMessage (limit)"

		msg = messages.OutboundMessage(
			localID='foo',
			message=OutBoxTestMessage(payload='bar')
			)

		for i in range(32768):
			self.outBox.addMessage(msg)

		#After exactly 32768 times, it gives an exception:
		self.assertRaises(Exception, self.outBox.addMessage, msg)

		self.assertEqual(len(self.outBox.lists['foo'].messages), 32768)



if __name__ == "__main__":
	unittest.main(verbosity=2)

