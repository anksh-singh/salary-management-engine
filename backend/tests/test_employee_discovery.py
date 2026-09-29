from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

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


def add_employee(engine: Engine, **overrides: str) -> Employee:
    index = overrides.pop("index", "001")
    values = {
        "employee_code": f"EMP-{index}",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": f"ada{index}@example.test",
        "country": "GB",
        "department": "Engineering",
        "job_title": "Analyst",
        **overrides,
    }
    employee = Employee(**values)
    with Session(engine) as session:
        session.add(employee)
        session.commit()
        session.refresh(employee)
    return employee


def test_list_employees_returns_default_page_and_total(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="002")
    add_employee(engine, index="001")

    response = client.get("/api/v1/employees")

    assert response.status_code == 200
    body = response.json()
    assert [item["employee_code"] for item in body["items"]] == ["EMP-001", "EMP-002"]
    assert body["pagination"] == {"page": 1, "page_size": 25, "total": 2, "total_pages": 1}


def test_list_employees_paginates_in_stable_order(client: TestClient, engine: Engine) -> None:
    for index in range(1, 6):
        add_employee(engine, index=f"{index:03}")

    response = client.get("/api/v1/employees?page=2&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert [item["employee_code"] for item in body["items"]] == ["EMP-003", "EMP-004"]
    assert body["pagination"] == {"page": 2, "page_size": 2, "total": 5, "total_pages": 3}


def test_page_size_accepts_maximum_of_100(client: TestClient, engine: Engine) -> None:
    add_employee(engine)

    response = client.get("/api/v1/employees?page_size=100")

    assert response.status_code == 200
    assert response.json()["pagination"]["page_size"] == 100


@pytest.mark.parametrize(
    "search",
    ["EMP-001", "Ada", "Lovelace", "ada001@example.test"],
)
def test_search_matches_each_supported_field(client: TestClient, engine: Engine, search: str) -> None:
    add_employee(engine)
    add_employee(engine, index="002", first_name="Grace", last_name="Hopper", email="grace@example.test")

    response = client.get("/api/v1/employees", params={"search": search})

    assert response.status_code == 200
    assert [item["employee_code"] for item in response.json()["items"]] == ["EMP-001"]


def test_search_treats_percent_as_a_literal_character(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001", first_name="Ava%100")
    add_employee(engine, index="002", first_name="AvaX100")

    response = client.get("/api/v1/employees", params={"search": "ava%100"})

    assert response.status_code == 200
    assert [item["employee_code"] for item in response.json()["items"]] == ["EMP-001"]


def test_search_treats_underscore_as_a_literal_character(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001", first_name="Ava_100")
    add_employee(engine, index="002", first_name="AvaX100")

    response = client.get("/api/v1/employees", params={"search": "Ava_100"})

    assert response.status_code == 200
    assert [item["employee_code"] for item in response.json()["items"]] == ["EMP-001"]


def test_search_with_no_matches_returns_empty_page(client: TestClient, engine: Engine) -> None:
    add_employee(engine)

    response = client.get("/api/v1/employees", params={"search": "nobody-matches"})

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "pagination": {"page": 1, "page_size": 25, "total": 0, "total_pages": 0},
    }


def test_country_filter_is_exact(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001", country="GB")
    add_employee(engine, index="002", country="US")

    response = client.get("/api/v1/employees", params={"country": "US"})

    assert [item["employee_code"] for item in response.json()["items"]] == ["EMP-002"]


def test_department_filter_is_exact(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001", department="Engineering")
    add_employee(engine, index="002", department="People")

    response = client.get("/api/v1/employees", params={"department": "People"})

    assert [item["employee_code"] for item in response.json()["items"]] == ["EMP-002"]


def test_job_title_filter_is_exact(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001", job_title="Analyst")
    add_employee(engine, index="002", job_title="Manager")

    response = client.get("/api/v1/employees", params={"job_title": "Manager"})

    assert [item["employee_code"] for item in response.json()["items"]] == ["EMP-002"]


def test_search_and_filters_combine_and_count_matching_rows(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001", first_name="Ada", country="GB", department="Engineering")
    add_employee(engine, index="002", first_name="Ada", country="US", department="Engineering")
    add_employee(
        engine,
        index="003",
        first_name="Grace",
        email="grace@example.test",
        country="GB",
        department="Engineering",
    )
    add_employee(engine, index="004", first_name="Ada", country="GB", department="People")

    response = client.get(
        "/api/v1/employees",
        params={"search": "ada", "country": "GB", "department": "Engineering", "job_title": "Analyst"},
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["employee_code"] for item in body["items"]] == ["EMP-001"]
    assert body["pagination"]["total"] == 1


def test_filters_count_and_page_are_executed_in_database(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001", department="Engineering")
    add_employee(engine, index="002", department="Engineering")
    statements: list[str] = []
    event.listen(engine, "before_cursor_execute", lambda conn, cursor, sql, params, context, many: statements.append(sql))

    response = client.get("/api/v1/employees", params={"department": "Engineering", "page": 2, "page_size": 1})

    assert response.status_code == 200
    selects = [sql.upper() for sql in statements if sql.lstrip().upper().startswith("SELECT")]
    assert any("COUNT(EMPLOYEES.ID)" in sql and "WHERE EMPLOYEES.DEPARTMENT" in sql for sql in selects)
    assert any("WHERE EMPLOYEES.DEPARTMENT" in sql and "LIMIT" in sql and "OFFSET" in sql for sql in selects)


def test_beyond_last_page_skips_paginated_query(client: TestClient, engine: Engine) -> None:
    add_employee(engine, index="001")
    add_employee(engine, index="002")
    statements: list[str] = []

    def capture_statement(conn, cursor, sql, params, context, executemany) -> None:
        statements.append(sql)

    event.listen(engine, "before_cursor_execute", capture_statement)
    response = client.get(
        "/api/v1/employees",
        params={"page": "999999999999999999999999999999", "page_size": 1},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "pagination": {
            "page": 999999999999999999999999999999,
            "page_size": 1,
            "total": 2,
            "total_pages": 2,
        },
    }
    selects = [sql.upper() for sql in statements if sql.lstrip().upper().startswith("SELECT")]
    assert len(selects) == 1
    assert "COUNT(EMPLOYEES.ID)" in selects[0]
    assert "LIMIT" not in selects[0]
    assert "OFFSET" not in selects[0]


def test_employee_detail_returns_employee(client: TestClient, engine: Engine) -> None:
    employee = add_employee(engine)

    response = client.get(f"/api/v1/employees/{employee.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(employee.id)
    assert response.json()["employee_code"] == "EMP-001"


def test_employee_detail_returns_consistent_not_found_response(client: TestClient) -> None:
    response = client.get(f"/api/v1/employees/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "employee_not_found", "message": "Employee not found"}
    }


@pytest.mark.parametrize(
    "params",
    [
        {"page": "0"},
        {"page": "invalid"},
        {"page_size": "0"},
        {"page_size": "101"},
        {"search": ""},
        {"country": ""},
        {"department": ""},
        {"job_title": ""},
    ],
)
def test_invalid_list_parameters_return_validation_error(client: TestClient, params: dict[str, str]) -> None:
    response = client.get("/api/v1/employees", params=params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"]


def test_validation_error_uses_consistent_error_contract(client: TestClient) -> None:
    response = client.get("/api/v1/employees", params={"page_size": "101"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert set(error) == {"code", "message", "details"}
    assert error["code"] == "validation_error"
    assert error["message"] == "Request validation failed"
    assert error["details"][0]["field"] == "query.page_size"
    assert error["details"][0]["code"] == "less_than_equal"
    assert "input" not in error["details"][0]
