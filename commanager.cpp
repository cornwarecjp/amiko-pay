/*
    commanager.cpp
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

#include "commanager.h"


CComManager::CComManager()
{
}


CComManager::~CComManager()
{
	//TODO: prevent deadlocks with the comlink threads themselves
	CMutexLocker lock(m_ComLinks);
	for(size_t i=0; i < m_ComLinks.m_Value.size(); i++)
		delete m_ComLinks.m_Value[i];
	m_ComLinks.m_Value.clear();
}


void CComManager::addComLink(CComLink *link)
{
	CMutexLocker lock(m_ComLinks);
	m_ComLinks.m_Value.push_back(link);
}


void CComManager::threadFunc()
{
	while(!m_terminate)
	{
		CTimer::sleep(10);
	}
}

