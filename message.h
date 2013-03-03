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

class CMessage
{
public:
	SIMPLEEXCEPTIONCLASS(CSerializationError)

	enum eTypeID
	{
	//Amiko link protocol version 1
	eMyPublicKey=0
	};

	static CMessage *constructMessage(const CBinBuffer &data, eTypeID ID);

	virtual eTypeID getTypeID() const=0;

	CBinBuffer serialize() const;
	void deserialize(const CBinBuffer &data);

	virtual CBinBuffer getSerializedBody() const = 0;
	virtual void setSerializedBody(const CBinBuffer &data) = 0;

private:

	CKey m_Source, m_Destination;

	//TODO: make this hashes
	CBinBuffer m_lastSentByMe;
	CBinBuffer m_lastAcceptedByMe;

	uint64_t m_Timestamp;
};

#endif

