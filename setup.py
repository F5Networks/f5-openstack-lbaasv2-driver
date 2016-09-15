# Copyright 2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import f5lbaasdriver

from setuptools import find_packages
from setuptools import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='f5-openstack-lbaasv2-driver',

      description='F5 Networks Driver for OpenStack LBaaSv2 service',
      long_description=readme(),
      version=f5lbaasdriver.__version__,
      entry_points={
          'console_scripts': ['add_f5agent_environment='
                              'f5lbaasdriver.utils.add_environment:main']},
      author='f5-openstack-lbaasv2-driver',
      author_email='f5-openstack-lbaasv2-driver@f5.com',
      url='https://github.com/F5Networks/f5-openstack-lbaasv2-driver',

      # Runtime dependencies.
      install_requires=[],

      packages=find_packages(exclude=["*.test", "*.test.*", "test*", "test"]),

      classifiers=['Development Status :: 5 - Production/Stable',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Intended Audience :: System Administrators']
      )
