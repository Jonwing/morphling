#! /usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from morphling import __version__ as VERSION


setup(
    name='morphling',
    version=VERSION,
    description='morphling - Markdown-HTML converter',
    url='https://github.com/Jonwing/morphling',
    author='lAzUr',
    author_email='jonwing.lee@gmail.com',
    keywords='markdown html converter',
    packages=find_packages(),
    include_package_data=True,
)
