/*
    amiko.cpp
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

#include "amiko.h"


CAmiko::CAmiko(const CAmikoSettings &settings) :
	m_Settings(settings),
	m_ListenerThread(this, m_Settings.m_Value.m_portNumber)
{
}


CAmiko::~CAmiko()
{
	CMutexLocker lock(m_ComLinks);
	for(std::list<CComLink *>::iterator i=m_ComLinks.m_Value.begin();
		i != m_ComLinks.m_Value.end(); i++)
	{
		(*i)->setReceiver(NULL);
		(*i)->stop();
		delete (*i);
	}
}


void CAmiko::start()
{
	m_ListenerThread.start();
}


void CAmiko::stop()
{
	m_ListenerThread.stop();
}


