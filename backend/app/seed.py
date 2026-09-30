"""Generate and load the deterministic local assessment dataset."""

import argparse
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal
import random
from uuid import UUID, uuid5

from sqlalchemy import delete, insert
from sqlalchemy.orm import Session, sessionmaker

from app.compensation.models import Compensation
from app.database import SessionLocal
from app.employees.models import Employee

SEED_EMPLOYEE_COUNT = 10_000
BATCH_SIZE = 1_000
MISSING_COMPENSATION_INTERVAL = 20
RANDOM_SEED = 20_260_930
SEED_NAMESPACE = UUID("f106f75d-a9b4-41ca-85e4-b6cafaa1e101")
SEED_TIMESTAMP = datetime(2025, 1, 1, tzinfo=UTC)

FIRST_NAMES = (
    "Aarav", "Aisha", "Amelia", "Anika", "Arjun", "Ava", "Benjamin", "Charlotte", "Daniel", "Ethan",
    "Fatima", "Grace", "Hana", "Isabella", "James", "Kai", "Liam", "Maya", "Noah", "Olivia",
    "Priya", "Ravi", "Sofia", "Theo", "Zara",
)
LAST_NAMES = (
    "Anderson", "Bennett", "Brown", "Campbell", "Chen", "Clark", "Davis", "Evans", "Garcia", "Gupta",
    "Harris", "Ito", "Johnson", "Kim", "Kumar", "Martin", "Miller", "Nguyen", "Patel", "Robinson",
    "Singh", "Taylor", "Thomas", "Williams", "Wilson",
)

COUNTRY_DISTRIBUTION = (
    ("US", 24), ("GB", 10), ("IN", 18), ("DE", 8), ("FR", 7), ("CA", 7),
    ("AU", 6), ("SG", 4), ("JP", 4), ("BR", 4), ("NL", 4), ("ES", 4),
)
CURRENCY_BY_COUNTRY = {
    "US": "USD",
    "GB": "GBP",
    "IN": "INR",
    "DE": "EUR",
    "FR": "EUR",
    "CA": "CAD",
    "AU": "AUD",
    "SG": "SGD",
    "JP": "JPY",
    "BR": "BRL",
    "NL": "EUR",
    "ES": "EUR",
}

DEPARTMENTS = (
    ("Engineering", 22), ("Sales", 16), ("Product", 13), ("People", 10),
    ("Finance", 10), ("Marketing", 10), ("Operations", 10), ("Customer Support", 9),
)
ROLE_DISTRIBUTION = (45, 32, 16, 6, 1)
ROLES_BY_DEPARTMENT = {
    "Engineering": (
        ("Software Engineer", "entry"), ("Senior Software Engineer", "mid"),
        ("Staff Software Engineer", "senior"), ("Engineering Manager", "manager"),
        ("Engineering Director", "director"),
    ),
    "Sales": (
        ("Sales Development Representative", "entry"), ("Account Executive", "mid"),
        ("Senior Account Executive", "senior"), ("Sales Manager", "manager"),
        ("Sales Director", "director"),
    ),
    "Product": (
        ("Product Analyst", "entry"), ("Product Manager", "mid"),
        ("Senior Product Manager", "senior"), ("Group Product Manager", "manager"),
        ("Director of Product", "director"),
    ),
    "People": (
        ("People Coordinator", "entry"), ("HR Business Partner", "mid"),
        ("Senior HR Business Partner", "senior"), ("People Manager", "manager"),
        ("Director of People", "director"),
    ),
    "Finance": (
        ("Finance Analyst", "entry"), ("Accountant", "mid"),
        ("Senior Accountant", "senior"), ("Finance Manager", "manager"),
        ("Finance Director", "director"),
    ),
    "Marketing": (
        ("Marketing Coordinator", "entry"), ("Marketing Specialist", "mid"),
        ("Senior Marketing Specialist", "senior"), ("Marketing Manager", "manager"),
        ("Marketing Director", "director"),
    ),
    "Operations": (
        ("Operations Associate", "entry"), ("Operations Analyst", "mid"),
        ("Senior Operations Analyst", "senior"), ("Operations Manager", "manager"),
        ("Operations Director", "director"),
    ),
    "Customer Support": (
        ("Support Specialist", "entry"), ("Senior Support Specialist", "mid"),
        ("Support Lead", "senior"), ("Support Manager", "manager"),
        ("Support Director", "director"),
    ),
}

# Annual base salary ranges use each employee's local currency and are not cross-currency comparisons.
SALARY_BANDS = {
    "USD": {
        "entry": (52_000, 78_000), "mid": (75_000, 125_000), "senior": (115_000, 180_000),
        "manager": (130_000, 205_000), "director": (175_000, 265_000),
    },
    "GBP": {
        "entry": (28_000, 42_000), "mid": (40_000, 72_000), "senior": (68_000, 118_000),
        "manager": (78_000, 132_000), "director": (112_000, 178_000),
    },
    "INR": {
        "entry": (600_000, 1_200_000), "mid": (1_100_000, 2_300_000),
        "senior": (2_100_000, 4_000_000), "manager": (2_500_000, 4_800_000),
        "director": (3_800_000, 6_500_000),
    },
    "EUR": {
        "entry": (30_000, 48_000), "mid": (45_000, 82_000), "senior": (78_000, 135_000),
        "manager": (88_000, 150_000), "director": (128_000, 215_000),
    },
    "CAD": {
        "entry": (48_000, 76_000), "mid": (72_000, 125_000), "senior": (118_000, 188_000),
        "manager": (128_000, 200_000), "director": (170_000, 255_000),
    },
    "AUD": {
        "entry": (55_000, 84_000), "mid": (78_000, 132_000), "senior": (125_000, 195_000),
        "manager": (138_000, 210_000), "director": (180_000, 270_000),
    },
    "SGD": {
        "entry": (42_000, 72_000), "mid": (68_000, 122_000), "senior": (115_000, 185_000),
        "manager": (125_000, 205_000), "director": (170_000, 280_000),
    },
    "JPY": {
        "entry": (4_000_000, 6_500_000), "mid": (6_000_000, 10_000_000),
        "senior": (9_500_000, 16_000_000), "manager": (11_000_000, 18_000_000),
        "director": (15_000_000, 24_000_000),
    },
    "BRL": {
        "entry": (60_000, 105_000), "mid": (95_000, 180_000), "senior": (165_000, 285_000),
        "manager": (185_000, 320_000), "director": (260_000, 450_000),
    },
}


def generate_seed_data(
    employee_count: int = SEED_EMPLOYEE_COUNT,
) -> tuple[list[dict[str, object]], list[dict[str, object] | None]]:
    """Return stable employee and optional current-compensation rows."""
    if employee_count < 0:
        raise ValueError("employee_count cannot be negative")

    rng = random.Random(RANDOM_SEED)
    countries, country_weights = zip(*COUNTRY_DISTRIBUTION, strict=True)
    departments, department_weights = zip(*DEPARTMENTS, strict=True)
    employees: list[dict[str, object]] = []
    compensations: list[dict[str, object] | None] = []

    for sequence in range(1, employee_count + 1):
        employee_id = uuid5(SEED_NAMESPACE, f"employee:{sequence:05}")
        first_name = rng.choice(FIRST_NAMES)
        last_name = rng.choice(LAST_NAMES)
        employee_code = f"EMP-{sequence:05}"
        country = rng.choices(countries, weights=country_weights, k=1)[0]
        department = rng.choices(departments, weights=department_weights, k=1)[0]
        role_index = rng.choices(range(len(ROLE_DISTRIBUTION)), weights=ROLE_DISTRIBUTION, k=1)[0]
        job_title, salary_level = ROLES_BY_DEPARTMENT[department][role_index]
        currency = CURRENCY_BY_COUNTRY[country]
        minimum, maximum = SALARY_BANDS[currency][salary_level]

        employees.append(
            {
                "id": employee_id,
                "employee_code": employee_code,
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{first_name}.{last_name}.{sequence:05}@example.test".lower(),
                "country": country,
                "department": department,
                "job_title": job_title,
                "created_at": SEED_TIMESTAMP,
                "updated_at": SEED_TIMESTAMP,
            }
        )

        if sequence % MISSING_COMPENSATION_INTERVAL == 0:
            compensations.append(None)
        else:
            compensations.append(
                {
                    "employee_id": employee_id,
                    "amount": Decimal(rng.randint(minimum, maximum)),
                    "currency": currency,
                    "created_at": SEED_TIMESTAMP,
                    "updated_at": SEED_TIMESTAMP,
                }
            )

    return employees, compensations


def seed_database(
    session_factory: sessionmaker[Session] = SessionLocal,
    *,
    employee_count: int = SEED_EMPLOYEE_COUNT,
    batch_size: int = BATCH_SIZE,
) -> tuple[int, int]:
    """Replace all employee and compensation data in one transaction."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    employees, compensations = generate_seed_data(employee_count)
    seeded_compensation_count = sum(compensation is not None for compensation in compensations)

    with session_factory.begin() as session:
        session.execute(delete(Compensation))
        session.execute(delete(Employee))
        for start in range(0, employee_count, batch_size):
            stop = start + batch_size
            session.execute(insert(Employee), employees[start:stop])
            compensation_batch = [row for row in compensations[start:stop] if row is not None]
            if compensation_batch:
                session.execute(insert(Compensation), compensation_batch)

    return employee_count, seeded_compensation_count


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Replace local employee data with the deterministic 10,000-person dataset."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        required=True,
        help="confirm that all existing employees and compensation records should be deleted first",
    )
    parser.parse_args(argv)

    employee_count, compensation_count = seed_database()
    print(
        f"Seeded {employee_count} employees and {compensation_count} current compensation records "
        f"({employee_count - compensation_count} employees without compensation)."
    )


if __name__ == "__main__":
    main()
