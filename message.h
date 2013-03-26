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
#include "ripemd160.h"
#include "sha256.h"

class CMessage
{
public:
	SIMPLEEXCEPTIONCLASS(CSerializationError)

	enum eTypeID
	{
	//Amiko link protocol version 1
	eHello=0,
	eAck=1,
	eNack=2,
	eFinState=3
	};

	/*
	Constructed object:
	Uninitialized message object

	Exceptions:
	none
	*/
	CMessage();

	virtual ~CMessage();

	/*
	data:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Return value:
	Valid pointer
	Pointer ownership: passed to the caller
	Pointed memory contains CMessage-derived object
	Pointed object is deserialized from data

	Exceptions:
	CBinBuffer::CReadError
	CSerializationError
	*/
	static CMessage *constructMessage(const CBinBuffer &data);

	/*
	Return value:
	Valid eTypeID value

	Exceptions:
	none
	*/
	virtual eTypeID getTypeID() const=0;

	/*
	Return value:
	Serialized message

	Exceptions:
	CBinBuffer::CWriteError
	*/
	CBinBuffer serialize() const;

	/*
	data:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	Serialized message
	Type ID matches this object (CHECKED)

	Exceptions:
	CBinBuffer::CReadError
	*/
	void deserialize(const CBinBuffer &data);

	/*
	Return value:
	Serialized "payload" body data

	Exceptions:
	CBinBuffer::CWriteError
	*/
	virtual CBinBuffer getSerializedBody() const = 0;

	/*
	data:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	Serialized "payload" body data

	Exceptions:
	CBinBuffer::CReadError
	*/
	virtual void setSerializedBody(const CBinBuffer &data) = 0;

	/*
	key:
	Reference to properly formed CKey object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	Contains a private key (CHECKED/TODO)
	Corresponds with m_source (NOT CHECKED/TODO)

	Exceptions:
	CBinBuffer::CWriteError
	CKey::CKeyError
	*/
	void sign(const CKey &key);

	/*
	key:
	Reference to properly formed CKey object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	Contains a public key (CHECKED/TODO)
	Corresponds with m_source (NOT CHECKED/TODO)

	Return value:
	true if the signature is valid
	false if the signature is invalid

	Exceptions:
	CBinBuffer::CWriteError
	CKey::CKeyError
	*/
	bool verifySignature(const CKey &key) const;


	CRIPEMD160 m_source;       //ripemd160 of sha256 of source public key
	CRIPEMD160 m_destination;  //ripemd160 of sha256 of destination public key
	CBinBuffer m_signature; //signature of source

	CSHA256 m_lastSentBySource;     //hash of previous message sent by source
	CSHA256 m_lastAcceptedBySource; //hash of last message accepted by source

	uint64_t m_timestamp; //timestamp when this message was created by source


private:

	/*
	Return value:
	Serialized data which is signed

	Exceptions:
	CBinBuffer::CWriteError
	*/
	CBinBuffer getSignedBody() const;

	/*
	data:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	Serialized data which is signed

	Exceptions:
	CBinBuffer::CReadError
	*/
	void setSignedBody(const CBinBuffer &data);
};

#endif

