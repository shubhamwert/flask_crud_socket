# pylint: disable=too-few-public-methods
from typing import Literal, Optional

from pydantic import BaseModel, Field, constr


class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=50)  # type: ignore
    password: constr(min_length=6)  # type: ignore
    role: str = Field(default="read", description="User role (default is 'read')")
    model_config = {
        "from_attributes": True  # Enables reading from SQLAlchemy-style objects
    }


class UserRead(BaseModel):
    id: int
    username: str
    role: str = Field(default="read", description="User role (default is 'read')")
    model_config = {
        "from_attributes": True  # Enables reading from SQLAlchemy-style objects
    }


class UserLogin(BaseModel):
    username: str
    password: str
    model_config = {
        "from_attributes": True  # Enables reading from SQLAlchemy-style objects
    }


class IssueCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    file_url: Optional[str] = None
    severity: Literal["P0", "P1", "P2", "P3"]
    status: Literal["Open", "triaged", "in_progress", "done"] = "Open"
    reported_by: int
    model_config = {"from_attributes": True}


class IssuePut(BaseModel):
    status: Literal["Open", "triaged", "in_progress", "done"] = "Open"


class IssueRead(IssueCreate):
    id: int


class IssuePermissionCreate(BaseModel):
    user_id: int
    issue_id: int
    role: Literal["reporter", "manager", "admin"]

    model_config = {"from_attributes": True}


class IssuePermissionRead(IssuePermissionCreate):
    id: int
