/*
    paylink.cpp
    Copyright (C) 2013-2014 by CJP

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
#include "log.h"

#include "paylink.h"


#define AMIKOPAY_MIN_PROTOCOL_VERSION 1
#define AMIKOPAY_MAX_PROTOCOL_VERSION 1

//With 32-bit protocol version numbers, we'll never exceed this:
#define MAX_NEGOTIATION_STRING_LENGTH 32


CPayLink::CPayLink(const CTCPListener &listener,
	const std::map<CString, CTransaction> &transactions) :

	m_connection(listener),
	m_transactionID(""),
	m_isReceiverSide(true),
	m_transactions(transactions),
	m_state(eInitial)
{
}


CPayLink::CPayLink(const CURI &paymentURL) :
	m_connection(paymentURL.getHost(), paymentURL.getPort(AMIKO_DEFAULT_PAYMENT_PORT)),
	m_transactionID(paymentURL.getPath()),
	m_isReceiverSide(false),
	m_state(eInitial)
{
}


CPayLink::~CPayLink()
{
}


void CPayLink::threadFunc()
{
	//Catch all exceptions and handle them
	try
	{
		if(m_isReceiverSide)
			{threadFuncReceiverSide();}
		else
			{threadFuncSenderSide();}
	}
	catch(CTCPConnection::CClosedException &e)
	{
		log("CPayLink::threadFunc(): Payment connection closed by peer\n");
		setState(eCanceled);
	}
	catch(CException &e)
	{
		log(CString::format(
			"CPayLink::threadFunc(): Caught application exception: %s\n",
			256, e.what()));
		setState(eCanceled);
	}
	catch(std::exception &e)
	{
		log(CString::format(
			"CPayLink::threadFunc(): Caught standard library exception: %s\n",
			256, e.what()));
		setState(eCanceled);
	}
}


void CPayLink::threadFuncReceiverSide()
{
	initialHandshake();
	receiveOK(300000); //300 s = 5 minutes
	setState(eOperational);

	//TODO: how do we know it when routing fails?
	m_receivedHaveRoute.wait();
	log("Receiver-side paylink has route to meeting point\n");

	sendMessage(CString("haveRoute"));
	expectMessage("haveRoute", 10000); //10 s

	//TODO
	//Fall-through: for now, the thread stops immediately
	log("Receiver-side paylink thread ends\n");
}


void CPayLink::threadFuncSenderSide()
{
	//Note: the sender side starts its own thread later in the process
	//than the receiver side.

	//TODO: how do we know it when routing fails?
	m_receivedHaveRoute.wait();
	log("Sender-side paylink has route to meeting point\n");

	sendMessage(CString("haveRoute"));
	expectMessage("haveRoute", 10000); //10 s

	//TODO
	//Fall-through: for now, the thread stops immediately
	log("Sender-side paylink thread ends\n");
}


void CPayLink::initialHandshake()
{
	negotiateVersion();
	exchangeTransactionID();
	exchangeTransactionData();
}


void CPayLink::sendPayerAgrees(bool agree)
{
	if(agree)
	{
		sendOK();
		setState(eOperational);
	}
	else
		{sendAndThrowError("Payment canceled by payer");}
}


void CPayLink::sendAndThrowError(const CString &message)
{
	setState(eCanceled);
	sendMessage(message);
	throw CProtocolError(message);
}


void CPayLink::expectMessage(
	const CString &expectedText, int timeoutValue)
{
	CString message = receiveMessage(timeoutValue).toString();

	//TODO: input validation on message

	CString peer = m_isReceiverSide ? "payer" : "payee";

	if(message != expectedText)
		throw CProtocolError(
			CString("Received error from ") + peer + ": " + message);
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


void CPayLink::exchangeTransactionID()
{
	if(m_isReceiverSide)
	{
		m_transactionID = receiveMessage().toString();

		std::map<CString, CTransaction>::const_iterator iter =
			m_transactions.find(m_transactionID);
		if(iter == m_transactions.end())
			sendAndThrowError("Transaction not found");

		m_transaction = iter->second;

		log(CString("Got incoming connection for payment ") + iter->first + "\n");
		sendOK();
	}
	else
	{
		sendMessage(m_transactionID);
		receiveOK();
	}
}


void CPayLink::exchangeTransactionData()
{
	if(m_isReceiverSide)
	{
		CBinBuffer buffer;
		buffer.appendRawBinBuffer(m_transaction.m_commitHash.toBinBuffer());
		buffer.appendUint<uint64_t>(m_transaction.m_amount);
		buffer.appendBinBuffer(m_transaction.m_receipt);

		//For now, only suggest one meeting point:
		buffer.appendUint<uint32_t>(1); //Number of meeting points
		buffer.appendRawBinBuffer(m_transaction.m_meetingPoint.toBinBuffer());

		sendMessage(buffer);


		receiveOK();
		//TODO: Maybe check whether the received meeting point is one of the
		//sent meeting points. This is probably not necessary though.
		m_transaction.m_meetingPoint = CRIPEMD160::fromBinBuffer(
			receiveMessage()
			);
	}
	else
	{
		CBinBuffer buffer = receiveMessage();
		size_t pos = 0;
		m_transaction.m_commitHash = CSHA256::fromBinBuffer(
			buffer.readRawBinBuffer(pos, CSHA256::getSize())
			);
		m_transaction.m_amount = buffer.readUint<uint64_t>(pos);
		m_transaction.m_receipt = buffer.readBinBuffer(pos).toString();

		//Check whether the characters in receipt are acceptable.
		//This check may be relaxed in the future, but it's important to
		//remain safe.
		CString acceptedSpecialChars = " \n\r\t,.:;()*/+-_=";
		for(size_t i=0; i < m_transaction.m_receipt.length(); i++)
		{
			char c = m_transaction.m_receipt[i];
			if(c>='A' && c<='Z') continue;
			if(c>='a' && c<='z') continue;
			if(c>='0' && c<='9') continue;
			if(acceptedSpecialChars.find(c) != acceptedSpecialChars.npos) continue;

			sendAndThrowError(CString::format(
				"Found a suspicious character in the transaction receipt "
				"(ASCII code %d)", 256, c
				));
		}

		uint32_t numMeetingPoints = buffer.readUint<uint32_t>(pos);
		if(numMeetingPoints < 1)
			sendAndThrowError("Payee must suggest at least one meeting point");

		//For now, always choose the first meeting point suggested by payee:
		m_transaction.m_meetingPoint = CRIPEMD160::fromBinBuffer(
			buffer.readRawBinBuffer(pos, CRIPEMD160::getSize())
			);


		sendOK();
		sendMessage(m_transaction.m_meetingPoint.toBinBuffer());
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


CBinBuffer CPayLink::receiveMessage(int timeoutValue)
{
	CBinBuffer sizebuffer(4);
	m_connection.receive(sizebuffer, timeoutValue);
	size_t pos = 0;
	uint32_t size = sizebuffer.readUint<uint32_t>(pos);

	//TODO: check whether size is unreasonably large
	CBinBuffer ret; ret.resize(size);
	m_connection.receive(ret, timeoutValue);

	return ret;
}


void CPayLink::sendMessage(const CBinBuffer &message) const
{
	CBinBuffer sizebuffer;
	sizebuffer.appendUint<uint32_t>(message.size());
	m_connection.send(sizebuffer);
	m_connection.send(message);
}

