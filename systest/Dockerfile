FROM    docker-registry.pdbld.f5net.com/kevin/jenkins-worker-ubuntu-16.04:9d1fcc866de21a1a6c2c761a5829fc9ddb2da51a
USER    root
RUN     apt-get update && \
        apt-get install -y git=1:2.7.4-0ubuntu1.1 && \
        apt-get install -y nfs-common=1:1.2.8-9ubuntu12.1 && \
        apt-get install -y docker.io=1.12.6-0ubuntu1~16.04.1 && \
        apt-get install -y ipmitool=1.8.16-3ubuntu0.1 && \
        apt-get install -y python-protobuf=2.6.1-1.3 && \
        apt-get install -y protobuf-compiler=2.6.1-1.3 && \
        apt-get install -y gosu=1.7-1
RUN     adduser jenkins staff 
RUN     git clone https://github.com/pypa/pip.git
RUN     cd /home/jenkins/pip && \
        git checkout 022248f6484fe87dc0ef5aec3437f4c7971fd14b && \
        python ./setup.py install && cd /home/jenkins
RUN \
pip install git+git://github.com/pypa/virtualenv.git@2db288fe1f8b6 && \
pip install git+git://github.com/pexpect/pexpect.git@b4fb7c414aca7 && \
pip install git+git://github.com/kjd/idna@0088bfce9c3270e15d8356f0709110c1 && \
pip install git+git://github.com/wbond/asn1crypto@eff254fba6519fadb3cded95 && \
pip install git+git://github.com/benjaminp/six.git@c3ec058bf8c4d6329224eac && \
pip install git+git://github.com/eliben/pycparser.git@2b96ddfd27ec2a9ef84c && \
pip install https://bitbucket.org/cffi/cffi/get/e7063ce.tar.bz2 && \
pip install git+git://github.com/etingof/pyasn1.git@c22b813b9251c35347eace && \
pip install git+git://github.com/pyca/pynacl.git@74ef3bac181fde4bc08f5aa98 && \
pip install git+git://github.com/pyca/bcrypt.git@f3280bda0a560fbf4d401bd8e && \
pip install git+git://github.com/pyca/cryptography.git@23ead43fd70df178289 && \
pip install git+git://github.com/pallets/jinja.git@d78a1b079cd985eea7d636f && \
pip install git+git://github.com/yaml/pyyaml.git@7e026bfee9cc0bddeb1bbca0c && \
pip install git+git://github.com/paramiko/paramiko.git@353e628d34d2ffab6bf && \
pip install git+git://github.com/kislyuk/argcomplete.git@5cd934c586ab2a4f4 && \
pip install git+git://github.com/erikrose/blessings.git@1a463ac86c76453151 && \
pip install git+git://github.com/bw2/ConfigArgParse.git@93b6c6d57e3e05d751 && \
pip install prettytable==0.7.2
RUN     ln -fs /bin/bash /usr/local/bin/bash
RUN     git clone https://gitlab.pdbld.f5net.com/openstack/tlc-toolsbase.git \
/toolsbase
RUN     cd /toolsbase && git checkout 8641ada1fa72079476427e364b326c539739b21d
RUN     mkdir -p /toolsbase/independent/share
RUN     mkdir -p /toolsbase/Ubuntu-10-x86_64/share
RUN     find /toolsbase/independent/ /toolsbase/Ubuntu-10-x86_64/ -iname *pyc \
-exec rm {} \;
RUN     rm -rf /toolsbase/independent/bin/tlc_pb2.py
RUN     ln -sf /toolsbase/Ubuntu-10-x86_64 /tools
RUN     for f in interactive.py ipaddr.py switch_lacp_config.py switches.py; \
do \
    rm -rf /toolsbase/Ubuntu-10-x86_64/bin/$f; \
    rm -rf /toolsbase/independent/bin/$f; \
done
RUN     git clone -b jenkins --single-branch https://gitlab.pdbld.f5net.com/openstack/tlc.git /home/jenkins/tlc
ADD     ./scripts/patches/* /tmp/
RUN     patch /home/jenkins/tlc/tlc/install.sh /tmp/tlc_install.sh.patch
RUN     patch /toolsbase/independent/create_softlinks /tmp/create_softlinks.patch
RUN     patch /home/jenkins/tlc/vmware/install.sh /tmp/vmware_install.patch
RUN     cd /home/jenkins/tlc/tlc && ./install.sh && cd ../tl3 && ./install.sh \
&& cd ../vmware && ./install.sh && cd ../tlc_client && \
python ./setup.py install && cd ../bash_completion_feature && \
./install_bash_completions.sh
USER    jenkins
