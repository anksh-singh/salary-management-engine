from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.api.schemas import ApiErrorResponse
from app.compensation.models import Compensation
from app.compensation.schemas import CompensationResponse, CompensationWriteRequest
from app.database import get_session
from app.employees.models import Employee

router = APIRouter(prefix="/employees/{employee_id}/compensation", tags=["compensation"])


@router.get(
    "",
    response_model=CompensationResponse,
    responses={404: {"model": ApiErrorResponse}, 422: {"model": ApiErrorResponse}},
)
def get_compensation(
    employee_id: UUID,
    session: Session = Depends(get_session),
) -> CompensationResponse:
    employee = session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "employee_not_found", "message": "Employee not found"},
        )

    compensation = session.get(Compensation, employee_id)
    if compensation is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "compensation_not_found", "message": "Compensation not found"},
        )
    return CompensationResponse.model_validate(compensation)


@router.put(
    "",
    response_model=CompensationResponse,
    responses={404: {"model": ApiErrorResponse}, 422: {"model": ApiErrorResponse}},
)
def set_compensation(
    employee_id: UUID,
    request: CompensationWriteRequest,
    session: Session = Depends(get_session),
) -> CompensationResponse:
    with session.begin():
        employee = session.get(Employee, employee_id)
        if employee is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "employee_not_found", "message": "Employee not found"},
            )

        dialect_name = session.get_bind().dialect.name
        if dialect_name == "postgresql":
            insert = postgresql_insert(Compensation)
        elif dialect_name == "sqlite":
            insert = sqlite_insert(Compensation)
        else:
            raise RuntimeError(f"Compensation upsert is not supported for {dialect_name}")

        insert = insert.values(
            employee_id=employee_id,
            amount=request.amount,
            currency=request.currency,
        )
        changed = or_(
            Compensation.amount.is_distinct_from(insert.excluded.amount),
            Compensation.currency.is_distinct_from(insert.excluded.currency),
        )
        statement = insert.on_conflict_do_update(
            index_elements=[Compensation.employee_id],
            set_={
                "amount": insert.excluded.amount,
                "currency": insert.excluded.currency,
                "updated_at": case((changed, func.now()), else_=Compensation.updated_at),
            },
        ).returning(Compensation)
        compensation = session.scalars(statement).one()
        response = CompensationResponse.model_validate(compensation)

    return response
