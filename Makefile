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

.PHONY: dependencies
dependencies:
	pipenv lock -r > requirements.txt
	pip install -r requirements.txt --no-deps -t ${DIST}

.PHONY: copy
copy:
	cp -r ${SRC}/*.py ${DIST}

.PHONY: terraform
terraform:
	$(MAKE) -C tf terraform