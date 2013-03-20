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

#include <errno.h>

#include <openssl/crypto.h>

#include "timer.h"

#include "cthread.h"


CThread::CThread()
{
	m_terminate = false;
	m_tid = 0;
	m_isRunning = false;
}


CThread::~CThread()
{
	stop();
}


void CThread::start()
{
	if(m_isRunning)
		throw CAlreadyRunningError("Attempt to start a thread that is already running");

	m_isRunning = true;
	m_terminate = false;
	if(pthread_create(&m_tid, NULL, &CThread::run, (void *) this) != 0)
	{
		m_isRunning = false;
		throw CStartFailedError("Failed to start the thread");
	}
}


void CThread::stop()
{
	/*
	Since m_tid is private and is only set to zero when the thread is stopped,
	it is safe to do nothing if m_tid is already zero.

	In fact, when m_tid is zero, it is necessary to do nothing, since there is
	no thread with that ID.
	*/
	if(m_tid == 0) return;

	m_terminate = true;
	if(pthread_join(m_tid, NULL) != 0)
		throw CStopFailedError("Failed to stop the thread");
	m_tid = 0;
	m_isRunning = false;
}


bool CThread::isRunning()
{
	return m_isRunning;
}


void *CThread::run(void *arg)
{
	CThread *parent = (CThread *)arg;
	parent->threadFunc();
	parent->m_isRunning = false;
	return NULL;
}


CMutex::CMutex()
{
	if(pthread_mutex_init(&m_mutex, NULL) != 0)
		throw CError("Mutex construction failed");
}


CMutex::~CMutex()
{
	//TODO: how to deal failure here? We cannot throw exceptions in a destructor.
	pthread_mutex_destroy(&m_mutex);
}


void CMutex::lock()
{
	if(pthread_mutex_lock(&m_mutex) != 0)
		throw CError("Mutex locking failed");
}


void CMutex::unlock()
{
	if(pthread_mutex_unlock(&m_mutex) != 0)
		throw CError("Mutex unlocking failed");
}


CSemaphore::CSemaphore()
{
	if(sem_init(&m_semaphore, 0, 0) != 0)
		throw CError("Semaphore construction failed");
}


CSemaphore::~CSemaphore()
{
	//TODO: how to deal failure here? We cannot throw exceptions in a destructor.
	sem_destroy(&m_semaphore);
}


void CSemaphore::wait()
{
	if(sem_wait(&m_semaphore) != 0)
		throw CError("Semaphore waiting failed");
}


void CSemaphore::waitWithTimeout(unsigned int milliseconds)
{
	uint64_t endTime = CTimer::getTime() + milliseconds;
	timespec ts;
	ts.tv_sec = endTime / 1000;
	ts.tv_nsec = (endTime % 1000) * 1000000;

	if(sem_timedwait(&m_semaphore, &ts) != 0)
	{
		if(errno == ETIMEDOUT)
			{throw CTimeoutError("waitWithTimeout timeout occurred");}
		else
			{throw CError("waitWithTimeout: semaphore waiting failed");}
	}
}


void CSemaphore::post()
{
	if(sem_post(&m_semaphore) != 0)
		throw CError("Semaphore posting failed");
}


int CSemaphore::getValue()
{
	int ret = 0;
	if(sem_getvalue(&m_semaphore, &ret) != 0)
		throw CError("Semaphore getValue failed");
	return ret;
}


CMutex **COpenSSLMutexes::m_mutexes = NULL;

COpenSSLMutexes::COpenSSLMutexes()
{
	if(m_mutexes != NULL)
		throw CException(
			"Programming error: there are multiple instances of COpenSSLMutexes");

	m_mutexes = (CMutex **)OPENSSL_malloc(CRYPTO_num_locks() * sizeof(CMutex *));
	for(int i = 0; i < CRYPTO_num_locks(); i++)
		m_mutexes[i] = new CMutex();
	CRYPTO_set_locking_callback(lockingCallback);
}


COpenSSLMutexes::~COpenSSLMutexes()
{
	CRYPTO_set_locking_callback(NULL);
	for(int i = 0; i < CRYPTO_num_locks(); i++)
		delete m_mutexes[i];
	OPENSSL_free(m_mutexes);
	m_mutexes = NULL;
}


void COpenSSLMutexes::lockingCallback(int mode, int i, const char* file, int line)
{
	if (mode & CRYPTO_LOCK)
		{m_mutexes[i]->lock();}
	else
		{m_mutexes[i]->unlock();}
}

