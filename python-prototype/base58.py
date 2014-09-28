#    base58.py
#    Copyright (c) 2009-2010 Satoshi Nakamoto
#    Copyright (c) 2009-2012 The Bitcoin Developers
#    Copyright (C) 2013-2014 by CJP
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

import binascii
import struct

from crypto import SHA256, RIPEMD160



base58Chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def encodeBase58(data):
	# Convert big endian data to bignum
	bignum = int(data.encode("hex"), 16)

	ret = ""
	while bignum > 0:
		bignum, remainder = divmod(bignum, 58)
		ret = ret + base58Chars[remainder]

	# Leading zeroes encoded as base58 zeros
	for i in range(len(data)):
		if data[i] != '\0':
			break
		ret = ret + base58Chars[0]

	# Convert little endian string to big endian
	ret = ret[::-1]

	return ret


def decodeBase58(data):
	#TODO: there might be a bug when the to-be-decoded value is zero

	#Leading zeroes:
	zeroes = ""
	while len(data) > 0 and data[0] == base58Chars[0]:
		zeroes += '\0'
		data = data[1:]

	#Big endian base58 decoding:
	bignum = 0
	for c in data:
		digit = base58Chars.index(c)
		bignum = 58*bignum + digit

	#To big endian:
	ret = binascii.unhexlify("%x" % bignum)

	#Skip zeroes:
	while len(ret) > 0 and ret[0] == '\0':
		ret = ret[1:]

	return zeroes + ret


def encodeBase58Check_noVersion(data):
	# add 4-byte hash check to the end
	checksum = SHA256(SHA256(data))[:4]
	return encodeBase58(data + checksum)


def decodeBase58Check_noVersion(data):
	decoded = decodeBase58(data)
	checksum = decoded[-4:]
	rest = decoded[:-4]
	if checksum != SHA256(SHA256(rest))[:4]:
		raise Exception("Checksum failed")
	return rest


def encodeBase58Check(data, version):
	"""
	version:
	PUBKEY_ADDRESS = 0,
	SCRIPT_ADDRESS = 5,
	PUBKEY_ADDRESS_TEST = 111,
	PRIVKEY = 128,
	SCRIPT_ADDRESS_TEST = 196,
	AMIKO = 23,
	"""

	return encodeBase58Check_noVersion(
		struct.pack('B', version) + data)


def decodeBase58Check(data, version):
	decoded = decodeBase58Check_noVersion(data)
	if version != struct.unpack('B', decoded[0])[0]:
		raise Exception("Version mismatch")
	return decoded[1:]


if __name__ == "__main__":

	def testPubKey(testDescr, hexPubKey, address):
		pubKey = binascii.unhexlify(hexPubKey)
		hashedPK = RIPEMD160(SHA256(pubKey))

		print testDescr, encodeBase58Check(hashedPK, 0) == address
		print testDescr, decodeBase58Check(address, 0) == hashedPK


	#I just took some random keys from the block chain
	#(thanks to blockexplorer.com for the service).
	#I have no idea whose keys they are.

	#hash160 = 66750c10f3f64d0e4b8d6d80fa3d9f08cb59cdd3
	testPubKey("  The address of a public key corresponds to the known value",
		"0406e4a5c2a5f8dcfbfbadd86dd4fc908e4de1068599f2a818677f8eb0f4e375"
		"b220fb7c0845960d0ec2c11cdffa4b22dbb264e6f2e8c0b90d196985aa11cfd435",
		"1ALk99MqTNc9ifW1DhbUa8g39FTiHuyr3L"
		)

	#hash160 = 0000a21b7e708c3816f18be8cfce5f6740f94c2b
	testPubKey("  Leading zeroes are processed as required",
		"04791ee6c09049ba1c7a3db01b563d0a3ad580a4e2ce232fa7eb017ea7384194"
		"aecd156054a3186bd405363936715c6216e73980ff03f2c9eeec74ec132a32f7c4",
		"111kzsNZ1w27kSGXwyov1ZvUGVLJMvLmJ"
		)

