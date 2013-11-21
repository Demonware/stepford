.PHONY: test lint

test:
	rm -f .coverage
	nosetests -s --with-coverage --cover-package=stepford

lint:
	pylint stepford.py -r n \
		-d F0401,E0611 \
		--output-format=colorized \
		--msg-template='{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}'
