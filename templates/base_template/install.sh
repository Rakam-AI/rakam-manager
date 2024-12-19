#!/bin/bash

# Exit on error
set -e

pip install virtualenv

# Initialize a virtual environment
python -m venv venv

source ./venv/bin/activate

pip install -r requirements.txt