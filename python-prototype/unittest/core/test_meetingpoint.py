#!/usr/bin/env python
#    test_meetingpoint.py
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

from dummy_interfaces import DummyTransaction

from amiko.core import meetingpoint



class Test(unittest.TestCase):
	def setUp(self):
		self.mp = meetingpoint.MeetingPoint("foobar")


	def test_initialState(self):
		"Test the initial state of a meeting point"

		self.assertEqual(self.mp.ID, "foobar")
		self.assertEqual(self.mp.getState(),
			{
			"ID": "foobar",
			"openTransactions": []
			}
			)


	def test_makeRoute_payerFirst(self):
		"Test msg_makeRoute (payer message arrives first)"

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		self.mp.msg_makeRoute(t1)
		self.assertEqual(self.mp.transactionPairs, {"hash": [t1, None]})
		self.assertEqual(t1.trace, [])

		t1.trace = []
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.msg_makeRoute(t2)
		self.assertEqual(self.mp.transactionPairs, {"hash": [t1, t2]})
		self.assertEqual(t1.trace, [
			('msg_haveRoute', (self.mp, 12, 34), {})
			])
		self.assertEqual(t2.trace, [
			('msg_haveRoute', (self.mp, 12, 34), {})
			])


	def test_makeRoute_payeeFirst(self):
		"Test msg_makeRoute (payee message arrives first)"

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.msg_makeRoute(t1)
		self.assertEqual(self.mp.transactionPairs, {"hash": [None, t1]})
		self.assertEqual(t1.trace, [])

		t1.trace = []
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		self.mp.msg_makeRoute(t2)
		self.assertEqual(self.mp.transactionPairs, {"hash": [t2, t1]})
		self.assertEqual(t1.trace, [
			('msg_haveRoute', (self.mp, 12, 34), {})
			])
		self.assertEqual(t2.trace, [
			('msg_haveRoute', (self.mp, 12, 34), {})
			])


	def test_makeRoute_payerTwice(self):
		"Test msg_makeRoute (payer message arrives twice)"

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		self.mp.msg_makeRoute(t1)
		self.assertEqual(self.mp.transactionPairs, {"hash": [t1, None]})
		self.assertEqual(t1.trace, [])

		t1.trace = []
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		self.mp.msg_makeRoute(t2)
		self.assertEqual(self.mp.transactionPairs, {})
		self.assertEqual(t1.trace, [
			('msg_cancelRoute', (), {})
			])
		self.assertEqual(t2.trace, [
			('msg_cancelRoute', (), {})
			])


	def test_makeRoute_payeeTwice(self):
		"Test msg_makeRoute (payee message arrives twice)"

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.msg_makeRoute(t1)
		self.assertEqual(self.mp.transactionPairs, {"hash": [None, t1]})
		self.assertEqual(t1.trace, [])

		t1.trace = []
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.msg_makeRoute(t2)
		self.assertEqual(self.mp.transactionPairs, {})
		self.assertEqual(t1.trace, [
			('msg_cancelRoute', (), {})
			])
		self.assertEqual(t2.trace, [
			('msg_cancelRoute', (), {})
			])


	def test_makeRoute_amountMismatch(self):
		"Test msg_makeRoute (payer message arrives first)"

		t1 = DummyTransaction(
			amount=100, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		self.mp.msg_makeRoute(t1)
		self.assertEqual(self.mp.transactionPairs, {"hash": [t1, None]})
		self.assertEqual(t1.trace, [])

		t1.trace = []
		t2 = DummyTransaction(
			amount=101, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.msg_makeRoute(t2)
		self.assertEqual(self.mp.transactionPairs, {})
		self.assertEqual(t1.trace, [
			('msg_cancelRoute', (), {})
			])
		self.assertEqual(t2.trace, [
			('msg_cancelRoute', (), {})
			])


	def test_endRoute(self):
		"Test msg_endRoute"

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.transactionPairs = {"hash": [t1, t2]}
		self.mp.msg_endRoute(t1)
		self.assertEqual(self.mp.transactionPairs, {})
		self.assertEqual(t1.trace, [])
		self.assertEqual(t2.trace, [
			('msg_cancelRoute', (), {})
			])

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.transactionPairs = {"hash": [t1, t2]}
		self.mp.msg_endRoute(t2)
		self.assertEqual(self.mp.transactionPairs, {})
		self.assertEqual(t2.trace, [])
		self.assertEqual(t1.trace, [
			('msg_cancelRoute', (), {})
			])

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		self.mp.transactionPairs = {"hash": [t1, None]}
		self.mp.msg_endRoute(t1)
		self.assertEqual(self.mp.transactionPairs, {})
		self.assertEqual(t1.trace, [])


	def test_lock(self):
		"Test msg_lock"

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.transactionPairs = {"hash": [t1, t2]}
		self.mp.msg_lock(t1)
		self.assertEqual(self.mp.transactionPairs, {"hash": [t1, t2]})
		self.assertEqual(t1.trace, [])
		self.assertEqual(t2.trace, [
			('msg_lock', (), {})
			])


	def test_commit(self):
		"Test msg_commit"

		t1 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=True)
		t1.token = "token"
		t2 = DummyTransaction(
			amount=0, hash="hash", meetingPoint="meetingpoint", isPayerSide=False)
		self.mp.transactionPairs = {"hash": [t1, t2]}
		self.mp.msg_commit(t1)
		self.assertEqual(self.mp.transactionPairs, {})
		self.assertEqual(t1.trace, [])
		self.assertEqual(t2.trace, [
			('msg_commit', ("token",), {})
			])


if __name__ == "__main__":
	unittest.main(verbosity=2)

