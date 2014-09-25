#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='toradbapi',
    version='0.1',
    description='Wrapper for twisted.enterprise.adbapi.ConnectionPool to use with tornado',
    long_description=open('README.md').read(),
    author='Timofey Trukhanov',
    author_email='timofey.trukhanov@gmail.com',
    license='MIT',
    test_suite='tests',
    install_requires=('tornado', 'twisted'),
    classifiers = (
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: 2.7',
        'Topic :: Database'))
