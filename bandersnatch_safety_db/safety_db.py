"""
Bandersnatch safety-db filtering plugin module
"""
import collections
import logging
from typing import Any, Dict, List
from bandersnatch.filter import FilterReleasePlugin
from packaging.requirements import Requirement, InvalidRequirement
from packaging.version import InvalidVersion, Version
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
    def load_safety_db_from_package():
        """Load the safety_db from the safety-db package"""
        from safety_db import INSECURE
        return INSECURE  # pylint: disable=E0611

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
        name = kwargs['name']
        version = kwargs['version']
        print(f'Checking for {name}=={version} in safety_db')
        try:
            version = Version(version)
        except InvalidVersion:
            logger.warning(f"Package {name}=={version} has an invalid version")
            return False

        for requirement in self.safety_db[name]:
            if version in requirement.specifier:
                logger.debug(f"MATCH: Release {name}=={version} matches specifier {requirement.specifier}")
                return True

        return False
