#!/usr/bin/env python
#    test_paylog.py
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

import unittest
import os

import testenvironment

from amiko.core import settings

from amiko.core import paylog

logFile = "test_paylog.log"


class DummyPayStates:
	committed = "committed"



class DummyPay:
	states = DummyPayStates()

	def __init__(self, amount, receipt, state, transactionID, token):
		self.amount = amount
		self.receipt = receipt
		self.state = state
		self.transactionID = transactionID
		self.token = token



class Test(unittest.TestCase):
	def test_newLogFile(self):
		'Test creation of a new log file'

		if os.access(logFile, os.R_OK):
			os.remove(logFile)
		self.assertFalse(os.access(logFile, os.R_OK))

		s = settings.Settings()
		s.payLogFile = logFile
		payLog = paylog.PayLog(s)

		payLog.writePayer(DummyPay(123, "abc", "committed", "\x01\xde", "\xab\xcd"))
		payLog.writePayee(DummyPay(456, "def", "committed", "\x99\xaf", "\xef\x01"))

		payLog.close()

		self.checkLogContents(
			"-123, 'abc', committed, 01de, abcd\n"
			"456, 'def', committed, 99af, ef01\n"
			)


	def test_write(self):
		'Test appending to an existing log file'

		with open(logFile, "wb") as f:
			f.write("Existing data\n")

		self.checkLogContents(
			"Existing data\n"
			)

		s = settings.Settings()
		s.payLogFile = logFile
		payLog = paylog.PayLog(s)

		payLog.writePayer(DummyPay(123, "abc", "committed", "\x01\xde", "\xab\xcd"))
		self.checkLogContents(
			"Existing data\n"
			"-123, 'abc', committed, 01de, abcd\n"
			)

		payLog.writePayee(DummyPay(456, "def", "committed", "\x99\xaf", "\xef\x01"))
		self.checkLogContents(
			"Existing data\n"
			"-123, 'abc', committed, 01de, abcd\n"
			"456, 'def', committed, 99af, ef01\n"
			)

		payLog.writePayer(DummyPay(123, "abc", "otherState", "\x01\xde", "\xab\xcd"))
		self.checkLogContents(
			"Existing data\n"
			"-123, 'abc', committed, 01de, abcd\n"
			"456, 'def', committed, 99af, ef01\n"
			"-123, 'abc', otherState, 01de, \n"
			)

		payLog.writePayee(DummyPay(456, "def", "cancelled", "\x99\xaf", "\xef\x01"))
		self.checkLogContents(
			"Existing data\n"
			"-123, 'abc', committed, 01de, abcd\n"
			"456, 'def', committed, 99af, ef01\n"
			"-123, 'abc', otherState, 01de, \n"
			"456, 'def', cancelled, 99af, \n"
			)

		payLog.close()


	def checkLogContents(self, expected):
		with open(logFile, "rb") as f:
			data = f.read()
		self.assertEqual(data, expected)


	def test_recentPayerState(self):
		'Test collection of recent payer state information'

		s = settings.Settings()
		s.payLogFile = logFile
		payLog = paylog.PayLog(s)
		self.assertRaises(KeyError, payLog.getRecentPayerState, '\x01\xde')

		payLog.writePayer(DummyPay(123, 'abc', 'committed', '\x01\xde', '\xab\xcd'))
		self.assertEqual(payLog.getRecentPayerState('\x01\xde'), 'committed')

		payLog.removeRecentPayerState('\x01\xde')
		self.assertRaises(KeyError, payLog.getRecentPayerState, '\x01\xde')



if __name__ == "__main__":
	unittest.main(verbosity=2)

