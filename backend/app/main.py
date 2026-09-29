from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.employees.router import router as employees_router

app = FastAPI(title="Salary Management System API")
app.include_router(employees_router, prefix="/api/v1")


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
    employee_not_found = {
        "code": "employee_not_found",
        "message": "Employee not found",
    }
    if exc.status_code == 404 and exc.detail == employee_not_found:
        error = employee_not_found
    else:
        error = {
            "code": "http_error",
            "message": "The request could not be completed",
        }
    return JSONResponse(status_code=exc.status_code, content={"error": error})


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
