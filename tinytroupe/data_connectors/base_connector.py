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


class TinyAgentMemoryConnector(ABC):
    """
    Abstract base class for agent-controlled memory persistence.

    This connector is agent-centric and uses memory_id instead of world_name,
    allowing agents to independently manage their own memory persistence across
    different simulations or sessions.

    Different from TinyDataConnector which is world-centric and controlled by
    TinyWorld for saving all agents in a simulation.
    """

    @abstractmethod
    def save_agent_memory(self,
                          agent_name: str,
                          memory_id: str,
                          memory_payload: Dict[str, Any],
                          **kwargs) -> bool:
        """
        Save agent memory with a specific memory_id.

        Args:
            agent_name (str): Name of the agent
            memory_id (str): Identifier for this memory (e.g., simulation name, session ID)
            memory_payload (Dict[str, Any]): Memory data to persist

        Returns:
            bool: True if save was successful, False otherwise
        """
        pass

    @abstractmethod
    def load_agent_memory(self,
                          agent_name: str,
                          memory_id: str,
                          **kwargs) -> Optional[Dict[str, Any]]:
        """
        Load agent memory by memory_id.

        Args:
            agent_name (str): Name of the agent
            memory_id (str): Identifier for the memory to load

        Returns:
            Optional[Dict[str, Any]]: Memory payload if found, None otherwise
        """
        pass

    @abstractmethod
    def list_agent_memories(self,
                            agent_name: str,
                            **kwargs) -> List[str]:
        """
        List all available memory_ids for an agent.

        Args:
            agent_name (str): Name of the agent

        Returns:
            List[str]: List of memory_id strings
        """
        pass

    @abstractmethod
    def delete_agent_memory(self,
                            agent_name: str,
                            memory_id: str,
                            **kwargs) -> bool:
        """
        Delete a specific agent memory.

        Args:
            agent_name (str): Name of the agent
            memory_id (str): Identifier for the memory to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass
