import inspect
import os
import md5
from nose.plugins import Plugin
from snakefood.find import find_dependencies

try:
    from cpickle import dump, load
except ImportError:
    from pickle import dump, load


def file_hash(path):
    f = open(path, 'rb')
    h = md5.new(f.read()).digest()
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

class Changed(Plugin):
    """
    Activate to add a test id (like #1) to each test name output. Activate
    with --failed to rerun failing tests only.
    """
    name = 'changed'
    hash_file = '.nosehashes'
    graph = {}
    hashes = {}
    known_hashes = {}
    failed_modules = set()
    files_tested = set()

    def configure(self, options, conf):
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
            print 'file updated %s' % (path,)
            return True
        else:
            return any(self.dependenciesUpdated(f) for f in self.graph[path] if f not in self.files_tested)        

    def finalize(self, result):
        for m in self.failed_modules:
            print 'module failed: %s' % (m,)
            del self.hashes[m]

        f = open(self.hash_file, 'w')
        dump(self.hashes, f)
        f.close()

    def wantModule(self, m):
        source = inspect.getsourcefile(m)
        self.updateGraph(source)
        if not self.dependenciesUpdated(source):
            return False

import nose

if __name__ == '__main__':
    nose.main(addplugins=[Changed()])
