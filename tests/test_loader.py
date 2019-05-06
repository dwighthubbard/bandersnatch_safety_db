from bandersnatch_safety_db.loader import SafetyDBGit, SafetyDBPackage
from vcr_unittest import VCRTestCase


class TestLoaderSafetyDBGit(VCRTestCase):
    def test__git__is_singleton(self):
        instance_1 = SafetyDBGit()
        instance_2 = SafetyDBGit()
        self.assertEqual(instance_1, instance_2)

    def test__git__loads_db(self):
        result = SafetyDBGit().safety_db
        self.assertIsInstance(result, dict)
        self.assertIn('aiohttp', list(result.keys()))
        self.assertIn('<0.16.3', result['aiohttp'])
