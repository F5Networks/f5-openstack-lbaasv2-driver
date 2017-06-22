#!/usr/bin/env groovy

pipeline {
    agent { docker defaultWorker.getConfig("openstack-test") }
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
