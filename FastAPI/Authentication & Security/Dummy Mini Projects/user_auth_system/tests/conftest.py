import os
os.environ["TESTING"]="1"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from user_auth_system.core.config import settings
from db.database import Base,get_db
from models.user import User
from models.refresh_token import RefreshToken
from  main import app
from services.user import create_user
from schemas.user import UserRegistration

test_engine=create_engine(settings.database_url)
TestingSessionLocal=sessionmaker(bind=test_engine,autoflush=False,autocommit=False)

@pytest.fixture(scope="session",autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    connection=test_engine.connect()
    transaction=connection.begin()
    session=TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db]=override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(db_session):
    user_in=UserRegistration(
        email="testuser@gmail.com",
        password="strongpass",
        confirm_password="strongpass",
    )
    return create_user(db_session,user_in)
