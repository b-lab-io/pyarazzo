#!/bin/bash
curl -LsSf https://astral.sh/uv/install.sh | sh

make clean
make setup 
make vscode
export VIRTUAL_ENV=.venv
source $VIRTUAL_ENV/bin/activate