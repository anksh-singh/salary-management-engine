from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.schemas import ApiErrorResponse
from app.database import get_session
from app.employees.models import Employee
from app.employees.schemas import (
    EmployeeListResponse,
    EmployeePagination,
    EmployeeResponse,
)

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=EmployeeListResponse, responses={422: {"model": ApiErrorResponse}})
def list_employees(
    search: str | None = Query(default=None, min_length=1),
    country: str | None = Query(default=None, min_length=1),
    department: str | None = Query(default=None, min_length=1),
    job_title: str | None = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    session: Session = Depends(get_session),
) -> EmployeeListResponse:
    statement = select(Employee)
    count_statement = select(func.count(Employee.id))
    conditions = []

    if search is not None:
        escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped_search}%"
        conditions.append(
            or_(
                Employee.employee_code.ilike(pattern, escape="\\"),
                Employee.first_name.ilike(pattern, escape="\\"),
                Employee.last_name.ilike(pattern, escape="\\"),
                Employee.email.ilike(pattern, escape="\\"),
            )
        )
    if country is not None:
        conditions.append(Employee.country == country)
    if department is not None:
        conditions.append(Employee.department == department)
    if job_title is not None:
        conditions.append(Employee.job_title == job_title)

    if conditions:
        statement = statement.where(*conditions)
        count_statement = count_statement.where(*conditions)

    total = session.scalar(count_statement) or 0
    offset = (page - 1) * page_size
    employees: list[Employee] = []
    if offset < total:
        employees = session.scalars(
            statement.order_by(Employee.employee_code, Employee.id).offset(offset).limit(page_size)
        ).all()

    return EmployeeListResponse(
        items=employees,
        pagination=EmployeePagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size),
        ),
    )


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    responses={404: {"model": ApiErrorResponse}, 422: {"model": ApiErrorResponse}},
)
def get_employee(employee_id: UUID, session: Session = Depends(get_session)) -> EmployeeResponse:
    employee = session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "employee_not_found", "message": "Employee not found"},
        )
    return EmployeeResponse.model_validate(employee)
