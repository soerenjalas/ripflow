## Introduction

ripflow provides a framework to parallelize data analysis tasks in arbitrary data streams.

The package contains the Python classes to build a middle layer application that reads data from various sources and applies arbitrary analysis pipelines onto the data using overlapping worker processes. The processed data is then published via programmable sink connectors.
