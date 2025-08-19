
# TinyTroupe Data Connectors

This module currently provides only the base class for data connectors: `TinyDataConnector`.

## Overview

`TinyDataConnector` is an abstract base class that defines the interface for saving and loading world simulation data to and from external destinations (such as files, databases, or cloud storage). All custom connectors should inherit from this class and implement its methods.

## Usage

To create your own connector, subclass `TinyDataConnector` and implement the required methods:

```python
from tinytroupe.data_connectors.base_connector import TinyDataConnector

class MyCustomConnector(TinyDataConnector):
    def save_world_data(self, world_data, destination=None, **kwargs):
        # Implement saving logic
        pass

    def load_world_data(self, source=None, **kwargs):
        # Implement loading logic
        pass

    def list_available_data(self, **kwargs):
        # Implement listing logic
        pass

    def delete_data(self, identifier, **kwargs):
        # Implement deletion logic
        pass
```

## Notes

- All other connector implementations have been removed from this module.
- You can use this base class as a template for your own storage backends.
- For examples of how to implement a connector, see the docstring in `TinyDataConnector`.

---

*Last updated: August 2025*
