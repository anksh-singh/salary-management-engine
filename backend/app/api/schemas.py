from pydantic import BaseModel


class ApiErrorDetail(BaseModel):
    field: str
    message: str
    code: str


class ApiError(BaseModel):
    code: str
    message: str
    details: list[ApiErrorDetail] | None = None


class ApiErrorResponse(BaseModel):
    error: ApiError
