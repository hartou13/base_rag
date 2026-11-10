from contextvars import ContextVar
from datetime import datetime, timedelta
import os
import re
from typing import Optional
import bcrypt
from fastapi import HTTPException
from sqlalchemy import insert, select, update
from sqlalchemy.orm import load_only, joinedload
from src.database.mysql_connector import get_db
from src.logs.models.log import ActionType, LogTypes
from src.logs.services.log_service import count_users_login_last_months, create_log, create_log_from_exception
from src.users.dto.user_dto import SimpleNewUserDto, UpdateUserDto
from src.users.models.user import User

current_user_var: ContextVar[Optional[str]] = ContextVar("current_user_var", default=None)
current_user_token_var: ContextVar[Optional[str]] = ContextVar("current_user_token_var", default=None)

email_regex = re.compile(
    r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
)
    # Define the regex patterns for each criterion
uppercase_pattern = r'[A-Z]'
lowercase_pattern = r'[a-z]'
digit_pattern = r'[0-9]'
special_character_pattern = r'[^\w\s]'
my_aux_adress = os.environ.get("MY_AUX_ADRESS", "http://localhost:8001")
bearer_token = os.environ.get("MY_AUX_TOKEN", "")


def get_current_user() -> Optional[str]:
    return current_user_var.get()

def get_current_user_token() -> Optional[str]:
    return current_user_token_var.get()


def is_valid_password(password: str, pass_length:int = 13) -> bool:
    if len(password) < pass_length:
        return False    
    # Check each criterion
    criteria = [uppercase_pattern, lowercase_pattern, digit_pattern,
                special_character_pattern]
    for pattern in criteria:
        if not re.search(pattern, password):
            return False
    
    return True

def is_valid_email(email: str) -> bool:
    """Check if the provided email is valid."""
    return re.match(email_regex, email) is not None


async def create_simple_user(user:SimpleNewUserDto):
    # if not is_valid_password(user.password, pass_length=8):
    #     raise HTTPException(status_code=400, detail="Password too weak")
    if not is_valid_email(user.email):
        raise HTTPException(status_code=400,detail="Email invalide")
    password_bytes = user.password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    async with get_db() as session:
        result = await session.scalar(select(User).options(load_only(User.email)).where(User.email==user.email))
        if (result):
            await create_log(result.id, ActionType.REGISTER, LogTypes.ERR, "Email address is already used, try login")
            raise HTTPException(status_code=400, detail="Email address is already used, try login")
    
        stmt = insert(User).values(
            email=user.email, password=hashed.decode('utf-8'),
            first_name=user.first_name,
            last_name=user.last_name,
            language=user.language,
        )
        result=await session.execute(stmt)
        await session.commit()
        await create_log(result.inserted_primary_key[0], ActionType.REGISTER, LogTypes.INFO, "Compte créé")
        return result.inserted_primary_key[0]

async def find_user_service(current_user_id: str):
    async with get_db() as db:
        stmt = select(User).where(User.id == current_user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()

        if user is None:
            raise HTTPException(
                status_code=404, detail="User non trouvé"
            )
    return user

async def update_user_service(user_id: str, user: UpdateUserDto):
    async with get_db() as db:
        existing_user = await db.scalar(select(User).options(load_only(User.email, User.first_name, User.last_name, User.language)).where(User.id == user_id))
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")
        existing_user.email = user.email
        existing_user.first_name = user.first_name
        existing_user.last_name = user.last_name
        existing_user.language = user.language
        await db.commit()
        return existing_user