test:
	make -C unittest test
	make -C scenariotest test

clean:
	make -C unittest clean
	make -C scenariotest clean
	-rm amiko/*.pyc amiko/*/*.pyc
	-rm bitcoinrpc/*.pyc
	-rm goodies/*.pyc
	-rm *.log *.pyc
	#*.dat files might remain: removing them could cause loss of funds.

