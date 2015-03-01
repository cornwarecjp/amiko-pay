#    bitcointransaction.py
#    Copyright (C) 2014-2015 by CJP
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

import struct
import copy
from crypto import SHA256



"""
See multisigchannel.py.
For now, we need support for transactions with the following:

Bitcoin standard:
	ScriptPubKey: DUP HASH160 <pubKeyHash> EQUALVERIFY CHECKSIG
	ScriptSig:    <sig> <pubKey>

2-of-2 multisig:
	ScriptPubKey: 2 <pubKey1> <pubKey2> 2 CHECKMULTISIG
	ScriptSig:    <sig1> <sig2>

Signature and secret:
	ScriptPubKey: <pubKey> CHECKSIGVERIFY SHA256 <secretHash> EQUAL
	ScriptSig:    <secret> <sig>

Time locking
"""

#see https://en.bitcoin.it/wiki/Transactions
#see https://en.bitcoin.it/wiki/Protocol_specification
#see https://en.bitcoin.it/wiki/Script

def packVarInt(i):
	if i < 0xfd:
		return struct.pack('B', i) #uint8_t
	elif i <= 0xffff:
		return struct.pack('B', 0xfd) + struct.pack('<H', i) #uint16_t
	elif i <= 0xffffffff:
		return struct.pack('B', 0xfe) + struct.pack('<I', i) #uint32_t
	else:
		return struct.pack('B', 0xff) + struct.pack('<Q', i) #uint64_t


def unpackVarInt(data):
	firstByte = struct.unpack('B', data[0])[0] #uint8_t
	if firstByte < 0xfd:
		value = firstByte
		return value, 1
	elif firstByte == 0xfd:
		value = struct.unpack('<H', data[1:3])[0] #uint16_t
		return value, 3
	elif firstByte == 0xfe:
		value = struct.unpack('<I', data[1:5])[0] #uint32_t
		return value, 5
	elif firstByte == 0xff:
		value = struct.unpack('<Q', data[1:9])[0] #uint64_t
		return value, 9

	raise Exception("Bug detected in unpackVarInt")



class OP:
	ZERO = 0x00
	TWO = 0x52
	DUP = 0x76
	EQUAL  = 0x87
	EQUALVERIFY = 0x88
	SHA256 = 0xa8
	HASH160 = 0xa9
	CHECKSIG = 0xac
	CHECKSIGVERIFY = 0xad
	CHECKMULTISIG = 0xae



class Script:
	@staticmethod
	def standardPubKey(pubKeyHash):
		return Script((OP.DUP, OP.HASH160, pubKeyHash, OP.EQUALVERIFY, OP.CHECKSIG))


	@staticmethod
	def multiSigPubKey(pubKey1, pubKey2):
		return Script((OP.TWO, pubKey1, pubKey2, OP.TWO, OP.CHECKMULTISIG))


	@staticmethod
	def secretPubKey(pubKey, secretHash):
		return Script((pubKey, OP.CHECKSIGVERIFY, OP.SHA256, secretHash, OP.EQUAL))


	@staticmethod
	def deserialize(data):
		elements = []
		while len(data) > 0:
			opcode = struct.unpack('B', data[0])[0]
			data = data[1:]

			if opcode <= 0x4e:
				if opcode <= 0x4b:
					length = opcode
				elif opcode == 0x4c:
					length = struct.unpack('B', data[:1])[0]
					data = data[1:]
				elif opcode == 0x4d:
					length = struct.unpack('<H', data[:2])[0]
					data = data[2:]
				else:
					length = struct.unpack('<I', data[:4])[0]
					data = data[4:]
				elements.append(data[:length])
				data = data[length:]
			else:
				elements.append(opcode)

		return Script(elements)


	def __init__(self, elements=tuple()):
		self.elements = elements


	def serialize(self):
		return ''.join([self.__serializeElement(e) for e in self.elements])


	def __serializeElement(self, e):
		if isinstance(e, str):
			if len(e) <= 0x4b:
				return struct.pack('B', len(e)) + e
			elif len(e)<= 0xff:
				return struct.pack('B', 0x4c) + struct.pack('B', len(e)) + e
			elif len(e) <= 0xffff:
				return struct.pack('B', 0x4d) + struct.pack('<H', len(e)) + e
			elif len(e) <= 0xffffffff:
				return struct.pack('B', 0x4e) + struct.pack('<I', len(e)) + e
			else:
				raise Exception('Too long data for a script item')
		elif isinstance(e, int):
			return struct.pack('B', e)
		else:
			raise Exception('Unsupported element type in script')



class TxIn:
	@staticmethod
	def deserialize(data):
		outputHash = data[:32]
		data = data[32:]

		outputIndex = struct.unpack('<I', data[:4])[0] #uint32_t
		data = data[4:]

		scriptSigLen, numBytesInLen = unpackVarInt(data)
		data = data[numBytesInLen:]

		scriptSig = Script.deserialize(data[:scriptSigLen])
		data = data[scriptSigLen:]

		sequenceNumber = struct.unpack('<I', data[:4])[0] #uint32_t
		if sequenceNumber != 0xffffffff:
			raise Exception("Deserialization failed: non-standard sequence number")

		obj = TxIn(outputHash, outputIndex)
		obj.scriptSig = scriptSig
		numBytes = 36 + numBytesInLen + scriptSigLen + 4

		return obj, numBytes


	def __init__(self, outputHash, outputIndex):
		self.previousOutputHash = outputHash
		self.previousOutputIndex = outputIndex
		self.scriptSig = Script() #Default: no signature (to be filled in later)


	def serialize(self):
		ret = self.previousOutputHash
		ret += struct.pack('<I', self.previousOutputIndex) #uint32_t
		scriptSig = self.scriptSig.serialize()
		ret += packVarInt(len(scriptSig))
		ret += scriptSig
		ret += struct.pack('<I', 0xffffffff) #sequence number, uint32_t

		return ret


class TxOut:
	@staticmethod
	def deserialize(data):
		amount = struct.unpack('<Q', data[:8])[0] #uint64_t
		data = data[8:]

		scriptPubKeyLen, numBytesInLen = unpackVarInt(data)
		data = data[numBytesInLen:]

		scriptPubKey = Script.deserialize(data[:scriptPubKeyLen])

		obj = TxOut(amount, scriptPubKey)
		numBytes = 8 + numBytesInLen + scriptPubKeyLen

		return obj, numBytes


	def __init__(self, amount, scriptPubKey):
		self.amount = amount
		self.scriptPubKey = scriptPubKey


	def serialize(self):
		ret = struct.pack('<Q', self.amount) #uint64_t
		scriptPubKey = self.scriptPubKey.serialize()
		ret += packVarInt(len(scriptPubKey))
		ret += scriptPubKey		

		return ret


class Transaction:
	@staticmethod
	def deserialize(data):
		version = struct.unpack('<I', data[:4])[0] #version, uint32_t
		data = data[4:]

		if version != 1:
			raise Exception("Transaction deserialization failed: version != 1")

		num_tx_in, numBytes = unpackVarInt(data)
		data = data[numBytes:]
		tx_in = []
		for i in range(num_tx_in):
			obj, numBytes = TxIn.deserialize(data)
			data = data[numBytes:]
			tx_in.append(obj)

		num_tx_out, numBytes = unpackVarInt(data)
		data = data[numBytes:]
		tx_out = []
		for i in range(num_tx_out):
			obj, numBytes = TxOut.deserialize(data)
			data = data[numBytes:]
			tx_out.append(obj)

		#To make sure we're not accepting a transaction that has been serialized
		#in a non-standard way (e.g. containing trailing information).
		#This might be important when making/checking signatures.
		#It might be advisable anyway to re-serialize a received transaction and
		#check whether the result matches the original.
		if len(data) != 4:
			raise Exception("Transaction deserialization failed: incorrect data length")

		lockTime = struct.unpack('<I', data[:4])[0] #uint32_t

		return Transaction(tx_in, tx_out, lockTime)


	def __init__(self, tx_in, tx_out, lockTime=0):
		self.tx_in = tx_in
		self.tx_out = tx_out
		self.lockTime = lockTime


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


	def getSignatureBodyHash(self, index, scriptPubKey, hashType=1):
		#https://en.bitcoin.it/wiki/OP_CHECKSIG

		#1.	the public key and the signature are popped from the stack, in that
		#	order. If the hash-type value is 0, then it is replaced by the
		#	last_byte of the signature. Then the last byte of the signature is
		#	always deleted.
		#2.	A new subscript is created from the instruction from the most
		#	recently parsed OP_CODESEPARATOR (last one in script) to the end of
		#	the script. If there is no OP_CODESEPARATOR the entire script
		#	becomes the subscript (hereby referred to as subScript)
		#3.	The sig is deleted from subScript.
		#4.	All OP_CODESEPARATORS are removed from subScript

		#Since there is no OP_CODESEPARATOR or signature in scriptPubKey:
		subScript = scriptPubKey

		#6.	A copy is made of the current transaction (hereby referred to txCopy)
		txCopy = copy.deepcopy(self)

		#7.	The scripts for all transaction inputs in txCopy are set to empty
		#	scripts (exactly 1 byte 0x00)
		for tx_in in txCopy.tx_in:
			tx_in.scriptSig = Script() #Empty (zero-byte)

		#8.	The script for the current transaction input in txCopy is set to
		#	subScript (lead in by its length as a var-integer encoded!)
		txCopy.tx_in[index].scriptSig = subScript

		#An array of bytes is constructed from the serialized txCopy appended by
		#four bytes for the hash type.
		signatureBody = txCopy.serialize() + struct.pack('<I', hashType) #uint32_t

		#This array is sha256 hashed twice,
		bodyHash = SHA256(SHA256(signatureBody))

		return bodyHash


	def signInputWithSignatures(self, index, scriptSigTemplate, signatures):
		elements = scriptSigTemplate[:]
		for sig in signatures:
			i = elements.index(None)
			elements[i] = sig

		self.tx_in[index].scriptSig = Script(elements)


	def signInput(self, index, scriptPubKey, scriptSigTemplate, privateKeys):
		hashType = 1 #SIGHASH_ALL
		bodyHash = self.getSignatureBodyHash(index, scriptPubKey, hashType)

		#then the public key is used to check the supplied signature against the
		#hash. The secp256k1 elliptic curve is used for the verification with
		#the given public key.

		#5.	The hashtype is removed from the last byte of the sig and stored
		#hashType = sig[-1]
		#sig = sig[:-1]
		#Here we do the inverse - add hashType:
		signatures = \
		[
			key.sign(bodyHash) + struct.pack('B', hashType) #uint8_t
			for key in privateKeys
		]

		self.signInputWithSignatures(index, scriptSigTemplate, signatures)


	def getTransactionID(self):
		return SHA256(SHA256(self.serialize())) #Note: in Bitcoin, the tx hash is shown reversed!


