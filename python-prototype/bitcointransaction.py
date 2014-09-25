#    bitcointransaction.py
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

import struct

"""
See multisigchannel.py.
For now, we need support for transactions with the following:

Bitcoin standard:
	ScriptPubKey: OP_DUP OP_HASH160 <pubKeyHash> OP_EQUALVERIFY OP_CHECKSIG
	ScriptSig:    <sig> <pubKey>

2-of-2 multisig:
	ScriptPubKey: 2 <pubKey1> <pubKey2> 2 CHECKMULTISIGVERIFY
	ScriptSig:    <sig1> <sig2>

Signature and secret:
	ScriptPubKey: <pubKey> CHECKSIGVERIFY SHA256 <secretHash> EQUALVERIFY
	ScriptSig:    <secret> <sig>

Time locking
"""



def packVarInt(i):
	if i < 0xfd:
		return struct.pack('B', i) #uint8_t
	elif i <= 0xffff:
		return struct.pack('B', 0xfd) + struct.pack('<H', i) #uint16_t
	elif i <= 0xffffffff:
		return struct.pack('B', 0xfe) + struct.pack('<I', i) #uint32_t
	else:
		return struct.pack('B', 0xff) + struct.pack('<Q', i) #uint64_t


class TxIn:
	def __init__(self):
		#Example data:
		self.previousOutputHash = 'X'*32 #TODO
		self.previousOutputIndex = 0
		self.scriptSig = '' #TODO


	#https://en.bitcoin.it/wiki/Transactions
	#Untested code!!!
	def serialize(self):
		ret = self.previousOutputHash
		ret += struct.pack('<I', self.previousOutputIndex) #uint32_t
		ret += packVarInt(len(self.scriptSig))
		ret += self.scriptSig
		ret += struct.pack('<I', 0xffffffff) #sequence number, uint32_t

		return ret


class TxOut:
	def __init__(self):
		#Example data:
		self.amount = 0
		self.scriptPubKey = '' #TODO


	#https://en.bitcoin.it/wiki/Transactions
	#Untested code!!!
	def serialize(self):
		ret = struct.pack('<Q', self.amount) #uint64_t
		ret += packVarInt(len(self.scriptPubKey))
		ret += self.scriptPubKey		

		return ret


class Transaction:
	def __init__(self, tx_in, tx_out, lockTime=0):
		#Example data:
		self.tx_in = tx_in
		self.tx_out = tx_out
		self.lockTime = lockTime


	#https://en.bitcoin.it/wiki/Transactions
	#Untested code!!!
	def serialize(self):
		ret = struct.pack('<I', 1) #version, uint32_t
		ret += packVarInt(len(self.tx_in))
		for tx_in in self.tx_in:
			ret += tx_in.serialize()
		ret += packVarInt(len(self.tx_out))
		for tx_out in self.tx_out:
			ret += tx_out.serialize()
		ret += struct.pack('<I', self.lockTime) #uint32_t
		return ret


