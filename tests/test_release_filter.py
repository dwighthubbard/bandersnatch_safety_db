import os
from collections import defaultdict
from tempfile import TemporaryDirectory
from unittest import skip
import logging
logging.basicConfig(level=logging.DEBUG)
from bandersnatch_safety_db.safety_db import SafetyDBReleaseFilter
from vcr_unittest import VCRTestCase

import bandersnatch.filter
import bandersnatch.main
from bandersnatch.configuration import BandersnatchConfig, Singleton
from bandersnatch.filter import filter_release_plugins
from bandersnatch.master import Master
from bandersnatch.mirror import Mirror
from bandersnatch.package import Package


TEST_CONF = "test.conf"


class TestReleaseFilter(VCRTestCase):

    tempdir = None
    cwd = None

    def setUp(self):
        super(TestProjectFilter, self).setUp()
        self.cwd = os.getcwd()
        self.tempdir = TemporaryDirectory()
        bandersnatch.filter.loaded_filter_plugins = defaultdict(list)
        os.chdir(self.tempdir.name)

    def tearDown(self):
        super(TestProjectFilter, self).tearDown()
        if self.tempdir:
            os.chdir(self.cwd)
            self.tempdir.cleanup()
            self.tempdir = None

    def test__git__loads_db__v1(self):
        plugin = SafetyDBReleaseFilter()
        plugin.initialize_plugin()
        self.assertIsInstance(plugin.safety_db, dict)
        self.assertIn('aiohttp', list(plugin.safety_db.keys()))

        self.assertIn('<0.16.3', [_.specifier for _ in plugin.safety_db['aiohttp']])

    def test__git__loads_db__v2(self):
        plugin = SafetyDBReleaseFilterV2()
        plugin.initialize_plugin()
        self.assertIsInstance(plugin.safety_db, dict)
        self.assertIn('aiohttp', list(plugin.safety_db.keys()))

        self.assertIn('<0.16.3', [_.specifier for _ in plugin.safety_db['aiohttp']])

    def test__plugin__loads__explicitly_enabled_v1(self):
        with open(TEST_CONF, "w") as testconfig_handle:
            testconfig_handle.write(
                """\
[blacklist]
plugins =
    safety_db_release
"""
            )
        instance = BandersnatchConfig()
        instance.config_file = TEST_CONF
        instance.load_configuration()

        plugins = bandersnatch.filter.filter_release_plugins()
        names = [plugin.name for plugin in plugins]
        self.assertListEqual(names, ["safety_db_release"])
        self.assertEqual(len(plugins), 1)

    def test__plugin__doesnt_load__explicitly__disabled(self):
        with open(TEST_CONF, "w") as testconfig_handle:
            testconfig_handle.write(
                """\
[blacklist]
plugins =
    blacklist_package
"""
            )
        instance = BandersnatchConfig()
        instance.config_file = TEST_CONF
        instance.load_configuration()

        plugins = bandersnatch.filter.filter_release_plugins()
        names = [plugin.name for plugin in plugins]
        self.assertNotIn("safety_db_release", names)
        self.assertNotIn("whitelist_project", names)

    def test__filter__matches__release(self):
        with open(TEST_CONF, "w") as testconfig_handle:
            testconfig_handle.write(
                """\
[blacklist]
plugins =
    safety_db_release
"""
            )
        instance = BandersnatchConfig()
        instance.config_file = TEST_CONF
        instance.load_configuration()

        self._dump_config(instance)
        mirror = Mirror(".", Master(url="https://foo.bar.com"))
        pkg = Package("aiohttp", 1, mirror)
        pkg.info = {"name": "aiohttp"}
        pkg.releases = {"0.16.3": {}, "0.16.0": {}, "0.15.1": {}}

        pkg._filter_releases()

        self.assertEqual(pkg.releases, {"0.16.3": {}})

    def test__mirror_run__filter_package(self):
        # Create a configuration that mirrors only the aiida-core package and verify that the created index file
        # does not contain the links for the releases that are in the safety_db for that package.
        # The aiida-core rule in the safety_db is currently     "aiida-core": [ "<0.12.3"]
        config = f"""[mirror]
directory = {os.getcwd()}
json = false
master = https://test.pypi.org
timeout = 10
workers = 1
hash-index = false
stop-on-error = false
verifiers = 1

[blacklist]
plugins =
    safety_db_release
    whitelist_project

[whitelist]
packages =
    aiohttp
    aiida-core
"""
        print(f'Config: \n{config}')
        with open(TEST_CONF, "w") as testconfig_handle:
            testconfig_handle.write(config)

        bandersnatch_config = BandersnatchConfig()
        bandersnatch_config.config_file = TEST_CONF
        bandersnatch_config.load_configuration()

        self._dump_config(bandersnatch_config)
        print('Release plugins:', [_.name for _ in filter_release_plugins()])
        bandersnatch.main.mirror(bandersnatch_config.config)

        print(os.listdir('.'))
        self.assertTrue(os.path.exists('web/simple/aiida-core/index.html'))
        with open('web/simple/aiida-core/index.html') as fh:
            index = fh.read()
        self.assertIn('aiida-core-0.12.3.tar.gz', index)
        self.assertNotIn('aiida-core-0.6.0.1.tar.gz', index)

    def _dump_config(self, configuraton):
        for section in configuraton.config.sections():
            print(f'[{section}]')
            for key, value in configuraton.config.items(section):
                print(f'{key}={value}')
