#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='mockhttp',
    version='0.1',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    url='http://github.com/disqus/mockhttp',
    description = 'Utilities for mocking HTTP requests with Mock',
    license='Apache License 2.0',
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        'mock',
    ],
    tests_require=[
        'mock',
        'unittest2',
    ],
    test_suite='unittest2.collector',
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)