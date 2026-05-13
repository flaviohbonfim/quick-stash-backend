from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import Base, engine
from api.routers.users import router as users_router
from api.routers.auth import router as auth_router
from api.routers.payment_methods import router as payment_methods_router
from api.routers.transactions import router as transactions_router


app = FastAPI(title="Users CRUD API", version="1.0.0")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        from models.user import User  # noqa: F401
        from models.payment_method import PaymentMethod  # noqa: F401
        from models.transaction import Transaction  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "https://quickstash.apti.dev",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(auth_router)
app.include_router(payment_methods_router)
app.include_router(transactions_router)


_original_openapi = app.openapi


def custom_openapi():
    schema = _original_openapi()
    if "components" not in schema:
        schema["components"] = {}
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path, path_item in schema.get("paths", {}).items():
        for method in ["get", "post", "put", "delete", "patch"]:
            operation = path_item.get(method)
            if not operation:
                continue
            security = operation.get("security")
            if security is None:
                continue
            new_security = []
            for req in security:
                if "OAuth2PasswordBearer" in req:
                    new_security.append({"BearerAuth": []})
                else:
                    new_security.append(req)
            if new_security:
                operation["security"] = new_security
            else:
                operation.pop("security", None)
    return schema


app.openapi = custom_openapi