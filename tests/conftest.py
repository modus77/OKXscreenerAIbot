"""Common pytest fixtures."""
import pytest
import pytest_asyncio

@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
