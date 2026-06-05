from pydantic import BaseModel, Field


class BootstrapUserRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str | None = None
    is_active: bool


class DeviceRegisterRequest(BaseModel):
    device_uuid: str = Field(min_length=8, max_length=128)
    platform: str = Field(min_length=2, max_length=40)
    app_version: str = Field(min_length=1, max_length=40)


class DeviceResponse(BaseModel):
    id: str
    device_uuid: str
    platform: str
    app_version: str
    is_trusted: bool

