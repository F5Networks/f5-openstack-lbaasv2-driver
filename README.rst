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

The F5® OpenStack LBaaSv2 service provider driver (also called the 'F5 LBaaSv2 driver') makes it possible to provision F5 BIG-IP® Local Traffic Manager® (LTM®) services in an OpenStack cloud.

The F5 LBaaSv2 driver works in conjunction with the F5® OpenStack agent, which uses the `f5-sdk <http://f5-sdk.readthedocs.io/en/latest/>`_ to translate Neutron API calls into BIG-IP REST API calls.

Compatibility
-------------

See the `F5 OpenStack Releases, Versioning, and Support Matrix <http://f5-openstack-docs.readthedocs.org/en/latest/releases_and_versioning.html>`_.

Documentation
-------------

Please refer to the F5 OpenStack LBaaSv2 `project documentation <http://f5-openstack-lbaasv2-driver.readthedocs.io>`_ for installation and configuration instructions.

Filing Issues
-------------

If you find an issue, we would love to hear about it. Please let us know by filing an `issue <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/issues>`_ in this repository. Use the issue template to tell us as much as you can about what you found, how you found it, your environment, etc.. We also welcome you to file feature requests as issues.

Contributing
------------

See `Contributing <https://github.com/F5Networks/f5-openstack-lbaasv2-driver/blob/master/CONTRIBUTING.md>`_.


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
    :target: http://f5-openstack-lbaasv2-driver.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. |slack badge| image:: https://f5-openstack-slack.herokuapp.com/badge.svg
    :target: https://f5-openstack-slack.herokuapp.com/
    :alt: Slack
