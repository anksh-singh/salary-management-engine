from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_code: str
    first_name: str
    last_name: str
    email: str
    country: str
    department: str
    job_title: str
    created_at: datetime
    updated_at: datetime


class EmployeePagination(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class EmployeeListResponse(BaseModel):
    items: list[EmployeeResponse]
    pagination: EmployeePagination
