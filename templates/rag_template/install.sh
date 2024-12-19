#!/bin/bash

# Exit on error
set -e

# Get the parent folder name
PARENT_FOLDER=$(basename "$(pwd)")

# Install virtualenv if not already installed
pip install --user virtualenv

# Initialize a virtual environment
python -m venv venv

# Activate the virtual environment with a custom shell prompt
exec bash --rcfile <(echo "source ./venv/bin/activate; export PS1='(${PARENT_FOLDER}_workspace) bash ';")
