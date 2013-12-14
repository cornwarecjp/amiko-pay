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
#include "bitcoinaddress.h"
#include "pointerowner.h"
#include "uriparser.h"

#include "comlink.h"

//With 32-bit protocol version numbers, we'll never exceed this:
#define MAX_NEGOTIATION_STRING_LENGTH 32

CComLink::CComLink(const CLinkConfig &config, const CAmikoSettings &settings) :
	m_URI(config.m_remoteURI),
	m_Connection(m_URI.getHost(), m_URI.getPort(AMIKO_DEFAULT_PORT)),
	m_Settings(settings),
	m_isServerSide(false),
	m_linkConfig(config),
	m_State(ePending)
{
}


CComLink::CComLink(const CTCPListener &listener, const CAmikoSettings &settings, const std::vector<CLinkConfig> &linkConfigs) :
	m_URI("dummy://localhost"),
	m_Connection(listener),
	m_Settings(settings),
	m_isServerSide(true),
	m_linkConfigs(linkConfigs),
	m_State(ePending)
{
}


CComLink::~CComLink()
{
	//stop the thread before members are deleted
	stop();
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
					deliverMessage(receiveMessageDirect());
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
	catch(CTCPConnection::CClosedException &e)
	{
		log(CString::format(
			"Connection closed by peer (local: %s)\n",
			1024,
			getBitcoinAddress(getLocalKey()).c_str()
			));
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

	try
	{
		{
			CMutexLocker lock(m_State);
			m_State.m_Value = eClosed;
		}

		log(CString::format(
			"Disconnected (local: %s)\n",
			1024,
			getBitcoinAddress(getLocalKey()).c_str()
			));
	}
	catch(CKey::CKeyError &e)
	{
		log("Disconnected (local: unknown)\n");
	}
	catch(CException &e)
	{
		log(CString::format(
			"CComLink::threadFunc(): Caught application exception after disconnect: %s\n",
			256, e.what()));
	}
	catch(std::exception &e)
	{
		log(CString::format(
			"CComLink::threadFunc(): Caught standard library exception after disconnect: %s\n",
			256, e.what()));
	}
}


void CComLink::initialize()
{
	negotiateVersion();
	exchangeHello();

	if(m_isServerSide)
	{
		log(CString::format(
			"Connected as server (local: %s remote: %s) with protocol version %d\n",
			1024,
			getBitcoinAddress(getLocalKey()).c_str(),
			getBitcoinAddress(getRemoteKey()).c_str(),
			m_ProtocolVersion));
	}
	else
	{
		log(CString::format(
			"Connected as client (local: %s remote: %s) with protocol version %d\n",
			1024,
			getBitcoinAddress(getLocalKey()).c_str(),
			getBitcoinAddress(getRemoteKey()).c_str(),
			m_ProtocolVersion));
	}
}


void CComLink::negotiateVersion()
{
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
		m_Connection.receive(buf, 1000); //1 s timeout (TODO)
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


void CComLink::exchangeHello()
{
	if(m_isServerSide)
	{
		//1 s timeout:
		CHelloMessage hello = receiveHello(1000);

		//TODO: send nack reply in all the below error cases

		if(hello.m_source != CRIPEMD160(CSHA256(hello.m_myPublicKey).toBinBuffer()))
			throw CProtocolError(
				"Source address and public key mismatch in received hello");

		//Initial setting of the remote key.
		//This is only to allow us to verify the signature of the hello message.
		//Final setting will happen further down this function.
		m_linkConfig.m_remoteKey.setPublicKey(hello.m_myPublicKey);

		if(!hello.verifySignature(m_linkConfig.m_remoteKey))
			throw CProtocolError(
				"Signature and public key mismatch in received hello");

		{
			CString address = hello.m_yourAddress;

			const CLinkConfig *match = NULL;
			for(size_t i=0; i < m_linkConfigs.size(); i++)
			{
				const CLinkConfig &link = m_linkConfigs[i];
				if(getBitcoinAddress(link.m_localKey) == address)
				{
					if(match != NULL)
						throw CLinkDoesNotExist(
							"Multiple links match address; can't choose");

					if(link.m_completed && hello.m_myPublicKey != link.m_remoteKey.getPublicKey())
						throw CProtocolError(
							"Public key in received hello does not match known public key of this link");

					match = &link;
				}
			}
			if(match == NULL)
				throw CLinkDoesNotExist("No matching link found for address");

			m_linkConfig = *match;
		}

		//Set remote key again after receiving a correct hello.
		//This is necessary, because the complete m_linkConfig was overwritten
		// by the matching algorithm.
		m_linkConfig.m_remoteKey.setPublicKey(hello.m_myPublicKey);
		//Also, the link is now completed:
		m_linkConfig.m_completed = true;

		//Set the remote URI to the one received from the peer
		m_linkConfig.m_remoteURI = hello.m_myPreferredURL;

		CHelloMessage helloReply;
		//TODO: remaining fields
		helloReply.m_source = CRIPEMD160(CSHA256(getLocalKey().getPublicKey()).toBinBuffer());
		helloReply.m_destination = CRIPEMD160(CSHA256(getRemoteKey().getPublicKey()).toBinBuffer());
		helloReply.m_myPublicKey = getLocalKey().getPublicKey();
		helloReply.m_myPreferredURL = m_Settings.getLocalURL(getLocalKey());
		helloReply.m_yourAddress = getBitcoinAddress(helloReply.m_destination);

		helloReply.sign(getLocalKey());
		sendMessageDirect(helloReply.serialize());

		//TODO: wait for ack/nack?
	}
	else
	{
		CHelloMessage hello;
		//TODO: remaining fields
		hello.m_source = CRIPEMD160(CSHA256(getLocalKey().getPublicKey()).toBinBuffer());
		hello.m_myPublicKey = getLocalKey().getPublicKey();
		hello.m_myPreferredURL = m_Settings.getLocalURL(getLocalKey());
		hello.m_yourAddress = m_URI.getPath();
		hello.sign(getLocalKey());
		sendMessageDirect(hello.serialize());

		//1 s timeout:
		CHelloMessage helloReply = receiveHello(1000);

		//TODO: send nack reply in all the below error cases

		if(getBitcoinAddress(helloReply.m_source) != hello.m_yourAddress)
			throw CProtocolError(
				"Mismatch between own hello and received hello source");

		if(helloReply.m_yourAddress != getBitcoinAddress(hello.m_source))
			throw CProtocolError(
				"Mismatch between own hello source and received hello");

		if(helloReply.m_destination != CRIPEMD160(CSHA256(getLocalKey().getPublicKey()).toBinBuffer()))
			throw CProtocolError(
				"Destination address and public key mismatch in received hello");

		if(helloReply.m_source != CRIPEMD160(CSHA256(helloReply.m_myPublicKey).toBinBuffer()))
			throw CProtocolError(
				"Source address and public key mismatch in received hello");

		if(m_linkConfig.m_completed && helloReply.m_myPublicKey != m_linkConfig.m_remoteKey.getPublicKey())
			throw CProtocolError(
				"Public key in received hello does not match known public key of this link");

		m_linkConfig.m_remoteKey.setPublicKey(helloReply.m_myPublicKey);
		m_linkConfig.m_completed = true;

		//Set the remote URI to the one received from the peer
		m_linkConfig.m_remoteURI = helloReply.m_myPreferredURL;

		if(!helloReply.verifySignature(getRemoteKey()))
			throw CProtocolError(
				"Signature and public key mismatch in received hello");

		//TODO: send ack?
	}
}


CHelloMessage CComLink::receiveHello(int timeoutValue)
{
	CMessage *msg = CMessage::constructMessage(receiveMessageDirect(timeoutValue));

	//This object takes care of deleting msg
	CPointerOwner<CMessage> msgOwner(msg);

	//TODO: deal with Nack reply (which is a valid reply)

	if(msg->getTypeID() != CMessage::eHello)
		throw CProtocolError("Expected hello message, got different message type");

	CHelloMessage ret = *((CHelloMessage *)msg);

	return ret;
}


void CComLink::sendMessageDirect(const CBinBuffer &message)
{
	//TODO: check whether everything fits in the integer data types
	CBinBuffer sizebuffer;
	sizebuffer.appendUint<uint32_t>(message.size());
	m_Connection.send(sizebuffer);
	m_Connection.send(message);
}


CBinBuffer CComLink::receiveMessageDirect(int timeoutValue)
{
	CBinBuffer sizebuffer(4);
	try
	{
		m_Connection.receive(sizebuffer, timeoutValue);
	}
	catch(CTCPConnection::CTimeoutException &e)
	{
		throw CNoDataAvailable("Timeout when reading size");
	}

	size_t pos = 0;
	uint32_t size = sizebuffer.readUint<uint32_t>(pos);

	//TODO: check whether size is unreasonably large
	CBinBuffer ret; ret.resize(size);

	try
	{
		m_Connection.receive(ret, timeoutValue);
	}
	catch(CTCPConnection::CTimeoutException &e)
	{
		/*
		If receiving the message body gives a timeout, then we have to put
		back the size data, so it can be re-read the next time this method is
		called.
		*/
		m_Connection.unreceive(sizebuffer);
		throw CNoDataAvailable("Timeout when reading message body");
	}

	return ret;
}


