/*
    transaction.cpp
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

#include "transaction.h"

CTransaction::CTransaction(
	const CString &receipt,
	uint64_t amount,
	const CSHA256 &commitHash,
	const CSHA256 &commitToken,
	const CBinBuffer &nonce):
		m_receipt(receipt),
		m_amount(amount),
		m_nonce(nonce),
		m_commitToken(commitToken),
		m_commitHash(commitHash)
{}


void CTransaction::calculateTokenAndHash()
{
	CBinBuffer data;
	data.appendBinBuffer(m_receipt);
	data.appendUint<uint64_t>(m_amount);
	data.appendRawBinBuffer(m_nonce);

	m_commitToken = CSHA256(data);
	m_commitHash = CSHA256(m_commitToken);
}

