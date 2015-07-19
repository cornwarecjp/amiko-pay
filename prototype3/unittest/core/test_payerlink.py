#!/usr/bin/env python
#    test_payerlink.py
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
import copy
import threading
import time

import testenvironment

from amiko.core import messages

from amiko.core import payerlink



class Test(unittest.TestCase):
	def setUp(self):
		self.payerLink = payerlink.PayerLink()


	def test_defaultAttributes(self):
		"Test default attributes"

		self.assertEqual(self.payerLink.payeeHost, None)
		self.assertEqual(self.payerLink.payeePort, None)
		self.assertEqual(self.payerLink.payeeLinkID, None)
		self.assertEqual(self.payerLink.amount, None)
		self.assertEqual(self.payerLink.receipt, None)
		self.assertEqual(self.payerLink.transactionID, None)
		self.assertEqual(self.payerLink.token, None)
		self.assertEqual(self.payerLink.meetingPointID, None)
		self.assertEqual(self.payerLink.state, payerlink.PayerLink.states.initial)


	def test_deepcopy(self):
		"Test deep copy operator"

		self.payerLink = payerlink.PayerLink(
			payeeHost      = "payeeHost",
			payeePort      = "payeePort",
			payeeLinkID    = "payeeLinkID",
			amount         = "amount",
			receipt        = "receipt",
			transactionID  = "transactionID",
			token          = "token",
			meetingPointID = "meetingPointID",
			state          = "state"
			)
		payer2 = copy.deepcopy(self.payerLink)
		self.assertEqual(payer2.payeeHost      , "payeeHost")
		self.assertEqual(payer2.payeePort      , "payeePort")
		self.assertEqual(payer2.payeeLinkID    , "payeeLinkID")
		self.assertEqual(payer2.amount         , "amount")
		self.assertEqual(payer2.receipt        , "receipt")
		self.assertEqual(payer2.transactionID  , "transactionID")
		self.assertEqual(payer2.token          , "token")
		self.assertEqual(payer2.meetingPointID , "meetingPointID")
		self.assertEqual(payer2.state          , "state")


	def test_getTimeoutMessage(self):
		"Test getTimeoutMessage"

		msg = self.payerLink.getTimeoutMessage()
		self.assertTrue(isinstance(msg, messages.Timeout))
		self.assertEqual(msg.state, payerlink.PayerLink.states.initial)

		self.payerLink.state = payerlink.PayerLink.states.receivedCommit

		msg = self.payerLink.getTimeoutMessage()
		self.assertTrue(isinstance(msg, messages.Timeout))
		self.assertEqual(msg.state, payerlink.PayerLink.states.receivedCommit)


	def test_msg_timeout_initial(self):
		"Test msg_timeout (state: initial)"

		measuredTime = [0.0]
		def measureTime():
			t0 = time.time()
			self.payerLink.waitForReceipt()
			t1 = time.time()
			measuredTime[0] = t1 - t0
		measureTime = threading.Thread(target=measureTime)
		measureTime.start()

		time.sleep(0.5)
		ret = self.payerLink.handleMessage(
			messages.Timeout(state=payerlink.PayerLink.states.initial))

		self.assertEqual(self.payerLink.state, payerlink.PayerLink.states.cancelled)

		self.assertEqual(len(ret), 0)

		measureTime.join()
		self.assertGreaterEqual(measuredTime[0], 0.5)
		self.assertLess(measuredTime[0], 0.6)


	def test_msg_timeout_receivedCommit(self):
		"Test msg_timeout (state: receivedCommit)"

		self.payerLink.state = payerlink.PayerLink.states.receivedCommit

		measuredTime = [0.0]
		def measureTime():
			t0 = time.time()
			self.payerLink.waitForFinished()
			t1 = time.time()
			measuredTime[0] = t1 - t0
		measureTime = threading.Thread(target=measureTime)
		measureTime.start()

		time.sleep(0.5)
		ret = self.payerLink.handleMessage(
			messages.Timeout(state=payerlink.PayerLink.states.receivedCommit))

		self.assertEqual(self.payerLink.state, payerlink.PayerLink.states.committed)

		self.assertEqual(len(ret), 0)

		measureTime.join()
		self.assertGreaterEqual(measuredTime[0], 0.5)
		self.assertLess(measuredTime[0], 0.6)


	def test_msg_timeout_other(self):
		"Test msg_timeout (state: other)"

		ret = self.payerLink.handleMessage(
			messages.Timeout(state=payerlink.PayerLink.states.receivedCommit))

		self.assertEqual(self.payerLink.state, payerlink.PayerLink.states.initial)

		self.assertEqual(len(ret), 0)


	def test_msg_receipt(self):
		"Test msg_receipt"

		measuredTime = [0.0]
		def measureTime():
			t0 = time.time()
			self.payerLink.waitForReceipt()
			t1 = time.time()
			measuredTime[0] = t1 - t0
		measureTime = threading.Thread(target=measureTime)
		measureTime.start()

		time.sleep(0.5)
		ret = self.payerLink.handleMessage(
			messages.Receipt(
				amount=123,
				receipt="receipt",
				transactionID="txID",
				meetingPoints=["MPID"]
				))

		self.assertEqual(self.payerLink.state, payerlink.PayerLink.states.hasReceipt)
		self.assertEqual(self.payerLink.amount, 123)
		self.assertEqual(self.payerLink.receipt, "receipt")
		self.assertEqual(self.payerLink.transactionID, "txID")
		#self.assertEqual(self.payerLink.meetingPointID, "MPID") #TODO

		self.assertEqual(len(ret), 0)

		measureTime.join()
		self.assertGreaterEqual(measuredTime[0], 0.5)
		self.assertLess(measuredTime[0], 0.6)



if __name__ == "__main__":
	unittest.main(verbosity=2)

