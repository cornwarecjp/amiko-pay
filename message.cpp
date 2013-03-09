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


CMessage::CMessage() :
	m_lastSentByMe(CBinBuffer()),
	m_lastAcceptedByMe(CBinBuffer())
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
	case eMyPublicKey:
		ret = new CMyPublicKeyMessage;
		break;
	default:
		throw CSerializationError("Invalid message type ID");
	}

	ret->deserialize(data);
	return ret;
}


CBinBuffer CMessage::serialize() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer signedBody = getSignedBody();

	//TODO: add source and destination pubkeys
	CBinBuffer ret;
	ret.appendBinBuffer(signedBody);
	ret.appendBinBuffer(m_Signature);

	return ret;
}


void CMessage::deserialize(const CBinBuffer &data)
{
	//TODO: add source and destination pubkeys
	size_t pos = 0;
	CBinBuffer signedBody = data.readBinBuffer(pos);
	m_Signature = data.readBinBuffer(pos);

	pos = 0;
	uint32_t ID = signedBody.readUint<uint32_t>(pos);
	m_Timestamp = signedBody.readUint<uint64_t>(pos);
	m_lastSentByMe = CSHA256::fromBinBuffer(signedBody.readBinBuffer(pos));
	m_lastAcceptedByMe = CSHA256::fromBinBuffer(signedBody.readBinBuffer(pos));
	setSerializedBody(signedBody.readBinBuffer(pos));

	//verify ID:
	if(ID != getTypeID())
		throw CSerializationError(CString::format(
			"CMessage::deserialize(const CBinBuffer &): ID in message (%d) does not match ID of message class (%d)",
			256, ID, getTypeID()));

	//TODO: verify signature
	//TODO: sanity check on timestamp
	//TODO: check hashes of previous messages
}


void CMessage::sign()
{
	m_Signature = m_Source.sign(CSHA256(getSignedBody()));
}


bool CMessage::verifySignature() const
{
	return m_Source.verify(CSHA256(getSignedBody()), m_Signature);
}


CBinBuffer CMessage::getSignedBody() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer signedBody;
	signedBody.appendUint<uint32_t>(getTypeID());
	signedBody.appendUint<uint64_t>(m_Timestamp);
	signedBody.appendBinBuffer(m_lastSentByMe.toBinBuffer());
	signedBody.appendBinBuffer(m_lastAcceptedByMe.toBinBuffer());
	signedBody.appendBinBuffer(getSerializedBody());
	return signedBody;
}

