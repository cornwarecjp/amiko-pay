/*
    ripemd160.cpp
    Copyright (c) 2009-2010 by Satoshi Nakamoto
    Copyright (c) 2009-2012 by The Bitcoin developers
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

#include <openssl/ripemd.h>

#include "ripemd160.h"


CRIPEMD160::CRIPEMD160()
{
	resize(getSize());
}


CRIPEMD160::CRIPEMD160(const CBinBuffer &data)
{
	//TODO: can this fail?
	resize(getSize());
	static unsigned char pblank[1];
	RIPEMD160((data.size()==0 ? pblank : &data[0]), data.size() * sizeof(unsigned char), &(*this)[0]);
}


CRIPEMD160 CRIPEMD160::fromBinBuffer(const CBinBuffer &buffer)
{
	if(buffer.size() != getSize())
		throw CBinBuffer::CReadError("CRIPEMD160::fromBinBuffer(const CBinBuffer &): incorrect input size");

	CRIPEMD160 ret;
	ret.assign(buffer.begin(), buffer.end());
	return ret;
}



