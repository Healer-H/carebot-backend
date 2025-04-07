#tests/internal/conftest.py
# This file contains fixtures and setup code for integration tests.
import pytest
from tests.mock_data_generator import drop_tables, create_tables, main as generate_data

@pytest.fixture(scope="session", autouse=True)
def prepare_test_db():
    print(" [prepare_test_db] Initializing test DB...")
    drop_tables()
    create_tables()
    generate_data()