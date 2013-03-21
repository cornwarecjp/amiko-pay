/*
    messages.h
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

#ifndef MESSAGES_H
#define MESSAGES_H

#include <stdint.h>
#include <vector>

#include "message.h"


/*
Greeting message sent during initialization.
It informs the other party to which link the connection applies (m_yourAddress),
It gives the other party the public key to be used for signing/encryption
(m_myPublicKey),
and it gives the preferred URL for connecting back (m_myPreferredURL).
*/
class CHelloMessage : public CMessage
{
public:
	virtual ~CHelloMessage();

	eTypeID getTypeID() const
		{return eHello;}

	CBinBuffer getSerializedBody() const;
	void setSerializedBody(const CBinBuffer &data);

	CBinBuffer m_myPublicKey;
	CString m_myPreferredURL;
	CString m_yourAddress;
};


class CAckMessage : public CMessage
{
public:
	virtual ~CAckMessage();

	eTypeID getTypeID() const
		{return eAck;}

	CBinBuffer getSerializedBody() const;
	void setSerializedBody(const CBinBuffer &data);

	//No contents here:
	//The purpose of this message is purely to
	//update m_lastAcceptedBySource
};


class CNackMessage : public CMessage
{
public:

	enum eReason
	{
	//Amiko link protocol version 1
	eNonstandardReason=0,
	eBadSignature=1,
	eWrongBalance=2
	};


	virtual ~CNackMessage();

	eTypeID getTypeID() const
		{return eNack;}

	CBinBuffer getSerializedBody() const;
	void setSerializedBody(const CBinBuffer &data);

	CSHA256 m_rejectedBySource; //hash of message rejected by source
	eReason m_reasonCode;       //machine-readable reason code
	CString m_reason;           //reason why the message was rejected
};


class CFinStateMessage : public CMessage
{
public:
	virtual ~CFinStateMessage();

	eTypeID getTypeID() const
		{return eFinState;}

	CBinBuffer getSerializedBody() const;
	void setSerializedBody(const CBinBuffer &data);

	int64_t m_myBalance, m_yourBalance;
	std::vector<CSHA256> m_pendingTransactions;
	std::vector<CSHA256> m_myPendingDeposits;
	std::vector<CSHA256> m_yourPendingDeposits;
};

#endif


