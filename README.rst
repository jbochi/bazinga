=======
Bazinga
=======

Bazinga is a nose plugin to run incremental tests.

Motivation
==========

Running the complete test suite on large projects can take a significantly large time. This can affect your workflow, specially if you are doing TDD. Some people choose to run only a subset of the tests, specifying them explicitly on the command line, but you can easily forget to run affected tests after any particular change and things can break unnoticed. Using "bazinga" you can rest assured that all (and only) the affected tests will be run.

How it works
============

Looking at what is imported by each module, "bazinga" recursively detects what are the dependencies for each test. Only tests that were modified or had a file that they depend one changed, are run. Tests that failed are also run.

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