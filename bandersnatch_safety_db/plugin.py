import collections
import logging
import requests

from typing import Dict, List
from bandersnatch.filter import FilterProjectPlugin, FilterReleasePlugin
from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import InvalidVersion, Version


logger = logging.getLogger("bandersnatch")


class SafetyDBLoader(object):
    safety_db_src = 'github'

    # Details to fetch from github
    git_branch: str = 'master'
    git_org: str = 'pyupio'
    git_repo: str = 'safety-db'

    # Requires iterable default
    safety_db: Dict[str, List] = {}

    def load_safety_db_from_github(self):
        """Load the safety_db from the official github repo"""
        url = f'https://raw.githubusercontent.com/{self.git_org}/{self.git_repo}/{self.git_branch}/data/insecure.json'
        response = requests.get(url)
        response.raise_for_status()
        logger.debug(f'Loaded safety_db from github at url: {url}')
        print(url)
        return response.json()

    def load_safety_db_from_package(self):
        """Load the safety_db from the safety-db package"""
        from safety_db import INSECURE
        return INSECURE

    def load_safety_db(self):
        """Load the safety_db into the plugin"""
        # Get the safety_db
        if self.safety_db_src == 'github':
            safety_db_src = self.load_safety_db_from_github()
        elif self.safety_db_src == 'package':
            safety_db_src = self.load_safety_db_from_package()

        # Change the requiremnt strings to requirements
        self.safety_db = collections.defaultdict(lambda: [])
        for package, requirements in safety_db_src.items():
            for req in requirements:
                req = req.strip()
                req_str = f'{package}{req}'
                try:
                    self.safety_db[package].append(Requirement(req_str))
                except InvalidRequirement:
                    logger.warn(f'Error adding invalid requirement {req_str}')


class SafetyDBReleaseFilter(FilterReleasePlugin, SafetyDBLoader):
    name = "safety_db_release"

    def initialize_plugin(self):
        """
        Initialize the plugin
        """
        if not self.safety_db:
            self.load_safety_db()

    def _determine_filtered_package_requirements(self):
        """
        Parse the configuration file for [blacklist]packages

        Returns
        -------
        list of packaging.requirements.Requirement
            For all PEP440 package specifiers
        """
        filtered_requirements = set()
        try:
            lines = self.configuration["blacklist"]["packages"]
            package_lines = lines.split("\n")
        except KeyError:
            package_lines = []
        for package_line in package_lines:
            package_line = package_line.strip()
            if not package_line or package_line.startswith("#"):
                continue
            filtered_requirements.add(Requirement(package_line))
        return list(filtered_requirements)

    def filter(self, info, releases):
        name = info["name"]
        if name not in self.safety_db.keys():
            # Package is not in the safety_db
            return

        for version in list(releases.keys()):
            if self._check_match(name, version):
                del releases[version]

    def _check_match(self, name, version_string) -> bool:
        """
        Check if the package name and version matches against a blacklisted
        package version specifier.

        Parameters
        ==========
        name: str
            Package name

        version: str
            Package version

        Returns
        =======
        bool:
            True if it matches, False otherwise.
        """
        if not name or not version_string:
            return False

        try:
            version = Version(version_string)
        except InvalidVersion:
            logger.debug(f"Package {name}=={version_string} has an invalid version")
            return False
        for requirement in self.blacklist_release_requirements:
            if name != requirement.name:
                continue
            if version in requirement.specifier:
                logger.debug(
                    f"MATCH: Release {name}=={version} matches specifier "
                    f"{requirement.specifier}"
                )
                return True
        return False
