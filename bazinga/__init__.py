import hashlib
import inspect
import os
from nose.plugins import Plugin
from snakefood.find import find_dependencies

try:
    from cpickle import dump, load
except ImportError:
    from pickle import dump, load


def file_hash(path):
    f = open(path, 'rb')
    h = hashlib.md5(f.read()).hexdigest()
    f.close()
    return h

def dependencies(path):
    files = []
    try:
        files, _ = find_dependencies(path, verbose=False, process_pragmas=False)
    except:
        pass #snakefood has some issues :( ignoring them

    files = filter(os.path.isfile, files) #sometimes snakefood returns wrong paths for internal libraries
    return files

class Bazinga(Plugin):
    name = 'bazinga'
    hash_file = '.nosehashes'
    graph = {}
    hashes = {}
    known_hashes = {}
    failed_modules = set()
    files_tested = set()

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
            self.failed_modules.add(test.address()[0])

    def updateGraph(self, path):
        if path not in self.graph and not self.updated(path):
            files = dependencies(path)
            self.graph[path] = files
            for f in files:
                self.updateGraph(f)

    def updated(self, path):
        self.hashes.setdefault(path, file_hash(path))
        return path not in self.known_hashes or self.hashes[path] != self.known_hashes[path]

    def dependenciesUpdated(self, path):
        self.files_tested.add(path)
        if self.updated(path):
            return True
        else:
            return any(self.dependenciesUpdated(f) for f in self.graph[path]
                       if f not in self.files_tested)

    def finalize(self, result):
        for m in self.failed_modules:
            self.hashes.pop(m, None)

        f = open(self.hash_file, 'w')
        dump(self.hashes, f)
        f.close()

    def wantModule(self, m):
        source = inspect.getsourcefile(m)
        self.updateGraph(source)
        if not self.dependenciesUpdated(source):
            return False
