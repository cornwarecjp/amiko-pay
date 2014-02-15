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

#include "exception.h"
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
	SIMPLEEXCEPTIONCLASS(CPaymentFailed)

	//TODO: spec
	CFinRoutingThread(CAmiko *amiko);

	//TODO: spec
	~CFinRoutingThread();

	void threadFunc();

	//TODO: spec
	void doPayment(CPayLink &link);

	CCriticalSection< std::list<CPayLink *> > m_PayLinks;

private:

	CAmiko *m_Amiko;
	//CRouteTable m_RouteTable;

	CCriticalSection< CPayLink * > m_OutgoingPayLink;
	CSemaphore m_OutgoingPaymentInProgress;


	class CActiveTransaction
	{
	public:
		//Interface IDs are the local public keys of finlinks
		//Exception for payer/payee: inbound interface is commit hash
		//If we are both payer and payee,
		//  there are two active transactions with opposite m_receiverSide
		//Exception for meeting point: outbound interface is empty
		CBinBuffer m_inboundInterface;
		CBinBuffer m_currentOutboundInterface;
		std::list<CBinBuffer> m_remainingOutboundInterfaces;

		//Amount in satoshi
		uint64_t m_amount;
		//true: inbound interface is towards receiver
		//false: inbound interface is towards payer
		bool m_receiverSide;

		//See CTransaction for the meaning of these
		CSHA256 m_commitToken, m_commitHash;
		CRIPEMD160 m_meetingPoint;

		//TODO: something about the transaction state
	};
	std::list<CActiveTransaction> m_activeTransactions;


	//TODO: spec
	//void initializeRoutingTable();

	//TODO: spec
	void processIncomingMessages();

	//TODO: spec
	void searchForNewPayLinks();

	//TODO: spec
	void addAndProcessPayLink(const CPayLink &link);

	//TODO: spec
	void matchWithOwnMeetingPoint(CActiveTransaction &t);

	//TODO: spec
	//void processRoutingChanges();

	//TODO: spec
	//void sendRoutingChanges();
};

#include "amiko.h"

#endif

