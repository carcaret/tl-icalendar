SRC=${CURDIR}/src
DIST=$(CURDIR)/dist

.PHONY: deploy
deploy:
	make bundle terraform clean

.PHONY: bundle
bundle:
	make clean dependencies copy

.PHONY: clean
clean:
	echo $(CURDIR)
	rm -rf ${DIST}
	rm -f requirements.txt
	rm -rf out

# Only the runtime dependencies ([packages] in the Pipfile) end up in the
# package; boto3 is provided by the Lambda runtime. The platform is pinned so
# the wheels match the Lambda runtime even when bundling from another machine.
.PHONY: dependencies
dependencies:
	pipenv requirements > requirements.txt
	pip install -r requirements.txt --no-deps -t ${DIST} \
		--platform manylinux2014_x86_64 \
		--python-version 3.13 \
		--only-binary=:all:

.PHONY: copy
copy:
	cp -r ${SRC}/. ${DIST}
	find ${DIST} -type d -name __pycache__ -prune -exec rm -rf {} +

.PHONY: test
test:
	pipenv run pytest tests --ignore=tests/test_integration.py

.PHONY: test-integration
test-integration:
	pipenv run pytest tests/test_integration.py

.PHONY: terraform
terraform:
	$(MAKE) -C tf terraform
