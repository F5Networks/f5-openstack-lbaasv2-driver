From ubuntu:xenial

RUN apt-get -y update \
    && apt-get -y install \
        python-pip \
        git \
        mtr \
        libssl-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install tempest
RUN pip install crudini
RUN pip install git+https://github.com/openstack/neutron.git@stable/mitaka
RUN pip install git+https://github.com/openstack/neutron-lbaas.git@stable/mitaka
RUN mkdir -p /etc/tempest
RUN mkdir -p /root/f5-openstack-lbaasv2-driver
RUN tempest workspace register --name tempest_test --path /root/f5-openstack-lbaasv2-driver/
ADD run_tempest.sh /root/
WORKDIR /root/f5-openstack-lbaasv2-driver
ENTRYPOINT ["/root/run_tempest.sh"]
