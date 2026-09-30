from collections.abc import Iterator
from datetime import UTC, datetime
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.compensation.models import Compensation
from app.database import Base, get_session
from app.employees.models import Employee
from app.main import app


@pytest.fixture
def engine() -> Iterator[Engine]:
    database_url = os.environ.get("COMPENSATION_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("COMPENSATION_TEST_DATABASE_URL must point to a disposable PostgreSQL test database")

    url = make_url(database_url)
    if url.get_backend_name() != "postgresql" or not (
        url.database and url.database.startswith("salary_management_compensation_test_")
    ):
        raise RuntimeError("PostgreSQL integration tests require a dedicated compensation test database")

    test_engine = create_engine(url)
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_postgresql_compensation_upsert_and_timestamp_behavior(
    client: TestClient,
    engine: Engine,
) -> None:
    employee = Employee(
        employee_code=f"COMP-{uuid4().hex[:12]}",
        first_name="Ada",
        last_name="Lovelace",
        email=f"{uuid4().hex}@example.test",
        country="GB",
        department="Engineering",
        job_title="Analyst",
    )
    with Session(engine) as session:
        session.add(employee)
        session.commit()
        employee_id = employee.id

    endpoint = f"/api/v1/employees/{employee_id}/compensation"
    created_response = client.put(endpoint, json={"amount": "85000.125", "currency": "USD"})
    assert created_response.status_code == 200
    created_at = created_response.json()["created_at"]

    updated_response = client.put(endpoint, json={"amount": "90000.125", "currency": "GBP"})
    assert updated_response.status_code == 200
    assert updated_response.json()["amount"] == "90000.125"
    assert updated_response.json()["currency"] == "GBP"
    assert updated_response.json()["created_at"] == created_at

    ancient_timestamp = datetime(2000, 1, 1, tzinfo=UTC)
    with Session(engine) as session:
        session.execute(
            update(Compensation)
            .where(Compensation.employee_id == employee_id)
            .values(updated_at=ancient_timestamp)
        )
        session.commit()

    identical_response = client.put(endpoint, json={"amount": "90000.125", "currency": "GBP"})
    assert identical_response.status_code == 200
    assert identical_response.json()["updated_at"].startswith("2000-01-01T00:00:00")

    changed_response = client.put(endpoint, json={"amount": "90000.125", "currency": "EUR"})
    assert changed_response.status_code == 200
    assert changed_response.json()["currency"] == "EUR"
    assert not changed_response.json()["updated_at"].startswith("2000-01-01T00:00:00")

    with Session(engine) as session:
        rows = session.scalars(
            select(Compensation).where(Compensation.employee_id == employee_id)
        ).all()
        assert len(rows) == 1
        assert rows[0].created_at.isoformat() == created_at.replace("Z", "+00:00")
