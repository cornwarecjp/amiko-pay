/*
    commanager.h
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

#ifndef COMMANAGER_H
#define COMMANAGER_H

#include <vector>

#include "tcplistener.h"
#include "comlink.h"

#include "cthread.h"

/*
Communication manager:
routes messages between senders and receivers of messages
*/
class CComManager : public CThread
{
public:
	/*
	Constructed object:
	Empty communication manager object

	Exceptions:
	none
	*/
	CComManager();

	~CComManager();


	void threadFunc();

private:

	std::vector<CComLink *> m_ComLinks;
};

#endif

