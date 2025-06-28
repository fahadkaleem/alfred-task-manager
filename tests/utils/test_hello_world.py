"""Unit tests for hello_world module."""

from epic_task_manager.utils.hello_world import hello_world


class TestHelloWorld:
    """Test cases for hello_world function."""

    def test_hello_world_return_value(self):
        """Test that hello_world returns the correct string."""
        result = hello_world()
        assert result == "Hello World"

    def test_hello_world_return_type(self):
        """Test that hello_world returns a string type."""
        result = hello_world()
        assert isinstance(result, str)

    def test_hello_world_no_parameters(self):
        """Test that hello_world can be called without parameters."""
        # Should not raise any exceptions
        result = hello_world()
        assert result is not None

    def test_hello_world_integration(self):
        """Integration test for hello_world function."""
        # Test multiple calls return consistent results
        result1 = hello_world()
        result2 = hello_world()
        assert result1 == result2
        assert len(result1) > 0
