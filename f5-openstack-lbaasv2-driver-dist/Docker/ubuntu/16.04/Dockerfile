# Dockerfile
FROM ubuntu:xenial

RUN apt-get update && apt-get install -y \
	python-stdeb \
	fakeroot \
	python-all \
        dh-python \
	git

COPY ./build-debs.sh /

