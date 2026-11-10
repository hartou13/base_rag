import asyncio
from datetime import datetime
import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.auth.services.auth_service import checkToken
from src.database.mysql_global import set_ip_address
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
import bcrypt
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
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    token = None
    
    while True:
        try:
            await database.connect()
            print("Connected to MySQL database", flush=True)
            break  # Si la connexion est réussie, sortez de la boucle
        except Exception as e:
            raise e
            print(f"Error connecting to MySQL database: {e}", flush=True)
            await asyncio.sleep(5)  # Attendez 5 secondes avant de réessayer

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
            headers={"Access-Control-Allow-Origin": "*"},
        )
    non_protected_url = [
        "/auth/login",
        "/auth/sign-up",
    ]

    if (
        request.url.path not in non_protected_url
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
                    headers={"Access-Control-Allow-Origin": "*"},
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Token is missing"},
                headers={"Access-Control-Allow-Origin": "*"},
            )
    response = await call_next(request)
    # origin = request.headers.get("origin")
    return response


if os.getenv("ENV") == "prod":
    app.add_middleware(HTTPSRedirectMiddleware)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    print("Disconnecting from database")

def hash_password(password: str):
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


print(hash_password("password"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
