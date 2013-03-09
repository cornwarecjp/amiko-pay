/*
    message.h
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

#ifndef MESSAGE_H
#define MESSAGE_H

#include <stdint.h>

#include "exception.h"

#include "binbuffer.h"
#include "key.h"
#include "sha256.h"

class CMessage
{
public:
	SIMPLEEXCEPTIONCLASS(CSerializationError)

	enum eTypeID
	{
	//Amiko link protocol version 1
	eMyPublicKey=0
	};

	//TODO: specs for all these methods

	CMessage();
	virtual ~CMessage();

	static CMessage *constructMessage(const CBinBuffer &data);

	virtual eTypeID getTypeID() const=0;

	CBinBuffer serialize() const;
	void deserialize(const CBinBuffer &data);

	virtual CBinBuffer getSerializedBody() const = 0;
	virtual void setSerializedBody(const CBinBuffer &data) = 0;

	void sign(const CKey &key);
	bool verifySignature(const CKey &key) const;


	CSHA256 m_source;       //hash of source public key
	CSHA256 m_destination;  //hash of destination public key
	CBinBuffer m_Signature; //signature of source

	CSHA256 m_lastSentBySource;     //hash of previous message sent by source
	CSHA256 m_lastAcceptedBySource; //hash of last message accepted by source

	uint64_t m_Timestamp; //timestamp when this message was created by source


private:

	CBinBuffer getSignedBody() const;
	void setSignedBody(const CBinBuffer &data);
};

#endif

