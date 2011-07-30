import unittest
from bazinga import Bazinga
from nose.plugins import Plugin, PluginTester

class TestBazingaPlugin(PluginTester, unittest.TestCase):
    activate = '--with-bazinga'
    plugins = [Bazinga()]

    def makeSuite(self):
        class TC(unittest.TestCase):
            def runTest(self):
                raise ValueError("I thought the 'bazinga' was implied.")
        return unittest.TestSuite([TC()])

    def test_error_on_output(self):
        assert "ValueError" in self.output
