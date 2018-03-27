# -*- coding: utf-8 -*-
'''
test_requirements = {'devices':         [],
                     'openstack_infra': []}

'''
# Copyright (c) 2016-2018, F5 Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from barbicanclient import client
from keystoneauth1 import identity
from keystoneauth1 import session
from pytest import symbols as symbol_data

from f5_openstack_agent.lbaasv2.drivers.bigip import barbican_cert


FAKE_CERT = """-----BEGIN CERTIFICATE-----
MIIBozCCAQwCAQEwDQYJKoZIhvcNAQEFBQAwGjEYMBYGA1UEAxQPY2EtaW50QGFj
bWUuY29tMB4XDTE2MDUxMTE2MjcyN1oXDTI2MDUwOTE2MjcyN1owGjEYMBYGA1UE
AxQPc2VydmVyQGFjbWUuY29tMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCn
48EdxKMaBvd2nBY4Pt3UI9OhWfDt0JHF/FnE0MOR1DYEP9WqlRlDorojVSignlne
febsSOFxciUGkeYvGTycR58/aAcWfp6lz6gLoTydfi7/XdReQt4JLzH9f0HYdKzz
z06PjNTOGKtcBipUQjAjtH8HRIfOyatIAiUAHHBrBwIDAQABMA0GCSqGSIb3DQEB
BQUAA4GBACvhrSKPtZVMvTUz4I0oxpl85IeM6p2X1qNjlSreCtLLp8o55HF1BEdI
gLdNgzCs1x9/Mi7ZIwA0FySS4s6E8hMA3OG5Z/42aKGCJyHybeoWXsiVYIwkQi/J
7293ACoLewtjwaGAFeSijukgyHooJUkqWi/oG8qc+K2GwZ8yeYYi
-----END CERTIFICATE-----"""

FAKE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQCn48EdxKMaBvd2nBY4Pt3UI9OhWfDt0JHF/FnE0MOR1DYEP9Wq
lRlDorojVSignlnefebsSOFxciUGkeYvGTycR58/aAcWfp6lz6gLoTydfi7/XdRe
Qt4JLzH9f0HYdKzzz06PjNTOGKtcBipUQjAjtH8HRIfOyatIAiUAHHBrBwIDAQAB
AoGBAIKTPZBEbkIA5xhlv1ZRdr/WeXNFe3/KtoWQhdTwNRrHPJfDeg+o1LRo7HIs
emOppOXJb/+Xk1djWm6orKk27I6wgIGcLJv61jRq9mOG3Hlfs9ZSkVsQIqutUSVm
amhp3uwK3KIk3k7yv16+VTGfsXsPWsT1oWd4CWmWNAjMol9JAkEA3IloSbt+orEf
x36qv//jsq87gOr5eUmwXTySMHaxbXmkIjaCjZHAb70/kWewXZMoj7k6c1Pj9i3T
Tdfhgl3eLQJBAMLjFS1xIqXKLeBzMjcBfVlDF/ZJa4e2EZd1OOJreGkllx3j23fU
NBdsN71XGr16RuxkLo/4HozequTCh5fU4oMCQAfFG5SFc5e9z9XSg6eSF26jN+B5
5uI8E2eli60DcYre30aJTx43xWTqcQPpeFBDsAkoSIPpr71rrecvNPXH4t0CQGGB
JbZPlUsnZV6Xo/b7StCfDd0ODLugbxq87lHx/RN2WC3/M223gLx7S0Py0ZEdHWDm
GpmzRO2r9gpv/VEMlKsCQQCV+EffCQ4wKBIYeCchdntop1/A9PWWCS+pjUNdIJNR
CKxlxUfEZw9yNfLw9g0FKxrdSZiHCAw7fwN7s+CszjT4
-----END RSA PRIVATE KEY-----"""


class Config(object):
    def __init__(self):
        self.auth_version = symbol_data.os_auth_version
        self.os_auth_url = symbol_data.auth_url
        self.os_username = symbol_data.admin_name
        self.os_user_domain_name = 'default'
        self.os_password = symbol_data.admin_password
        self.os_project_name = symbol_data.admin_name
        self.os_project_domain_name = 'default'


def test_cert_manager():
    conf = Config()

    # create Barbican container with cert and key
    container_ref = create_container('server', FAKE_CERT, FAKE_KEY, conf)

    print "\n\nContainer Reference: " + container_ref + "\n"

    # test retrieving cert and key from container
    cert_manager = barbican_cert.BarbicanCertManager(Config())
    cert = cert_manager.get_certificate(container_ref)
    assert cert == FAKE_CERT

    key = cert_manager.get_private_key(container_ref)
    assert key == FAKE_KEY


def create_container(name, cert_payload, key_payload, conf):

    auth = identity.v3.Password(auth_url=conf.os_auth_url,
                                username=conf.os_username,
                                user_domain_name=conf.os_user_domain_name,
                                password=conf.os_password,
                                project_name=conf.os_project_name,
                                project_domain_name=conf.os_project_domain_name)

    # create a Keystone session using the auth plugin we just created
    sess = session.Session(auth=auth)

    # use the session to create a Barbican client
    barbican = client.Client(session=sess)

    # create container
    secret_cert = barbican.secrets.create(name + '.crt', payload=cert_payload)
    secret_key = barbican.secrets.create(name + '.key', payload=key_payload)
    container = barbican.containers.create_certificate(certificate=secret_cert,
                                                       private_key=secret_key)

    # save container in Barbican server
    ref = container.store()

    # test that have valid container reference
    assert ref.startswith("http")

    return ref

