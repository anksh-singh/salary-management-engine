from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.compensation.router import router as compensation_router
from app.employees.router import router as employees_router
from app.insights.router import router as insights_router

app = FastAPI(title="Salary Management System API")
app.include_router(employees_router, prefix="/api/v1")
app.include_router(compensation_router, prefix="/api/v1")
app.include_router(insights_router, prefix="/api/v1")

_NOT_FOUND_ERRORS = {
    "employee_not_found": "Employee not found",
    "compensation_not_found": "Compensation not found",
}


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "code": error["type"],
        }
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "details": details,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = exc.detail.get("code") if isinstance(exc.detail, dict) else None
    if exc.status_code == 404 and code in _NOT_FOUND_ERRORS:
        error = {"code": code, "message": _NOT_FOUND_ERRORS[code]}
    else:
        error = {
            "code": "http_error",
            "message": "The request could not be completed",
        }
    return JSONResponse(status_code=exc.status_code, content={"error": error})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
