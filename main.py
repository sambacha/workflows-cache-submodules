import os
import re
import yaml
import hashlib
from pygit2 import Repository, discover_repository

def parse_gitmodules(repo_path):
    """
    Parse the .gitmodules file to find all submodules recursively.

    Args:
        repo_path (str): The path to the git repository.

    Returns:
        list: A list of dictionaries containing submodule name, path, and URL.
    """
    repo = Repository(discover_repository(repo_path))
    submodules = []

    def collect_submodules(repo, base_path=''):
        for submodule in repo.listall_submodules():
            submodule_path = os.path.join(base_path, submodule)
            submodule_repo_path = os.path.join(repo_path, submodule_path)
            submodule_repo = Repository(submodule_repo_path)
            submodules.append({
                'name': submodule,
                'path': submodule_path,
                'url': submodule_repo.remotes['origin'].url
            })
            collect_submodules(submodule_repo, submodule_path)
    
    collect_submodules(repo)
    return submodules

def generate_bash_scripts(submodules, deduplicate=False):
    """
    Generate bash scripts for creating reference repositories and checking out with reference.

    Args:
        submodules (list): A list of dictionaries containing submodule name, path, and URL.
        deduplicate (bool): Flag to deduplicate nested submodules.
    """
    create_script_content = (
        "#!/bin/bash\n"
        "mkdir -p ~/.cache/git\n"
        "git clone --mirror ${{ github.repository }} ~/.cache/git/repo\n"
    )

    if deduplicate:
        url_to_path = {}
        for submodule in submodules:
            url_hash = hashlib.md5(submodule['url'].encode()).hexdigest()
            if url_hash not in url_to_path:
                url_to_path[url_hash] = submodule['name']
                create_script_content += f"git clone --bare {submodule['url']} ~/.cache/git/{submodule['name']}\n"
            else:
                create_script_content += (
                    f"rm -rf ~/.cache/git/{submodule['name']}\n"
                    f"ln -s ~/.cache/git/{url_to_path[url_hash]} ~/.cache/git/{submodule['name']}\n"
                )
    else:
        create_script_content += "".join(
            [f"git clone --bare {submodule['url']} ~/.cache/git/{submodule['name']}\n" for submodule in submodules]
        )

    checkout_script_content = (
        "#!/bin/bash\n"
        "git clone --reference ~/.cache/git/repo ${{ github.repository }} repo\n"
        "cd repo\n" +
        "".join([f"git submodule update --init --reference ~/.cache/git/{submodule['name']} {submodule['path']}\n" for submodule in submodules])
    )

    with open('create_reference_repo.sh', 'w') as f:
        f.write(create_script_content)

    with open('checkout_with_reference.sh', 'w') as f:
        f.write(checkout_script_content)

def generate_workflow(submodules, repo_url):
    """
    Generate a GitHub Actions workflow file to cache submodules.

    Args:
        submodules (list): A list of dictionaries containing submodule name, path, and URL.
        repo_url (str): The remote URL of the git repository.
    """
    assert isinstance(submodules, list), "submodules should be a list"
    assert all(isinstance(submodule, dict) for submodule in submodules), "Each submodule should be a dictionary"
    assert isinstance(repo_url, str), "repo_url should be a string"

    repo_name = re.sub(r'\W+', '_', repo_url)  # sanitize repo URL to use as filename

    cache_paths = ['~/.cache/git/repo']
    cache_keys = ['${{ runner.os }}-git-${{ hashFiles(\'**/.git\') }}']
    restore_keys = ['${{ runner.os }}-git-']

    for submodule in submodules:
        cache_paths.append(f"~/.cache/git/{submodule['name']}")
        cache_keys.append(f"${{ runner.os }}-git-${{ hashFiles('**/{submodule['path']}/.git') }}")

    workflow = {
        'name': 'CI with Git Submodule Caching',
        'on': ['push', 'pull_request'],
        'jobs': {
            'build': {
                'runs-on': 'ubuntu-latest',
                'steps': [
                    {
                        'name': 'Checkout repository',
                        'uses': 'actions/checkout@v3',
                        'with': {
                            'submodules': 'false',  # Do not use recurse-submodules
                            'fetch-depth': 0
                        }
                    },
                    {
                        'name': 'Setup cache',
                        'id': 'cache-submodule',
                        'uses': 'actions/cache@v3',
                        'with': {
                            'path': '\n'.join(cache_paths),
                            'key': '-'.join(cache_keys),
                            'restore-keys': '\n'.join(restore_keys)
                        }
                    },
                    {
                        'name': 'Create reference repository',
                        'if': "steps.cache-submodule.outputs.cache-hit != 'true'",
                        'run': 'bash create_reference_repo.sh'
                    },
                    {
                        'name': 'Checkout with reference',
                        'run': 'bash checkout_with_reference.sh'
                    },
                    {
                        'name': 'Build',
                        'run': 'echo "Building the project"'
                    }
                ]
            }
        }
    }

    os.makedirs('.github/workflows', exist_ok=True)
    workflow_file = f'.github/workflows/{repo_name}.yml'
    with open(workflow_file, 'w') as f:
        yaml.dump(workflow, f, sort_keys=False)

    print(f"Generated workflow file: {workflow_file}")

def main():
    """
    Main function to parse gitmodules, generate bash scripts, and create the GitHub Actions workflow.

    Args:
        deduplicate (bool): Flag to deduplicate nested submodules.
    """
    repo_path = '.'
    repo = Repository(discover_repository(repo_path))
    repo_url = repo.remotes['origin'].url
    submodules = parse_gitmodules(repo_path)

    assert submodules is not None, "Submodules should not be None"
    assert repo_url, "Repository URL should not be empty"

    deduplicate = True  # Set to True to enable deduplication
    generate_bash_scripts(submodules, deduplicate)
    generate_workflow(submodules, repo_url)

if __name__ == "__main__":
    main()
