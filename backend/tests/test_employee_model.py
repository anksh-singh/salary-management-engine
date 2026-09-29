from collections.abc import Iterator
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.employees.models import Employee


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session
    Base.metadata.drop_all(engine)
    engine.dispose()


def employee_values(**overrides: object) -> dict[str, object]:
    return {
        "employee_code": "EMP-001",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.test",
        "country": "GB",
        "department": "Engineering",
        "job_title": "Analyst",
        **overrides,
    }


def add_employee(session: Session, **overrides: object) -> Employee:
    employee = Employee(**employee_values(**overrides))
    session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


def test_employee_can_be_created_with_generated_identity_and_timestamps(session: Session) -> None:
    employee = add_employee(session)

    assert isinstance(employee.id, UUID)
    assert employee.employee_code == "EMP-001"
    assert employee.first_name == "Ada"
    assert employee.last_name == "Lovelace"
    assert employee.email == "ada@example.test"
    assert employee.country == "GB"
    assert employee.department == "Engineering"
    assert employee.job_title == "Analyst"
    assert employee.created_at is not None
    assert employee.updated_at is not None


def test_employee_code_must_be_unique(session: Session) -> None:
    add_employee(session)
    session.add(Employee(**employee_values(email="grace@example.test")))

    with pytest.raises(IntegrityError):
        session.commit()


def test_email_must_be_unique_case_insensitively(session: Session) -> None:
    add_employee(session)
    session.add(Employee(**employee_values(employee_code="EMP-002", email="ADA@example.test")))

    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize(
    "field",
    ["employee_code", "first_name", "last_name", "email", "country", "department", "job_title"],
)
def test_required_fields_cannot_be_null(session: Session, field: str) -> None:
    session.add(Employee(**employee_values(**{field: None})))

    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize("field", ["employee_code", "first_name", "last_name", "email", "department", "job_title"])
def test_required_text_fields_cannot_be_blank(session: Session, field: str) -> None:
    session.add(Employee(**employee_values(**{field: "  "})))

    with pytest.raises(IntegrityError):
        session.commit()


@pytest.mark.parametrize("country", ["usa", "USA", "u1", "U1"])
def test_country_must_be_an_uppercase_two_letter_code(session: Session, country: str) -> None:
    session.add(Employee(**employee_values(country=country)))

    with pytest.raises(IntegrityError):
        session.commit()
