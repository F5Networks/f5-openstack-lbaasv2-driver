FROM centos:7

RUN yum update -y && yum install rpm-build make python-setuptools git -y

COPY ./build-rpms.sh /
