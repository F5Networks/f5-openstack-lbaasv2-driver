# Copyright 2016 F5 Networks Inc.
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

import pytest
from uuid import uuid4


class FakeDict(dict):
    """Can be used as Neutron model object or as service builder dict"""
    def __init__(self, *args, **kwargs):
        super(FakeDict, self).__init__(*args, **kwargs)
        if 'id' not in kwargs:
            self['id'] = _uuid()

    def __getattr__(self, item):
        """Needed for using as a model object"""
        if item in self:
            return self[item]
        else:
            return None

    def to_api_dict(self):
        return self

    def to_dict(self, **kwargs):
        return self


def _uuid():
    """Create a random UUID string for model object IDs"""
    return str(uuid4())


@pytest.fixture
def member():
    return [FakeDict(subnet_id=_uuid())]
