from fastapi import APIRouter, Depends

from src.users.services.user_service import find_user_service, get_current_user, update_user_service
from src.users.dto.user_dto import UpdateUserDto


router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)

@router.get("")
async def get_user(current_user: str = Depends(get_current_user)):
    user = await find_user_service(current_user)
    return user

@router.put("")
async def update_user(user: UpdateUserDto, current_user: str = Depends(get_current_user)):
    user = await update_user_service(current_user, user)
    return user
