/*
    cthread.cpp
    Copyright (C) 2002 by bones
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

#include "cthread.h"


CThread::CThread()
{
	m_terminate = false;
	m_tid = 0;
}


CThread::~CThread()
{
	stop();
}


void CThread::start()
{
	if (m_tid != 0)
		throw CAlreadyRunningError("Attempt to start a thread that is already running");

	m_terminate = false;
	if (pthread_create(&m_tid, NULL, &CThread::run, (void *) this) != 0)
		throw CStartFailedError("Failed to start the thread");
}


void CThread::stop()
{
	if (m_tid == 0)
		throw CNotRunningError("Attempt to stop a thread that is not running");

	m_terminate = true;
	pthread_join(m_tid, NULL);
	m_tid = 0;
}


bool CThread::isRunning()
{
	return m_tid != 0;
}


void *CThread::run(void *arg)
{
	CThread *parent = (CThread *)arg;
	parent->threadFunc();
	parent->m_tid = 0;
	return NULL;
}


CMutex::CMutex()
{
	if(!pthread_mutex_init(&m_mutex, NULL))
		throw CError("Mutex construction failed");
}


CMutex::~CMutex()
{
	//TODO: how to deal failure here? We cannot throw exceptions in a destructor.
	pthread_mutex_destroy(&m_mutex);
}


void CMutex::lock()
{
	if(!pthread_mutex_lock(&m_mutex))
		throw CError("Mutex locking failed");
}


void CMutex::unlock()
{
	if(!pthread_mutex_unlock(&m_mutex))
		throw CError("Mutex unlocking failed");
}

