/*
    finlink.h
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

#ifndef FINLINK_H
#define FINLINK_H

#include <list>
#include <queue>

#include "amikosettings.h"
#include "key.h"
#include "transaction.h"
#include "messages.h"
#include "cstring.h"
#include "exception.h"
//#include "routetable.h"

#include "cominterface.h"

/*
A FinLink object maintains the financial state of a link. It is usually
paired with a ComLink object, which performs communication with the peer.
*/
class CFinLink : public CComInterface
{
public:
	SIMPLEEXCEPTIONCLASS(CLoadError)
	SIMPLEEXCEPTIONCLASS(CSaveError)
	SIMPLEEXCEPTIONCLASS(CNotCompletedError)

	/*
	filename:
	TODO

	Constructed object:
	TODO

	Exceptions:
	CLoadError
	CSaveError
	*/
	CFinLink(const CString &filename);

	/*
	filename:
	TODO

	config:
	TODO

	Constructed object:
	TODO

	Exceptions:
	CSaveError
	*/
	CFinLink(const CString &filename, const CLinkConfig &config);

	~CFinLink();

	void sendMessage(const CBinBuffer &message);

	/*
	config:
	TODO
	*/
	void updateLinkConfig(const CLinkConfig &config);

	/*
	Return value:
	Reference to properly formed CLinkConfig object
	Reference lifetime: equal to lifetime of this object
	*/
	inline const CLinkConfig &getLinkConfig() const
		{return m_linkConfig;}

	/*
	Return value:
	Reference to properly formed CKey object
	Reference lifetime: equal to lifetime of this object
	*/
	inline const CKey &getRemoteKey() const
		{return m_linkConfig.m_remoteKey;}
	inline const CKey &getLocalKey() const
		{return m_linkConfig.m_localKey;}

	//TODO: spec
	inline bool isCompleted() const
		{return m_linkConfig.m_completed;}

	//TODO: spec
	void processInbox();

	//TODO: spec
	//note: changes msg
	//CNotCompletedError
	void sendOutboundMessage(CMessage &msg);

	//CCriticalSection<CRouteTable> m_RouteTable;

protected:
	/*
	Exceptions:
	CLoadError
	*/
	void load();

	/*
	Exceptions:
	CSaveError
	*/
	void save();

	//TODO: spec
	CBinBuffer serialize();

	/*
	Exceptions:
	CLoadError
	*/
	void deserialize(const CBinBuffer &data);

	//void processRouteInfoMessage(const CRouteInfoMessage *msg);

	//TODO: spec
	void sendNackMessage(
		CNackMessage::eReason reasonCode,
		const CString &reason,
		const CSHA256 &rejectedMessage,
		const CString &reasonInLog="");

	//TODO: spec
	//CNotCompletedError
	void setOutboundMessageFields(CMessage &msg);

	//Mutex is there to protect file loading and saving
	CCriticalSection<CString> m_Filename;

	CLinkConfig m_linkConfig;

	//To-be-checked-and-processed:
	CCriticalSection< std::queue<CBinBuffer> > m_Inbox;

	std::list<CBinBuffer> m_myMessages, m_yourMessages;

	std::list<CTransaction> m_InboundTransactions, m_OutboundTransactions;
};

#endif

