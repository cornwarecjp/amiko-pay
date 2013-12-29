/*
    paylink.h
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

#ifndef PAYLINK_H
#define PAYLINK_H

#include <stdint.h>

#include <map>

#include "cthread.h"

#include "tcpconnection.h"
#include "transaction.h"
#include "exception.h"
#include "uriparser.h"

//1 second:
#define PAYLINK_DEFAULT_TIMEOUT 1000


/*
A PayLink object received payments from a remote payer.
It contains its own thread which manages sending and receiving of messages.
*/
class CPayLink : public CThread
{
public:
	SIMPLEEXCEPTIONCLASS(CProtocolError)
	SIMPLEEXCEPTIONCLASS(CVersionNegotiationFailure)

	/*
	listener:
	Reference to properly formed CTCPListener object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	TODO: lifetime at least as long as lifetime of this object??

	transactions:
	TODO

	Constructed object:
	TODO

	Exceptions:
	CTCPConnection::CConnectException
	CTCPConnection::CTimeoutException
	*/
	CPayLink(const CTCPListener &listener,
		const std::map<CString, CTransaction> &transactions);

	/*
	paymentURL:
	Reference to properly formed CURI object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	TODO

	Exceptions:
	CTCPConnection::CConnectException
	CURI::CNotFound
	CString::CFormatException
	*/
	CPayLink(const CURI &paymentURL);

	~CPayLink();

	//TODO: spec
	void initialHandshake();

	void sendOK() const;
	void sendAndThrowError(const CString &message) const;


	//Receiver-side specific:
	//TODO: spec
	void threadFunc();


	CTransaction m_transaction;

private:

	/*
	Exceptions:
	CProtocolError
	CVersionNegotiationFailure
	CTCPConnection::CSendException
	CTCPConnection::CReceiveException
	TODO: timeout exception
	*/
	void negotiateVersion();

	/*
	Exceptions:
	CTCPConnection::CSendException
	CTCPConnection::CReceiveException
	CTCPConnection::CTimeoutException
	CBinBuffer::CReadError
	CProtocolError
	*/
	void exchangeTransactionID();

	/*
	Exceptions:
	CTCPConnection::CSendException
	CTCPConnection::CReceiveException
	CTCPConnection::CTimeoutException
	CBinBuffer::CReadError
	CProtocolError
	*/
	void exchangeTransactionData();

	/*
	Exceptions:
	CTCPConnection::CSendException
	*/
	void sendNegotiationString(uint32_t minVersion, uint32_t maxVersion);

	/*
	minVersion:
	Reference to valid uint32_t (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	maxVersion:
	Reference to valid uint32_t (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Note: method writes values into minVersion and maxVersion.

	Exceptions:
	CTCPConnection::CReceiveException
	CProtocolError
	*/
	void receiveNegotiationString(uint32_t &minVersion, uint32_t &maxVersion);

	//TODO: spec
	void receiveOK(int timeoutValue=PAYLINK_DEFAULT_TIMEOUT);

	//TODO: spec
	CBinBuffer receiveMessage(int timeoutValue=PAYLINK_DEFAULT_TIMEOUT);
	void sendMessage(const CBinBuffer &message) const;

	CTCPConnection m_connection;
	CString m_transactionID;
	bool m_isReceiverSide;

	//Transactions to choose from (receiver side only) when a sender connects
	std::map<CString, CTransaction> m_transactions;

	uint32_t m_protocolVersion;
};

#endif

