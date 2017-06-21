FROM    docker-registry.pdbld.f5net.com/kevin/jenkins-worker-ubuntu-16.04:9d1fcc866de21a1a6c2c761a5829fc9ddb2da51a
USER    root
RUN     apt-get update && \
        apt-get install -y docker.io=1.12.6-0ubuntu1~16.04.1
RUN     adduser jenkins staff 
RUN     git clone https://github.com/pypa/pip.git
RUN     cd /home/jenkins/pip && \
        git checkout 022248f6484fe87dc0ef5aec3437f4c7971fd14b && \
        python ./setup.py install && cd /home/jenkins
RUN     pip install git+git://github.com/pypa/virtualenv.git@2db288fe1f8b6
USER    jenkins
