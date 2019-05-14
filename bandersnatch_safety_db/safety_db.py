"""
Bandersnatch safety-db filtering plugin module
"""
import collections
import logging
from typing import Any, Dict, List
from bandersnatch.filter import FilterReleasePlugin
from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import InvalidVersion, LegacyVersion, Version
from pkg_resources import safe_name
import requests


logger = logging.getLogger(__name__)  # pylint: disable=C0103


class SafetyDBReleaseFilter(FilterReleasePlugin):
    """
    Bandersnatch Release filter to filter all release specified in safety_db
    """
    name = "safety_db_release"
    safety_db_src = 'github'

    # Details to fetch from github
    git_branch: str = 'master'
    git_org: str = 'pyupio'
    git_repo: str = 'safety-db'

    # Requires iterable default
    safety_db: Dict[str, List] = {}

    def initialize_plugin(self):
        """
        Initialize the plugin
        """
        if not self.safety_db:
            self.load_safety_db()

    def load_safety_db_from_github(self):
        """Load the safety_db from the official github repo"""
        url = f'https://raw.githubusercontent.com/{self.git_org}/{self.git_repo}/{self.git_branch}/data/insecure.json'
        response = requests.get(url)
        response.raise_for_status()
        logger.debug(f'Loaded safety_db from github at url: {url}')
        return response.json()

    @staticmethod
    def load_safety_db_from_package():  # pragma: no cover
        """Load the safety_db from the safety-db package"""
        # This currently fails because the current versions of the security_db packages are broken and don't include
        # the database files.
        from safety_db import INSECURE  # pylint: disable=E0611
        return INSECURE

    def load_safety_db(self):
        """Load the safety_db into the plugin"""

        # Get the safety_db
        safety_db_src = {}
        if self.safety_db_src == 'github':
            safety_db_src = self.load_safety_db_from_github()
        elif self.safety_db_src == 'package':  # pragma: no cover - The packages are currently broken
            safety_db_src = self.load_safety_db_from_package()

        # Change the requiremnt strings to requirements
        self.safety_db = collections.defaultdict(lambda: [])
        for package, requirements in safety_db_src.items():
            for req in requirements:
                req = req.strip()
                req_str = f'{package}{req}'
                try:
                    self.safety_db[package].append(Requirement(req_str))
                except InvalidRequirement:  # pragma: no cover
                    logger.warning(f'Error adding invalid requirement {req_str}')

    def check_match(self, **kwargs: Any) -> bool:
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
        name = safe_name(kwargs['name']).lower()
        if name not in self.safety_db.keys():
            return False

        version = kwargs['version']
        try:
            version = Version(version)
        except InvalidVersion:  # pragma: no cover
            try:
                version = LegacyVersion(version)
                logger.debug(f'Package {name}=={version} is not a valid PEP 440 version, trying Legacy versioning')
            except InvalidVersion:
                logger.debug(f"Package {name}=={version} has an invalid version")
                return False

        for requirement in self.safety_db[name]:
            if version in requirement.specifier:
                logger.debug(f"Safety DB MATCH: Release {name}=={version} matches specifier {requirement.specifier}")
                return True
        return False


class SafetyDBReleaseFilterV2(SafetyDBReleaseFilter):
    """
    SafetyDBRelease filter for the bandersnatch v2 plugin api
    """
    def filter(self, info, releases):
        """
        Filter releases as per the bandersnatch v2 plugin api.

        This method will delete releases from the releases dictionary that are listed in the loaded safety_db.

        Parameters
        ==========
        info: dict
            The bandersnatch release info from the package metadata

        releases: list
            The bandersnatch releases dictionary to be filtered.
        """
        name = info["name"]
        delete_count = 0
        for version in list(releases.keys()):
            if self.check_match(name=name, version=version):
                del releases[version]
                delete_count += 1
        if delete_count > 0:
            logger.info(f'Filtered {delete_count} releases from {name}')
