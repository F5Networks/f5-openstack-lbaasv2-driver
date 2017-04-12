# Makefile for building and testing documentation in a docker container
#

.PHONY: help
help:
	@echo "  docker-preview     to build live preview of docs using sphinx-autobuild in a docker container"
	@echo "  docker-test        to build and test docs in a docker container"

# Build live preview docs in a docker container
.PHONY: docker-preview
docker-preview:
	make -C docs clean
	DOCKER_RUN_ARGS="-p 0.0.0.0:8000:8000" ./docs/scripts/docker-docs.sh \
	  make -C docs preview

# run quality tests in a docker container
.PHONY: docker-test
docker-test:
	make -C docs clean
	./docs/scripts/docker-docs.sh ./docs/scripts/test-docs.sh