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



if __name__ == "__main__":
	unittest.main(verbosity=2)
