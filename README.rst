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

|Build Status| |Docs Build Status| |slack badge|

Introduction
------------
The F5® OpenStack LBaaSv2 plugin enables F5® services in OpenStack's Neutron LBaaSv2 service. The plugin comprises an agent and a service provider driver. This repo houses the code for the driver.

The code for the agent, which allows Neutron services to communicate with BIG-IP®, is in the `F5Networks/f5-openstack-agent <https://github.com/F5Networks/f5-openstack-agent>`_ repo.

The code for the plugin that gets upstreamed to the OpenStack community is in the `F5Networks/f5-openstack-lbaasv2 <https://github.com/F5Networks/f5-openstack-lbaasv2>`_ repo.


Compatibility
-------------
The LBaaSv2 plugin is compatible with OpenStack releases from Liberty forward. If
you are using an earlier release, you'll have to use the `LBaaSv1
plugin <https://github.com/F5Networks/f5-openstack-lbaasv1>`__.

For more information, please see the F5® OpenStack `Releases, Versioning, and Support Matrix <http://f5-openstack-docs.readthedocs.org/en/latest/releases_and_versioning.html>`_.

Documentation
-------------
Please refer to the F5® OpenStack LBaaSv2 `project documentation <http://f5-openstack-lbaasv2.readthedocs.org/en/>`_ for installation and configuration instructions.

Filing Issues
-------------
If you find an issue, we would love to hear about it. Please let us know by filing an `issue <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/issues>`_ in this repository. Use the issue template to tell us as much as you can about what you found, how you found it, your environment, etc.. We also welcome feature requests, which can be filed as issues and marked with the ``enhancement`` label.

Contributing
------------
See `Contributing <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/blob/master/CONTRIBUTING.md>`_.

Build
-----
To make a PyPI package:

.. code:: shell

    $ python setup.py sdist


Test
----
Before you open a pull request, your code must have passing `pytest <http://pytest.org>`_ unit tests. In addition, you should include a set of functional tests written to use a real BIG-IP® for testing. Information on how to run our set of tests is provided below.

Unit Tests
~~~~~~~~~~
We use pytest for our unit tests.

1. If you haven't already, install the required test packages in the :file:`requirements.txt` in your virtual environment.

.. code:: shell

    $ pip install hacking pytest pytest-cov
    $ pip install -r requirements.txt


2. Run the tests and produce a coverage report. The ``--cov-report=html`` will create a ``htmlcov/`` directory that you can view in your browser to see the missing lines of code.

.. code:: shell

   $ py.test --cov ./icontrol --cov-report=html
   $ open htmlcov/index.html


Style Checks
~~~~~~~~~~~~

We use the hacking module for our style checks (installed as part of step 1 in the Unit Test section).

.. code:: shell

    $ flake8 ./


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
have completed and submitted the `F5® Contributor License
Agreement <http://f5-openstack-docs.readthedocs.org/en/latest/cla_landing.html>`_
to Openstack_CLA@f5.com prior to their code submission being included
in this project.


.. |Build Status| image:: https://travis-ci.org/F5Networks/f5-openstack-lbaasv2-driver.svg?branch=master
    :target: https://travis-ci.org/F5Networks/f5-openstack-lbaasv2-driver

.. |Docs Build Status| image:: https://readthedocs.org/projects/f5-openstack-lbaasv2/badge/?version=latest
    :target: http://f5-openstack-lbaasv2.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

.. |slack badge| image:: https://f5-openstack-slack.herokuapp.com/badge.svg
    :target: https://f5-openstack-slack.herokuapp.com/
    :alt: Slack