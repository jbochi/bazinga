#!/usr/bin/env python
import codecs
import os

try:
    from setuptools import setup, find_packages
except ImportError:
    raise
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

url = "https://github.com/jbochi/bazinga"
if os.path.exists("README.rst"):
    long_description = codecs.open("README.rst", "r", "utf-8").read()
else:
    long_description = "See %s" % (url,)

setup(
	name="Bazinga",
	version="0.1.2",
	description="Bazinga is a nose plugin to run tests only if their dependencies were modified",
	author="Juarez Bochi",
	author_email="jbochi@gmail.com",
	url=url,
	platforms=["any"],
	license="MIT",
        packages=['bazinga'],
	install_requires=["nose", "snakefood"],
	entry_points = {
            'nose.plugins.0.10': [
                'bazinga = bazinga:Bazinga'
            ]
        },
	classifiers=[
		"Development Status :: 4 - Beta",
		"Operating System :: OS Independent",
		"Environment :: No Input/Output (Daemon)",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Natural Language :: Portuguese (Brazilian)",
		"Programming Language :: Python :: 2.5",
		"Programming Language :: Python :: 2.6",
		"Programming Language :: Python :: 2.7",
		"Topic :: Internet",
	],
	long_description=long_description
)
