/*
    transaction.h
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

#ifndef TRANSACTION_H
#define TRANSACTION_H

#include <stdint.h>

#include "sha256.h"
#include "ripemd160.h"
#include "binbuffer.h"
#include "cstring.h"


//Number of bytes in a nonce
#define TRANSACTION_NONCE_LENGTH 32

class CTransaction
{
public:
	//TODO: spec
	CTransaction(
		const CString &receipt = "",
		uint64_t amount = 0,
		const CSHA256 &commitHash = CSHA256(),
		const CSHA256 &commitToken = CSHA256(),
		const CBinBuffer &nonce = CBinBuffer());

	//TODO: spec
	void calculateTokenAndHash();

	CString m_receipt;
	uint64_t m_amount;
	CBinBuffer m_nonce; //should have TRANSACTION_NONCE_LENGTH bytes

	//The commit token is a hash of the above.
	CSHA256 m_commitToken;

	//The commit hash is a hash of the commit token.
	CSHA256 m_commitHash;

	CRIPEMD160 m_meetingPoint;
};

#endif

