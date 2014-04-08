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
#include <cstdio>

#include <openssl/ssl.h>
#include <openssl/err.h>

#include "cthread.h"

#include "test.h"

std::vector<CTest *> &getTestList()
{
	static std::vector<CTest *> testList;
	return testList;
}


std::vector<CFailure> &getFailureList()
{
	static std::vector<CFailure> failList;
	return failList;
}


int main(int argc, char *argv[])
{
	//Commandline options
	int n = 1;
	const char *testName = NULL;

	for(int i=0; i < argc; i++)
	{
		if(strcmp(argv[i], "-n") == 0 && i+1 < argc)
		{
			i++;
			n = atoi(argv[i]);
		}
		if(strcmp(argv[i], "-t") == 0 && i+1 < argc)
		{
			i++;
			testName = argv[i];
		}
	}

	//Initialize libssl
	SSL_load_error_strings();
	SSL_library_init();
	COpenSSLMutexes openSSLMutexes;

	std::vector<CTest *> &testList = getTestList();

	int count = 0;
	while(true)
	{
		for(std::size_t i=0; i < testList.size(); i++)
			if(testName==NULL || strcmp(testList[i]->getName(), testName) == 0)
			{
				printf("\nTest: \"%s\"\n", testList[i]->getName());
				testList[i]->run();
			}

		count++;
		if(n > 0 && count >= n) break;
	}

	std::vector<CFailure> &failures = getFailureList();
	printf("\n\n%ld failures\n\n", long(failures.size()));

	for(std::size_t i=0; i < failures.size(); i++)
		printf("  Failed in test \"%s\": %s\n",
			failures[i].m_testName.c_str(),
			failures[i].m_description.c_str());

	return 0;
}

