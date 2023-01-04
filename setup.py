import os
import sys
from setuptools import setup

base_dir = os.path.dirname(os.path.abspath(__file__))
tests_require = ["tox"]

setup(
    packages=['app',],
    test_suite = "tests.get_tests"
)