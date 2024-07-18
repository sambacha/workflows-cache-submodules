import unittest
from unittest.mock import patch, MagicMock
import os
import yaml
from pygit2 import Repository, discover_repository
from your_script_name import parse_gitmodules, generate_bash_scripts, generate_workflow
from hypothesis import given, strategies as st

class TestGitSubmoduleCaching(unittest.TestCase):

    @patch('your_script_name.Repository')
    @patch('your_script_name.discover_repository')
    def test_parse_gitmodules(self, mock_discover, mock_repository):
        mock_repo = MagicMock()
        mock_repo.listall_submodules.return_value = ['submodule1', 'submodule2']
        
        mock_submodule_repo1 = MagicMock()
        mock_submodule_repo1.remotes = {'origin': MagicMock(url='https://example.com/repo1.git')}
        
        mock_submodule_repo2 = MagicMock()
        mock_submodule_repo2.remotes = {'origin': MagicMock(url='https://example.com/repo2.git')}
        
        mock_repository.side_effect = [mock_repo, mock_submodule_repo1, mock_submodule_repo2]
        mock_discover.return_value = 'fake_repo_path'
        
        expected_submodules = [
            {'name': 'submodule1', 'path': 'submodule1', 'url': 'https://example.com/repo1.git'},
            {'name': 'submodule2', 'path': 'submodule2', 'url': 'https://example.com/repo2.git'}
        ]
        
        submodules = parse_gitmodules('fake_repo_path')
        self.assertEqual(submodules, expected_submodules)

    @given(st.lists(st.fixed_dictionaries({
        'name': st.text(min_size=1),
        'path': st.text(min_size=1),
        'url': st.text(min_size=1)
    }), min_size=1))
    def test_generate_bash_scripts(self, submodules):
        generate_bash_scripts(submodules, deduplicate=True)
        
        with open('create_reference_repo.sh', 'r') as f:
            content = f.read()
            for submodule in submodules:
                self.assertIn(f"git clone --bare {submodule['url']} ~/.cache/git/{submodule['name']}", content)
        
        with open('checkout_with_reference.sh', 'r') as f:
            content = f.read()
            for submodule in submodules:
                self.assertIn(f"git submodule update --init --reference ~/.cache/git/{submodule['name']} {submodule['path']}", content)

    @given(st.lists(st.fixed_dictionaries({
        'name': st.text(min_size=1),
        'path': st.text(min_size=1),
        'url': st.text(min_size=1)
    }), min_size=1), st.text(min_size=1))
    @patch('os.makedirs')
    @patch('builtins.open')
    def test_generate_workflow(self, submodules, repo_url, mock_open, mock_makedirs):
        repo_name = re.sub(r'\W+', '_', repo_url)  # sanitize repo URL to use as filename
        mock_open.return_value.__enter__.return_value = MagicMock()
        
        generate_workflow(submodules, repo_url)
        
        mock_makedirs.assert_called_with('.github/workflows', exist_ok=True)
        mock_open.assert_called_with(f'.github/workflows/{repo_name}.yml', 'w')
        
if __name__ == '__main__':
    unittest.main()
