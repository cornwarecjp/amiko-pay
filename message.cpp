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

	CBinBuffer signedBody;
	signedBody.appendUint<uint64_t>(m_Timestamp);
	signedBody.appendBinBuffer(m_lastSentByMe.asBinBuffer());
	signedBody.appendBinBuffer(m_lastAcceptedByMe.asBinBuffer());
	signedBody.appendUint<uint32_t>(getTypeID());
	signedBody.appendBinBuffer(getSerializedBody());

	CBinBuffer signature = m_Source.sign(CSHA256(signedBody));

	//TODO: add source and destination pubkeys
	CBinBuffer ret;
	ret.appendUint<uint32_t>(signedBody.size());
	ret.appendBinBuffer(signedBody);
	ret.appendUint<uint32_t>(signature.size());
	ret.appendBinBuffer(signature);

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
	CBinBuffer signature = data.readBinBuffer(pos, signatureSize);

	//TODO: verify signature
	//TODO: store signature (important for later evidence!!!)

	pos = 0;
	m_Timestamp = signedBody.readUint<uint64_t>(pos);
	CBinBuffer lastSentByMe = signedBody.readBinBuffer(pos, 256); //TODO
	CBinBuffer lastAcceptedByMe = signedBody.readBinBuffer(pos, 256); //TODO
	//TODO:
	//signedBody.appendUint<uint32_t>(getTypeID());
	//signedBody.appendBinBuffer(getSerializedBody());
	//setSerializedBody(data);
}

