"""Base connector interfaces for TinyTroupe persistence backends."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from tinytroupe.environment import logger
from tinytroupe.utils import JsonSerializableRegistry


class TinyDataConnector(JsonSerializableRegistry, ABC):
    """Abstract base class for persistence connectors used by TinyTroupe."""

    serializable_attributes = ["name", "description", "connector_type"]
    
    def __init__(self, name: str, description: str = "", connector_type: str = "base"):
        """
        Initialize the data connector.
        
        Args:
            name (str): Unique name for this connector instance
            description (str): Optional description of the connector
            connector_type (str): Type identifier for the connector
        """
        self.name = name
        self.description = description
        self.connector_type = connector_type
        self.created_at = datetime.now().isoformat()
        self.last_operation = None
        self.operation_count = 0
        
    @abstractmethod
    def save_simulation_step(self,
                             world_metadata: Dict[str, Any],
                             step_payload: Dict[str, Any],
                             **kwargs) -> bool:
        """Persist a single simulation step snapshot."""

    @abstractmethod
    def load_simulation_steps(self,
                              world_name: str,
                              start_step: Optional[int] = None,
                              limit: int = 50,
                              reverse: bool = False,
                              **kwargs) -> List[Dict[str, Any]]:
        """Retrieve simulation steps for a world, optionally paginated."""

    @abstractmethod
    def save_agent_memory(self,
                          world_name: str,
                          agent_name: str,
                          memory_payload: Dict[str, Any],
                          **kwargs) -> bool:
        """Persist the memory snapshot for an agent."""

    @abstractmethod
    def load_agent_memory(self,
                          world_name: str,
                          agent_name: str,
                          **kwargs) -> Optional[Dict[str, Any]]:
        """Load the memory snapshot for a single agent."""

    def load_agent_memories(self,
                            world_name: str,
                            agent_names: Optional[List[str]] = None,
                            **kwargs) -> Dict[str, Dict[str, Any]]:
        """Load memory snapshots for multiple agents."""
        results: Dict[str, Dict[str, Any]] = {}
        if agent_names is None:
            logger.debug("No agent names provided to load_agent_memories; returning empty mapping.")
            return results
        for agent_name in agent_names:
            memory = self.load_agent_memory(world_name, agent_name, **kwargs)
            if memory is not None:
                results[agent_name] = memory
        return results

    @abstractmethod
    def list_available_data(self, **kwargs) -> List[str]:
        """List identifiers (typically world names) available in the connector."""

    @abstractmethod
    def delete_data(self, identifier: str, **kwargs) -> bool:
        """Delete all persisted data associated with the provided identifier."""

    def validate_step_record(self,
                             world_metadata: Dict[str, Any],
                             step_payload: Dict[str, Any]) -> bool:
        """Basic validation helper for step persistence inputs."""
        required_fields = ["world_name", "simulation_step", "saved_at"]
        if not isinstance(world_metadata, dict):
            logger.warning("world_metadata must be a dictionary")
            return False
        for field in required_fields:
            if world_metadata.get(field) is None:
                logger.warning(f"Missing required field in world metadata: {field}")
                return False
        if not isinstance(step_payload, dict):
            logger.warning("step_payload must be a dictionary")
            return False
        return True

    def get_connector_info(self) -> Dict[str, Any]:
        """
        Get information about this connector instance.
        
        Returns:
            Dict[str, Any]: Connector metadata and status
        """
        return {
            "name": self.name,
            "description": self.description,
            "connector_type": self.connector_type,
            "created_at": self.created_at,
            "last_operation": self.last_operation,
            "operation_count": self.operation_count
        }
    
    def _update_operation_stats(self, operation_type: str):
        """
        Update internal operation statistics.
        
        Args:
            operation_type (str): Type of operation performed
        """
        self.last_operation = {
            "type": operation_type,
            "timestamp": datetime.now().isoformat()
        }
        self.operation_count += 1
        
    def _handle_error(self, operation: str, error: Exception) -> bool:
        """
        Standard error handling for connector operations.
        
        Args:
            operation (str): The operation that failed
            error (Exception): The exception that occurred
            
        Returns:
            bool: Always False (indicating failure)
        """
        logger.error(f"Error in {self.name} connector during {operation}: {error}")
        self._update_operation_stats(f"failed_{operation}")
        return False


class TinyBatchDataConnector(TinyDataConnector):
    """Optional mixin for connectors that support batch persistence APIs."""

    def save_simulation_steps_batch(self,
                                    steps: List[Dict[str, Dict[str, Any]]],
                                    **kwargs) -> List[bool]:
        """Persist a batch of simulation step records."""
        statuses: List[bool] = []
        for step in steps:
            metadata = step.get("metadata", {})
            payload = step.get("payload", {})
            statuses.append(self.save_simulation_step(metadata, payload, **kwargs))
        return statuses

    def save_agent_memories_batch(self,
                                   world_name: str,
                                   memories: List[Dict[str, Any]],
                                   **kwargs) -> List[bool]:
        """Persist a batch of agent memory snapshots."""
        statuses: List[bool] = []
        for entry in memories:
            agent_name = entry.get("agent_name")
            if agent_name is None:
                logger.warning("Missing agent_name in batch memory entry; skipping.")
                statuses.append(False)
                continue
            payload = entry.get("memory") if "memory" in entry else entry
            statuses.append(self.save_agent_memory(world_name, agent_name, payload, **kwargs))
        return statuses


class TinyStreamingDataConnector:
    """
    Connector for streaming world data in real-time.
    """
    
    @abstractmethod
    def start_streaming(self, **kwargs) -> bool:
        """
        Start streaming world data.
        
        Args:
            **kwargs: Additional streaming parameters
            
        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def stream_world_data(self, world_data: Dict[str, Any], **kwargs) -> bool:
        """
        Stream a single world data update.
        
        Args:
            world_data (Dict[str, Any]): World data to stream
            **kwargs: Additional streaming parameters
            
        Returns:
            bool: True if streaming was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def stop_streaming(self, **kwargs) -> bool:
        """
        Stop the current streaming operation.
        
        Args:
            **kwargs: Additional parameters
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        pass
