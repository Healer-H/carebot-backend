import pytest
from utils.mock_data_generator import drop_tables, create_tables, main as generate_data

@pytest.fixture(scope="session", autouse=True)
def prepare_test_db():
    drop_tables()
    create_tables()
    generate_data(confirm=False)