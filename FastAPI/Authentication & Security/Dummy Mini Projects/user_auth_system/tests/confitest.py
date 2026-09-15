import os
os.environ["TESTING"]="1"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from core.config import settings
from db.database import Base,get_db
from models.user import User
from models.refresh_token import RefreshToken
from  main import app

test_engine=create_engine(settings.database_url)
TestingSessionLocal=sessionmaker(bind=test_engine,autoflush=False,autocommit=False)

@pytest.fixture(scope="session",autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

