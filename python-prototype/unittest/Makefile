test:
	-rm -rf coverage-html
	python-coverage erase
	make -C core test
	make -C utils test
	make -C channels test
	cp core/.coverage .coverage.core
	cp utils/.coverage .coverage.utils
	cp channels/.coverage .coverage.channels
	python-coverage run --branch --append test_node.py
	python-coverage combine
	python-coverage html -d coverage-html
	python-coverage report -m

clean:
	make -C core clean
	make -C utils clean
	make -C channels clean
	rm -rf .coverage .coverage.* coverage-html
	rm -rf *.pyc *.log

