from pydantic import BaseModel
from typing import Optional


class StudentUser(BaseModel):
    fullname: str
    email: str
    username: str
    password: str
    grade: int
    school: str


class TeacherUser(BaseModel):
    fullname: str
    email: str
    username: str
    password: str
    school: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    username: str
    email: str
    new_password: str
