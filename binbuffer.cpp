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


void CBinBuffer::appendBinBuffer(const CBinBuffer &value)
{
	if(value.size() > uint32_t(-1))
		throw CWriteError("CBinBuffer::appendBinBuffer(const CBinBuffer &): buffer too large");

	appendUint<uint32_t>(value.size());
	insert(end(), value.begin(), value.end());
}


CBinBuffer CBinBuffer::readBinBuffer(size_t &pos) const
{
	size_t length = readUint<uint32_t>(pos);

	if(pos > size())
		throw CReadError("CBinBuffer::readBinBuffer(size_t &): start past end of buffer");
	if(size() - pos < length)
		throw CReadError("CBinBuffer::readBinBuffer(size_t &): end past end of buffer");

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

