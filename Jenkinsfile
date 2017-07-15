#!/usr/bin/env groovy

pipeline {
    agent {
        docker {
            label "docker"
            registryUrl "https://docker-registry.pdbld.f5net.com"
            image "openstack-infra/drivertestrunner:latest"
            args "-v /etc/localtime:/etc/localtime:ro" \
                + " -v /srv/mesos/trtl/results:/home/jenkins/results" \
                + " -v /srv/nfs:/testlab" \
                + " -v /var/run/docker.sock:/var/run/docker.sock" \
                + " --env-file /srv/kubernetes/infra/jenkins-worker/config/openstack-test.env"
        }
    }
    options {
        ansiColor('xterm')
        timestamps()
        timeout(time: 2, unit: "HOURS")
    }
    stages {
        stage("systest") {
            steps {
                sh '''
                    # - initialize env vars
                    . systest/scripts/init_env.sh

                    # - record start of build
                    systest/scripts/record_build_start.sh

                    # - setup ssh agent
                    eval $(ssh-agent -s)
                    ssh-add

                    # - run systests
                    target_name=tempest_$(echo $JOB_BASE_NAME | sed s/-/_/g)
                    make -C systest $target_name

                    # - record results
                    systest/scripts/record_results.sh
                '''
            }
        }
    }
    post {
        always {
            // cleanup workspace
            dir("${env.WORKSPACE}") { deleteDir() }
        }
    }
}
