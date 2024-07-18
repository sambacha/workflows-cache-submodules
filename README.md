# `cache-submodules-workflow`

> [!NOTE] 
> This script was developed to facilitate efficient CI/CD workflows by caching Git submodules, reducing build times and network I/O.

## Overview

This repository contains a Python script designed to generate a GitHub Actions workflow for caching Git submodules. The script utilizes PyGit2 to parse the repository's `.gitmodules` file, creates bash scripts for setting up a reference repository, and generates a GitHub Actions workflow YAML file. It also includes deduplication logic to eliminate redundant submodules by creating symlinks.

## Features

- **Parse Git Submodules**: Recursively parse submodules listed in `.gitmodules`.
- **Generate Bash Scripts**: Create scripts to set up a reference repository and checkout with reference.
- **GitHub Actions Workflow**: Generate a workflow file that caches submodules and uses the latest `actions/checkout` and `actions/cache`.
- **Deduplication**: Hoist nested submodules by symlinking identical submodules to reduce redundancy.

## Requirements

- Python 3.6+
- PyGit2
- PyYAML
- Hypothesis (for testing)

## Installation

Install the required Python packages using pip:

```bash
pip install pygit2 pyyaml hypothesis
```

## Usage

1. Clone the repository.
2. Navigate to the repository's root directory.
3. Run the Python script:

```bash
python script_name.py
```

Replace `script_name.py` with the actual name of the script file.

4. Make the bash scripts executable:

```bash
chmod +x create_reference_repo.sh checkout_with_reference.sh
```

## Testing

Unit tests are provided using the `unittest` framework and `hypothesis` for property-based testing. To run the tests:

```bash
python -m unittest test_script_name.py
```

Replace `test_script_name.py` with the actual name of the test script file.

## File Structure

- `script_name.py`: Main script for generating the GitHub Actions workflow.
- `create_reference_repo.sh`: Bash script for creating the reference repository.
- `checkout_with_reference.sh`: Bash script for checking out the repository with reference.
- `test_script_name.py`: Unit tests for the main script.

## Example

Here is an example of the generated GitHub Actions workflow file:

```yaml
name: CI with Git Submodule Caching

on:
  - push
  - pull_request

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        with:
          submodules: 'false'
          fetch-depth: 0

      - name: Setup cache
        id: cache-submodule
        uses: actions/cache@v3
        with:
          path: |
            ~/.cache/git/repo
            ~/.cache/git/submodule1
            ~/.cache/git/submodule2
          key: ${{ runner.os }}-git-${{ hashFiles('**/.git') }}
          restore-keys: |
            ${{ runner.os }}-git-

      - name: Create reference repository
        if: steps.cache-submodule.outputs.cache-hit != 'true'
        run: bash create_reference_repo.sh

      - name: Checkout with reference
        run: bash checkout_with_reference.sh

      - name: Build
        run: echo "Building the project"
```
