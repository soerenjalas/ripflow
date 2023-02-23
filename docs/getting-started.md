# Getting Started

## Installation
### with pip
The middle-layer-analyzer package is published as a Python package and can be installed with pip from the DESY gitlab package registry:
```bash
pip install middle-layer-analyzer --index-url https://gitlab.desy.de/api/v4/projects/5555/packages/pypi
```

### with poetry
You can also add middle-layer-analyzer to a project that is managed with poetry. For this, first the gitlab registry needs to be added to the poetry configuration:
```bash
poetry source add --secondary middle-layer-analyzer-repo https://gitlab.desy.de/api/v4/projects/5555/packages/pypi
```
Then the package can be installed:
```bash
poetry add --source middle-layer-analyzer-repo middle-layer-analyzer
```

### from source
To install the package from source, clone the repository and install the package with poetry:
```bash
poetry install
```
