from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function

from setuptools import setup, find_packages

EXCLUDE_FROM_PACKAGES = ['anflow.templates',
                         'anflow.bin']

setup(
    name="anflow",
    version="0.0.0",
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    scripts=['anflow/bin/anflow-admin.py'],
    entry_points={'console_scripts': [
        'anflow-admin = anflow.management:execute_from_command_line',
    ]},
)
