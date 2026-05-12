import os
import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from core.database import Base, engine, session_local
from models.user import User
from core.security import get_password_hash, verify_password


@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    """Initialize the test database with proper schema before tests."""
    db_path = "users.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    from sqlalchemy.ext.asyncio import create_async_engine

    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async def _setup():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio
    asyncio.run(_setup())
    yield
    asyncio.run(test_engine.dispose())
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="function")
async def db_session(init_test_db):
    """Provide a transactional database session for each test."""
    async with session_local() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
        yield session
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "securepassword123",
    }


@pytest.fixture
async def authenticated_user(db_session, test_user_data):
    from crud.user import create_user
    from schemas.user import UserCreate
    user_in = UserCreate(**test_user_data)
    user = await create_user(session=db_session, user_in=user_in)
    await db_session.commit()
    return user


@pytest.mark.asyncio
async def test_register(client, test_user_data):
    response = await client.post("/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == test_user_data["name"]
    assert data["email"] == test_user_data["email"]
    assert "password" not in data
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client, authenticated_user):
    test_user_data = {
        "name": "Another User",
        "email": authenticated_user.email,
        "password": "anotherpassword",
    }
    response = await client.post("/auth/register", json=test_user_data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client, authenticated_user):
    response = await client.post("/auth/login", json={
        "email": authenticated_user.email,
        "password": "securepassword123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post("/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "any_password",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    response = await client.get("/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(client, authenticated_user):
    from core.security import create_access_token
    access_token = create_access_token(data={"sub": authenticated_user.id})
    response = await client.get("/users", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_password_not_stored_in_plaintext(db_session, authenticated_user):
    assert authenticated_user.password != "securepassword123"
    assert verify_password("securepassword123", authenticated_user.password)
    assert not verify_password("wrongpassword", authenticated_user.password)


@pytest.mark.asyncio
async def test_refresh_token(client, authenticated_user, db_session):
    from core.security import create_refresh_token, create_access_token
    access_token = create_access_token(data={"sub": authenticated_user.id})
    refresh_token = create_refresh_token(data={"sub": authenticated_user.id})

    from crud.user import update_user_refresh_token
    await update_user_refresh_token(session=db_session, user_id=authenticated_user.id, refresh_token=refresh_token)
    await db_session.commit()

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_logout(client, authenticated_user, db_session):
    from core.security import create_access_token, create_refresh_token
    from crud.user import update_user_refresh_token

    access_token = create_access_token(data={"sub": authenticated_user.id})
    refresh_token = create_refresh_token(data={"sub": authenticated_user.id})
    await update_user_refresh_token(session=db_session, user_id=authenticated_user.id, refresh_token=refresh_token)
    await db_session.commit()

    response = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Logout realizado com sucesso"
