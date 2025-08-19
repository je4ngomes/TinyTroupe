"""
Base connector class for TinyTroupe world data export and import.

This module defines the abstract base class for data connectors that handle
saving and loading of world generated data to external destinations.
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from tinytroupe.utils import JsonSerializableRegistry
from tinytroupe.environment import logger


class TinyDataConnector(JsonSerializableRegistry, ABC):
    """
    Abstract base class for data connectors that handle saving and loading
    of TinyTroupe world data to external destinations.
    
    This class provides the interface for implementing connectors to various
    data storage systems such as files, databases, cloud storage, APIs, etc.
    """
    
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
    def save_world_data(self, world_data: Dict[str, Any], 
                       destination: str = None, 
                       **kwargs) -> bool:
        """
        Save world data to the external destination.
        
        Args:
            world_data (Dict[str, Any]): The world data dictionary to save
            destination (str): Optional specific destination within the connector
            **kwargs: Additional connector-specific parameters
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod 
    def load_world_data(self, source: str = None, 
                       **kwargs) -> Optional[Dict[str, Any]]:
        """
        Load world data from the external source.
        
        Args:
            source (str): Optional specific source within the connector
            **kwargs: Additional connector-specific parameters
            
        Returns:
            Optional[Dict[str, Any]]: The loaded world data or None if failed
        """
        pass
    
    @abstractmethod
    def list_available_data(self, **kwargs) -> List[str]:
        """
        List available data sources/destinations in this connector.
        
        Args:
            **kwargs: Additional connector-specific parameters
            
        Returns:
            List[str]: List of available data identifiers
        """
        pass
    
    @abstractmethod
    def delete_data(self, identifier: str, **kwargs) -> bool:
        """
        Delete data from the external destination.
        
        Args:
            identifier (str): Identifier of the data to delete
            **kwargs: Additional connector-specific parameters
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass
    
    def validate_world_data(self, world_data: Dict[str, Any]) -> bool:
        """
        Validate that the provided data appears to be valid world data.
        
        Args:
            world_data (Dict[str, Any]): The world data to validate
            
        Returns:
            bool: True if data appears valid, False otherwise
        """
        required_fields = ["world_name", "saved_at"]
        
        if not isinstance(world_data, dict):
            logger.warning("World data must be a dictionary")
            return False
            
        for field in required_fields:
            if field not in world_data:
                logger.warning(f"Missing required field in world data: {field}")
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
    """
    Extension of TinyDataConnector that supports batch operations for
    saving/loading multiple world data sets at once.
    """
    
    @abstractmethod
    def save_batch_world_data(self, world_data_list: List[Dict[str, Any]], 
                             destination_prefix: str = None,
                             **kwargs) -> List[bool]:
        """
        Save multiple world data sets in a batch operation.
        
        Args:
            world_data_list (List[Dict[str, Any]]): List of world data to save
            destination_prefix (str): Optional prefix for batch destinations
            **kwargs: Additional connector-specific parameters
            
        Returns:
            List[bool]: Success status for each save operation
        """
        pass
    
    @abstractmethod
    def load_batch_world_data(self, source_list: List[str],
                             **kwargs) -> List[Optional[Dict[str, Any]]]:
        """
        Load multiple world data sets in a batch operation.
        
        Args:
            source_list (List[str]): List of sources to load from
            **kwargs: Additional connector-specific parameters
            
        Returns:
            List[Optional[Dict[str, Any]]]: List of loaded world data
        """
        pass


class TinyStreamingDataConnector(TinyDataConnector):
    """
    Extension of TinyDataConnector that supports streaming/real-time
    data operations for continuous world data export.
    """
    
    @abstractmethod
    def start_streaming(self, destination: str = None, **kwargs) -> bool:
        """
        Start streaming world data to the destination.
        
        Args:
            destination (str): Stream destination identifier
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
