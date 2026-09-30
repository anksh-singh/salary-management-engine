from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import ColumnElement, case, func, select
from sqlalchemy.orm import Session

from app.compensation.models import Compensation
from app.database import get_session
from app.employees.models import Employee
from app.insights.schemas import (
    CompensationCoverage,
    CompensationInsightsResponse,
    CountryEmployeeBreakdown,
    CurrencySalaryStatistics,
    DepartmentCurrencySalaryStatistics,
    DepartmentEmployeeBreakdown,
    EmployeeBreakdowns,
    JobTitleEmployeeBreakdown,
)

router = APIRouter(prefix="/insights", tags=["compensation insights"])


def _employee_counts_by(
    session: Session,
    dimension: ColumnElement[str],
) -> list[tuple[str, int, int]]:
    statement = (
        select(
            dimension.label("dimension"),
            func.count(Employee.id).label("employee_count"),
            func.count(Compensation.employee_id).label("employees_with_compensation"),
        )
        .select_from(Employee)
        .outerjoin(Compensation, Compensation.employee_id == Employee.id)
        .group_by(dimension)
        .order_by(dimension)
    )
    return [(row.dimension, row.employee_count, row.employees_with_compensation) for row in session.execute(statement)]


def _salary_statistics(
    session: Session,
    group_columns: tuple[ColumnElement[str], ...],
    group_names: tuple[str, ...],
) -> list[tuple[tuple[str, ...], int, Decimal, Decimal, Decimal, Decimal]]:
    ranked = (
        select(
            *(column.label(name) for column, name in zip(group_columns, group_names, strict=True)),
            Compensation.amount.label("amount"),
            func.row_number()
            .over(partition_by=group_columns, order_by=Compensation.amount)
            .label("salary_position"),
            func.count()
            .over(partition_by=group_columns)
            .label("group_size"),
        )
        .select_from(Compensation)
        .join(Employee, Employee.id == Compensation.employee_id)
        .cte("ranked_compensation")
    )
    # The center position has distance 0 for odd groups and ±1 for even groups.
    middle_rows = func.abs(2 * ranked.c.salary_position - ranked.c.group_size - 1) <= 1
    grouping = tuple(ranked.c[name] for name in group_names)
    statement = (
        select(
            *grouping,
            func.count(ranked.c.amount).label("employee_count"),
            func.avg(ranked.c.amount).label("average_amount"),
            func.avg(case((middle_rows, ranked.c.amount))).label("median_amount"),
            func.min(ranked.c.amount).label("minimum_amount"),
            func.max(ranked.c.amount).label("maximum_amount"),
        )
        .group_by(*grouping)
        .order_by(*grouping)
    )
    return [
        (
            tuple(row._mapping[name] for name in group_names),
            row.employee_count,
            row.average_amount,
            row.median_amount,
            row.minimum_amount,
            row.maximum_amount,
        )
        for row in session.execute(statement)
    ]


@router.get("/compensation", response_model=CompensationInsightsResponse)
def get_compensation_insights(
    session: Session = Depends(get_session),
) -> CompensationInsightsResponse:
    total_employee_count, employees_with_compensation = session.execute(
        select(
            func.count(Employee.id),
            func.count(Compensation.employee_id),
        ).select_from(Employee).outerjoin(Compensation, Compensation.employee_id == Employee.id)
    ).one()

    country_counts = _employee_counts_by(session, Employee.country)
    department_counts = _employee_counts_by(session, Employee.department)
    job_title_counts = _employee_counts_by(session, Employee.job_title)

    currency_statistics = _salary_statistics(
        session,
        (Compensation.currency,),
        ("currency",),
    )
    department_currency_statistics = _salary_statistics(
        session,
        (Employee.department, Compensation.currency),
        ("department", "currency"),
    )

    return CompensationInsightsResponse(
        coverage=CompensationCoverage(
            total_employee_count=total_employee_count,
            employees_with_compensation=employees_with_compensation,
            employees_without_compensation=total_employee_count - employees_with_compensation,
        ),
        salary_by_currency=[
            CurrencySalaryStatistics(
                currency=groups[0],
                employee_count=count,
                average_amount=average,
                median_amount=median,
                minimum_amount=minimum,
                maximum_amount=maximum,
            )
            for groups, count, average, median, minimum, maximum in currency_statistics
        ],
        employee_breakdowns=EmployeeBreakdowns(
            by_country=[
                CountryEmployeeBreakdown(
                    country=dimension,
                    employee_count=count,
                    employees_with_compensation=compensated,
                )
                for dimension, count, compensated in country_counts
            ],
            by_department=[
                DepartmentEmployeeBreakdown(
                    department=dimension,
                    employee_count=count,
                    employees_with_compensation=compensated,
                )
                for dimension, count, compensated in department_counts
            ],
            by_job_title=[
                JobTitleEmployeeBreakdown(
                    job_title=dimension,
                    employee_count=count,
                    employees_with_compensation=compensated,
                )
                for dimension, count, compensated in job_title_counts
            ],
        ),
        department_salary_by_currency=[
            DepartmentCurrencySalaryStatistics(
                department=groups[0],
                currency=groups[1],
                employee_count=count,
                average_amount=average,
                median_amount=median,
                minimum_amount=minimum,
                maximum_amount=maximum,
            )
            for groups, count, average, median, minimum, maximum in department_currency_statistics
        ],
    )
