export WS_ROOT=$(shell pwd)
export PLUGIN=$(notdir $(CURDIR))
export CACHE = 

define banner
	@echo "========================================================================"
	@echo " $(1)"
	@echo "========================================================================"
	@echo " "
endef

.PHONY: debug
debug:
	docker build -t debug/${PLUGIN} . $(CACHE)
	docker run -d --name ${PLUGIN} -v ${WS_ROOT}:/opt debug/${PLUGIN}

.PHONY: test
test: debug
	docker exec ${PLUGIN} bash -c "export AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}; export AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}; cd /opt/test/api; test-tool"

.PHONY: clean
clean:
	docker rm -f ${PLUGIN}

help:
	@echo "Make Targets:"
	@echo " debug                                        - build Plugin Docker Image and Run"
	@echo " test                                         - build Plugin Docker Image then Run UnitTest case"
	@echo " clean                                        - stop Plugin Docker"
