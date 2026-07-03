import pytest

from app.connectors import demo_connectors
from app.state.repository import SQLiteRunRepository


@pytest.fixture
def repository():
    return SQLiteRunRepository(":memory:")


@pytest.fixture
def connectors():
    return demo_connectors()

