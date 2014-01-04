/*
    finroutingthread.h
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

#ifndef FINROUTINGTHREAD_H
#define FINROUTINGTHREAD_H

#include <list>

//#include "routetable.h"
#include "sha256.h"
#include "ripemd160.h"
#include "binbuffer.h"
#include "paylink.h"

#include "cthread.h"

class CAmiko;

class CFinRoutingThread : public CThread
{
public:
	//TODO: spec
	CFinRoutingThread(CAmiko *amiko);

	//TODO: spec
	~CFinRoutingThread();

	void threadFunc();


private:

	//TODO: spec
	//void initializeRoutingTable();

	//TODO: spec
	void processIncomingMessages();

	//TODO: spec
	void searchForNewPayLinks();

	//TODO: spec
	void addAndProcessPayLink(const CPayLink &link);

	//TODO: spec
	//void processRoutingChanges();

	//TODO: spec
	//void sendRoutingChanges();

	CAmiko *m_Amiko;
	//CRouteTable m_RouteTable;

	class CActiveTransaction
	{
	public:
		//Interface IDs are the local public keys of finlinks
		//Exception for payer/payee: inbound interface is commit hash
		//TODO: how to deal with being both payer and payee???
		//Exception for meeting point: outbound interface is empty
		CBinBuffer m_inboundInterface;
		CBinBuffer m_currentOutboundInterface;
		std::list<CBinBuffer> m_remainingOutboundInterfaces;

		//See CTransaction for the meaning of these
		CSHA256 m_commitToken, m_commitHash;
		CRIPEMD160 m_meetingPoint;

		//TODO: something about the transaction state
	};
	std::list<CActiveTransaction> m_activeTransactions;
};

#include "amiko.h"

#endif

