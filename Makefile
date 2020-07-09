SRC=${CURDIR}/src
DIST=$(CURDIR)/dist

.PHONY: deploy
deploy:
	make bundle terraform

.PHONY: bundle
bundle:
	make clean dependencies copy

.PHONY: clean
clean:
	echo $(CURDIR)
	rm -rf ${DIST}
	rm -f ${ZIP_FILE}

.PHONY: dependencies
dependencies:
	pipenv lock -r > requirements.txt
	pip install -r requirements.txt --no-deps -t ${DIST}
	rm requirements.txt

.PHONY: copy
copy:
	cp -r ${SRC}/*.py ${DIST}

.PHONY: terraform
terraform:
	$(MAKE) -C tf terraform