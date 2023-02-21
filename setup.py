import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="middle_layer_server",
    version="0.1.0",
    author="Soeren Jalas",
    author_email="soeren.jalas@desy.de",
    description="A package to run the middle layer analysis tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitlab.desy.de/mls/kaldera-electrons/python-doocs-middlelayer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
