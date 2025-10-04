"""MongoDB persistence connector for TinyTroupe."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from tinytroupe.data_connectors.base_connector import TinyBatchDataConnector
from tinytroupe.environment import logger

try:  # Optional dependency
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except Exception:  # pragma: no cover - pymongo not installed in some environments
    MongoClient = None  # type: ignore
    PyMongoError = Exception  # type: ignore


class TinyMongoDBConnector(TinyBatchDataConnector):
    """MongoDB-backed connector that stores simulation steps and agent memories."""

    serializable_attributes = [
        "name",
        "description",
        "connector_type",
        "connection_string",
        "database_name",
        "steps_collection_name",
        "agent_memory_collection_name",
    ]

    def __init__(
        self,
        name: str = "MongoDB Database Connector",
        connection_string: Optional[str] = None,
        database_name: Optional[str] = None,
        steps_collection_name: Optional[str] = None,
        agent_memory_collection_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name, "MongoDB persistence connector", "mongodb")

        self.connection_string = connection_string or os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
        self.database_name = database_name or os.getenv("MONGODB_DATABASE", "tinytroupe")
        self.steps_collection_name = steps_collection_name or os.getenv("MONGODB_STEPS_COLLECTION", "world_simulation_steps")
        self.agent_memory_collection_name = (
            agent_memory_collection_name or os.getenv("MONGODB_AGENT_MEMORY_COLLECTION", "world_agent_memory")
        )

        self.client = None
        self.db = None
        self._steps_collection = None
        self._agent_memory_collection = None

        if MongoClient is None:
            logger.warning("pymongo is not installed. MongoDB connector will be inactive.")
            return

        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self._ensure_indexes()
        except Exception as exc:  # pragma: no cover - connection failures are environment dependent
            logger.error(f"Failed to initialize MongoDB connection: {exc}")
            self.client = None
            self.db = None
            self._steps_collection = None
            self._agent_memory_collection = None

    # ------------------------------------------------------------------
    # Collection helpers
    # ------------------------------------------------------------------
    def _ensure_indexes(self) -> None:
        steps = self._get_steps_collection(create_if_missing=True)
        if steps is not None:
            steps.create_index([("world_name", 1), ("simulation_step", 1)], unique=True)
            steps.create_index([("world_name", 1), ("saved_at", -1)])

        memories = self._get_agent_memory_collection(create_if_missing=True)
        if memories is not None:
            memories.create_index([("world_name", 1), ("agent_name", 1)], unique=True)
            memories.create_index([("world_name", 1), ("updated_at", -1)])

    def _get_steps_collection(self, create_if_missing: bool = False):
        if MongoClient is None:
            return None
        if self.db is None and create_if_missing:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
        if self.db is None:
            return None
        if self._steps_collection is None and create_if_missing:
            self._steps_collection = self.db[self.steps_collection_name]
        return self._steps_collection

    def _get_agent_memory_collection(self, create_if_missing: bool = False):
        if MongoClient is None:
            return None
        if self.db is None and create_if_missing:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
        if self.db is None:
            return None
        if self._agent_memory_collection is None and create_if_missing:
            self._agent_memory_collection = self.db[self.agent_memory_collection_name]
        return self._agent_memory_collection

    # ------------------------------------------------------------------
    # Simulation step persistence
    # ------------------------------------------------------------------
    def save_simulation_step(self,
                             world_metadata: Dict[str, Any],
                             step_payload: Dict[str, Any],
                             **kwargs: Any) -> bool:
        if MongoClient is None:
            logger.error("MongoDB connector not available (pymongo not installed).")
            return False

        if not self.validate_step_record(world_metadata, step_payload):
            return False

        collection = self._get_steps_collection(create_if_missing=True)
        if collection is None:
            logger.error("MongoDB steps collection is not available.")
            return False

        document = {
            "world_name": world_metadata["world_name"],
            "simulation_step": world_metadata["simulation_step"],
            "saved_at": world_metadata.get("saved_at"),
            "metadata": world_metadata,
            "payload": step_payload,
            "created_at": datetime.utcnow(),
        }

        try:
            collection.update_one(
                {"world_name": document["world_name"], "simulation_step": document["simulation_step"]},
                {"$set": document},
                upsert=True,
            )
            self._update_operation_stats("save_step")
            return True
        except PyMongoError as exc:  # pragma: no cover - depends on runtime DB state
            return self._handle_error("save_simulation_step", exc)

    def load_simulation_steps(self,
                              world_name: str,
                              start_step: Optional[int] = None,
                              limit: int = 50,
                              reverse: bool = False,
                              **kwargs: Any) -> List[Dict[str, Any]]:
        collection = self._get_steps_collection()
        if collection is None:
            return []

        query: Dict[str, Any] = {"world_name": world_name}
        if start_step is not None:
            comparison_operator = "$lte" if reverse else "$gte"
            query["simulation_step"] = {comparison_operator: start_step}

        sort_direction = -1 if reverse else 1

        try:
            cursor = collection.find(query).sort("simulation_step", sort_direction)
            if limit:
                cursor = cursor.limit(limit)
            steps: List[Dict[str, Any]] = []
            for doc in cursor:
                doc.pop("_id", None)
                steps.append(doc)
            self._update_operation_stats("load_steps")
            return steps
        except PyMongoError as exc:  # pragma: no cover - depends on runtime DB state
            self._handle_error("load_simulation_steps", exc)
            return []

    # ------------------------------------------------------------------
    # Agent memory persistence
    # ------------------------------------------------------------------
    def save_agent_memory(self,
                          world_name: str,
                          agent_name: str,
                          memory_payload: Dict[str, Any],
                          **kwargs: Any) -> bool:
        if MongoClient is None:
            logger.error("MongoDB connector not available (pymongo not installed).")
            return False

        collection = self._get_agent_memory_collection(create_if_missing=True)
        if collection is None:
            logger.error("MongoDB agent memory collection is not available.")
            return False

        document = {
            "world_name": world_name,
            "agent_name": agent_name,
            "memory": memory_payload,
            "updated_at": datetime.utcnow(),
        }

        try:
            collection.update_one(
                {"world_name": world_name, "agent_name": agent_name},
                {"$set": document},
                upsert=True,
            )
            self._update_operation_stats("save_agent_memory")
            return True
        except PyMongoError as exc:  # pragma: no cover
            return self._handle_error("save_agent_memory", exc)

    def save_agent_memories_batch(self,
                                   world_name: str,
                                   memories: List[Dict[str, Any]],
                                   **kwargs: Any) -> List[bool]:
        statuses: List[bool] = []
        for entry in memories:
            agent_name = entry.get("agent_name")
            if agent_name is None:
                logger.warning("Missing agent_name in batch memory entry; skipping.")
                statuses.append(False)
                continue
            payload = entry.get("memory") or entry
            statuses.append(self.save_agent_memory(world_name, agent_name, payload, **kwargs))
        return statuses

    def load_agent_memory(self,
                          world_name: str,
                          agent_name: str,
                          **kwargs: Any) -> Optional[Dict[str, Any]]:
        collection = self._get_agent_memory_collection()
        if collection is None:
            return None
        try:
            doc = collection.find_one({"world_name": world_name, "agent_name": agent_name})
        except PyMongoError as exc:  # pragma: no cover
            self._handle_error("load_agent_memory", exc)
            return None

        if not doc:
            return None

        memory = doc.get("memory")
        if isinstance(memory, dict):
            return memory
        return None

    def load_agent_memories(self,
                            world_name: str,
                            agent_names: Optional[List[str]] = None,
                            **kwargs: Any) -> Dict[str, Dict[str, Any]]:
        collection = self._get_agent_memory_collection()
        if collection is None:
            return {}

        query: Dict[str, Any] = {"world_name": world_name}
        if agent_names:
            query["agent_name"] = {"$in": agent_names}

        try:
            cursor = collection.find(query)
        except PyMongoError as exc:  # pragma: no cover
            self._handle_error("load_agent_memories", exc)
            return {}

        memories: Dict[str, Dict[str, Any]] = {}
        for doc in cursor:
            agent_name = doc.get("agent_name")
            memory = doc.get("memory")
            if agent_name and isinstance(memory, dict):
                memories[agent_name] = memory
        if memories:
            self._update_operation_stats("load_agent_memories")
        return memories

    # ------------------------------------------------------------------
    # Misc utilities
    # ------------------------------------------------------------------
    def list_available_data(self, **kwargs: Any) -> List[str]:
        collection = self._get_steps_collection()
        if collection is None:
            return []
        try:
            worlds = collection.distinct("world_name")
            return sorted(worlds)
        except PyMongoError as exc:  # pragma: no cover
            self._handle_error("list_available_data", exc)
            return []

    def delete_data(self, identifier: str, **kwargs: Any) -> bool:
        steps = self._get_steps_collection()
        memories = self._get_agent_memory_collection()
        if steps is None and memories is None:
            return False

        success = True
        try:
            if steps is not None:
                steps.delete_many({"world_name": identifier})
            if memories is not None:
                memories.delete_many({"world_name": identifier})
            self._update_operation_stats("delete_world")
        except PyMongoError as exc:  # pragma: no cover
            success = False
            self._handle_error("delete_data", exc)
        if success:
            logger.info(f"Deleted data for world '{identifier}' from MongoDB.")
        return success
