from collections.abc import Iterator
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event, update
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.compensation.models import Compensation
from app.database import Base, get_session
from app.employees.models import Employee
from app.main import app


@pytest.fixture
def engine() -> Iterator[Engine]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(connection, record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def add_employee(engine: Engine) -> Employee:
    employee = Employee(
        employee_code="EMP-001",
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.test",
        country="GB",
        department="Engineering",
        job_title="Analyst",
    )
    with Session(engine) as session:
        session.add(employee)
        session.commit()
        session.refresh(employee)
    return employee


def set_compensation(client: TestClient, employee_id: object, amount: object = "85000.125", currency: str = "USD"):
    return client.put(
        f"/api/v1/employees/{employee_id}/compensation",
        json={"amount": amount, "currency": currency},
    )


def test_get_compensation_returns_existing_record(client: TestClient, engine: Engine) -> None:
    employee = add_employee(engine)
    created = set_compensation(client, employee.id)

    response = client.get(f"/api/v1/employees/{employee.id}/compensation")

    assert created.status_code == 200
    assert response.status_code == 200
    assert response.json()["employee_id"] == str(employee.id)
    assert response.json()["amount"] == "85000.125"
    assert response.json()["currency"] == "USD"
    assert response.json()["created_at"]
    assert response.json()["updated_at"]


def test_compensation_request_openapi_amount_is_string_only() -> None:
    amount_schema = app.openapi()["components"]["schemas"]["CompensationWriteRequest"]["properties"]["amount"]

    assert amount_schema["type"] == "string"
    assert "anyOf" not in amount_schema


def test_compensation_get_documents_validation_error_response() -> None:
    response = app.openapi()["paths"]["/api/v1/employees/{employee_id}/compensation"]["get"]["responses"]["422"]

    assert response["content"]["application/json"]["schema"]["$ref"].endswith("/ApiErrorResponse")


def test_get_compensation_without_record_returns_compensation_not_found(client: TestClient, engine: Engine) -> None:
    employee = add_employee(engine)

    response = client.get(f"/api/v1/employees/{employee.id}/compensation")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "compensation_not_found", "message": "Compensation not found"}
    }


def test_get_compensation_for_unknown_employee_returns_employee_not_found(client: TestClient) -> None:
    response = client.get(f"/api/v1/employees/{uuid4()}/compensation")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "employee_not_found", "message": "Employee not found"}
    }


def test_put_creates_compensation(client: TestClient, engine: Engine) -> None:
    employee = add_employee(engine)

    response = set_compensation(client, employee.id, "123456.789", "INR")

    assert response.status_code == 200
    assert response.json()["amount"] == "123456.789"
    assert response.json()["currency"] == "INR"
    with Session(engine) as session:
        assert session.get(Compensation, employee.id) is not None


def test_put_replaces_existing_compensation(client: TestClient, engine: Engine) -> None:
    employee = add_employee(engine)
    initial = set_compensation(client, employee.id)

    response = set_compensation(client, employee.id, "90000.5", "GBP")

    assert response.status_code == 200
    assert response.json()["amount"] == "90000.5"
    assert response.json()["currency"] == "GBP"
    assert response.json()["created_at"] == initial.json()["created_at"]


def test_put_for_unknown_employee_returns_employee_not_found(client: TestClient) -> None:
    response = set_compensation(client, uuid4())

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "employee_not_found", "message": "Employee not found"}
    }


@pytest.mark.parametrize("amount", [85000.125, None, "not-a-decimal", "NaN", "Infinity"])
def test_put_rejects_non_decimal_or_non_finite_amounts(
    client: TestClient,
    engine: Engine,
    amount: object,
) -> None:
    employee = add_employee(engine)

    response = set_compensation(client, employee.id, amount)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    with Session(engine) as session:
        assert session.get(Compensation, employee.id) is None


@pytest.mark.parametrize("amount", ["0", "-0.001"])
def test_put_rejects_zero_and_negative_amounts(client: TestClient, engine: Engine, amount: str) -> None:
    employee = add_employee(engine)

    response = set_compensation(client, employee.id, amount)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    with Session(engine) as session:
        assert session.get(Compensation, employee.id) is None


def test_put_rejects_more_than_three_fractional_digits_before_persistence(
    client: TestClient,
    engine: Engine,
) -> None:
    employee = add_employee(engine)

    response = set_compensation(client, employee.id, "85000.1251")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    with Session(engine) as session:
        assert session.get(Compensation, employee.id) is None


@pytest.mark.parametrize("currency", ["usd", "US", "U$D", "123"])
def test_put_rejects_invalid_currency(client: TestClient, engine: Engine, currency: str) -> None:
    employee = add_employee(engine)

    response = set_compensation(client, employee.id, currency=currency)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    with Session(engine) as session:
        assert session.get(Compensation, employee.id) is None


def test_identical_put_does_not_change_updated_at(client: TestClient, engine: Engine) -> None:
    employee = add_employee(engine)
    set_compensation(client, employee.id)
    fixed_updated_at = datetime(2000, 1, 1)
    with Session(engine) as session:
        session.execute(
            update(Compensation)
            .where(Compensation.employee_id == employee.id)
            .values(updated_at=fixed_updated_at)
        )
        session.commit()

    before = client.get(f"/api/v1/employees/{employee.id}/compensation").json()["updated_at"]
    response = set_compensation(client, employee.id)

    assert response.status_code == 200
    assert response.json()["updated_at"] == before
