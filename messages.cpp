/*
    messages.cpp
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

#include "messages.h"


//=====================================
CPublicKeyMessage::~CPublicKeyMessage()
{}

CBinBuffer CPublicKeyMessage::getSerializedBody() const
{return m_publicKey;}

void CPublicKeyMessage::setSerializedBody(const CBinBuffer &data)
{m_publicKey = data;}


//=====================================
CAckMessage::~CAckMessage()
{}

CBinBuffer CAckMessage::getSerializedBody() const
{return CBinBuffer();}

void CAckMessage::setSerializedBody(const CBinBuffer &data)
{}


//=====================================
CNackMessage::~CNackMessage()
{}

CBinBuffer CNackMessage::getSerializedBody() const
{
	CBinBuffer ret;
	ret.appendRawBinBuffer(m_rejectedBySource.toBinBuffer());
	ret.appendUint<uint32_t>(m_reasonCode);
	ret.appendBinBuffer(CString(m_reason));
	return ret;
}

void CNackMessage::setSerializedBody(const CBinBuffer &data)
{
	size_t pos = 0;
	m_rejectedBySource = CSHA256::fromBinBuffer(
		data.readRawBinBuffer(pos, CSHA256::getSize()));

	uint32_t reasonCode = data.readUint<uint32_t>(pos);
	switch(reasonCode)
	{
	case eNonstandardReason:
	case eBadSignature:
	case eWrongBalance:
		m_reasonCode = eReason(reasonCode);
		break;
	default:
		throw CBinBuffer::CReadError("CNackMessage::setSerializedBody(const CBinBuffer &): invalid reason code");
	}

	m_reason = data.readBinBuffer(pos).toString();
}


//=====================================
CFinStateMessage::~CFinStateMessage()
{}

CBinBuffer CFinStateMessage::getSerializedBody() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer ret;
	ret.appendUint<uint64_t>(m_myBalance   + (uint64_t(1)<<62));
	ret.appendUint<uint64_t>(m_yourBalance + (uint64_t(1)<<62));

	ret.appendUint<uint32_t>(m_pendingTransactions.size());
	ret.appendUint<uint32_t>(m_myPendingDeposits.size());
	ret.appendUint<uint32_t>(m_yourPendingDeposits.size());

	for(size_t i=0; i < m_pendingTransactions.size(); i++)
		ret.appendRawBinBuffer(m_pendingTransactions[i].toBinBuffer());
	for(size_t i=0; i < m_myPendingDeposits.size(); i++)
		ret.appendRawBinBuffer(m_myPendingDeposits[i].toBinBuffer());
	for(size_t i=0; i < m_yourPendingDeposits.size(); i++)
		ret.appendRawBinBuffer(m_yourPendingDeposits[i].toBinBuffer());

	return ret;
}

void CFinStateMessage::setSerializedBody(const CBinBuffer &data)
{
	size_t pos = 0;
	m_myBalance   = data.readUint<uint64_t>(pos) - (uint64_t(1)<<62);
	m_yourBalance = data.readUint<uint64_t>(pos) - (uint64_t(1)<<62);

	uint32_t numPendingTransactions = data.readUint<uint32_t>(pos);
	uint32_t numMyPendingDeposits   = data.readUint<uint32_t>(pos);
	uint32_t numyourPendingDeposits = data.readUint<uint32_t>(pos);

	if(CSHA256::getSize() *
		(numPendingTransactions+numMyPendingDeposits+numyourPendingDeposits)
		!= data.size()-pos)
			throw CBinBuffer::CReadError(
				"CFinStateMessage::setSerializedBody(const CBinBuffer &): sizes don't add up to remaining buffer size"
				);

	m_pendingTransactions.resize(numPendingTransactions);
	m_myPendingDeposits.resize(numMyPendingDeposits);
	m_yourPendingDeposits.resize(numyourPendingDeposits);

	for(size_t i=0; i < numPendingTransactions; i++)
		m_pendingTransactions[i] = CSHA256::fromBinBuffer(
			data.readRawBinBuffer(pos, CSHA256::getSize())
			);
	for(size_t i=0; i < numMyPendingDeposits; i++)
		m_myPendingDeposits[i] = CSHA256::fromBinBuffer(
			data.readRawBinBuffer(pos, CSHA256::getSize())
			);
	for(size_t i=0; i < numyourPendingDeposits; i++)
		m_yourPendingDeposits[i] = CSHA256::fromBinBuffer(
			data.readRawBinBuffer(pos, CSHA256::getSize())
			);
}


