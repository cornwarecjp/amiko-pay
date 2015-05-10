#!/usr/bin/env python
#    escrow.py
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

import sys
import binascii

from amiko.core import bitcoind, settings
from amiko.utils import base58, bitcoinutils, bitcointransaction, crypto
from amiko.channels import tcd


if len(sys.argv) != 2:
	print "Usage: %s private_key_file" % sys.argv[0]
	sys.exit()


print "Loading the private key...",
with open(sys.argv[1], "rb") as f:
	privateKey = f.read()

#Assume base58 encoded private key on the first line of the file.
#Anything else will be very likely to result in an exception.
privateKey = privateKey.split('\n')[0]
privateKey = base58.decodeBase58Check(privateKey, 128) #PRIVKEY = 128

key = crypto.Key()
key.setPrivateKey(privateKey)

print "done"

print "Our public key is: ", key.getPublicKey().encode("hex")

print "Reading the settings file...",
settings = settings.Settings("amikopay.conf")
bitcoind = bitcoind.Bitcoind(settings)
print "done"

print
WID = raw_input("Enter the withdraw transaction ID: ")
W = bitcoind.getTransaction(WID)

if W["confirmations"] < 6:
	print "Error: number of confirmations is %d < 6" % W["confirmations"]
	sys.exit()

W = binascii.unhexlify(W["hex"])
W = bitcointransaction.Transaction.deserialize(W)

#print "Reconstructed ID:", W.getTransactionID()[::-1].encode("hex")

#Ask for serialized list of TCDs (maybe get this from a file)
TCDlist_serialized = raw_input("Enter the serialized TCD list: ")
TCDlist = tcd.deserializeList(TCDlist_serialized)

#Check presence of list hash in W
listHash = crypto.RIPEMD160(crypto.SHA256(TCDlist_serialized))
#TODO

#TODO:
#Ask for index to be resolved
#Check whether W's output has our public key on it

#De-serialize TCD
#Get start(!) and end timestamps and token hash
#Check that end > start and last existing block time >> end
#Search in block range for token -> determine commit condition

#Make transaction
#Sign transaction
#Print transaction

print "Sorry, but the rest of the escrow script is not yet implemented."

