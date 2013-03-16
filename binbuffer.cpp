/*
    binbuffer.cpp
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

#include <cstdio>
#include <string.h>
#include <stdint.h>

#include "cstring.h"

#include "binbuffer.h"

CBinBuffer::CBinBuffer()
{
}


CBinBuffer::CBinBuffer(const CString &str)
{
	resize(str.size());
	memcpy(&((*this)[0]), str.c_str(), size());
}


bool CBinBuffer::operator==(const CBinBuffer &data) const
{
	if(size() != data.size()) return false;
	return memcmp(&(*this)[0], &data[0], size()) == 0;
}


const CBinBuffer &CBinBuffer::operator+=(const CBinBuffer &data)
{
	insert(end(), data.begin(), data.end());
	return *this;
}


const CBinBuffer CBinBuffer::operator+(const CBinBuffer &data) const
{
	CBinBuffer ret(*this);
	ret += data;
	return ret;
}


CString CBinBuffer::toString() const
{
	CString ret;
	ret.resize(size());
	for(size_t i=0; i<size(); i++)
	{
		if((*this)[i] == '\0')
			throw CReadError(
				"Buffer could not be converted to string because it contains a null character");

		ret[i] = (*this)[i];
	}
	return ret;
}


void CBinBuffer::appendBinBuffer(const CBinBuffer &value)
{
	if(value.size() > uint32_t(-1))
		throw CWriteError("CBinBuffer::appendBinBuffer(const CBinBuffer &): buffer too large");

	appendUint<uint32_t>(value.size());
	appendRawBinBuffer(value);
}


void CBinBuffer::appendRawBinBuffer(const CBinBuffer &value)
{
	insert(end(), value.begin(), value.end());
}


CBinBuffer CBinBuffer::readBinBuffer(size_t &pos) const
{
	size_t length = readUint<uint32_t>(pos);
	return readRawBinBuffer(pos, length);
}


CBinBuffer CBinBuffer::readRawBinBuffer(size_t &pos, size_t length) const
{
	if(pos > size())
		throw CReadError("CBinBuffer::readBinBuffer(size_t &, size_t): start past end of buffer");
	if(size() - pos < length)
		throw CReadError("CBinBuffer::readBinBuffer(size_t &, size_t): end past end of buffer");

	CBinBuffer ret;
	ret.resize(length);
	memcpy(&ret[0], &(*this)[pos], length);

	pos += length;
	return ret;
}


CString CBinBuffer::hexDump() const
{
	CString ret;
	for(size_t i=0; i < size(); i++)
		ret += CString::format("%02x", 3, (*this)[i]);
	return ret;
}

inline unsigned int decodeHexChar(char c)
{
	//TODO: more efficient way with no branching etc.
	if(c>='0' && c<='9')
		return c-'0';
	if(c>='a' && c<='f')
		return 10+c-'a';
	if(c>='A' && c<='F')
		return 10+c-'F';
	throw CBinBuffer::CWriteError("decodeHexChar: invalid character");
	return 0;
}

CBinBuffer CBinBuffer::fromHex(const CString &hex)
{
	if(hex.length() % 2 != 0)
		throw CWriteError("CBinBuffer::fromHex(const CString &): input contains an odd number of characters");

	CBinBuffer ret;
	ret.resize(hex.length()/2);

	size_t j = 0;
	for(size_t i=0; i < ret.size(); i++)
	{
		unsigned int c1 = decodeHexChar(hex[j]);
		unsigned int c2 = decodeHexChar(hex[j+1]);
		ret[i] = 16*c1 + c2;
		j += 2;
	}

	return ret;
}


