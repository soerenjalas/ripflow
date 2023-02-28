# Contributing to ripflow

Thank you for your interest in contributing to ripflow! This file provides guidelines for contributing to the project. Please take a moment to review these guidelines before submitting any contributions.

## Pull Requests from Forks

We welcome pull requests from forks. To submit a pull request, please fork the repository, make your changes, and then submit a pull request to the `main` branch. We will review your changes as soon as possible and provide feedback if necessary.

## Using Type Hints

We encourage the use of type hints in this project to help ensure code correctness and readability. Here's an example of how to use type hints:

```python
def greet(name: str) -> str:
return f"Hello, {name}!"
```

In this example, the `name` parameter is annotated as a string (`str`) and the return value is annotated as a string as well. Please try to use type hints wherever possible in your contributions. 

## Conforming to Black Code Style

We use the [Black](https://github.com/psf/black) code formatter in this project to ensure consistent code style.

## Pre-commit hooks

You can automatically prepare your code for a PR with pre-commit. This will make your code black conform and will do some type checks using mypy. To prepare this you need to install all dependencies to check the code:

```bash
poetry install
```

To activate the pre-commit hooks run:

```bash
poetry run pre-commit install
```

Now whenever you commit changes they will be checked to see if they are ready to be merged. If a hook fails, you will need to fix the issue before you can commit your changes. The pre-commit output will provide instructions on how to fix the issue.


