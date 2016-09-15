#!/usr/bin/env python

# Copyright 2014 F5 Networks Inc.
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
'''See environment_library for details.'''
import argparse

from f5lbaasdriver.utils.environment_library import generate_driver


def main():
    parser = argparse.ArgumentParser(
        description='''This utility is designed to run on the Neutron
        controller. Use the
        ``f5lbaasdriver.utils.add_environment.add_diff_env_to_controller``
        function to remotely configure your controller with this utility.

        ''')
    parser.add_argument("environment",
                        help="The name of the environment to generate.")
    args = parser.parse_args()
    generate_driver(args.environment)

if __name__ == '__main__':
    main()
