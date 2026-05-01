from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

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
