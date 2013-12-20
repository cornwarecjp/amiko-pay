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
#include "cstring.h"


typedef uint32_t transactionID_t;
typedef  int32_t signed_transactionID_t;


class CTransaction
{
public:
	CTransaction(
		transactionID_t ID = 0,
		const CString &receipt = "",
		int64_t amount = 0,
		const CSHA256 &commitHash = CSHA256(),
		const CRIPEMD160 &meetingPoint = CRIPEMD160()) :
			m_ID(ID),
			m_receipt(receipt),
			m_amount(amount),
			m_commitHash(commitHash),
			m_meetingPoint(meetingPoint)
		{}

	transactionID_t m_ID;
	CString m_receipt;
	int64_t m_amount;

	CSHA256 m_commitHash;
	CRIPEMD160 m_meetingPoint;
};

#endif

