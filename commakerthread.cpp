/*
    commakerthread.cpp
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

#include "timer.h"
#include "log.h"

#include "commakerthread.h"

CComMakerThread::CComMakerThread(CAmiko *amiko) :
	m_Amiko(amiko)
{
}


CComMakerThread::~CComMakerThread()
{
}


void CComMakerThread::threadFunc()
{
	unsigned int count = 0;
	while(!m_terminate)
	{
		if(count == 0)
			makeMissingComLinks_noExceptions();

		//every iteration takes 1 s
		CTimer::sleep(1000);

		//once every 60 iterations, we try again
		//TODO: randomize, to reduce collision risk
		count = (count+1) % 60;
	}
}


void CComMakerThread::makeMissingComLinks_noExceptions()
{
	try
	{
		m_Amiko->makeMissingComLinks();
	}
	catch(CException &e)
	{
		log(CString::format(
			"CComMakerThread: Caught application exception: %s\n",
			256, e.what()));
	}
	catch(std::exception &e)
	{
		log(CString::format(
			"CComMakerThread: Caught standard library exception: %s\n",
			256, e.what()));
	}
}


