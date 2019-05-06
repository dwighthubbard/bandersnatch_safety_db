import json
import requests
from typing import Dict, List


class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class SafetyDBLoader(object, metaclass=Singleton):
    _safety_db: Dict[str, List[str]] = {}

    @property
    def safety_db(self):
        if not self._safety_db:
            self.load()
        return self._safety_db

    def load(self):
        data = self.load_stream().decode(errors='ignore')
        self._safety_db = json.loads(data)

    def load_stream(self):
        return b''


class SafetyDBPackage(SafetyDBLoader):
    name: str = 'package'

    def load(self):
        from safety_db import INSECURE
        self._safety_db = INSECURE


class SafetyDBGit(SafetyDBLoader):
    name: str = 'git'
    git_branch: str = 'master'
    git_org: str = 'pyupio'
    git_repo: str = 'safety-db'

    def load_stream(self):
        url = f'https://raw.githubusercontent.com/{self.git_org}/{self.git_repo}/{self.git_branch}/data/insecure.json'
        response = requests.get(url)
        response.raise_for_status()
        return response.content


safety_db_loaders = {'git': SafetyDBGit, 'package': SafetyDBPackage}
