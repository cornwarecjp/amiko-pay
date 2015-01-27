#    base58.py
#    Copyright (c) 2009-2010 Satoshi Nakamoto
#    Copyright (c) 2009-2012 The Bitcoin Developers
#    Copyright (C) 2013-2015 by CJP
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

import binascii
import struct

from crypto import SHA256, RIPEMD160



base58Chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def encodeBase58(data):
	"""
	Base58-encodes the given data, without checksum or version number.

	Arguments:
	data: str; the to-be-encoded data.

	Return value:
	str; the encoded data.
	"""

	# Convert big endian data to bignum
	bignum = int('00' + data.encode("hex"), 16) #00 is necessary in case of empty string

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
	"""
	Base58-decodes the given data, without checksum or version number.

	Arguments:
	data: str; the to-be-decoded data.

	Return value:
	str; the decoded data.

	Exceptions:
	ValueError: data contains an illegal character
	"""

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
	#First to hex:
	ret = "%x" % bignum
	#Add leading zero to force even-length: (unhexlify doesn't like odd-length)
	ret = "0"*(len(ret) & 1) + ret
	#Then to binary string:
	ret = binascii.unhexlify(ret)

	#Skip zeroes:
	while len(ret) > 0 and ret[0] == '\0':
		ret = ret[1:]

	return zeroes + ret


def encodeBase58Check_noVersion(data):
	"""
	Base58-encodes the given data, with checksum but without version number.

	Arguments:
	data: str; the to-be-encoded data.

	Return value:
	str; the encoded data.
	"""

	# add 4-byte hash check to the end
	checksum = SHA256(SHA256(data))[:4]
	return encodeBase58(data + checksum)


def decodeBase58Check_noVersion(data):
	"""
	Base58-decodes the given data, with checksum but without version number.

	Arguments:
	data: str; the to-be-decoded data.

	Return value:
	str; the decoded data.

	Exceptions:
	Exception: checksum failed
	ValueError: data contains an illegal character
	"""

	decoded = decodeBase58(data)
	checksum = decoded[-4:]
	rest = decoded[:-4]
	if checksum != SHA256(SHA256(rest))[:4]:
		raise Exception("Checksum failed")
	return rest


def encodeBase58Check(data, version):
	"""
	Base58-encodes the given data, with checksum and version number.

	Arguments:
	data: str; the to-be-encoded data.
	version: int, the version number. Example values:
	         PUBKEY_ADDRESS = 0
	         SCRIPT_ADDRESS = 5
	         PUBKEY_ADDRESS_TEST = 111
	         PRIVKEY = 128
	         SCRIPT_ADDRESS_TEST = 196
	         AMIKO = 23 (not used anywhere)

	Return value:
	str; the encoded data.
	"""

	return encodeBase58Check_noVersion(
		struct.pack('B', version) + data)


def decodeBase58Check(data, version):
	"""
	Base58-decodes the given data, with checksum and version number.

	Arguments:
	data: str; the to-be-decoded data.
	version: int, the version number. Example values:
	         PUBKEY_ADDRESS = 0
	         SCRIPT_ADDRESS = 5
	         PUBKEY_ADDRESS_TEST = 111
	         PRIVKEY = 128
	         SCRIPT_ADDRESS_TEST = 196
	         AMIKO = 23 (not used anywhere)

	Return value:
	str; the decoded data.

	Exceptions:
	Exception: checksum failed, or version number mismatch
	ValueError: data contains an illegal character
	"""

	decoded = decodeBase58Check_noVersion(data)
	if version != struct.unpack('B', decoded[0])[0]:
		raise Exception("Version mismatch")
	return decoded[1:]

