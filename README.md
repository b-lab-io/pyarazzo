# pyarazzo

[![ci](https://github.com/b-lab-io/pyarazzo/workflows/ci/badge.svg)](https://github.com/b-lab-io/pyarazzo/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-zensical-FF9100.svg?style=flat)](https://b-lab-io.github.io/pyarazzo/)
[![pypi version](https://img.shields.io/pypi/v/pyarazzo.svg)](https://pypi.org/project/pyarazzo/)
[![gitter](https://img.shields.io/badge/matrix-chat-4DB798.svg?style=flat)](https://app.gitter.im/#/room/#pyarazzo:gitter.im)

CLI to transform Arazzo specification into some other formats:

- Simple Markdown format combining plnat uml to
- [planned] robot framework scritps to use robot as execution and execution engine 

## Installation

```bash
pip install pyarazzo
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install pyarazzo
```

## usage

```bash
pyarazzo doc generate -s ./examples/pet-coupons-example.yaml -o ./out
```

## Developement environment

```bash
make clean
make setup 
make vscode
export VIRTUAL_ENV=.venv
source $VIRTUAL_ENV/bin/activate
```
