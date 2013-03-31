/*
    comlink.h
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

#ifndef COMLINK_H
#define COMLINK_H

#include <map>
#include <queue>
#include <stdint.h>

#include "exception.h"
#include "cstring.h"
#include "uriparser.h"
#include "key.h"
#include "tcpconnection.h"
#include "amikosettings.h"
#include "messages.h"

#include "cthread.h"
#include "cominterface.h"

#define AMIKO_MIN_PROTOCOL_VERSION 1
#define AMIKO_MAX_PROTOCOL_VERSION 1

/*
A ComLink object is a ComInterface that sends messages to and from a (remote)
peer process. It contains its own thread which manages sending and receiving
of messages.
A ComLink object can have the following states:
  pending
  operational
  closed
The initial state is 'pending'. An object can spontaneously perform the
following state transitions:
  pending->operational
  pending->closed
  operational->closed
Sending and receiving of messages only happens in the operational state.
As soon as the closed state is reached, the ComLink object should be deleted
to free up system resources (such as memory, the thread and the network socket).
*/
class CComLink : public CComInterface, public CThread
{
public:
	SIMPLEEXCEPTIONCLASS(CProtocolError)
	SIMPLEEXCEPTIONCLASS(CLinkDoesNotExist)
	SIMPLEEXCEPTIONCLASS(CVersionNegotiationFailure)
	SIMPLEEXCEPTIONCLASS(CNoDataAvailable)

	enum eState
	{
	ePending,
	eOperational,
	eClosed
	};


	/*
	uri:
	Reference to properly formed CURI object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	Contains a host and a path (NOT CHECKED)
	Path equals m_remoteURI.getPath() of one link in settings (CHECKED)

	settings:
	Reference to properly formed CAmikoSettings object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	Connected link object in pending state

	Exceptions:
	CURI::CNotFound
	CTCPConnection::CConnectException
	CLinkDoesNotExist
	*/
	CComLink(const CURI &uri, const CAmikoSettings &settings);

	/*
	listener:
	Reference to properly formed CTCPListener object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	TODO: lifetime at least as long as lifetime of this object??

	settings:
	Reference to properly formed CAmikoSettings object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Constructed object:
	Connected link object in pending state

	Exceptions:
	CTCPConnection::CConnectException
	CTCPConnection::CTimeoutException
	*/
	CComLink(const CTCPListener &listener, const CAmikoSettings &settings);

	virtual ~CComLink();

	/*
	message:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	TODO
	*/
	void sendMessage(const CBinBuffer &message);

	/*
	This object:
	comlink in pending state (CHECKED)
	*/
	void threadFunc();


	inline eState getState()
	{
		CMutexLocker lock(m_State);
		return m_State.m_Value;
	}

	/*
	Return value:
	Reference to properly formed CKey object
	Reference lifetime: equal to lifetime of this object
	*/
	inline const CKey &getRemoteKey() const
		{return m_RemoteKey;}
	inline const CKey &getLocalKey() const
		{return m_LocalKey;}


private:
	/*
	This object:
	Uninitialized (NOT CHECKED)

	Exceptions:
	CLinkDoesNotExist
	CTCPConnection::CSendException
	CTCPConnection::CReceiveException
	CProtocolError
	CVersionNegotiationFailure
	*/
	void initialize();

	/*
	message:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	CTCPConnection::CSendException
	*/
	void sendMessageDirect(const CBinBuffer &message);

	/*
	timeoutValue:
	timeoutValue >= 0: time-out in milliseconds
	timeoutValue < 0: infinite time-out

	Return value:
	CBinBuffer object

	Exceptions:
	CTCPConnection::CReceiveException
	CBinBuffer::CReadError
	CNoDataAvailable
	*/
	CBinBuffer receiveMessageDirect(int timeoutValue=0);

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
	CLinkDoesNotExist
	CProtocolError
	CNoDataAvailable
	CTCPConnection::CSendException
	CTCPConnection::CReceiveException
	*/
	void exchangeHello();

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

	/*
	timeoutValue:
	timeoutValue >= 0: time-out in milliseconds
	timeoutValue < 0: infinite time-out

	Exceptions:
	CTCPConnection::CReceiveException
	CBinBuffer::CReadError
	CNoDataAvailable
	CProtocolError
	*/
	CHelloMessage receiveHello(int timeoutValue);

	CKey m_RemoteKey, m_LocalKey;
	CTCPConnection m_Connection;
	CURI m_URI;
	CAmikoSettings m_Settings;
	bool m_isServerSide;
	uint32_t m_ProtocolVersion;

	CCriticalSection< std::queue<CBinBuffer> > m_SendQueue;
	CSemaphore m_HasNewSendData;

	CCriticalSection<eState> m_State;
};

#endif


