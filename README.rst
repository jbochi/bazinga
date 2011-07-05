=======
Bazinga
=======

Bazinga is a nose plugin to run incremental tests.

It recursively detects what are the dependencies for each test module by looking at the modules that are imported. If no dependency file was changed since the last successful test, it skips all the tests in that module.


Installation
============

::

    pip install Bazinga


Usage
=====

::

    nosetests --with-bazinga


Requirements
============

* Nose
* Snakefood

LICENSE
=======

* MIT License