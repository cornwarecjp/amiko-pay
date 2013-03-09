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


class CPublicKeyMessage : public CMessage
{
public:
	virtual ~CPublicKeyMessage();

	eTypeID getTypeID() const
		{return ePublicKey;}

	CBinBuffer getSerializedBody() const;
	void setSerializedBody(const CBinBuffer &data);

	CBinBuffer m_publicKey;
};


class CAckMessage : public CMessage
{
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
	virtual ~CNackMessage();

	eTypeID getTypeID() const
		{return eNack;}

	CBinBuffer getSerializedBody() const;
	void setSerializedBody(const CBinBuffer &data);

	CSHA256 m_rejectedBySource; //hash of message rejected by source
	uint32_t m_reasonCode;      //machine-readable reason code (to be standardized)
	CString m_reason;           //reason why the message was rejected
};


class CFinStateMessage : public CMessage
{
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


