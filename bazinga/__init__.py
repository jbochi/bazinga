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
    f = open(path, 'rb')
    h = hashlib.md5(f.read()).hexdigest()
    f.close()
    return h

class Bazinga(Plugin):
    name = 'bazinga'
    hash_file = '.nosehashes'
    graph = {}
    hashes = {}
    known_hashes = {}
    failed_modules = set()
    files_tested = set()
    _missing = []
    _built_in_path = os.path.dirname(os.__file__)

    def configure(self, options, conf):
        self.hash_file = os.path.join(conf.workingDir, self.hash_file)
        if os.path.isfile(self.hash_file):
            f = open(self.hash_file, 'r')
            self.known_hashes = load(f)
            f.close()
        Plugin.configure(self, options, conf)

    def afterTest(self, test):
        # None means test never ran, False means failed/err
        if test.passed is False:
            filename = test.address()[0]
            self.failed_modules.add(filename)

    def dependencies(self, path):
        if os.path.dirname(path) == self._built_in_path:
            log.debug('Ignoring built-in module: %s' % (path,))
            return []

        try:
            files, _ = find_dependencies(path, verbose=False, process_pragmas=False)
        except TypeError, err:
            if path not in self._missing:
                self._missing.append(path)
                log.debug('Snakefood raised an error (%s) parsing path %s' % (err, path))
                return []

        for f in files:
            if not os.path.isfile(path) and path not in missing:
                self._missing.append(path)
                log.debug('Snakefood returned a wrong path: %s' % (f,))

        files = filter(os.path.isfile, files)
        return files

    def updateGraph(self, path):
        if path not in self.graph:
            files = self.dependencies(path)
            self.graph[path] = files
            for f in files:
                self.updateGraph(f)

    def updated(self, path):
        self.hashes.setdefault(path, file_hash(path))
        return path not in self.known_hashes or self.hashes[path] != self.known_hashes[path]

    def dependenciesUpdated(self, path):
        if self.updated(path):
            log.debug('File updated or has failed before: %s' % (path,))
            return True
        else:
            self.files_tested.add(path)
            d = any(self.dependenciesUpdated(f) for f in self.graph[path]
                    if f not in self.files_tested)
            if d:
                log.debug('File depends on updated file: %s' % (path,))
            return d

    def finalize(self, result):
        for k, v in self.known_hashes.iteritems():
            self.hashes.setdefault(k, v)

        for m in self.failed_modules:
            log.debug('Module failed: %s' % (m,))
            self.hashes.pop(m, None)

        f = open(self.hash_file, 'w')
        dump(self.hashes, f)
        f.close()

    def wantModule(self, m):
        source = inspect.getsourcefile(m)
        self.updateGraph(source)
        if not self.dependenciesUpdated(source):
            log.debug('Ignoring module %s, since no dependencies have changed' % (source,))
            return False
