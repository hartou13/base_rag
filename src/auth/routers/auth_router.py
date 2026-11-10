from fastapi import APIRouter, Depends

from src.auth.dto.login_dto import LoginDto
from src.auth.services.auth_service import authenticate_user, logout_user
from src.users.dto.user_dto import SimpleNewUserDto
from src.users.services.user_service import create_simple_user, get_current_user_token


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login")
async def login(credentials: LoginDto):
    auth= await authenticate_user(credentials.email, credentials.password)
    return auth


@router.post("/sign-up")
async def sign_up(user_data: SimpleNewUserDto):
    await create_simple_user(user_data)
    return await authenticate_user(user_data.email, user_data.password)

@router.delete("/logout")
async def logout(current_user_token: str = Depends(get_current_user_token)):
    return await logout_user(current_user_token)