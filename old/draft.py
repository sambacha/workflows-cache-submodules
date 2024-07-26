import os
import configparser
from pathlib import Path

# Function to recursively gather submodule paths
def gather_submodule_paths(repo_path, base_path=""):
    submodule_paths = []
    gitmodules_path = os.path.join(repo_path, base_path, ".gitmodules")
    if not os.path.exists(gitmodules_path):
        return submodule_paths
    
    config = configparser.ConfigParser()
    config.read(gitmodules_path)
    
    for section in config.sections():
        submodule_path = config[section]["path"]
        full_submodule_path = os.path.join(base_path, submodule_path)
        submodule_paths.append(full_submodule_path)
        
        # Recursively gather nested submodule paths
        submodule_paths.extend(gather_submodule_paths(repo_path, full_submodule_path))
    
    return submodule_paths

# Function to generate GitHub Action workflow content
def generate_github_action_workflow(submodule_paths):
    cache_paths = "\n          - ".join(submodule_paths)
    workflow_content = f"""name: Cache Git Submodules

on: [push, pull_request]

jobs:
  cache-git-submodules:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        with:
          submodules: recursive

      - name: Cache reference repository
        id: cache-reference-repo
        uses: actions/cache@v3
        with:
          path: |
            reference-repo-cache.tar.gz
            {cache_paths}
          key: ${{{{ runner.os }}}}-reference-repo-${{{{ github.sha }}}}
          restore-keys: |
            ${{{{ runner.os }}}}-reference-repo-

      - name: Extract reference repository cache
        if: steps.cache-reference-repo.outputs.cache-hit == 'true'
        run: tar -xzf reference-repo-cache.tar.gz -C $HOME

      - name: Set up Git and Submodules
        run: |
          chmod +x setup-submodules.sh
          ./setup-submodules.sh

      - name: Save reference repository cache
        if: steps.cache-reference-repo.outputs.cache-hit != 'true'
        run: tar -czf reference-repo-cache.tar.gz -C $HOME git-reference-repo
        continue-on-error: true

      - name: Build and test
        run: |
          # Your build and test commands here
"""
    return workflow_content

# Main script logic
if __name__ == "__main__":
    repo_path = Path(".").resolve()
    submodule_paths = gather_submodule_paths(repo_path)
    
    workflow_content = generate_github_action_workflow(submodule_paths)
    
    with open(".github/workflows/cache_git_submodules.yml", "w") as workflow_file:
        workflow_file.write(workflow_content)
    
    print("GitHub Action workflow file generated at .github/workflows/cache_git_submodules.yml")

