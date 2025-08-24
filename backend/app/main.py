from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import create_all_tables


def get_application() -> FastAPI:
    app = FastAPI(title="SG Indicadores", version="1.0.0", openapi_url="/api/v1/openapi.json")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers will be included after they are implemented
    from app.api.v1.routers import auth, users, datasets, kpis, metas

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
    app.include_router(kpis.router, prefix="/api/v1/kpis", tags=["kpis"])
    app.include_router(metas.router, prefix="/api/v1/metas", tags=["metas"])

    @app.on_event("startup")
    def on_startup() -> None:
        create_all_tables()

    return app


app = get_application()
