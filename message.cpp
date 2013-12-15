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

	try
	{
		size_t pos = 4;
		uint32_t ID = data.readUint<uint32_t>(pos);

		CMessage *ret = NULL;

		switch(ID)
		{
		case eHello:
			ret = new CHelloMessage;
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
		case eRouteInfo:
		//	ret = new CRouteInfoMessage;
		//	break;
		default:
			throw CSerializationError("Invalid message type ID");
		}

		//TODO: in case of any exception here, delete the object to prevent a memory leak
		ret->deserialize(data);

		return ret;
	}
	catch(CBinBuffer::CReadError &e)
	{
		throw CSerializationError(
			CString("Deserialization error: %s") +
			e.what()
			);
	}

	//Should never be reached (see above code)
	return NULL;
}


CBinBuffer CMessage::serialize() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer ret;
	ret.appendBinBuffer(getSignedBody());
	ret.appendRawBinBuffer(m_signature);

	return ret;
}


void CMessage::deserialize(const CBinBuffer &data)
{
	size_t pos = 0;
	setSignedBody(data.readBinBuffer(pos));
	m_signature = data.readRawBinBuffer(pos, data.size()-pos);

	//TODO: verify signature
	//TODO: sanity check on timestamp
	//TODO: check hashes of previous messages
}


void CMessage::sign(const CKey &key)
{
	//TODO: check whether m_Source corresponds with key
	//maybe set m_Source??
	m_signature = key.sign(CSHA256(getSignedBody()));
}


bool CMessage::verifySignature(const CKey &key) const
{
	//TODO: check whether m_Source corresponds with key
	return key.verify(CSHA256(getSignedBody()), m_signature);
}


CBinBuffer CMessage::getSignedBody() const
{
	//TODO: assert that everything fits within specified integer sizes

	CBinBuffer ret;
	ret.appendUint<uint32_t>(getTypeID());
	ret.appendRawBinBuffer(m_source.toBinBuffer());
	ret.appendRawBinBuffer(m_destination.toBinBuffer());
	ret.appendUint<uint64_t>(m_timestamp);
	ret.appendRawBinBuffer(m_previousMessage.toBinBuffer());
	ret.appendRawBinBuffer(getSerializedBody());
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

	m_source = CRIPEMD160::fromBinBuffer(
		data.readRawBinBuffer(pos, CRIPEMD160::getSize()));
	m_destination = CRIPEMD160::fromBinBuffer(
		data.readRawBinBuffer(pos, CRIPEMD160::getSize()));
	m_timestamp = data.readUint<uint64_t>(pos);
	m_previousMessage = CSHA256::fromBinBuffer(
		data.readRawBinBuffer(pos, CSHA256::getSize()));
	setSerializedBody(data.readRawBinBuffer(pos, data.size()-pos));

	if(getSignedBody() != data)
		throw CSerializationError(
			"CMessage::setSignedBody(const CBinBuffer &): input data does not match reconstructed object");
}

