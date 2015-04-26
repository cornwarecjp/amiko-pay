#!/usr/bin/env python
#    test_messages.py
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
import sys
sys.path.append('../..')
sys.path.append('..')

import testenvironment

from amiko.core import messages



class Test(unittest.TestCase):
	def test_messageIDs(self):
		"Test numerical values of message IDs"

		self.assertEqual(messages.ID_STRING      , 1)
		self.assertEqual(messages.ID_LINK        , 2)
		self.assertEqual(messages.ID_PAY         , 3)
		self.assertEqual(messages.ID_RECEIPT     , 4)
		self.assertEqual(messages.ID_CONFIRM     , 5)
		self.assertEqual(messages.ID_MAKEROUTE   , 6)
		self.assertEqual(messages.ID_HAVEROUTE   , 7)
		self.assertEqual(messages.ID_LOCK        , 8)
		self.assertEqual(messages.ID_CANCEL      , 9)
		self.assertEqual(messages.ID_COMMIT      , 10)
		self.assertEqual(messages.ID_MYURLS      , 11)
		self.assertEqual(messages.ID_DEPOSIT     , 12)
		self.assertEqual(messages.ID_WITHDRAW    , 13)


	def test_Message(self):
		"Test Message base class"

		msg = messages.Message(0x42)
		self.assertEqual(msg.serializeAttributes(), "")
		self.assertEqual(msg.serialize(), "\x00\x00\x00\x42")
		msg.deserializeAttributes("")
		self.assertTrue(str(0x42) in str(msg))


	def test_String(self):
		"Test String message class"

		msg = messages.String("Foo", 0x42)
		self.assertEqual(msg.value, "Foo")
		self.assertEqual(msg.serializeAttributes(), "Foo")
		self.assertEqual(msg.serialize(), "\x00\x00\x00\x42Foo")
		msg.deserializeAttributes("Bar")
		self.assertEqual(msg.value, "Bar")
		self.assertTrue("Bar" in str(msg))


	def test_Pay(self):
		"Test Pay message class"

		msg = messages.Pay("Foo")
		self.assertEqual(msg.serialize(), "\x00\x00\x00%cFoo" % \
			messages.ID_PAY)
		msg.deserializeAttributes("Bar")
		self.assertEqual(msg.value, "Bar")


	def test_Confirm(self):
		"Test Confirm message class"

		msg = messages.Confirm("Foo")
		self.assertEqual(msg.serialize(), "\x00\x00\x00%cFoo" % \
			messages.ID_CONFIRM)
		msg.deserializeAttributes("Bar")
		self.assertEqual(msg.value, "Bar")


	def test_HaveRoute(self):
		"Test HaveRoute message class"

		msg = messages.HaveRoute("Foo")
		self.assertEqual(msg.serialize(), "\x00\x00\x00%cFoo" % \
			messages.ID_HAVEROUTE)
		msg.deserializeAttributes("Bar")
		self.assertEqual(msg.value, "Bar")


	def test_Cancel(self):
		"Test Cancel message class"

		msg = messages.Cancel()
		self.assertEqual(msg.serialize(), "\x00\x00\x00%c" % \
			messages.ID_CANCEL)


	def test_MyURLs(self):
		"Test MyURLs message class"

		msg = messages.MyURLs(["Foo", "Bar", "Foobar"])
		self.assertEqual(msg.getURLs(), ["Foo", "Bar", "Foobar"])
		self.assertEqual(msg.serialize(),
			"\x00\x00\x00%cFoo\nBar\nFoobar" % \
			messages.ID_MYURLS)
		msg.deserializeAttributes("Bar\nFoo")
		self.assertEqual(msg.getURLs(), ["Bar", "Foo"])


	def test_Link(self):
		"Test Link message class"

		msg = messages.Link("Foo", 0x42)
		self.assertEqual(msg.ID, "Foo")
		self.assertEqual(msg.dice, 0x42)
		self.assertEqual(msg.serialize(),
			"\x00\x00\x00%c\x00\x00\x00\x42Foo" % \
			messages.ID_LINK)
		msg.deserializeAttributes("\x12\x34\x56\x78Bar")
		self.assertEqual(msg.ID, "Bar")
		self.assertEqual(msg.dice, 0x12345678)
		self.assertTrue("Bar" in str(msg))
		self.assertTrue(str(0x12345678) in str(msg))


	def test_MakeRoute(self):
		"Test MakeRoute message class"

		msg = messages.MakeRoute(
			amount=0x0775f05a074000, isPayerSide=True, hash="Foo", meetingPoint="Bar")
		self.assertEqual(msg.amount, 0x0775f05a074000)
		self.assertEqual(msg.isPayerSide, True)
		self.assertEqual(msg.hash, "Foo")
		self.assertEqual(msg.meetingPoint, "Bar")
		self.assertEqual(msg.serialize(),
			("\x00\x00\x00%c" % messages.ID_MAKEROUTE) + \
			"\x00\x07\x75\xf0\x5a\x07\x40\x00"
			"\x00\x00\x00\x03Foo"
			"\x01"
			"Bar"
			)
		msg.deserializeAttributes(
			"\x00\x00\x00\x00\x12\x34\x56\x78"
			"\x00\x00\x00\x06Foobar"
			"\x00"
			"FOO"
			)
		self.assertEqual(msg.amount, 0x12345678)
		self.assertEqual(msg.isPayerSide, False)
		self.assertEqual(msg.hash, "Foobar")
		self.assertEqual(msg.meetingPoint, "FOO")
		self.assertTrue(str(0x12345678) in str(msg))
		self.assertTrue(str(False) in str(msg))
		self.assertTrue("Foobar" in str(msg))
		self.assertTrue("FOO" in str(msg))


	def test_Receipt(self):
		"Test Receipt message class"

		msg = messages.Receipt(
			amount=0x0775f05a074000, receipt="Foo", hash="Foobar",
			meetingPoints=["ABC", "D", "EFGHI"])
		self.assertEqual(msg.amount, 0x0775f05a074000)
		self.assertEqual(msg.receipt, "Foo")
		self.assertEqual(msg.hash, "Foobar")
		self.assertEqual(msg.meetingPoints, ["ABC", "D", "EFGHI"])
		self.assertEqual(msg.serialize(),
			("\x00\x00\x00%c" % messages.ID_RECEIPT) + \
			"\x00\x07\x75\xf0\x5a\x07\x40\x00"
			"\x00\x00\x00\x03Foo"
			"\x00\x00\x00\x06Foobar"
			"\x00\x00\x00\x03"
				"\x00\x00\x00\x03ABC"
				"\x00\x00\x00\x01D"
				"\x00\x00\x00\x05EFGHI"
			)
		msg.deserializeAttributes(
			"\x00\x00\x00\x00\x12\x34\x56\x78"
			"\x00\x00\x00\x03FOO"
			"\x00\x00\x00\x03Bar"
			"\x00\x00\x00\x00"
			)
		self.assertEqual(msg.amount, 0x12345678)
		self.assertEqual(msg.receipt, "FOO")
		self.assertEqual(msg.hash, "Bar")
		self.assertEqual(msg.meetingPoints, [])
		msg.deserializeAttributes(
			"\x00\x00\x00\x00\x12\x34\x56\x78"
			"\x00\x00\x00\x03FOO"
			"\x00\x00\x00\x03Bar"
			"\x00\x00\x00\x02"
				"\x00\x00\x00\x01A"
				"\x00\x00\x00\x03BCD"
			)
		self.assertEqual(msg.meetingPoints, ["A", "BCD"])
		self.assertTrue(str(0x12345678) in str(msg))
		self.assertTrue("FOO" in str(msg))
		self.assertTrue("Bar" in str(msg))
		self.assertTrue("A" in str(msg))
		self.assertTrue("BCD" in str(msg))


	def test_ChannelMessage(self):
		"Test ChannelMessage base class"

		msg = messages.ChannelMessage(
			typeID=0x42, channelID=0x02, stage=0x03, payload="Foo")
		self.assertEqual(msg.channelID, 0x02)
		self.assertEqual(msg.stage, 0x03)
		self.assertEqual(msg.payload, "Foo")
		self.assertEqual(msg.serialize(),
			"\x00\x00\x00\x42\x00\x00\x00\x02\x03Foo"
			)
		msg.deserializeAttributes(
			"\x00\x00\x00\x12\x34Bar"
			)
		self.assertEqual(msg.channelID, 0x12)
		self.assertEqual(msg.stage, 0x34)
		self.assertEqual(msg.payload, "Bar")
		self.assertTrue(str(0x12) in str(msg))
		self.assertTrue(str(0x34) in str(msg))


	def test_Deposit(self):
		"Test Deposit message class"

		msg = messages.Deposit(
			channelID=0x02, type="Foo", isInitial=False, stage=0x03,
			payload="Bar")
		self.assertEqual(msg.channelID, 0x02)
		self.assertEqual(msg.type, "Foo")
		self.assertEqual(msg.isInitial, False)
		self.assertEqual(msg.stage, 0x03)
		self.assertEqual(msg.payload, "Bar")
		self.assertEqual(msg.serialize(),
			("\x00\x00\x00%c" % messages.ID_DEPOSIT) + \
			"\x00\x00\x00\x03Foo"
			"\x00"
			"\x00\x00\x00\x02"
			"\x03"
			"Bar"
			)
		msg.deserializeAttributes(
			"\x00\x00\x00\x06Foobar"
			"\x01"
			"\x00\x00\x00\x12"
			"\x34"
			"FOO"
			)
		self.assertEqual(msg.channelID, 0x12)
		self.assertEqual(msg.type, "Foobar")
		self.assertEqual(msg.isInitial, True)
		self.assertEqual(msg.stage, 0x34)
		self.assertEqual(msg.payload, "FOO")
		self.assertTrue(str(0x12) in str(msg))
		self.assertTrue("Foobar" in str(msg))
		self.assertTrue(str(True) in str(msg))
		self.assertTrue(str(0x34) in str(msg))


	def test_Withdraw(self):
		"Test Withdraw message class"

		msg = messages.Withdraw(
			channelID=0x02, stage=0x03, payload="Foo")
		self.assertEqual(msg.channelID, 0x02)
		self.assertEqual(msg.stage, 0x03)
		self.assertEqual(msg.payload, "Foo")
		self.assertEqual(msg.serialize(),
			"\x00\x00\x00%c\x00\x00\x00\x02\x03Foo" % messages.ID_WITHDRAW
			)


	def test_Lock(self):
		"Test Lock message class"

		msg = messages.Lock(
			channelID=0x02, hash="Foo", payload="Bar")
		self.assertEqual(msg.channelID, 0x02)
		self.assertEqual(msg.stage, 0)
		self.assertEqual(msg.hash, "Foo")
		self.assertEqual(msg.payload, "Bar")
		self.assertEqual(msg.serialize(),
			("\x00\x00\x00%c" % messages.ID_LOCK) + \
			"\x00\x00\x00\x03Foo"
			"\x00\x00\x00\x02\x00Bar"
			)
		msg.deserializeAttributes(
			"\x00\x00\x00\x06Foobar"
			"\x00\x00\x00\x03\x00FOO"
			)
		self.assertEqual(msg.channelID, 0x03)
		self.assertEqual(msg.stage, 0)
		self.assertEqual(msg.hash, "Foobar")
		self.assertEqual(msg.payload, "FOO")
		self.assertTrue(str(0x03) in str(msg))
		self.assertTrue("Foobar".encode("hex") in str(msg))


	def test_Commit(self):
		"Test Commit message class"

		msg = messages.Commit(
			channelID=0x02, token="Foo", payload="Bar")
		self.assertEqual(msg.channelID, 0x02)
		self.assertEqual(msg.stage, 0)
		self.assertEqual(msg.token, "Foo")
		self.assertEqual(msg.payload, "Bar")
		self.assertEqual(msg.serialize(),
			("\x00\x00\x00%c" % messages.ID_COMMIT) + \
			"\x00\x00\x00\x03Foo"
			"\x00\x00\x00\x02\x00Bar"
			)
		msg.deserializeAttributes(
			"\x00\x00\x00\x06Foobar"
			"\x00\x00\x00\x03\x00FOO"
			)
		self.assertEqual(msg.channelID, 0x03)
		self.assertEqual(msg.stage, 0)
		self.assertEqual(msg.token, "Foobar")
		self.assertEqual(msg.payload, "FOO")
		self.assertTrue(str(0x03) in str(msg))
		self.assertTrue("Foobar".encode("hex") in str(msg))


	def test_Deserialize(self):
		"Test deserialize function"

		for clss in [
			messages.String,
			messages.Link,
			messages.Pay,
			messages.Receipt,
			messages.Confirm,
			messages.MakeRoute,
			messages.HaveRoute,
			messages.Lock,
			messages.Cancel,
			messages.Commit,
			messages.MyURLs,
			messages.Deposit,
			messages.Withdraw
			]:
				a = clss()
				s1 = a.serialize()
				b = messages.deserialize(s1)
				s2 = b.serialize()
				self.assertEqual(s1, s2)

		self.assertRaises(Exception, messages.deserialize, "**** Invalid ID")



if __name__ == "__main__":
	unittest.main(verbosity=2)

