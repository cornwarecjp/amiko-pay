/*
    finroutingthread.h
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

#ifndef FINROUTINGTHREAD_H
#define FINROUTINGTHREAD_H

#include "routetable.h"

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
	void initializeRoutingTable();

	//TODO: spec
	void processIncomingMessages();

	//TODO: spec
	void processRoutingChanges();

	//TODO: spec
	void sendRoutingChanges();

	CAmiko *m_Amiko;
	CRouteTable m_RouteTable;
};

#include "amiko.h"

#endif

