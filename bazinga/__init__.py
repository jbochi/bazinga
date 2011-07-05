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
    hash_file = '.nosebazinga'
    graph = {}
    hashes = {}
    known_graph = {}
    known_hashes = {}
    failed_modules = set()
    _file_updated = {}
    _ignored = set()
    _built_in_path = os.path.dirname(os.__file__)

    def configure(self, options, conf):
        self.hash_file = os.path.join(conf.workingDir, self.hash_file)
        if os.path.isfile(self.hash_file):
            f = open(self.hash_file, 'r')
            data = load(f)
            f.close()
            self.known_hashes = data['hashes']
            self.known_graph = data['graph']
        Plugin.configure(self, options, conf)

    def afterTest(self, test):
        # None means test never ran, False means failed/err
        if test.passed is False:
            filename = test.address()[0]
            self.failed_modules.add(filename)

    def inspect_dependencies(self, path):
        try:
            files, _ = find_dependencies(path, verbose=False, process_pragmas=False)
        except TypeError, err:
            if path not in self._ignored:
                self._ignored.add(path)
                log.debug('Snakefood raised an error (%s) parsing path %s' % (err, path))
                return []

        valid_files = []
        for f in files:
            if not os.path.isfile(path) and path not in self._ignored:
                self._ignored.append(path)
                log.debug('Snakefood returned a wrong path: %s' % (f,))
            elif os.path.dirname(path) == self._built_in_path and path not in self._ignored:
                self._ignored.append(path)
                log.debug('Ignoring built-in module: %s' % (path,))
            else:
                valid_files.append(path)

        return valid_files

    def updateGraph(self, path):
        if path not in self.graph:
            if not self.updated(path) and path in self.known_graph:
                files = self.known_graph[path]
            else:
                files = self.inspect_dependencies(path)
            self.graph[path] = files
            for f in files:
                self.updateGraph(f)

    def updated(self, path):
        if path not in self.known_hashes:
            return True

        if path not in self.hashes:
            hash = file_hash(path)
            self.hashes[path] = hash
        else:
            hash = self.hashes[path]

        return hash != self.known_hashes[path]

    def dependenciesUpdated(self, path, parents=None):
        parents = parents or []

        if path in self._file_updated:
            return self._file_updated[path]
        elif self.updated(path):
            log.debug('File updated or has failed before: %s' % (path,))
            updated = True
        else:
            childs = self.graph[path]
            new_parents = parents + [path, ]
            if len(new_parents) > 30:
                import ipdb; ipdb.set_trace()

            updated = any(self.dependenciesUpdated(f, new_parents) for f in childs if
                          f not in new_parents)

            if updated:
                log.debug('File depends on updated file: %s' % (path,))

        self._file_updated[path] = updated
        return updated

    def finalize(self, result):
        for k, v in self.known_hashes.iteritems():
            self.hashes.setdefault(k, v)

        for k, v in self.known_graph.iteritems():
            self.graph.setdefault(k, v)

        for m in self.failed_modules:
            log.debug('Module failed: %s' % (m,))
            self.hashes.pop(m, None)

        f = open(self.hash_file, 'w')
        dump({'hashes': self.hashes, 'graph': self.graph}, f)
        f.close()

    def wantModule(self, m):
        source = inspect.getsourcefile(m)
        self.updateGraph(source)
        if not self.dependenciesUpdated(source):
            log.debug('Ignoring module %s, since no dependencies have changed' % (source,))
            return False
