from pydantic import BaseModel, Field


class RoleResponse(BaseModel):
    id: str
    code: str
    name: str
    description: str | None = None


class UserCreateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role_code: str = Field(min_length=2, max_length=40)
    phone: str | None = Field(default=None, max_length=40)


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    role_code: str | None = Field(default=None, min_length=2, max_length=40)
    is_active: bool | None = None


class UserPasswordResetRequest(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str | None = None
    role: str | None = None
    is_active: bool


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    limit: int
    offset: int

