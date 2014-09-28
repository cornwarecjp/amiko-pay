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
import bitcoinutils
from bitcointransaction import Transaction, TxIn, TxOut, Script

from crypto import Key



s = settings.Settings("../amikopay.conf")
d = bitcoind.Bitcoind(s)

amount = int(100000 * float(raw_input("Amount to be transferred (mBTC): ")))
fee = 10000 #0.1 mBTC

print d.getBalance()

totalIn, inputs = bitcoinutils.getInputsForAmount(d, amount+fee)
change = totalIn - fee - amount

print "%d -> %d, %d, %d" % (totalIn, amount, change, fee)

tx = Transaction(
	tx_in = [
		TxIn(x[0], x[1])
		for x in inputs
		],
	tx_out = [
		TxOut(amount, Script.standardPubKey(
			#The TO-address (it's mine - thanks for donating :-P)
			binascii.unhexlify("fd5627c5eff58991dec54877272e82f758ea8b65")
			)),
		TxOut(change, Script.standardPubKey(
			#The CHANGE-address (it's mine - thanks for donating :-P)
			binascii.unhexlify("ab22c699d3e72f2c1e4896508bf9d8d7910104d0")
			))
		]
	)

for i in range(len(inputs)):
	scriptPubKey = Script.deserialize(inputs[i][2])
	key = Key()
	key.makeNewKey() #TODO: get private key from bitcoind
	tx.signInput(i, scriptPubKey, [None, key.getPublicKey()], [key])


print tx.serialize().encode("hex")

