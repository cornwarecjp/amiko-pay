/*
    bitcoinaddress.cpp
    Copyright (c) 2009-2010 Satoshi Nakamoto
    Copyright (c) 2009-2012 The Bitcoin Developers
    Copyright (C) 2013 by CJP

    This file is part of Amiko Pay.

    Amiko Pay is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Amiko Pay is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Amiko Pay. If not, see <http://www.gnu.org/licenses/>.
*/

#include <stdint.h>

#include <vector>
#include <algorithm>

#include "ripemd160.h"

#include "bitcoinaddress.h"


static const char *base58Chars = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

//Big endian big number class
class CBigNum : public std::vector<uint32_t>
{
public:

	CBigNum(const CBinBuffer &data)
	{
		size_t pos = 0;

		//Generally, data.size() is not a multiple of 4 bytes.
		//So the first value must be read from fewer than 4 bytes.
		if(data.size() % 4 != 0)
		{
			uint32_t firstValue = 0;
			while((data.size()-pos) % 4 != 0)
				firstValue = (firstValue<<8) + data.readUint<uint8_t>(pos);
			push_back(firstValue);
		}

		//Read all the other values
		while(pos < data.size())
			push_back(data.readUint<uint32_t>(pos));
	}

	//returns the remainder
	unsigned int divideBy58()
	{
		unsigned int remainder = 0;
		for(size_t i=0; i < size(); i++)
		{
			uint64_t value = (uint64_t(remainder)<<32) + (*this)[i];
			remainder = value % 58;
			(*this)[i] = value / 58;
		}
		return remainder;
	}

	bool isGreaterThanZero() const
	{
		for(size_t i=0; i < size(); i++)
			if((*this)[i] != 0)
				return true;
		return false;
	}
};

// Encode a byte sequence as a base58-encoded string
inline CString encodeBase58(const CBinBuffer &data)
{
	// Convert big endian data to bignum
	CBigNum bignum(data);

	// Convert bignum to CString
	CString str;
	// Expected size increase from base58 conversion is approximately 137%
	// use 138% to be safe
	str.reserve(data.size() * 138 / 100 + 1);

	while(bignum.isGreaterThanZero())
	{
		unsigned int remainder = bignum.divideBy58();
		str += base58Chars[remainder];
	}

	// Leading zeroes encoded as base58 zeros
	for(size_t i=0; i < data.size(); i++)
	{
		if(data[i] != 0) break;
		str += base58Chars[0];
	}

	// Convert little endian std::string to big endian
	std::reverse(str.begin(), str.end());
	return str;
}


inline CString encodeBase58Check(const CBinBuffer &data)
{
	// add 4-byte hash check to the end
	CSHA256 hash(CSHA256(data).toBinBuffer());
	CBinBuffer firstFourBytes = hash.toBinBuffer(); firstFourBytes.resize(4);
	CBinBuffer withChecksum(data);
	withChecksum.appendRawBinBuffer(firstFourBytes);
	return encodeBase58(withChecksum);
}


CString getBitcoinAddress(const CSHA256 &hashedPublicKey)
{
	CRIPEMD160 address(hashedPublicKey.toBinBuffer());

	/*
	PUBKEY_ADDRESS = 0,
	SCRIPT_ADDRESS = 5,
	PUBKEY_ADDRESS_TEST = 111,
	SCRIPT_ADDRESS_TEST = 196,
	AMIKO = 23,
	*/
	unsigned int version = 0; //PUBKEY_ADDRESS

	CBinBuffer data;
	data.appendUint<uint8_t>(version);
	data.appendRawBinBuffer(address.toBinBuffer());
	return encodeBase58Check(data);
}


