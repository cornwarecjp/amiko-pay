/*
    comlink.cpp
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

#include "log.h"

#include "comlink.h"

//With 32-bit protocol version numbers, we'll never exceed this:
#define MAX_NEGOTIATION_STRING_LENGTH 32

CComLink::CComLink(const CURI &uri) :
	m_Connection(uri.getHost(), uri.getPort(AMIKO_DEFAULT_PORT)),
	m_URI(uri.getURI()),
	m_isServerSide(false),
	m_State(ePending)
{
}


CComLink::CComLink(const CTCPListener &listener) :
	m_Connection(listener),
	m_isServerSide(true),
	m_State(ePending)
{
}


CComLink::~CComLink()
{
}


void CComLink::sendMessage(const CBinBuffer &message)
{
	{
		CMutexLocker lock(m_SendQueue);
		m_SendQueue.m_Value.push(message);
	}
	m_HasNewSendData.post();
}


void CComLink::threadFunc()
{
	if(getState() != ePending)
	{
		log("CComLink::threadFunc(): initial state was not 'pending'; stopping thread\n");
		CMutexLocker lock(m_State);
		m_State.m_Value = eClosed;
		return;
	}

	//Catch all exceptions and handle them
	try
	{
		initialize();

		{
			CMutexLocker lock(m_State);
			m_State.m_Value = eOperational;
		}

		while(!m_terminate)
		{
			//Receive data:
			try
			{
				while(true)
					deliverReceivedMessage(receiveMessageDirect());
			}
			catch(CNoDataAvailable &e)
			{
				/*
				Ignore this exception:
				It is normal that this occurs, in fact it is our way to get out of
				the while loop in the try block
				*/
			}

			//Wait a while, unless there is data to be sent:
			m_HasNewSendData.waitWithTimeout(10); //10 ms

			//Send data:
			{
				CMutexLocker lock(m_SendQueue);
				while(!m_SendQueue.m_Value.empty())
				{
					sendMessageDirect(m_SendQueue.m_Value.front());
					m_SendQueue.m_Value.pop();
				}
			}
		}
	}
	catch(CException &e)
	{
		log(CString::format(
			"CComLink::threadFunc(): Caught application exception: %s\n",
			256, e.what()));
	}
	catch(std::exception &e)
	{
		log(CString::format(
			"CComLink::threadFunc(): Caught standard library exception: %s\n",
			256, e.what()));
	}

	{
		CMutexLocker lock(m_State);
		m_State.m_Value = eClosed;
	}
}


void CComLink::initialize()
{
	//TODO: catch exceptions
	if(m_isServerSide)
	{
		uint32_t minVersion, maxVersion;
		receiveNegotiationString(minVersion, maxVersion);

		if(minVersion > maxVersion)
			throw CProtocolError("Protocol negotiation gave weird result");

		//Version matching
		minVersion = std::max<uint32_t>(minVersion, AMIKO_MIN_PROTOCOL_VERSION);
		maxVersion = std::min<uint32_t>(maxVersion, AMIKO_MAX_PROTOCOL_VERSION);

		if(minVersion > maxVersion)
		{
			//No matching version found
			//Inform other side
			sendNegotiationString(minVersion, maxVersion);
			throw CVersionNegotiationFailure("No matching protocol version");
		}

		//Choose the highest version supported by both parties
		m_ProtocolVersion = maxVersion;
		sendNegotiationString(m_ProtocolVersion, m_ProtocolVersion);

		log(CString::format("Connected as server with protocol version %d\n",
			1024, m_ProtocolVersion));
	}
	else
	{
		sendNegotiationString(AMIKO_MIN_PROTOCOL_VERSION, AMIKO_MAX_PROTOCOL_VERSION);

		uint32_t minVersion, maxVersion;
		receiveNegotiationString(minVersion, maxVersion);

		if(minVersion < AMIKO_MIN_PROTOCOL_VERSION || maxVersion > AMIKO_MAX_PROTOCOL_VERSION)
			throw CProtocolError("Peer returned illegal protocol negotiation result");

		if(minVersion < maxVersion)
			throw CProtocolError("Protocol negotiation gave weird result");

		if(minVersion > maxVersion)
			throw CVersionNegotiationFailure("No matching protocol version");

		m_ProtocolVersion = minVersion;
		log(CString::format("Connected as client to %s with protocol version %d\n",
			1024, m_URI.c_str(), m_ProtocolVersion));
	}
}


void CComLink::sendNegotiationString(uint32_t minVersion, uint32_t maxVersion)
{
	m_Connection.send(CBinBuffer(
		CString::format(
			"AMIKOPAY/%d/%d\n", MAX_NEGOTIATION_STRING_LENGTH,
			minVersion, maxVersion
			)
		));
}


void CComLink::receiveNegotiationString(uint32_t &minVersion, uint32_t &maxVersion)
{
	//TODO: more efficient than one-byte-at-a-time

	CString receivedString;
	CBinBuffer buf(1);
	bool finished = false;

	for(unsigned int i=0; i < MAX_NEGOTIATION_STRING_LENGTH; i++)
	{
		m_Connection.receive(buf, -1); //TODO: set time-out on receiving
		unsigned char c = buf[0];

		if(c == '\n')
		{
			finished = true;
			break;
		}

		if(c < '/' || c > 'Z')
			throw CProtocolError(
				"Illegal character in protocol negotiation");

		receivedString += c;
	}

	if(!finished)
		throw CProtocolError(
			"Received protocol negotiation exceeds maximum length");

	size_t slash1 = receivedString.find('/', 0);
	if(slash1 == std::string::npos || slash1 >= receivedString.length()-1)
		throw CProtocolError(
			"Protocol negotiation syntax error: first slash not found");

	size_t slash2 = receivedString.find('/', slash1+1);
	if(slash2 == std::string::npos || slash2 >= receivedString.length()-1)
		throw CProtocolError(
			"Protocol negotiation syntax error: second slash not found");

	CString protocolName = receivedString.substr(0, slash1);
	CString minVerStr = receivedString.substr(slash1+1, slash2-slash1-1);
	CString maxVerStr = receivedString.substr(slash2+1);

	if(protocolName != "AMIKOPAY")
		throw CProtocolError(
			"Protocol name mismatch");

	if(minVerStr.length() > 9)
		throw CProtocolError(
			"Received minimum version number is close to or above integer overflow");

	if(maxVerStr.length() > 9)
		throw CProtocolError(
			"Received maximum version number is close to or above integer overflow");

	minVersion = minVerStr.parseAsDecimalInteger();
	maxVersion = maxVerStr.parseAsDecimalInteger();
}


