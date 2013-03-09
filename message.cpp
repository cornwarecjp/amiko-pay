/*
    message.cpp
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
#include <stdint.h>

#include "message.h"
#include "messages.h"


CMessage::CMessage()
{
	//TODO: sensible default values, e.g. for timestamp
}


CMessage::~CMessage()
{
}


CMessage *CMessage::constructMessage(const CBinBuffer &data)
{
	//The ID is located at bytes 4..8
	if(data.size() < 8)
		throw CSerializationError("Message does not contain a type ID");
	size_t pos = 4;
	uint32_t ID = data.readUint<uint32_t>(pos);

	CMessage *ret = NULL;

	switch(ID)
	{
	case ePublicKey:
		ret = new CPublicKeyMessage;
		break;
	case eAck:
		ret = new CAckMessage;
		break;
	case eNack:
		ret = new CNackMessage;
		break;
	case eFinState:
		ret = new CFinStateMessage;
		break;
	default:
		throw CSerializationError("Invalid message type ID");
	}

	//TODO: in case of any exception here, delete the object to prevent a memory leak
	ret->deserialize(data);

	return ret;
}


CBinBuffer CMessage::serialize() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer ret;
	ret.appendBinBuffer(getSignedBody());
	ret.appendBinBuffer(m_Signature);

	return ret;
}


void CMessage::deserialize(const CBinBuffer &data)
{
	size_t pos = 0;
	setSignedBody(data.readBinBuffer(pos));
	m_Signature = data.readBinBuffer(pos);

	//TODO: verify signature
	//TODO: sanity check on timestamp
	//TODO: check hashes of previous messages
}


void CMessage::sign(const CKey &key)
{
	//TODO: check whether m_Source corresponds with key
	//maybe set m_Source??
	m_Signature = key.sign(CSHA256(getSignedBody()));
}


bool CMessage::verifySignature(const CKey &key) const
{
	//TODO: check whether m_Source corresponds with key
	return key.verify(CSHA256(getSignedBody()), m_Signature);
}


CBinBuffer CMessage::getSignedBody() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer ret;
	ret.appendUint<uint32_t>(getTypeID());
	ret.appendBinBuffer(m_source.toBinBuffer());
	ret.appendBinBuffer(m_destination.toBinBuffer());
	ret.appendUint<uint64_t>(m_Timestamp);
	ret.appendBinBuffer(m_lastSentBySource.toBinBuffer());
	ret.appendBinBuffer(m_lastAcceptedBySource.toBinBuffer());
	ret.appendBinBuffer(getSerializedBody());
	return ret;
}


void CMessage::setSignedBody(const CBinBuffer &data)
{
	size_t pos = 0;

	uint32_t ID = data.readUint<uint32_t>(pos);
	if(ID != getTypeID())
		throw CSerializationError(CString::format(
			"CMessage::setSignedBody(const CBinBuffer &): ID in message (%d) does not match ID of message class (%d)",
			256, ID, getTypeID()));

	m_source = CSHA256::fromBinBuffer(data.readBinBuffer(pos));
	m_destination = CSHA256::fromBinBuffer(data.readBinBuffer(pos));
	m_Timestamp = data.readUint<uint64_t>(pos);
	m_lastSentBySource = CSHA256::fromBinBuffer(data.readBinBuffer(pos));
	m_lastAcceptedBySource = CSHA256::fromBinBuffer(data.readBinBuffer(pos));
	setSerializedBody(data.readBinBuffer(pos));

	if(getSignedBody() != data)
		throw CSerializationError(
			"CMessage::setSignedBody(const CBinBuffer &): input data does not match reconstructed object");
}

