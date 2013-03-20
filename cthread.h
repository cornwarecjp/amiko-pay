/*
    cthread.h
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

#ifndef CTHREAD_H
#define CTHREAD_H

#include <pthread.h>
#include <semaphore.h>

#include "exception.h"


class CThread
{
public:
	SIMPLEEXCEPTIONCLASS(CAlreadyRunningError)
	SIMPLEEXCEPTIONCLASS(CStartFailedError)
	SIMPLEEXCEPTIONCLASS(CStopFailedError)

	/*
	Constructed object:
	non-running thread object

	Exceptions:
	none
	*/
	CThread();

	/*
	Note: waits until thread stops
	*/
	virtual ~CThread();

	/*
	this object:
	not running (CHECKED)

	Exceptions:
	CAlreadyRunningError
	CStartFailedError
	*/
	void start();

	/*
	Note: waits until thread stops

	Exceptions:
	CStopFailedError
	*/
	void stop();

	/*
	Return value:
	true if thread is running
	false if thread is not running

	Exceptions:
	none
	*/
	bool isRunning();

	/*
	Note: all exceptions are caught and handled inside this function.
	Note: regularly checks the value of m_terminate, and finishes if
	m_terminate is set to true.

	Exceptions:
	none
	*/
	virtual void threadFunc()=0;


protected:

	bool m_terminate; // threadFunc() has to return if this is set to true


private:

	/*
	arg:
	Valid pointer (NOT CHECKED)
	Pointed memory contains CThread instance (NOT CHECKED)
	Pointer ownership: remains with the caller
	Pointer lifetime: at least until the end of this function

	Return value:
	NULL
	*/
	static void *run(void *arg);

	pthread_t m_tid;
	bool m_isRunning;
};


class CMutex
{
public:
	SIMPLEEXCEPTIONCLASS(CError)

	/*
	Constructed object:
	An unlocked mutex object

	Exceptions:
	CError
	*/
	CMutex();

	~CMutex();

	/*
	This object:
	not locked by this thread (NOT CHECKED)

	Note: blocks as long as the mutex is locked by another thread

	Exceptions:
	CError
	*/
	void lock();

	/*
	This object:
	locked by this thread (NOT CHECKED)

	Exceptions:
	CError
	*/
	void unlock();

private:
	pthread_mutex_t m_mutex;
};


template<class T> class CCriticalSection : public CMutex
{
public:
	CCriticalSection() : m_Value() {}
	CCriticalSection(const T &v) : m_Value(v) {}

	T m_Value;
};


class CSemaphore
{
public:
	SIMPLEEXCEPTIONCLASS(CError)
	SIMPLEEXCEPTIONCLASS(CTimeoutError)

	/*
	Constructed object:
	An semaphore object with value 0

	Exceptions:
	CError
	*/
	CSemaphore();

	~CSemaphore();

	/*
	Waits until the value of the semaphore is greater than 0,
	then decrements the value.

	Exceptions:
	CError
	*/
	void wait();

	/*
	Waits until the value of the semaphore is greater than 0,
	then decrements the value.

	Exceptions:
	CError
	CTimeout
	*/
	void waitWithTimeout(unsigned int milliseconds);

	/*
	Increments the value of the semaphore

	Exceptions:
	CError
	*/
	void post();

	/*
	Return value:
	The value of the semaphore
	
	Exceptions:
	CError
	*/
	int getValue();

private:
	sem_t m_semaphore;
};


/*
Instantiating this class registers mutexes for use by OpenSSL.
There should always be either zero or one instance of this class.
*/
class COpenSSLMutexes
{
public:
	COpenSSLMutexes();
	~COpenSSLMutexes();

private:
	static void lockingCallback(int mode, int i, const char* file, int line);

	static CMutex **m_mutexes;
};

#endif

