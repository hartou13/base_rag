from datetime import datetime, timedelta, timezone
import json
import os
from typing import Optional
import bcrypt
from fastapi import HTTPException
from sqlalchemy import delete, insert, select
from src.database.mysql_connector import get_db
from src.logs.models.log import ActionType, LogTypes
from src.logs.services.log_service import create_log
from src.users.models.user import User
from src.users.models.user_active_token import UserActiveToken
import jwt
from fastapi import Depends, HTTPException, status


JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM")
JWT_SECRET = os.environ.get("JWT_SECRET")
TOKEN_EXPIRATION_TIME = os.environ.get("JWT_EXPIRACY")
if TOKEN_EXPIRATION_TIME.endswith('d'):
    TOKEN_EXPIRATION_TIME = timedelta(days=int(TOKEN_EXPIRATION_TIME[:-1]))
elif TOKEN_EXPIRATION_TIME.endswith('h'):
    TOKEN_EXPIRATION_TIME = timedelta(hours=int(TOKEN_EXPIRATION_TIME[:-1]))
elif TOKEN_EXPIRATION_TIME.endswith('m'):
    TOKEN_EXPIRATION_TIME = timedelta(minutes=int(TOKEN_EXPIRATION_TIME[:-1]))
elif TOKEN_EXPIRATION_TIME.endswith('s'):
    TOKEN_EXPIRATION_TIME = timedelta(seconds=int(TOKEN_EXPIRATION_TIME[:-1]))
else:
    raise ValueError(f"Invalid expiration time: {TOKEN_EXPIRATION_TIME}")


async def authenticate_user(email: str, password: str):
    async with get_db() as session:
        # Create a select query for the Item based on the provided item_id
        stmt = select(User).where(User.email == email)
        # Execute the query asynchronously
        result = await session.execute(stmt)
        # Fetch the first row returned by the query
        item = result.scalars().first()

        if not item:
            raise HTTPException(
                status_code=404, detail="Email ou mot de passe invalide")
        else:
            # Check if the user is active
            if not item.is_active:
                await create_log(item.id, ActionType.LOGIN, LogTypes.ERR, "Compte désactivé")
                raise HTTPException(status_code=401, detail="Compte désactivé")
            # Check if the user is verified
            if not item.is_verified:
                await create_log(item.id, ActionType.LOGIN, LogTypes.ERR, "Compte pas encore vérifié")
                raise HTTPException(status_code=401, detail="Compte pas encore vérifié")
            # Check if the password is correct
            if not bcrypt.checkpw(password.encode(), item.password.encode()):
                await create_log(item.id, ActionType.LOGIN, LogTypes.ERR, "Email ou mot de passe invalide")
                raise HTTPException(
                    status_code=401, detail="Email ou mot de passe invalide")

            token = create_jwt_token(item)
            # uncomment so that only the last session remains active
            # await delete_other_token(item.id)
            stmt_token = insert(UserActiveToken).values(token=token)
            await session.execute(stmt_token)
            await create_log(item.id, ActionType.LOGIN, LogTypes.INFO, "Connexion réussie")
            return {"token": token, "first_name": item.first_name, "last_name": item.last_name, "email": item.email}

def create_jwt_token(user: User):
    expiration_time = datetime.utcnow() + TOKEN_EXPIRATION_TIME
    token_payload = {"sub": user.id,
                     "exp": expiration_time, "nbf": datetime.utcnow()}
    jwt_token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return jwt_token

async def checkToken(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les informations de l'utilisateur",
    )
    try:
        async with get_db() as session:
            stmt = select(UserActiveToken).where(
                UserActiveToken.token == token)
            result = await session.execute(stmt)
            item = result.scalars().first()
            if not item:
                raise HTTPException(status_code=401, detail="Token invalide")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Check if the token is expired
        if 'exp' in payload:
            expiry_date = datetime.fromtimestamp(
                payload['exp'], tz=timezone.utc)
            if datetime.now(timezone.utc) > expiry_date:
                raise HTTPException(status_code=401, detail="Token expiré")

        # Check if the token is not valid yet
        if 'nbf' in payload:
            not_before_date = datetime.fromtimestamp(
                payload['nbf'], tz=timezone.utc)
            if datetime.now(timezone.utc) < not_before_date:
                raise HTTPException(
                    status_code=401, detail="Token pas encore valide")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")
    
async def logout_user(token: str):
    async with get_db() as session:
        stmt = select(UserActiveToken).where(UserActiveToken.token == token)
        result = await session.execute(stmt)
        item = result.scalars().first()
        user_id = await checkToken(token)
        if not item:
            await create_log(user_id, ActionType.LOGOUT, LogTypes.ERR, "Token invalide")
            raise HTTPException(status_code=401, detail="Token invalide")
        stmt = delete(UserActiveToken).where(UserActiveToken.token == token)
        await session.execute(stmt)
        await create_log(user_id, ActionType.LOGOUT, LogTypes.INFO, "Déconnexion réussie")
        return {"message": "Token supprimé"}