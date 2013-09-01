.PHONY: test

test:
	rm -f .coverage
	nosetests -s --with-coverage --cover-package=stepford
