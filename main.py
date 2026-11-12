import asyncio
from datetime import datetime
import os
import re
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.auth.services.auth_service import checkToken
from src.database.mysql_global import set_ip_address
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.security.utils import get_authorization_scheme_param
from src.users.services.user_service import current_user_token_var, current_user_var
set_ip_address()


from src.auth.routers import auth_router
from src.users.routers import user_router
from src.collections.routers import collection_router
from src.collections.routers import file_router
from src.sessions.routers import session_router
from src.chat.routers import chat_router
from src.database.mysql_connector import database
from src.core.logging_setup import get_logger, setup_logging
from src.logs.services.log_service import purge_old_logs
from src.rag.services import rag_config as cfg
setup_logging()
logger = get_logger("app")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


def _cors_headers(request: Request) -> dict:
    origin = request.headers.get("origin")
    return {"Access-Control-Allow-Origin": origin} if origin in cfg.CORS_ORIGINS else {}


async def _purge_logs_forever():
    while True:
        try:
            removed = await purge_old_logs(cfg.LOG_RETENTION_DAYS)
            logger.info("log purge done, %s rows removed", removed)
        except Exception as e:
            logger.error("log purge failed: %s", e)
        await asyncio.sleep(24 * 3600)


@app.on_event("startup")
async def startup():
    if len(cfg.FILE_URL_SECRET) < 32:
        raise RuntimeError("FILE_URL_SECRET must be set (at least 32 characters) to sign download URLs")
    token = None

    while True:
        try:
            await database.connect()
            logger.info("Connected to MySQL database")
            break  # Si la connexion est réussie, sortez de la boucle
        except Exception as e:
            raise e
    asyncio.create_task(_purge_logs_forever())

#router inclusion
app.include_router(auth_router.router)
app.include_router(user_router.router)
app.include_router(collection_router.router)
app.include_router(file_router.router)
app.include_router(session_router.router)
app.include_router(chat_router.router)

@app.middleware("http")
async def verify_token(request: Request, call_next):
    # print(request)
    # print(request.url)
    # print(request.url.path)
    # print(request.headers)

    if request.method == "OPTIONS":
        return await call_next(request)

    if request.url.path == "/health-check":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "MyAuxilium OK"},
            headers=_cors_headers(request),
        )
    non_protected_url = [
        "/auth/login",
        "/auth/sign-up",
    ]
    # Signed download URLs carry no Bearer header; the route itself verifies signature, expiry and owner.
    is_signed_download = (
        request.method == "GET"
        and "sig" in request.query_params
        and "Authorization" not in request.headers
        and re.fullmatch(r"/files/[^/]+/content", request.url.path) is not None
    )

    if (
        request.url.path not in non_protected_url and not is_signed_download
    ):
        token = None
        if "Authorization" in request.headers:
            scheme, param = get_authorization_scheme_param(
                request.headers["Authorization"]
            )
            if scheme.lower() == "bearer":
                token = param

        if token:
            try:
                user_id = await checkToken(token)
                current_user_var.set(user_id)
                current_user_token_var.set(token)
            except HTTPException as e:
                return JSONResponse(
                    status_code=e.status_code,
                    content={"message": e.detail},
                    headers=_cors_headers(request),
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Token is missing"},
                headers=_cors_headers(request),
            )
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("X-Frame-Options", "DENY")
    return response


if os.getenv("ENV") == "prod":
    app.add_middleware(HTTPSRedirectMiddleware)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("Disconnecting from database")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
