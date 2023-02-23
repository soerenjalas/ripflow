# Getting Started

## Installation
### with pip
The ripflow package is published as a Python package and can be installed with pip from the DESY gitlab package registry:
```bash
pip install ripflow --index-url https://gitlab.desy.de/api/v4/projects/5555/packages/pypi
```

### with poetry
You can also add ripflow to a project that is managed with poetry. For this, first the gitlab registry needs to be added to the poetry configuration:
```bash
poetry source add --secondary ripflow-repo https://gitlab.desy.de/api/v4/projects/5555/packages/pypi
```
Then the package can be installed:
```bash
poetry add --source ripflow-repo ripflow
```

### from source
To install the package from source, clone the [repository](https://gitlab.desy.de/mls/kaldera-electrons/python-doocs-middlelayer) and install the package with poetry:
```bash
poetry install
```
