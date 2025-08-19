"""
MongoDB data connector for TinyTroupe

This connector saves and loads world data to a MongoDB collection.
Requires pymongo to be installed.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from .base_connector import TinyDataConnector, TinyBatchDataConnector
from tinytroupe.environment import logger

# Optional dependency: PyMongo
MongoClient = None
try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None


class TinyMongoDBConnector(TinyBatchDataConnector):
    """MongoDB-based connector for TinyTroupe world data."""

    serializable_attributes = [
        "name", "description", "connector_type",
        "connection_string", "database_name", "collection_name",
    ]

    def __init__(self,
                 name: str = "MongoDB Database Connector",
                 connection_string: str = "mongodb://localhost:27017/",
                 database_name: str = "tinytroupe",
                 collection_name: str = "world_data",
                 **kwargs):
        super().__init__(name, "MongoDB database world data connector", "mongodb")
        self.connection_string = connection_string
        self.database_name = database_name
        self.collection_name = collection_name

        self.client = None
        self.db = None
        self._collection = None

        if MongoClient is None:
            logger.warning("pymongo is not installed. MongoDB connector will be inactive.")
        else:
            try:
                self.client = MongoClient(self.connection_string)
                self.db = self.client[self.database_name]
                self._collection = self.db[self.collection_name]
                # Basic index for fast lookups
                self._collection.create_index([("world_name", 1), ("saved_at", 1)], unique=False)
            except Exception as e:
                logger.error(f"Failed to initialize MongoDB connection: {e}")
                self.client = None
                self.db = None
                self._collection = None

    def _get_collection(self):
        if self._collection is None and MongoClient is not None:
            try:
                self.client = MongoClient(self.connection_string)
                self.db = self.client[self.database_name]
                self._collection = self.db[self.collection_name]
                self._collection.create_index([("world_name", 1), ("saved_at", 1)], unique=False)
            except Exception as e:
                logger.error(f"MongoDB connection error: {e}")
                self._collection = None
        return self._collection

    def save_world_data(self, world_data: Dict[str, Any], destination: str = None, **kwargs) -> bool:
        if MongoClient is None:
            logger.error("MongoDB connector not available (pymongo not installed).")
            return False
        if not self.validate_world_data(world_data):
            return False
        coll = self._get_collection()
        if coll is None:
            logger.error("MongoDB collection is not available.")
            return False

        world_name = world_data["world_name"]
        saved_at = world_data["saved_at"]
        data_type = kwargs.get("data_type", "complete")
        replace_existing = kwargs.get("replace_existing", False)

        try:
            existing = coll.find_one({"world_name": world_name, "saved_at": saved_at, "data_type": data_type})
            doc = {
                "world_name": world_name,
                "saved_at": saved_at,
                "data_type": data_type,
                "world_data_json": json.dumps(world_data),
                "created_at": datetime.utcnow(),
                "connector_info": json.dumps(self.get_connector_info())
            }

            if existing and not replace_existing:
                logger.warning(f"Record already exists for {world_name} at {saved_at} in MongoDB.")
                return False

            if existing and replace_existing:
                coll.update_one({"_id": existing["_id"]}, {"$set": {"world_data_json": doc["world_data_json"],
                                                                     "connector_info": doc["connector_info"],
                                                                     "created_at": doc["created_at"]}})
                self._update_operation_stats("save")
                return True

            coll.insert_one(doc)
            self._update_operation_stats("save")
            return True

        except Exception as e:
            return self._handle_error("save_world_data", e)

    def load_world_data(self, source: str = None, **kwargs) -> Optional[Dict[str, Any]]:
        coll = self._get_collection()
        if coll is None:
            return None
        try:
            if source is None:
                cursor = coll.find({"world_name": {"$exists": True}}).sort("saved_at", -1).limit(1)
                doc = None
                for d in cursor:
                    doc = d
                    break
            else:
                data_type = kwargs.get("data_type", "complete")
                saved_at = kwargs.get("saved_at", None)
                if saved_at:
                    doc = coll.find_one({"world_name": source, "data_type": data_type, "saved_at": saved_at})
                else:
                    cursor = coll.find({"world_name": source, "data_type": data_type}).sort("created_at", -1).limit(1)
                    doc = None
                    for d in cursor:
                        doc = d
                        break

            if not doc:
                logger.warning(f"No world data found for: {source}")
                return None

            world_data = json.loads(doc["world_data_json"])
            if not self.validate_world_data(world_data):
                return None

            self._update_operation_stats("load")
            return world_data
        except Exception as e:
            return self._handle_error("load_world_data", e)

    def list_available_data(self, **kwargs) -> List[str]:
        coll = self._get_collection()
        if coll is None:
            return []
        try:
            limit = kwargs.get("limit", 20)
            cursor = coll.find({"world_name": {"$exists": True}}).sort("saved_at", -1).limit(limit)
            seen = set()
            results = []
            for doc in cursor:
                name = doc.get("world_name")
                if name not in seen:
                    results.append(f"{name} (latest: {doc.get('saved_at')})")
                    seen.add(name)
            return results
        except Exception as e:
            return self._handle_error("list_available_data", e) or []

    def delete_data(self, identifier: str, **kwargs) -> bool:
        coll = self._get_collection()
        if coll is None:
            return False
        try:
            coll.delete_many({"world_name": identifier})
            self._update_operation_stats("delete")
            logger.info(f"Deleted world data from MongoDB: {identifier}")
            return True
        except Exception as e:
            return self._handle_error("delete_data", e)

    def save_batch_world_data(self, world_data_list: List[Dict[str, Any]], destination_prefix: str = None, **kwargs) -> List[bool]:
        results: List[bool] = []
        for world_data in world_data_list:
            results.append(self.save_world_data(world_data, **kwargs))
        return results

    def load_batch_world_data(self, source_list: List[str], **kwargs) -> List[Optional[Dict[str, Any]]]:
        results: List[Optional[Dict[str, Any]]] = []
        for source in source_list:
            results.append(self.load_world_data(source, **kwargs))
        return results
