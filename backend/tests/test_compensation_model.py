from collections.abc import Iterator
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.compensation.models import Compensation
from app.database import Base
from app.employees.models import Employee


@pytest.fixture
def engine() -> Iterator[Engine]:
    test_engine = create_engine("sqlite://")

    @event.listens_for(test_engine, "connect")
    def enable_foreign_keys(connection, record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(test_engine)
    yield test_engine
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()


def add_employee(session: Session) -> Employee:
    employee = Employee(
        employee_code="EMP-001",
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.test",
        country="GB",
        department="Engineering",
        job_title="Analyst",
    )
    session.add(employee)
    session.flush()
    return employee


def test_compensation_persists_exact_decimal_and_timestamps(engine: Engine) -> None:
    with Session(engine) as session:
        employee = add_employee(session)
        compensation = Compensation(
            employee_id=employee.id,
            amount=Decimal("85000.125"),
            currency="USD",
        )
        session.add(compensation)
        session.commit()
        session.refresh(compensation)

        assert compensation.amount == Decimal("85000.125")
        assert compensation.currency == "USD"
        assert compensation.created_at is not None
        assert compensation.updated_at is not None


def test_employee_id_allows_at_most_one_compensation(engine: Engine) -> None:
    with Session(engine) as session:
        employee = add_employee(session)
        session.add(Compensation(employee_id=employee.id, amount=Decimal("1"), currency="USD"))
        session.commit()
        session.add(Compensation(employee_id=employee.id, amount=Decimal("2"), currency="USD"))

        with pytest.raises(IntegrityError):
            session.commit()


def test_compensation_requires_an_existing_employee(engine: Engine) -> None:
    with Session(engine) as session:
        session.add(Compensation(employee_id=uuid4(), amount=Decimal("1"), currency="USD"))

        with pytest.raises(IntegrityError):
            session.commit()


def test_employee_delete_is_rejected_while_compensation_exists(engine: Engine) -> None:
    with Session(engine) as session:
        employee = add_employee(session)
        employee_id = employee.id
        session.add(Compensation(employee_id=employee_id, amount=Decimal("1"), currency="USD"))
        session.commit()

        session.delete(employee)
        with pytest.raises(IntegrityError):
            session.commit()

        session.rollback()
        assert session.get(Compensation, employee_id) is not None


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-0.001")])
def test_compensation_amount_must_be_positive(engine: Engine, amount: Decimal) -> None:
    with Session(engine) as session:
        employee = add_employee(session)
        session.add(Compensation(employee_id=employee.id, amount=amount, currency="USD"))

        with pytest.raises(IntegrityError):
            session.commit()


@pytest.mark.parametrize("currency", ["usd", "US", "U$D", "123"])
def test_currency_must_be_three_uppercase_ascii_letters(engine: Engine, currency: str) -> None:
    with Session(engine) as session:
        employee = add_employee(session)
        session.add(Compensation(employee_id=employee.id, amount=Decimal("1"), currency=currency))

        with pytest.raises(IntegrityError):
            session.commit()
