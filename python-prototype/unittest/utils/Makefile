test:
	-rm .coverage
	-rm -rf coverage-html
	python-coverage erase
	#python-coverage run --branch --append twonodes.py
	python-coverage run --branch --append all.py
	python-coverage html -d coverage-html
	python-coverage report -m

clean:
	rm -f *.log *.dat *.pyc
	rm -rf .coverage coverage-html

