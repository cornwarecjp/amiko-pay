/*
    tests_main.cpp
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

#include <string.h>
#include <cstdlib>

#include <openssl/ssl.h>
#include <openssl/err.h>

#include "test.h"

std::vector<CTest *> &getTestList()
{
	static std::vector<CTest *> testList;
	return testList;
}

int main(int argc, char *argv[])
{
	//Commandline options
	int n = 1;

	for(int i=0; i < argc; i++)
		if(strcmp(argv[i], "-n") == 0 && i+1 < argc)
		{
			i++;
			n = atoi(argv[i]);
		}

	//Initialize libssl
	SSL_load_error_strings();
	SSL_library_init();

	/*
	TODO:
	Multi-threaded applications must provide two callback functions to
	OpenSSL by calling CRYPTO_set_locking_callback() and
	CRYPTO_set_id_callback(), for all versions of OpenSSL up to and
	including 0.9.8[abc...].
	As of version 1.0.0, CRYPTO_set_id_callback() and associated APIs are
	deprecated by CRYPTO_THREADID_set_callback() and friends.
	This is described in the threads(3) manpage. 
	*/

	std::vector<CTest *> &testList = getTestList();

	int count = 0;
	while(true)
	{
		for(std::size_t i=0; i < testList.size(); i++)
			testList[i]->run();

		count++;
		if(n > 0 && count >= n) break;
	}

	return 0;
}

