/*
    sha256.h
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

#ifndef SHA256_H
#define SHA256_H

#include "binbuffer.h"

class CSHA256 : protected CBinBuffer
{
public:
	/*
	data:
	Reference to properly formed CBinBuffer object
	Reference lifetime: at least until the end of this function

	Constructed object:
	SHA256 hash of data

	Exceptions:
	none (TODO)
	*/
	CSHA256(const CBinBuffer &data);

	/*
	hash2:
	Reference to properly formed CSHA256 object
	Reference lifetime: at least until the end of this function
	
	Exceptions:
	none
	*/
	inline bool operator==(const CSHA256 &hash2) const
		{return CBinBuffer::operator==(hash2.toBinBuffer());}

	/*
	Return value:
	Valid pointer
	Pointed memory contains at least getSize() bytes
	Pointed memory contains SHA256 hash
	Pointer ownership: remains with this object
	Pointer lifetime: equal to the lifetime of this object

	Exceptions:
	none
	*/
	inline const unsigned char *getData() const
		{return &(*this)[0];}

	/*
	Return value:
	32

	Exceptions:
	none
	*/
	inline size_t getSize() const
		{return size();}

	/*
	Return value:
	Reference to properly formed CBinBuffer object
	Reference lifetime: equal to the lifetime of this object

	Exceptions:
	none
	*/
	inline const CBinBuffer &toBinBuffer() const
		{return *this;}

	/*
	buffer:
	Reference to properly formed CBinBuffer object
	Reference lifetime: at least until the end of this function
	buffer.size() == 32 (CHECKED)

	Return value:
	SHA256 hash containing the data of buffer

	Exceptions:
	CBinBuffer::CReadError
	*/
	static CSHA256 fromBinBuffer(const CBinBuffer &buffer);


private:
	/*
	Constructed object:
	Uninitialized CSHA256 object

	Exceptions:
	none
	*/
	CSHA256();
};

#endif

