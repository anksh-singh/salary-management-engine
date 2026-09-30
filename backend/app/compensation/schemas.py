from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class CompensationWriteRequest(BaseModel):
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")

    @field_validator("amount", mode="before", json_schema_input_type=str)
    @classmethod
    def parse_decimal_string(cls, value: object) -> Decimal:
        if not isinstance(value, str):
            raise ValueError("Amount must be a decimal string")
        try:
            return Decimal(value)
        except InvalidOperation as error:
            raise ValueError("Amount must be a valid decimal string") from error

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        if not value.is_finite():
            raise ValueError("Amount must be finite")
        if value <= 0:
            raise ValueError("Amount must be greater than zero")
        if max(0, -value.as_tuple().exponent) > 3:
            raise ValueError("Amount must have no more than 3 fractional digits")
        if value.adjusted() >= 12:
            raise ValueError("Amount exceeds the supported precision")
        return value


class CompensationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: UUID
    amount: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime

    @field_serializer("amount")
    def serialize_amount(self, amount: Decimal) -> str:
        serialized = format(amount, "f")
        if "." in serialized:
            serialized = serialized.rstrip("0").rstrip(".")
        return serialized
