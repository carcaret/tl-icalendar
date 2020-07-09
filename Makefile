SRC=${CURDIR}/src
DIST=$(CURDIR)/dist
ZIP_FILE=$(shell basename $(CURDIR)).zip

.PHONY: bundle
bundle:
	make clean dependencies copy zip

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

.PHONY: zip
zip:
	cd ${DIST} && zip -r ${ZIP_FILE} *