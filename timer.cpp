/*
    timer.cpp
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

#include <time.h>
#include <unistd.h>

#include "timer.h"


uint64_t CTimer::getTime()
{
	//TODO: check for failure
	//TODO: maybe select monotomic clock?
	timespec t;
	clock_gettime(CLOCK_REALTIME, &t);
	return uint64_t(t.tv_sec)*1000 + t.tv_nsec/1000000;
}


void CTimer::sleep(unsigned int milliseconds)
{
	usleep(milliseconds*1000);
}


