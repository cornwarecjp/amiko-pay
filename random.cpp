/*
    random.cpp
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

#include <cstdlib>

#include "random.h"

CBinBuffer getSecureRandom(size_t length)
{
	CBinBuffer buffer;
	buffer.resize(length);

	//TODO: actual secure random number generator!!!!!!!!
	//This one even repeats on program re-start!
	size_t pos = 0;
	while(pos < length)
	{
		long int rnd = random();
		long int max = RAND_MAX;
		while(max >= 256 && pos < length)
		{
			buffer[pos] = char(rnd & 0xff);
			rnd /= 256;
			max /= 256;
			pos++;
		}
	}

	return buffer;
}


