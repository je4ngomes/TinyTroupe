
# TinyTroupe Data Connectors

This module currently provides only the base class for data connectors: `TinyDataConnector`.

## Overview

`TinyDataConnector` is an abstract base class that defines the interface for persisting TinyTroupe simulation data (steps, agent memories, etc.) to external destinations such as databases or cloud storage. All custom connectors should inherit from this class and implement its methods.

## Usage

To create your own connector, subclass `TinyDataConnector` and implement the required methods:

```python
from tinytroupe.data_connectors.base_connector import TinyDataConnector


class MyCustomConnector(TinyDataConnector):
    def save_simulation_step(self, world_metadata, step_payload, **kwargs):
        # Persist step metadata and payload
        ...

    def load_simulation_steps(self, world_name, start_step=None, limit=50, reverse=False, **kwargs):
        # Return a list of step documents for the requested world
        ...

    def save_agent_memory(self, world_name, agent_name, memory_payload, **kwargs):
        # Persist an agent memory snapshot
        ...

    def load_agent_memory(self, world_name, agent_name, **kwargs):
        # Retrieve the stored memory snapshot for an agent
        ...

    def list_available_data(self, **kwargs):
        # List identifiers (typically world names) stored by the connector
        ...

    def delete_data(self, identifier, **kwargs):
        # Remove all data associated with a given world
        ...
```

## Notes

- Use this base class as a template for your own storage backends.
- The MongoDB connector (`mongo_connector.py`) provides a concrete example implementation.

---

*Last updated: 2025-03-12*
