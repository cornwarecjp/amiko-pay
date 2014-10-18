#!/usr/bin/env python
#    test_multisignature.py
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
import base58
from crypto import Key, RIPEMD160, SHA256
import bitcointransaction
from bitcoinutils import sendToMultiSigPubKey
from bitcoinutils import makeSpendMultiSigTransaction, signMultiSigTransaction, applyMultiSigSignatures



s = settings.Settings("../amikopay.conf")
d = bitcoind.Bitcoind(s)

#(these addresses are mine - thanks for donating :-P)
keyHash1 = binascii.unhexlify("fd5627c5eff58991dec54877272e82f758ea8b65")
keyHash2 = binascii.unhexlify("ab22c699d3e72f2c1e4896508bf9d8d7910104d0")

address1 = base58.encodeBase58Check(keyHash1, 0)
address2 = base58.encodeBase58Check(keyHash2, 0)
print address1
print address2

#Note: this will fail, unless you change the above addresses to some of your own
privKey1 = base58.decodeBase58Check(d.getPrivateKey(address1), 128)
privKey2 = base58.decodeBase58Check(d.getPrivateKey(address2), 128)

key1 = Key()
key1.setPrivateKey(privKey1)
key2 = Key()
key2.setPrivateKey(privKey2)

print key1.getPublicKey().encode("hex")
print key2.getPublicKey().encode("hex")

print base58.encodeBase58Check(RIPEMD160(SHA256(key1.getPublicKey())), 0)
print base58.encodeBase58Check(RIPEMD160(SHA256(key2.getPublicKey())), 0)

amount = int(100000 * float(raw_input("Amount to be transferred (mBTC): ")))
fee = 10000 #0.1 mBTC

outputHash = binascii.unhexlify(raw_input("Input hash (empty: create multisig): "))[::-1]

if outputHash == "":
	tx = sendToMultiSigPubKey(d, amount,
		key1.getPublicKey(),
		key2.getPublicKey(),
		keyHash2,
		fee=fee)
else:
	outputIndex = 0

	tx = makeSpendMultiSigTransaction(outputHash, outputIndex, amount, keyHash1, fee)

	sig1 = signMultiSigTransaction(tx, outputIndex, key1.getPublicKey(), key2.getPublicKey(), key1)
	sig2 = signMultiSigTransaction(tx, outputIndex, key1.getPublicKey(), key2.getPublicKey(), key2)

	applyMultiSigSignatures(tx, sig1, sig2)


print "Tx:", tx.serialize().encode("hex")

print "Tx ID:", tx.getTransactionID()[::-1].encode("hex")

tx_s = tx.serialize()
#d.sendRawTransaction(tx_s)

tx = bitcointransaction.Transaction.deserialize(tx_s)
tx_s2 = tx.serialize()
print "Serialization remains constant: ", tx_s == tx_s2

