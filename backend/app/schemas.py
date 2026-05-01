from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: Optional[int] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    token_type: Optional[str] = None

class TokenRefresh(BaseModel):
    refresh_token: str

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = UserRole.USER

class UserLogin(BaseModel):
    username: str
    password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[int] = None

class DataUploadResponse(BaseModel):
    message: str
    file_id: str
    file_name: str
    rows_count: int
    columns: List[str]

class DataCleaningResult(BaseModel):
    original_rows: int
    cleaned_rows: int
    removed_rows: int
    columns: List[str]
    sample_data: List[Dict[str, Any]]

class ChartDataResponse(BaseModel):
    chart_type: str
    x_axis: List[str]
    series: List[Dict[str, Any]]
    title: str

class AnalysisRecordBase(BaseModel):
    file_name: str
    analysis_type: str
    chart_type: Optional[str] = "line"

class AnalysisRecordCreate(AnalysisRecordBase):
    chart_data: Optional[str] = None
    analysis_config: Optional[str] = None

class AnalysisRecordResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    analysis_type: str
    chart_type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisRecordDetail(AnalysisRecordResponse):
    chart_data: Optional[str] = None
    analysis_config: Optional[str] = None
