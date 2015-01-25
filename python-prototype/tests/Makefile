test:
	-rm .coverage
	python-coverage run --branch twonodes.py
	python-coverage html -d coverage-html
	python-coverage report -m

clean:
	rm -f *.log *.dat
	rm -rf coverage-html

