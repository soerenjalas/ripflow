

# <img src="docs/assets/ripflow_logo_k.svg" width="60"> ripflow Python middle layer analysis framework

## Introduction

ripflow provides a framework to parallelize data analysis tasks in arbitrary data streams.

The package contains the Python classes to build a middle layer application that reads data from various sources and applies arbitrary analysis pipelines onto the data using overlapping worker processes. The processed data is then published via programmable sink connectors.

For more information, see the [documentation](https://soerenjalas.github.io/ripflow/).

## Installation
### with pip
The ripflow package is published as a Python package and can be installed with pip:
```bash
pip install ripflow
```

### with poetry
You can also add ripflow to a project that is managed with poetry:
```bash
poetry add --source ripflow-repo ripflow
```

### from source
To install the package from source, clone the [repository](https://github.com/soerenjalas/ripflow/) and install the package with poetry:
```bash
poetry install
```
