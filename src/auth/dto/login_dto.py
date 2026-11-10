from pydantic import BaseModel, Field, validator, EmailStr

class LoginDto(BaseModel):
    email: EmailStr = Field(..., description="The email field is required")
    password: str = Field(..., description="The password field is required")

    @validator('email', 'password')
    def check_fields(cls, value):
        if value is None or value == '':
            raise ValueError('Field cannot be null or empty')
        return value
    
class CheckPasswordDto(BaseModel):
    password: str = Field(..., description="The password field is required")