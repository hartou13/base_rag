from pydantic import BaseModel, EmailStr, Field


class SimpleNewUserDto(BaseModel):
    email: EmailStr = Field(..., description="The email field is required")
    password: str = Field(..., description="The password field is required")
    first_name: str = Field(..., description="The first_name field is required")
    last_name: str = Field(..., description="The last_name field is required")
    language: str = Field(..., description="The language field is required")

class UpdateUserDto(BaseModel):
    email: EmailStr = Field(..., description="The email field is required")
    first_name: str = Field(..., description="The first_name field is required")
    last_name: str = Field(..., description="The last_name field is required")
    language: str = Field(..., description="The language field is required")