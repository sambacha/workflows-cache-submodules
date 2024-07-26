import unittest
from unittest.mock import patch, MagicMock
import os
import tempfile
import shutil
from pygit2 import Repository, discover_repository
from main import parse_gitmodules, generate_bash_scripts, generate_workflow
# TODO Change Main to script name

class FakeRepository:
    def __init__(self, path, submodules=None):
        self.path = path
        self._submodules = submodules or []

    def listall_submodules(self):
        return self._submodules

    def remotes(self):
        return {'origin': FakeRemote(self.path)}

class FakeRemote:
    def __init__(self, url):
        self.url = url

def fake_discover_repository(path):
    return path

class TestGitSubmoduleCaching(unittest.TestCase):

    def setUp(self):
        self.repo_path = tempfile.mkdtemp()
        self.submodule1_path = os.path.join(self.repo_path, 'submodule1')
        self.submodule2_path = os.path.join(self.repo_path, 'submodule2')
        os.makedirs(self.submodule1_path)
        os.makedirs(self.submodule2_path)

        self.repo = FakeRepository(self.repo_path, submodules=['submodule1', 'submodule2'])
        self.submodule1 = FakeRepository(self.submodule1_path)
        self.submodule2 = FakeRepository(self.submodule2_path)

    def tearDown(self):
        shutil.rmtree(self.repo_path)

    def test_parse_gitmodules(self):
        with patch('your_script_name.Repository', side_effect=[self.repo, self.submodule1, self.submodule2]):
            with patch('your_script_name.discover_repository', side_effect=fake_discover_repository):
                expected_submodules = [
                    {'name': 'submodule1', 'path': 'submodule1', 'url': 'fake_url1'},
                    {'name': 'submodule2', 'path': 'submodule2', 'url': 'fake_url2'}
                ]

                submodules = parse_gitmodules(self.repo_path)
                self.assertEqual(submodules, expected_submodules)

    def test_generate_bash_scripts(self):
        submodules = [
            {'name': 'submodule1', 'path': 'submodule1', 'url': 'https://example.com/repo1.git'},
            {'name': 'submodule2', 'path': 'submodule2', 'url': 'https://example.com/repo2.git'}
        ]

        generate_bash_scripts(submodules, deduplicate=True)
        
        with open('create_reference_repo.sh', 'r') as f:
            content = f.read()
            for submodule in submodules:
                self.assertIn(f"git clone --bare {submodule['url']} ~/.cache/git/{submodule['name']}",```python
                self.assertIn(f"git clone --bare {submodule['url']} ~/.cache/git/{submodule['name']}", content)
        
        with open('checkout_with_reference.sh', 'r') as f:
            content = f.read()
            for submodule in submodules:
                self.assertIn(f"git submodule update --init --reference ~/.cache/git/{submodule['name']} {submodule['path']}", content)

    def test_generate_workflow(self):
        submodules = [
            {'name': 'submodule1', 'path': 'submodule1', 'url': 'https://example.com/repo1.git'},
            {'name': 'submodule2', 'path': 'submodule2', 'url': 'https://example.com/repo2.git'}
        ]

        repo_url = 'https://example.com/repo.git'
        with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
            generate_workflow(submodules, repo_url)

            repo_name = re.sub(r'\W+', '_', repo_url)
            mock_open.assert_called_with(f'.github/workflows/{repo_name}.yml', 'w')

if __name__ == '__main__':
    unittest.main()
