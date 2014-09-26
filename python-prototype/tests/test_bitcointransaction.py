#!/usr/bin/env python
#    test_bitcointransaction.py
#    Copyright (C) 2014 by CJP
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

import sys
import binascii

sys.path.append("..")

import settings
import bitcoind
from bitcointransaction import Transaction, TxIn, TxOut, Script

s = settings.Settings("../amikopay.conf")
d = bitcoind.Bitcoind(s)

print d.getBalance()

tx = Transaction(
	tx_in = [
		TxIn('X'*32, 0)
		],
	tx_out = [
		TxOut(5000000, Script.standardPubKey(
			binascii.unhexlify("1AA0CD1CBEA6E7458A7ABAD512A9D9EA1AFB225E")
			)),
		TxOut(3354000000, Script.standardPubKey(
			binascii.unhexlify("0EAB5BEA436A0484CFAB12485EFDA0B78B4ECC52")
			))
		]
	)

print tx.serialize().encode("hex")

