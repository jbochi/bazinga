import hashlib
import inspect
import imp
import logging
from nose.plugins import Plugin
import os
from snakefood.find import find_dependencies
import sys

try:
    from cpickle import dump, load
except ImportError:
    from pickle import dump, load

log = logging.getLogger(__name__)

def file_hash(path):
    try:
        f = open(path, 'rb')
    except IOError:
        # sometimes we are not able to open a file, even if
        # os.path.isfile returns True, e.g., for files inside
        # an egg. Return "" to assume the file was not modified
        contents = ""
    else:
        contents = f.read()
        f.close()
    finally:
        h = hashlib.md5(contents).hexdigest()
        return h

class Bazinga(Plugin):
    name = 'bazinga'
    hash_file = '.nosebazinga'
    _graph = {}
    _hashes = {}
    _known_graph = {}
    _known_hashes = {}
    _failed_test_modules = set()
    _file_status = {}
    _ignored_files = set()
    _built_in_path = os.path.dirname(os.__file__)

    def configure(self, options, conf):
        self.hash_file = os.path.join(conf.workingDir, self.hash_file)
        if os.path.isfile(self.hash_file):
            log.debug("Loading last known hashes and dependency graph")
            f = open(self.hash_file, 'r')
            data = load(f)
            f.close()
            self._known_hashes = data['hashes']
            self._known_graph = data['graph']
        Plugin.configure(self, options, conf)

    def afterTest(self, test):
        # None means test never ran, False means failed/err
        if test.passed is False:
            filename = test.address()[0]
            self._failed_test_modules.add(filename)

    def inspectDependencies(self, path):
        try:
            files, _ = find_dependencies(path, verbose=False, process_pragmas=False)
        except TypeError, err:
            if path not in self._ignored_files:
                self._ignored_files.add(path)
                log.debug('Snakefood raised an error (%s) parsing path %s' % (err, path))
                return []

        valid_files = []
        for f in files:
            if not os.path.isfile(f):
                if f not in self._ignored_files:
                    self._ignored_files.add(f)
                    log.debug('Snakefood returned a wrong path: %s' % (f,))
            elif os.path.dirname(f) == self._built_in_path:
                if f not in self._ignored_files:
                    self._ignored_files.add(f)
                    log.debug('Ignoring built-in module: %s' % (f,))
            else:
                valid_files.append(f)

        return valid_files

    def updateGraph(self, path):
        if path not in self._graph:
            if not self.fileChanged(path) and path in self._known_graph:
                files = self._known_graph[path]
            else:
                log.debug('Inspecting %s dependencies' % (path,))
                files = self.inspectDependencies(path)
            self._graph[path] = files
            for f in files:
                self.updateGraph(f)

    def fileChanged(self, path):
        if path in self._hashes:
            hash = self._hashes[path]
        else:
            hash = file_hash(path)
            self._hashes[path] = hash

        return path not in self._known_hashes or hash != self._known_hashes[path]

    def dependenciesChanged(self, path, parents=None):
        parents = parents or []

        if path in self._file_status:
            return self._file_status[path]
        elif self.fileChanged(path):
            log.debug('File has been modified or failed: %s' % (path,))
            changed = True
        else:
            childs = self._graph[path]
            parents.append(path)
            changed = any(self.dependenciesChanged(f, parents) for f in childs if
                          f not in parents)

            if changed:
                log.debug('File depends on modified file: %s' % (path,))

        self._file_status[path] = changed
        return changed

    def finalize(self, result):
        for k, v in self._known_hashes.iteritems():
            self._hashes.setdefault(k, v)

        for k, v in self._known_graph.iteritems():
            self._graph.setdefault(k, v)

        for m in self._failed_test_modules:
            log.debug('Module failed: %s' % (m,))
            self._hashes.pop(m, None)

        f = open(self.hash_file, 'w')
        dump({'hashes': self._hashes, 'graph': self._graph}, f)
        f.close()

    def wantModule(self, m):
        source = inspect.getsourcefile(m)
        self.updateGraph(source)
        if not self.dependenciesChanged(source):
            log.debug('Ignoring module %s, since no dependencies have changed' % (source,))
            return False

    def wantClass(self, cls):
        # This test is needed in order to prevent tests from being run
        # even if a module is passed as argument to Nose
        try:
            source = inspect.getsourcefile(cls)
        except TypeError:
            return None

        self.updateGraph(source)
        if not self.dependenciesChanged(source):
            log.debug('Ignoring class %s, since no dependencies have changed' % (source,))
            return False
