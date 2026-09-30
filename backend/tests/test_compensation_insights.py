from collections.abc import Iterator
from decimal import Decimal
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.compensation.models import Compensation
from app.database import Base, get_session
from app.employees.models import Employee
from app.main import app


@pytest.fixture
def engine() -> Iterator[Engine]:
    postgres_url = os.environ.get("COMPENSATION_TEST_DATABASE_URL")
    if postgres_url:
        url = make_url(postgres_url)
        if url.get_backend_name() != "postgresql" or not (
            url.database and url.database.startswith("salary_management_compensation_test_")
        ):
            raise RuntimeError("Insights PostgreSQL tests require a dedicated compensation test database")
        test_engine = create_engine(url)
    else:
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


def add_employee(
    engine: Engine,
    *,
    index: int,
    country: str = "GB",
    department: str = "Engineering",
    job_title: str = "Analyst",
    amount: Decimal | None = None,
    currency: str = "USD",
) -> None:
    employee = Employee(
        employee_code=f"EMP-{index:03}",
        first_name="Ada",
        last_name="Lovelace",
        email=f"ada{index}@example.test",
        country=country,
        department=department,
        job_title=job_title,
    )
    with Session(engine) as session:
        session.add(employee)
        session.flush()
        if amount is not None:
            session.add(Compensation(employee_id=employee.id, amount=amount, currency=currency))
        session.commit()


def test_empty_organization_returns_zero_coverage_and_empty_groups(client: TestClient) -> None:
    response = client.get("/api/v1/insights/compensation")

    assert response.status_code == 200
    assert response.json() == {
        "coverage": {
            "total_employee_count": 0,
            "employees_with_compensation": 0,
            "employees_without_compensation": 0,
        },
        "salary_by_currency": [],
        "employee_breakdowns": {"by_country": [], "by_department": [], "by_job_title": []},
        "department_salary_by_currency": [],
    }


def test_no_compensation_reports_employee_counts_but_no_salary_statistics(
    client: TestClient,
    engine: Engine,
) -> None:
    add_employee(engine, index=1, country="US", department="People", job_title="Manager")
    add_employee(engine, index=2, country="US", department="People", job_title="Manager")

    body = client.get("/api/v1/insights/compensation").json()

    assert body["coverage"] == {
        "total_employee_count": 2,
        "employees_with_compensation": 0,
        "employees_without_compensation": 2,
    }
    assert body["salary_by_currency"] == []
    assert body["department_salary_by_currency"] == []
    assert body["employee_breakdowns"]["by_country"] == [
        {"country": "US", "employee_count": 2, "employees_with_compensation": 0}
    ]


def test_coverage_and_employee_breakdowns_count_compensated_and_missing_employees(
    client: TestClient,
    engine: Engine,
) -> None:
    add_employee(engine, index=1, country="US", department="People", job_title="Manager")
    add_employee(engine, index=2, country="GB", department="Engineering", job_title="Analyst", amount=Decimal("1"))
    add_employee(engine, index=3, country="GB", department="Engineering", job_title="Analyst")

    body = client.get("/api/v1/insights/compensation").json()

    assert body["coverage"] == {
        "total_employee_count": 3,
        "employees_with_compensation": 1,
        "employees_without_compensation": 2,
    }
    assert body["employee_breakdowns"]["by_country"] == [
        {"country": "GB", "employee_count": 2, "employees_with_compensation": 1},
        {"country": "US", "employee_count": 1, "employees_with_compensation": 0},
    ]
    assert body["employee_breakdowns"]["by_department"] == [
        {"department": "Engineering", "employee_count": 2, "employees_with_compensation": 1},
        {"department": "People", "employee_count": 1, "employees_with_compensation": 0},
    ]
    assert body["employee_breakdowns"]["by_job_title"] == [
        {"job_title": "Analyst", "employee_count": 2, "employees_with_compensation": 1},
        {"job_title": "Manager", "employee_count": 1, "employees_with_compensation": 0},
    ]


def test_salary_statistics_are_exact_and_separate_for_each_currency(
    client: TestClient,
    engine: Engine,
) -> None:
    add_employee(engine, index=1, amount=Decimal("0.125"), currency="USD")
    add_employee(engine, index=2, amount=Decimal("0.375"), currency="USD")
    add_employee(engine, index=3, amount=Decimal("100.125"), currency="EUR")
    add_employee(engine, index=4, amount=Decimal("100.375"), currency="EUR")
    add_employee(engine, index=5, amount=Decimal("100.625"), currency="EUR")
    add_employee(engine, index=6, amount=Decimal("999.999"), currency="JPY", department="People")
    add_employee(engine, index=7, currency="JPY", department="People")

    body = client.get("/api/v1/insights/compensation").json()

    assert body["salary_by_currency"] == [
        {
            "currency": "EUR",
            "employee_count": 3,
            "average_amount": "100.375",
            "median_amount": "100.375",
            "minimum_amount": "100.125",
            "maximum_amount": "100.625",
        },
        {
            "currency": "JPY",
            "employee_count": 1,
            "average_amount": "999.999",
            "median_amount": "999.999",
            "minimum_amount": "999.999",
            "maximum_amount": "999.999",
        },
        {
            "currency": "USD",
            "employee_count": 2,
            "average_amount": "0.25",
            "median_amount": "0.25",
            "minimum_amount": "0.125",
            "maximum_amount": "0.375",
        },
    ]


def test_department_salary_statistics_are_grouped_by_department_and_currency(
    client: TestClient,
    engine: Engine,
) -> None:
    add_employee(engine, index=1, department="Engineering", amount=Decimal("100.125"), currency="USD")
    add_employee(engine, index=2, department="Engineering", amount=Decimal("100.375"), currency="USD")
    add_employee(engine, index=3, department="Engineering", amount=Decimal("500"), currency="EUR")
    add_employee(engine, index=4, department="People", amount=Decimal("1000"), currency="EUR")

    body = client.get("/api/v1/insights/compensation").json()

    assert body["department_salary_by_currency"] == [
        {
            "department": "Engineering",
            "currency": "EUR",
            "employee_count": 1,
            "average_amount": "500",
            "median_amount": "500",
            "minimum_amount": "500",
            "maximum_amount": "500",
        },
        {
            "department": "Engineering",
            "currency": "USD",
            "employee_count": 2,
            "average_amount": "100.25",
            "median_amount": "100.25",
            "minimum_amount": "100.125",
            "maximum_amount": "100.375",
        },
        {
            "department": "People",
            "currency": "EUR",
            "employee_count": 1,
            "average_amount": "1000",
            "median_amount": "1000",
            "minimum_amount": "1000",
            "maximum_amount": "1000",
        },
    ]


def test_aggregations_run_in_six_database_queries(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index=1, amount=Decimal("10"))
    statements: list[str] = []

    def capture_statement(conn, cursor, statement, parameters, context, executemany) -> None:
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            statements.append(statement.upper())

    event.listen(engine, "before_cursor_execute", capture_statement)
    try:
        response = client.get("/api/v1/insights/compensation")
    finally:
        event.remove(engine, "before_cursor_execute", capture_statement)

    assert response.status_code == 200
    assert len(statements) == 6
    assert all("EMPLOYEES.EMPLOYEE_CODE" not in statement for statement in statements)
    assert sum("ROW_NUMBER() OVER" in statement for statement in statements) == 2
    assert all("GROUP BY" in statement for statement in statements[1:])


def test_postgresql_even_median_preserves_exact_decimal_precision(
    client: TestClient,
    engine: Engine,
) -> None:
    if engine.dialect.name != "postgresql":
        pytest.skip("Run with COMPENSATION_TEST_DATABASE_URL to verify PostgreSQL numeric aggregation")

    add_employee(engine, index=1, amount=Decimal("0.001"), currency="USD")
    add_employee(engine, index=2, amount=Decimal("0.002"), currency="USD")

    body = client.get("/api/v1/insights/compensation").json()

    assert body["salary_by_currency"] == [
        {
            "currency": "USD",
            "employee_count": 2,
            "average_amount": "0.0015",
            "median_amount": "0.0015",
            "minimum_amount": "0.001",
            "maximum_amount": "0.002",
        }
    ]
    assert body["department_salary_by_currency"][0]["median_amount"] == "0.0015"
