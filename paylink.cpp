/*
    paylink.cpp
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

#include "amikosettings.h"

#include "paylink.h"


#define AMIKOPAY_MIN_PROTOCOL_VERSION 1
#define AMIKOPAY_MAX_PROTOCOL_VERSION 1

//With 32-bit protocol version numbers, we'll never exceed this:
#define MAX_NEGOTIATION_STRING_LENGTH 32


CPayLink::CPayLink(const CTCPListener &listener) :
	m_connection(listener),
	m_transactionID(""),
	m_isReceiverSide(true)
{
}


CPayLink::CPayLink(const CURI &paymentURL) :
	m_connection(paymentURL.getHost(), paymentURL.getPort(AMIKO_DEFAULT_PAYMENT_PORT)),
	m_transactionID(paymentURL.getPath()),
	m_isReceiverSide(false)
{
}


CPayLink::~CPayLink()
{
}


void CPayLink::threadFunc()
{
	negotiateVersion();

	//TODO
	//Fall-through: for now, the thread stops immediately
}


void CPayLink::initialHandshake()
{
	negotiateVersion();
}


void CPayLink::negotiateVersion()
{
	if(m_isReceiverSide)
	{
		uint32_t minVersion, maxVersion;
		receiveNegotiationString(minVersion, maxVersion);

		if(minVersion > maxVersion)
			throw CProtocolError("Protocol negotiation gave weird result");

		//Version matching
		minVersion = std::max<uint32_t>(minVersion, AMIKOPAY_MIN_PROTOCOL_VERSION);
		maxVersion = std::min<uint32_t>(maxVersion, AMIKOPAY_MAX_PROTOCOL_VERSION);

		if(minVersion > maxVersion)
		{
			//No matching version found
			//Inform other side
			sendNegotiationString(minVersion, maxVersion);
			throw CVersionNegotiationFailure("No matching protocol version");
		}

		//Choose the highest version supported by both parties
		m_protocolVersion = maxVersion;
		sendNegotiationString(m_protocolVersion, m_protocolVersion);
	}
	else
	{
		sendNegotiationString(AMIKOPAY_MIN_PROTOCOL_VERSION, AMIKOPAY_MAX_PROTOCOL_VERSION);

		uint32_t minVersion, maxVersion;
		receiveNegotiationString(minVersion, maxVersion);

		if(minVersion < AMIKOPAY_MIN_PROTOCOL_VERSION || maxVersion > AMIKOPAY_MAX_PROTOCOL_VERSION)
			throw CProtocolError("Peer returned illegal protocol negotiation result");

		if(minVersion < maxVersion)
			throw CProtocolError("Protocol negotiation gave weird result");

		if(minVersion > maxVersion)
			throw CVersionNegotiationFailure("No matching protocol version");

		m_protocolVersion = minVersion;
	}
}


void CPayLink::sendNegotiationString(uint32_t minVersion, uint32_t maxVersion)
{
	m_connection.send(CBinBuffer(
		CString::format(
			"AMIKOPAY/%d/%d\n", MAX_NEGOTIATION_STRING_LENGTH,
			minVersion, maxVersion
			)
		));
}


void CPayLink::receiveNegotiationString(uint32_t &minVersion, uint32_t &maxVersion)
{
	//TODO: more efficient than one-byte-at-a-time

	CString receivedString;
	CBinBuffer buf(1);
	bool finished = false;

	for(unsigned int i=0; i < MAX_NEGOTIATION_STRING_LENGTH; i++)
	{
		m_connection.receive(buf, 1000); //1 s timeout (TODO)
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


