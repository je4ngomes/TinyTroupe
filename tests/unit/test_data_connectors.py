


"""
Unit tests for TinyTroupe data connectors (base class only).

This module contains tests for the TinyDataConnector abstract base class.
"""



import pytest
from tinytroupe.data_connectors import TinyDataConnector

# Dummy connector for testing
class DummyConnector(TinyDataConnector):
    def save_world_data(self, world_data, destination=None, **kwargs):
        self.saved = (world_data, destination)
        return True
    def load_world_data(self, source=None, **kwargs):
        return {"loaded": True, "source": source}
    def list_available_data(self, **kwargs):
        return ["data1", "data2"]
    def delete_data(self, identifier, **kwargs):
        self.deleted = identifier
        return True

class TestDummyConnector:
    """Test a dummy connector based on TinyDataConnector base class."""

    @pytest.fixture
    def connector(self):
        return DummyConnector("Dummy")

    def test_save_world_data(self, connector):
        data = {"foo": "bar"}
        result = connector.save_world_data(data, destination="dest1")
        assert result is True
        assert connector.saved == (data, "dest1")

    def test_load_world_data(self, connector):
        result = connector.load_world_data(source="src1")
        assert result["loaded"] is True
        assert result["source"] == "src1"

    def test_list_available_data(self, connector):
        files = connector.list_available_data()
        assert files == ["data1", "data2"]

    def test_delete_data(self, connector):
        result = connector.delete_data("data1")
        assert result is True
        assert connector.deleted == "data1"

class TestTinyDataConnector:
    """Test the base data connector class interface and abstractness."""

    def test_cannot_instantiate_abstract_base(self):
        """Test that TinyDataConnector cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TinyDataConnector("Test Connector")


