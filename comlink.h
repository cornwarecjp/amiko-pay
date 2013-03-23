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

#include "exception.h"
#include "cstring.h"
#include "uriparser.h"
#include "key.h"
#include "tcpconnection.h"

#include "cthread.h"
#include "cominterface.h"

//TODO: choose a friendly default port
#define AMIKO_DEFAULT_PORT "12345"

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

	Constructed object:
	Connected link object in pending state

	Exceptions:
	CTCPConnection::CConnectException
	*/
	CComLink(const CURI &uri);

	/*
	listener:
	Reference to properly formed CTCPListener object (NOT CHECKED)
	Reference lifetime: at least until the end of this function
	TODO: lifetime at least as long as lifetime of this object??

	Constructed object:
	Connected link object in pending state

	Exceptions:
	CTCPConnection::CConnectException
	*/
	CComLink(const CTCPListener &listener);

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
	virtual const CKey &getRemoteAddress() const;
	virtual const CKey &getLocalAddress() const;


protected:
	/*
	This object:
	Uninitialized (NOT CHECKED)

	Exceptions:
	TODO
	*/
	virtual void initialize()=0;

	/*
	message:
	Reference to properly formed CBinBuffer object (NOT CHECKED)
	Reference lifetime: at least until the end of this function

	Exceptions:
	TODO
	*/
	virtual void sendMessageDirect(const CBinBuffer &message)=0;

	/*
	Return value:
	CBinBuffer object

	Exceptions:
	CNoDataAvailable
	TODO
	*/
	virtual CBinBuffer receiveMessageDirect()=0;


	CKey m_RemoteAddress, m_LocalAddress;
	CTCPConnection m_Connection;
	CString m_URI;
	bool m_isServerSide;
	uint32_t m_ProtocolVersion;

private:

	CCriticalSection< std::queue<CBinBuffer> > m_SendQueue;
	CSemaphore m_HasNewSendData;

	CCriticalSection<eState> m_State;
};

#endif


