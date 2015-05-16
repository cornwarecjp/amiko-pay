#!/usr/bin/env python
#    botg.py
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
sys.path.append(".")
sys.path.append("..")

from amiko.utils.crypto import Key, SHA256, RIPEMD160
from amiko.utils import base58



def makekey(args):
	k = Key()
	k.makeNewKey(compressed=True)

	privateKey = k.getPrivateKey()
	privateKey = base58.encodeBase58Check(privateKey, 128) #PRIVKEY = 128

	publicKeyHash = RIPEMD160(SHA256(k.getPublicKey()))
	address = base58.encodeBase58Check(publicKeyHash, 0) #PUBKEY_ADDRESS = 0

	with open(address, "wb") as f:
		f.write(privateKey + "\n")
	print "Saved as ", address


def getinfo(args):
	for filename in args:
		print "----------------"
		print "Filename: ", filename
		with open(filename, "rb") as f:
			privateKey = f.read()
		privateKey = privateKey.split("\n")[0] #first line
		privateKey = privateKey.strip() #ignore whitespace
		privateKey = base58.decodeBase58Check(privateKey, 128) #PRIVKEY = 128
		k = Key()
		k.setPrivateKey(privateKey)
		publicKey = k.getPublicKey()
		publicKeyHash = RIPEMD160(SHA256(publicKey))
		print "Public key: ", publicKey.encode("hex")
		print "Address: ", base58.encodeBase58Check(publicKeyHash, 0) #PUBKEY_ADDRESS = 0



#TODO: other BOTG-functions, like making and signing a transaction


funcs = \
{
"makekey": makekey,
"getinfo": getinfo
}
funcNames = funcs.keys()
funcNames.sort()

if len(sys.argv) < 2 or sys.argv[1] not in funcNames:
	print "Usage: %s <command> [<args>]" % sys.argv[0]
	print "Command can be one of:"
	for fn in funcNames:
		print fn
	sys.exit(1)

funcs[sys.argv[1]](sys.argv[2:])

