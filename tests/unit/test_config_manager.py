import pytest
import threading
import logging
import sys
import time

logger = logging.getLogger("tinytroupe")

sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe import config_manager
from testing_utils import *


class TestModelOverride:
    """Test suite for ConfigManager.model_override() context manager."""

    def test_model_override_basic(self):
        """Test basic model override functionality."""
        original_model = config_manager.get("model")

        with config_manager.model_override(model="test-model"):
            assert config_manager.get("model") == "test-model"

        # Should restore original value after context
        assert config_manager.get("model") == original_model

    def test_model_override_none(self):
        """Test model override with None (should not change config)."""
        original_model = config_manager.get("model")

        with config_manager.model_override(model=None):
            assert config_manager.get("model") == original_model

        assert config_manager.get("model") == original_model

    def test_model_override_nested(self):
        """Test nested model overrides."""
        original_model = config_manager.get("model")

        with config_manager.model_override(model="outer-model"):
            assert config_manager.get("model") == "outer-model"

            with config_manager.model_override(model="inner-model"):
                assert config_manager.get("model") == "inner-model"

            # Should restore to outer-model
            assert config_manager.get("model") == "outer-model"

        # Should restore to original
        assert config_manager.get("model") == original_model

    def test_model_override_thread_safety(self):
        """Test that model overrides are thread-safe."""
        results = {}
        errors = {}

        def worker(model_name, worker_id, delay=0):
            """Worker function that sets a model override and records the result."""
            try:
                with config_manager.model_override(model=model_name):
                    # Add small delay to increase chance of race conditions
                    if delay:
                        time.sleep(delay)
                    results[worker_id] = config_manager.get("model")
            except Exception as e:
                errors[worker_id] = str(e)

        # Create multiple threads with different model overrides
        threads = [
            threading.Thread(target=worker, args=("model-1", 1, 0.01)),
            threading.Thread(target=worker, args=("model-2", 2, 0.01)),
            threading.Thread(target=worker, args=("model-3", 3, 0.01)),
            threading.Thread(target=worker, args=("model-4", 4, 0.01)),
        ]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Check that there were no errors
        assert len(errors) == 0, f"Errors occurred in threads: {errors}"

        # Check that each thread got its own model override
        assert results[1] == "model-1"
        assert results[2] == "model-2"
        assert results[3] == "model-3"
        assert results[4] == "model-4"

    def test_model_override_exception_handling(self):
        """Test that original value is restored even if exception occurs."""
        original_model = config_manager.get("model")

        try:
            with config_manager.model_override(model="test-model"):
                assert config_manager.get("model") == "test-model"
                raise ValueError("Intentional error for testing")
        except ValueError:
            pass

        # Should still restore original value after exception
        assert config_manager.get("model") == original_model

    def test_model_override_different_models(self):
        """Test overriding with different model formats."""
        original_model = config_manager.get("model")

        # Test OpenAI model
        with config_manager.model_override(model="gpt-4-turbo"):
            assert config_manager.get("model") == "gpt-4-turbo"

        # Test Anthropic model (OpenRouter format)
        with config_manager.model_override(model="anthropic/claude-3.5-sonnet"):
            assert config_manager.get("model") == "anthropic/claude-3.5-sonnet"

        # Test OpenRouter format for OpenAI
        with config_manager.model_override(model="openai/gpt-4-turbo"):
            assert config_manager.get("model") == "openai/gpt-4-turbo"

        # Should restore original
        assert config_manager.get("model") == original_model

    def test_model_override_concurrent_same_model(self):
        """Test multiple threads using the same model override."""
        results = []

        def worker(model_name):
            """Worker that uses model override and records result."""
            with config_manager.model_override(model=model_name):
                results.append(config_manager.get("model"))

        # Create multiple threads with the same model
        threads = [
            threading.Thread(target=worker, args=("same-model",))
            for _ in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All should have gotten the same model
        assert all(r == "same-model" for r in results)
        assert len(results) == 5

    def test_model_override_sequential_calls(self):
        """Test sequential model override calls."""
        original_model = config_manager.get("model")

        # First override
        with config_manager.model_override(model="model-1"):
            assert config_manager.get("model") == "model-1"

        # Should restore
        assert config_manager.get("model") == original_model

        # Second override
        with config_manager.model_override(model="model-2"):
            assert config_manager.get("model") == "model-2"

        # Should restore again
        assert config_manager.get("model") == original_model

        # Third override
        with config_manager.model_override(model="model-3"):
            assert config_manager.get("model") == "model-3"

        # Should restore again
        assert config_manager.get("model") == original_model

    def test_model_override_dictionary_access(self):
        """Test that model override works with dictionary-style access."""
        original_model = config_manager["model"]

        with config_manager.model_override(model="dict-test-model"):
            # Test both get() and dictionary access
            assert config_manager.get("model") == "dict-test-model"
            assert config_manager["model"] == "dict-test-model"

        assert config_manager["model"] == original_model

    def test_model_override_cleanup(self):
        """Test that thread overrides are properly cleaned up."""
        original_model = config_manager.get("model")

        # Check initial state of thread overrides
        initial_overrides_count = len(config_manager._thread_overrides)

        with config_manager.model_override(model="cleanup-test"):
            # During override, thread should be in overrides dict
            current_thread_id = threading.get_ident()
            assert current_thread_id in config_manager._thread_overrides

        # After context exit, thread should be removed from overrides
        current_thread_id = threading.get_ident()
        assert current_thread_id not in config_manager._thread_overrides

        # Should return to initial state
        assert len(config_manager._thread_overrides) == initial_overrides_count
        assert config_manager.get("model") == original_model


class TestConfigManagerIntegration:
    """Integration tests for ConfigManager with model_override."""

    def test_config_manager_exists(self):
        """Test that config_manager is properly initialized."""
        assert config_manager is not None
        assert hasattr(config_manager, 'model_override')
        assert hasattr(config_manager, '_override_lock')
        assert hasattr(config_manager, '_thread_overrides')

    def test_config_manager_attributes(self):
        """Test that config_manager has the required attributes."""
        # Check for thread-safety attributes
        assert isinstance(config_manager._override_lock, threading.Lock)
        assert isinstance(config_manager._thread_overrides, dict)

    def test_model_override_is_context_manager(self):
        """Test that model_override is a proper context manager."""
        override = config_manager.model_override(model="test")
        assert hasattr(override, '__enter__')
        assert hasattr(override, '__exit__')
