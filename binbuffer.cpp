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

#include <string.h>

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
	insert(end(), value.begin(), value.end());
}


CBinBuffer CBinBuffer::readBinBuffer(size_t &pos, size_t length) const
{
	if(pos > size())
		throw CReadError("CBinBuffer::readBinBuffer(size_t &, size_t): start past end of buffer");
	if(size() - pos < length)
		throw CReadError("CBinBuffer::readBinBuffer(size_t &, size_t): end past end of buffer");

	CBinBuffer ret;
	ret.resize(length);
	memcpy(&ret[0], &(*this)[0], size());

	pos += length;
	return ret;;
}


