#!/usr/bin/env python
#    timestamp.py
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
import time
from datetime import datetime
import binascii
sys.path.append("..")

from amiko.core import bitcoind as bd
from amiko.core import settings
from amiko.utils import bitcoinutils, crypto, base58



bitcoind = None

def connect():
	global bitcoind

	print "Reading the settings file...",
	s = settings.Settings("../amikopay.conf")
	print "done"
	print "Connecting...",
	bitcoind = bd.Bitcoind(s)
	print "done"


def help(args):
	if len(args) == 0:
		print "Usage: %s command [args]" % sys.argv[0]
		print "Command can be one of:"
		for fn in funcNames:
			print fn

	if "help" in args:
		print "Usage: %s help [command]" % sys.argv[0]

	if "make" in args:
		print "Usage: %s make to_be_timestamped_file output_certificate_file" % sys.argv[0]

	if "verify" in args:
		print "Usage: %s verify timestamped_file input_certificate_file" % sys.argv[0]


def getMerkleBranch(transactions, index):
	ret = []
	while len(transactions) > 1:
		if (len(transactions) % 2) != 0:
			transactions.append(transactions[-1]) #repeat last element to make even-length

		nextIndex = index/2
		left = transactions[2*nextIndex]
		right = transactions[2*nextIndex+1]

		ret.append((left, right))

		transactions = \
		[
			crypto.SHA256(crypto.SHA256(
				transactions[2*i] + transactions[2*i+1]
				))

			for i in range(len(transactions)/2)
		]
		index = nextIndex

	return ret, transactions[0]


def make(args):
	if len(args) != 2:
		help(["make"])
		sys.exit(1)

	with open(args[0], "rb") as f:
		data = f.read()

	dataHash = crypto.SHA256(crypto.SHA256(data))

	fee =    10000 #0.1 mBTC = 0.0001 BTC
	connect()

	changeAddress = bitcoind.getNewAddress()
	changeHash = base58.decodeBase58Check(changeAddress, 0) # PUBKEY_ADDRESS = 0

	tx = bitcoinutils.sendToDataPubKey(bitcoind, dataHash, changeHash, fee)
	txID = tx.getTransactionID()[::-1].encode("hex")
	print "Transaction ID: ", txID

	bitcoind.sendRawTransaction(tx.serialize())

	print "Transaction is published. Now we wait for 3 confirmations..."
	confirmations = -1
	while confirmations < 3:
		time.sleep(5)
		try:
			newConfirmations = bitcoind.getTransaction(txID)["confirmations"]
		except KeyError:
			newConfirmations = 0
		if newConfirmations != confirmations:
			print "  %d confirmations" % newConfirmations
		confirmations = newConfirmations

	height = bitcoind.getBlockCount()
	for i in range(1000):
		transactionsInBlock = bitcoind.getTransactionHashesByBlockHeight(height)
		if txID in transactionsInBlock:
			break
		height -= 1
	if txID not in transactionsInBlock:
		raise Exception(
			"Something went wrong: transaction ID not found in the last 1000 blocks")

	print "Block height: ", height

	index = transactionsInBlock.index(txID)
	transactionsInBlock = [binascii.unhexlify(x)[::-1] for x in transactionsInBlock]
	merkleBranch, merkleRoot = getMerkleBranch(transactionsInBlock, index)

	blockInfo = bitcoind.getBlockInfoByBlockHeight(height)
	if blockInfo["merkleroot"] != merkleRoot[::-1].encode("hex"):
		raise Exception("Something went wrong: merkle root value mismatch")

	dt = datetime.utcfromtimestamp(blockInfo["time"])
	timeText = dt.strftime("%A %B %d %I:%m:%S %p %Y (UTC)")

	with open(args[1], "wb") as f:
		f.write("#Timestamp certificate for the file %s\n\n" % args[0])

		f.write("#Double-SHA256 of the file contents:\n")
		f.write("dataHash = %s\n\n" % dataHash.encode("hex"))

		f.write("#The timestamping transaction, containing the above hash:\n")
		f.write("transaction = %s\n\n" % tx.serialize().encode("hex"))

		f.write("#The double-SHA256 of the timestamping transaction:\n")
		f.write("#(This is the same as the transaction ID, with the byte order reversed)\n")
		f.write("transactionHash = %s\n\n" % tx.getTransactionID().encode("hex"))

		f.write("#The Merkle-branch of the timestamping transaction:\n")
		for i in range(len(merkleBranch)):
			left, right = merkleBranch[i]
			f.write("merkle_%d = %s, %s\n" % (i, left.encode("hex"), right.encode("hex")))
		f.write("\n")

		f.write("#The Merkle root of the block:\n")
		f.write("#(byte order is the reverse as typically shown in Bitcoin)\n")
		f.write("merkleRoot = %s\n\n" % merkleRoot.encode("hex"))

		f.write("#The block information:\n")
		f.write("blockHeight = %d\n" % height)
		f.write("blockHash = %s\n" % blockInfo["hash"])
		f.write("blockTime = %d\n\n" % blockInfo["time"])

		f.write("#The timestamp:\n")
		f.write("timestamp = %s\n" % timeText)

def verify(args):
	if len(args) != 2:
		help(["verify"])
		sys.exit(1)

	print "Not Yet Implemented" #TODO


funcs = \
{
"help": help,
"make": make,
"verify": verify
}
funcNames = funcs.keys()
funcNames.sort()

if len(sys.argv) < 2 or sys.argv[1] not in funcNames:
	help([])
	sys.exit(1)

funcs[sys.argv[1]](sys.argv[2:])

