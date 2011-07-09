=======
Bazinga
=======

Bazinga is a nose plugin to run incremental tests.

Motivation
==========

Running the complete test suite on large projects can take a significantly large time. This can affect your work flow, specially if you are doing TDD. Some people choose to run only a subset of the tests, specifying them explicitly on the command line, but you can easily forget to run affected tests after any particular change and things can break unnoticed. Using "bazinga" you can rest assured that all (and only) the affected tests will be run.

How it works
============

Inspecting what is imported by each module, "bazinga" recursively detects what are the dependencies for each test. Only tests that failed, were modified, or had a file that they depend on changed, are run. Each time nose is run with bazinga, a md5 hash for each module that your project depends on will be stored on a file named `.nosebazinga` on the working directory. This file also contains a dependency graph that is used as cache. Bazinga will run all the tests that are needed if a third party package is updated, but the standard library is considered "stable" and is not checked for modifications.

Installation
============

::

    pip install Bazinga


Usage
=====

::

    nosetests --with-bazinga


Debugging
=========

::

    nosetests --with-bazinga --debug=bazinga


Requirements
============

* Nose
* Snakefood

LICENSE
=======

* MIT License