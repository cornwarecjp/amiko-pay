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

#include <stdint.h>

#include "message.h"

CMessage *CMessage::constructMessage(const CBinBuffer &data, eTypeID ID)
{
	//TODO
	return NULL;
}


CBinBuffer CMessage::serialize() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer signedBody = getSignedBody();

	//TODO: add source and destination pubkeys
	CBinBuffer ret;
	ret.appendUint<uint32_t>(signedBody.size());
	ret.appendBinBuffer(signedBody);
	ret.appendUint<uint32_t>(m_Signature.size());
	ret.appendBinBuffer(m_Signature);

	return ret;
}


void CMessage::deserialize(const CBinBuffer &data)
{
	//TODO: check whether sizes are not unreasonably large

	//TODO: add source and destination pubkeys
	size_t pos = 0;
	uint32_t signedBodySize = data.readUint<uint32_t>(pos);
	CBinBuffer signedBody = data.readBinBuffer(pos, signedBodySize);
	uint32_t signatureSize = data.readUint<uint32_t>(pos);
	m_Signature = data.readBinBuffer(pos, signatureSize);

	pos = 0;
	uint32_t ID = signedBody.readUint<uint32_t>(pos);
	m_Timestamp = signedBody.readUint<uint64_t>(pos);
	m_lastSentByMe = CSHA256::fromBinBuffer(signedBody.readBinBuffer(pos, 32));
	m_lastAcceptedByMe = CSHA256::fromBinBuffer(signedBody.readBinBuffer(pos, 32));
	setSerializedBody(signedBody.readBinBuffer(pos, signedBody.size()-pos));

	//verify ID:
	if(ID != getTypeID())
		throw CSerializationError("CMessage::deserialize(const CBinBuffer &): ID in message does not match ID of message class");

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

