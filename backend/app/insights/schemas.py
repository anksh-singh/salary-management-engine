from decimal import Decimal

from pydantic import BaseModel, field_serializer


class CompensationCoverage(BaseModel):
    total_employee_count: int
    employees_with_compensation: int
    employees_without_compensation: int


class EmployeeCountBreakdown(BaseModel):
    employee_count: int
    employees_with_compensation: int


class CountryEmployeeBreakdown(EmployeeCountBreakdown):
    country: str


class DepartmentEmployeeBreakdown(EmployeeCountBreakdown):
    department: str


class JobTitleEmployeeBreakdown(EmployeeCountBreakdown):
    job_title: str


class EmployeeBreakdowns(BaseModel):
    by_country: list[CountryEmployeeBreakdown]
    by_department: list[DepartmentEmployeeBreakdown]
    by_job_title: list[JobTitleEmployeeBreakdown]


class SalaryStatistics(BaseModel):
    employee_count: int
    average_amount: Decimal
    median_amount: Decimal
    minimum_amount: Decimal
    maximum_amount: Decimal

    @field_serializer("average_amount", "median_amount", "minimum_amount", "maximum_amount")
    def serialize_amount(self, amount: Decimal) -> str:
        serialized = format(amount, "f")
        if "." in serialized:
            serialized = serialized.rstrip("0").rstrip(".")
        return serialized


class CurrencySalaryStatistics(SalaryStatistics):
    currency: str


class DepartmentCurrencySalaryStatistics(SalaryStatistics):
    department: str
    currency: str


class CompensationInsightsResponse(BaseModel):
    coverage: CompensationCoverage
    salary_by_currency: list[CurrencySalaryStatistics]
    employee_breakdowns: EmployeeBreakdowns
    department_salary_by_currency: list[DepartmentCurrencySalaryStatistics]
