.. raw:: html

   <!--
   Copyright 2016 F5 Networks Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
   -->

f5-openstack-lbaasv2-driver
===========================

|Build Status| |Docs Build Status|

Introduction
------------
This repo houses the code for F5's OpenStack LBaaSv2 driver. The driver is part of the plugin package that enables F5 services in OpenStack Neutron's LBaaSv2 service.

Compatibility
-------------
This driver can be used with OpenStack releases from Liberty forward. If
you are using an earlier release, you'll have to use the `LBaaSv1
plugin <https://github.com/F5Networks/f5-openstack-lbaasv1>`__. For more information, please see the F5 OpenStack `Releases, Versioning, and Support Matrix <http://f5-openstack-docs.readthedocs.org/en/latest/releases_and_versioning.html>`_.

Documentation
-------------
The project documentation is on `Read the Docs <http://f5-openstack-lbaasv2-driver.rtfd.org/en/>`_.

Installation
------------

:todo: provide installation instructions

Installing directly from GitHub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration
-------------

:todo: provide configuration instructions

Usage
-----

:todo: provide usage information

Filing Issues
-------------

If you find an issue we would love to hear about it. Please let us know
by filing an issue in this repository and tell us as much as you can
about what you found and how you found it.

Contributing
------------

See `Contributing <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/blob/master/CONTRIBUTING.md>`_.

Build
-----

To make a PyPI package...

.. code:: shell

    $ python setup.py sdist


Test
----
Before you open a pull request, your code must have passing
`pytest <http://pytest.org>`_ unit tests. In addition, you should
include a set of functional tests written to use a real BIG-IP device
for testing. Information on how to run our set of tests is included
below.

Unit Tests
~~~~~~~~~~

We use pytest for our unit tests.

1. If you haven't already, install the required test packages and the :file:`requirements.txt` in your virtual environment.

.. code:: shell

    $ pip install hacking pytest pytest-cov
    $ pip install -r requirements.txt


2. Run the tests and produce a coverage report. The
   ``--cov-report=html`` will create a ``htmlcov/`` directory that you
   can view in your browser to see the missing lines of code.

.. code:: shell

   $ py.test --cov ./icontrol --cov-report=html
   $ open htmlcov/index.html


Style Checks
~~~~~~~~~~~~

We use the hacking module for our style checks (installed as part of
step 1 in the Unit Test section).

.. code:: shell

    $ flake8 ./


Contact
-------
f5_openstack_lbaasv2@f5.com

Copyright
---------
Copyright 2015-2016 F5 Networks Inc.

Support
-------
See `Support <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/blob/master/SUPPORT>`_.

License
-------

Apache V2.0
~~~~~~~~~~~

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Contributor License Agreement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Individuals or business entities who contribute to this project must
have completed and submitted the `F5 Contributor License
Agreement <http://f5-openstack-docs.readthedocs.org/en/latest/cla_landing.html>`_
to Openstack_CLA@f5.com prior to their code submission being included
in this project.


.. |Build Status| image:: https://travis-ci.org/F5Networks/f5-openstack-lbaasv2-driver.svg?branch=master
    :target: https://travis-ci.org/F5Networks/f5-openstack-lbaasv2-driver

.. |Docs Build Status| image:: https://readthedocs.org/projects/f5-openstack-lbaasv2-driver/badge/?version=latest
    :target: http://f5-openstack-lbaasv2-driver.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

