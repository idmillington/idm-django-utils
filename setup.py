#!/usr/bin/env python

from distutils.core import setup

setup(
    name='django-utils',

    version="0.2.2",
    author='Ian Millington',
    author_email='idmillington@googlemail.com',

    url="https://github.com/idmillington/django_utils",
    description="Ian's Django Utility Application",
    packages=['dj_utils', 'dj_utils.fields']
    )
