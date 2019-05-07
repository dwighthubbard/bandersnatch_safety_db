import logging
logging.basicConfig(level=logging.DEBUG)
from bandersnatch_safety_db.plugin import SafetyDBReleaseFilter
from packaging.requirements import Requirement
from vcr_unittest import VCRTestCase


class TestProjectFilter(VCRTestCase):

    def test__git__loads_db(self):
        plugin = SafetyDBReleaseFilter()
        plugin.initialize_plugin()
        self.assertIsInstance(plugin.safety_db, dict)
        self.assertIn('aiohttp', list(plugin.safety_db.keys()))

        self.assertIn('<0.16.3', [_.specifier for _ in plugin.safety_db['aiohttp']])
