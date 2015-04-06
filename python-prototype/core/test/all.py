#!/usr/bin/env python
#    all.py
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

from test_base58 import Test as test_base58
from test_bitcointransaction import Test as test_bitcointransaction
from test_bitcoinutils import Test as test_bitcoinutils
from test_channel import Test as test_channel
from test_crypto import Test as test_crypto
from test_log import Test as test_log
from test_meetingpoint import Test as test_meetingpoint
from test_messages import Test as test_messages
from test_transaction import Test as test_transaction
from test_utils import Test as test_utils


if __name__ == "__main__":
	unittest.main(verbosity=2)

