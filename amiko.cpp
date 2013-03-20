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


CAmiko::CAmiko()
{
}

CAmiko::~CAmiko()
{
	CMutexLocker lock(m_ComLinks);
	for(size_t i=0; i < m_ComLinks.m_Value.size(); i++)
	{
		m_ComLinks.m_Value[i]->setReceiver(NULL);
		m_ComLinks.m_Value[i]->stop();
		delete m_ComLinks.m_Value[i];
	}
}

